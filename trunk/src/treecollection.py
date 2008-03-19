
from phylogenictree import PhylogenicTree
from taxobject import Taxobject
from lib.phylogelib import getTaxa, tidyNwk, removeBootStraps, \
  removeNexusComments
import re

class TreeCollection( Taxobject ):
    """
    Manipulate phylogenic tree collection:
        - filtering
        - query
        - diplay
        ...
    """

    NCBI = "http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id="
    
    def __init__( self, nwk_collection, reference ):
        """
        @nwk_collection (string): collection in phylip or nexus format
        """
        #super( TreeCollection, self ).__init__()
        self.reference = reference
        self.collection = []
        self.query_collection = []
        # Nexus collection
        if nwk_collection[:6].lower().strip() == "#nexus":
            nwk_collection = removeNexusComments( nwk_collection )
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
        self.__init()

    def __init( self ):
        """
        count the number of species by tree
        """
        self.taxa_list = set()
        self.species_count = {"XXX":0}
        self._d_taxonlist = {}
        self._d_reprtaxon = {}
        self.bad_taxa_list = set()
        self.homonyms = {}
        for tree in self.getCollection():
            if not self.species_count.has_key( tree["name"] ):
                self.species_count[tree["name"]] = {}
                self._d_taxonlist[tree["name"]] = set()#stats
            for taxon in getTaxa( tree["tree"] ):
                old_taxon_name = taxon
                taxon = self.reference.stripTaxonName(taxon)
                if self.reference.isHomonym( taxon ):
                    if not self.homonyms.has_key( taxon ):
                        self.homonyms[taxon] =  self.reference.getHomonyms( taxon )
                if self.reference.isValid( taxon ):
                    self.taxa_list.add( taxon )#stats
                    self._d_taxonlist[tree["name"]].add( taxon )#stats
                    for tax in self.reference.getParents( taxon ):#stats
                        self._d_taxonlist[tree["name"]].add( tax )#stats
                        if not self._d_reprtaxon.has_key( tax ): #
                            self._d_reprtaxon[tax] = set()#
                        self._d_reprtaxon[tax].add( taxon )#
                    if not self.species_count[tree["name"]].has_key( taxon ):
                        self.species_count[tree["name"]][taxon] = 0
                    if not self._d_reprtaxon.has_key( taxon ):#stats
                        self._d_reprtaxon[taxon] = set()#stats
                    self._d_reprtaxon[taxon].add( old_taxon_name )#stats
                    self.species_count[tree["name"]][taxon] += 1
                    for parent in self.reference.getParents( taxon ):
                        if not self.species_count[tree["name"]].has_key( parent ):
                            self.species_count[tree["name"]][parent] = 0
                        self.species_count[tree["name"]][parent] += 1
                elif not self.reference.isHomonym( taxon ):
                    self.species_count["XXX"] += 1
                    self.bad_taxa_list.add( taxon )
        #self.taxa_list = list( self.taxa_list )#stats

    def getNbTrees( self, taxon ):
        """
        return the number of trees where taxon is
        """
        nb = 0
        for tree, taxa_list in self._d_taxonlist.iteritems():
            if taxon in taxa_list:
                nb += 1
        return nb

    def getCollection( self ):
        """
        return the query collection if there was a query
        return the complete collection otherwise
        """
        if self.query_collection:
            return self.query_collection
        return self.collection

    def clearQuery( self ):
        """
        clear the query collection
        """
        self.query_collection = []
    
    def __eval_query( self, query, tree ):
        res = query 
        for pattern in re.findall("{([^}]+)}", query):
            striped_pattern = pattern.strip().lower()
            if not self.reference.isValid( striped_pattern ):
                raise NameError, striped_pattern
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
        for i in xrange( len(self.getCollection()) ):
            tree = self.getCollection()[i]
            try:
                if self.__eval_query( query, tree ):
                    new_list.append( tree )
            except SyntaxError, e:
                raise SyntaxError, e
        self.query_collection = new_list
        return new_list

    def statNbTreeWithNode( self ):
        """
        return the number of tree for each taxon
        """
        d_tree_taxon = {}
        l_taxa = []
        for tree in self.collection:
            for taxon in getTaxa( tree["tree"] ):
                if self.reference.isValid( taxon ):
                    if taxon not in l_taxa: l_taxa.append( taxon )
                    if not d_tree_taxon.has_key( taxon ):
                        d_tree_taxon[l_taxa.index(taxon)] = 0
                    d_tree_taxon[l_taxa.index(taxon)] += 1
        result_list = []
        for i, j in d_tree_taxon.iteritems():
            result_list.append( (i,j) )
        return result_list

    def statNbTreeWithNbNodes( self ):
        """
        return the number of tree for each number of taxa
        """
        d_tree_nodes = {}
        for tree in self.collection:
            taxa_len = len( getTaxa( tree["tree"] ) )
            if not d_tree_nodes.has_key( taxa_len ):
                d_tree_nodes[taxa_len] = 0
            d_tree_nodes[taxa_len] += 1
        result_list = []
        for i, j in d_tree_nodes.iteritems():
            result_list.append( (i,j) )
        return result_list

    def displayStats( self, allparents = False ):
        """
        Display NCBI arborescence with stats
        """
        self.__init()
        tree = self.reference.getNCBIArborescence( self.taxa_list )
        if not allparents:
            tree = self.__removeSingleParent( tree )
        return self.__displayStat( tree, root="root" )

    def __removeSingleParent( self, tree ):
        for node in tree:
            n = tree.predecessors( node ) + tree.successors(node)
            if len(n) == 2:
                tree.delete_edge( n[0], node )
                tree.delete_edge( node, n[1] )
                tree.add_edge( n[0], n[1] )
        return tree

    def __displayStat( self, tree, root = "",  mydepth = 0, lastnode = 'root', blockname = "" ):
        """
        Pretty print of the tree in HTML.

        @root (string): parent name
        @mydepth (int): depth in the tree
        @return (string): the display in html format
        """
        result = ""
        blocknum = 0
        # Create root node display
        if root == "root":
            result += "<a class='genre' href='"+self.NCBI+ \
              self.reference.TAXONOMY[root]["id"]+"'>"+root.capitalize()+ \
                "</a> Exemple:(6/7) = (6 species in 7 trees)<br />\n"
            result += "|<br />\n"
        # Create tree display
        for node in tree.successors( root ):
            dispnode = node.split("|")[0].replace(self.reference.delimiter, " ")
            dispnode = dispnode.replace( "<", "&lt;" )
            dispnode = dispnode.replace( ">", "&gt;" )
            bdnode = self.reference.stripTaxonName( node.split("|")[0] )
            nb_inter_parents = 0
            # Create div for interparents (parents beetween nodes)
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
            # Create arborescence display
            depth = 0
            while depth != mydepth :
                result += "| "
                depth += 1
            subnodes = tree.successors( node )
            if subnodes: # it's a genre
                result += self.__linkGenre( dispnode, bdnode, blockname, True, nb_inter_parents )
                result += self.__displayStat( tree,  node, depth + 1, 
                  lastnode = bdnode, blockname = blockname+"a")
            else: # it's a species (ie taxon)
                if "XXX" in node:
                    result += "+-<font color='red'><b>"+dispnode.capitalize()+"</b></font><br />\n"
                else:
                    result += self.__linkSpecies( dispnode, bdnode, True, blockname, nb_inter_parents)
        return result

    def __linkSpecies( self, dispnode, bdnode, stat=False, blockname="", nb_inter_parents=0 ):
        result = ""
        dispnode = dispnode.replace( "<", "&lt;" )
        dispnode = dispnode.replace( ">", "&gt;" )
        if self.reference.isHomonym( bdnode ):
            style = 'class="species_homonym"'
        else:
            style = 'class="species"'
        if stat:
            result += "+-"
        result += """<a id="%s" %s onmouseover="go('%s');" target='_blank' href="%s%s"> %s</a>""" % (
          self.reference.TAXONOMY[bdnode]["id"],
          style,                        
          bdnode,#.capitalize().replace(" ", "_"),
          self.NCBI,
          self.reference.TAXONOMY[bdnode]["id"],
          dispnode.capitalize() )
        if stat:
            result += """ (<a href="check?query=%%7B%s%%7D">%s</a>/<a title='%s'>%s</a>)\n""" % (
              bdnode,
              self.getNbTrees( bdnode ),
              ",".join( [i for i in self._d_reprtaxon[bdnode]]) ,
              str(len(self._d_reprtaxon[bdnode])))
        if nb_inter_parents:
            result += """<a id="a-%s" class='showparents'
              onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
                blockname,
                blockname )
        elif stat:
            result += "<br />\n"
        return result

    def __linkGenre( self, dispnode, bdnode, blockname, isinterparent=False, nb_inter_parents=0 ):
        result = ""
        dispnode = dispnode.replace( "<", "&lt;" )
        dispnode = dispnode.replace( ">", "&gt;" )
        if self.reference.isHomonym( bdnode ):
            style = 'class="genre_homonym"'
        else:
            style = 'class="genre"'
        result += """+-<a id="%s" %s name="genre" onmouseover="go('%s')" 
          href="%s%s" target='_blank'> %s </a>""" % (
          self.reference.TAXONOMY[bdnode]["id"],
          style,
          bdnode,#.capitalize().replace(" ", "_"),
          self.NCBI,
          self.reference.TAXONOMY[bdnode]["id"],
          dispnode.capitalize())
        result += """ (<a href="check?query=%%7B%s%%7D">%s</a>/<a title='%s'>%s</a>)\n""" % (
          bdnode,
          self.getNbTrees( bdnode ),
          ",".join( [i for i in self._d_reprtaxon[bdnode]]),
          str(len(self._d_reprtaxon[bdnode])))
        if isinterparent and nb_inter_parents:
            result += """<a id="a-%s" class='showparents'
              onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
                blockname,
                blockname )
        else:
            result += "<br />\n"
        return result
    
    def displayHomonymList( self ):
        result = """<fieldset>
        <legend> %s homonym(s) </legend>\n""" % len(self.homonyms.keys())
        for homonym, taxa in self.homonyms.iteritems():
            result += """<font color="orange">%s</font> : """ % homonym
            for taxon in taxa:
                dispnode = taxon.split("|")[0].replace(self.reference.delimiter, " ")
                dispnode = dispnode.replace( "<", "&lt;" )
                dispnode = dispnode.replace( ">", "&gt;" )
                result += """%s """ % self.__linkSpecies( dispnode, taxon )
            result += "<br />\n"
        result += "</fieldset>\n"
        return result
            

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
[balblabla des commentaires]
tree ENm001.mcs1.merge20.2758.22.mfa = [arf arf arf]
(Pan,Pongo,Hylobates,Colobus,Papio,Macaca,Callicebus,Aotus,Callithrix,Saimiri,Microcebus,Otolemur,Tupaia,Rattus,Mus,Spermophilus,Oryctolagus,Bos,Felis,Canis,Equus,Pteropus,Chiroptera,Myotis,Sorex,Dasypus,Echinops,Loxodonta,Monodelphis);
[enocdfks fklsdfj skldfj sdkf
skfjs dklfjsdklf]
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
    import time
    col = open( "../data/omm_cds_nex.tre" ).read()
    col = open("../data/tree.nwk").read()
    d = time.time()
    treecol = TreeCollection( col, TaxonomyReference() )
    f = time.time()
    print len(treecol.collection)
#    for tree in treecol.collection:
#        print tree["tree"]
#    print len(col.split(";")[1:-1]), col.split(";")[1:-1]
    dr = time.time()
    col = treecol.query( "{murinae}>1" )
    fr = time.time()
    print len(col)
    print treecol.homonyms
    print treecol.displayHomonymList()
    print "collection generee en ", f-d
    print "requete generee en ", fr-dr