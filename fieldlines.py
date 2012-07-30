import pyglet
from pyglet.window import Window, key
from pyglet.gl import *
import math
from basicgraphics import *
from numpy import *
#from simplui import *

pyglet.options['debug_gl'] = False
config = pyglet.gl.Config(stencil_size=0,depth_size=0, double_buffer=True)
window = Window(640,640, config = config, caption = 'FieldLines', vsync = False)

#themes = [Theme('../simplui-1.0.4/themes/macos'), Theme('../simplui-1.0.4/themes/pywidget')]
#theme = 0
#frame = Frame(themes[theme], w=640, h=640)
#window.push_handlers(frame)

#dialogue = Dialogue('Inspector', x=200, y=500, content=
## add a vertical layout to hold the window contents
#    VLayout(autosizex=True, hpadding=0, children=[
#    # now add some folding boxes
#        FoldingBox('stats', content=
#        # each box needs a content layout
#            VLayout(children=[
#            # add a text label, note that this element is named...
#                Label('0.0 fps', name='fps_label')
#                ])
#            ),
#        FoldingBox('settings', content=
#            VLayout(children=[
#            # a clickable button to change the theme
#                Button('Change GUI Theme'),
#            # a slider, with label
#                HLayout(children=[
#                    Label('Segments', halign='right'),
#                    Slider(w=100, min=0.0, max=1000, name='grid'),
#                    ]),
#                Checkbox('Lines', h=100, name='vectlines'),
#                Checkbox('Grid', h=100, name='vectgrid')
#                ])
#            ),
#        ])
#    )
## add the dialogue to the frame
#frame.add( dialogue )
import ctypes
clib = ctypes.CDLL("./drawlines.so")
class vec2(ctypes.Structure):
        _fields_ = [("x", c_double),
                    ("y", c_double)]
class pointcharge(ctypes.Structure):
        _fields_ = [("x", c_double),
                    ("y", c_double),
                    ("charge",c_double)]
clib.field.restype = vec2

held_objects = set()
hovered = None
buttons = []
fps_display = pyglet.clock.ClockDisplay()

mouseX = window.width/2
mouseY = window.height/2
update = True

zoom = 10.0
grid = 50
scale = 10

vectlines = True
vectgrid = False
useC = True
  
class Button(object):
    def __init__(self, x, y, radii, halo_colour = None, held_colour=None, charge=1.0):
        self.x, self.y = int(x), int(y)
        self.radii = radii
        self.sqradii = self.radii ** 2
        
        self.held = False
        self.hovered = False
        
        self.halo_colour = halo_colour or rand_colour()
        self.held_colour = held_colour or rand_colour()
        
        self.haloshape = Circle(self.radii, colour=self.halo_colour)
        self.handleshape = Circle(self.radii, colour=self.held_colour)
        self.charge = charge
    def mouse_press(self, x, y, button, modifiers):
        if self.hovered:
            held_objects.add(self)
            self.held = True
            return True
            
    def mouse_drag(self, x, y, dx, dy, but, mod):
        self.x += dx
        self.y += dy
        self.x = self.x % window.width
        self.y = self.y % window.height
    def mouse_release(self, x, y, button, modifiers):
        self.held = False
    def mouse_motion(self, x, y, dx, dy):
        if ((x-self.x)**2 + (y-self.y)**2) <= self.sqradii:
            global hovered
            hovered = self
            self.hovered = True
            return True
        else:
            self.hovered = False
            if hovered == self:
                hovered = None
                return True
            
    def key_press(self, symbol, mods):
        if self.hovered and symbol == key.DELETE:
                buttons.remove(self)
                del self
        
    def draw(self):
        if self.held:
            self.handleshape.draw(self.x,self.y)
        elif self is hovered:
            self.haloshape.draw(self.x,self.y)
        point(self.x, self.y)
  

class ButtonEventHandler(object):
    def on_mouse_motion(self, *args):
        global mouseX
        global mouseY
        mouseX, mouseY = args[:2]
        hovered = None
        for button in buttons:
            if button.mouse_motion(*args):
                global update
                update = True
                break
      
    def on_mouse_press(self, *args):
        if hovered:
            hovered.mouse_press(*args)
      
    def on_mouse_release(self, *args):
        for object in held_objects:
            object.mouse_release(*args)
        held_objects.clear()

    def on_draw(self):
        global update
        if update:
            glPushMatrix()
            window.clear()
            fps_display.draw()
            for button in buttons:
                button.draw()
            if vectgrid: drawvectorfield()
            if vectlines: Cdrawfieldlines() if useC else drawfieldlines()
            glPopMatrix()
            update = False
    def on_mouse_drag(self, *args):
        global update
        for object in held_objects:
            object.mouse_drag(*args)
        update = True
            
    def on_key_press(self, *args):
        global vectlines; global vectgrid; global update; global useC
        if args[0] == key.C: useC = not useC
        if args[0] == key.Q:window.config.sample_buffers = 0 if window.config.sample_buffers else 1
        if args[0] == key.L: vectlines = not vectlines
        if args[0] == key.G: vectgrid = not vectgrid
        if args[0] == key.B:
            buttons.append(Button(mouseX, mouseY, 20))
        if args[0] == key.N:
            buttons.append(Button(mouseX, mouseY, 20, charge=-1))
        elif args[0] == key.S:
            buttons.append(Slider(mouseX, mouseY, 20))
        elif hovered:
                hovered.key_press(*args)
        update = True
        
def EfieldB(pos):
    vect = [0, 0]
    for Button in buttons:
        mousevect = (pos[0] - Button.x, pos[1] - Button.y)
        mag = sqrt(mousevect[0]**2 + mousevect[1]**2)
        scale = (Button.charge/(mag*zoom)**2)
        mousevect = (mousevect[0]/mag * scale, mousevect[1]/mag * scale)
        vect[0] += mousevect[0]
        vect[1] += mousevect[1]
    return array(vect)

def EfieldC(pos):
    pointsarray = pointcharge * len(buttons)
    pos = vec2(*pos)
    points = pointsarray(*(pointcharge(button.x, button.y, button.charge) for button in buttons))
    force = clib.field(pos, ctypes.c_int(len(points)), points)
    return array((force.x, force.y))

def drawvectorfield():
    for x in range(0, window.width, grid):
        for y in range(0, window.height, grid):
            if useC:
                vect = EfieldC(array((x,y)))
            else: vect = EfieldB(array((x,y)))
            vect = vect/sqrt(vect.dot(vect)) * grid
            line(x, y, x+vect[0], y+vect[1])
    
def Cdrawfieldlines():
    pointsarray = pointcharge * len(buttons)
    points = pointsarray(*(pointcharge(button.x, button.y, button.charge) for button in buttons))
    numofbuttons = len(buttons)
    datatype = ((ctypes.c_double * 200)*12)*numofbuttons
    data = datatype()
    clib.vectorline(ctypes.c_int(len(buttons)),points,data)
    for cbutton,pbutton in zip(data, buttons):
        for list in cbutton:
            #print "after",list[:10]
            line(*list, colour=pbutton.halo_colour)
    
def drawfieldlines():
    linesperbutton = 12
    maxits = 50
    ini = 1
    step = 20
    anglestep = (2*pi/linesperbutton)
    angles = [(math.cos(i*anglestep),math.sin(i*anglestep)) for i in range(linesperbutton)]
    points = [int() for i in range(maxits * 2)]
    for Button in buttons:
        for angle in angles:
            end = None
            pos = array((Button.x + angle[0],angle[1] + Button.y))
            for i in range(maxits):
                points[2*i], points[(2*i)+1] = pos[0], pos[1] 
                field = EfieldC(pos)
                vect = field/sqrt(field.dot(field)) * Button.charge
                pos += vect * step
                if offscreen(pos) or nearbutton(pos):
                    end = (i+1)*2
                    break
            line(*points[:end or maxits*2], colour=Button.halo_colour)

def nearbutton(pos):
    for Button in buttons:
        if ((Button.x-10 < pos[0] < Button.x+10) and (Button.y-10 < pos[1] < Button.y+10)): return True
    return False
def offscreen(pos):
    return not ((0 < pos[0] < window.width) and (0 < pos[1] < window.height))
 
window.push_handlers(ButtonEventHandler())
pyglet.app.run()
