
import species

class Taxon( species.Species ):
    """
    Class which represente a Taxon
    """
    
    def __init__( self, name_id, name, parent=None ):
        super( Taxon, self ).__init__( name_id, name, parent )

    def display( self ):
        """
        Return the representation in html code

        @return: string
        """
        pass
