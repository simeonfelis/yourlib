'''
Created on 12.08.2012

@author: simeon
'''

import os
from celery import task

from music.models import Song
from music.helper import dbgprint, add_song
from django.conf import settings

@task()
def rescan_task(user, collection):

    try:
        userdir = os.path.join(settings.MUSIC_PATH, user.username)
        amount = 1  # less accurate, but avoid division by 0
        for root, dirs, files in os.walk(userdir):
            for filename in files:
                amount += 1
        dbgprint("Estimating effort:", amount);

        dbgprint("Check for orphans")
        for s in Song.objects.filter(user=user):
            if not os.path.isfile(s.path_orig):
                dbgprint("Deleting orphan entry", s.path_orig)
                s.delete()

        collection.scan_status = "0"
        collection.save()

        dbgprint("Rescan music folder ", userdir)
        processed = 0

        for root, dirs, files in os.walk(userdir):
            processed += add_song(root, files, user)
            so_far = int((processed*100)/amount)
            #dbgprint("we have processed so far", processed, "files (", so_far, ") from ", amount)

            if so_far > 0 and so_far % 5 == 0:
                # update status every 5 percent
                collection.scan_status = str(so_far)
                collection.save()

        collection.scan_status = "finished"
        collection.save()
        dbgprint("Rescan of music folder", userdir, "done")

    except Exception, e:
        dbgprint("Error during rescan", e)
        collection.scan_status = "error"
        collection.save()