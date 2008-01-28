
class TaxonomyReference( object ):
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
    """

    def __init__( self, file ):
        taxonomy = open( file )
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

    def correct( self, name ):
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
            synonym_list = self.getNameFromSynonym( name )
            if synonym_list:
                return synonym_list
            else:
                common_list = self.getNameFromCommon( name )
                if common_list:
                    return common_list
                else:
                    from spellcheck import SpellCheck
                    splchk = SpellCheck( self.TAXONOMY.iterkeys() )
                    return splchk.correct( name )

        
if __name__ == "__main__":
    ref = TaxonomyReference( "taxonomy.csv" )
    print "rattus>", ref.correct( "rattus" )
    print "rats>", ref.correct( "rats" )
    print "ratus>", ref.correct( "ratus" )

