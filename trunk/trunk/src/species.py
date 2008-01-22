
from tools.taxocheck import TaxoCheck
from tools import reference
import os

class Species( object ):
    """
    Class which represente a species
    """

    TAXONOMY_THESAURUS = reference.TBN.keys()
    TAXONOMY_BY_NAME = reference.TBN
    TAXONOMY_BY_ID = reference.TBI
    TAXONOMY_INDEX = reference.TI
    
    def __init__( self, name=None, id=None ):
        self.taxonomy = None
        self.parent_id = None
        self.id = id
        self.name = name
        if name:
            self.setName( name )
        if id:
            self.setId( id )
        self.children = []
        self.url = self.getWebUrl()

    def setName( self, name ):
        name = name.lower()
        self.name = name
        try:
            self.taxonomy = self.TAXONOMY_BY_NAME[name]
        except KeyError:
            raise KeyError, "Cannot find %s. Do you mean : %s ?" % (
                name, self.checkName( name ) )
        self.id = self.taxonomy["id"]
        self.parent_id = self.taxonomy["parent"]

    def setId( self, id ): 
        self.id = id
        try:
            self.taxonomy = self.TAXONOMY_BY_ID[id]
        except KeyError:
            raise KeyError, "ID not found in reference"
        self.name = self.taxonomy["name"]
        self.parent_id = self.taxonomy["parent"]

    def setChild( self, child ):
        """
        Set the child of species

        @child: species
        """
        self.children.append( child )

    def getParent( self ):
        return Species( id = self.parent_id )

    def __iteritems__( self ):
        for child in self.children:
            yield child

    def isValid( self ): 
        """
        Check if name is well written

        @return: bool
        """
        if self.name.lower() in self.TAXONOMY_THESAURUS:
            return True
        return False

    def checkName( self, name ):
        """
        return the real name of the species
        
        @return : list
        """
        if not self.isValid():
            try:
                l_res = [ self.TAXONOMY_BY_ID[str(i)]["name"] for i in \
                    self.TAXONOMY_INDEX[name] ]
                return l_res
            except KeyError:
                return TaxoCheck( self.TAXONOMY_THESAURUS ).correct( name )
        return []
        
    def pickName( self, name ):
        """
        return the whole name. It can return more than one occurence

        @return : list
        """
        name_list = []
        for words in self.TAXONOMY_THESAURUS:
            if name.lower() in words.lower():
                name_list.append( words )
        return name_list

    def display( self ):
        """
        Return the representation in html code

        @return: string
        """
        pass

    def getWebUrl( self ):
        """
        Return the NCBI web link

        @return: string
        """
        return ""

    def __repr__( self ):
        return "<name=%s, id=%s, parent=%s>" % (
            self.name, self.id, self.getParent().name )

    def __str__( self ):
        return self.name
