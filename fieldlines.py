#!/usr/bin/env python

import pyglet
from pyglet.window import Window, key
from pyglet.gl import *
import math
from basicgraphics import *
from numpy import *
#from simplui import *

pyglet.options['debug_gl'] = False
window = Window(800,640, caption = 'FieldLines', vsync = True)

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



fps_display = pyglet.clock.ClockDisplay()

Buttons = []
Links = []

mouseX = window.width/2
mouseY = window.height/2
update = True

vectlines = True
vectgrid = False
useC = True
paused = True

try:
    import ctypes
    clib = ctypes.CDLL("./drawlines.so")
    class vec2(ctypes.Structure):
            _fields_ = [("x", ctypes.c_double),
                        ("y", ctypes.c_double)]
    class pointcharge(ctypes.Structure):
            _fields_ = [("x", ctypes.c_double),
                        ("y", ctypes.c_double),
                        ("charge",ctypes.c_double)]
    clib.field.restype = vec2
except ImportError:
    print "Ctypes not installed, switching to python (slow)"
    useC = False
except:
    print "Couldn't find drawlines.so, try running make. switching to python (slow)"
    useC = False
class Link(object):
    def __init__(self, button1, button2, strength=10.0, length=100.0, damp=0.8):
        self.button1 = button1
        self.button2 = button2
        self.strength = strength
        self.length = length
        self.damp = damp
    def compute(self, dt):
        deltap = array((self.button1.x - self.button2.x, self.button1.y - self.button2.y))
        distance = math.sqrt(deltap[0]**2 + deltap[1]**2)
        direction = array((deltap[0] / distance, deltap[1] / distance))
        displacement = distance - self.length
        force = direction * displacement * self.strength

        self.button2.acc += force * self.button2.invmass * 1.0 
        self.button1.acc += force * self.button1.invmass * -1.0
        line(self.button1.x, self.button1.y, self.button2.x, self.button2.y)


class Button(object):
    def __init__(self, x, y, radii, halo_colour = None, held_colour=None, charge=1.0, mass = 1.0):
        self.radii = radii
        self.sqradii = self.radii ** 2
        
        self.held = False
        self.hovered = False
        
        self.halo_colour = halo_colour or rand_colour()
        self.held_colour = held_colour or rand_colour()
        
        self.haloshape = Circle(self.radii, colour=self.halo_colour)
        self.handleshape = Circle(self.radii, colour=self.held_colour)
        self.normalshape = Circle(self.radii / 3, colour=self.halo_colour)
        self.charge = charge

        self.invmass = 1.0 / mass
        self.pos = array((float(x), float(y)))
        self.vel = array((0,0))
        self.acc = array((0,0))
        self.x, self.y = self.pos[0], self.pos[1]
        self.vertexlists = [pyglet.graphics.vertex_list(steps,
                        ('v2f/stream', [0 for _ in range(steps*2)]),
                        ('c%sB/static' % len(self.halo_colour),[c for _ in range(steps) for c in self.halo_colour]) 
                        ) for _ in range(linesperbutton)]

    def mouse_press(self, x, y, button, modifiers, context):
        if self.hovered:
            if button == 1:
                held_objects.add(self)
                context.selected_objects = self
                self.held = True
                return True
            if button == 4:
                Links.add(Link(self, context.selected_objects))
            
    def mouse_drag(self, x, y, dx, dy, but, mod):
        self.x += dx
        self.y += dy
        self.vel = array((0,0))
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
        if self.hovered and symbol == key.D:
                Buttons.remove(self)
                deadlinks = set()
                for link in Links:
                    if link.button1 == self or link.button2 == self:
                        deadlinks.add(link)
                Links.difference_update(deadlinks)
                del self
        
    def draw(self, dt = 1.0/20.0):
        friction = 0.7

        if not paused:
            self.acc += (self.charge * 1000 * EfieldC((self.x, self.y), [button for button in Buttons if button is not self]) * self.invmass)
            #print 'acc ' ,self.acc
            self.vel += self.acc * dt
            self.vel *= friction
            #print 'old pos ', self.x, self.y
            self.x, self.y = (self.x, self.y) + (self.vel * dt)
            #print 'new pos ', self.x, self.y


        if self.held:
            self.handleshape.draw(self.x,self.y)
        elif self is hovered:
            self.haloshape.draw(self.x,self.y)
        else:
            self.normalshape.draw(self.x,self.y)
        self.acc = (0.0,0.0)
  

class ButtonEventHandler(object):
    def __init__(self):
        self.scalef = 1.0
        self.translation = array((0,0,0))
        self.mousepos = array((0,0))
        self.keys = key.KeyStateHandler()
        self.selected_objects = None

    def on_mouse_motion(self, *args):
        global mouseX
        global mouseY
        args = list(args)
        self.mousepos = (array((args[:2])) - self.translation[:2]) / self.scalef
        args[:2] = self.mousepos
        hovered = None
        for button in Buttons:
            if button.mouse_motion(*args):
                global update
                update = True
                break
      
    def on_mouse_press(self, x, y, button, mod):
        if hovered:
            hovered.mouse_press(x, y, button, mod, self)
      
    def on_mouse_release(self, *args):
        for object in held_objects:
            object.mouse_release(*args)
        held_objects.clear()

    def compute(self, dt=1.0/20.0):
        global update
        update = True
        window.clear()

        fps_display.draw()
        debuginfo = pyglet.text.Label('scale: {:.3} worldpoint: {p[0]:4.0f},{p[0]:4.0f}, force: {f}  '.format(self.scalef, p=self.mousepos, f=EfieldC(self.mousepos)),
                          font_name='monospace',
                          font_size=15,
                          x=0, y=window.height - 15)
        debuginfo.draw()

        if hovered:
            buttoninfo = pyglet.text.Label('charge {:.3f}, mass {:.3f}'.format(hovered.charge, 1.0/hovered.invmass),
                          font_name='monospace',
                          font_size=15,
                          x=0, y=window.height - 32)
            buttoninfo.draw()

        glPushMatrix()
        glTranslatef(*self.translation)

        glScalef(*([self.scalef] * 3))
        point(0,0)
        for link in Links:
            link.compute(dt=dt)
        for button in Buttons:
            button.draw(dt=dt)
        if vectgrid: drawvectorfield()
        if vectlines: Cdrawfieldlines(self)
        glPopMatrix()
    def on_mouse_drag(self, *args):
        global update
        args = list(args)
        if held_objects:
            args[2:4] = array(args[2:4]) / self.scalef    
            for object in held_objects:
                object.mouse_drag(*args)
        else:
            self.translation += array(args[2:4] + [0])
        update = True
            
    def on_key_press(self, *args):
        global vectlines; global vectgrid; global update; global useC
        global Buttons; global Links; global paused
        if args[0] == key.C: Buttons = []; Links = set()
        elif args[0] == key.L: vectlines = not vectlines
        elif args[0] == key.B:
            Buttons.append(Button(self.mousepos[0], self.mousepos[1], 20, charge =10))
        elif args[0] == key.N:
            Buttons.append(Button(self.mousepos[0], self.mousepos[1], 20, charge=-10))
        elif args[0] == key.P:
            paused = not paused
        elif args[0] == key.Q:
            plot_field()
        elif hovered:
                hovered.key_press(*args)
        update = True
    def on_mouse_scroll(self, x, y, dx, dy):
        if not hovered:
            inc = 1.1
            newscalef = self.scalef * (inc**dy)
            self.translation[:2] -= (self.mousepos * newscalef) - (self.mousepos * self.scalef)
            self.scalef = newscalef
        elif self.keys[key.M]:
            hovered.invmass /= 1.5**dy
        else:
            hovered.charge *= 1.5**dy
        

def EfieldC(pos, buttons = Buttons):
    #print 'EfieldC in', pos
    pointsarray = pointcharge * len(buttons)
    pos = vec2(*pos)
    points = pointsarray(*(pointcharge(button.x, button.y, button.charge) for button in buttons))
    force = clib.field(pos, ctypes.c_int(len(points)), points)
    #print  'EfieldC out', array((force.x, force.y)), force.x, force.y
    return array((force.x, force.y)) * 100

steps = 300
linesperbutton = 12
    
def Cdrawfieldlines(context):

    step = 5.0 / context.scalef if 5.0 / context.scalef >= 1.0 else 1.0

    pointsarray = pointcharge * len(Buttons)
    points = pointsarray(*(pointcharge(button.x, button.y, button.charge) for button in Buttons))
    numofButtons = len(Buttons)
    datatype = ((ctypes.c_double * (steps*2))*linesperbutton)*numofButtons
    data = datatype()
    clib.vectorline(ctypes.c_int(len(Buttons)),points,data, ctypes.c_double(step))
    for cbutton,pbutton in zip(data, Buttons):
        for vertexlist,clist in zip(pbutton.vertexlists,cbutton):
            #print "after",list[:10]
            #print len(clist)
            vertexlist.vertices = clist
            vertexlist.draw(pyglet.gl.GL_LINE_STRIP)
def plot_field():
    granularity = 10
    width = window.width / granularity
    height = window.height / granularity
    print EfieldC((1.0,1.0))
    data = bytearray(EfieldC)
    fieldtexture = pyglet.image.ImageData(width, height, "RGB", data)

    

buttonevents = ButtonEventHandler() 

window.push_handlers(buttonevents)
window.push_handlers(buttonevents.keys)

pyglet.clock.schedule_interval(buttonevents.compute, 1.0/20.0)

held_objects = set()
selected_objects = set()
hovered = None
Buttons = [Button(mouseX, mouseY, 20, charge = 10), Button(mouseX, mouseY + 100, 20, charge = 10)]
Links = set()#set([Link(Buttons[0] , Buttons[1], 10.0, 100.0)])
#window.push_handlers(pyglet.window.event.WindowEventLogger())

pyglet.app.run()
