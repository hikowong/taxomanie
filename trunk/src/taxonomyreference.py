
from networkx import DiGraph
from lib.phylogelib import getTaxa, getBrothers, \
    getChildren, tidyNwk, removeBootStraps, checkNwk

class TaxonomyReference( DiGraph ):
    """
    This class build a taxonomy reference from the NCBI project and provide tools to manipulate and
    query it.

    With this class, you can:
        - check if names are valid
        - try to correct misspelling names
        - know if a name is a common name or a synonym and get all scientific
          name in relation

    You must provide a csv file which has the bellowed structure:
        id|name|first_parent|homonym|list_parents|synonyms_list|common_name_list

    all without spaces.

    list_parents, synonyms_list and common_name_list must have this structure:
        first_item!second_item!...!...


    This class provides also methods to create Digraph 
    """

    def __init__( self, file = "" ):
        super( TaxonomyReference, self ).__init__()
        if file:
            taxonomy = open( file )
        else:
            taxonomy = open( "tools/taxonomy.csv" )
        # taxonomy reference generation
        self.TAXONOMY = {}
        self._homonym_by_name = {}
        self._homonym_by_id = {}
        for species in taxonomy.readlines():
            id, name, parent, homonym, list_parents, synonym, common = species.split("|")
            # Striping...
            id = id.strip()
            name = name.strip()
            parent = parent.strip()
            homonym = homonym.strip()
            list_parents = list_parents.strip()
            synonym = synonym.strip()
            common = common.strip()
            # Filling TAXONOMY
            if synonym:
                synonym = synonym.split("!")
            if common:
                common = common.split("!")
            if homonym:
                if not self._homonym_by_name.has_key( homonym ):
                    self._homonym_by_name[homonym] = set()
                self._homonym_by_name[homonym].add( name )
            self._homonym_by_id[id] = homonym
            if list_parents:
                list_parents = list_parents.split("!")
            self.TAXONOMY[name] = {
                "id": id,
                "parent": parent,
                "homonym": homonym,
                "parents": list_parents,
                "synonym": synonym,
                "common": common
            }
        # reference tree generation
        for taxon in self.TAXONOMY.iterkeys():
            parent = self.TAXONOMY[taxon]["parent"]
            self.add_edge( parent, taxon )
        self.delimiter = "_"

    def stripTaxonName( self, taxon_name ):
        """
        Strip Taxon name in order to keep the scientifique name and to remove
        all user staff.

        Exemple:
            stripTaxonName( "rattus" ) -> "rattus"
            stripTaxonName( "rattus_france" ) -> "rattus"
            stripTaxonName( "rattus_rattus_france" ) -> "rattus_rattus"
        """
        name = " ".join( taxon_name.replace(self.delimiter," ").split()[:2] )
        if not self.isValid( name ):
            return name.split()[0]
        return name
 
    def getNameFromCommon( self, common_name ): #XXX not used
        """
        @return (list): all scientific names which is related with this common name
        """
        species_list = []
        for name, body in self.TAXONOMY.iteritems():
            if common_name in body["common"]:
                species_list.append( name )
        return species_list
             
    def getNameFromSynonym( self, synonym ): # XXX not used
        """
        @return (list): all scientific names which is related with this synonym
        """
        species_list = []
        for name, body in self.TAXONOMY.iteritems():
            if synonym in body["common"]:
                species_list.append( name )
        return species_list

    def isHomonym( self, name ):
        """ return True if name is an homonym """
        name = name.lower().strip()
        if self._homonym_by_name.has_key( name ):
            return True
        return False

    def getHomonyms( self, name ):
        """
        return the homonyms list of a taxon.
        """
        name = name.lower().strip()
        if self._homonym_by_name.has_key( name ):
            return self._homonym_by_name[name]
        raise ValueError, "%s is not an homonym" % name

    def isValid( self, name ):
        """
        return (bool): True if name is a scientific name
            return False otherwise
        """
        return self.TAXONOMY.has_key( name.lower() )


    def getParents( self, name ):
        """
        return parents list of name until the root node

        @name: string
        @return: list
        """
        if name != "root" and self.isValid( name ):
            return self.TAXONOMY[name]["parents"]
        return []

    def getIntervalParents( self, name1, name2 ):
        """
        return parents list beetween 2 taxons.

        Exemple:
            >>> self.getIntervalParents( "eukaryota", "eutheria" )
            ['euarchontoglires', 'glires', 'rodentia', 'sciurognathi', 'muroidea']
            >>> self.getIntervalParents( "murinae", "eutheria" )
        """
        parents_list = self.getParents( name2 )
        try:
            return parents_list[parents_list.index( name1 )+1:]
        except ValueError:
            raise NameError, "%s is not a parent of %s" % (name1, name2) 
            

    def __getMissSpelledList( self, taxa_list ):
        miss_spelled_list = []
        for taxon in taxa_list:
            related_name = self.correct( self.stripTaxonName(taxon) )
            if related_name:
                miss_spelled_list.append( taxon ) 
        return miss_spelled_list

    def getCommonParent( self, taxa_list ):
        """
        return the first common parent of taxa_list

        @taxa_list: list
        @return: string
        """
        miss_spelled_list = self.__getMissSpelledList( taxa_list )
        taxa_list = [self.stripTaxonName(taxon) for taxon in taxa_list if taxon not in miss_spelled_list]
        if len( taxa_list ) >= 2:
            dict_parents = {}
            parents_list1 = self.getParents( taxa_list[0] )
            parents_list2 = self.getParents( taxa_list[1] )
            all_common_parents = [parent for parent in parents_list1 if parent in parents_list2]
            if len(taxa_list) > 2:
                for i in range( len( taxa_list) ):
                    for j in range(i, len( taxa_list ) ):
                        if i == j or (i == 0 and j == 1):
                            continue
                        parents_list1 = self.getParents( taxa_list[i] )
                        parents_list2 = self.getParents( taxa_list[j] )
                        common_parents = [parent for parent in parents_list1 if parent in parents_list2]
                        all_common_parents = [parent for parent in common_parents\
                          if parent in (common_parents and all_common_parents)]
            return all_common_parents[-1]
        elif len( taxa_list ) == 1:
            return self.getParents( taxa_list[0] )[-1]
        else:
            return "XXX"

    def getNCBIArborescence( self, taxa_list ):
        """
        Take a taxa list, search in reference all parents names and
        return the tree.

        @nwk : string
        @return: networkx.DiGraph
        """
        import networkx as NX
        tree = NX.DiGraph()
        for taxon in taxa_list:
            taxon = self.stripTaxonName( taxon )
            if self.isValid( taxon ):
                parents = self.getParents( taxon )[:]
                parents.reverse()
                for parent in parents:
                    tree.add_edge( parent, taxon )
                    taxon = parent
        return tree

if __name__ == "__main__":
    ref = TaxonomyReference()
    print ref.getHomonyms( "echinops" )



