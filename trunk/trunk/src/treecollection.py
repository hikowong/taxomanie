
from phylogenictree import PhylogenicTree
from taxobject import Taxobject
from lib.phylogelib import getTaxa, tidyNwk, removeBootStraps
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
                nwktree = removeBootStraps( tidyNwk( tree.split("=")[1].strip().lower() ) )
                tree_name = " ".join(tree.split("=")[0].split()[1:]).strip()
                self.collection.append( {
                    "name": tree_name,
                    "tree": nwktree,
                  })
        # Phylip collection
        else:
            index = 0
            for nwktree in nwk_collection.strip().split(";"):
                nwktree = removeBootStraps( tidyNwk( nwktree.strip().lower() ))
                if nwktree:
                    index += 1
                    self.collection.append( {
                      "name": index,
                      "tree": nwktree,
                    } )
        self.species_count = self.countNbSpeciesByTree()

    def countNbSpeciesByTree( self ):
        """
        Return the number of each species in the collection for each tree
        """
        d_genre = {}
        for tree in self.collection:
            if not d_genre.has_key( tree["name"] ):
                d_genre[tree["name"]] = {}
            for taxon in getTaxa( tree["tree"] ):
                if not d_genre[tree["name"]].has_key( taxon ):
                    d_genre[tree["name"]][taxon] = 0
                d_genre[tree["name"]][taxon] += 1
                for parent in self.reference.getParents( taxon ):
                    if not d_genre[tree["name"]].has_key( parent ):
                        d_genre[tree["name"]][parent] = 0
                    d_genre[tree["name"]][parent] += 1
        return d_genre

    def countNbSpecies( self ):
        #XXX Not used
        """
        Return the number of each species in the collection

        exemple : (mus, rattus);(mus, canis);(rattus, bos);
        will return {'murinae':4, 'phasianinae': 1 ...}
        """
        d_genre = {}
        for tree in self.collection:
            for taxon in getTaxa( tree["tree"] ):
                for parent in self.reference.getParents( taxon ):
                    if not d_genre.has_key( parent ):
                        d_genre[parent] = 0
                    d_genre[parent] += 1
        return d_genre

    def __eval_query( self, query, tree ):
        res = query 
        for pattern in re.findall("{([^}]+)}", query):
            striped_pattern = pattern.strip().lower()
            if not self.species_count[tree["name"]].has_key( striped_pattern ):
                index = 0
            else:
                index = self.species_count[tree["name"]][striped_pattern]
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
            try:
                if self.__eval_query( query, tree ):
                    new_list.append( tree )
            except SyntaxError, e:
                raise SyntaxError, "bad query %s" % e
        return new_list

    def stat1( self, pattern ):
        """
        for taxon in 
            for taxon in getTaxa( tree ):
                taxon = self.reference.stripTaxonName( taxon )
        return {"name1":3, "name2":4}
        """
        pass
    
    def statNbNodesTree( self ):
        pass

    def statNbTreeWithNbNodes( self ):
        """
        return the number of tree for each number of taxa
        """
        d_tree_nodes = {}
        for tree in self.collection:
            taxa_len = len( getTaxa( tree ) )
            if not d_tree_nodes.has_key( taxa_len ):
                d_tree_nodes[taxa_len] = 0
            d_tree_node[taxa_len] += 1
        result_list = []
        for i, j in d_tree_node.iteritems():
            result_list.append( (i,j) )
        ar = PC.area.T( size=(500,500),
          x_axis= PC.axis.X(label="Number of taxa"),
          y_axis = PC.axis.Y(label="Number of trees")
        )
        ar.add_plot(PC.bar_plot.T(data=data))
        ar.draw()

if __name__ == "__main__":
    from taxonomyreference import TaxonomyReference
    col = """#nexus
begin trees;
tree aa = ((rattus, pan), homo);
tree aaa = 
tree bb = ((homo_sapiens, mususus), (pan, rattus));
tree cc = (homo, (bos, pan));
tree dd = ((mus, rattus),pan);
end;
"""

    col = """#nexus
begin trees;
tree ENm001.mcs1.merge20.2758.22.mfa =
(Pan,Pongo,Hylobates,Colobus,Papio,Macaca,Callicebus,Aotus,Callithrix,Saimiri,Microcebus,Otolemur,Tupaia,Rattus,Mus,Spermophilus,Oryctolagus,Bos,Felis,Canis,Equus,Pteropus,Chiroptera,Myotis,Sorex,Dasypus,Echinops,Loxodonta,Monodelphis);
tree ENm001.mcs10.merge20.22980.53.mfa =
(Pan,Pongo,Hylobates,Colobus,Chlorocebus,Papio,Macaca,Callicebus,Aotus,Callithrix,Saimiri,Microcebus,Otolemur,Tupaia,Rattus,Mus,Cavia,Spermophilus,Oryctolagus,Bos,Felis,Canis,Equus,Pteropus,Chiroptera,Myotis,Sorex,Dasypus,Echinops,Loxodonta,Monodelphis);
tree ENm001.mcs100.merge20.57317.211.mfa =
(Pan,Pongo,Hylobates,Colobus,Chlorocebus,Papio,Macaca,Callicebus,Aotus,Callithrix,Saimiri,Microcebus,Otolemur,Tupaia,Rattus,Mus,Cavia,Spermophilus,Oryctolagus,Bos,Felis,Canis,Equus,Pteropus,Chiroptera,Myotis,Erinaceus,Sorex,Dasypus,Echinops,Loxodonta,Procavia,Monodelphis);
tree ENm001.mcs1000.merge20.436545.34.mfa =
(Pan,Pongo,Hylobates,Colobus,Chlorocebus,Papio,Callicebus,Aotus,Callithrix,Saimiri,Microcebus,Otolemur,Tupaia,Rattus,Mus,Cavia,Spermophilus,Bos,Felis,Canis,Equus,Pteropus,Chiroptera,Myotis,Erinaceus,Sorex,Dasypus,Loxodonta,Procavia,Monodelphis,Ornithorhynchus);
tree ENm001.mcs1001.merge20.436710.36.mfa =
(Pan,Pongo,Hylobates,Colobus,Chlorocebus,Papio,Callicebus,Aotus,Callithrix,Saimiri,Microcebus,Otolemur,Rattus,Mus,Cavia,Spermophilus,Oryctolagus,Felis,Canis,Equus,Pteropus,Chiroptera,Myotis,Erinaceus,Sorex,Dasypus,Loxodonta,Procavia,Monodelphis,Ornithorhynchus);
tree ENm001.mcs1002.merge20.436830.27.mfa =
(Pan,Pongo,Hylobates,Colobus,Chlorocebus,Papio,Callicebus,Aotus,Callithrix,Saimiri,Microcebus,Otolemur,Tupaia,Rattus,Mus,Cavia,Spermophilus,Oryctolagus,Felis,Canis,Equus,Pteropus,Chiroptera,Myotis,Erinaceus,Sorex,Dasypus,Loxodonta,Procavia,Monodelphis,Ornithorhynchus);
tree ENm001.mcs1003.merge20.439936.6.mfa =
(Pan,Pongo,Hylobates,Colobus,Chlorocebus,Papio,Callicebus,Aotus,Callithrix,Saimiri,Microcebus,Otolemur,Tupaia,Cavia,Spermophilus,Oryctolagus,Bos,Felis,Canis,Equus,Myotis,Erinaceus,Sorex,Dasypus,Loxodonta,Monodelphis,Gallus);
tree ENm001.mcs1004.merge20.442993.6.mfa =
(Pan,Hylobates,Colobus,Chlorocebus,Papio,Callicebus,Aotus,Callithrix,Saimiri,Microcebus,Otolemur,Rattus,Mus,Cavia,Spermophilus,Oryctolagus,Bos,Felis,Canis,Equus,Pteropus,Chiroptera,Myotis,Erinaceus,Procavia);
tree ENm001.mcs1005.merge20.443262.6.mfa =
(Pan,Hylobates,Colobus,Chlorocebus,Papio,Callicebus,Aotus,Callithrix,Saimiri,Microcebus,Otolemur,Rattus,Mus,Cavia,Spermophilus,Oryctolagus,Bos,Felis,Canis,Equus,Chiroptera,Myotis,Sorex,Dasypus,Loxodonta,Procavia);
end;
"""
    treecol = TreeCollection( col, TaxonomyReference() )
#    print len(treecol.collection), treecol.collection
#    for tree in treecol.collection:
#        print tree["tree"]
    print len(col.split(";")[1:-1]), col.split(";")[1:-1]
    import time
    d = time.time()
    col = treecol.query( "{murinae}>1" )
    f = time.time()
    print len(col), col
    print "generee en ", f-d
