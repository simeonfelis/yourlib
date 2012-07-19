#!/bin/python2
import socket

if socket.gethostname() == "skynet":
    from settings_skynet import *
if socket.gethostname() == "pandora":
    from settings_pandora import *
