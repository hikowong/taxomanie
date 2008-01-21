
from tools.taxocheck import TaxoCheck
from tools import reference
import os

class Species( object ):
    """
    Class which represente a species
    """

    TAXONOMY_THESAURUS = reference.TBN.keys()
    
    def __init__( self, name=None, name_id=None, parent=None ):
        self.name_id = name_id
        self.name = name
        self.parent = parent
        self.children = []
        self.url = self.getWebUrl()

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

    def checkName( self ):
        """
        return the real name of the species
        
        @return : list
        """
        if not self.isValid():
            return TaxoCheck( self.TAXONOMY_THESAURUS ).correct( self.name )
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

    def setName( self, name ):
        self.name = Name

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

