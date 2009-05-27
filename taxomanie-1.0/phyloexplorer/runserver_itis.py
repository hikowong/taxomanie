#!/usr/bin/env python

import wsgiserver
#This can be from cherrypy import wsgiserver if you're not running it standalone.
import os
import django.core.handlers.wsgi
from django.conf import settings
from phyloconf import ITIS_PORT, IP

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'itis.settings'
    print "===",settings.TAXONOMY_ENGINE,"==="
    server = wsgiserver.CherryPyWSGIServer(
        (IP, ITIS_PORT),
        django.core.handlers.wsgi.WSGIHandler(),
        #server_name='django.example',
        numthreads = 20,
    )
    print "Server launched. See Phyloexplorer in action at :\n    http://%s:%s/phyloexplorer" % (IP, ITIS_PORT)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()