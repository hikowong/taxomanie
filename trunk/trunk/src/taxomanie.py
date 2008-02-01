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
    def css( self ):
        return open( "templates/site.css" ).read()

    @cherrypy.expose
    def index( self ):
        return self._presentation( "index.html" )
    
    @cherrypy.expose
    def check( self, myFile=None, index=0, allparents=0, target="html" ):
        try:
            if myFile is not None:
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
                self.collection = [col for col in collection.strip().split( ";" ) if col]
            self.pleet["collection"] = self.collection
            self.pleet["allparents"] = int(allparents)
            self.pleet["target"] = target.strip()
            self.pleet["index"] = int(index)
            self.pleet["reference"] = self.reference
            return self._presentation( "check.pyhtml" )
        except IndexError:
            return self.index()

        
    def download(self):
        path = os.path.join(absDir, "pdf_file.pdf")
        return static.serve_file(path, "application/x-download",
                                 "attachment", os.path.basename(path))
    download.exposed = True

    @cherrypy.expose
    def about( self ):
        return "not yet"

    @cherrypy.expose
    def help( self ):
        return "not yet"

cherrypy.tree.mount(Taxomanie())

if __name__ == '__main__':
    import os.path
    # Start the CherryPy server.
    cherrypy.config.update(os.path.join(os.path.dirname(__file__), 'taxomanie.conf'))
    cherrypy.server.quickstart()
    cherrypy.engine.start()
