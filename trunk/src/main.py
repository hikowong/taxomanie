
def isInTree( taxa, tree ):
    pass

def generateTree( tree ):
    finaltree = {}
    # On récupère la liste des taxa

    for taxon in taxa:
        if isInTree( taxa, finaltree ):
            addTaxa( taxa, finaltree )
        else:
            pass
            # on insère le taxon au bon endroit
    # Pour chaque taxon, on recupère son père
    

def setVal( val ):
    val = val.replace( "(", "[" ).replace( ")", "]" )
    val = val.replace( ",", "','" ).replace( "]',", "]," ).replace(",'[",",[")
    val = val.replace("[","['").replace( "['[", "[[" )
    val = val.replace( "]", "']" ).replace( "]']", "]]")
    val = val.replace("['[", "[[" )
    val = val.replace("]']", "]]" )
    return eval( val )

l = "((((Bos,Canis),(((Homo,Pan),Macaca),((Mus,Rattus),Oryctolagu))),Dasypus),(Echinops,Loxodonta))"
print setVal( l )[0]
