import os
from django.conf import settings as globals


# music files of each username. must have a subfolder for each user here
MUSIC_PATH             = os.path.join(globals.BASE_SERVER, 'music')

FILE_UPLOAD_TEMP_DIR   = os.path.join(globals.BASE_SERVER, 'uploads') # all user upload dumps
FILE_UPLOAD_USER_DIR   = os.path.join(globals.BASE_SERVER, 'useruploads') # user specific upload dumps
FILE_DOWNLOAD_USER_DIR = os.path.join(globals.BASE_SERVER, 'userdownloads') # prepared downloads will go there

