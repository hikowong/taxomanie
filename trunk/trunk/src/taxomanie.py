import os
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)
import sys
sys.path.insert( 0, "lib" )

import cherrypy
from cherrypy.lib import static

from lib import phylogelib
from phylogenictree import PhylogenicTree
from pleet.pleet import Pleet

class Taxomanie(object):
    
    reference = None

    def __init__( self ):
        if self.reference is None:
            from referencetree import ReferenceTree
            Taxomanie.reference = ReferenceTree()
        self.pleet = Pleet()
        self.path = "templates/"

    def _presentation( self, file_name ):
        full_path = os.path.join( self.path, file_name )
        ext = os.path.splitext( file_name )[1]
        if ext == ".pyhtml":
            self.pleet.setTemplate( open(full_path).read() )
            return self.pleet.render()
        elif ext in ( ".html", ".htm", ".xhtml" ) :
            return open( full_path ).read() 
        else:
            raise TypeError, "Wrong template type %s" % file_name

    @cherrypy.expose
    def index( self ):
        return self._presentation( "index.html" )
    
    @cherrypy.expose
    def check(self, myFile):
        if isinstance( myFile, str ):
            collection = myFile 
        else:
            size = 0
            collection = ""
            while True:
                recv = myFile.file.read(8192)
                collection += recv
                if not recv:
                    break
                size += len(recv)
        collection = collection.split( ";" )
        self.pleet["collection"] = collection
        self.pleet["reference"] = self.reference
        return self._presentation( "check.pyhtml" )
        

    @cherrypy.expose
    def display( self, id ):
        # XXX
        return self._presentation( "display.pyhtml" )

    def download(self):
        path = os.path.join(absDir, "pdf_file.pdf")
        return static.serve_file(path, "application/x-download",
                                 "attachment", os.path.basename(path))
    download.exposed = True


cherrypy.tree.mount(Taxomanie())

if __name__ == '__main__':
    import os.path
    # Start the CherryPy server.
    cherrypy.config.update(os.path.join(os.path.dirname(__file__), 'taxomanie.conf'))
    cherrypy.server.quickstart()
    cherrypy.engine.start()
