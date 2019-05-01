
'''
ZetCode PyCairo tutorial 

In this program, we connect all mouse
clicks with a line.

Author: Jan Bodnar
Website: zetcode.com 
Last edited: April 2016
'''
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GLib
import cairo
import math
import time

class Example(Gtk.Window):

    def __init__(self):
        super(Example, self).__init__()
        self.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(red=25000,green=40000,blue=25000))

        self.init_ui()
        self.init_time = time.time();
        self.prev_time = time.time();
             
        self.tick_rate = 0.1;
        self.counter = 0;
        self.timeout_id = GLib.timeout_add(500, self.redraw, None)
        self.bottom_msg = "Authentication in progress."

    def redraw(self,data):
        self.queue_draw()
        self.timeout_id = GLib.timeout_add(500, self.redraw, None)
#        self.on_draw()

    def init_ui(self):
        grid = Gtk.Grid()
        button1 = Gtk.Button(label="Button 1")
        frame = Gtk.Frame()
        frame.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(100,100,100,1))
        w, h = self.get_size()
#        grid.set_column_spacing(20)
        darea = Gtk.DrawingArea()
        darea.connect("draw", self.on_draw)
        grid.attach(button1, 0, 0, 1, 1)
        grid.attach(frame, 1, 0, 2, 2)
        self.add(grid)

        self.set_title("Fill & stroke")
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete-event", Gtk.main_quit)
        self.show_all()


    def draw_text(self, wid, cr):
        cr.translate(0,0)
        cr.move_to(0, 0)
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.select_font_face("Courier", cairo.FontSlant.NORMAL, 
            cairo.FontWeight.NORMAL)

        w, h = self.get_size()
        
        cr.set_font_size(60)
                
        (x, y, width, height, dx, dy) = cr.text_extents(self.bottom_msg)

        cr.move_to(w/2 - width/2, h/2)
    
        cr.show_text(self.bottom_msg)

    def on_draw(self, wid, cr):

        self.draw_arc(wid,cr)
        self.draw_text(wid,cr)
        self.draw_img(wid,cr)
        self.inc_counter()

    def draw_img(self,wid,cr):
        self.ims = cairo.ImageSurface.create_from_png("res/Opti.png")
        cr.scale(0.5,0.5*(self.counter+1))
        cr.set_source_surface(self.ims, 10, 10)
        cr.paint()

    def inc_counter(self):
        if(time.time()-self.prev_time > self.tick_rate):        
            self.prev_time = time.time()
            self.counter += 1

    def draw_arc(self,wid,cr):
        cr.set_line_width(9)
        cr.set_source_rgb(0.7, 0.2, 0.0)
        w, h = self.get_size()      
        cr.translate(w/2, h/2)
        angle = self.counter/0.01
        if(angle > 2*math.pi):
            angle = 2*math.pi
        
        cr.arc(0, 0, 50, angle, 2*math.pi)
        cr.set_fill_rule(cairo.FillRule.EVEN_ODD)
        cr.stroke_preserve()
        cr.translate(-w/2, -h/2)
        
        cr.set_source_rgb(0.3, 0.4, 0.6)

def main():
    
    app = Example()
    start = time.time()
    curr = time.time()
    Gtk.main()
    # while(True):
    #     Gtk.main_iteration_do(False)
    #     if(time.time()-curr > 0.01):
    #         Gtk.DrawingArea.queue_draw(app)
    #         curr = time.time()
    #     if(time.time()-start > 10):
    #         app.bottom_msg = "AUTHENTICATED!"
if __name__ == "__main__":    
    main()