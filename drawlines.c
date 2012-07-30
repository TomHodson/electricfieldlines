#include  <stdio.h>
#include  <math.h>

#define numoflines 12
#define maxits 100
#define step 10.0

typedef struct {
    double x;
    double y;
    } vec2;
    
typedef struct {
    double x;
    double y;
    double charge;
    } pointcharge;

int nearbutton(vec2 pos, int numberofpoints, pointcharge point[]);
vec2 field(vec2 pos, int numofpoints, pointcharge points[]);
void vectorline(int numofpoints, pointcharge points[], double output[][numoflines][maxits*2]);

    
vec2 field(vec2 pos, int numofpoints, pointcharge points[])
{   
    vec2 force;
    force.x = 0; force.y = 0;
    for(int i = 0; i < numofpoints; i++)
    {
    pointcharge point = points[i];
    vec2 f_part;
    f_part.x = pos.x - point.x; f_part.y = pos.y - point.y;
    double mag = sqrt(f_part.x*f_part.x + f_part.y*f_part.y);
    f_part.x = (f_part.x/(mag*mag*mag)) * point.charge; f_part.y = (f_part.y/(mag*mag*mag)) * point.charge;
    
    force.x += f_part.x; force.y += f_part.y;
    }
    return force;
}


void vectorline(int numofpoints, pointcharge points[], double output[][numoflines][maxits*2])
{
double anglestep = (M_PI*2.0)/(double)numoflines;

for(int point = 0; point < numofpoints; point++)
    {
    vec2 thispos;
    thispos.x = points[point].x; thispos.y = points[point].y;
    for(int lineno = 0; lineno < numoflines; lineno++)
        {
        double angle = (double)lineno * anglestep;
        output[point][lineno][0] = thispos.x;
        output[point][lineno][1] = thispos.y;
        double lastx = output[point][lineno][2] = (cos(angle)*step) + thispos.x;
        double lasty = output[point][lineno][3] = (sin(angle)*step) + thispos.y;
        for(int it = 2; it < maxits; it++)
            {
            vec2 pos;
            pos.x = lastx; pos.y = lasty;
            vec2 this = field(pos, numofpoints, points);
            double mag = sqrt((this.x*this.x) + (this.y*this.y));
            this.x = this.x/mag; this.y = this.y/mag;
            lastx = output[point][lineno][2*it] = lastx + (this.x * step * points[point].charge);
            lasty = output[point][lineno][(2*it)+1] = lasty + (this.y * step * points[point].charge);
            }
        }
    }
}
/*
int nearbutton(vec2 pos, int numberofpoints, pointcharge point[])
{
    for(int i=0;i<numerofpoints;i++)
    {
        Button = points[i];
        if((Button.x-10 < pos.x < Button.x+10) and (Button.y-10 < pos.y < Button.y+10))
        return 1;
    }
    return 0;
}
*/
int main(void)
{
;
}
