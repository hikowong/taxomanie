from referencetree import ReferenceTree
from lib.phylogelib import getTaxa, getBrothers, getChildren, tidyNwk

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
                PhylogenicTree.ref_tree = ReferenceTree()
            else:
                PhylogenicTree.ref_tree = reference
        self.nwk = tidyNwk(nwk.lower())
        self.hasparents = None
        #self.tree, self.root, self.miss_spelled = 
        self.root = "root"
        self._getArborescence()

    def getMissSpelled( self ):
        """
        @return (dict): dictionnary of all miss spelled taxon with all related
            taxon
        """
        taxa = [taxon.strip().lower() for taxon in getTaxa( self.nwk ) ]
        rel_dict = {}
        for taxon in taxa:
            related_name = self.ref_tree.taxoref.correct( taxon )
            if related_name:
                rel_dict[taxon] = related_name
        return rel_dict

    def getCommonParent( self, taxa_list ):
        """
        return the first common parent of taxa_list

        @taxa_list: list
        @return: string
        """
        dict_parents = {}
        parents_list1 = self.ref_tree.getParents( taxa_list[0] )
        parents_list2 = self.ref_tree.getParents( taxa_list[1] )
        all_common_parents = [parent for parent in parents_list1 if parent in parents_list2]
        if len( taxa_list ) > 2:
            for i in range( len( taxa_list) ):
                for j in range(i, len( taxa_list ) ):
                    if i == j or (i == 0 and j == 1):
                        continue
                    parents_list1 = self.ref_tree.getParents( taxa_list[i] )
                    parents_list2 = self.ref_tree.getParents( taxa_list[j] )
                    common_parents = [parent for parent in parents_list1 if parent in parents_list2]
                    all_common_parents = [parent for parent in common_parents\
                      if parent in (common_parents and all_common_parents)]
        return all_common_parents[-1]

    def _getArborescence( self, tree=None ):
        if tree is None:
            # Init attributes
            import networkx as NX
            self.tree = NX.DiGraph()
            tree = self.nwk
            print ">>", tree
            self.children_name = []
            self.last_child = ""
            self.rel_name = {}
            self.miss_spelled = {}
            # Check all taxa name
            bad = False
            for taxon in getTaxa( self.nwk ):
                related_name = self.ref_tree.taxoref.correct( taxon )
                if related_name:
                    bad = True
                    self.miss_spelled[taxon] = related_name
            if bad:
                return
        if getChildren( tree ):
            if tree == self.nwk:
                parent_name = self.root
            else:
                if not self.rel_name.has_key( tree ):
                    parent_name = self.getCommonParent(getTaxa(tree))
                else:
                    parent_name = self.rel_name[tree]
            for child in getChildren( tree ):
                if getChildren( child ): # child is a node
                    child_name = self.getCommonParent(getTaxa(child))
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
                    self.tree.add_edge( parent_name, child )
     
    def display( self, target = "text" ):
        """
        @target (string): the target format (currently: text and html)
        @return (string): the representation of the phylogenic tree in the
            target format.
        """
        result = ""
        if self.miss_spelled:
            return self.__displayMissSpelled( self.miss_spelled, target )
        if not self.root:
            self.hasparents = False
            return result
        else:
            self.hasparents = True
        if target == "text":
            result += self.__display()
        elif target == "html":
            result += self.__displayHTML()
        else:
            raise ValueError, "Unknow target %s" % target
        return result

    def __linkList( self, my_list ):
        """
        Link all taxon in list with html
        """
        my_list = self.__purgeList( my_list )
        return str( [
          "<a href='"+self.NCBI+self.ref_tree.TAXONOMY[item]["id"]+\
              "'>"+item+"</a>" \
          for item in my_list ] )

    def __purgeList( self, my_list ):
        """
        Remove all non-scientific name in list

        @return (list): the purged list
        """
        return [ item for item in my_list if self.ref_tree.TAXONOMY.has_key( item ) ]

    def __displayMissSpelled( self, miss_spelled_dict, target ):
        """
        @return (string): display all miss spelled taxon and show all
            propositions of correct name
        """
        output = ""
        for i,j in miss_spelled_dict.iteritems():
            try:
                if target == "html":
                    output += "<li>"+i+" not found. Do you mean "+self.__linkList(j)+"</li>\n"
                else:
                    output += "* "+i+" not found. Do you mean "+\
                      str( self.__purgeList( j ) )+"\n"
            except KeyError:
                pass
        return output

    def __display( self, root = "",  mydepth = 0 ):
        """
        Pretty print of the tree.

        @root (string): parent name
        @mydepth (int): depth in the tree
        @return (string): the display in text format
        """
        result = ""
        if not root:
            root = self.root
            result += root+"\n"
            result += "|\n"
        for node in self.tree.successors( root ):
            depth = 0
            while depth != mydepth :
                result += "| "
                depth += 1
            subnodes = self.tree.successors( node )
            if subnodes:
                result += "+-"+node.split("|")[0]+"\n"
                result += self.__display( node, depth + 1)
            else:
                result += "+-["+node+"]\n"
        return result

    def __displayHTML( self, root = "",  mydepth = 0 ):
        """
        Pretty print of the tree.


        @root (string): parent name
        @mydepth (int): depth in the tree
        @return (string): the display in html format
        """
        result = ""
        end_ul = False
        if not root:
            result += "<ul>\n"
            end_ul = True
            root = self.root
            result += "<li><a href='"+self.NCBI+self.ref_tree.TAXONOMY[root]["id"]+"'>"+root.upper()+"</a></li>\n"
        for node in self.tree.successors( root ):
            dispnode = node.split("|")[0]
            depth = 0
            while depth != mydepth :
                depth += 1
            subnodes = self.tree.successors( node )
            result += "<ul>\n"
            if subnodes:
                result += "<li><a href='"+self.NCBI+self.ref_tree.TAXONOMY[dispnode]["id"]+"'>"+dispnode.upper()+"</a></li>\n"
                result += self.__displayHTML( node, depth + 1)
            else:
                result += "<li><a href='"+self.NCBI+self.ref_tree.TAXONOMY[dispnode]["id"]+"'>"+dispnode.upper()+"</a></li>\n"
            result += "</ul>\n"
        if end_ul:
            result += "</ul>\n"
            end_ul = False
        return result

    def __removeSingleParent( self, tree ):
        """
        @tree (networkx.DiGraph): tree where removing parents
        @return (networkx.DiGraph): the elaged tree
        """
        for node in tree:
            n = tree.predecessors( node ) + tree.successors(node)
            if len(n) == 2:
                tree.delete_edge( n[0], node )
                tree.delete_edge( node, n[1] )
                tree.add_edge( n[0], n[1] )
        return tree

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
     
