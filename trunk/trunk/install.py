#!/usr/bin/env python

import os.path

os.system( "mv src/phyloexplorer.conf ." )
print "cleaning old version..."
os.system( "rm -rf src" )
print "updating new version..."
os.system( "svn update" )
os.system( "mv phyloexplorer.conf src" )
print "generating taxonomy.csv"
os.chdir( "src/tools" )
os.system( "python preproc.py" )
os.chdir( "../.." )
print "PhyloExplorer installed"
