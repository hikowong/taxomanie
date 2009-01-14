# Django settings for taxomanie project.

##############################################################################
################# Please edit this section for your needs ####################

DATABASE_ENGINE = 'mysql'           # 'mysql' or 'sqlite3'

# If you choosed mysql please fill the lines bellow
DATABASE_NAME = 'phylocore_ncbi'    # Database name
DATABASE_USER = 'root'    # User name
DATABASE_PASSWORD = 'mysql'     # Password for the user
# You can also pass optional database informations
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

###############################################################################
################################ DON'T EDIT ###################################

TAXONOMY_ENGINE = 'ncbi'            # 'ncbi" or 'itis'
DEBUG = False
ADMINS = []

assert TAXONOMY_ENGINE == 'ncbi', "TAXONOMY_ENGINE must be 'ncbi'"
assert DATABASE_ENGINE in ['mysql','sqlite3'], "DATABASE_ENGINE must be 'mysql' or 'sqlite3'"

import os
ROOT_PATH = os.path.join(os.getcwd(), os.path.dirname(__file__) )

TEMPLATE_DEBUG = DEBUG
MANAGERS = ADMINS

# For sqlite3
if DATABASE_ENGINE == 'sqlite3':
    import phylocore_ncbi
    DATABASE_PATH = os.path.join( os.path.split( phylocore_ncbi.__file__ )[0] )
    DATABASE_NAME = os.path.join( DATABASE_PATH, 'phylocore_%s.db' % TAXONOMY_ENGINE )    # Or path to database file if using sqlite3.
elif DATABASE_ENGINE == 'mysql':
    pass
else:
    raise RuntimeError, "Database engine %s not supported" % DATABASE_ENGINE

TEST_DATABASE_NAME = 'test_phylocore'
#BOOST_SQLITE = False

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'uiq_^0i!e3kw+dtt$w_wiz-03%hp6m=(v9k1$5)zyq$r!j8h5!'

TAXONOMY_TARGET_URL = {
  "ncbi":"http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=",
  "itis":"http://www.itis.gov/servlet/SingleRpt/SingleRpt?search_topic=TSN&search_value="
}

INSTALLED_APPS = (
#    'django_extensions',
    'djangophylocore',
)
