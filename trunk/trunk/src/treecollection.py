
from phylogenictree import PhylogenicTree
from taxobject import Taxobject
from lib.phylogelib import getTaxa, tidyNwk, removeBootStraps, \
  removeNexusComments, getBrothers
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
        self.orignial_collection = nwk_collection.lower()
        self.reference = reference
        self.collection = []
        self.query_collection = None
        self.last_query = ""
        # Nexus collection
        if nwk_collection[:6].lower().strip() == "#nexus":
            nwk_collection = removeNexusComments( nwk_collection )
            nwk_collection = nwk_collection.lower()
            # Support of the nexus translate
            if "translate" in nwk_collection:
                d_translation = {}
                translation = nwk_collection.split("translate")[1].split(";")[0].split()
                for i in range(0,len(translation),2):
                    d_translation[translation[i]] = translation[i+1].replace(",","")
                for indice, translation in d_translation.iteritems():
                    nwk_collection = nwk_collection.replace( indice+":", translation+":" )
                nwk_collection = "#nexus\nbegin trees;\n"+ \
                  ";".join(nwk_collection.split("translate")[1].split(";")[1:])
                nwk_collection = removeBootStraps( nwk_collection )
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

    def  __init( self ):
        """
        count the number of species by tree
        """
        self.taxa_list = set() # stats
        self.species_count = {"XXX":0}
        self._d_taxonlist = {} # stats
        self._d_taxon_user = {}
        self._d_reprtaxon = {} # stats
        self.bad_taxa_list = set()
        self.homonyms = {}
        for tree in self.getCollection():
            if not self.species_count.has_key( tree["name"] ):
                self.species_count[tree["name"]] = {}
                self._d_taxonlist[tree["name"]] = set()#stats
            for taxon in getTaxa( tree["tree"] ):
                if taxon.strip():
                    old_taxon_name = taxon
                    taxon = self.reference.stripTaxonName(taxon)
                    if not self._d_taxon_user.has_key( taxon ):
                        self._d_taxon_user[taxon] = set()
                    self._d_taxon_user[taxon].add( old_taxon_name )
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

    def initStat( self ):
        """
        count the number of species by tree
        """
        self._d_taxonlist = {}
        self._d_reprtaxon = {}
        self.taxa_list = set() # stats
        for tree in self.getCollection():
            if not self._d_taxonlist.has_key( tree["name"] ):
                self._d_taxonlist[tree["name"]] = set()#stats
            for taxon in getTaxa( tree["tree"] ):
                if taxon.strip():
                    old_taxon_name = taxon
                    taxon = self.reference.stripTaxonName(taxon)
                    if self.reference.isValid( taxon ):
                        self.taxa_list.add( taxon )#stats
                        self._d_taxonlist[tree["name"]].add( taxon )#stats
                        for tax in self.reference.getParents( taxon ):#stats
                            self._d_taxonlist[tree["name"]].add( tax )#stats
                            if not self._d_reprtaxon.has_key( tax ): #
                                self._d_reprtaxon[tax] = set()#
                            self._d_reprtaxon[tax].add( taxon )#
                        if not self._d_reprtaxon.has_key( taxon ):#stats
                            self._d_reprtaxon[taxon] = set()#stats
                        self._d_reprtaxon[taxon].add( old_taxon_name )#stats

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
        if self.query_collection is not None:
            return self.query_collection
        return self.collection

    def clearQuery( self ):
        """
        clear the query collection
        """
        self.query_collection = None
        self.last_query = ""
    
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
        for i in xrange( len(self.collection) ):
            tree = self.collection[i]
            try:
                if self.__eval_query( query, tree ):
                    new_list.append( tree )
            except SyntaxError, e:
                raise SyntaxError, e
        self.query_collection = new_list
        self.last_query = "+and+"+query 
        # transform query to html
        self.last_query = self.last_query.replace("{", "%7B" )
        self.last_query = self.last_query.replace("}", "%7D" )
        self.last_query = self.last_query.replace(" ", "+" )
        self.last_query = self.last_query.replace("<", "&lt;" )
        self.last_query = self.last_query.replace(">", "&gt;" )
        self.last_query = self.last_query.replace("=", "%3D" )
        return new_list

    def stat1( self ):
        stat = {}
        for tree in self.getCollection():
            nbtaxa = len(getTaxa( tree["tree"] ) )
            if not stat.has_key( nbtaxa ):
                stat[nbtaxa] = 0
            stat[nbtaxa] += 1
        nbmax = max( stat.keys() )
        ratio = int( nbmax*10.0/100) or 1
        result_stat = {}
        for i in xrange( 0, nbmax, ratio):
            result_stat[i] = 0
        for i,j in stat.iteritems():
            for key in result_stat.keys():
                if key <= i < key+ratio:
                    result_stat[key] += j
        return result_stat

    def stat2( self ):
        stat = {}
        for tree in self.getCollection():
            already_done = set()
            for taxon in getTaxa( tree["tree"] ):
                taxon = self.reference.stripTaxonName( taxon )
                if taxon not in already_done:
                    if not stat.has_key( taxon ):
                        stat[taxon] = 0
                    stat[taxon] += 1    
                    already_done.add( taxon )
        nbmax = max( stat.values() )
        ratio = int( nbmax*10.0/100) or 1
        result_stat = {}
        for i in xrange( 0, nbmax, ratio):
            result_stat[i] = 0
        for i in stat.values():
            for key in result_stat.keys():
                if key <= i < key+ratio:
                    result_stat[key] += 1
        return result_stat

    def displayStats( self, allparents = False ):
        """
        Display NCBI arborescence with stats
        """
        #self.initStat()
        if self.getCollection():
            tree = self.reference.getNCBIArborescence( self.taxa_list )
            if not allparents:
                tree = self.__removeSingleParent( tree )
            return self.__displayStat( tree, root="root" )
        return ""

    def __removeSingleParent( self, tree ):
        for node in tree:
            if node not in self.taxa_list:
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
                "</a> (%s/%s) = (%s species in %s trees)<br />\n" % (
                  len(self.taxa_list), len(self.getCollection()),
                  len(self.taxa_list), len(self.getCollection()))
            result += """<span class="treeline">|</span><br />\n"""
        # Create tree display
        if root in tree.nodes():
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
                        result += """<span class="treeline">|</span> """*mydepth
                        result +=  ("""<span class="treeline">|</span> """*mydepth).join(
                          self.__linkGenre(i,i,blockname) for i in inter_parents ) 
                    result += "</tt></div>" 
                # Create arborescence display
                depth = 0
                while depth != mydepth :
                    result += """<span class="treeline">|</span> """
                    depth += 1
                subnodes = tree.successors( node )
                if subnodes: # it's a genre
                    result += """<span genre="%s">\n""" % bdnode
                    if bdnode in self.taxa_list:
                        result += self.__linkSpecies( dispnode, bdnode, True, blockname, nb_inter_parents)
                    else:
                        result += self.__linkGenre( dispnode, bdnode, blockname, True, nb_inter_parents, stat=True )
                    result += self.__displayStat( tree,  node, depth + 1, 
                      lastnode = bdnode, blockname = blockname+"a")
                    result += """</span>\n"""
                else: # it's a species (ie taxon)
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
            result += """<input class="restrict" type="checkbox" name="%s" value="%s" />""" % (
              bdnode, bdnode )
        result += """<a id="%s" %s onmouseover="go('%s');" target='_blank' href="%s%s"> %s</a>""" % (
          self.reference.TAXONOMY[bdnode]["id"],
          style,                        
          bdnode,#.capitalize().replace(" ", "_"),
          self.NCBI,
          self.reference.TAXONOMY[bdnode]["id"],
          dispnode.capitalize() )
        if stat:
            result += """
            (<a class="nolink" title='%s'>%s</a>/
            <a title='%s' href="statistics?query=%%7B%s%%7D%s">%s</a>)\n""" % (
              ",".join( [i for i in self._d_reprtaxon[bdnode]]) ,
              str(len(self._d_reprtaxon[bdnode])),
              "Restrict your collection to these trees",
              bdnode,
              self.last_query,
              self.getNbTrees( bdnode ))
        if nb_inter_parents:
            result += """<a id="a-%s" class='showparents'
              onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
                blockname,
                blockname )
        elif stat:
            result += "<br />\n"
        return result

    def __linkGenre( self, dispnode, bdnode, blockname, isinterparent=False, nb_inter_parents=0, stat = 0 ):
        result = ""
        dispnode = dispnode.replace( "<", "&lt;" )
        dispnode = dispnode.replace( ">", "&gt;" )
        if self.reference.isHomonym( bdnode ):
            style = 'class="genre_homonym"'
        else:
            style = 'class="genre"'
        result += "+-"
        if stat:
            result += """<input class="restrict" type="checkbox" genre="%s"
            onclick="javascript:selectGenre('%s');" />""" % ( bdnode, bdnode )
        result += """<a id="%s" %s name="genre" onmouseover="go('%s')" 
          href="%s%s" target='_blank'> %s </a>""" % (
          self.reference.TAXONOMY[bdnode]["id"],
          style,
          bdnode,
          self.NCBI,
          self.reference.TAXONOMY[bdnode]["id"],
          dispnode.capitalize())
        result += """
        (<a class="nolink" title='%s'>%s</a>/
        <a title="%s" href="statistics?query=%%7B%s%%7D%s">%s</a>)\n""" % (
          ",".join( [i for i in self._d_reprtaxon[bdnode]]),
          str(len(self._d_reprtaxon[bdnode])),
          "Restrict your collection to these trees",
          bdnode,
          self.last_query,
          self.getNbTrees( bdnode ))
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

    def _nxgraph2list( self, tree, node, d="" ):
        if not d:
            d = {}
            for i in tree.edges():
                if not d.has_key( i[0] ):
                    d[i[0]] = []
                d[i[0]].append( i[1] )
            for i in tree.edges():
                if not d.has_key( i[1] ):
                    d[i[1]] = i[1]        
        m = []
        for node in tree.successors( node ):
            if isinstance( d[node], list ):
                m.append( self._nxgraph2list( tree, node, d ) )
            else:
                m.append( d[node] )
        return m

    def _list2nwk( self, l ):
        result = str( l )
        result = result.replace("[", "(").replace("]",")")
        result = result.replace(", ",",").replace( " ,", "," )
        result = result.replace( "'", "" )
        return result

    def _nxgraph2nwk( self, tree, root ):
        l = self._nxgraph2list( tree, root )
        return self._list2nwk( l )[1:-1]+";" # removing extras parenthesis
        
    def getNCBITreeAsNwk( self ):
        """
        return the NCBI arborescence in a newick string
        """
        self.initStat()
        if self.getCollection():
            tree = self.reference.getNCBIArborescence( self.taxa_list )
            tree = self.__removeSingleParent( tree )
            tree = self._nxgraph2nwk( tree, "root" )
            tree = tree.replace( " ", self.reference.delimiter )
            return tree
        return ""

    def filter( self, taxa_list ):
        new_col = "#nexus\nbegin trees;\n"
        for tree in self.getCollection():
            new_tree = tidyNwk( tree["tree"] )
            if " " in new_tree:
                new_tree = new_tree.replace( " ", "_" )
                delimiter = "_"
            else:
                delimiter = self.reference.delimiter
            try:
                for taxon in taxa_list:
                    for_list = list( self._d_taxon_user[taxon] )
                    if self._d_taxon_user.has_key( taxon.split()[0] ):
                        for_list += list(self._d_taxon_user[taxon.split()[0]])
                    for taxon in for_list:
                        taxon = delimiter.join( taxon.split() )
                        while taxon in getTaxa( new_tree ):
                            list_taxa = getBrothers(new_tree, taxon )
                            list_brother = getBrothers(new_tree, taxon )
                            list_brother.remove( taxon )
                            if len( list_brother ) > 1:
                                new_tree = new_tree.replace( "("+",".join(list_taxa)+")", "("+",".join( list_brother)+")")
                            else:
                                new_tree = new_tree.replace( "("+",".join(list_taxa)+")", ",".join( list_brother ))
                if len( getTaxa( new_tree ) ) == 1:
                    new_col += "Tree "+str(tree["name"])+" = ("+new_tree+");\n"
                else:
                    new_col += "Tree "+str(tree["name"])+" = "+new_tree+";\n"
            except:
                continue
        new_col += "end;\n"
        return new_col

    def filter2( self, taxa_list ):
        """
        return the original collection without certains taxa
        """
        ori = removeBootStraps( self.orignial_collection )
        for taxon in taxa_list:
            ori = re.sub( "\s*"+taxon+"\s*([),])", r"\1", ori, count=0 )
            for taxon_user in self._d_taxon_user[taxon]:
                ori = re.sub( "\s*"+taxon_user+"\s*([),])", r"\1", ori, count=0 )
        while ",," in ori or "(," in ori or ",)" in ori or "()" in ori:
            ori = ori.replace(",,",",")
            ori = ori.replace("(,","(")
            ori = ori.replace(",)",")")
            ori = ori.replace("()","")
            ori = re.sub( r"(,\s+\))",")", ori )
            ori = re.sub( r"(\(\s+,)","(", ori )
            ori = re.sub( r"(\(\s+\))","", ori )
            ori = re.sub( r"(,\s+,)",",", ori )
        while re.findall( r"\((\([^()]+\))\)", ori, re.DOTALL ):
            ori = re.sub( r"\((\([^()]+\))\)", r"\1", ori, count=0  )
#        ori = re.sub( r"\(([^,()]+\))[^;]", r"\1", ori, re.DOTALL )
#        ori = re.sub( r"\((\([^()]+\))\)", r"\1", ori, re.DOTALL )
#        ori = re.sub( r"\(([^,()]+)\)", r"\1", ori, re.DOTALL )
#        print "ori_avant_whiles>>>", ori
#        replace_list = re.findall(r"\((\([^()]+\))\)", ori, re.DOTALL )
#        while replace_list:
#            for i in replace_list:
#                ori = ori.replace( "("+i+")", i )
#            replace_list = re.findall( r"\((\([^()]+\))\)", ori, re.DOTALL)
#        print "ori_avant_while2>>>", ori
#        replace_list =  re.findall( r"\(([^,( )]+)\)[^;]", ori, re.DOTALL )
#        while replace_list:
#            for i in replace_list:
#                print ">>replace", i
#                ori = ori.replace( "("+i+")", i )
#            replace_list =  re.findall( r"\(([^,( )]+)\)[^;]", ori, re.DOTALL )
        return ori

        
        

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
#    col = open( "../data/omm_cds_nex.tre" ).read()
    col = open("../data/tree.nwk").read()
#    col = "((rattus,mus),bos,(pan,homo));(mus musculus,(pan,bos));"
#    col = '((((bos,canis),(((homo,pan),macaca),((mus,rattus),oryctolagus))),dasypus),(echinops,loxodonta),monodelphis);'
    d = time.time()
    treecol = TreeCollection( col, TaxonomyReference() )
    f = time.time()
    dr = time.time()
    print len(treecol.getCollection())
    fr = time.time()
    print len(treecol.getCollection())
#    print treecol.statNbTreeWithNbNodes()
#    print treecol.bad_taxa_list
#    print treecol.displayStats()
#    print treecol.getCollection()
#    print treecol.bad_taxa_list
#    print treecol.homonyms
#    print treecol.displayHomonymList()
#    print treecol.statNbTreeWithNbNodes()
    print ">"*20
    print treecol.filter( ["mus musculus"] )
    print "<"*20
    print "collection generee en ", f-d
    print "requete generee en ", fr-dr
