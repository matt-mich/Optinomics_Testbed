import subprocess as sp
import time
import PIL
from PIL import Image, ImageOps

RES_PATH = "/home/doctor/GitHub/Optinomics_Testbed/res/"

def get_dims():
    dim = sp.check_output(["xdpyinfo"])
    dim = str(dim)
    dim = dim.split("\\n")
    res = None
    for line in dim:
        if "dimensions" in line:
            res = line
    res = res.split('dimensions:')[1]
    res = res.replace(" ", "")
    res = res.split('pixels')[0]
    res = res.split('x')
    w = res[0]
    h = res[1]
    return w, h


def set_logo_scale():
    logo = Image.open(RES_PATH+"orig_logo.png")
    w, h = get_dims()
    l_w, l_h = logo.size
    w_diff = int(w)/2 - int(l_w)/2
    if w_diff > 0:
        logo = ImageOps.expand(logo,(int(w_diff),int(int(l_h)/4)))
    fin_path = RES_PATH+"scaled_logo.png"
    logo.save(fin_path)
    return fin_path


img_path = set_logo_scale()
sp.call(["i3lock", "--blur", "5", "-i", img_path])
time.sleep(2)
sp.call(["killall", "i3lock"])
