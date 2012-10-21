This project could be considered 0.1 stage. Use at your own risk!

Purpose
=======

I want to listen to __my__ music, that means to the files I posess. I have
a weak server (arm, atom) so I don't want to live recode stuff. I don't want
to use flash. html5 should be fine. And I want a user interface that does not
suck.

So I build a little webinterface to my music folder, that just plays directly
my files via the browser's <audio> tag. A decent browser will play oggs and mp3s
(like chrome). Furthermore, multiple users have their own music folder.

ATM I use the webinterface on a daily base with chromium. Firefox can't play mp3,
but works fine with oggs.

Features
========

 * Support for ogg and mp3 as source files
 * zip file upload
 * Password protected urls to music files
 * watch music folder
 * See [screenshots](https://github.com/simeonfelis/yourlib/wiki/screenshots)

Requires
========

chrome or firefox or any other that can play mp3/ogg music files natively.
iPhone did work, too.

Software Dependencies
=====================

If you plan to deploy only the django app "music" and not the whole django project, you
will need probably at least a django 1.4 release and the following further apps:

 * celery (comes with django-celery)

The music app relies on following python packages:

 * django-celery
 * mutagen (tagreader)
 * zipfile
 * pyinotify (python inotify bindings)
 * shutil (python shell utilities)

If you want want to deploy the whole project, you will also need:

 * python south (migrating django databases easily)

I recommend to create a virtualenv and vanilla python packages from easy_install or pip
for deployment. For deployment on windows you will need some hacks for the pyinotify
package: [pyinotify windows hack](http://www.themacaque.com/?p=803)

BSD-server deployment (like on openNAS) needs much more work. Patches welcome.


Deployment
==========

There are five services required that shouuld run as daemons:

 * webserver
 * database
 * django
 * celery
 * message broker

Webserver
---------

I use nginx as webserver. The webserver should be capable of handling X-Accel-Redirect
requests. An example nginx config is in this repo.

Database
--------

I use postgresql as database backend. sqlite3 won`t be enough, as the database must be
able to handle multiple connections. They are required for celery. Your can try sqlite3,
but this will result in unpredictable, slow and erronemous behaviour.

Django
------

I run django as wsgi server in a virtualenv with the help of guinicorn. An example
startup script is in this repo.

Celery
------

Celery administrates long-running tasks like library rescans are file upload processings
(unpacking zips, structuring and moving uploaded files). I use celeryd as daemon in the
same virtualenv as django. An example startup script is in this repo.

Message broker
--------------

I believe the message broker is a task queue manager, that queues tasks from celery. I use
rabbitmq. There is not much to configure. There should be a example systemd service file for
rabbitmq in this repo. See [celery rabbitmq docs](http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#rabbitmq)

Configuration
--------------

In all startup scripts and config files, you will have to set the correct paths. The  
``yourlib/settings_example.py``  
will be loaded by default and should work out of the box. Remember to set your own 
secret key, e.g. with ``pwgen -sy 50``.   
Next, you have to set the correct paths to your music folders in  
``music/settings.py``  
If the base music path is set to ``/path/to/music``, the music app will create user directories::

    /path/to/music/username1/....
    /path/to/music/username2/....


The directory ``/path/to/music`` will be watched by pyinotify for changes. If a song is added or
changed the library is automatically updated.

Furthermore you need an upload directory for temporary upload stuff. One is for tmp files
the other one for evaluted files. Use an actual file system, not tmpfs. And don't use ``/path/to/music/``,
otherwise the message queue will burst because of all the inotify events.

If you have a decent amount of songs (>8000), you will have to tune inotify:

    echo 1048576 > /proc/sys/fs/inotify/max_user_watches

Remember to make this setting somehow persistent across reboots. On older kernels this setting
might be burried somewhere in ``/sys/``.



Startup:
--------

Don't forget to run ``./manage.py syncdb`` (or when using south: ``./manage.py schemamigration music --init``)
and ``./manage.py collectstatic``. For starting the django wsgi with gunicorn and celery, see 
the startup scripts in the repo.

 * Do not expose the deployment to arbitrary or untrusted users. the zip-upload
   functionality does not check for tar bombs, songs are maybe exposed to other
   users and there are probably more security and privacy holes.

 * make sure the webserver completely owns all configured directories

 * You should not put your music in the media folder of the django project or app

 * You should use a big storage different to your django project folder and
   media folder that holds temporary upload stuff. Clean it yourself from time to time.

 * Neither the temporary upload folder nor the django project files should be
   accessible through the web server indexes.


Wishlist
========
 * Automatic conversion to mp3 and ogg to serve all files to major browsers equally
 * Server side playlist stream for puplic access
 * Playlist sharing within users, later server instances
 * Mobile device support (UI)
 * zip file upload (DONE)

