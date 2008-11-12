from django.conf import settings
from django.conf.urls.defaults import *

import os
ROOT_PATH = os.path.join(os.getcwd(), os.path.dirname(__file__) )

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

if settings.DEBUG:
    urlpatterns = patterns('',
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
      {'document_root': os.path.join( ROOT_PATH, 'templates' )}),
    )
else:
    urlpatterns = patterns('')

urlpatterns += patterns('phylocore.views',
    # Example:
    #(r'^taxomanie/', include('taxomanie.phylocore.urls')),

    (r'^phyloexplorer/get_img_url/(?P<taxon>.*)$', 'get_img_url'),
    (r'^phyloexplorer/recreate_collection$', 'recreate_collection'),
    (r'^phyloexplorer/statistics$', 'statistics'),
    (r'^phyloexplorer/browse$', 'browse'),
    (r'^phyloexplorer/help$', 'help'),
    (r'^phyloexplorer/about$', 'about'),
    (r'^', 'index'),

    #(r'^articles/(\d{4})/$', 'news.views.year_archive'),
    #(r'^articles/(\d{4})/(\d{2})/$', 'news.views.month_archive'),
    #(r'^articles/(\d{4})/(\d{2})/(\d+)/$', 'news.views.article_detail'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
)


