# Django settings for taxomanie project.

##############################################################################
################# Please edit this section for your needs ####################

DATABASE_ENGINE = 'sqlite3'           # 'mysql' or 'sqlite3'

# If you choosed mysql please fill the lines bellow
DATABASE_NAME = ''    # Database name
DATABASE_USER = ''    # User name
DATABASE_PASSWORD = ''     # Password for the user
# You can also pass optional database informations
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

###############################################################################
################################ DON'T EDIT ###################################

TAXONOMY_ENGINE = 'itis' 
DEBUG = False
ADMINS = []

assert TAXONOMY_ENGINE == 'itis', "TAXONOMY_ENGINE must be 'itis'"
assert DATABASE_ENGINE in ['mysql','sqlite3'], "DATABASE_ENGINE must be 'mysql' or 'sqlite3'"

import os
ROOT_PATH = os.path.join(os.getcwd(), os.path.dirname(__file__) )

TEMPLATE_DEBUG = DEBUG
MANAGERS = ADMINS

# For sqlite3
if DATABASE_ENGINE == 'sqlite3':
    import phylocore_itis
    DATABASE_PATH = os.path.join( os.path.split( phylocore_itis.__file__ )[0] )
    DATABASE_NAME = os.path.join( DATABASE_PATH, 'phylocore_%s.db' % TAXONOMY_ENGINE )    # Or path to database file if using sqlite3.
elif DATABASE_ENGINE == 'mysql':
    pass
else:
    raise RuntimeError, "Database engine %s not supported" % DATABASE_ENGINE

TEST_DATABASE_NAME = 'test_phylocore'
#BOOST_SQLITE = False

TAXONOMY_TARGET_URL = {
  "ncbi":"http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=",
  "itis":"http://www.itis.gov/servlet/SingleRpt/SingleRpt?search_topic=TSN&search_value="
}

INSTALLED_APPS = (
#    'django_extensions',
    'djangophylocore',
)
