#!/bin/python2
import socket

if socket.gethostname() == "example":
    from settings_example import *
if socket.gethostname() == "skynet":
    from settings_skynet import *
if socket.gethostname() == "pandora":
    from settings_pandora import *
if socket.gethostname() == "thinkpad":
    from settings_thinkpad import *
