
from lib.phylogelib import getBrothers, getTaxa


data = {'a':"ab", "b":"ab", "c":"ab", "d":"ab" }

t = "((a,b),(c,d))"

def getCommonParent(parent):
    return "ab"

def getInformalParent( l ):
    return "("+",".join( l )+")"

def getName( nwk ):
    pass

parents_name = {"(a,b)": "ab", '(c,d)':"ab"}

import lib.phylogelib as p
def arbo( tree, data ):
    if p.getChildren( tree ):
        for child in p.getChildren(tree):
            print ">>>", child
            print "g.add_edges(", tree, p.getTaxa(child), ")"
            if p.getChildren( child ):
                arbo( child, data )
         

"""
def arbo(tree, data):
    already_done = []
    nodes = []
    for taxon in getTaxa( tree ):
        parent = getInformalParent( getBrothers(tree, taxon ) )
        while parent != tree:
#            index = 0
#            parent_name = getCommonParent( parent )
#            while parent_name in nodes:
#                index += 1
#                parent_name = parent_name+str(index)
#            nodes.append( parent_name )
            print "g.add_egdes(", parent, taxon ,")"
            already_done.append( (parent,taxon) )
            taxon = parent
            if getInformalParent( getBrothers( tree, taxon ) ) == tree:
                if (tree,parent) not in already_done:
                    print "g.add_egdes(", tree, parent,")"
                    already_done.append( (tree,parent) )
            parent = getInformalParent( getBrothers( tree, taxon ) )
"""
arbo( t, data )
