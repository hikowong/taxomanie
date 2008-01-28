
NAMES = "../data/taxonomy/names.dmp"
NODES = "../data/taxonomy/nodes.dmp"

TBI = {}
TI = {}
TBN = {}

print "Generating structure..."
# Retrieving all scientific names
for line in file( NAMES ).readlines():
    id = line.split("|")[0].strip()
    name = line.split("|")[1].strip().lower()
    type_name = line.split("|")[3].strip()
    synonym = "synonym" in type_name
    common = "common name" in type_name
    if type_name == "scientific name":
        # Creating TAXONOMY_INDEX
        if not TI.has_key( int(id) ):
            TI[int(id)] = []
        TI[int(id)].append( name )
        if not TI.has_key( name ):
            TI[name] = []
        TI[name].append( id )
        # Creating TAXONOMY_BY_ID
        TBI[id] = {}
        TBI[id]["name"] = name
        TBI[id]["common"] = []
        TBI[id]["synonym"] = []
        TBI[id]["parent"] = []
        # Creating TAXONOMY_BY_NAME
        TBN[name] = {}
        TBN[name]["id"] = id

print "Adding synonyms and common names..."
# Adding synonyms, and common names
for line in file( NAMES ).readlines():
    type_name = line.split("|")[3].strip()
    synonym = "synonym" in type_name
    common = "common name" in type_name
    if synonym or common:
        id = line.split("|")[0].strip()
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

print "Creating parents..."
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

print "Generating csv file..."
import os
open( "taxonomy.csv", "w" ).write("")
csv = open( "taxonomy.csv", "a" )
for species in TBI.keys():
    line = "%s|%s|%s|%s|%s\n" % ( 
      species,
      TBI[species]["name"],
      TBI[TBI[species]["parent"]]["name"],
      "!".join(TBI[species]["synonym"]),
      "!".join(TBI[species]["common"]) )
    csv.write( line )


TAXONOMY_BY_ID = TBI
TAXONOMY_INDEX = TI
TAXONOMY_BY_NAME = TBN
