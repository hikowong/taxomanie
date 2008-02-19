
from taxonomyreference import TaxonomyReference
from lib.phylogelib import getTaxa, getBrothers, \
    getChildren, tidyNwk, removeBootStraps, checkNwk

class PhylogenicTree( object ):
    """
    This class represente an Phylogenic Tree. It take a newick file in
    constructor. This class provides all some basis methods to get information
    of the phylogenic tree.
    """
    
    NCBI = "http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id="
    ref_tree = None

    def __init__( self, nwk, reference = None ):
        """
        @nwk (string): string in newick format
        @reference (networkx.DiGraph): The reference tree of NCBI database
        """
        if self.ref_tree is None:
            if reference is None:
                PhylogenicTree.ref_tree = TaxonomyReference()
            else:
                PhylogenicTree.ref_tree = reference
        self.nwk = removeBootStraps( tidyNwk(nwk.lower()) )
        checkNwk( self.nwk )
#        self.nwk = ",".join([ " ".join(i.split()[:2]) for i in self.nwk.replace( "_", " ").split(",") ])
        self.root = "root"
        self._getArborescence()
        
    def _getArborescence( self, tree=None ):
        if tree is None:
            # Init attributes
            import networkx as NX
            self.tree = NX.DiGraph()
            tree = self.nwk
            self.children_name = []
            self.last_child = ""
            self.rel_name = {}
            self.miss_spelled = {}
        if getChildren( tree ):
            if tree == self.nwk:
                parent_name = self.root
            else:
                if not self.rel_name.has_key( tree ):
                    parent_name = self.ref_tree.getCommonParent(getTaxa(tree))
                else:
                    parent_name = self.rel_name[tree]
            for child in getChildren( tree ):
                if getChildren( child ): # child is a node
                    child_name = self.ref_tree.getCommonParent(getTaxa(child))
                    if child_name not in self.children_name:
                        self.children_name.append( parent_name )
                    # Rename child_name if already exists
                    index = 0
                    while child_name in self.children_name:
                        index += 1
                        child_name = child_name+"|"+str(index)
                    self.rel_name[child] = child_name
                    self.children_name.append( child_name )
                    self.last_child = child_name
                    self.tree.add_edge( parent_name, child_name )
                    self._getArborescence( tree = child )
                else: # child is a taxon
                    if not self.ref_tree.isValid( self.ref_tree.stripTaxonName(child) ):
                        child += "|XXX"
                    self.tree.add_edge( parent_name, child )


    def display( self ):
        """
        @return (string): the representation of the phylogenic tree
        """
        result = ""
        if not self.root:
            return result
        result += self.__display()
        return result

    def __linkList( self, my_list ):
        """
        Link all taxon in list with html
        """
        my_list =  [ item for item in my_list if self.ref_tree.TAXONOMY.has_key( item ) ]
        return str( [
          "<a href='"+self.NCBI+self.ref_tree.TAXONOMY[item]["id"]+\
              "'>"+item+"</a>" \
          for item in my_list ] )

    def __display( self, root = "",  mydepth = 0 ):
        """
        Pretty print of the tree in HTML.

        @root (string): parent name
        @mydepth (int): depth in the tree
        @return (string): the display in html format
        """
        result = ""
        if not root:
            root = self.root
            result += "<a class='genre' href='"+self.NCBI+ \
              self.ref_tree.TAXONOMY[root]["id"]+"'>"+root.capitalize()+"</a><br />\n"
            result += "|<br />\n"
        for node in self.tree.successors( root ):
            dispnode = node.split("|")[0].replace(self.ref_tree.delimiter, " ")
            bdnode = self.ref_tree.stripTaxonName( node.split("|")[0] )
            depth = 0
            while depth != mydepth :
                result += "| "
                depth += 1
            subnodes = self.tree.successors( node )
            if subnodes:
                if "XXX" in node:
                    result += "+-<font color='red'><b>"+dispnode.capitalize()+"</b></font><br />\n"
                else:
                    result += """+-<a id="%s" class="genre" onmouseover="go('%s')"
                      onmouseout="afficheDescURL('')" href="%s%s"> %s
                      </a><br />\n""" % (
                        self.ref_tree.TAXONOMY[bdnode]["id"],
                        bdnode.capitalize(),
                        self.NCBI,
                        self.ref_tree.TAXONOMY[bdnode]["id"],
                        dispnode.capitalize() )
                result += self.__display( node, depth + 1)
            else:
                if "XXX" in node:
                    result += "+-<font color='red'><b>"+dispnode.capitalize()+"</b></font><br />\n"
                else:
                    result += """+-<a id="%s" class="species" onmouseover="go('%s')"
                      onmouseout="afficheDescURL('')" href="%s%s"> %s
                      </a><br />\n""" % (
                        self.ref_tree.TAXONOMY[bdnode]["id"],
                        bdnode.capitalize(),
                        self.NCBI,
                        self.ref_tree.TAXONOMY[bdnode]["id"],
                        dispnode.capitalize() )
        return result

if __name__ == "__main__":
    
#    tree = """((((Bos:0.037413,Canis:0.017881):0.002871,(((Homo:0,Pan:0.001478):0.003588,Macaca:0.006948):0.012795,((Mus:0.031070,Rattus:0.016167):0.055242,Oryctolagus:0.050478):0.002924):0.002039):0.005355,Dasypus:0.033681):0.002698,(Echinops:0.076122,Loxodonta:0.025376):0.007440,Monodelphis:0.093131);"""
#    tree = """((((Bos:0.037413,Canis:0.017881):0.002871,(((Homo:0,Pan:0.001478):0.003588,Macaca:0.006948):0.012795,((Mus:0.031070,Ratus:0.016167):0.055242,Oryctolagu:0.050478):0.002924):0.002039):0.005355,Dasypus:0.033681):0.002698,(Echinops:0.076122,Loxodonta:0.025376):0.007440,Monodelph:0.093131);"""
    trees = ["((loxondonta africana,pan),homo)"]#, "((homo,mus),(ratus,pan))", "((mu,ratus),homo)"]

    for tree in trees:
        ptree = PhylogenicTree( tree )
        print tree
        print ptree.tree.edges()
        print ptree.miss_spelled
        print ptree.display("html")
        print "#"*10
     
