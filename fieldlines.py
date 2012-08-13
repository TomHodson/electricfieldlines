#!/usr/bin/env python

import pyglet
from pyglet.window import Window, key
from pyglet.gl import *
import math
from basicgraphics import *
from numpy import *
#from simplui import *

pyglet.options['debug_gl'] = False
window = Window(640,640, caption = 'FieldLines', vsync = True)

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

zoom = 10.0
grid = 50
scale = 10

vectlines = True
vectgrid = False
useC = True

try:
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
except ImportError:
    print "Ctypes not installed, switching to python (slow)"
    useC = False
except:
    print "Couldn't find drawlines.so, try running make. switching to python (slow)"
    useC = False
class Link(object):
    def __init__(self, button1, button2, strength, length, damp=0.8):
        self.button1 = button1
        self.button2 = button2
        self.strength = strength
        self.length = length
        self.damp = damp
    def compute(self, dt):
        deltap = (self.button1.x - self.button2.x, self.button1.y - self.button2.y)
        distance = math.sqrt(deltap[0]**2 + deltap[1]**2)
        direction = (deltap[0] / distance, deltap[1] / distance)
        displacement = distance - self.length
        force = (displacement * direction[0] * self.strength - self.damp * displacement , displacement * direction[1] * self.strength - self.damp * displacement )

        self.button2.acc = (self.button1.acc[0] + force[0] * dt,self.button1.acc[0] + force[1] * dt)
        self.button1.acc = (self.button2.acc[0] + (-1.0) * force[0] * dt,self.button2.acc[1] + -1.0 * force[1] * dt)
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
        self.charge = charge

        self.invmass = 1.0 / mass
        self.pos = array((float(x), float(y)))
        self.vel = array((0,0))
        self.acc = array((0,0))
        self.x, self.y = self.pos[0], self.pos[1]

    def mouse_press(self, x, y, button, modifiers):
        if self.hovered:
            held_objects.add(self)
            self.held = True
            return True
            
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
        if self.hovered and symbol == key.DELETE:
                Buttons.remove(self)
                del self
        
    def draw(self, dt = 1.0/20.0):
        self.acc += (self.charge * 100000 * EfieldC((self.x, self.y), [button for button in Buttons if button is not self]) * self.invmass)
        #print 'acc ' ,self.acc
        self.vel += self.acc * dt
        #print 'old pos ', self.x, self.y
        self.x, self.y = (self.x, self.y) + (self.vel * dt)
        #print 'new pos ', self.x, self.y


        if self.held:
            self.handleshape.draw(self.x,self.y)
        elif self is hovered:
            self.haloshape.draw(self.x,self.y)
        self.acc = (0.0,0.0)
  

class ButtonEventHandler(object):
    def __init__(self):
        self.scalef = 2.0
        self.translation = array((0,0,0))
        self.mousepos = array((0,0))

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
      
    def on_mouse_press(self, *args):
        if hovered:
            hovered.mouse_press(*args)
      
    def on_mouse_release(self, *args):
        for object in held_objects:
            object.mouse_release(*args)
        held_objects.clear()

    def compute(self, dt=1.0/20.0):
        global update
        global scalef
        update = True
        #dt = pyglet.clock.tick()
        glPushMatrix()
        fps_display.draw()
        window.clear()
        glTranslatef(*self.translation)

        glScalef(*([self.scalef] * 3))
        point(0,0)
        point(*self.mousepos)
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
        global Buttons
        if args[0] == key.P: print Buttons[0].x, Buttons[0].y, self.mousepos
        if args[0] == key.C: useC = not useC
        if args[0] == key.L: vectlines = not vectlines
        if args[0] == key.G: vectgrid = not vectgrid
        if args[0] == key.B:
            Buttons.append(Button(self.mousepos[0], self.mousepos[1], 20))
        if args[0] == key.N:
            Buttons.append(Button(self.mousepos[0], self.mousepos[1], 20, charge=-1))
        elif hovered:
                hovered.key_press(*args)
        update = True
    def on_mouse_scroll(self, x, y, dx, dy):
        inc = 0.05
        if self.scalef + (dy * inc) < 0.001: dy = 0

        newscalef = self.scalef + (dy * inc)
        self.translation[:2] -= (self.mousepos * newscalef) - (self.mousepos * self.scalef)
        self.scalef = newscalef
         #self.translation += array((dx,dy, 0)) * 0.5
        

def EfieldC(pos, buttons = Buttons):
    #print 'EfieldC in', pos
    pointsarray = pointcharge * len(buttons)
    pos = vec2(*pos)
    points = pointsarray(*(pointcharge(button.x, button.y, button.charge) for button in buttons))
    force = clib.field(pos, ctypes.c_int(len(points)), points)
    #print  'EfieldC out', array((force.x, force.y)), force.x, force.y
    return array((force.x, force.y))

    
def Cdrawfieldlines(context):
    step = 5.0 / context.scalef if 5.0 / context.scalef >= 1.0 else 1.0

    pointsarray = pointcharge * len(Buttons)
    points = pointsarray(*(pointcharge(button.x, button.y, button.charge) for button in Buttons))
    numofButtons = len(Buttons)
    datatype = ((ctypes.c_double * 600)*12)*numofButtons
    data = datatype()
    clib.vectorline(ctypes.c_int(len(Buttons)),points,data, ctypes.c_double(step))
    for cbutton,pbutton in zip(data, Buttons):
        for list in cbutton:
            #print "after",list[:10]
            line(*list, colour=pbutton.halo_colour)
    

buttonevents = ButtonEventHandler() 

window.push_handlers(buttonevents)
pyglet.clock.schedule_interval(buttonevents.compute, 1.0/20.0)

held_objects = set()
hovered = None
Buttons = [Button(mouseX, mouseY, 20)]#, Button(mouseX, mouseY + 10, 20)]
#Links = [Link(Buttons[0] , Buttons[1], 10.0, 100.0)]

#window.push_handlers(pyglet.window.event.WindowEventLogger())

pyglet.app.run()
