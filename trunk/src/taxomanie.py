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
            import httplib
            self.conn = httplib.HTTP('www.info-ufr.univ-montp2.fr:3128')
        self.collection = []
        self.named_tree = {}

    @cherrypy.expose
    def css( self ):
        return open( "templates/site.css" ).read()

    @cherrypy.expose
    def index( self, msg = "" ):
        return self._presentation( "index.html", msg )
    
    @cherrypy.expose
    def check( self, myFile=None, index=1, querry=None ):
        # return PhylogenicTree( myFile, self.reference ).display("html")
        index = int( index )
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
            if querry is not None:
                try:
                    self._pleet["_collection_"] = self.collection.querry( querry )
                except:
                    self._pleet["_collection_"] = self.collection.collection
                    self._pleet["_msg_"] = "arf"
            else:
                self._pleet["_collection_"] = self.collection.collection
            if index > len(self.collection.collection):
                index = len(self.collection.collection)
            elif index < 1:
                index = 1
            self._pleet["_index_"] = index
            return self._presentation( "check.html" )
        else:#except IndexError:
            return self._presentation( "index.html", msg = "No Phylip or Nexus collection found")

    @cherrypy.expose
    def getImgUrl( self, taxon ):
        taxon = taxon.split()[0].strip().capitalize()
        self.conn.putrequest( 'GET',"http://species.wikimedia.org/wiki/"+taxon )
        self.conn.putheader('Accept', 'text/html')
        self.conn.putheader('Accept', 'text/plain')
        self.conn.endheaders()
        errcode, errmsg, headers = self.conn.getreply()
        f=self.conn.getfile()
        for line in f.readlines():
            if "thumbinner" in line:
                url_img = line.split("thumbinner")[1].split("<img")[1].split("src=\"")[1].split("\"")[0].strip()
                self.conn.close()    
                return url_img
        self.conn.close()    
        return ""
        
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
