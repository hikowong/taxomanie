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
import ConfigParser
import httplib

class Taxomanie( Taxobject ):
    
    reference = None

    def __init__( self ):
        if self.reference is None:
            from taxonomyreference import TaxonomyReference
            Taxomanie.reference = TaxonomyReference()
        self.session = {}
        self.id = 0
        self.__loadProxy()

    def __loadProxy( self ):
        config = ConfigParser.ConfigParser()
        config.read("taxomanie.conf")
        try:
            self.proxy = config.get("global","proxy").strip("\"")
        except:
            self.proxy = ""

    @cherrypy.expose
    def css( self ):
        return open( "templates/site.css" ).read()

    @cherrypy.expose
    def index( self, msg = "" ):
        self.id += 1
        self._pleet["_id_"] = self.id
        return self._presentation( "index.html", msg )
    
    @cherrypy.expose
    def check( self, id,  myFile=None, index=1, query=None, clear_query=False, delimiter="_" ):
        # return PhylogenicTree( myFile, self.reference ).display("html")
        index = int( index )
        id = int(id)
        if 1:#try:
            if myFile is not None:
                self.session[id] = {}
                self.session[id]["query"] = None
                self.session[id]["col_query"] = []
                self.session[id]["cache"] = {}
                self.session[id]["named_tree"] = {}
                self.session[id]["collection"] = []
                self.session[id]["nbbadtaxa"] = 0
                self.reference.delimiter = delimiter
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
                    self.session[id]["collection"] = TreeCollection( input, self.reference )
                    self.session[id]["nbbadtaxa"] = self.session[id]["collection"].species_count["XXX"]
                else:#except ValueError, e:
                    return self._presentation( "index.html", msg = e)
            _msg_ = ""
            if query:
                self.session[id]["query"] = query
            if not clear_query:
                if self.session[id]["query"]:
                    try:
                        self.session[id]["col_query"] = self.session[id][
                          "collection"].query( self.session[id]["query"] )
                        self._pleet["_collection_"] = self.session[id]["col_query"]
                    except NameError, e:
                        self.session[id]["col_query"] = self.session[id]["collection"].collection
                        self._pleet["_collection_"] = self.session[id]["col_query"]
                        _msg_ = "Bad taxon name : %s" % e
                    except SyntaxError, e:
                        _msg_ = "Bad query : %s" % query
                        self.session[id]["col_query"] = self.session[id]["collection"].collection
                        self._pleet["_collection_"] = self.session[id]["col_query"]
                else:
                    self.session[id]["col_query"] = self.session[id]["collection"].collection
                    self._pleet["_collection_"] = self.session[id]["col_query"]
            else:
                self.session[id]["query"] = None
                self.session[id]["col_query"] = self.session[id]["collection"].collection
                self._pleet["_collection_"] = self.session[id]["col_query"]
            if index > len(self.session[id]["collection"].collection):
                index = len(self.session[id]["collection"].collection)
            elif index < 1:
                index = 1
            self._pleet["_index_"] = index
            self._pleet["_query_"] = self.session[id]["query"]
            self._pleet["_clearquery_"] = clear_query
            self._pleet["_cache_"] = self.session[id]["cache"]
            self._pleet["_reference_"] = self.reference
            self._pleet["_id_"] = id
            self._pleet["_nbbadtaxa_"] = self.session[id]["nbbadtaxa"]
            return self._presentation( "check.html", msg = _msg_ )
        else:#except IndexError:
            return self._presentation( "index.html", msg = "No Phylip or Nexus collection found")

    @cherrypy.expose
    def getImgUrl( self, taxon ):
        if self.proxy:
            return self.__getImageUrlProxy( taxon )
        else:
            return self.__getImageUrl( taxon )

    def __getImageUrlProxy( self, taxon ):
        taxon = taxon.split()[0].strip().capitalize()
        conn = httplib.HTTP( self.proxy )
        conn.putrequest( 'GET',"http://species.wikimedia.org/wiki/"+taxon )
        conn.putheader('Accept', 'text/html')
        conn.putheader('Accept', 'text/plain')
        conn.endheaders()
        errcode, errmsg, headers = conn.getreply()
        f=conn.getfile()
        for line in f.readlines():
            if "thumbinner" in line:
                url_img = line.split("thumbinner")[1].split("<img")[1].split("src=\"")[1].split("\"")[0].strip()
                conn.close()    
                return """<img src="%s" class="imgTaxa" />""" % url_img
        conn.putrequest( 'GET',"http://en.wikipedia.org/wiki/"+taxon )
        conn.putheader('Accept', 'text/html')
        conn.putheader('Accept', 'text/plain')
        conn.endheaders()
        errcode, errmsg, headers = conn.getreply()
        f=conn.getfile()
        for line in f.readlines():
            if "class=\"image\"" in line:
                url_img = line.split("class=\"image\"")[1].split("src=\"")[1].split("\"")[0].strip()
                conn.close()    
                return """<img src="%s" class="imgTaxa" />""" % url_img
        conn.close() 
        return "Image not found"

    def __getImageUrl( self, taxon ):
        taxon = taxon.split()[0].strip().capitalize()
        conn = httplib.HTTPConnection("species.wikimedia.org")
        conn.request("GET", "/wiki/"+taxon)
        f = conn.getresponse().read()
        for line in f.split("\n"):
            if "thumbinner" in line:
                url_img = line.split("thumbinner")[1].split("<img")[1].split("src=\"")[1].split("\"")[0].strip()
                conn.close()    
                return """<img src="%s" class="imgTaxa" />""" % url_img
        conn.close()    
        conn = httplib.HTTPConnection("en.wikipedia.org")
        conn.request("GET", "/wiki/"+taxon)
        f = conn.getresponse().read()
        for line in f.split("\n"):
            if "class=\"image\"" in line:
                url_img = line.split("class=\"image\"")[1].split("src=\"")[1].split("\"")[0].strip()
                conn.close()    
                return """<img src="%s" class="imgTaxa" />""" % url_img
        conn.close()    
        return "Image not found"

    @cherrypy.expose
    def downloadCollection(self, id, target="nexus"):
        cherrypy.response.headers['Content-Type'] = 'application/x-download'
        id = int(id)
        if target == "nexus":
            body = "#nexus\nbegin trees;\n"
            for i in xrange( len(self.session[id]["col_query"]) ):
                tree = self.session[id]["col_query"][i]
                body += "Tree %s = %s;\n" % (tree["name"], tree["tree"])#.replace("|XXX", ""))
            body += "end;\n"
        else:
            body = ";\n".join( tree["tree"] for tree in self.session[id]["col_query"] )
        cherrypy.response.headers['Content-Length'] = len(body)
        cherrypy.response.headers['Content-Disposition'] = \
          'attachment; filename=filtered-collection-%s.nwk' % str(id)
        cherrypy.response.body = body 
        return cherrypy.response.body

    @cherrypy.expose
    def getStatImg1( self, id ):
        resultlist = self.session[int(id)]["collection"].statNbTreeWithNbNodes()
        return os.popen( 'python stat1.py "%s"' % resultlist ).read()

    @cherrypy.expose
    def getStatImg2( self, id ):
        resultlist = self.session[int(id)]["collection"].statNbTreeWithNode()
        return os.popen( 'python stat2.py "%s"' % resultlist ).read()

    @cherrypy.expose
    def statistics( self, id ):
        self._pleet["_id_"] = id
        self._pleet["_collection_"] = self.session[int(id)]["col_query"] 
        self._pleet["_ncbitree_"] = self.session[int(id)]["collection"].displayStats(id)
        return self._presentation( "statistics.html" )

    @cherrypy.expose
    def about( self, id ):
        self._pleet["_id_"] = id
        try:
            self._pleet["_collection_"] = self.session[int(id)]["collection"]
        except:
            self._pleet["_collection_"] = []
        return self._presentation( "about.html" )

    @cherrypy.expose
    def help( self, id ):
        self._pleet["_id_"] = id
        try:
            self._pleet["_collection_"] = self.session[int(id)]["collection"]
        except:
            self._pleet["_collection_"] = []
        return self._presentation( "help.html" )

    @cherrypy.expose
    def getImage( self, imagename ): #XXX not used
        return open( imagename, "rb").read()

cherrypy.tree.mount(Taxomanie())


if __name__ == '__main__':
    import os.path
    import ConfigParser
    ## Open and parse config file
    config = ConfigParser.ConfigParser()
    config.read("taxomanie.conf")
    ## Fill variables
    try:
        log_screen = bool(int(config.get("global","log.screen")))
    except:
        log_screen = False
    ip = config.get("global","server.socket_host").strip("\"")
    port = int(config.get("global","server.socket_port"))
    thread_pool = int(config.get("global","server.thread_pool"))
    # Fill cherrypy configuration
    cherrypy.config.update({
          "log.screen": log_screen,
          "server.socket_host": ip,
          "server.socket_port": port,
          "server.thread_pool": thread_pool 
        })
    # Start the CherryPy server.
    cherrypy.server.quickstart()
    cherrypy.engine.start()
