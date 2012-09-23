#!/bin/python2
import socket

if socket.gethostname() == "skynet":
    from settings_skynet import *
elif socket.gethostname() == "pandora":
    from settings_pandora import *
elif socket.gethostname() == "thinkpad":
    from settings_thinkpad import *
else:
    from settings_example import *
