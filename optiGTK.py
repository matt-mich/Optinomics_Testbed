#!/usr/bin/python3

import gi
import PIL.Image
import array
import sys
import numpy as np
import math
import cairo
import time
import cv2


gi.require_version('LightDM', '1')
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from gi.repository import GObject, LightDM

CAM_FOUND = False
info_label = None
DEV = True
ims = None
greeter = None
builder = None
TIME_SCALE = 10

STATE = None

STATES = ["INIT","AUTH_INIT","AUTH_COMPLETE","LOGIN"]

STATE_LABELS = ["Starting webcam feed",
                "Authenticating user...",
                "User found in network!",
                "Please Login"]

ANIM_QUEUE = []



class Animation:
    def __init__(self):
        self.total_stages = 0
        self.equation = None
    # def isFinished(self):
    # def isStarted(self):
    # def isFinished(self):
    # def isFinished(self):

def show_message_func(greeter,text,type):
    setInfoLabel(info_label,text)

def show_prompt_func(greeter,text,type):
    setInfoLabel(info_label,text)
    
def authentication_complete_cb(greeter):
    if greeter.get_is_authenticated():
        if not greeter.start_session_sync("xfce"):
            setInfoLabel(info_label,"Failed to start xfce")
    else:
        setInfoLabel(info_label,"Auth failed")
class State:
    def __init__(self,window):
        self.set_state(STATES[0])
        self.state_int = 0
        self.tick = 0
        self.init_time = time.time()
        self.prev_time = time.time()
        self.update_dims(window)

    def update_dims(self,window):
        self.w = window.get_screen().get_width()
        self.h = window.get_screen().get_height()

    def get_state(self):
        return self.STATE

    def set_state(self,state):
        self.STATE = state
        setInfoLabel(info_label,STATE_LABELS[STATES.index(state)])
        self.tick = 0
        self.init_time = time.time()
        self.prev_time = time.time()

    def get_time(self):
        return self.tick

    def inc_time(self):
        self.tick+=(time.time()-self.prev_time)
        self.prev_time = time.time()
    def inc_state(self):
        self.state_int += 1
        if self.state_int >= len(STATES):
            self.state_int = 0
        self.set_state(STATES[self.state_int])

def pil2cairo(im):
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    s = im.tobytes('raw', 'BGRA')
    a = array.array('B', s)
    dest = cairo.ImageSurface(cairo.FORMAT_ARGB32, im.size[0], im.size[1])
    ctx = cairo.Context(dest)
    non_premult_src_wo_alpha = cairo.ImageSurface.create_for_data(
        a, cairo.FORMAT_RGB24, im.size[0], im.size[1])
    non_premult_src_alpha = cairo.ImageSurface.create_for_data(
        a, cairo.FORMAT_ARGB32, im.size[0], im.size[1])
    ctx.set_source_surface(non_premult_src_wo_alpha)
    ctx.mask_surface(non_premult_src_alpha)
    return dest

def mat_mask(n):
    cent = int(n/2)
    y,x = np.ogrid[-cent:n-cent, -cent:n-cent]

    mask = x**2 + y**2 <= cent*cent

    array = np.zeros((n, n))
    array[mask] = 255
    return array

class Handler:
    def onDestroy(self, *args):
        print("Destroy!")
        Gtk.main_quit()

    def keypress(self,win,event_key):
        print("keypress")
        print(event_key.keyval)
        if event_key.keyval == 65289:
            STATE.inc_state()

    def onButtonPressed(self, button):
        if greeter.get_is_authenticated():
            authentication_complete_cb(greeter)
        elif greeter.get_in_authentication():
            greeter.respond('matt')
        else:
            greeter.authenticate('matt')

    def on_draw(self,wid, cr):
        win_w = wid.get_window().get_width()
        win_h = wid.get_window().get_height()
        STATE.inc_time()

        if CAM_FOUND:
            cam = cv2.VideoCapture(0)  #set the port of the camera as before
            retval, cam_image = cam.read() #return a True bolean and and the image if all go right
            cam.release() #Closes video file or capturing device.
            img = cv2.cvtColor(cam_image, cv2.COLOR_BGR2RGB)
            cam_image = PIL.Image.fromarray(img).convert('RGB')
            cam_found = True
        else:
            if DEV:
                cam_image = PIL.Image.open("res/matt.png").convert('RGB')
            else:
                cam_image = PIL.Image.open("/usr/local/bin/optinomics/res/matt.png").convert('RGB')



        cam_image = cam_image.crop((0,0,cam_image.width,cam_image.width))
        fin_size = int(win_w*0.5)

        cam_image = cam_image.resize((fin_size,fin_size), PIL.Image.ANTIALIAS)

        # Make into Numpy array of RGB and get dimensions
        RGB = np.array(cam_image)
        h, w = RGB.shape[:2]

        # Add an alpha channel, fully opaque (255)
        RGBA = np.dstack((RGB, mat_mask(w))).astype('uint8')
        # Make mask of black pixels - mask is True where image is black
        mBlack = (RGBA[:, :, 0:3] == [0,0,0]).all(2)
        # Make all pixels matched by mask into transparent ones
        RGBA[mBlack] = (0,0,0,0)
        cam_image = PIL.Image.fromarray(RGBA)
        #cam_image = Image.fromarray(cam_image)
     
        #cam_image = get_masked_img(cam_image,0)
        arr = array.array('B',cam_image.tobytes())
        i_w, i_h = cam_image.size
        ims = pil2cairo(cam_image)
        time_update= None
        if STATE.get_state() == "INIT":
            cr.set_line_width(1)
            #print(w," ",h)
            cr_x, cr_y = int(win_w/2), int(win_h/2)
            cr.translate(cr_x,cr_y)
            offset = math.pi*1.5
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.arc(0, 0, cam_image.size[0]/2, 0, math.pi*2)
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.fill()

            cr.set_line_width(15)
            cr.set_source_rgb(1.0, 1.0, 1.0)

            img_mid = cam_image.size[0]/2

            time_update = STATE.get_time()*6
            if time_update < 2*math.pi:
                cr.arc(0, 0, img_mid, offset, time_update+offset)
            elif time_update < 4*math.pi:
                cr.arc(0, 0, img_mid, time_update-2*math.pi+offset, 2*math.pi+offset)
            else:
                STATE.set_state(STATE.get_state())
            cr.stroke_preserve()


        elif STATE.get_state() == "AUTH_INIT":
            cr.set_line_width(15)
            #print(w," ",h)
            cr_x, cr_y = int(win_w/2), int(win_h/2)
            cr.translate(cr_x,cr_y)
            img_mid = cam_image.size[0]/2
            time_update = STATE.get_time()*2
            offset = math.pi*1.5

            cr.set_source_surface(ims, -img_mid, -img_mid)
            cr.paint()
            cr.set_source_rgb(1.0, 1.0, 1.0)

            cr.arc(0, 0, img_mid, offset, time_update+offset)
            cr.stroke_preserve()
            
#            cr.set_source_rgb(0.3, 0.4, 0.6)
#            cr.fill()
        elif STATE.get_state() == "AUTH_COMPLETE":

            cr.set_line_width(30)
            #print(w," ",h)
            cr_x, cr_y = int(win_w/2), int(win_h/2)
            cr.translate(cr_x,cr_y)
            time_wait = 0.5
            time_update = (STATE.get_time()-time_wait)*win_w
            if(time_update < 0):
                time_update = 0
            img_mid = cam_image.size[0]/2
            cr.set_source_surface(ims,-img_mid+time_update,-cam_image.size[1]/2)
            cr.paint()            
            cr.set_source_rgb(0.3, 1.0, 0.3)

            cr.arc(time_update, 0, img_mid, 0, 7)
            cr.stroke_preserve()
        else:
            login.set_visible(True)


def image2pixbuf(im):
    arr = array.array('B', im.tobytes())
    width, height = im.size
    return GdkPixbuf.Pixbuf.new_from_data(arr, GdkPixbuf.Colorspace.RGB,True, 8, width, height, width * 4)

def setLogo(logo_obj,window):
    if DEV:
        logo_img = PIL.Image.open('res/Opti.png')
    else:
        logo_img = PIL.Image.open('/usr/local/bin/optinomics/res/Opti.png')

    w,h = logo_img.width, logo_img.height

    win_w = window.get_screen().get_width()
    win_h= window.get_screen().get_height()
    
    print(window.get_size())
    scale = win_w/w
    scale *= 0.2
    logo_img = logo_img.resize((int(w*scale),int(h*scale)),PIL.Image.ANTIALIAS)
    #logo_arr = np.array(logo_img.tostring())
    #GdkPixbuf.Pixbuf.new_from_data(logo_arr, GdkPixbuf.Colorspace.RGB, True, 8, logo_arr.shape[1], logo_arr.shape[0], logo_arr.shape[1] * 4)
    pix = image2pixbuf(logo_img)
    logo_obj.set_from_pixbuf(pix)

class Render:
    def __init__(self,window):
        self.window = window
    def render(self):
        self.window.queue_draw()
        self.timeout_id = GLib.timeout_add(100, self.render, None)      

def win_draw(self):
    darea.queue_draw()
    timeout_id = GLib.timeout_add(TIME_SCALE, win_draw, None)

def get_masked_img(src,arc):
	mask = PIL.Image.new('L', (src.width,src.height), 0)
	draw = PIL.ImageDraw.Draw(mask)
	draw.pieslice((0, 0) + mask.size,0,arc, fill=255)
	src = PIL.ImageOps.fit(src, mask.size, centering=(0.5, 0.5))
	src.putalpha(mask)
	return src

def setInfoLabel(label,text):
    markup = "<span font_desc='Source Code Pro Bold "
    size = 20
    markup = markup + str(size) +"'>" + text + "</span>"
    #info_label.set_markup("<span font_desc='Sans 5.4'>%s</span>" % text)
    label.set_markup(markup)


handlers = {
	"show-message":show_message_func,
	"show-prompt":show_prompt_func
}

DEV = False

def debug_print(msg):
    if DEV:
        f = open("pyGTK_log.txt","a+")
    else:
        f = open("/usr/local/bin/optinomics/pyGTK_log.txt","a+")
#        f = open("/home/pyGTK_log.txt","a+")
    f.write(msg+"\n")
    f.close()

if __name__ == "__main__":
    builder = Gtk.Builder()
    try:
        cam = cv2.VideoCapture(0)  #set the port of the camera as before
        CAM_FOUND = True
    except:
        CAM_FOUND = False

    if len(sys.argv) > 1 and sys.argv[1] == 'dev':
        DEV = True
        debug_print("Started DEV Mode")
    else:
        debug_print("Started in GREETER mode")            

    greeter = LightDM.Greeter()

    if not DEV:
        greeter.connect_to_daemon_sync()
        debug_print("Connected to daemon")            

    greeter.connect("show-message",show_message_func)
    greeter.connect("show-prompt",show_prompt_func)
    greeter.connect ("authentication-complete", authentication_complete_cb)
    debug_print("Greeter functions connected")            

    css_P = Gtk.CssProvider()
    if DEV:
        css_P.load_from_path("./res/style.css")
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css_P,400)
        builder.add_from_file("gtk_glade.glade")
    else:
        css_P.load_from_path("/usr/local/bin/optinomics/res/style.css")
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css_P,400)
        builder.add_from_file("/usr/local/bin/optinomics/gtk_glade.glade")
    debug_print("Styles connected, glade_UI built")            

    builder.connect_signals(Handler())
    debug_print("Handlers connected to UI")

    window = builder.get_object("main_window")
    
    logo = builder.get_object("logo")
    
    setLogo(logo,window)
    debug_print("Logo set")

    info_label = builder.get_object("info_label")
    debug_print("Info label set")

    darea = builder.get_object("darea")
    login = builder.get_object("login")

    timeout_id = GLib.timeout_add(TIME_SCALE, win_draw, None)
    STATE = State(window)

    screen = window.get_screen()
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    debug_print("S_W: " + str(screen_width) + " S_H: " + str(screen_height))

    geo = Gdk.Geometry()
    debug_print("Geometry set")

    geo.min_width = screen_width
    geo.min_height = screen_height
    window.set_geometry_hints(None, geo, Gdk.WindowHints.MIN_SIZE)

    window.set_default_size(screen_width,screen_height)
    window.show_all()
    window.resize(screen_width,screen_height)
    debug_print("Starting main loop")
    Gtk.main()