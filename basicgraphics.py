from __future__ import division
import pyglet
from pyglet.gl import *
from math import *
from itertools import cycle
from random import randrange

def b_assert(thing1, thing2):
    if thing1 == thing2:
        return
    else:
        raise AssertionError(str(thing1) + ' != ' + str(thing2))

def rand_colour(len = 3):
    return tuple(randrange(255) for _ in range(len))
    

def polar_to_cart(r, theta, x=0, y =0):
    return r * cos(theta) + x, r * sin(theta) + y

def line(*args, **kwargs):
    assert len(args) % 2 == 0
    numofpoints = len(args) // 2 
    colour = kwargs.get('colour') or (255,255,255)
    pyglet.graphics.draw(numofpoints, pyglet.gl.GL_LINE_STRIP,
                        ('v2f', tuple(args)),
                        ('c%sB' % len(colour),[x for _ in range(numofpoints) for x in colour]) 
                        )


def point(x, y, colour = (255,255,255)):
    x, y = float(x), float(y)
    pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
                        ('v2f', (x,y)),
                        ('c3B',colour)
                        )

class Polygon(object):
    def __init__(self, **kwargs):
        self.vertices = kwargs['points']
        self.colour = kwargs.get('colour') or (255,255,255)
    def draw(self,x,y, *args, **kwargs):
        self.colour = kwargs.get('colour') or self.colour # update colour if need be
        numofvertices = len(self.vertices)
        flattenedpointlist = [term for point in self.vertices for term in point]
        glPushMatrix()
        glTranslated(x, y, 0)
        pyglet.graphics.draw(numofvertices, pyglet.gl.GL_POLYGON,
                            ('v2f', flattenedpointlist),
                            ('c%sB' % len(self.colour),[x for _ in range(numofvertices) for x in self.colour]) 
                            )
        glPopMatrix()
        
class Circle(Polygon):
    def __init__(self, r, vertexdensity=5.0, **kwargs):
        circumference = 2 * pi * r
        numofvertices = int(circumference // vertexdensity)
        step = (2*pi) / numofvertices
        points =  tuple([polar_to_cart(r, theta) for theta in (step*vertex for vertex in range(numofvertices))])
        super(Circle, self).__init__(points=points, **kwargs)
        
class RoundedSquare(Polygon):
    def __init__(self, r, vertexdensity=5.0, **kwargs):
        pass

def findline(x, y, x1, y1):
    reallybig = 2**64
    if x != x1:
        slope = (y - y1)/float(x - x1)
        intercept = y - (slope*x)
        return slope, intercept
    else:
        return reallybig, 0 # fail semi-gracefully
def abstractline(slope, intercept, width, height):
    rightintercept = slope*width + intercept
    line(0, intercept, width, rightintercept)
def perpline(x, y, x1,y1):
    if x1 != x and y != y1:
        slope = -1.0 / ((y - y1)/(x-x1))
        intercept = ((y+y1)/2) - slope * ((x+x1)/2)
    elif y == y1:
        slope = 2**64
        intercept = 0
    else:
        slope = 0
        intercept = (y+y1)/2
    return slope, intercept
if __name__ == '__main__':
    b_assert(polar_to_cart(1, pi*0.5)[1], 1)
    print rand_colour()