#!/usr/bin/env python

import os.path

print "cleaning old version..."
os.system( "rm -rf src" )
print "updating new version..."
os.system( "svn update" )
print "generating taxonomy.csv"
os.chdir( "src/tools" )
os.system( "python preproc.py" )
os.chdir( "../.." )
print "Taxomanie installed"
