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
from phylogenictree import PhylogenicTree

class Taxomanie(object):
    
    @cherrypy.expose
    def index( self ):
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
        
        size = 0
        data = ""
        while True:
            recv = myFile.file.read(8192)
            data += recv
            if not recv:
                break
            size += len(recv)
         
        print "processing tree..."
        mytree = PhylogenicTree( data )
        print "processing display..."
        output = mytree.display( target = "html" )
        return out % output
    
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
