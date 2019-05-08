#!/usr/bin/python3

import gi
import PIL.Image
import PIL.ImageOps
import array
import sys
import numpy as np
import math
import cairo
import time
import cv2
import pytweening

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

DEF_TS = 5
TIME_SCALE = DEF_TS

STATE = None

STATES = ["INIT",
          "AUTH_D1",
          "AUTH_D2",
          "LOGIN"]

STATE_LABELS = ["Authenticating user...",
                "User found in network!",
                "User found in network!",
                "Please Login"]

ANIM_QUEUE = []

search_anim = None
auth_done_anim = None
auth_done_swipe_anim = None


class Animation:
    def __init__(self, time_per_step, loop, eq):
        self.completion = 0
        self.tween = 0
        self.time_per_step = time_per_step
        self.equation = eq
        self.complete = False
        self.looping = loop
        self.last_time = time.time()
        self.curr_time = time.time()
        self.delta_time = 0
        self.paused = False

    def step(self):
        if self.complete is False:
            self.curr_time = time.time()
            self.delta_time = self.curr_time - self.last_time
            self.last_time = time.time()
            if self.paused is False:
                next_comp = self.completion + (self.delta_time*self.time_per_step)
                if next_comp >= 1:
                    next_comp = 1
                self.tween = self.equation(next_comp)
                self.completion = next_comp
                if self.completion >= 1:
                    if not self.looping:
                        self.finish()
                    else:
                        self.completion = 0
        return self.tween

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def finish(self):
        self.completion = 1.0
        self.complete = True

    def restart(self):
        self.complete = False
        self.completion = 0

    def is_finished(self):
        return self.complete


def show_message_func(greeter, text, type):
    setInfoLabel(info_label,text)


def show_prompt_func(greeter, text, type):
    setInfoLabel(info_label,text)


def authentication_complete_cb(greeter):
    if greeter.get_is_authenticated():
        if not greeter.start_session_sync("xfce"):
            setInfoLabel(info_label,"Failed to start xfce")
    else:
        setInfoLabel(info_label,"Auth failed")


class State:
    def __init__(self,window):
        self.state = 0
        self.set_state(STATES[0])
        self.state_int = 0
        self.tick = 0
        self.init_time = time.time()
        self.prev_time = time.time()
        self.update_dims(window)

    def update_dims(self, window):
        self.w = window.get_screen().get_width()
        self.h = window.get_screen().get_height()

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.reset_time()
        self.state = state
        setInfoLabel(info_label, STATE_LABELS[STATES.index(state)])
        self.tick = 0
        self.init_time = time.time()
        self.prev_time = time.time()

    def get_time(self):
        return self.tick

    def inc_time(self):
        self.tick += time.time()-self.prev_time
        self.prev_time = time.time()

    def reset_time(self):
        self.tick = 0
        self.init_time = time.time()
        self.prev_time = time.time()

    def inc_state(self):
        self.reset_time()
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
    y, x = np.ogrid[-cent:n-cent, -cent:n-cent]

    mask = x**2 + y**2 <= cent*cent

    array = np.zeros((n, n))
    array[mask] = 255
    return array


class Handler:

    def onDestroy(self, *args):
        print("Destroy!")
        if CAM_FOUND and cam is not None:
            cam.release()
        Gtk.main_quit()

    def keypress(self,win,event_key):
        # print(event_key.keyval)
        if event_key.keyval == 65506:
            STATE.inc_state()

    def onButtonPressed(self, button):
        if greeter.get_is_authenticated():
            authentication_complete_cb(greeter)
        elif greeter.get_in_authentication():
            greeter.respond('matt')
        else:
            greeter.authenticate('matt')

    def on_draw(self, wid, cr):
        global search_anim
        global auth_done_anim
        global auth_done_swipe_anim
        global TIME_SCALE

        line_width = 16

        win_w = wid.get_window().get_width()
        win_h = wid.get_window().get_height()

        if CAM_FOUND is True:
            retval, cam_image = cam.read()
            img = cv2.cvtColor(cam_image, cv2.COLOR_BGR2RGB)
            cam_image = PIL.Image.fromarray(img).convert('RGB')
            cam_image = PIL.ImageOps.mirror(cam_image)
        else:
            if DEV:
                cam_image = PIL.Image.open("res/matt.png").convert('RGB')
            else:
                cam_image = PIL.Image.open("/usr/local/bin/optinomics/res/matt.png").convert('RGB')

        if cam_image.width > cam_image.height:
            fin_dim = cam_image.height
            dim_cropped = cam_image.width - cam_image.height
            cam_image = cam_image.crop((dim_cropped/2,0,fin_dim+dim_cropped/2,fin_dim))            
        else:
            fin_dim = cam_image.width
            dim_cropped = cam_image.width - cam_image.height
            cam_image = cam_image.crop((0,0,fin_dim,fin_dim))

        cam_image = cam_image.crop((0,0,fin_dim,fin_dim))

        fin_size = int(win_w*0.3)

        cam_image = cam_image.resize((fin_size,fin_size), PIL.Image.ANTIALIAS)

        RGB = np.array(cam_image)
        h, w = RGB.shape[:2]
        RGBA = np.dstack((RGB, mat_mask(w))).astype('uint8')
        mBlack = (RGBA[:, :, 0:3] == [0,0,0]).all(2)
        RGBA[mBlack] = (0,0,0,0)
        cam_image = PIL.Image.fromarray(RGBA)

        arr = array.array('B',cam_image.tobytes())
        i_w, i_h = cam_image.size
        ims = pil2cairo(cam_image)

        if STATE.get_state() == "INIT":
            TIME_SCALE = DEF_TS

            if login.get_visible() is True:
                login.set_visible(False)
                darea.set_visible(True)

            if search_anim is None:
                search_anim = Animation(0.5, True, pytweening.easeInOutSine)

            cr.set_line_width(1)

            cr_x, cr_y = int(win_w/2), int(win_h/2)
            cr.translate(cr_x,cr_y)
            offset = math.pi*1.5

            img_mid = cam_image.size[0]/2

            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.set_source_surface(ims, -img_mid, -img_mid)
            cr.paint()

            cr.fill()
            cr.set_line_width(line_width)
            cr.set_source_rgb(1.0, 1.0, 1.0)

            anim_step = search_anim.step()*4*math.pi
            if anim_step < 2*math.pi:
                cr.arc(0, 0, img_mid-line_width/2, offset, anim_step+offset)
            elif anim_step < 4*math.pi:
                cr.arc(0, 0, img_mid-line_width/2, anim_step-2*math.pi+offset, 2*math.pi+offset)
            else:
                search_anim.pause()
                STATE.inc_time()
                if STATE.get_time() > 2.5:
                    search_anim = None
                    STATE.set_state(STATE.get_state())

            cr.stroke_preserve()

        elif STATE.get_state() == "AUTH_D1":
            TIME_SCALE = DEF_TS

            if login.get_visible() is True:
                login.set_visible(False)
                darea.set_visible(True)

            search_anim = None
            if auth_done_anim is None:
                auth_done_anim = Animation(1, False, pytweening.easeInOutElastic)
            if auth_done_anim.is_finished():
                anim_step = 1
            else:
                anim_step = auth_done_anim.step()

            cr.set_line_width(line_width+line_width*anim_step)

            cr_x, cr_y = int(win_w/2), int(win_h/2)
            cr.translate(cr_x, cr_y)

            img_mid = cam_image.size[0]/2
            cr.set_source_surface(ims, -img_mid, -cam_image.size[1]/2)
            cr.paint()

            r = 1 - (1-0.3)*anim_step
            b = 1
            g = 1 - (1-0.3)*anim_step

            cr.set_source_rgb(r, b, g)

            cr.arc(0, 0, img_mid-line_width/2, 0, 7)
            cr.stroke_preserve()

            if auth_done_anim.is_finished():
                STATE.inc_time()
                if STATE.get_time() > 1:
                    STATE.inc_state()

        elif STATE.get_state() == "AUTH_D2":
            TIME_SCALE = DEF_TS

            if login.get_visible() is True:
                login.set_visible(False)
                darea.set_visible(True)

            auth_done_anim = None
            if auth_done_swipe_anim is None:
                auth_done_swipe_anim = Animation(0.8, False, pytweening.easeInQuad)
            if auth_done_swipe_anim.is_finished():
                anim_step = 1
            else:
                anim_step = auth_done_swipe_anim.step() * 3500

            cr.set_line_width(line_width*2)

            cr_x, cr_y = int(win_w/2), int(win_h/2)
            cr.translate(cr_x, cr_y)

            img_mid = cam_image.size[0]/2
            cr.set_source_surface(ims, -img_mid+anim_step,-cam_image.size[1]/2)
            cr.paint()
            cr.set_source_rgb(0.3, 1.0, 0.3)

            cr.arc(anim_step, 0, img_mid-line_width/2, 0, 7)
            cr.stroke_preserve()

            if auth_done_swipe_anim.is_finished():
                STATE.inc_time()
                if STATE.get_time() > 0.5:
                    STATE.inc_state()

        # cr.set_source_rgb(0.3, 0.4, 0.6)
          # cr.fill()
        elif STATE.get_state() == "LOGIN":
            auth_done_anim = None
            auth_done_swipe_anim = None

            TIME_SCALE = DEF_TS*100
            darea.set_visible(False)
            login.set_visible(True)


def image2pixbuf(im):
    arr = array.array('B', im.tobytes())
    width, height = im.size
    return GdkPixbuf.Pixbuf.new_from_data(arr, GdkPixbuf.Colorspace.RGB,True, 8, width, height, width * 4)


def setLogo(logo_obj, window):
    if DEV:
        logo_img = PIL.Image.open('res/Opti.png')
    else:
        logo_img = PIL.Image.open('/usr/local/bin/optinomics/res/Opti.png')

    w, h = logo_img.width, logo_img.height

    win_w = window.get_screen().get_width()
    win_h = window.get_screen().get_height()
    
    print(window.get_size())
    scale = win_w/w
    scale *= 0.3
    logo_img = logo_img.resize((int(w*scale),int(h*scale)),PIL.Image.ANTIALIAS)
    pix = image2pixbuf(logo_img)
    logo_obj.set_from_pixbuf(pix)


class Render:
    def __init__(self, window):
        self.window = window

    def render(self):
        self.window.queue_draw()
        self.timeout_id = GLib.timeout_add(100, self.render, None)      


def win_draw(self):
    darea.queue_draw()
    timeout_id = GLib.timeout_add(TIME_SCALE, win_draw, None)


def get_masked_img(src, arc, draw):
    mask = PIL.Image.new('L', (src.width,src.height), 0)
    draw.pieslice((0, 0) + mask.size,0,arc, fill=255)
    src = PIL.ImageOps.fit(src, mask.size, centering=(0.5, 0.5))
    src.putalpha(mask)
    return src


def setInfoLabel(label,text):
    markup = "<span font_desc='Source Code Pro Bold "
    size = 20
    markup = markup + str(size) +"'>" + text + "</span>"
    label.set_markup(markup)


handlers = {
    "show-message": show_message_func,
    "show-prompt": show_prompt_func
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
    if len(sys.argv) > 1 and sys.argv[1] == 'dev':
        DEV = True
        debug_print("Started DEV Mode")
    else:
        debug_print("Started in GREETER mode")            

    cam = cv2.VideoCapture(0)
    if cam is not None and cam.isOpened():
        CAM_FOUND = True
        debug_print("CAM FOUND!")

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