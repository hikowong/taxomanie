
NAMES = "../data/taxonomy/names.dmp"
NODES = "../data/taxonomy/nodes.dmp"

TBI = {}
TBN = {}

for line in file( NAMES ).readlines():
    id = line.split("|")[0].strip()
    name = line.split("|")[1].strip().lower()
    synonym = line.split("|")[3].strip() == "synonym"
    if not synonym:
        TBI[id] = {}
        TBI[id]["name"] = name
        TBN[name] = {}
        TBN[name]["id"] = id

for line in file( NAMES ).readlines():
    id = line.split("|")[0].strip()
    name = line.split("|")[1].strip().lower()
    synonym = line.split("|")[3].strip() == "synonym"
    base_name = TBI[id]["name"]
    if synonym:
        if not TBN[base_name].has_key( "synonym" ):
            TBN[base_name]["synonym"] = []
        TBN[base_name]["synonym"].append( name )

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
TAXONOMY_BY_NAME = TBN
