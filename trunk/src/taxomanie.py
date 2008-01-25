"""
"""

import os
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)
import sys
sys.path.insert( 0, "lib" )

import cherrypy
from cherrypy.lib import static

from lib import phylogelib
from species import Species

class Taxomanie(object):
    
    @cherrypy.expose
    def index(self):
        return """
        <html><body>
            <form action="check" method="post" enctype="multipart/form-data">
            filename: <input type="file" name="myFile" /><br />
            <input type="submit" />
            </form>
        </body></html>
        """
    
    @cherrypy.expose
    def check(self, myFile):
        out = """<html>
        <body>
            <ul>
            %s
            </ul>
        </body>
        </html>"""
        
        # Although this just counts the file length, it demonstrates
        # how to read large files in chunks instead of all at once.
        # CherryPy uses Python's cgi module to read the uploaded file
        # into a temporary file; myFile.file.read reads from that.
        size = 0
        data = ""
        while True:
            recv = myFile.file.read(8192)
            data += recv
            if not recv:
                break
            size += len(recv)
         
        result = ""
        for taxon in phylogelib.getTaxa( data ):
            try:
                sp = Species( name = taxon )
                sp = "<a href='http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=%s'> %s </a>" % (
                    sp.id, sp.name )
            except KeyError, e:
                sp = "<strike>%s</strike> %s" % ( taxon, e )
                
            result += "<li> %s </li>\n" % sp 
        return out % result
    
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
