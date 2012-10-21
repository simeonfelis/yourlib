from django import template

import math


register = template.Library()

@register.filter()
def formatSeconds(s):
    hours = math.floor(s / 3600)
    mins = math.floor((s - (hours * 3600)) / 60);
    secs = math.floor(s - (hours * 3600) - ( mins * 60));
    if (hours > 0):
        return "%d:%0d:%02d" % (hours, mins, secs);
    return "%d:%02d" % (mins, secs);
