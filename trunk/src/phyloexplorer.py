#!/usr/bin/env python
import sys
sys.path.insert( 0, "lib" )
import cherrypy
from phylocore.treecollection import TreeCollection
import ConfigParser
import httplib
import string

from pleet.pleet import Pleet
import os.path

import os
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)


class Taxobject( object ):

    _path_templates = os.path.join( absDir,"..","share","phyloexplorer","templates" )
    _pleet = Pleet()
    
    def _presentation( self, filename, msg="", pagedef="" ):
        full_path = os.path.join( self._path_templates, filename )
        self._pleet.setTemplate(
          self.header() + open(full_path).read() + self.footer() )
        self._pleet["_msg_"] = msg
        self._pleet["_pagedef_"] = pagedef
        return self._pleet.render()

class PhyloExplorer( Taxobject ):
    
    reference = None

    def __init__( self ):
        if self.reference is None:
            from phylocore.taxonomyreference import TaxonomyReference
            PhyloExplorer.reference = TaxonomyReference( 
              os.path.join( absDir, "..", "share", "phyloexplorer","data", "taxonomy.csv" ) )
        self._taximage_url = {}
        self.__loadProxy()

    def header( self ):
        return open( os.path.join( absDir, "..",
          "share","phyloexplorer","templates","header.html" )).read()

    def footer( self ):
        return open( os.path.join( absDir, "..",
          "share","phyloexplorer","templates","footer.html" )).read()

    def __loadProxy( self ):
        config = ConfigParser.ConfigParser()
        if os.path.exists( os.path.join( os.environ["HOME"],
          ".phyloexplorer" )):
            path = os.path.join( os.environ["HOME"], ".phyloexplorer")
        else:
            path = os.path.join(absDir, "..", "share", "phyloexplorer", "etc",
              "phyloexplorer.conf" )
        config.read( path )
        try:
            self.proxy = config.get("global","proxy").strip("\"")
        except:
            self.proxy = ""

    def __initCollection( self, myFile=None, query=None, clear_query=False, delimiter="_" ):
        if myFile is not None:
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
        _msg_ = ""
        if query is not None and query == "":
            clear_query = True
        if query:
            cherrypy.session.get("collection").clearQuery()
            cherrypy.session["query"] = query
            try:
                cherrypy.session.get("collection").query( query )
            except NameError, e:
                _msg_ = "Bad taxon name : %s" % e
            except SyntaxError, e:
                _msg_ = "Bad query : %s" % query
        if clear_query:
            cherrypy.session["query"] = None
            cherrypy.session.get("collection").clearQuery()
        self._pleet["_collection_"] = cherrypy.session.get("collection").getCollection()
        return _msg_

    @cherrypy.expose
    def css( self ):
        return open( os.path.join( absDir, "..",
          "share","phyloexplorer","templates","site.css" )).read()

    @cherrypy.expose
    def index( self, msg = "" ):
        cherrypy.session.clear()
        return self._presentation( "index.html", msg, pagedef = "Home > Upload Collection")
    

    @cherrypy.expose
    def check( self,  myFile=None, index=1, query=None, clear_query=False, delimiter="_" ):
        pagedef = "Home > Upload Collection > Collection visualization"
        try:
            _msg_ = self.__initCollection( myFile, query, clear_query, delimiter )
        except AttributeError: # if session expired
            return self._presentation( "error.html",
              msg="Your session has expired. Please upload your collection again",
              pagedef="Home > Error" )
        index = int( index )
        cherrypy.session["nbbadtaxa"] = cherrypy.session.get("collection").species_count["XXX"]
        if index > len(cherrypy.session.get("collection").getCollection()):
            index = len(cherrypy.session.get("collection").getCollection())
        elif index < 1:
            index = 1
        self._pleet["_index_"] = index
        self._pleet["_query_"] = cherrypy.session.get("query")
        self._pleet["_clearquery_"] = clear_query
        self._pleet["_cache_"] = cherrypy.session.get("cache")
        self._pleet["_reference_"] = self.reference
        self._pleet["_nbbadtaxa_"] = cherrypy.session.get("nbbadtaxa")
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
            for tree in cherrypy.session.get("collection").getCollection():
                body += "Tree %s = %s;\n" % (tree["name"], tree["tree"])
            body += "end;\n"
        else:
            body = ";\n".join( tree["tree"] for tree in cherrypy.session.get("collection").getCollection() )
        cherrypy.response.headers['Content-Length'] = len(body)
        cherrypy.response.headers['Content-Disposition'] = \
          'attachment; filename=filtered_tree_collection-%s.nwk' % (
            cherrypy.session.get('id_download') )
        cherrypy.response.body = body 
        return cherrypy.response.body

    @cherrypy.expose
    def downloadNCBITree( self ):
        cherrypy.session["id_download"] += 1
        body = cherrypy.session.get("collection").getNCBITreeAsNwk()
        cherrypy.response.headers['Content-Length'] = len(body)
        cherrypy.response.headers['Content-Disposition'] = \
          'attachment; filename=NCBI_taxonomy_tree_of_your_species-%s.nwk' % (
            cherrypy.session.get('id_download') )
        cherrypy.response.body = body 
        return cherrypy.response.body

    def __getNCBIDidYouMean( self ):
        my_meaning_list = {}
        for badtaxon in cherrypy.session.get("collection").bad_taxa_list:
            if self.proxy:
                conn = httplib.HTTP( self.proxy )
                conn.putrequest( 'GET',
                  "http://www.ncbi.nlm.nih.gov//Taxonomy/Browser/wwwtax.cgi?name="+badtaxon )
                conn.putheader('Accept', 'text/html')
                conn.putheader('Accept', 'text/plain')
                conn.endheaders()
                errcode, errmsg, headers = conn.getreply()
                f=conn.getfile()
                contenu = f.read()
                conn.close()    
            else:
                conn = httplib.HTTPConnection("www.ncbi.nlm.nih.gov")
                conn.request("GET", "/Taxonomy/Browser/wwwtax.cgi?name="+badtaxon)
                contenu = conn.getresponse().read()
                conn.close()    
            contenu = contenu.split( "<!--  the contents   -->" )[1]
            contenu = contenu.split( "<!--  end of content  -->" )[0]
            contenu = contenu.split( "<a " )[1:]
            my_meaning_list[badtaxon] = []
            ncbi_url = "http://www.ncbi.nlm.nih.gov"
            for i in contenu:
                link_body = i.split( "</a>" )[0]
                if link_body.split(">")[1] == "<strong":
                    my_meaning_list[badtaxon].append(
                      link_body.split(">")[2].split("[")[0].strip().lower() )
                else:
                    my_meaning_list[badtaxon].append(
                      link_body.split(">")[1].strip().lower() )
        return my_meaning_list
                    
    @cherrypy.expose
    def getAllSugestions( self ):
        path = os.path.join( absDir, "..",
          "share","phyloexplorer","templates","getallsugestions.html" )
        self._pleet.setTemplate( open(path).read() )
        self._pleet["_suggestlist_"] = self.__getNCBIDidYouMean()
        return self._pleet.render()

    def getStat1( self, sort ):
        d_stat = cherrypy.session.get("collection").stat1()
        ratio = sorted( d_stat.keys() )[1]-sorted( d_stat.keys() )[0]
        result = ""
        nbtaxa_max = max( d_stat.values() ) 
        for nbtaxon, nbtree in sorted(d_stat.items()):
            nbtreepourcent = nbtree*100/nbtaxa_max
            bar = " "*( nbtree*70/nbtaxa_max )
            bar = bar.replace( " ", "&nbsp;&nbsp;" )#.replace( "-", "&nbsp;")
            bar = """<span class="statMetric">"""+bar+"</span>"
            if nbtaxon == nbtaxon + ratio-1:
                if nbtaxon:
                    base = "["+string.center( str(nbtaxon), 7)+"]"
                else:
                    base = ""
            else:
                base = "["+string.center( str(nbtaxon)+"-"+str(nbtaxon+ratio-1), 7)+"]"
            base = base.replace( " ", "&nbsp;" )
            if base:
                result += "<tt>"+base+"</tt>&nbsp;"+bar+"&nbsp;<tt>("+str(nbtree)+" trees)</tt><br />\n"
        return result

    def getStat2( self, sort ):
        d_stat = cherrypy.session.get("collection").stat2()
        ratio = sorted( d_stat.keys() )[1]-sorted( d_stat.keys() )[0]
        result = ""
        nbtaxa_max = max( d_stat.values() ) 
        for nbtaxon, nbtree in sorted(d_stat.items()):
            nbtreepourcent = nbtree*100/nbtaxa_max
            bar = " "*( nbtree*70/nbtaxa_max )
            bar = bar.replace( " ", "&nbsp;&nbsp;" )#.replace( "-", "&nbsp;")
            bar = """<span class="statMetric">"""+bar+"</span>"
            if nbtaxon == nbtaxon + ratio-1:
                if nbtaxon:
                    base = "["+string.center( str(nbtaxon), 7)+"]"
                else:
                    base = ""
            else:
                base = "["+string.center( str(nbtaxon)+"-"+str(nbtaxon+ratio-1), 7)+"]"
            base = base.replace( " ", "&nbsp;" )
            if base:
                result += "<tt>"+base+"&nbsp;"+bar+"&nbsp;("+str(nbtree)+" taxa)</tt><br />\n"
        return result


    @cherrypy.expose
    def statistics( self, myFile=None, query=None, clear_query=False,
      delimiter="_", sortby_stat1="", sortby_stat2="" ):
        try:
            _msg_ = self.__initCollection( myFile, query, clear_query, delimiter )
        except AttributeError: # if session expired
            return self._presentation( "error.html",
              msg="Your session has expired. Please upload your collection again",
              pagedef="Home > Error" )
        cherrypy.session.get("collection").initStat()
        self._pleet["_treecollection_"] = cherrypy.session.get("collection")
        self._pleet["_query_"] = cherrypy.session.get("query")
        self._pleet["_clearquery_"] = clear_query
        if 1:#try:
            self._pleet["_ncbitree_"] = cherrypy.session.get("collection").displayStats()
        else:#except:
            return self._presentation( "error.html", msg="Bad collection", pagedef="Home > Error" )
        self._pleet["_nbtaxa_"] = len(cherrypy.session.get("collection").taxa_list)
        self._pleet["_taxalist_"] = cherrypy.session.get("collection").taxa_list
        self._pleet["_nbtree_"] = len( cherrypy.session.get("collection").getCollection() )
        self._pleet["_badtaxalist_"] = cherrypy.session.get("collection").bad_taxa_list
        self._pleet["_homonymlist_"] = cherrypy.session.get("collection").homonyms.keys()
        self._pleet["_disphomonym_"] = cherrypy.session.get("collection").displayHomonymList()
        try:
            self._pleet["_NCBItree_"] = cherrypy.session.get("collection").getNCBITreeAsNwk()
        except:
            return self._presentation( "error.html",
              msg="Bad collection. Please, check your trees.", pagedef="Home > Error" )
        cherrypy.session["sortby_stat1"] = sortby_stat1 or cherrypy.session.get("sortby_stat1") or "trees"
        cherrypy.session["sortby_stat2"] = sortby_stat2 or cherrypy.session.get("sortby_stat2") or "trees"
        self._pleet["_sortby_stat1_"] = cherrypy.session.get("sortby_stat1")
        self._pleet["_sortby_stat2_"] = cherrypy.session.get("sortby_stat2")
        if cherrypy.session.get( "collection" ).getCollection():
            try:
                self._pleet["_stat1_"] = self.getStat1( cherrypy.session.get("sortby_stat1") )
                self._pleet["_stat2_"] = self.getStat2( cherrypy.session.get("sortby_stat2") )
            except:
                return self._presentation( "error.html",
                  msg="Your collection might be contains some empty or incorrect trees...  Please, check your collection.",
                  pagedef="Home > Error" )
        else:
            self._pleet["_stat1_"] = ""
            self._pleet["_stat2_"] = ""
        pagedef = "Home > Upload Collection > Statistics"
        return self._presentation( "statistics.html", msg = _msg_, pagedef = pagedef)


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
    def getImageFond( self, imagename ): #XXX not used
        if imagename not in ["Raster.gif", "NautilusBlack.jpg",\
            "NautilusGrey.jpg", "NautilusGreen.jpg", "NautilusWhite.jpg",\
            "NautilusDarkGreen.jpg"]:
            raise "What do you the fucking do ?!?"
        return open( os.path.join( absDir, "..",
          "share","phyloexplorer","templates",imagename ), "rb").read()

    @cherrypy.expose
    def getJquery( self ):
        return open( os.path.join( absDir, "..",
          "share","phyloexplorer","templates", "jquery-1.2.3.js" )).read()

    @cherrypy.expose
    def getIco( self ):
        return open( os.path.join( absDir, "..",
          "share","phyloexplorer","templates", "favicon.ico" ), "rb").read()


    @cherrypy.expose
    def getJavascript( self ):
        path = os.path.join( absDir, "..",
          "share","phyloexplorer","templates" )
        result =  open( os.path.join( path, "jquery-1.2.3.js")).read()
        result +=  open( os.path.join( path, "jquery.blockUI.js")).read()
        result += open( os.path.join( path, "phyloexplorer.js")).read()
        #return open( "templates/phyloexplorer.js").read()
        return result

    @cherrypy.expose
    def recreateCollection( self, **kwargs ):
        if not kwargs:
            return self._presentation( "statistics.html", msg="You must choose taxon to correct your collection" )
        if not cherrypy.session.get("collection"):
            return self._presentation( "error.html", msg="Your session has expired" )
        new_nwk = cherrypy.session.get("collection").orignial_collection
        for old_name, new_name in kwargs.iteritems():
            new_nwk = new_nwk.replace( old_name, new_name ) 
        return self.statistics( new_nwk )

    @cherrypy.expose
    def createFilteredCollection( self, **kwargs ):
        if not kwargs:
            return self._presentation( "statistics.html", msg="You must choose one or more taxon to restrict your collection" )
        if not cherrypy.session.get("collection"):
            return self._presentation( "error.html", msg="Your session has expired" )
        filtered_list = [i for i in cherrypy.session.get("collection").taxa_list if i not in kwargs]
        return self.statistics( cherrypy.session.get("collection").filter( kwargs.keys() ) )

cherrypy.tree.mount(PhyloExplorer())


if __name__ == '__main__':
    ## Open and parse config file
    config = ConfigParser.ConfigParser()
    if os.path.exists( os.path.join( os.environ["HOME"],
      ".phyloexplorer" )):
        path = os.path.join( os.environ["HOME"], ".phyloexplorer")
    else:
        path = os.path.join(absDir, "..", "share", "phyloexplorer", "etc",
          "phyloexplorer.conf" )
    config.read( path )
    ## Fill variables
    try:
        log_screen = bool(int(config.get("global","log.screen")))
    except:
        log_screen = False
    ip = config.get("global","server.socket_host").strip("\"")
    port = int(config.get("global","server.socket_port"))
    thread_pool = int(config.get("global","server.thread_pool"))
    session_timeout = int(config.get("global","session.timeout"))
    # Fill cherrypy configuration
    cherrypy.config.update({
          "log.screen": log_screen,
          "tools.sessions.timeout" : session_timeout,
          "tools.sessions.on" : True,
          "server.socket_host": ip,
          "server.socket_port": port,
          "server.thread_pool": thread_pool 
        })
    # Start the CherryPy server.
    cherrypy.server.quickstart()
    cherrypy.engine.start()