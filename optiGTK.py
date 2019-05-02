#!/usr/bin/env python

# import time
# from scipy import misc
# import PIL
# from PIL import Image, ImageDraw, ImageTk, ImageOps
# from cv2 import *
import gi
# import logging
gi.require_version('Gtk', '3.0') 
gi.require_version('LightDM', '1')

from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk

from gi.repository import LightDM

import sys

DEV = True

def debug_print(msg):

    if DEV:
        f = open("pyGTK_log.txt","a+")
    else:
        f = open("/home/matt/git/Optinomics_Testbed/pyGTK_log.txt","a+")
    f.write(msg)
    f.close()

if __name__ == "__main__":
    #builder = Gtk.Builder()

    if len(sys.argv) > 1:
        if sys.argv[1] == 1:
            DEV = False
            debug_print("Started")
    else:
        debug_print("Started in DEV mode")            

        
    greeter = LightDM.Greeter()

    if not DEV:
        greeter.connect_to_daemon_sync()

    class OptiGreeter(Gtk.Window):
        def __init__(self):
            Gtk.Window.__init__(self, title="OptiGreeter")

            #self.add(self.u_entry)
            #self.add(self.p_entry)

    win = OptiGreeter()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    Gtk.main()