
from phylogenictree import PhylogenicTree
from taxobject import Taxobject
from lib.phylogelib import getTaxa
import re

class TreeCollection( Taxobject ):
    """
    Manipulate phylogenic tree collection:
        - filtering
        - query
        - diplay
        ...
    """
    
    def __init__( self, nwk_collection, reference ):
        """
        @nwk_collection (string): collection in phylip or nexus format
        """
        #super( TreeCollection, self ).__init__()
        self.reference = reference
        self.collection = []
        # Nexus collection
        if nwk_collection[:6].lower() == "#nexus":
            for tree in nwk_collection.split(";")[1:-2]:
                tree = tree.strip()
                nwktree = tree.split("=")[1].strip()
                tree_name = tree.split("=")[0].split()[1].strip()
                self.collection.append( {
                    "name": tree_name,
                    "tree": self.__tagBadTaxon(nwktree),
                  })
        # Phylip collection
        else:
            index = 0
            for nwktree in nwk_collection.strip().split(";"):
                nwktree = nwktree.strip()
                if nwktree:
                    index += 1
                    self.collection.append( {
                      "name": index,
                      "tree": self.__tagBadTaxon(nwktree),
                    } )

    def __tagBadTaxon( self, nwk ):
        taxa_list = getTaxa( nwk )[:]
        for taxon in taxa_list:
            if not self.reference.isValid( taxon ):
                nwk = nwk.replace( taxon, taxon+"|XXX" )
        return nwk
 
    def __eval_query( self, query, tree ):
        res = ""
        for pattern in re.findall("{([^}]+)}", query):
            index = 0
            for taxon in getTaxa(tree["tree"]):
                if "XXX" not in taxon:
                    taxon = taxon.split("|")[0].strip()
                    if pattern in self.reference.getParents( taxon ):
                        index += 1
            res = query.replace("{"+pattern+"}", str(index) )
        if res:
            return eval( res )
        raise SyntaxError, "bad query %s" % query

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
            try:
                if self.__eval_query( query, tree ):
                    new_list.append( tree )
            except SyntaxError, e:
                raise SyntaxError, "bad query %s" % e
        return new_list

if __name__ == "__main__":
    from taxonomyreference import TaxonomyReference
    col = """
((rattus, pan), homo);
((homo, mususus), (pan, rattus));
(homo, (bos, pan));
((mus, rattus),pan);
"""
    treecol = TreeCollection( col, TaxonomyReference() )
    print len(treecol.collection), treecol.collection
#    treecol.display()
    for tree in treecol.collection:
        print tree["tree"]
    col = treecol.query( "{murinae}>1" )
    print len(col), col
