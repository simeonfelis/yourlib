'''
Created on 12.08.2012

@author: simeon
'''

import os
import magic
import zipfile
import shutil
from celery import task

from music.models import Song, Collection, User, Upload
from music.helper import dbgprint, add_song, update_song, get_tags
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
def rescan_task(user_id):

    user = User.objects.get(id=user_id)
    collection = Collection.objects.get(user=user)

    dbgprint("rescan requested by", user);

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

            if so_far > 0 and so_far % 2 == 0:
                collection.scan_status = str(so_far)
                collection.save()

        collection.scan_status = "finished"
        collection.save()
        dbgprint("Rescan of music folder", userdir, "done")

    except Exception, e:
        dbgprint("Error during rescan", e)
        collection.scan_status = "error"
        collection.save()

@task()
def upload_done(useruppath, userupdir, upload_status_id):

    upload_status = Upload.objects.get(id=upload_status_id)

    ################################# decompress ################################
    # determine file type, unzip or untar (.zip, .7z, [.tar].[gz|bz2|xz|lzma])
    # put deflates in tmp dir. I will use the user's specific django upload temp
    # TODO: check for tar bombs (expand root dir, xTB null file images)
    ############################################################################
    upload_status.step = "decompress"
    upload_status.step_status = 0
    upload_status.save()

    deflates = []
    magic_mime = magic.Magic(mime=True)
    mime = magic_mime.from_file(useruppath.encode('utf-8')) # Magic has problems with unicode?
    if "application/zip" == mime:
        # deflate
        todeflate = zipfile.ZipFile(useruppath, 'r')
        processed = 0
        step_status = 0
        old_status = 0
        amount = len(todeflate.namelist())
        for name in todeflate.namelist():
            extracted_to = todeflate.extract(name, userupdir)

            deflates.append(extracted_to)

            processed += 1
            step_status = int(processed*100/amount)
            if (old_status < step_status) and ((step_status % 3) == 0):
                    old_status = step_status
                    upload_status.step_status = step_status
                    upload_status.save()
                    dbgprint("Deflated", step_status, "%")
        todeflate.close()
    else:
        deflates.append(useruppath)

    # Suppose we have decompressed a zip, so there multiple files now, and
    # their paths will be stored as list in ''deflates''.

    ############################### structuring ################################
    # read tags, determine file paths, move files
    ############################################################################
    upload_status.step = "structuring"
    upload_status.step_status = 0
    upload_status.save()

    step_status = 0
    old_status = 0
    amount = len(deflates)
    processed = 0
    for defl in deflates:
        if not amount == 0:
            step_status = int(processed*100/amount)
        else:
            step_status = 1
        processed += 1

        if (old_status < step_status) and ((step_status % 3) == 0):
            dbgprint("Structuring:", step_status, "%")
            old_status = step_status
            upload_status.step_status = step_status
            upload_status.save()

        # there could be subdirectories in zips deflate list
        if os.path.isdir(defl):
            continue

        # It's only worth to have a look at files with following mimess
        mime = magic_mime.from_file(defl.encode('utf-8'))
        if mime == 'application/ogg':
            f_extension = 'ogg'
        elif mime == 'audio/mpeg':
            f_extension = 'mp3'
        else:
            dbgprint("Ignoring mime", mime, "on file", defl)
            continue

        try:
            tags = get_tags(defl)
        except Exception, e:
            dbgprint("Error reading tags on", defl, e)
            continue

        if tags == None:
            # ignore files that have no tags
            #dbgprint("File has no tags:", defl)
            continue

        # determine target location of deflate based on tags
        musicuploaddir = os.path.join(
                settings.MUSIC_PATH,
                upload_status.user.username,
                'uploads'
                )
        if not os.path.isdir(musicuploaddir):
            os.makedirs(musicuploaddir)


        # this filedir does not have to be unique
        filedir = os.path.join(
                musicuploaddir.encode('utf-8'),
                tags['artist'].replace(os.path.sep, '_'),
                tags['album'].replace(os.path.sep, '_')
                )

        if not os.path.isdir(filedir):
            # this could fail if filedir exists and is a file
            os.makedirs(filedir)

        filename = str(tags['track']) + ". " + \
                tags['title'].replace(os.path.sep, '_') + '.' + \
                f_extension

        filepath = os.path.join(filedir, filename)
        jj = 0
        exists = os.path.exists(filepath)
        while exists:
            filename = str(tags['track']) + ". " + \
                    tags['title'].replace(os.path.sep, '_') + str(jj) + '.' + \
                    f_extension

            filepath = os.path.join(filedir, filename)
            exists = os.path.exists(filepath)
            jj += 1

        #dbgprint("Moving deflate", defl, "to", filepath)
        shutil.move(defl, filepath)

    # we are done here. inotify signal handler will add a database entry,
    # based on the last filesystem change
    upload_status.delete()