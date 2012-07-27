#!/bin/bash
#set -x

# http://www.derekschaefer.net/2011/06/07/nginx-django-yay/

CWD=$(cd `dirname $0` && pwd)

MYAPP=music
PIDFILE=/tmp/${MYAPP}_fcgi.pid
HOST=127.0.0.1
PORT=8080
OUTLOG=/tmp/TRACE_STD
ERRLOG=/tmp/TRACE_ERR
DAEMONIZE=false

echo "CWD:     " $CWD
echo "PIDFILE: " $PIDFILE
echo "HOST:    " $HOST
echo "PORT:    " $PORT
echo "OUTLOG:  " $OUTLOG
echo "ERRLOG:  " $ERRLOG

# Associate it with the settings file
#SETTINGS=$CWD/yourlib/settings.py
# Use a socket instead of host/port
#SOCKET=
# Maximum requests for a child to service before expiring

#METHOD=prefork
METHOD=threaded
# Maximum number of children to have idle
MAXSPARE=8
# Minimum number of children to have idle
MINSPARE=4
# Maximum number of children to spawn
MAXCHILDREN=20
#MAXREQ=
# Spawning method - prefork or threaded

cd "`dirname $0`"

echo "Now in " $(pwd)

function failure () {
  STATUS=$?;
  echo; echo "Failed $1 (exit code ${STATUS}).";
  exit ${STATUS};
}

function start_server () {
  python2 ./manage.py runfcgi pidfile=$PIDFILE \
    ${HOST:+host=$HOST} \
    ${PORT:+port=$PORT} \
    ${SOCKET:+socket=$SOCKET} \
    ${OUTLOG:+outlog=$OUTLOG} \
    ${ERRLOG:+errlog=$ERRLOG} \
    ${SETTINGS:+--settings=$SETTINGS} \
    ${MAXREQ:+maxrequests=$MAXREQ} \
    ${METHOD:+method=$METHOD} \
    ${MAXSPARE:+maxspare=$MAXSPARE} \
    ${MINSPARE:+minspare=$MINSPARE} \
    ${MAXCHILDREN:+maxchildren=$MAXCHILDREN} \
    ${DAEMONIZE:+damonize=$DAEMONIZE}
}

function stop_server () {
  kill `cat $PIDFILE` || failure "stopping fcgi"
  rm $PIDFILE
}

case "$1" in
  start)
    echo -n "Starting fcgi: "
    [ -e $PIDFILE ] && { echo "PID file exists."; exit; }
    start_server || failure "starting fcgi"
    echo "Done."
    ;;
  stop)
    echo -n "Stopping fcgi: "
    [ -e $PIDFILE ] || { echo "No PID file found."; exit; }
    stop_server
    echo "Done."
    ;;
  poll)
    [ -e $PIDFILE ] && exit;
    start_server || failure "starting fcgi"
    ;;
  restart)
    echo -n "Restarting fcgi: "
    [ -e $PIDFILE ] || { echo -n "No PID file found..."; }
    stop_server
    start_server || failure "restarting fcgi"
    echo "Done."
    ;;
  *)
    echo "Usage: $0 {start|stop|restart} [--daemonise]"
    ;;
esac

exit 0

