
from pleet.pleet import Pleet
import os.path

class Taxobject( object ):

    _path_templates = "templates/"
    _pleet = Pleet()
    
    def _presentation( self, filename, msg="", pagedef="" ):
        full_path = os.path.join( self._path_templates, filename )
        self._pleet.setTemplate(
          self.header() + open(full_path).read() + self.footer() )
        self._pleet["_msg_"] = msg
        self._pleet["_pagedef_"] = pagedef
        return self._pleet.render()
