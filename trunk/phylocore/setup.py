"""A library for dealing with phylogenetic trees

This library provides classes and methods to manipulate phylogenetic trees.
"""

import sys

classifiers = """\
Development Status :: 1 - Alpha
Intended Audience :: Developers
License :: OSI Approved :: CeCILL
Programming Language :: Python
Topic :: Engenering/Scientist
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Unix
"""

from distutils.core import setup

if sys.version_info < (2, 4):
    _setup = setup
    def setup(**kwargs):
        if kwargs.has_key("classifiers"):
            del kwargs["classifiers"]
        _setup(**kwargs)

doclines = __doc__.split("\n")

from distutils.core import setup

import os
if not os.path.exists( "phylocore/data/taxonomy.csv" ):
    os.system( "(cd tools ; ./preproc.py )" )

setup(name="phylocore",
      version="1.0",
      author="Nicolas Clairon, Nicolas Auberval, Sorel Diser",
      maintainer="Nicolas Clairon",
      maintainer_email="phylocore-dev@gmail.com",
      url = "http://code.google.com/p/taxomanie",
      license = "http://www.cecill.info",
      platforms = ["any"],
      description = doclines[0],
      classifiers = filter(None, classifiers.split("\n")),
      long_description = "\n".join(doclines[2:]),
      packages=['phylocore'],
      package_dir={'phylocore': 'phylocore'},
      package_data={'phylocore': ['data/taxonomy.csv']}
      )

