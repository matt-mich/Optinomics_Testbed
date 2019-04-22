#!/usr/bin/env python

import time
from scipy import misc
import tkinter as tk
import PIL
from PIL import Image, ImageDraw, ImageTk, ImageOps
from cv2 import *
import gi
import logging
gi.require_version('Gtk', '3.0') 
gi.require_version('LightDM', '1')

from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk

from gi.repository import LightDM
import sys
c = None
mylabel = None
NOTE = None
greeter = None
MASK = None

USER = None
PASS = None


logger = logging.getLogger('OptiGreeter:')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/usr/local/bin/optinomics/opti.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

def login_cb():
	if greeter.get_is_authenticated():
		logger.info('AUTHENTICATED!')

		NOTE.set("Attempting to start session")
		authentication_complete_cb(greeter)
	elif greeter.get_in_authentication():
		#NOTE.set("Sending password")
		#c.itemconfig(mylabel,text=NOTE.get())
		logger.info('SENDING PASSWORD')
		greeter.respond(PASS.get())
	else:
		#NOTE.set("Username accepted")
		#c.itemconfig(mylabel,text=NOTE.get())
		logger.info('SENDING USERNAME')
		greeter.authenticate(USER.get())

def submitUserPass():
	username = USER.get()
	password = PASS.get()
	greeter.authenticate(username)
	greeter.respond(password)
	if greeter.get_is_authenticated():
		authentication_complete_cb(greeter)

def show_message_func(greeter,text,type):
	logger.info('SHOWING MESSAGE')
	logger.info(text)
	NOTE.set(text);
	c.itemconfig(mylabel,text=NOTE.get())

def show_prompt_func(greeter,text,type):
	logger.info('SHOWING PROMPT')
	logger.info(text)
	
	NOTE.set(text);
	c.itemconfig(mylabel,text=NOTE.get())

def authentication_complete_cb(greeter):
	logger.info('AUTH COMPLETE!')
	NOTE.set("Auth complete")
	c.itemconfig(mylabel,text=NOTE.get())
	if greeter.get_is_authenticated():
		if not greeter.start_session_sync("xfce"):
			NOTE.set("Failed to start XFCE")
			c.itemconfig(mylabel,text=NOTE.get())
	else:
		NOTE.set("Login failed.")
		c.itemconfig(mylabel,text=NOTE.get())

def get_masked_img(src,arc):
	mask = Image.new('L', (src.width,src.height), 0)
	draw = ImageDraw.Draw(mask) 
	draw.pieslice((0, 0) + mask.size,0,arc, fill=255)
	src = ImageOps.fit(src, mask.size, centering=(0.5, 0.5))
	src.putalpha(mask)
	return ImageTk.PhotoImage(src)

handlers = {
    "login_cb": login_cb,
	"show-message":show_message_func,
	"show-prompt":show_prompt_func
}


if __name__ == "__main__":
	builder = Gtk.Builder()
	greeter = LightDM.Greeter()

	greeter.connect("::show-message",show_message_func)
	greeter.connect("::show-prompt",show_prompt_func)
	greeter.connect ("::authentication-complete", authentication_complete_cb)
	greeter.connect_to_daemon_sync()

	BG = "darkseagreen"
	r = tk.Tk() 

	#cam = VideoCapture(0)  #set the port of the camera as before
	#retval, cam_image = cam.read() #return a True bolean and and the image if all go right
	#cam.release() #Closes video file or capturing device.

	w = int(r.winfo_screenwidth())
	h = int(r.winfo_screenheight())
	r.configure(background="black")

	c = tk.Canvas(r, width=w, height=h)
	c.configure(background=BG)
#	image = Image.open("res/Opti.png")
	image = Image.open("/usr/local/bin/optinomics/res/Opti.png")
	i_w = image.width
	i_h = image.height
	f_w = int(w*0.8)
	f_h = int(i_h*(f_w/i_w))

	image = image.resize((f_w,f_h), PIL.Image.ANTIALIAS)
	tkimg = ImageTk.PhotoImage(image)
	c.create_image(int(f_w)/2+int(0.1*w),f_h, anchor=tk.CENTER,image=tkimg)
	cam_image = None

	if cam_image is not None:
		cam_image = cvtColor(cam_image, COLOR_BGR2RGB)
		cam_image = Image.fromarray(cam_image)
	else:
		cam_image = misc.imread("/usr/local/bin/optinomics/res/matt.gif", mode='RGBA')
#		cam_image = misc.imread("res/matt.gif", mode='RGBA')

		cam_image = Image.fromarray(cam_image)

	cam_image = cam_image.resize((int(w*0.2),(int(w*0.2))), PIL.Image.ANTIALIAS)
	tk_cam_img = get_masked_img(cam_image,0)
	cam_img_obj = c.create_image(int(w/2),f_h+int(h*0.4), anchor=tk.CENTER,image=tk_cam_img)

	NOTE = tk.StringVar()
	NOTE.set("Accessing camera feed...")
	status_var = "Accessing camera feed..."
	c.itemconfig(mylabel,text=status_var)

	mylabel = c.create_text((int(w/2),(0.9*h)),fill='white',font='sans-serif, 20', text=status_var,justify=tk.LEFT)
	#button = tk.Button(r, text='Login', width=int(w/10))
	c.pack()
	r.update_idletasks()

	time.sleep(2)
	NOTE.set("Authenticating from camera feed...")

	status_var = "Authenticating from camera feed..."
	c.itemconfig(mylabel,text=status_var)
	r.update_idletasks()

	time.sleep(1)

	for x in range(0, 360):
		tk_cam_img = get_masked_img(cam_image,x)
		c.itemconfig(cam_img_obj,image=tk_cam_img)
		r.update_idletasks()
		time.sleep(0.005)

	NOTE.set("Authenticated!")
	c.itemconfig(mylabel,text="Authenticated!")

	confirmed = c.create_oval(c.bbox(cam_img_obj), outline="green2",width=0)

	for x in range(0, 10):
		c.itemconfig(confirmed,width=x)
		r.update_idletasks()
		time.sleep(0.01)

	time.sleep(0.5)

	for x in range(0, 90):
		c.move(cam_img_obj,0,5)
		c.move(confirmed,0,5)
		r.update_idletasks()
		time.sleep(0.005)

	c.delete(cam_img_obj)
	c.delete(confirmed)

	time.sleep(1)
	NOTE.set("Please login as normal.")
	
	c.itemconfig(mylabel,text="Please login as normal.")

	USER = tk.StringVar()
	PASS = tk.StringVar()

	user_input = tk.Entry(c,relief=tk.FLAT,textvariable=USER)
	password_input = tk.Entry(c,relief=tk.FLAT,textvariable=PASS)

	login_button = tk.Button(c,text="Login",relief=tk.FLAT,font='sans-serif, 15',fg='white',bg='green',command=login_cb)

	user_label = tk.Label(c,text="User:",font='sans-serif, 15',fg='white',bg=BG,justify='left')

	password_label = tk.Label(c,text="Password:",font='sans-serif, 15',fg='white',bg=BG,justify='left')

	c.create_window(int(w/2),int(h/2)-30,window=user_label)
	c.create_window(int(w/2),int(h/2),window=user_input)
	c.create_window(int(w/2),int(h/2)+30,window=password_label)
	c.create_window(int(w/2),int(h/2)+60,window=password_input)
	c.create_window(int(w/2),int(h/2)+100,window=login_button)

	r.mainloop()