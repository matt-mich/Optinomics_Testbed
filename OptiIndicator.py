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

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from gi.repository import GObject
from OptiFunctions import *

TIME_SCALE = 1000

RES_PATH = None

class Handler:
    def on_destroy(self, *args):
        print("Destroy!")
        Gtk.main_quit()

    def keypress(self, win, event_key):
        # print(event_key.keyval)
        if event_key.keyval == 65506:
            STATE.inc_state()
    def on_draw(self,win, cr):
        x = 1

def update(self):
    rand = np.random.randint(0, 1000)
    set_info_label(info_label, str(rand))
    timeout_id = GLib.timeout_add(TIME_SCALE, update,None)


DEV = False


def debug_print(msg):
    print(msg)
    # if DEV:
    #     f = open("pyGTK_log.txt", "a+")
    # else:
    #     f = open("/usr/local/bin/optinomics/pyGTK_log.txt", "a+")
    # #        f = open("/home/pyGTK_log.txt","a+")
    # f.write(msg + "\n")
    # f.close()


if __name__ == "__main__":
    builder = Gtk.Builder()
    if len(sys.argv) > 1 and sys.argv[1] == 'dev':
        DEV = True
        debug_print("Started DEV Mode")
    else:
        debug_print("Started in GREETER mode")

    RES_PATH = set_resource_path(DEV)

    builder.add_from_file(RES_PATH+"OptiIndicator_UI.glade")
    css_P = Gtk.CssProvider()
    css_P.load_from_path(RES_PATH+"style.css")
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css_P, 400)

    builder.connect_signals(Handler())

    window = builder.get_object("main_window")

    info_label = builder.get_object("info_label")

    debug_print("Info label set")

    timeout_id = GLib.timeout_add(TIME_SCALE, update, None)

    STATE = State(window, info_label)

    screen = window.get_screen()
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    debug_print("S_W: " + str(screen_width) + " S_H: " + str(screen_height))

    window.move(0,0)
    window.show_all()
    debug_print("Starting main loop")
    Gtk.main()