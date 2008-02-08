
from phylogenictree import PhylogenicTree

class TreeCollection( object ):
    """
    Manipulate phylogenic tree collection:
        - filtering
        - querry
        - diplay
        ...
    """
    
    def __init__( self, collection ):
        """
        @collection (string): collection in phylip or nexus format
        """
        # Nexus collection
        if collection[:6].lower() == "#nexus":
            for tree in collection.split(";")[1:-2]:
                tree = tree.strip()
                nwktree = tree.split("=")[1]
                tree_name = tree.split("=")[0].split()[1]
                self.collection.append( nwktree )
                self.named_tree[nwktree] = tree_name
        # Phylip collection
        else:
            self.collection = [col for col in collection.strip().split( ";" ) if col]
            self.named_tree = range(1, len(self.collection)+1 )
        self.phylogenictree_collection = [ PhylogenicTree( tree ) for tree in self.collection ]
#        self.phylogenictree_collection = {}
#        for tree in self.collection: 
#           self.phylogenictree_collection = PhylogenicTree( tree ) 
#
    def display( self ):
        for tree in self.phylogenictree_collection:
            print tree.display()

    def __eval_querry( self, querry ):
        a = []
        for i in [i.strip() for i in querry.split("#") if i]:
            if i[0] not in ["=", "<", ">"]:
                a.append( "len("+i+")" )
            else:
                a.append(i)
        return eval( " ".join( a ) )

    def querry( self, querry ):
        """
        filter the collection with querry. The querry must be a string like
        this:
            #genre1# > 3 and #genre2# = 2...

        @querry (string): the querry which will filter the collection
        @new_list (list): the filtered collection
        """
        new_list = []
        for tree in self.phylogenictree_collection:
            a = []
            for pattern  in [i.strip() for i in querry.split("#") if i]:
                if pattern[0] not in ["=", "<", ">"]:
                    index = 0
                    for taxon in tree.tree.nodes():
                        taxon = taxon.split("|")[0]
                        print "+++", taxon
                        if pattern in tree.ref_tree.getParents( taxon ):
                            index += 1
                    a.append( "len("+str(range( index ))+")" )
                else:
                    a.append( pattern )
            if eval( " ".join( a ) ):
                new_list.append( tree )
        return new_list

if __name__ == "__main__":
    col = """
((rattus, mus), homo);
((homo, mus), (pan, rattus));
(homo, (mus, pan));
((mus, rattus),pan);
"""
    treecol = TreeCollection( col )
    treecol.display()
    print treecol.querry( "#murinae#>1" )
