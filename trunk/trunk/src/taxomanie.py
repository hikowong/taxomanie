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
        self._taximage_url = {}
        self.__loadProxy()

    def header( self ):
        return open( "templates/header.html" ).read()

    def footer( self ):
        return open( "templates/footer.html" ).read()

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
        return self._presentation( "index.html", msg, pagedef = "Home > Upload Collection")
    
    @cherrypy.expose
    def check( self,  myFile=None, index=1, query=None, clear_query=False, delimiter="_" ):
        index = int( index )
        if myFile is not None:
            print cherrypy.session.keys()
            cherrypy.session.clear()
            print cherrypy.session.keys()
            cherrypy.session["query"] = None
            cherrypy.session["col_query"] = []
            cherrypy.session["cache"] = {}
            cherrypy.session["named_tree"] = {}
            cherrypy.session["collection"] = []
            cherrypy.session["nbbadtaxa"] = 0
            cherrypy.session["id_download"] = 0
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
            cherrypy.session["collection"] = TreeCollection( input, self.reference )
            cherrypy.session["nbbadtaxa"] = cherrypy.session.get("collection").species_count["XXX"]
        _msg_ = ""
        if query:
            cherrypy.session["query"] = query
        if not clear_query:
            if cherrypy.session.get("query"):
                try:
                    cherrypy.session["col_query"] = cherrypy.session.get(
                      "collection").query( cherrypy.session.get("query") )
                    self._pleet["_collection_"] = cherrypy.session.get("col_query")
                except NameError, e:
                    cherrypy.session["col_query"] = cherrypy.session.get("collection").collection
                    self._pleet["_collection_"] = cherrypy.session.get("col_query")
                    _msg_ = "Bad taxon name : %s" % e
                except SyntaxError, e:
                    _msg_ = "Bad query : %s" % query
                    cherrypy.session["col_query"] = cherrypy.session.get("collection").collection
                    self._pleet["_collection_"] = cherrypy.session.get("col_query")
            else:
                cherrypy.session["col_query"] = cherrypy.session.get("collection").collection
                self._pleet["_collection_"] = cherrypy.session.get("col_query")
        else:
            cherrypy.session["query"] = None
            cherrypy.session["col_query"] = cherrypy.session.get("collection").collection
            self._pleet["_collection_"] = cherrypy.session.get("col_query")
        if index > len(cherrypy.session.get("collection").collection):
            index = len(cherrypy.session.get("collection").collection)
        elif index < 1:
            index = 1
        self._pleet["_index_"] = index
        self._pleet["_query_"] = cherrypy.session.get("query")
        self._pleet["_clearquery_"] = clear_query
        self._pleet["_cache_"] = cherrypy.session.get("cache")
        self._pleet["_reference_"] = self.reference
        self._pleet["_nbbadtaxa_"] = cherrypy.session.get("nbbadtaxa")
        pagedef = "Home > Upload Collection > Collection visualization"
        return self._presentation( "check.html", msg = _msg_, pagedef=pagedef)

    @cherrypy.expose
    def getImgUrl( self, taxon ):
        if self.proxy:
            return self.__getImageUrlProxy( taxon )
        else:
            return self.__getImageUrl( taxon )

    def __getImageUrlProxy( self, taxon ):
        taxon = "_".join(taxon.split()).strip().capitalize()
        if not self._taximage_url.has_key( taxon ):
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
                    self._taximage_url[taxon] = """<img src="%s" class="imgTaxa" />""" % url_img
                    return self._taximage_url[taxon]
            conn.putrequest( 'GET',"http://en.wikipedia.org/wiki/"+taxon )
            conn.putheader('Accept', 'text/html')
            conn.putheader('Accept', 'text/plain')
            conn.endheaders()
            errcode, errmsg, headers = conn.getreply()
            f=conn.getfile()
            for line in f.readlines():
                if "class=\"image\"" in line and not "<img alt=\"\"" in line:
                    url_img = line.split("class=\"image\"")[1].split("src=\"")[1].split("\"")[0].strip()
                    conn.close()    
                    self._taximage_url[taxon] = """<img src="%s" class="imgTaxa" />""" % url_img
                    return self._taximage_url[taxon]
            conn.close() 
            self._taximage_url[taxon] = "Image not found"
        return self._taximage_url[taxon]

    def __getImageUrl( self, taxon ):
        taxon = "_".join(taxon.split()).strip().capitalize()
        if not self._taximage_url.has_key( taxon ):
            conn = httplib.HTTPConnection("species.wikimedia.org")
            conn.request("GET", "/wiki/"+taxon)
            f = conn.getresponse().read()
            for line in f.split("\n"):
                if "thumbinner" in line:
                    url_img = line.split("thumbinner")[1].split("<img")[1].split("src=\"")[1].split("\"")[0].strip()
                    conn.close()    
                    self._taximage_url[taxon] = """<img src="%s" class="imgTaxa" />""" % url_img
                    return self._taximage_url[taxon]
            conn.close()    
            conn = httplib.HTTPConnection("en.wikipedia.org")
            conn.request("GET", "/wiki/"+taxon)
            f = conn.getresponse().read()
            for line in f.split("\n"):
                if "class=\"image\"" in line and not "<img alt=\"\"" in line:
                    url_img = line.split("class=\"image\"")[1].split("src=\"")[1].split("\"")[0].strip()
                    conn.close()    
                    self._taximage_url[taxon] = """<img src="%s" class="imgTaxa" />""" % url_img
                    return self._taximage_url[taxon]
            conn.close()    
            self._taximage_url[taxon] = "Image not found"
        return self._taximage_url[taxon]

    @cherrypy.expose
    def downloadCollection(self, target="nexus"):
        cherrypy.session["id_download"] += 1
        cherrypy.response.headers['Content-Type'] = 'application/x-download'
        if target == "nexus":
            body = "#nexus\nbegin trees;\n"
            for i in xrange( len(cherrypy.session.get("col_query")) ):
                tree = cherrypy.session.get("col_query")[i]
                body += "Tree %s = %s;\n" % (tree["name"], tree["tree"])
            body += "end;\n"
        else:
            body = ";\n".join( tree["tree"] for tree in cherrypy.session.get("col_query") )
        cherrypy.response.headers['Content-Length'] = len(body)
        cherrypy.response.headers['Content-Disposition'] = \
          'attachment; filename=filtered_tree_collection-%s.nwk' % (
            cherrypy.session.get('id_download') )
        cherrypy.response.body = body 
        return cherrypy.response.body

    """
    @cherrypy.expose
    def getStatImg1( self ):
        resultlist = cherrypy.session.get("collection").statNbTreeWithNbNodes()
        return os.popen( 'python stat1.py "%s"' % resultlist ).read()

    @cherrypy.expose
    def getStatImg2( self ):
        resultlist = cherrypy.session.get("collection").statNbTreeWithNode()
        return os.popen( 'python stat2.py "%s"' % resultlist ).read()
    """

    @cherrypy.expose
    def statistics( self ):
        #self._pleet["_collection_"] = cherrypy.session.get("col_query") 
        self._pleet["_badtaxalist_"] = cherrypy.session.get("collection").bad_taxa_list
        self._pleet["_homonymlist_"] = cherrypy.session.get("collection").displayHomonymList()
        self._pleet["_ncbitree_"] = cherrypy.session.get("collection").displayStats()
        pagedef = "Home > Upload Collection > Statistics"
        return self._presentation( "statistics.html", pagedef = pagedef)

    @cherrypy.expose
    def about( self ):
        try:
            self._pleet["_collection_"] = cherrypy.session.get("collection")
        except:
            self._pleet["_collection_"] = []
        return self._presentation( "about.html", pagedef = "Home > About" )

    @cherrypy.expose
    def help( self ):
        try:
            self._pleet["_collection_"] = cherrypy.session.get("collection")
        except:
            self._pleet["_collection_"] = []
        return self._presentation( "help.html", pagedef = "Home > Help" )

    @cherrypy.expose
    def getImage( self, imagename ): #XXX not used
        return open( imagename, "rb").read()

    @cherrypy.expose
    def getJquery( self ):
        return open( "templates/jquery-1.2.3.js").read()

    @cherrypy.expose
    def getJavascript( self ):
        return open( "templates/phyloexplorer.js").read()

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
          "tools.sessions.timeout" : 21600, #6 hours
          "tools.sessions.on" : True,
          "server.socket_host": ip,
          "server.socket_port": port,
          "server.thread_pool": thread_pool 
        })
    # Start the CherryPy server.
    cherrypy.server.quickstart()
    cherrypy.engine.start()
