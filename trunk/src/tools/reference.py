
NAMES = "../data/taxonomy/names.dmp"
NODES = "../data/taxonomy/nodes.dmp"

TBI = {}
TI = {}
TBN = {}

for line in file( NAMES ).readlines():
    id = line.split("|")[0].strip()
    name = line.split("|")[1].strip().lower()
    synonym = line.split("|")[3].strip() == "synonym"
    common = "common name" in line.split("|")[3].strip()
    if not TI.has_key( int(id) ):
        TI[int(id)] = []
    TI[int(id)].append( name )
    if not TI.has_key( name ):
        TI[name] = []
    TI[name].append( id )
    if not synonym and not common:
        TBI[id] = {}
        TBI[id]["name"] = name
        TBN[name] = {}
        TBN[name]["id"] = id

for line in file( NAMES ).readlines():
    id = line.split("|")[0].strip()
    name = line.split("|")[1].strip().lower()
    synonym = line.split("|")[3].strip() == "synonym"
    common = "common name" in line.split("|")[3].strip()
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


TAXONOMY_BY_ID = TBI
TAXONOMY_INDEX = TI
TAXONOMY_BY_NAME = TBN
