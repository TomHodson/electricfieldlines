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

from colorsys import hsv_to_rgb
def rand_colour(len = 3):
    rgb = hsv_to_rgb(randrange(2**16)/float(2**16), 0.9, 0.9)
    print rgb
    return map(lambda x : int(x * 255.0), rgb)
    #return tuple(randrange(255) for _ in range(len))
    

def polar_to_cart(r, theta, x=0, y =0):
    return r * cos(theta) + x, r * sin(theta) + y

def line(*args, **kwargs):
    assert len(args) % 2 == 0
    numofpoints = len(args) // 2 
    colour = kwargs.get('colour') or (255,255,255)
    pyglet.graphics.draw(numofpoints, pyglet.gl.GL_LINE_STRIP,
                        ('v2f/stream', tuple(args)),
                        ('c%sB/static' % len(colour),[x for _ in range(numofpoints) for x in colour]) 
                        )


def point(x, y, colour = (255,255,255)):
    x, y = float(x), float(y)
    pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
                        ('v2f', (x,y)),
                        ('c3B',colour)
                        )

class Polygon(object):
    def __init__(self, **kwargs):

        self.colour = kwargs.get('colour') or (255,255,255)
        numofvertices = len(kwargs['points'])
        flattenedpointlist = [term for point in kwargs['points'] for term in point]
        self.vertexlist = pyglet.graphics.vertex_list(numofvertices,
                            ('v2f/static', flattenedpointlist),
                            ('c%sB/static' % len(self.colour),[x for _ in range(numofvertices) for x in self.colour]) 
                            )
    def draw(self,x,y, *args, **kwargs):
        glPushMatrix()
        glTranslated(x, y, 0)
        self.vertexlist.draw(pyglet.gl.GL_POLYGON)
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

if __name__ == '__main__':
    b_assert(polar_to_cart(1, pi*0.5)[1], 1)
    print rand_colour()