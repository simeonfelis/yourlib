#!/bin/bash

echo $0 " Starting nginx"
sudo systemctl start nginx.service

echo $0 " Starting rabbitmq broker"
sudo rabbitmq-server -detached

echo $0 " Starting celery"
python2 manage.py celery worker --loglevel=info

echo $0 "You have to run now 'python2 manage.py runserver' for local server, aptana to debug or 'uwsgi -x uwsgi.xml' for deployment"
