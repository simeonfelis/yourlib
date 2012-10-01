#!/bin/bash
set -e
LOGFILE=/home/http/webapps/yourlib/logs/guni.log
LOGDIR=$(dirname $LOGFILE)
NUM_WORKERS=3
# user/group to run as
USER=http
GROUP=http
ADDRESS=127.0.0.1:8002
PROJECT=/home/http/webapps/yourlib
cd $PROJECT
source /home/http/envs/yourlib/bin/activate
test -d $LOGDIR || mkdir -p $LOGDIR
python manage.py run_gunicorn -w $NUM_WORKERS --bind=$ADDRESS \
  --user=$USER --group=$GROUP --log-level=debug \
  --log-file=$LOGFILE 2>>$LOGFILE \
  --pid=/tmp/yourlib.pid \
  --daemon
