import subprocess
import time

subprocess.call(["i3lock", "--blur", "200", "-i", "/home/doctor/GitHub/Optinomics_Testbed/res/big_logo.png"])
time.sleep(2)




subprocess.call(["killall", "i3lock"])
