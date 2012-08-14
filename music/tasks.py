'''
Created on 12.08.2012

@author: simeon
'''

import os
from celery import task

from music.models import Song, User
from music.helper import dbgprint, add_song, update_song
from django.conf import settings

# Filesystem watcher
import pyinotify
#from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent

class ProcessInotifyEvent(pyinotify.ProcessEvent):

    def __init__(self):
        dbgprint( "INOTIFY ProcessInotifyEvent constructed")

    def process_IN_DELETE(self, event):
        dbgprint( "INOTIFY: IN_DELETE", event)
        fswatch_file_removed.delay(event)

    def process_IN_MOVED_FROM(self, event):
        dbgprint( "INOTIFY: IN_MOVED_FROM", event)
        # the case that the file was just moved on the same filesystem inside
        # a user's music folder is VERY COMPLICATED to handle in a way that
        # just the path of the song in the db is updated. therefore, I just
        # remove the db entry.
        fswatch_file_removed.delay(event)

    def process_IN_MOVED_TO(self, event):
        # see process_IN_MOVED_FROM
        dbgprint( "INOTIFY: IN_MOVED_TO", event)
        fswatch_file_written.delay(event)

    def process_IN_MODIFY(self, event):
        dbgprint( "INOTIFY: IN_MODIFY", event)

    def process_IN_CLOSE_WRITE(self, event):
        dbgprint( "INOTIFY: IN_CLOSE_WRITE", event)
        fswatch_file_written.delay(event)


# create filesystem watcher in seperate thread
wm       = pyinotify.WatchManager()
notifier = pyinotify.ThreadedNotifier(wm, ProcessInotifyEvent())
notifier.setDaemon(True)
notifier.start()
#mask     = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM
mask     = pyinotify.ALL_EVENTS
wdd      = wm.add_watch(settings.MUSIC_PATH, mask, rec=True, auto_add=True) # recursive = True, automaticly add new subdirs to watch
dbgprint("Notifier:", notifier, "status isAlive():", notifier.isAlive())


@task()
def fswatch_file_written(event):
    filepath = event.pathname
    filename = event.name
    filedir = event.path

    # determine username for file
    try:
        username = filedir[len(settings.MUSIC_PATH):].split(os.path.sep)[1]
    except:
        # ignore that file
        return

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # ignore that file
        return

    # determine what to do with the written file
    # maybe just update tags or add new song to db
    try:
        song = Song.objects.get(user=user, path_orig=filepath)
    except Song.DoesNotExist:
        add_song(filedir, [filename], user)
    else:
        update_song(song)

    dbgprint("fswatch_file_changed: ADDING SONG FOR USER", username, ":", os.path.join(filedir, filename))
    add_song(filedir, [filename], user)

@task()
def fswatch_file_removed(event):
    try:
        song = Song.objects.get(path_orig=event.pathname)
    except Song.DoesNotExist:
        pass
    else:
        dbgprint("fswatch_file_removed: deleting song entry", song)
        song.delete()

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

        dbgprint("Check existing files in music folder ", userdir)
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