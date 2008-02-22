
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
        if nwk_collection[:6].lower().strip() == "#nexus":
            for tree in nwk_collection.split(";")[1:-2]:
                tree = tree.strip()
                nwktree = tree.split("=")[1].strip()
                tree_name = " ".join(tree.split("=")[0].split()[1:]).strip()
                self.collection.append( {
                    "name": tree_name,
                    "tree": nwktree,
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
                      "tree": nwktree,
                    } )
        self.misspelled_taxa = None
        print "++++++++__init__ fini"

    def __listTaxon( self ):
        """
        return taxa set of the collection
        """
        all_taxa = set()
        for i in xrange( len( self.collection ) ):
            list_taxa_tree = getTaxa(self.collection[i]["tree"])
            for j in xrange( len(list_taxa_tree) ):
                all_taxa.add( list_taxa_tree[j].lower() )
        return all_taxa

    def __getMisSpelledTaxa( self, list_taxa ):
        """
        return the set of all misspelled taxa
        """
        bad_taxa = set()
        for taxon in list_taxa:
            if not self.reference.isValid(self.reference.stripTaxonName(taxon)):
                bad_taxa.add( taxon )
        return bad_taxa
 
    def __eval_query( self, query, tree ):
        res = query 
        for pattern in re.findall("{([^}]+)}", query):
            index = 0
            pattern = pattern.lower()
            for taxon in getTaxa(tree):
                taxon = self.reference.stripTaxonName(taxon.strip().lower())
                if taxon not in self.misspelled_taxa:
                    if pattern in self.reference.getParents(taxon) or \
                      pattern == taxon:
                        index += 1
            res = res.replace("{"+pattern+"}", str(index) )
        if res:
            return eval( res )
        raise SyntaxError, "bad query %s" % query

    def query( self, query ):
        """
        filter the collection with query. The query must be a string like
        this:
            {genre1} > 3 and {genre2}=2...

        @query (string): the query which will filter the collection
        @new_list (list): the filtered collection
        """
        new_list = []
        for i in xrange( len(self.collection) ):
            tree = self.collection[i]
            if self.misspelled_taxa is None:
                self.misspelled_taxa = self.__getMisSpelledTaxa(self.__listTaxon())
                print self.misspelled_taxa
            try:
                if self.__eval_query( query, tree["tree"] ):
                    new_list.append( tree )
            except SyntaxError, e:
                raise SyntaxError, "bad query %s" % e
        return new_list

if __name__ == "__main__":
    from taxonomyreference import TaxonomyReference
    col = """#nexus
begin trees;
tree aa = ((rattus, pan), homo);
tree bb = ((homo_sapiens, mususus), (pan, rattus));
tree cc = (homo, (bos, pan));
tree dd = ((mus, rattus),pan);
end;
"""
    treecol = TreeCollection( col, TaxonomyReference() )
    print len(treecol.collection), treecol.collection
#    treecol.display()
    for tree in treecol.collection:
        print tree["tree"]
    col = treecol.query( "{homo}" )
    print len(col), col
