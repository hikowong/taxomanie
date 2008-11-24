import wsgiserver
#This can be from cherrypy import wsgiserver if you're not running it standalone.
import os
import django.core.handlers.wsgi

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    ip = '127.0.0.1'
    port = 8000
    server = wsgiserver.CherryPyWSGIServer(
        (ip, port),
        django.core.handlers.wsgi.WSGIHandler(),
        #server_name='django.example',
        numthreads = 20,
    )
    print "Server launched. See Phyloexplorer in action at :\n    http://%s:%s/phyloexplorer" % (ip, port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
