
from phylogenictree import PhylogenicTree
from taxobject import Taxobject

class TreeCollection( Taxobject ):
    """
    Manipulate phylogenic tree collection:
        - filtering
        - query
        - diplay
        ...
    """
    
    def __init__( self, collection, reference ):
        """
        @collection (string): collection in phylip or nexus format
        """
        #super( TreeCollection, self ).__init__()
        self.reference = reference
        self.collection = []
        # Nexus collection
        if collection[:6].lower() == "#nexus":
            for tree in collection.split(";")[1:-2]:
                tree = tree.strip()
                nwktree = tree.split("=")[1].strip()
                tree_name = tree.split("=")[0].split()[1].strip()
                self.collection.append( {
                    "name": tree_name,
                    "tree": PhylogenicTree(nwktree, self.reference)
                  })
        # Phylip collection
        else:
            index = 0
            for nwktree in collection.strip().split(";"):
                nwktree = nwktree.strip()
                if nwktree:
                    index += 1
                    self.collection.append( {
                      "name": index,
                      "tree":PhylogenicTree(nwktree, self.reference)
                    } )
 
    def __eval_query( self, query ):
        a = []
        for i in [i.strip() for i in query.split("#") if i]:
            if i[0] not in ["=", "<", ">"]:
                a.append( "len("+i+")" )
            else:
                a.append(i)
        print " ".join(a)
        return eval( " ".join( a ) )

    def query( self, query ):
        """
        filter the collection with query. The query must be a string like
        this:
            #genre1# > 3 and #genre2# = 2...

        @query (string): the query which will filter the collection
        @new_list (list): the filtered collection
        """
        new_list = []
        for tree in self.collection:
            a = []
            for pattern  in [i.strip() for i in query.split("#") if i]:
                if pattern[0] not in ["=", "<", ">"]:
                    index = 0
                    for taxon in tree["tree"].tree.nodes():
                        if "XXX" not in taxon:
                            taxon = taxon.split("|")[0]
                            if pattern in tree["tree"].ref_tree.getParents( taxon ):
                                index += 1
                    a.append( "len("+str(range( index ))+")" )
                else:
                    a.append( pattern )
            try:
                if eval( " ".join( a ) ):
                    new_list.append( tree )
            except SyntaxError, e:
                raise SyntaxError, "bad query %s" % e
                
        return new_list

if __name__ == "__main__":
    from referencetree import ReferenceTree
    col = """
((rattus, mus), homo);
((homo, mususus), (pan, rattus));
(homo, (mus, pan));
((mus, rattus),pan);
"""
    treecol = TreeCollection( col, ReferenceTree() )
#    treecol.display()
    for tree in treecol.collection:
        print tree["tree"].tree.nodes()
    print type(treecol.query( " sdfs#murinae#>1" ))
