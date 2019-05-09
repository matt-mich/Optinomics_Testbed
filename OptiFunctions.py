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
import gi

gi.require_version('LightDM', '1')
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from gi.repository import GObject, LightDM


RES_PATH = None
DEV = None

STATES = ["INIT",
          "AUTH_D1",
          "AUTH_D2",
          "LOGIN"]

STATE_LABELS = ["Authenticating user...",
                "User found in network!",
                "User found in network!",
                "Please Login"]


class State:
    def __init__(self, window, info_label):
        self.state = 0
        self.label = info_label
        self.set_state(STATES[0])
        self.state_int = 0
        self.tick = 0
        self.init_time = time.time()
        self.prev_time = time.time()

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.reset_time()
        self.state = state
        if self.label is not None:
            set_info_label(self.label, STATE_LABELS[STATES.index(state)])
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


def set_resource_path(DEV):
    if DEV:
        RES_PATH = "./res/"
    else:
        RES_PATH = "/usr/local/bin/optinomics/res/"
    return RES_PATH


def pil2cairo(im):
    # NOTE This function is not my own, it is a workaround designed by
    # https://stackoverflow.com/users/141253/joaquin-cuenca-abela with
    # some minor modifications by myself.

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
    cent = int(n / 2)
    y, x = np.ogrid[-cent:n - cent, -cent:n - cent]
    mask = x ** 2 + y ** 2 <= cent * cent
    mat_arr = np.zeros((n, n))
    mat_arr[mask] = 255
    return mat_arr


def get_masked_img(src, arc, draw):
    mask = PIL.Image.new('L', (src.width, src.height), 0)
    draw.pieslice((0, 0) + mask.size, 0, arc, fill=255)
    src = PIL.ImageOps.fit(src, mask.size, centering=(0.5, 0.5))
    src.putalpha(mask)
    return src


def image2pixbuf(im):
    arr = array.array('B', im.tobytes())
    width, height = im.size
    return GdkPixbuf.Pixbuf.new_from_data(arr, GdkPixbuf.Colorspace.RGB,True, 8, width, height, width * 4)


def set_info_label(label, text):
    markup = "<span font_desc='Source Code Pro Bold "
    size = 20
    markup = markup + str(size) +"'>" + text + "</span>"
    label.set_markup(markup)
