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
    
    reference = None

    @cherrypy.expose
    def index( self ):
        return """
        <html><body>
            <fieldset>
            <legend> Your collection file in newick format </legend>
            <form action="check" method="post" enctype="multipart/form-data">
            filename: <input type="file" name="myFile" /><br />
            <input type="submit" />
            </form>
            </fieldset>
            or
            <fieldset>
            <legend> Your string in newick format </legend>
            <form action="check" method="post" enctype="multipart/form-data">
            <textarea rows="10" cols="60" name="myFile"></textarea><br />
            <input type="submit" />
            </form>
            </fieldset>
        </body></html>
        """
    
    @cherrypy.expose
    def check(self, myFile):
        if self.reference is None:
            from referencetree import ReferenceTree
            Taxomanie.reference = ReferenceTree()

        out = """<html>
        <body>
            <ul>
            %s
            </ul>
        </body>
        </html>"""
        
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

        output = ""
        for tree in collection.split(";"):
            tree = tree.strip()    
            if tree:
                print "processing tree..."
                mytree = PhylogenicTree( tree, self.reference )
                print "processing display..."
                output += mytree.display( target = "html" )
                output += "<hr />\n"
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
