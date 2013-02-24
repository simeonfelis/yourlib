#!/bin/python2
import socket

if socket.gethostname() == "skynet":
    from settings_skynet import *
else:
    from settings_example import *
