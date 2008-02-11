import os
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)
import sys
sys.path.insert( 0, "lib" )

import cherrypy
from cherrypy.lib import static

from lib import phylogelib
from phylogenictree import PhylogenicTree
from treecollection import TreeCollection
from taxobject import Taxobject 
# from pleet.pleet import Pleet

class Taxomanie( Taxobject ):
    
    reference = None

    def __init__( self ):
        if self.reference is None:
            from referencetree import ReferenceTree
            Taxomanie.reference = ReferenceTree()
        self.collection = []
        self.named_tree = {}
        self.path = "templates/"

#    def _presentation( self, file_name, error="" ):
#        full_path = os.path.join( self.path, file_name )
#        ext = os.path.splitext( file_name )[1]
##        if ext == ".pyhtml":
#        self.pleet.setTemplate( open(full_path).read() )
#        self.pleet["error"] = error
#        return self.pleet.render()
##        elif ext in ( ".html", ".htm", ".xhtml" ) :
##            return open( full_path ).read() 
#        else:
#            raise TypeError, "Wrong template type %s" % file_name

    @cherrypy.expose
    def css( self ):
        return open( "templates/site.css" ).read()

    @cherrypy.expose
    def index( self, msg = "" ):
        return self._presentation( "index.html", msg )
    
    @cherrypy.expose
    def check( self, myFile=None, index=1, target="text" ):
        # return PhylogenicTree( myFile, self.reference ).display("html")
        try:
            if myFile is not None:
                self.named_tree = {}
                self.collection = []
                if isinstance( myFile, str ):
                    input = myFile 
                else:
                    size = 0
                    input = ""
                    while True:
                        recv = myFile.file.read(8192)
                        input += recv
                        if not recv:
                            break
                        size += len(recv)
                input = input.strip()
                try:
                    self.collection = TreeCollection( input, self.reference )
                except ValueError, e:
                    return self._presentation( "index.html", msg = e)
            print self.collection.collection
            self._pleet["_collection_"] = self.collection.collection
            self._pleet["_target_"] = target.strip()
            self._pleet["_index_"] = int(index)
            return self._presentation( "check.html" )
        except IndexError:
            return self._presentation( "index.html", msg = "No Phylip or Nexus collection found")

        
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
