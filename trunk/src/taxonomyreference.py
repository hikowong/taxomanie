
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
        id|name|parent_name|synonyms_list|common_name_list

    all without spaces.

    synonyms_list and common_name_list must have this structure:
        first_synonym!second_synonym!...!...


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
        for species in taxonomy.readlines():
            id, name, parent, synonym, common = species.split("|")
            common = common.strip()
            if synonym:
                synonym = synonym.split("!")
            if common:
                common = common.split("!")
            self.TAXONOMY[name] = {
                "id": id,
                "parent": parent,
                "synonym": synonym,
                "common": common
            }
        # reference tree generation
        for taxon in self.TAXONOMY.iterkeys():
            parent = self.TAXONOMY[taxon]["parent"]
            self.add_edge( parent, taxon )

    def getNameFromCommon( self, common_name ):
        """
        @return (list): all scientific names which is related with this common name
        """
        species_list = []
        for name, body in self.TAXONOMY.iteritems():
            if common_name in body["common"]:
                species_list.append( name )
        return species_list
             
    def getNameFromSynonym( self, synonym ):
        """
        @return (list): all scientific names which is related with this synonym
        """
        species_list = []
        for name, body in self.TAXONOMY.iteritems():
            if synonym in body["common"]:
                species_list.append( name )
        return species_list

    def isValid( self, name ):
        """
        return (bool): True if name is a scientific name
            return False otherwise
        """
        return name.lower() in self.TAXONOMY.iterkeys()

    def correct( self, name, guess = False ):
        """
        - Check if name is a scientific name
        - Check if name is a synonym
        - Check if name is a common name
        - Check if name is a misspell name

        @return (list): list of names that might corresponds.
            if the name is a scientific name, return an empty list.
        """
        if self.isValid( name ):
            return []
        else:
#            return [0]
            synonym_list = self.getNameFromSynonym( name )
            if synonym_list:
                return synonym_list
            else:
                common_list = self.getNameFromCommon( name )
                if common_list:
                    return common_list
                elif guess:
                    from lib.spellcheck import SpellCheck
                    splchk = SpellCheck( self.TAXONOMY.iterkeys() )
                    return splchk.correct( name )
                else:
                    return [0]

    def getParents( self, name ):
        """
        return parents list of name until the root node

        @name: string
        @return: list
        """
        parents_dict = {}
        if name != "root":
            if not parents_dict.has_key( name ):
                parents_dict[name] = []
                parent = self.predecessors( name )[0]
                while parent != "root":
                    parents_dict[name].append( parent )
                    parent = self.predecessors( parent )[0]
                parents_dict[name].append( "root" )
                parents_dict[name].reverse()
            return parents_dict[name]
        return [] 

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

    def __getMissSpelledList( self, taxa_list ):
        miss_spelled_list = []
        for taxon in taxa_list:
            related_name = self.correct( taxon )
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
        taxa_list = [taxon for taxon in taxa_list if taxon not in miss_spelled_list]
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
            print "taxa_list", taxa_list
            return "XXX"

    """
    def getCorrectedTaxa( self, nwk ):
        from lib.phylogelib import getTaxa
        taxa = [taxon.lower() for taxon in getTaxa( nwk ) ]
        rel_dict = {}
        for taxon in taxa:
            related_name = self.correct( taxon )
            if related_name:
                rel_dict[taxon] = related_name
        return rel_dict
    """     
if __name__ == "__main__":
    ref = TaxonomyReference( "taxonomy.csv" )
    print "rattus>", ref.correct( "rattus" )
    print "rats>", ref.correct( "rats" )
    print "ratus>", ref.correct( "ratus" )

