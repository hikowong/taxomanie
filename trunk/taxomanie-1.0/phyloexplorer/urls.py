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

urlpatterns += patterns('views',
    # Example:
    #(r'^taxomanie/', include('taxomanie.phylocore.urls')),

    (r'^phyloexplorer/get_img_url/(?P<taxon>.*)$', 'get_img_url'),
    (r'^phyloexplorer/get_images$', 'get_images'),
    (r'^phyloexplorer/autocomplete$', 'autocomplete'),
    (r'^phyloexplorer/get_matrix$', 'get_matrix'),
    (r'^phyloexplorer/single_reference_tree/(?P<idtree>.*)$', 'single_reference_tree'),
    (r'^phyloexplorer/get_tree_source/(?P<idtree>.*)$', 'get_tree_source'),
    (r'^phyloexplorer/get_tree_arborescence/(?P<idtree>.*)$', 'get_tree_arborescence'),
    (r'^phyloexplorer/get_phyfi_tree_image_url/(?P<idtree>.*)$', 'get_phyfi_tree_image_url'),
    (r'^phyloexplorer/get_phyfi_reference_tree_image_url/(?P<idtree>.*)$', 'get_phyfi_reference_tree_image_url'),
    (r'^phyloexplorer/browse_images$', 'browse_images'),
    (r'^phyloexplorer/progressbar$', 'progressbar'),
    (r'^phyloexplorer/suggestions$', 'suggestions'),
    (r'^phyloexplorer/reference_tree$', 'reference_tree'),
    (r'^phyloexplorer/filter_collection$', 'filter_collection'),
    (r'^phyloexplorer/recreate_collection$', 'recreate_collection'),
    (r'^phyloexplorer/statistics$', 'statistics'),
    (r'^phyloexplorer/browse$', 'browse'),
    (r'^phyloexplorer/download_correction$', 'download_correction'),
    (r'^phyloexplorer/downloadCollection$', 'downloadCollection'),
    (r'^phyloexplorer/download_reference_tree$', 'download_reference_tree'),
    (r'^phyloexplorer/help$', 'help'),
    (r'^phyloexplorer/about$', 'about'),
    (r'^phyloexplorer/$', 'index'),
    (r'^phyloexplorer$', 'index'),

    #(r'^articles/(\d{4})/$', 'news.views.year_archive'),
    #(r'^articles/(\d{4})/(\d{2})/$', 'news.views.month_archive'),
    #(r'^articles/(\d{4})/(\d{2})/(\d+)/$', 'news.views.article_detail'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
)


