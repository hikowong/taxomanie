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
import string

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
    def sessionexpired( self ):
        pagedef = "Home > Expired session"
        return self._presentation( "sessionexpired.html", pagedef = pagedef )

    @cherrypy.expose
    def css( self ):
        return open( "templates/site.css" ).read()

    @cherrypy.expose
    def index( self, msg = "" ):
        print cherrypy.session.keys()
        cherrypy.session.clear()
        print cherrypy.session.keys()
        return self._presentation( "index.html", msg, pagedef = "Home > Upload Collection")
    

    @cherrypy.expose
    def check( self,  myFile=None, index=1, query=None, clear_query=False, delimiter="_" ):
        pagedef = "Home > Upload Collection > Collection visualization"
        try:
            _msg_ = self.__initCollection( myFile, query, clear_query, delimiter )
        except AttributeError: # if session expired
            return self.sessionexpired()
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

    def __didYouMeanProxy( self, name ):
        name = "+".join(name.strip().split() )
        conn = httplib.HTTP( self.proxy )
        conn.putrequest( 'GET',"http://www.ncbi.nlm.nih.gov//Taxonomy/Browser/wwwtax.cgi?name="+name )
        conn.putheader('Accept', 'text/html')
        conn.putheader('Accept', 'text/plain')
        conn.endheaders()
        errcode, errmsg, headers = conn.getreply()
        f=conn.getfile()
        contenu = f.read()
        conn.close()    
        contenu = contenu.split( "<!--  the contents   -->" )[1]
        contenu = contenu.split( "<!--  end of content  -->" )[0]
        contenu = contenu.split( "<a " )[1:]
        my_meaning_list = []
        ncbi_url = "http://www.ncbi.nlm.nih.gov"
        for i in contenu:
            link_body = i.split( "</a>" )[0]
            link_body = link_body.replace( "/Taxonomy/", ncbi_url+"/Taxonomy/")
            my_meaning_list.append( """<a class="species" target="_blank" """+link_body+"</a>" )
        return ", ".join( my_meaning_list)

    def __didYouMean( self, name ):
        name = "+".join(name.strip().split() )
        conn = httplib.HTTPConnection("www.ncbi.nlm.nih.gov")
        conn.request("GET", "/Taxonomy/Browser/wwwtax.cgi?name="+name)
        contenu = conn.getresponse().read()
        conn.close()    
        contenu = contenu.split( "<!--  the contents   -->" )[1]
        contenu = contenu.split( "<!--  end of content  -->" )[0]
        contenu = contenu.split( "<a " )[1:]
        my_meaning_list = []
        ncbi_url = "http://www.ncbi.nlm.nih.gov"
        for i in contenu:
            link_body = i.split( "</a>" )[0]
            link_body = link_body.replace( "/Taxonomy/", ncbi_url+"/Taxonomy/")
            my_meaning_list.append( """<a class="species" target="_blank" """+link_body+"</a>" )
        return ", ".join( my_meaning_list)


    @cherrypy.expose
    def getAllSugestions( self ):
        bad_taxa_list = cherrypy.session.get("collection").bad_taxa_list
        result = ""
        if bad_taxa_list:
            for badtaxon in bad_taxa_list:
                if self.proxy:
                    did_you_mean_result = self.__didYouMeanProxy( badtaxon )
                else:
                    did_you_mean_result = self.__didYouMean( badtaxon )
                result += """<font color='red'>
                  <b>%s</b> 
                  <span class="didyoumean"> 
                  <i> Did you mean</i> : %s <br />
                  </span>
                  </font>
                  """ % (badtaxon, did_you_mean_result )
        return result

    def getStat1( self, sort ):
        resultlist = cherrypy.session.get("collection").statNbTreeWithNbNodes()
        result = ""
        #short by nbtaxa
        if sort == "nbtaxa":
            new_resultlist = []
            for i, j in resultlist:
                new_resultlist.append( (j,i) )
            resultlist = new_resultlist
        resultlist.sort()
        resultlist.reverse()
        nbtaxa_max, nop = max( resultlist ) 
        for res in resultlist:
            if sort == "nbtaxa":
                nbtaxon, nbtree = res
            else:
                nbtree, nbtaxon = res
            nbtreepourcent = nbtree*100/nbtaxa_max
            bar = string.center( "-<b>"+str(nbtreepourcent)+"%</b>-|", nbtree*70/nbtaxa_max )
            bar = bar.replace( " ", "&nbsp;&nbsp;|" ).replace( "-", "&nbsp;")
            bar = """<span class="statMetric">"""+bar+"</span>"
            base = "["+string.center( str(nbtaxon), 4)+"]"
            base = base.replace( " ", "&nbsp;" )
            result += "<tt>"+base+"</tt>&nbsp;"+bar+"&nbsp;("+str(nbtree)+" trees)<br />\n"
        return result

    def getStat2( self, sort ):
        resultlist = cherrypy.session.get("collection").statNbTreeWithNode()
        result = ""
        # get the max len of taxon name 
        nbtaxa_max, nop = max( resultlist ) 
        taxon_name_max = 0 
        for nbtaxa, taxon_name in resultlist:
            if len(taxon_name) > taxon_name_max:
                taxon_name_max = len(taxon_name)
        #short by names
        if sort == "names":
            new_resultlist = []
            for i, j in resultlist:
                new_resultlist.append( (j,i) )
            resultlist = new_resultlist
        resultlist.sort()
        for res in resultlist:
            if sort=="names":
                taxon, nbtree = res
            else:
                nbtree, taxon = res
            nbtreepourcent = nbtree*100/nbtaxa_max
            bar = string.center( "-<b>"+str(nbtreepourcent)+"%</b>-|", nbtree*70/nbtaxa_max )
            bar = bar.replace( " ", "&nbsp;&nbsp;|" ).replace( "-", "&nbsp;")
            bar = """<span class="statMetric">"""+bar+"</span>"
            base = "["+string.center( str(taxon), taxon_name_max)+"]"
            base = base.replace( " ", "&nbsp;" )
            if cherrypy.session.get("query"):
                last_query = "+and+"+cherrypy.session.get("query")
            else:
                last_query = ""
            result += "<tt>"+base+"</tt>&nbsp;"+bar+"&nbsp;("+\
              '<a href="/statistics?query=%7B'+taxon+'%7D'+last_query+'">'+ \
              str(nbtree)+"</a> trees)<br />\n"
        return result

    @cherrypy.expose
    def statistics( self, myFile=None, query=None, clear_query=False,
      delimiter="_", sortby_stat1="", sortby_stat2="" ):
        try:
            _msg_ = self.__initCollection( myFile, query, clear_query, delimiter )
        except AttributeError: # if session expired
            return self.sessionexpired()
        cherrypy.session.get("collection").initStat()
        self._pleet["_query_"] = cherrypy.session.get("query")
        self._pleet["_clearquery_"] = clear_query
        self._pleet["_ncbitree_"] = cherrypy.session.get("collection").displayStats()
        self._pleet["_nbtaxa_"] = len(cherrypy.session.get("collection").taxa_list)
        self._pleet["_nbtree_"] = len( cherrypy.session.get("collection").getCollection() )
        self._pleet["_badtaxalist_"] = cherrypy.session.get("collection").bad_taxa_list
        self._pleet["_homonymlist_"] = cherrypy.session.get("collection").homonyms.keys()
        self._pleet["_disphomonym_"] = cherrypy.session.get("collection").displayHomonymList()
        cherrypy.session["sortby_stat1"] = sortby_stat1 or cherrypy.session.get("sortby_stat1") or "trees"
        cherrypy.session["sortby_stat2"] = sortby_stat2 or cherrypy.session.get("sortby_stat2") or "trees"
        self._pleet["_sortby_stat1_"] = cherrypy.session.get("sortby_stat1")
        self._pleet["_sortby_stat2_"] = cherrypy.session.get("sortby_stat2")
        if cherrypy.session.get( "collection" ).getCollection():
            self._pleet["_stat1_"] = self.getStat1( cherrypy.session.get("sortby_stat1") )
            self._pleet["_stat2_"] = self.getStat2( cherrypy.session.get("sortby_stat2") )
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
        return open( "templates/"+imagename, "rb").read()

    @cherrypy.expose
    def getJquery( self ):
        return open( "templates/jquery-1.2.3.js").read()

    @cherrypy.expose
    def getJavascript( self ):
        result =  open( "templates/jquery-1.2.3.js").read()
        result +=  open( "templates/jquery.blockUI.js").read()
        result += open( "templates/phyloexplorer.js").read()
        #return open( "templates/phyloexplorer.js").read()
        return result

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
          "tools.sessions.timeout" : 1800 , #30 minutes
          "tools.sessions.on" : True,
          "server.socket_host": ip,
          "server.socket_port": port,
          "server.thread_pool": thread_pool 
        })
    # Start the CherryPy server.
    cherrypy.server.quickstart()
    cherrypy.engine.start()
