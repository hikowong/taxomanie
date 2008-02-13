
from pleet.pleet import Pleet
import os.path

class Taxobject( object ):

    _path_templates = "templates/"
    _pleet = Pleet()
    
    def _presentation( self, filename, msg="" ):
        full_path = os.path.join( self._path_templates, filename )
        self._pleet.setTemplate( open(full_path).read() )
        self._pleet["_msg_"] = msg
        return self._pleet.render()
