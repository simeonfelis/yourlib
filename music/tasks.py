'''
Created on 12.08.2012

@author: simeon
'''

import os
import pyinotify
import magic
import zipfile
import shutil

from celery import task
import celery.exceptions as CeleryExceptions

from django.db import transaction

from music.models import Song, Collection, User, Upload
from music.helper import dbgprint, add_song, update_song, get_tags, UserStatus
from music import settings

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
notifier = pyinotify.ThreadedNotifier(wm, ProcessInotifyEvent(), read_freq=0)
notifier.setDaemon(True)
notifier.start()
#mask     = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_DELETE | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM
mask     = pyinotify.ALL_EVENTS
wdd      = wm.add_watch(settings.MUSIC_PATH, mask, rec=True, auto_add=True) # recursive = True, automaticly add new subdirs to watch


@task(ignore_result=True, max_retries=10, default_retry_delay=10)
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
        try:
            song = Song.objects.get(user=user, path_orig=filepath)
        except Song.DoesNotExist:
            add_song(filedir, [filename], user)
        else:
            update_song(song)
    except CeleryExceptions.MaxRetriesExceededError:
        # well, whorses will have their trinkets
        print("fswatch_file_written giving up on file", event.pathname)
        return
    except Exception, exc:
        print("Exception in fswatch_file_written file", event.pathname)
        raise fswatch_file_written.retry(exc=exc, countdown=10)


@task(ignore_result=True, max_retires=10, default_retry_delay=10)
@transaction.autocommit
def fswatch_file_removed(event):
    try:
        song = Song.objects.get(path_orig=event.pathname)
    except Song.DoesNotExist:
        return
    try:
        dbgprint("fswatch_file_removed: deleting song entry", song)
        song.delete()

    except CeleryExceptions.MaxRetriesExceededError:
        # well, whorses will have their trinkets
        return
    except Exception, exc:
        raise fswatch_file_removed.retry(exc=exc, countdown=10)

@task(ignore_result=True)
def rescan_task(user_id, max_retires=2, default_retry_delay=10):

    user = User.objects.get(id=user_id)
    #collection = Collection.objects.get(user=user)
    user_status = helper.UserStatus(user)

    try:
        userdir = os.path.join(settings.MUSIC_PATH, user.username)

        #############    rescan preparations   ###################
        # estimating total effort: count users songs on filesystem and in db
        amount = 1  # less accurate, but avoid division by 0
        for root, dirs, files in os.walk(userdir):
            amount += len(files)

        songs = Song.objects.filter(user=user)

        amount += songs.count() # absolute amount
        processed = 0           # absolute progress
        so_far = 0              # progress in percent
        print ("rescan_task: user", user, "dir", userdir, "absolute amount", amount)

        ##############     check orphans     ##################
        for s in songs:
            if not os.path.isfile(s.path_orig):
                print("Deleting orphan entry", s.path_orig)
                s.delete()

            processed += 1
            if so_far > 0 and so_far % 1 == 0:
                user_status.set("rescan_status", "%i" % so_far)

        print ("rescan_task: user", user, "dir", userdir, "deleting orphans done")

        #############   check entrys in db if files have changed     ##############
        for root, dirs, files in os.walk(userdir):

            processed += add_song(root, files, user, force=True)

            so_far = int((processed*100)/amount)
            if so_far > 0 and so_far % 2 == 0:
                user_status.set("rescan_status", "%i" % so_far)

        user_status.set("rescan_status", "finished")

    except CeleryExceptions.MaxRetriesExceededError:
        print("MaxRetriesExceededError in rescan by user", user)
        # as stated already, whorses will have their trinkets
        try:
            user_status.set("rescan_status", "error")
        except:
            print("Giving up rescan for user", user)
            # ah, buckle off.
            pass
        return
    except Exception, exc:
        print("Exception in rescan for", user, exc)
        user_status.set("rescan_status", "error")
        raise rescan_task.retry(exc=exc, countdown=10)

@task(ignore_result=True)
@transaction.autocommit
def upload_done(user_id, upload_status_id, uploaded_file_path):
#def upload_done(useruppath, userupdir, upload_status_id):

    user = User.objects.get(id=user_id)
    upload_status = Upload.objects.get(id=upload_status_id)

    print("Entering status copying")
    step_status = 0


    # determine user upload dir
    userupdir = os.path.join(
                settings.FILE_UPLOAD_USER_DIR,
                user.username
                )
    # create user's upload dir
#    if not os.path.isdir(userupdir):
#        os.makedirs(userupdir)

    # move temporary file to users's upload dir determine file name and path,
    # don't overwrite
#    useruppath = os.path.join(userupdir, uploaded_file_name)
#    ii = 0
#    while os.path.exists(useruppath):
#        useruppath = os.path.join(
#                userupdir,
#                uploaded_file_name + "_" + str(ii)
#                )
#        ii += 1

#    print("Copy-to location:", useruppath, type(useruppath))
#    shutil.move(uploaded_file_path, uploaded_file_name)

    # now put the upload content to the user's location
#    step_status = 0
#    processed = 0
#    amount = upfile.size
#        helper.dbgprint("Chunks:", amount)
#        old_status = 0
#        with open(useruppath, 'wb+') as destination:
#            for chunk in upfile.chunks():
#                processed += upfile.DEFAULT_CHUNK_SIZE
#                destination.write(chunk)
#                step_status = int(processed*100/amount)
#                if (old_status < step_status) and (step_status % 2 == 0):
#                    helper.dbgprint("Chunks copied:", step_status, "%")
#                    userUploadStatus.step_status = step_status
#                    userUploadStatus.save()
#                    old_status = step_status
#            destination.close()
#        helper.dbgprint("Uploaded file written to", useruppath)




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
    mime = magic_mime.from_file(uploaded_file_path.encode('utf-8')) # Magic has problems with unicode?
    if "application/zip" == mime:
        # deflate
        todeflate = zipfile.ZipFile(uploaded_file_path, 'r')
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
                    try:
                        upload_status.save()
                    except:
                        pass
                    dbgprint("Deflated", step_status, "%")
        todeflate.close()
    else:
        deflates.append(uploaded_file_path)

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

        if (old_status < step_status) and ((step_status % 2) == 0):
            dbgprint("Structuring:", step_status, "%")
            old_status = step_status
            upload_status.step_status = step_status
            try:
                upload_status.save()
            except:
                pass

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
        if tags['artist']: artist = tags['artist'].replace(os.path.sep, '_')
        else:              artist = "UNKNOWN ARTIST"
        if tags['album']:  album  = tags['album'].replace(os.path.sep, '_')
        else:              album  = "UNKNOWN ALBUM"

        filedir = os.path.join(
                musicuploaddir, #.encode('utf-8'),
                artist,
                album
                )

        if not os.path.isdir(filedir):
            # this could fail if filedir exists and is a file
            os.makedirs(filedir)

        if tags['track']:  track = str(tags['track'])
        else:              track = '0'
        if tags ['title']: title = tags['title'].replace(os.path.sep, '_')
        else:              title = "UNKNOWN TITLE"
        filename = track + ". " + \
                title + '.' + \
                f_extension

        filepath = os.path.join(filedir, filename)
        jj = 0
        while os.path.exists(filepath):
            filename = track + ". " + \
                    title + str(jj) + '.' + \
                    f_extension

            filepath = os.path.join(filedir, filename)
            jj += 1

        #dbgprint("Moving deflate", defl, "to", filepath)
        shutil.move(defl, filepath)

    # we are done here. inotify signal handler will add a database entry,
    # based on the last filesystem change
    upload_status.delete()

