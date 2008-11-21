#!/usr/bin/env python
"""
Preproc.py

Preprocess NCBI database and produce and csv file: taxonomy.csv

USAGE:
    python preproc.py
"""
import sys
import os

if not os.path.exists( './names.dmp' ) and not os.path.exists( './nodes.dmp' ):
    if not os.path.exists( './taxdump.tar.gz' ):
        print "Downloading NCBI database on the web"
        os.system( "curl -# ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz > taxdump.tar.gz ")
        #os.system( "wget ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz" )
    print "Extracting database... please wait"
    os.system( "tar xf taxdump.tar.gz names.dmp nodes.dmp" )
 

NAMES = "names.dmp"
NODES = "nodes.dmp"

TBI = {}
TBN = {}

print "Generating structure..."
# Retrieving all scientific names
for line in file( NAMES ).readlines():
    id = line.split("|")[0].strip()
    name = line.split("|")[1].strip().lower()
    homonym = line.split("|")[2].strip().lower()
    type_name = line.split("|")[3].strip()
    synonym = "synonym" in type_name
    common = "common name" in type_name
    if type_name == "scientific name":
        # Creating TAXONOMY_BY_ID
        TBI[id] = {}
        if homonym:
            TBI[id]["name"] = homonym
        else:
            TBI[id]["name"] = name
        TBI[id]["common"] = []
        TBI[id]["homonym"] = []
        TBI[id]["synonym"] = []
        TBI[id]["parent"] = []
        TBI[id]["parents"] = []
        # Creating TAXONOMY_BY_NAME
        if homonym:
            TBN[homonym] = {}
            TBN[homonym]["id"] = id
            TBN[homonym]["homonym"] = name
        else:
            TBN[name] = {}
            TBN[name]["id"] = id

print "Adding synonyms, homonyms and common names..."
# Adding synonyms, homonyms and common names
for line in file( NAMES ).readlines():
    type_name = line.split("|")[3].strip()
    synonym = "synonym" in type_name
    common = "common name" in type_name
    homonym = line.split("|")[2].strip().lower()
    id = line.split("|")[0].strip()
    if synonym or common:
        name = line.split("|")[1].strip().lower()
        base_name = TBI[id]["name"]
        if synonym:
            if not TBN[base_name].has_key( "synonym" ):
                TBN[base_name]["synonym"] = []
            if not TBI[id].has_key( "synonym" ):
                TBI[id]["synonym"] = []
            TBN[base_name]["synonym"].append( name )
            TBI[id]["synonym"].append( name )
        if common:
            if not TBN[base_name].has_key( "common" ):
                TBN[base_name]["common"] = []
            if not TBI[id].has_key( "common" ):
                TBI[id]["common"] = []
            TBN[base_name]["common"].append( name )
            TBI[id]["common"].append( name )
    if type_name == "scientific name" and homonym:
        name = line.split("|")[1].strip().lower()
        TBI[id]["homonym"].append( name )


print "Extracting parents..."
for node in file( NODES ).readlines():
    id = node.split("|")[0].strip()
    parent = node.split("|")[1].strip()
    name = TBI[id]["name"]

    if not TBI.has_key( id ):
        TBI[id] = {}
    TBI[id]["parent"] = parent
    if not TBN.has_key( name ):
        TBN[name] = {}
    TBN[name]["parent"] = parent


def getParents( id ):
    global TBN, TBI
    lp = []
    while id != "1":
        id_parent = TBI[id]["parent"]
        lp.append( TBI[id_parent]["name"] )
        id = id_parent
    lp.reverse()
    return lp

    
print "Filling parents..."
for node in file( NODES ).readlines():
    id = node.split("|")[0].strip()
    TBI[id]["parents"] = getParents( id )

print "Generating csv file..."
import os
open( "taxonomy.csv", "w" ).write("")
csv = open( "taxonomy.csv", "a" )
for species in TBI.keys():
    line = "%s|%s|%s|%s|%s|%s|%s\n" % ( 
      species, #id
      TBI[species]["name"],
      TBI[TBI[species]["parent"]]["name"],
      "!".join(TBI[species]["homonym"]),
      "!".join(TBI[species]["parents"]),
      "!".join(TBI[species]["synonym"]),
      "!".join(TBI[species]["common"]) )
    csv.write( line )

os.system( "rm taxdump.tar.gz" )
os.system( "rm names.dmp nodes.dmp" )
os.system( "mkdir ../phylocore/data" )
os.system( "mv taxonomy.csv ../phylocore/data" )

print "Done"