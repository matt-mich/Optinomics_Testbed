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

# import sys

DEV = False

if __name__ == "__main__":
    #builder = Gtk.Builder()
    greeter = LightDM.Greeter()

    if not DEV:
        greeter.connect_to_daemon_sync()

    class OptiGreeter(Gtk.Window):
        def __init__(self):
            Gtk.Window.__init__(self, title="OptiGreeter")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            self.add(vbox)
            #self.u_entry = Gtk.Entry()

            #self.p_entry = Gtk.Entry()
            self.button = Gtk.Button(label="Click Here")
            vbox.pack_start(self.button, True, True, 0)

            #self.add(self.u_entry)
            #self.add(self.p_entry)

    win = OptiGreeter()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    Gtk.main()