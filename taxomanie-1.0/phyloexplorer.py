#!/usr/bin/python

import sys,os

def kill_process( process_name ):
    ps = os.popen( "ps aux|grep %s" % process_name )
    pid = None
    for line in ps.readlines():
        if "phyloexplorer/%s" % process_name in line:
            print line
            pid = line.split()[1]
    if pid:
        os.system( "kill -9 %s" % pid )

if len( sys.argv ) != 2:
    print """
phyloexplorer_server start|stop

    start : launch engines
    stop :  halt engines
"""
    sys.exit(0)

if sys.argv[1] == "start":
    print "Starting NCBI engine"
    os.system( "python phyloexplorer/runserver_ncbi.py &" )
    print "Starting ITIS engine"
    os.system( "python phyloexplorer/runserver_itis.py &" )
if sys.argv[1] == "stop":
    print "Halting NCBI engine"
    kill_process( "runserver_ncbi.py" )
    print "Halting ITIS engine"
    kill_process( "runserver_itis.py" )


