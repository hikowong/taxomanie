
import networkx as NX

class ReferenceTree( NX.DiGraph ):
    """
    This class is an directed graph which represente the hierarchy of the NCBI
    tree.

    Please, use the networkx (https://networkx.lanl.gov/wiki/QuickReference)
    reference for complete api documentation of this class.
    """
    
    TBN = None
    TBI = None

    def __init__( self ):
        super( ReferenceTree, self ).__init__()
        self.parents = {}
        if not self.TBN or not self.TBI:
            from tools.reference import TBI, TBN
            self.TBN = TBN
            self.TBI = TBI
        for taxon in self.TBN.iterkeys():
            try:
                parent = self.TBI[self.TBN[taxon]["parent"]]["name"]
            except:
                print taxon, self.TBN[taxon]
            self.add_edge( parent, taxon )

    def getParents( self, name ):
        """
        return parents list of name until the root node

        @name: string
        @return: list
        """
        if not self.parents.has_key( name ):
            self.parents[name] = []
            try:
                parent = self.predecessors( name )[0]
            except:
                raise RuntimeError, ">>> "+name
            while parent != "root":
                self.parents[name].append( parent )
                parent = self.predecessors( parent )[0]
            self.parents[name].append( "root" )
            self.parents[name].reverse()
        return self.parents[name]

    def getParent( self, name ):
        return self.predecessors( name )[0]


    def getCommonParent( self, name1, name2 ):
        """
        return the first common parent name of name1 and name2

        @name1: string
        @name2: string
        @return: string
        """
        parents_list1 = self.getParents( name1 )[:]
        parents_list1.reverse()
        parents_list2 = self.getParents( name2 )
        for parent1 in parents_list1:
            if parent1 in parents_list2:
                return parent1

    def getArborescence( self, nwk ):
        """
        Take a newick string, search in reference all parents names and
        return the tree and the name of root.

        @nwk : string
        @return: networkx.DiGraph and string
        """
        from lib.phylogelib import getTaxa
        tree = NX.DiGraph()
        taxa = [taxon.lower() for taxon in getTaxa( nwk ) ]
        for taxon in taxa:
            parents = self.getParents( taxon )[:]
            parents.reverse()
            for parent in parents:
                tree.add_edge( parent, taxon )
                taxon = parent
        return tree, parent

    """
    def getRoot( self, tree ):
        node = tree.nodes()[0]
        parent = tree.predecessors( node )[0]
        while parent:
            node = parent
            parent = tree.predecessors( node )
        return node
    """
     
class PhylogenicTree( object ):
    
    NCBI = "http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id="

    def __init__( self, nwk ):
        self.ref_tree = ReferenceTree()
        self.tree, self.root = self.ref_tree.getArborescence( nwk )

    def display( self, root = "",  mydepth = 0 ):
        """
        Pretty print of the tree.

        @tree: networkx.DiGraph
        """
        if not root:
            root = self.root
            print root
            print "|"
        for node in self.tree.successors( root ):
            depth = 0
            while depth != mydepth :
                print "| ",
                depth += 1
            subnodes = self.tree.successors( node )
            if subnodes:
                print "+-"+node
                self.display( node, depth + 1)
            else:
                print "+-["+node+"]"

    def displayHTML( self, root = "",  mydepth = 0 ):
        """
        Pretty print of the tree.

        @tree: networkx.DiGraph
        """
        end_ul = False
        if not root:
            print "<ul>"
            end_ul = True
            root = self.root
            print "<li><a href='"+self.NCBI+self.ref_tree.TBN[root]["id"]+"'>"+root+"</a></li>"
        for node in self.tree.successors( root ):
            depth = 0
            while depth != mydepth :
                depth += 1
            subnodes = self.tree.successors( node )
            print "<ul>"
            if subnodes:
                print "<li><a href='"+self.NCBI+self.ref_tree.TBN[node]["id"]+"'>"+node+"</a></li>"
                self.displayHTML( node, depth + 1)
            else:
                print "<li><a href='"+self.NCBI+self.ref_tree.TBN[node]["id"]+"'>"+node+"</a></li>"
            print "</ul>"
        if end_ul:
            print "</ul>"
            end_ul = False


if __name__ == "__main__":
#    taxonomy =  ReferenceTree()
#    print taxonomy.getParents( "rattus" )
#    print taxonomy.getCommonParent( "bos", "rattus" )

    
    tree = """((((Bos:0.037413,Canis:0.017881):0.002871,(((Homo:0,Pan:0.001478):0.003588,Macaca:0.006948):0.012795,((Mus:0.031070,Rattus:0.016167):0.055242,Oryctolagus:0.050478):0.002924):0.002039):0.005355,Dasypus:0.033681):0.002698,(Echinops:0.076122,Loxodonta:0.025376):0.0
    07440,Monodelphis:0.093131);"""
    ptree = PhylogenicTree( tree )
    ptree.displayHTML()
    
