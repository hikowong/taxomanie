
import networkx as NX

class ReferenceTree( NX.DiGraph ):
    """
    This class is an directed graph which represente the hierarchy of the NCBI
    tree.

    Please, use the networkx (https://networkx.lanl.gov/wiki/QuickReference)
    reference for complete api documentation of this class.
    """
    
    taxoref = None

    def __init__( self ):
        super( ReferenceTree, self ).__init__()
        self.parents = {}
        if self.taxoref is None:
            from taxonomyreference import TaxonomyReference
            ReferenceTree.taxoref = TaxonomyReference( "tools/taxonomy.csv" )
            self.TAXONOMY = self.taxoref.TAXONOMY
        for taxon in self.TAXONOMY.iterkeys():
            parent = self.TAXONOMY[taxon]["parent"]
            self.add_edge( parent, taxon )

    def getParents( self, name ):
        """
        return parents list of name until the root node

        @name: string
        @return: list
        """
        if not self.parents.has_key( name ):
            self.parents[name] = []
            parent = self.predecessors( name )[0]
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
        taxa = [taxon.lower().strip() for taxon in getTaxa( nwk ) ]
        rel_dict = {}
        for taxon in taxa:
            related_name = self.taxoref.correct( taxon )
            if related_name:
                rel_dict[taxon] = related_name
                continue
            parents = self.getParents( taxon )[:]
            parents.reverse()
            for parent in parents:
                tree.add_edge( parent, taxon )
                taxon = parent
        return tree, parent, rel_dict

    def getRelatedTaxa( self, nwk ):
        from lib.phylogelib import getTaxa
        taxa = [taxon.lower() for taxon in getTaxa( nwk ) ]
        rel_dict = {}
        for taxon in taxa:
            related_name = self.taxoref.correct( taxon )
            if related_name:
                rel_dict[taxon] = related_name
        return rel_dict

