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
        self.collection = []
        self.named_tree = {}
        self.path = "templates/"

    def _presentation( self, file_name, error="" ):
        full_path = os.path.join( self.path, file_name )
        ext = os.path.splitext( file_name )[1]
#        if ext == ".pyhtml":
        self.pleet.setTemplate( open(full_path).read() )
        self.pleet["error"] = error
        return self.pleet.render()
#        elif ext in ( ".html", ".htm", ".xhtml" ) :
#            return open( full_path ).read() 
#        else:
#            raise TypeError, "Wrong template type %s" % file_name

    @cherrypy.expose
    def css( self ):
        return open( "templates/site.css" ).read()

    @cherrypy.expose
    def index( self, error = "" ):
        return self._presentation( "index.html" )
    
    @cherrypy.expose
    def check( self, myFile=None, index=1, target="html" ):
        # return PhylogenicTree( myFile, self.reference ).display("html")
        try:
            if myFile is not None:
                self.named_tree = {}
                self.collection = []
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
                collection = collection.strip()
                # Nexus collection
                if collection[:6].lower() == "#nexus":
                    for tree in collection.split(";")[1:-2]:
                        tree = tree.strip()
                        nwktree = tree.split("=")[1]
                        tree_name = tree.split("=")[0].split()[1]
                        self.collection.append( nwktree )
                        self.named_tree[nwktree] = tree_name
                # Phylip collection
                else:
                    self.collection = [col for col in collection.strip().split( ";" ) if col]
            self.pleet["collection"] = self.collection
            self.pleet["target"] = target.strip()
            self.pleet["index"] = int(index)
            self.pleet["reference"] = self.reference
            self.pleet["named_tree"] = self.named_tree
            return self._presentation( "check.html" )
        except IndexError:
            return self._presentation( "index.html", error = "No Phylip or Nexus collection found")

        
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
