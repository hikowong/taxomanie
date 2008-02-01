from referencetree import ReferenceTree
from lib.phylogelib import getTaxa

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
        self.nwk = nwk
        self.hasparents = None

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

    def display( self, target = "text", all_parents = False ):
        """
        @target (string): the target format (currently: text and html)
        @all_parents (boolean): show all parents... or just common parents
        @return (string): the representation of the phylogenic tree in the
            target format.
        """
        result = ""
        self.tree, self.root, miss_spelled = self.ref_tree.getArborescence( self.nwk )
        if miss_spelled:
            result += self.__displayMissSpelled( miss_spelled, target )
        if not self.root:
            self.hasparents = False
            return result
        else:
            self.hasparents = True
        if not all_parents:
            self.tree = self.__removeSingleParent( self.tree )
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
                result += "+-"+node+"\n"
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
            result += "<li><a href='"+self.NCBI+self.ref_tree.TAXONOMY[root]["id"]+"'>"+root+"</a></li>\n"
        for node in self.tree.successors( root ):
            depth = 0
            while depth != mydepth :
                depth += 1
            subnodes = self.tree.successors( node )
            result += "<ul>\n"
            if subnodes:
                result += "<li><a href='"+self.NCBI+self.ref_tree.TAXONOMY[node]["id"]+"'>"+node+"</a></li>\n"
                result += self.__displayHTML( node, depth + 1)
            else:
                result += "<li><a href='"+self.NCBI+self.ref_tree.TAXONOMY[node]["id"]+"'>"+node+"</a></li>\n"
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
    
    tree = """((((Bos:0.037413,Canis:0.017881):0.002871,(((Homo:0,Pan:0.001478):0.003588,Macaca:0.006948):0.012795,((Mus:0.031070,Rattus:0.016167):0.055242,Oryctolagus:0.050478):0.002924):0.002039):0.005355,Dasypus:0.033681):0.002698,(Echinops:0.076122,Loxodonta:0.025376):0.007440,Monodelphis:0.093131);"""
#    tree = """((((Bos:0.037413,Canis:0.017881):0.002871,(((Homo:0,Pan:0.001478):0.003588,Macaca:0.006948):0.012795,((Mus:0.031070,Ratus:0.016167):0.055242,Oryctolagu:0.050478):0.002924):0.002039):0.005355,Dasypus:0.033681):0.002698,(Echinops:0.076122,Loxodonta:0.025376):0.007440,Monodelph:0.093131);"""
    ptree = PhylogenicTree( tree )
    print ptree.display()
 