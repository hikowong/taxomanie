#!/usr/bin/env python
import sys
from djangophylocore.models import *
import httplib
import string

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import simplejson
from django.shortcuts import render_to_response
from django.conf import settings

import phyloconf
from djangophylocore.lib.phylogelib import tidyNwk

# Use it for Jinja templates
#from django.http import HttpResponse
#from django.template.context import get_standard_processors
#from jinja2 import Environment, FileSystemLoader, ChoiceLoader
#from django.conf import settings
#
#loaders = []
#for location in settings.TEMPLATE_DIRS:
#    loaders.append(FileSystemLoader(location))
#env = Environment(loader=ChoiceLoader(loaders))
#
#def render_to_response(template, context, request=None):
#    template = env.get_template(template)
#    if request:
#        for processor in get_standard_processors():
#            context.update(processor(request))
#    return HttpResponse(template.render(context))

TAXOREF = TaxonomyReference()
TAXONOMY_TOC = get_taxonomy_toc()
D_PROGRESS = {}
CACHE_PHYFI_URL = {'reference':{}, 'tree':{} }
CACHE_REFERENCE_TREE = {}
CACHE_SUGGESTIONS = {}
TAXONOMY_ENGINE = settings.TAXONOMY_ENGINE

import os.path
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)

if settings.TAXONOMY_ENGINE == "ncbi":
    REFERENCE_ROOT_URL = phyloconf.ITIS_ROOT_URL
elif settings.TAXONOMY_ENGINE == "itis":
    REFERENCE_ROOT_URL = phyloconf.NCBI_ROOT_URL

def index( request ):
    #request.session['progress'] = 0
    global TAXONOMY_ENGINE, REFERENCE_ROOT_URL
    if request.session.get( "nb_taxa", "" ):
        not_empty_collection = True
    else:
        not_empty_collection = False
    return render_to_response( 'index.html', 
      {'msg':'', 'not_empty_collection':not_empty_collection,
      "taxo_engine":TAXONOMY_ENGINE,"ref_url":REFERENCE_ROOT_URL} )

def about( request ):
    global TAXONOMY_ENGINE, REFERENCE_ROOT_URL
    context = {"taxo_engine":TAXONOMY_ENGINE, "ref_url":REFERENCE_ROOT_URL}
    if 'original_collection_id' in request.session:
        context['collection'] = True
    else:
        context['collection'] = False
    return render_to_response( 'about.html', context )

def help( request ):
    global TAXONOMY_ENGINE
    context = {"taxo_engine":TAXONOMY_ENGINE, "ref_url":REFERENCE_ROOT_URL}
    if 'original_collection_id' in request.session:
        context['collection'] = True
    else:
        context['collection'] = False
    return render_to_response( 'help.html', context )

def statistics( request ):
    global TAXONOMY_ENGINE, REFERENCE_ROOT_URL
    print request.session.session_key
    D_PROGRESS[request.session.session_key] = { "initial_load": 0 }
    context = {'error_msg': "", "taxo_engine":TAXONOMY_ENGINE, "ref_url":REFERENCE_ROOT_URL }
    if 'error_msg' in request.session:
        context['error_msg'] = request.session['error_msg']
        del request.session['error_msg']
    if 'new_collection' in request.POST:
        print "upload..."
        if 'myFile' in request.POST:
            input = request.POST['myFile']
            myFile = 1
        if 'myFile' in request.FILES:
            input = request.FILES['myFile'].read()
            myFile = 1
        if "delimiter" in request.POST:
            request.session['delimiter'] = request.POST['delimiter']
        print "... done"
        D_PROGRESS[request.session.session_key]["initial_load"] = 5
        delimiter = request.session['delimiter']
        print "building..."
        try:
            collection = TreeCollection.objects.create( source = input, delimiter = delimiter )
        except Exception, e:
            context['bad_tree_msg'] = e
            return render_to_response( 'statistics.html', context )
        print "... done"
        D_PROGRESS[request.session.session_key]["initial_load"] = 60
        #if 'autocorrection' in request.POST:
        #    collection, list_correction = collection.get_autocorrected_collection()
        request.session['original_collection_id'] = collection.id
        request.session['collection'] = collection
        request.session['correction'] = {}
        #if collection.taxa.count():
        #    d_stat = collection.get_tree_size_distribution()
        #    d_stat = collection.get_taxon_frequency_distribution()
        #print "fin stats"
        request.session['last_query'] = ''
        request.session['collection_changed'] = False
    elif 'query_treebase' in request.POST:
        # XXX mettre progression ici aussi
        print "query_treebase"
        D_PROGRESS[request.session.session_key]["initial_load"] = 5 
        treebase = TreeCollection.objects.get( id = 1 )
        try:
            collection = treebase.get_collection_from_query( request.POST['query_treebase'] )
        except Exception, err:
            error_msg = str('bad query: %s' % err.message)
            context['error_msg'] = error_msg.replace( '<', '&lt;').replace( '>', '&gt;' ) 
            return render_to_response( 'index.html', context )
        request.session['original_collection_id'] = collection.id
        request.session['collection'] = collection
        #if collection.taxa:
        #    d_stat = collection.get_tree_size_distribution()
        #    d_stat = collection.get_taxon_frequency_distribution()
        request.session['last_query'] = ''
        request.session['correction'] = {}
        request.session['collection_changed'] = False
        D_PROGRESS[request.session.session_key]["initial_load"] = 60 
    elif 'clear_collection' in request.GET:
        request.session['collection_changed'] = False
        col_id = request.session['original_collection_id']
        request.session['collection'] = TreeCollection.objects.get( id = col_id )
    print "fin creation collection"
    try:
        collection = request.session['collection']
    except:
        context['bad_tree_msg'] = "Your session has expired"
        return render_to_response( 'statistics.html', context )
    ## Query
    print "quering..."
    query = ''
    if 'query_tree' in request.GET: #FIXME POST
        if not request.session['last_query']:
            query = request.GET['query_tree']
        else:
            query = request.session['last_query'] +' and '+ request.GET['query_tree']
    elif 'query' in request.GET:
        query = request.GET['query']
    if query:
        request.session['last_query'] = query
        query_against_treebase = 'treebase' in request.GET
        try:
            collection = collection.get_collection_from_query( query, query_against_treebase )
        except Exception, err:
            error_msg = str('bad query: %s' % err.message)
            if err.message == "usertaxa":
                error_msg += '. Try to query against TreeBase'
            context['error_msg'].append( error_msg.replace( '<', '&lt;').replace( '>', '&gt;' ) )
        if query_against_treebase:
            context['treebase'] = 'on'
        request.session['collection_changed'] = True
        context['query'] = query
        request.session['collection'] = collection
    print "... done"
    D_PROGRESS[request.session.session_key]["initial_load"] = 65
    ## Dealing collection
    print "extracting informations..."
    if not collection.trees.count(): #Empty collection
        context['not_empty_collection'] = False
        context['bad_tree_msg'] = "Empty collection"
        context['collection_changed'] = request.session['collection_changed']
        return render_to_response( 'statistics.html', context )
    # Proceed collection
    print "reference tree as nwk"
    context['reference_tree'] = collection.get_reference_tree_as_nwk()
    request.session['reference_tree_nwk'] = context['reference_tree']
    print "fin reference tree as nwk"
    context['reference_tree'] = collection.get_reference_tree_as_nwk()
    request.session['current_col_id'] = collection.id
    context['current_col_id'] = collection.id
    context['nb_taxa'] = collection.taxa.count()
    request.session['nb_taxa'] = context['nb_taxa']
    print "nb_taxa"
    context['nb_user_taxa'] = collection.rel.values( 'taxon' ).count()
    request.session['nb_user_taxa'] = context['nb_user_taxa']
    print "nb_user_taxa"
    context['nb_scientifics'] = collection.scientifics.count()
    request.session['nb_scientifics'] = context['nb_scientifics']
    print "nb_scientifics"
    context['nb_trees'] = collection.trees.count()
    request.session['nb_trees'] = context['nb_trees']
    print "nb_trees"
    context['nb_badtaxa'] = collection.bad_taxa.count()
    request.session['nb_badtaxa'] = context['nb_badtaxa']
    print "bad_taxa"
    homonyms_list = collection.homonyms.all()
    context['nb_homonyms'] = homonyms_list.count()
    print "homonyms"
    synonyms_list = collection.synonyms.all()
    context['nb_synonyms'] = synonyms_list.count()
    print "synonyms"
    commons_list = collection.commons.all()
    context['nb_commons'] = commons_list.count()
    print "commons"
    context['not_empty_collection'] = True
    if request.session['correction']:
        context['correction'] = True
    else:
        context['correction'] = False
    print "... done"
    D_PROGRESS[request.session.session_key]["initial_load"] = 85
    # stats
    print "stats..."
    if context['nb_taxa']:
        d_stat = collection.get_tree_size_distribution()
        context['tree_size_distributions'] = get_tree_size_distribution( d_stat )
        d_stat = collection.get_taxon_frequency_distribution()
        context['taxon_frequency_distribution'] = get_taxon_frequency_distribution( d_stat )
        print "fin stats"
        print "fin arbre ncbi"
    else:
        context['tree_size_distributions'] = ""
        context['taxon_frequency_distribution'] = ""
        context['stats_tree'] = None
    print "...done"
    D_PROGRESS[request.session.session_key]["initial_load"] = 90
    print "suggestions..."
    # correct homonyms
    dict_homonyms = {}
    for homonym in homonyms_list:
        dict_homonyms[homonym.name] = []
        for name in homonym.scientifics.values('name'):
            dict_homonyms[homonym.name].extend( name.values() )
    context['dict_homonyms'] = dict_homonyms
    print "fin homonym"
    # correct synonym
    dict_synonym = {}
    for synonym in synonyms_list:
        dict_synonym[synonym.name] = []
        for name in synonym.scientifics.values('name'):
            dict_synonym[synonym.name].extend( name.values() )
    context['dict_synonym'] = dict_synonym
    print "fin synonym"
    # correct common
    dict_common = {}
    for common in commons_list:
        dict_common[common.name] = []
        for name in common.scientifics.values('name'):
            dict_common[common.name].extend( name.values() )
    context['dict_common'] = dict_common
    print "fin common"
    print "...done"
    D_PROGRESS[request.session.session_key]["initial_load"] = 95
    print "bad trees infos..."
    nb_bad_trees = collection.bad_trees.count()
    if nb_bad_trees:
        context['bad_tree_msg'] = "Warning : your collection have %s bad trees. <a href='/phyloexplorer/browse?only_bad_trees=1'> Show them</a>" % nb_bad_trees
    print "...done"
    context['collection_changed'] = request.session['collection_changed']
    D_PROGRESS[request.session.session_key]["initial_load"] = 100
    return render_to_response( 'statistics.html', context )

#def check( request ):
#    #source = Source.objects.get( id = request.session['current_source_id'] )
#    source = None
#    col_id = request.session['current_col_id']
#    collection = TreeCollection.objects.get( id = col_id )
#    paginator = Paginator( collection.trees.all(), 1 )
#    if 'page' in request.GET:
#        tree_index = int( request.GET['page'] )-1
#        if tree_index < 0:
#            tree_index = 0
#        elif tree_index > paginator.count-1:
#            tree_index = paginator.count-1
#        tree = collection.trees.all()[tree_index] 
#    elif 'tree_id' in request.GET:
#        tree_id = request.GET['tree_id']
#        tree = Tree.objects.get( id = tree_id ) 
#        for page_index in paginator.page_range:
#            if tree in paginator.page(page_index).object_list:
#                tree_index = page_index - 1
#    else:
#        tree = collection.trees.all()[0] 
#        tree_index = 0
#    context = {}
#    if not tree.is_valid:
#        context['error_msg'] = "Warning : this tree is not well formated"
#    if 1:#try:
#        context['tree'] = _display_tree( tree.arborescence, source )
#    else:#except:
#        context['error_msg'] = "This tree contains error(s). Please, check the source"
#    context['source'] = tree.source.replace( collection.delimiter, ' ' )
#    context['current_tree_id'] = tree.id
#    context['page'] = paginator.page( tree_index+1 )
#    nb_trees = collection.trees.count()
#    context['enable_select_tree_names'] = nb_trees < 100 and nb_trees > 1
#    context['tree_names_list'] = [(tree.name, tree.id) for tree in collection.trees.iterator()]
#    return render_to_response( 'check.html', context )#TODO Rename to browse
#
def browse( request ):
    global TAXONOMY_ENGINE, REFERENCE_ROOT_URL
    context = {'taxo_engine':TAXONOMY_ENGINE, "ref_url":REFERENCE_ROOT_URL}
    col_id = request.session['current_col_id']
    collection = TreeCollection.objects.get( id = col_id )
    trees_list = []
    if 'only_bad_trees' in request.GET:
        tlist = collection.bad_trees.all()
    else:
        tlist = collection.trees.all()
    for i in tlist:
        if i.column_error:
            error_line = " "*(i.column_error)+"^"
        else:
            error_line = ""
        source = tidyNwk( i.source )
        trees_list.append( ( i.id, i.name.replace('.','').replace('|', '_'), "_".join(source.split()), error_line ) )
    #paginator = Paginator( trees_list, 100 )
    context['trees_list'] = trees_list
    if len( trees_list ):
        context['not_empty_collection'] = True
    return render_to_response( 'browse.html', context )#TODO Rename to browse

def recreate_collection( request ):
    # FIXME TODO Prendre en charge la correction sur les bad_taxa
    collection = request.session['collection']
    list_correction = []
    for bad, good in request.GET.iteritems():
        if not good.strip():
            good = bad
        if Taxonomy.objects.filter( name = bad ).count():
            list_user_taxon_name = set([i.user_taxon_name for i in collection.rel.filter( taxon = Taxonomy.objects.get( name = bad ) )])
        else:
            list_user_taxon_name = [BadTaxa.objects.get( name = bad ).name]
        for user_taxon_name in list_user_taxon_name:
            if user_taxon_name != " ".join( good.split() ):
                list_correction.append( (user_taxon_name, " ".join(good.split()) ))
    corrected_collection = collection.get_corrected_collection( dict(list_correction) ) 
    request.session['correction'].update( dict( list_correction ) )
    request.session['collection'] = corrected_collection
    return statistics( request )

def filter_collection( request ):
    collection = request.session['collection']
    filter_list = list( request.GET )
    keep = True
    if "filter_option" in request.GET:
        filter_option = request.GET['filter_option']
        keep = filter_option == "keep"
        filter_list.remove( "filter_option" )
        taxa_list = [i.name for i in collection.taxa.all()]
        diff = list(set(filter_list).difference( set( taxa_list ) ))
        if diff: # inter node we have to fetch leaves
            restricted_taxa_list = Taxonomy.objects.filter( name__in = diff )
            for taxon in restricted_taxa_list:
                filter_list.extend( [i.name for i in taxon.children.filter( name__in = taxa_list)] )
    user_filter_list = set([])
    for taxon_name in filter_list:
        try:
            rel_list = collection.rel.filter( taxon__id = TAXONOMY_TOC[taxon_name.lower().strip()])
        except KeyError, e:
            error_msg = str("bad taxon name : %s" % e.message)
            request.session['error_msg'] = error_msg.replace( '<', '&lt;').replace( '>', '&gt;' )
            return statistics( request )
        for rel in rel_list:
            user_filter_list.add( rel.user_taxon_name )
    filtered_collection = collection.get_restricted_collection( list(user_filter_list), keep=keep )
    request.session['collection'] = filtered_collection
    request.session['collection_changed'] = True
    return statistics( request )

def get_img_url( request, taxon ):
   return HttpResponse( _get_image_url( taxon )  )

def progressbar( request ):
    global D_PROGRESS
    col_id = request.session['current_col_id']
    response = HttpResponse(mimetype='text/json')
    json = D_PROGRESS.get( col_id, {} )
    json.update( D_PROGRESS.get( request.session.session_key, {} ) )
    response.write( str(json) )
    return response
    #return HttpResponse(response)

def suggestions( request ):
    # correct bad taxas
    global D_PROGRESS
    global CACHE_SUGGESTIONS
    collection = request.session['collection']
    col_id = collection.id
    print col_id
    if not col_id in D_PROGRESS:
        D_PROGRESS[col_id] = {}
    D_PROGRESS[col_id]['suggestions'] = 0
    context = {}
    if not collection.homonyms.count() and not collection.synonyms.count() and not collection.commons.count():
        context['display_button'] = True
    else:
        context['display_button'] = False
    if not col_id in CACHE_SUGGESTIONS:
        bad_taxa_list = list(collection.bad_taxa.all())
        CACHE_SUGGESTIONS[col_id] = { 'bad_taxa_list': bad_taxa_list, 'dict_bad_taxa': {}, 'progress':0  }
    else:
        if ( len( CACHE_SUGGESTIONS[col_id]['bad_taxa_list'] ) == len( CACHE_SUGGESTIONS[col_id]['dict_bad_taxa'] ) ):
            context['dict_bad_taxa'] = CACHE_SUGGESTIONS[col_id]['dict_bad_taxa']
            D_PROGRESS[col_id]['suggestions'] = 100
            return render_to_response( 'suggestions.html', context )
        bad_taxa_list = CACHE_SUGGESTIONS[col_id]['bad_taxa_list']
        D_PROGRESS[col_id]['suggestions'] = CACHE_SUGGESTIONS[col_id]['progress']
    for bad in bad_taxa_list:
        CACHE_SUGGESTIONS[col_id]['dict_bad_taxa'][bad.name] = []
        correct_list = TAXOREF.correct( bad.name, guess = True )
        for i in correct_list:
            if i != bad.name:
                CACHE_SUGGESTIONS[col_id]['dict_bad_taxa'][bad.name].append( i )
        D_PROGRESS[col_id]['suggestions'] = ((bad_taxa_list.index(bad)+1)*100.0)/request.session['nb_badtaxa']
        CACHE_SUGGESTIONS[col_id]['progress'] = D_PROGRESS[col_id]['suggestions']
    context['dict_bad_taxa'] = CACHE_SUGGESTIONS[col_id]['dict_bad_taxa']
    D_PROGRESS[col_id]['suggestions'] = 100
    CACHE_SUGGESTIONS[col_id]['progress'] = 100
    return render_to_response( 'suggestions.html', context )

def reference_tree( request ):
    global CACHE_REFERENCE_TREE
    global TAXONOMY_ENGINE
    context = {'taxo_engine':TAXONOMY_ENGINE}
    collection = request.session['collection']
    if collection.id in CACHE_REFERENCE_TREE:
        context['stats_tree'] = CACHE_REFERENCE_TREE[collection.id]
    else:
        if not request.session['nb_scientifics']:
            return HttpResponse( '<b><font color="red">No scientifics taxa found. Please correct your collection...</font></b>' )
        context['stats_tree'] = display_tree_stats( collection )
        CACHE_REFERENCE_TREE[collection.id] = context['stats_tree']
    context['reference_tree'] = request.session['reference_tree_nwk']
    return render_to_response( 'reference_tree.html', context )

def single_reference_tree( request, idtree ):
    global CACHE_REFERENCE_TREE
    if not "tree_%s" % idtree in CACHE_REFERENCE_TREE:
        tree = Tree.objects.get( id = idtree )
        if not tree.scientifics:
            return HttpResponse( '<b><font color="red">No scientifics taxa found in tree. Please correct your collection...</font></b>' )
        CACHE_REFERENCE_TREE["tree_%s"%idtree] = display_single_tree_stats( tree )
    return HttpResponse( CACHE_REFERENCE_TREE["tree_%s"%idtree] )

def download_correction( request ):
    csv = "user taxa names|corrected names\n"
    for (bad, good) in request.session['correction'].iteritems():
        csv += "%s|%s\n" % ( bad, good )
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=correction-%s.csv' % request.session['original_collection_id']
    response.write( csv )
    return response

def downloadCollection( request ):
    col_id = request.session['current_col_id']
    collection = TreeCollection.objects.get( id = col_id )
    response = HttpResponse(mimetype='text/plain')
    if collection.format == "phylip":
        ext = 'nwk'
    else:
        ext = 'nex'
    response['Content-Disposition'] = 'attachment; filename=collection-%s.%s' % (col_id, ext)
    response.write( collection.get_collection_string() )
    return response

def download_reference_tree( request ):
    col_id = request.session['current_col_id']
    collection = TreeCollection.objects.get( id = col_id )
    response = HttpResponse(mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=reference_collection-%s.nwk' % col_id
    response.write( collection.get_reference_tree_as_nwk(False) )
    return response

def get_images( request ):
    col_id = request.session['current_col_id']
    collection = TreeCollection.objects.get( id = col_id )
    taxa_list = collection.taxa.all()
    json = {'items':[]}
    d_taxa_list = {}
    for taxon in taxa_list:
        json['items'].append( {'name': str(taxon.name), 'url':_get_image_url( taxon.name ) } )
    return HttpResponse( str(json) )

def browse_images( request ):
    global TAXONOMY_ENGINE, REFERENCE_ROOT_URL
    context = {'taxo_engine':TAXONOMY_ENGINE, "ref_url":REFERENCE_ROOT_URL}
    col_id = request.session['current_col_id']
    collection = TreeCollection.objects.get( id = col_id )
    if "all" in request.GET:
        taxa_list = collection.taxa.all()
        context["all"] = True
    else:
        taxa_list = collection.taxa.all()[:20]
        context["all"] = False
    d_taxa_list = []
    for taxon in taxa_list:
        #d_taxa_list[taxon.name] = _get_wikipedia_url(taxon.name)
        l = _get_wikipedia_url( taxon.name ).values()
        d_taxa_list.append( ( taxon.name, l[0], l[1] ) )
    context['d_taxa_list'] = d_taxa_list
    if len( taxa_list ):
        context['not_empty_collection'] = True
    return render_to_response( 'browse_images.html', context )

def get_phyfi_tree_image_url( request, idtree ):
    return get_phyfi_image_url( request, idtree )

def get_phyfi_reference_tree_image_url( request, idtree ):
    return get_phyfi_image_url( request, idtree, reference = True )

def get_phyfi_image_url( request, idtree, reference = False ):
    global CACHE_PHYFI_URL
    internal_label = "internal_label" in request.GET
    if reference:
        if idtree in CACHE_PHYFI_URL['reference']:
            return HttpResponse( CACHE_PHYFI_URL['reference'][idtree] )
        else:
            tree_source = request.session['collection'].get_reference_tree_as_nwk(internal_label)
    else:
        if idtree in CACHE_PHYFI_URL['tree']:
            return HttpResponse( CACHE_PHYFI_URL['tree'][idtree] )
        else:
            if internal_label:
                tree_source = Tree.objects.get( id = idtree ).get_tree_as_nwk( True )
            else:
                tree_source = Tree.objects.get( id = idtree ).source
    conn = httplib.HTTPConnection("cgi-www.daimi.au.dk" )
    tree_source = tidyNwk( tree_source ).replace( ' ', '_' ).strip(';')
    conn.request("GET", "/cgi-chili/phyfi/go?newicktext=%s%%3B&lineth=1&format=png&angle=15&width=800" % tree_source)
    f = conn.getresponse().read()
    try:
        url = f.split('iframe')[1].split('"')[3].replace('http://cgi-www.daimi.au.dk','')
    except:
        if "The requested URL's length exceeds the capacity" in f:
            conn.close()
            return HttpResponse( "/site_media/exceeds_capacity_limit.png" )
        elif "This doesn't seem to be a properly formatted Newick phylogeny" in f:
            return HttpResponse( "/site_media/no_scientifics_found.png" )
    conn.request("GET", url )
    f = conn.getresponse().read()
    img_url = f.split('<img')[1].split('"')[3]
    conn.close()
    url = "http://cgi-www.daimi.au.dk/cgi-chili/phyfi/"+img_url
    if reference:
        CACHE_PHYFI_URL['reference'][idtree] = url
    else:
        CACHE_PHYFI_URL['tree'][idtree] = url
    return HttpResponse( url  )
    
def get_tree_source( request, idtree ):
    tree = Tree.objects.get( id = idtree )
    if tree.column_error:
        error_line = " "*(tree.column_error-1)+"^"
    else:
        error_line = ""
    if "internal_label" in request.GET:
        source = tree.get_tree_as_nwk( True )
    else:
        source = tidyNwk( tree.source )
    source = "_".join( source.split() )
    json = {"source":str(source), "error_line": str(error_line) }
    return HttpResponse( str(json) )

def get_tree_arborescence( request, idtree ):
    tree = Tree.objects.get( id = idtree )
    return HttpResponse( _display_tree( tree.arborescence ) )
    
def get_matrix( request ):
    """
    <img src="images/image.gif"
           width=150 height=70 usemap="#Map">
        <map name="Map">
            <area shape="rect" href="debut.html" COORDS="0,0,48,28">
        </MAP>
    </IMG>
    """
    global TAXONOMY_ENGINE, REFERENCE_ROOT_URL
    from djangophylocore.lib.svg import Scene, Rectangle
    nb_trees = request.session['nb_trees']
    nb_taxa = request.session['nb_taxa']
    collection = request.session['collection']
    stat = collection.get_statistics()
    matrix = collection.get_matrix()
    # Sorting matrix
    sort_info = {'trees':{}, 'taxa':{}}
    for taxa, trees in matrix.iteritems():
        sort_info["taxa"][taxa] = len( [i for i in trees.values() if i] )
        for tree, presence in trees.iteritems():
            if presence:
                if not tree in sort_info["trees"]:
                    sort_info["trees"][tree] = 0 
                sort_info["trees"][tree] += 1 
    #
    taxa_list = [i[1] for i in sorted([(i,v) for v,i in sort_info['taxa'].items()])]
    tree_list = [i[1] for i in sorted([(i,v) for v,i in sort_info['trees'].items()])]
    d_tree_id_name = dict( Tree.objects.filter( id__in = tree_list).values_list( 'id','name' ) )
    if nb_taxa < 20 and nb_trees < 20:
        pix = 20
    elif nb_taxa < 70 and nb_trees < 70:
        pix = 15
    elif nb_taxa < 100 and nb_trees < 100:
        pix = 10
    else:
        pix = 5
    scene = Scene('%s' % collection.id, (nb_taxa+1)*pix, (nb_trees+1)*pix )
    j = 0 # ordonnee
    map_j = 0
    map = """<map name="Map">"""
    for taxa in taxa_list:
        tmp = matrix[taxa]
        j += pix
        map_j += pix
        i = 0 # abscisse
        map_i = 0
        for tree in tree_list:
            val = tmp[tree]
            if val == 0:
                scene.add(Rectangle((i,j),pix,pix,(255,255,255)))
                map += """<area shape="rect" title="taxon: %s, tree: %s" coords="%s,%s,%s,%s">""" % (
                  list(stat[taxa]['scientific_taxon_list'])[0], d_tree_id_name[tree],
                  map_i, map_j, map_i+pix, map_j+pix )
            else:
                scene.add(Rectangle((i,j),pix,pix,(0,0,0)))
                map += """<area shape="rect" title="taxon: %s, tree: %s" coords="%s,%s,%s,%s">""" % (
                  list(stat[taxa]['scientific_taxon_list'])[0],d_tree_id_name[tree],
                  map_i, map_j, map_i+pix, map_j+pix )
            i += pix
            map_i += pix
    scene.write_svg()
    map += """</map>"""
    context = {'ref_url':REFERENCE_ROOT_URL, 'taxo_engine':TAXONOMY_ENGINE, 'col_id': collection.id, "not_empty_collection": True, "map":map }
    return render_to_response( 'matrix.html', context )

def autocomplete( request ):
    results = []
    if "query" in request.GET:
         value = request.GET['query']
         value_size = len(value)
         if value_size > 2:
            results = sorted([str(i) for i in TAXONOMY_TOC.keys() if i[:value_size] == value])
    json = simplejson.dumps(results)
    return HttpResponse(json, mimetype='application/json')


########################################
#   Needed fonctions (not views)       #
#    Beware : html inside !            #
########################################
def get_autocorrected_collection( self ):
    return self.get_corrected_collection( [(i.user_taxon_name,
      i.taxon.scientifics.get().name)\
        for i in self.rel.filter( taxon__in = self.taxa.exclude(
          type_name = 'scientific name' ) )\
            if i.taxon.scientifics.count() == 1] )


def correct_collection( collection ):
    # FIXME utiliser les vrais nom d'utilisateur...
    return collection.get_corrected_collection(
      [(collection.delimiter.join( synonym.name.split()),\
        collection.delimiter.join( synonym.scientifics.get().name.split()))\
        for synonym in collection.synonyms.all() if synonym.scientifics.count() == 1]
    )

#
# Images
#

taximage_url = {}

def _get_wikipedia_url( taxon ):
    global taximage_url
    taxon = "_".join(taxon.split()).strip().capitalize()
    if not taximage_url.has_key( taxon ):
        taximage_url[taxon] = {}
        url_thumb = ''
        conn = httplib.HTTPConnection("species.wikimedia.org")
        conn.request("GET", "/wiki/"+taxon)
        f = conn.getresponse().read()
        if 'class="thumbimage"' in f:
            url_thumb = f.split('thumbimage')[0].split('src=')[-1].split()[0].strip('"')
        else:
            conn = httplib.HTTPConnection("en.wikipedia.org")
            conn.request("GET", "/wiki/"+taxon)
            f = conn.getresponse().read()
            try:
                url_thumb = f.split('class="image"' )[1].split('</a>')[0].split('src=')[1].split()[0].strip('"')
            except:
                taximage_url[taxon] = { "thumb": "Image not found", "full": "Image not found" }
        conn.close()
        if url_thumb:
            url = url_thumb.split('/')[:-1]
            try:
                url.remove('thumb' )
                url = "/".join( url )
                taximage_url[taxon] = {"thumb": url_thumb, "full":url}
            except:
                print url, url_thumb
                taximage_url[taxon] = { "thumb": "Image not found", "full": "Image not found" }
        else:
            taximage_url[taxon] = { "thumb": "Image not found", "full": "Image not found" }
    return taximage_url[taxon]


taximage_url2 = {}
 
def _get_image_url( taxon ):
    global taximage_url2
    taxon = "_".join(taxon.split()).strip().capitalize()
    if not taximage_url2.has_key( taxon ):
        taximage_url2[taxon] = ""
        conn = httplib.HTTPConnection("species.wikimedia.org")
        conn.request("GET", "/wiki/"+taxon)
        f = conn.getresponse().read()
        for line in f.split("\n"):
            if "thumbinner" in line:
                url_img = line.split("thumbinner")[1].split("<img")[1].split("src=\"")[1].split("\"")[0].strip()
                conn.close()    
                taximage_url2[taxon] = """<img src="%s" class="imgTaxa" />""" % url_img
                break
        conn.close()
        if taximage_url2[taxon]:
            return taximage_url2[taxon]   
        conn = httplib.HTTPConnection("en.wikipedia.org")
        conn.request("GET", "/wiki/"+taxon)
        f = conn.getresponse().read()
        for line in f.split("\n"):
            if "class=\"image\"" in line and not "<img alt=\"\"" in line:
                url_img = line.split("class=\"image\"")[1].split("src=\"")[1].split("\"")[0].strip()
                conn.close()    
                taximage_url2[taxon] = """<img src="%s" class="imgTaxa" />""" % url_img
                return taximage_url2[taxon]
        conn.close()    
        taximage_url2[taxon] = "Image not found"
    return taximage_url2[taxon]



#
# Statistics
#

def get_tree_size_distribution( d_stat ):
    ratio = sorted( d_stat.keys() )[1]-sorted( d_stat.keys() )[0]
    result = ""
    nbtaxa_max = max( d_stat.values() ) 
    for nbtaxon, nbtree in sorted(d_stat.items()):
        if nbtree:
            nbtreepourcent = nbtree*100/nbtaxa_max
            bar = " "*( nbtree*70/nbtaxa_max ) # 70 is an abitrary taken number
            bar = bar.replace( " ", "&nbsp;&nbsp;" )#.replace( "-", "&nbsp;")
            bar = """<span class="statMetric">"""+bar+"</span>"
            if nbtaxon == nbtaxon + ratio-1:
                if nbtaxon:
                    base = "["+string.center( str(nbtaxon), 7)+"]"
                else:
                    base = ""
            else:
                base = "["+string.center( str(nbtaxon)+"-"+str(nbtaxon+ratio-1), 7)+"]"
            base = base.replace( " ", "&nbsp;" )
            if base:
                result += "<tt>"+base+"</tt>&nbsp;"+bar+"&nbsp;<tt>("
                if nbtree > 1:
                    result += str(nbtree)+" trees"
                else:
                    result += str(nbtree)+ " tree"
                if nbtaxon > 1:
                    result += " with %s leaves)</tt><br />\n" % nbtaxon
                else:
                    result += " with %s leave)</tt><br />\n" % nbtaxon
    return result

def get_taxon_frequency_distribution( d_stat ):
    ratio = sorted( d_stat.keys() )[1]-sorted( d_stat.keys() )[0]
    result = ""
    nbtaxa_max = max( d_stat.values() ) 
    for nbtaxon, nbtree in sorted(d_stat.items()):
        if nbtree:
            nbtreepourcent = nbtree*100/nbtaxa_max
            bar = " "*( nbtree*70/nbtaxa_max )# 70 is an abitrary taken number
            bar = bar.replace( " ", "&nbsp;&nbsp;" )#.replace( "-", "&nbsp;")
            bar = """<span class="statMetric">"""+bar+"</span>"
            if nbtaxon == nbtaxon + ratio-1:
                if nbtaxon:
                    base = "["+string.center( str(nbtaxon), 7)+"]"
                else:
                    base = ""
            else:
                base = "["+string.center( str(nbtaxon)+"-"+str(nbtaxon+ratio-1), 7)+"]"
            base = base.replace( " ", "&nbsp;" )
            if base:
                result += "<tt>"+base+"&nbsp;"+bar+"&nbsp;("
                if nbtree > 1:
                    result += str(nbtree)+" taxa are"
                else:
                    result += str(nbtree)+" taxon is"
                if nbtaxon > 1:
                    result += " present in %s trees) </tt><br />\n" % nbtaxon
                else:
                    result += " present in %s tree) </tt><br />\n" % nbtaxon
    return result

#
# Display Tree
#

#def _display_tree( tree, source=None, root = "",  mydepth = 0, lastnode = 'root', blockname = "" ):
#    """
#    Pretty print of the tree in HTML.
#
#    @root (string): parent name
#    @mydepth (int): depth in the tree
#    @return (string): the display in html format
#    """
#    result = ""
#    blocknum = 0
#    if not root:
#        root = Taxonomy.objects.get( name = 'root' )
#        if source:
#            result += "<a class='genre' name='genre' href='"+source.target_url+ \
#              root.fromsource_set.get( source = source ).taxon_id_in_source+\
#              "'>"+root.name.capitalize()+"</a><br />\n"
#        else:
#            result += "<a class='genre' name='genre' href=''>"+root.name.capitalize()+"</a><br />\n"
#        result += """<span class="treeline">|</span><br />\n"""
#        lastnode = root
#    # Create tree display
#    for node in tree.successors( root ):
#        dispnode = node.name
#        dispnode = dispnode.replace( "<", "&lt;" )
#        dispnode = dispnode.replace( ">", "&gt;" )
#        nb_inter_parents = 0
#        # Create div for interparents (parents beetween nodes)
#        if node._meta.module_name != 'badtaxa':
#            if TAXOREF.is_scientific_name( node.name ):
#                if lastnode in node.parents:
#                    inter_parents = TAXOREF.get_interval_parents( lastnode, node )
#                    nb_inter_parents = len( inter_parents )
#                    blocknum += 1
#                    blockname += str( blocknum )
#                    result += "<div id='%s' class='interparents'><tt>" % blockname
#                    if len( inter_parents ):
#                        result += """<span class="treeline">|</span> """*mydepth
#                        result +=  ("""<span class="treeline">|</span> """*mydepth).join(
#                          _link_genre_tree(i,source,blockname) for i in inter_parents ) 
#                    result += "</tt></div>" 
#        # Create arborescence display
#        depth = 0
#        while depth != mydepth :
#            result += """<span class="treeline">|</span> """
#            depth += 1
#        subnodes = tree.successors( node )
#        if subnodes: # it's a genre
#            result += _link_genre_tree( node, source, blockname, True, nb_inter_parents)
#            result += _display_tree( tree, source, node, depth + 1, 
#              lastnode = node, blockname = blockname+"a")
#        else: # it's a species (ie taxon)
#            if TAXOREF.is_bad_taxon( node.name ):
#                result += "+-<font color='red'><b>"+node.name.capitalize()+"</b></font><br />\n"
#            elif TAXOREF.is_homonym( node.name ):
#                result += "+-<font color='orange'><b>"+node.name.capitalize()+"</b></font><br />\n"
#            elif TAXOREF.is_common( node.name ):
#                result += "+-<font color='violet'><b>"+node.name.capitalize()+"</b></font><br />\n"
#            elif TAXOREF.is_synonym( node.name ):
#                result += "+-<font color='gray'><b>"+node.name.capitalize()+"</b></font><br />\n"
#            else:
#                result += _link_species_tree( node, source, blockname, nb_inter_parents)
#    return result
#
#def _link_species_tree( node, source, blockname, nb_inter_parents ):
#    dispnode = node.name.capitalize()
#    dispnode = dispnode.replace( "<", "&lt;" )
#    dispnode = dispnode.replace( ">", "&gt;" )
#    result = ""
#    if TAXOREF.is_homonym( node.name ):
#        style = 'class="species_homonym"'
#    else:
#        style = 'class="species"'
#    if source:
#        result += """+-<a id="%s" %s onmouseover="go('%s');" target='_blank' href="%s%s"> %s </a>""" % (
#          node.fromsource_set.get( source = source ).taxon_id_in_source,
#          style,                        
#          node.name,
#          source.target_url,
#          node.fromsource_set.get( source = source ).taxon_id_in_source,
#          dispnode.capitalize() )
#    else:
#        result += """+-<a %s onmouseover="go('%s');" href=""> %s </a>""" % (
#            style,
#            node.name,
#            dispnode.capitalize() )
#    if nb_inter_parents:
#        result += """<a id="a-%s" class='showparents'
#          onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
#            blockname,
#            blockname )
#    else:
#        result += "<br />\n"
#    return result
#
#def _link_genre_tree( node, source, blockname, isinterparent=False, nb_inter_parents=0 ):
#    dispnode = node.name
#    dispnode = dispnode.replace( "<", "&lt;" )
#    dispnode = dispnode.replace( ">", "&gt;" )
#    result = ""
#    if source:
#        result += """+-<a id="%s" class="genre" name="genre" onmouseover="go('%s')" 
#          href="%s%s" target='_blank'> %s </a>""" % (
#          node.fromsource_set.get( source = source ).taxon_id_in_source,
#          dispnode,
#          source.target_url,
#          node.fromsource_set.get( source = source ).taxon_id_in_source,
#          dispnode.capitalize())
#    else:
#        result += """+-<a class="genre" name="genre" onmouseover="go('%s')" href=""> %s </a>""" % (
#          dispnode,
#          dispnode.capitalize())
#    if isinterparent and nb_inter_parents:
#        result += """<a id="a-%s" class='showparents'
#          onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
#            blockname,
#            blockname )
#    else:
#        result += "<br />\n"
#    return result

#
# Display itis tree stats
#

def display_single_tree_stats( tree, allparents = False ):
    """
    Display reference arborescence with stats of one tree
    """
    global D_PROGRESS
    graph = tree.get_reference_arborescence()
    if len(graph):
        list_taxa_tree = tree.taxa.all()
        d_stats = {}
        itis_tree =  _display_itis_tree( tree, list_taxa_tree, d_stats, graph, root = 'root', show_nb_trees = False, progress=False )
        return itis_tree
    else:
        return ""
    return ''


def display_tree_stats( collection, allparents = False ):
    """
    Display reference arborescence with stats of collection
    """
    global D_PROGRESS
    if collection.trees.all().count():
        tree = collection.get_reference_arborescence()
        if len(tree):
            list_taxa_collection = collection.taxa.all()
            if not collection.id in D_PROGRESS:
                D_PROGRESS[collection.id] = {}
            D_PROGRESS[collection.id]['nb_taxa'] =  len( tree )
            D_PROGRESS[collection.id]['reference_tree'] = 0
            d_stats = collection.get_statistics()
            itis_tree =  _display_itis_tree( collection, list_taxa_collection, d_stats, tree, root = 'root' )
            D_PROGRESS[collection.id]['reference_tree'] = 100
            return itis_tree
        else:
            D_PROGRESS[collection.id]['reference_tree'] = 100
            return ""
    D_PROGRESS[collection.id]['reference_tree'] = 100
    return ''

#def _remove_single_parent( list_taxa_collection, tree ):
#    for node in tree:
#        if node not in list_taxa_collection:
#            n = tree.predecessors( node ) + tree.successors(node)
#            if len(n) == 2:
#                tree.delete_edge( n[0], node )
#                tree.delete_edge( node, n[1] )
#                tree.add_edge( n[0], n[1] )
#    return tree

#WIKISPECIES_ICON = "http://species.wikimedia.org/favicon.ico"
WIKISPECIES_ICON = "/site_media/logo_wikipedia.png"
#ISPECIES_ICON = "http://ispecies.org/images/logo.jpg"
ISPECIES_ICON = "/site_media/logo_ispecies.jpg"
def _display_itis_tree( collection, list_taxa_collection, d_stats, tree, root = "",  mydepth = 0, lastnode = 'root', blockname = "", show_nb_trees = True, progress=True ):
    """
    Pretty print of the tree in HTML.

    @root (string): parent name
    @mydepth (int): depth in the tree
    @return (string): the display in html format
    """
    global D_PROGRESS
    result = ""
    blocknum = 0
    # Create root node display
    if root == "root":
        nb_taxa = collection.taxa.all().count()
        nb_trees = 1
        if show_nb_trees:
            nb_trees =  collection.trees.all().count()
        result += "<a class='genre' href=''>Root</a> (%s/%s) = (%s species in %s trees)<br />\n" % (
          nb_taxa, nb_trees, nb_taxa, nb_trees )
        result += """<span class="treeline">|</span><br />\n"""
        root = Taxonomy.objects.get( name = 'root' )
    # Create tree display
    if root in tree.nodes():
        for node in tree.successors( root ):
            n = tree.predecessors( node ) + tree.successors(node)
            nb_inter_parents = 0
            if progress:
                D_PROGRESS[collection.id]['reference_tree'] += (1.0/D_PROGRESS[collection.id]['nb_taxa'])*100.0
            # Create div for interparents (parents beetween nodes)
            if len(n) == 2:
                if node in list_taxa_collection:
                    depth = 0
                    while depth != mydepth :
                        result += """<span class="treeline">|</span> """
                        depth += 1
                    result += _link_itis_species( d_stats, collection,  node, True, blockname, nb_inter_parents)
                    mydepth += 1
                result += _display_itis_tree( collection, list_taxa_collection, d_stats, tree,  node, mydepth, 
                  lastnode = node, blockname = blockname+"a", show_nb_trees = show_nb_trees, progress=progress)
                continue
#            if create_interparent:
#                if lastnode in node.parents:
#                    inter_parents = TAXOREF.get_interval_parents( lastnode, node )
#                    nb_inter_parents = len( inter_parents )
#                    blocknum += 1
#                    blockname += str( blocknum )
#                    result += "<div id='%s' class='interparents'><tt>" % blockname
#                    if len( inter_parents ):
#                        result += """<span class="treeline">|</span> """*mydepth
#                        result +=  ("""<span class="treeline">|</span> """*mydepth).join(
#                          _link_itis_genre(collection, i,i,blockname) for i in inter_parents ) 
#                    result += "</tt></div>" 
            # Create arborescence display
            depth = 0
            while depth != mydepth :
                result += """<span class="treeline">|</span> """
                depth += 1
            subnodes = tree.successors( node )
            if subnodes: # it's a genre
                result += """<span genre="%s">\n""" % node.name
                if node in list_taxa_collection:
                    result += _link_itis_species( d_stats, collection,  node, True, blockname, nb_inter_parents)
                else:
                    result += _link_itis_genre( d_stats, collection, node, blockname, True, nb_inter_parents, stat=True )
                result += _display_itis_tree( collection, list_taxa_collection, d_stats, tree,  node, depth + 1, 
                  lastnode = node, blockname = blockname+"a", show_nb_trees = show_nb_trees, progress=progress)
                result += """</span>\n"""
            else: # it's a species (ie taxon)
                result += _link_itis_species( d_stats, collection, node, True, blockname, nb_inter_parents)
    return result

def _link_itis_species( d_stats, collection, node, stat=False, blockname="", nb_inter_parents=0 ):
    global WIKISPECIES_ICON
    result = ""
    dispnode = node.name
    dispnode = dispnode.replace( "<", "&lt;" )
    dispnode = dispnode.replace( ">", "&gt;" )
    if TAXOREF.is_homonym( node.name ):
        style = 'class="species_homonym"'
    else:
        style = 'class="species"'
    if stat:
        result += "+-"
        result += """<input class="restrict" type="checkbox" name="%s" value="%s" />""" % (
          node.name, node.name )
    result += """<a id="%s" %s onmouseover="go('%s');" target='_blank' href="%s%s"> %s</a>""" % (
      node.id,
      style,                        
      node.name,
      settings.TAXONOMY_TARGET_URL[settings.TAXONOMY_ENGINE],
      node.id,
      dispnode.capitalize() )
    if stat and d_stats:
#        result += """(<a title='%s' href="statistics?query_tree=%%7B%s%%7D">%s</a>)\n""" % (
#          "Restrict your collection to these trees",
#          node.name,
#          len(d_stats[node.id]['trees_list']) )
        result += """ (<a class="nolink" title='%s'>%s</a>/ <a title="%s" href="statistics?query_tree=%%7B%s%%7D">%s</a>)\n""" % (
          ", ".join( sorted( d_stats[node.id]['user_taxon_list'])),
          len( d_stats[node.id]['user_taxon_list'] ),
          "Restrict your collection to these trees",
          node.name,
          len( d_stats[node.id]['trees_list'] ) )
    # ispecies redirection
    result += """<a href="http://ispecies.org/?q=%s&submit=Go" title="view
    ispecies informations" target="_blank" style="color:white"><img src="%s" width="50" /></a>""" % ( node.name.replace( ' ', '+' ), ISPECIES_ICON )
    # species.wikipedia.org redirection
    result += """<a href="http://species.wikipedia.org/wiki/%s" title="view wikispecies informations" target="_blank" style="color:white">
      <img src="%s" width="20" /></a>""" % ( node.name.replace( ' ', '_' ).capitalize(), WIKISPECIES_ICON )
    if nb_inter_parents:
        result += """<a id="a-%s" class='showparents' onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
            blockname,
            blockname )
    elif stat:
        result += "<br />\n"
    return result

def _link_itis_genre( d_stats, collection, node, blockname, isinterparent=False, nb_inter_parents=0, stat = 0  ):
    global WIKISPECIES_ICON
    result = ""
    dispnode = node.name
    dispnode = dispnode.replace( "<", "&lt;" )
    dispnode = dispnode.replace( ">", "&gt;" )
    if TAXOREF.is_homonym( node.name ):
        style = 'class="genre_homonym"'
    else:
        style = 'class="genre"'
    result += "+-"
    if stat:
        result += """<input class="restrict" type="checkbox" genre="%s"
        onclick="javascript:selectGenre('%s');" />""" % ( node.name, node.name )
    result += """<a id="%s" %s name="genre" onmouseover="go('%s')" href="%s%s" target='_blank'> %s </a>""" % (
      node.id,
      style,
      node.name,
      settings.TAXONOMY_TARGET_URL[settings.TAXONOMY_ENGINE],
      node.id,
      dispnode.capitalize())
    if d_stats:
        result += """ (<a class="nolink" title='%s'>%s</a>/ <a title="%s" href="statistics?query_tree=%%7B%s%%7D">%s</a>)\n""" % (
          ", ".join( sorted( d_stats[node.id]['user_taxon_list'])),
          len( d_stats[node.id]['user_taxon_list'] ),
          "Restrict your collection to these trees",
          node.name,
          len( d_stats[node.id]['trees_list'] ) )
    # ispecies redirection
    result += """<a href="http://ispecies.org/?q=%s&submit=Go" title="view ispecies informations" target="_blank" style="color:white"><img src="%s" width="50" /></a>""" % (
        node.name.replace( ' ', '+' ), ISPECIES_ICON )
    # species.wikipedia.org redirection
    result += """<a href="http://species.wikipedia.org/wiki/%s" title="view wikispecies informations" target="_blank" style="color:white">
      <img src="%s" width="20" /></a>""" % ( node.name.replace( ' ', '_').capitalize(), WIKISPECIES_ICON )
    if isinterparent and nb_inter_parents:
        result += """<a id="a-%s" class='showparents' onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
            blockname,
            blockname )
    else:
        result += "<br />\n"
    return result


