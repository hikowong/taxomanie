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

TAXONOMY_ENGINE = 'ncbi'            # 'ncbi" or 'itis'
DEBUG = False
ADMINS = []

assert TAXONOMY_ENGINE == 'ncbi', "TAXONOMY_ENGINE must be 'ncbi'"
assert DATABASE_ENGINE in ['mysql','sqlite3'], "DATABASE_ENGINE must be 'mysql' or 'sqlite3'"

# This is useful for apache
try:
    import matplotlib
    matplotlib.use('Agg')
except:
    pass

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

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
#TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
#LANGUAGE_CODE = 'fr-fr'

#SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
#USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
#MEDIA_ROOT = os.path.join( ROOT_PATH, 'templates' )
#MEDIA_ROOT = '/home/taxomanie/phyloexplorer/templates'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
#MEDIA_URL = 'http://localhost/site_media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
#ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'uiq_^0i!e3kw+dtt$w_wiz-03%hp6m=(v9k1$5)zyq$r!j8h5!'

# List of callables that know how to import templates from various sources.
#TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.load_template_source',
#    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
#)

#MIDDLEWARE_CLASSES = (
#    'django.middleware.common.CommonMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#)

TAXONOMY_TARGET_URL = {
  "ncbi":"http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=",
  "itis":"http://www.itis.gov/servlet/SingleRpt/SingleRpt?search_topic=TSN&search_value="
}

#ROOT_URLCONF = 'urls'

#SESSION_ENGINE = 'django.contrib.sessions.backends.file'

#SESSION_FILE_PATH = '/tmp'

#TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
#    os.path.join( ROOT_PATH, "templates" ),
#    '/var/www/site_media/',
    #"/home/taxomanie/phyloexplorer/templates",
#)

INSTALLED_APPS = (
#    'django.contrib.auth',
#    'django.contrib.contenttypes',
#    'django.contrib.sessions',
#    'django.contrib.sites',
#    'django_extensions',
    'djangophylocore',
)
