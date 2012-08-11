import os, sys, time
import magic    # file mime type detection
import zipfile
import shutil   # move, copy files and directories

# Filesystem watcher
import pyinotify
#from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent

import django.dispatch
from django.conf import settings
from django.contrib.auth.models import User

# You must not import anything from music.models
from music.models import Song, Upload, Playlist
from music.helper import dbgprint, add_song, get_tags

# declare and create signals
rescan_start = django.dispatch.Signal(providing_args=['user'])
upload_done  = django.dispatch.Signal(providing_args=['handler', 'request'])
download_start = django.dispatch.Signal(providing_args=['request'])

class ProcessInotifyEvent(pyinotify.ProcessEvent):

    def __init__(self):
        self.stacktrace = None
        dbgprint( "INOTIFY ProcessInotifyEvent constructed")

    # not all of these are filtered on watchmanager creation
    def process_IN_DELETE(self, event):
        self.song_removed(event)

    def process_IN_MOVED_FROM(self, event):
        # TODO: check if moved out of MUSIC_PATH
        self.song_removed(event)

    def process_IN_MOVED_TO(self, event):
        # TODO: check if moved out of MUSIC_PATH
        dbgprint( "INOTIFY: IN_MOVED_TO", event)
        self.song_changed(event)

    def process_IN_MODIFY(self, event):
        dbgprint( "INOTIFY: IN_MODIFY", event)

    def process_IN_CREATE(self, event):
        dbgprint( "INOTIFY: IN_CREATE", event)
        if os.path.isfile(event.pathname):
            self.song_changed(event)

    def process_IN_CLOSE_WRITE(self, event):
        dbgprint( "INOTIFY: IN_CLOSE_WRITE", event)
        self.song_changed(event)

    def song_removed(self, event):
        try:
            song = Song.objects.get(path_orig=event.pathname)
        except Song.DoesNotExist:
            pass
        else:
            dbgprint("INOTIFY: deleting song entry", song)
            song.delete()

    def song_changed(self, event):
        filedir = event.path
        filename = os.path.split(event.pathname)[-1]
        dbgprint("filename:", filename)
        dbgprint("filedir[len]", filedir[len(settings.MUSIC_PATH):])
        username = filedir[len(settings.MUSIC_PATH):].split(os.path.sep)[1]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            dbgprint("INOTIFY: could not determine user for changed path:", event.path, "and pathname:", event.pathname, "and user", username)
        else:
            dbgprint("INOTIFY: ADDING SONG FOR USER", username, ":", os.path.join(filedir, filename))
            add_song(filedir, [filename], user)

# create filesystem watcher in seperate thread
wm       = pyinotify.WatchManager()
notifier = pyinotify.ThreadedNotifier(wm, ProcessInotifyEvent())
#notifier.setDaemon(True)
notifier.start()
#mask     = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM
mask     = pyinotify.ALL_EVENTS
wdd      = wm.add_watch(settings.MUSIC_PATH, mask, rec=True, auto_add=True) # recursive = True, automaticly add new subdirs to watch
dbgprint("Notifier:", notifier, "status isAlive():", notifier.isAlive())


def connect_all():
    """
    to be called from models.py
    """
    dbgprint("CONNECTING SIGNALS")
    rescan_start.connect(rescan_start_callback)
    upload_done.connect(upload_done_callback)
    download_start.connect(download_start_callback)

def upload_done_callback(sender, **kwargs):
    dbgprint("upload_done_callback: checking for notifier:", notifier)
    dbgprint("upload_done_callback: notifier alive:", notifier.isAlive())

    handler = kwargs.pop('handler')
    request = kwargs.pop('request')
    try:
        upload = handler.userUploadStatus
    except Exception, e:
        dbgprint("An error occured when determining upload state", e)
        dbgprint("upload_done_callback: empty file uploaded by:", request.user)
        return

    #################################  copying ################################
    dbgprint("Entering status copying")
    step_status = 0
    upload.step = "copying"
    upload.step_status = 0
    upload.save()

    f = handler.file
    # create user's upload dir
    uploaddir = os.path.join(
            settings.FILE_UPLOAD_USER_DIR,
            request.user.username
            )
    if not os.path.isdir(uploaddir):
        os.makedirs(uploaddir)

    # move temporary file to users's upload dir determine file name and path,
    # don't overwrite
    uploadpath = os.path.join(uploaddir, f.name)
    ii = 0
    while os.path.exists(uploadpath):
        uploadpath = os.path.join(
                uploaddir,
                f.name + "_" + str(ii)
                )
        ii += 1

    dbgprint("Copy-to location:", uploadpath, type(uploadpath))

    # now put the upload content to the user's location
    step_status = 0
    processed = 0
    amount = f.size
    chunk_size = 64*1024  # 64KB (django default) TODO: read maybe own setting
    dbgprint("Chunks:", amount)
    old_status = 0
    with open(uploadpath, 'wb+') as destination:
        for chunk in f.chunks():
            processed += chunk_size
            destination.write(chunk)
            step_status = int(processed*100/amount)
            if (old_status < step_status) and (step_status % 3 == 0):
                dbgprint("Chunks copied:", step_status, "%")
                upload.step_status = step_status
                upload.save()
                old_status = step_status
        destination.close()
    dbgprint("Uploaded file written to", uploadpath)

    ################################# decompress ################################
    # determine file type, unzip or untar (.zip, .7z, [.tar].[gz|bz2|xz|lzma])
    # put deflates in tmp dir. I will use the user's specific django upload temp
    # TODO: check for tar bombs (expand root dir, xTB null file images)
    ############################################################################
    upload.step = "decompress"
    upload.step_status = 0
    upload.save()

    deflates = []
    magic_mime = magic.Magic(mime=True)
    mime = magic_mime.from_file(uploadpath.encode('utf-8')) # Magic has problems with unicode?
    if "application/zip" == mime:
        # deflate
        todeflate = zipfile.ZipFile(uploadpath, 'r')
        processed = 0
        step_status = 0
        old_status = 0
        amount = len(todeflate.namelist())
        for name in todeflate.namelist():
            extracted_to = todeflate.extract(name, uploaddir)

            deflates.append(extracted_to)

            processed += 1
            step_status = int(processed*100/amount)
            if (old_status < step_status) and ((step_status % 3) == 0):
                    old_status = step_status
                    upload.step_status = step_status
                    upload.save()
                    dbgprint("Deflated", step_status, "%")
        todeflate.close()
    else:
        deflates.append(uploadpath)

    # Suppose we have decompressed a zip, so there multiple files now, and
    # their paths will be stored as list in ''deflates''.

    ############################### structuring ################################
    # read tags, determine file paths, move files
    ############################################################################
    upload.step = "structuring"
    upload.step_status = 0
    upload.save()

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
            upload.step_status = step_status
            upload.save()

        # there could be subdirectories in zips deflate list
        if os.path.isdir(defl):
            continue

        try:
            tags = get_tags(defl)
        except Exception, e:
            dbgprint("Error reading tags on", defl, e)
            continue

        if tags == None:
            dbgprint("Deflate has no tags:", defl)
            continue

        # determine target location of deflate based on tags
        musicuploaddir = os.path.join(
                settings.MUSIC_PATH,
                request.user.username,
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
                tags['mime'].strip('audio/')

        filepath = os.path.join(filedir, filename)
        jj = 0
        while os.path.exists(filepath):
            filename = str(tags['track']) + ". " + \
                    tags['title'].replace(os.path.sep, '_') + str(jj) + '.' + \
                    tags['mime'].strip('audio/')

            filepath = os.path.join(filedir, filename)
            exists = os.path.exists(filepath)
            jj += 1

        #dbgprint("Moving deflate", defl, "to", filepath)
        shutil.move(defl, filepath)

    # we are done here. inotify signal handler will add a database entry,
    # based on the last filesystem change
    upload.delete()

def download_start_callback(sender, **kwargs):
    request = kwargs.pop("request")
    playlist_id = request.POST.get("playlist_id")
    playlist = Playlist.objects.get(user=request.user, id=playlist_id)
    upload = Upload(user=request.user, step="preparing", step_status=0)

    # create file list
    to_compress = []
    for item in playlist.items.all():
        path = item.song.path_orig.encode('utf-8')
        to_compress.append(path)
    # determine zipfile path
    zipname = playlist.name.replace(os.path.sep, "_").encode('utf-8') + ".zip"
    zipdir = os.path.join(settings.FILE_DOWNLOAD_USER_DIR, request.user.username)
    if not os.path.isdir(zipdir):
        os.makedirs(zipdir)

    zippath = os.path.join(zipdir, zipname)
    if os.path.isfile(zippath):
        os.remove(zippath)

    upload.step="compressing"
    upload.save()

    amount = len(playlist.items.all())
    processed=0
    newzip = zipfile.ZipFile(zippath, mode="w")
    for songpath in to_compress:
        dbgprint("Adding", songpath, type(songpath), os.path.exists(songpath))
        newzip.write(songpath)
        processed += 1
        step_status = int(processed*100/amount) # amount won't be 0
        if step_status % 3 == 0:
            upload.step_status = step_status
            upload.save()

    newzip.close()

    upload.step="finished"
    upload.step_status = 0
    upload.save()


