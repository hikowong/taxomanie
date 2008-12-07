from django.core.management import setup_environ
from phylocore_itis import settings
setup_environ(settings)
from djangophylocore.models import *
