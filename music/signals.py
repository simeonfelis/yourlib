import os

import django.dispatch
from django.conf import settings

# You must not import anything from music.models
from music.models import Song
from music.helper import dbgprint, add_song

# declare and create signals
rescan_start = django.dispatch.Signal(providing_args=['user'])

def connect_all():
    """
    to be called from models.py
    """
    dbgprint("CONNECTING SIGNALS")
    rescan_start.connect(rescan_start_callback)

################## Signal handler for rescan
# django doc says: "You can put signal handling and registration code
# anywhere you like. However, you'll need to make sure that the module
# it's in gets imported early on so that the signal handling gets
# registered before any signals need to be sent."
# but these signals here aren't expected to registered early.

def rescan_start_callback(sender, **kwargs):

    user = kwargs.pop("user")
    collection = kwargs.pop("collection")

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


