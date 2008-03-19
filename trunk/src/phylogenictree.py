
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
    reference = None

    def __init__( self, nwk, reference = None ):
        """
        @nwk (string): string in newick format
        @reference (networkx.DiGraph): The reference tree of NCBI database
        """
        if self.reference is None:
            if reference is None:
                PhylogenicTree.reference = TaxonomyReference()
            else:
                PhylogenicTree.reference = reference
        self.nwk = removeBootStraps( tidyNwk(nwk.lower()) )
        checkNwk( self.nwk )
#        self.nwk = ",".join([ " ".join(i.split()[:2]) for i in self.nwk.replace( "_", " ").split(",") ])
        self.root = "root"
        self.nb_taxa = 0
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
                    parent_name = self.reference.getCommonParent(getTaxa(tree))
                else:
                    parent_name = self.rel_name[tree]
            for child in getChildren( tree ):
                if getChildren( child ): # child is a node
                    child_name = self.reference.getCommonParent(getTaxa(child))
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
                    if not self.reference.isValid( self.reference.stripTaxonName(child) ):
                        child += "|XXX"
                    self.nb_taxa += 1
                    self.tree.add_edge( parent_name, child )

    def display( self, tree = None ):
        """
        @return (string): the representation of the phylogenic tree
        """
        result = ""
        if not self.root:
            return result
        if tree:
            result += self.__display( tree = tree )
        else:
            result += self.__display( tree = self.tree )
        return result

    def __display( self, tree, root = "",  mydepth = 0, lastnode = 'root', blockname = "" ):
        """
        Pretty print of the tree in HTML.

        @root (string): parent name
        @mydepth (int): depth in the tree
        @return (string): the display in html format
        """
        result = ""
        blocknum = 0
        if not root:
            root = self.root
            result += "<a class='genre' name='genre' href='"+self.NCBI+ \
              self.reference.TAXONOMY[root]["id"]+"'>"+root.capitalize()+"</a><br />\n"
            result += "|<br />\n"
        for node in tree.successors( root ):
            dispnode = node.split("|")[0].replace(self.reference.delimiter, " ")
            bdnode = self.reference.stripTaxonName( node.split("|")[0] )
            nb_inter_parents = 0
            if lastnode in self.reference.getParents( bdnode ):
                inter_parents = self.reference.getIntervalParents( lastnode, bdnode )
                nb_inter_parents = len( inter_parents )
                blocknum += 1
                blockname += str( blocknum )
                result += "<div id='%s' class='interparents'><tt>" % blockname
                if len( inter_parents ):
                    result += "| "*mydepth
                    result +=  ("| "*mydepth).join(
                      self.__linkGenre(i,i,blockname) for i in inter_parents ) 
                result += "</tt></div>" 
            depth = 0
            while depth != mydepth :
                result += "| "
                depth += 1
            subnodes = tree.successors( node )
            if subnodes: # it's a genre
                result += self.__linkGenre( dispnode, bdnode, blockname, True, nb_inter_parents)
                result += self.__display( tree,  node, depth + 1, 
                  lastnode = bdnode, blockname = blockname+"a")
            else: # it's a species (ie taxon)
                if "XXX" in node and not self.reference.isHomonym( bdnode ):
                    result += "+-<font color='red'><b>"+dispnode.capitalize()+"</b></font><br />\n"
                elif self.reference.isHomonym( bdnode ):
                    result += "+-<font color='orange'><b>"+dispnode.capitalize()+"</b></font><br />\n"
                else:
                    result += self.__linkSpecies( dispnode, bdnode, blockname, nb_inter_parents)
        return result


    def __linkSpecies( self, dispnode, bdnode, blockname, nb_inter_parents ):
        result = ""
        if self.reference.isHomonym( bdnode ):
            style = 'class="species_homonym"'
        else:
            style = 'class="species"'
        result += """+-<a id="%s" %s onmouseover="go('%s');" target='_blank' href="%s%s"> %s</a>""" % (
          self.reference.TAXONOMY[bdnode]["id"],
          style,                        
          bdnode.capitalize(),
          self.NCBI,
          self.reference.TAXONOMY[bdnode]["id"],
          dispnode.capitalize() )
        if nb_inter_parents:
            result += """<a id="a-%s" class='showparents'
              onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
                blockname,
                blockname )
        else:
            result += "<br />\n"
        return result

    def __linkGenre( self, dispnode, bdnode, blockname, isinterparent=False, nb_inter_parents=0 ):
        result = ""
        result += """+-<a id="%s" class="genre" name="genre" onmouseover="go('%s')" 
          href="%s%s" target='_blank'> %s </a>""" % (
          self.reference.TAXONOMY[bdnode]["id"],
          bdnode.capitalize(),
          self.NCBI,
          self.reference.TAXONOMY[bdnode]["id"],
          dispnode.capitalize())
        if isinterparent and nb_inter_parents:
            result += """<a id="a-%s" class='showparents'
              onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
                blockname,
                blockname )
        else:
            result += "<br />\n"
        return result
 

if __name__ == "__main__":
    
#    tree = """((((Bos:0.037413,Canis:0.017881):0.002871,(((Homo:0,Pan:0.001478):0.003588,Macaca:0.006948):0.012795,((Mus:0.031070,Rattus:0.016167):0.055242,Oryctolagus:0.050478):0.002924):0.002039):0.005355,Dasypus:0.033681):0.002698,(Echinops:0.076122,Loxodonta:0.025376):0.007440,Monodelphis:0.093131);"""
#    tree = """((((Bos:0.037413,Canis:0.017881):0.002871,(((Homo:0,Pan:0.001478):0.003588,Macaca:0.006948):0.012795,((Mus:0.031070,Ratus:0.016167):0.055242,Oryctolagu:0.050478):0.002924):0.002039):0.005355,Dasypus:0.033681):0.002698,(Echinops:0.076122,Loxodonta:0.025376):0.007440,Monodelph:0.093131);"""
    trees = ["((loxondonta africana,pan),homo)"]#, "((homo,mus),(ratus,pan))", "((mu,ratus),homo)"]

    tree = PhylogenicTree( "((mus, rattus), pan, (bos, canis))" )
    print tree.display()

    print "<hr />"
    xtree = tree.reference.getNCBIArborescence( ["mus", "rattus", "bos", "canis" ])
    #print type( xtree )
    print tree.display( xtree )

#    for tree in trees:
#        ptree = PhylogenicTree( tree )
#        print tree
#        print ptree.tree.edges()
#        print ptree.miss_spelled
#        print ptree.display()
#        print "#"*10
#    

     
