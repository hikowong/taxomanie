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

    @cherrypy.expose
    def css( self ):
        return open( "templates/site.css" ).read()

    @cherrypy.expose
    def index( self, msg = "" ):
        return self._presentation( "index.html", msg )
    
    @cherrypy.expose
    def check( self, myFile=None, index=1, target="text" ):
        # return PhylogenicTree( myFile, self.reference ).display("html")
        if 1:#try:
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
                if 1:#try:
                    self.collection = TreeCollection( input, self.reference )
                else:#except ValueError, e:
                    return self._presentation( "index.html", msg = e)
            print self.collection.collection
            self._pleet["_collection_"] = self.collection.collection
            self._pleet["_target_"] = target.strip()
            self._pleet["_index_"] = int(index)
            return self._presentation( "check.html" )
        else:#except IndexError:
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
