#!/usr/bin/env python
import sys
from djangophylocore.models import *
import httplib
import string

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render_to_response

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

import os.path
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)


def index( request ):
    return render_to_response( 'index.html', {'msg':''} )

def about( request ):
    context = {}
    if 'original_collection_id' in request.session:
        context['collection'] = True
    else:
        context['collection'] = False
    return render_to_response( 'about.html', context )

def help( request ):
    context = {}
    if 'original_collection_id' in request.session:
        context['collection'] = True
    else:
        context['collection'] = False
    return render_to_response( 'help.html', context )

def statistics( request ):
    if 'new_collection' in request.POST:
        if 'myFile' in request.POST:
            input = request.POST['myFile']
            myFile = 1
        if 'myFile' in request.FILES:
            input = request.FILES['myFile'].read()
            myFile = 1
        if "delimiter" in request.POST:
            request.session['delimiter'] = request.POST['delimiter']
        delimiter = request.session['delimiter']
        collection = TreeCollection.objects.create( source = input, delimiter = delimiter )
        #if 'autocorrection' in request.POST:
        #    collection, list_correction = collection.get_autocorrected_collection()
        request.session['original_collection_id'] = collection.id
        request.session['collection'] = collection
        if collection.taxa:
            d_stat = collection.get_tree_size_distribution()
            d_stat = collection.get_taxon_frequency_distribution()
        request.session['last_query'] = ''
    elif 'query_treebase' in request.POST:
        treebase = TreeCollection.objects.get( id = 1 )
        collection = treebase.get_collection_from_query( request.POST['query_treebase'] )
        request.session['original_collection_id'] = collection.id
        request.session['collection'] = collection
        if collection.taxa:
            d_stat = collection.get_tree_size_distribution()
            d_stat = collection.get_taxon_frequency_distribution()
        request.session['last_query'] = ''
    print "fin creation collection"
    collection = request.session['collection']
    context = {}
    ## Query
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
        if query_against_treebase:
            collection = collection.get_collection_from_query( query, query_against_treebase )
    if 'clear_query' in request.GET:
        collection = TreeCollection.objects.get( id = request.session['original_collection_id'] )
    context['query'] = query
    print "fin query"
    ## Dealing collection
    if not collection.trees.count(): #Empty collection
        context['not_empty_collection'] = False
        context['error_msg'] = "Empty collection"
    else:
        request.session['current_col_id'] = collection.id
        context['bad_taxa'] = collection.bad_taxa.all() # FIXME a supprimer
        if 'clear_query' in request.GET:
            return render_to_response( 'statistics.html', request.session['initial_context'] )
        context['nb_taxa'] = collection.taxa.count()
        context['nb_trees'] = collection.trees.count()
        context['nb_badtaxa'] = collection.bad_taxa.count()
        context['nb_homonyms'] = collection.homonyms.count()
        context['nb_synonyms'] = collection.synonyms.count()
        context['nb_commons'] = collection.commons.count()
        context['not_empty_collection'] = True
        print "fin donnees numeriques"
        # stats
        if collection.taxa:
            d_stat = collection.get_tree_size_distribution()
            context['tree_size_distributions'] = get_tree_size_distribution( d_stat )
            d_stat = collection.get_taxon_frequency_distribution()
            context['taxon_frequency_distribution'] = get_taxon_frequency_distribution( d_stat )
        print "fin stats"
        if 1:#context['nb_taxa'] < 200:
            context['stats_tree'] = display_tree_stats( collection )
            print "fin arbre ncbi"
        else:
            context['stats_tree'] = None
        context['reference_tree'] = collection.get_reference_tree_as_nwk()
        # correct bad taxas
#        dict_bad_taxas = {}
#        for bad in collection.bad_taxas.all():
#            dict_bad_taxas[bad.name] = []
#            for i in TAXOREF.correct( bad.name, guess = True ):
#                if i != bad.name:
#                    dict_bad_taxas[bad.name].append( i )
#        context['dict_bad_taxas'] = dict_bad_taxas
        # correct homonyms
        dict_homonyms = {}
        for homonym in collection.homonyms.all():
            dict_homonyms[homonym.name] = []
            for name in homonym.scientifics.values('name'):
                dict_homonyms[homonym.name].extend( name.values() )
        context['dict_homonyms'] = dict_homonyms
        print "fin homonym"
        # correct synonym
        dict_synonym = {}
        for synonym in collection.synonyms.all():
            dict_synonym[synonym.name] = []
            for name in synonym.scientifics.values('name'):
                dict_synonym[synonym.name].extend( name.values() )
        context['dict_synonym'] = dict_synonym
        print "fin synonym"
        # correct common
        dict_common = {}
        for common in collection.commons.all():
            dict_common[common.name] = []
            for name in common.scientifics.values('name'):
                dict_common[common.name].extend( name.values() )
        context['dict_common'] = dict_common
        print "fin common"
        nb_bad_trees = collection.bad_trees.count()
        if nb_bad_trees:
            context['error_msg'] = "Warning : your collection have %s bad trees" % nb_bad_trees
        if 'new_collection' in request.POST:
            request.session['initial_context'] = context
    return render_to_response( 'statistics.html', context )

def check( request ):
    #source = Source.objects.get( id = request.session['current_source_id'] )
    source = None
    col_id = request.session['current_col_id']
    collection = TreeCollection.objects.get( id = col_id )
    paginator = Paginator( collection.trees.all(), 1 )
    if 'page' in request.GET:
        tree_index = int( request.GET['page'] )-1
        if tree_index < 0:
            tree_index = 0
        elif tree_index > paginator.count-1:
            tree_index = paginator.count-1
        tree = collection.trees.all()[tree_index] 
    elif 'tree_id' in request.GET:
        tree_id = request.GET['tree_id']
        tree = Tree.objects.get( id = tree_id ) 
        for page_index in paginator.page_range:
            if tree in paginator.page(page_index).object_list:
                tree_index = page_index - 1
    else:
        tree = collection.trees.all()[0] 
        tree_index = 0
    context = {}
    if not tree.is_valid:
        context['error_msg'] = "Warning : this tree is not well formated"
    if 1:#try:
        context['tree'] = _display_tree( tree.arborescence, source )
    else:#except:
        context['error_msg'] = "This tree contains error(s). Please, check the source"
    context['source'] = tree.source.replace( collection.delimiter, ' ' )
    context['current_tree_id'] = tree.id
    context['page'] = paginator.page( tree_index+1 )
    nb_trees = collection.trees.count()
    context['enable_select_tree_names'] = nb_trees < 100 and nb_trees > 1
    context['tree_names_list'] = [(tree.name, tree.id) for tree in collection.trees.iterator()]
    return render_to_response( 'check.html', context )#TODO Rename to browse

def browse( request ):
    #source = Source.objects.get( id = request.session['current_source_id'] )
    source = None
    col_id = request.session['current_col_id']
    collection = TreeCollection.objects.get( id = col_id )
    trees_list = []
    for i in collection.trees.all():
        if i.column_error:
            error_line = " "*(i.column_error-1)+"^"
        else:
            error_line = ""
        trees_list.append( (i.name.replace('.','').replace('|', '_'), i.source, error_line ) )
    paginator = Paginator( trees_list, 100 )
    context = {'trees_list':trees_list}
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
            list_correction.append( (user_taxon_name, " ".join(good.split()) ))
    corrected_collection = collection.get_corrected_collection( dict(list_correction) ) 
    request.session['collection'] = corrected_collection
    return statistics( request )

def get_img_url( request, taxon ):
   return HttpResponse( _get_image_url( taxon )  )

def suggestions( request ):
    # correct bad taxas
    dict_bad_taxa = {}
    context = {}
    collection = request.session['collection']
    bad_taxa_list = collection.bad_taxa.all()
    for bad in bad_taxa_list:
        dict_bad_taxa[bad.name] = []
        for i in TAXOREF.correct( bad.name, guess = True ):
            if i != bad.name:
                dict_bad_taxa[bad.name].append( i )
    context['dict_bad_taxa'] = dict_bad_taxa
    return render_to_response( 'suggestions.html', context )

def downloadCollection( request ):
    col_id = request.session['current_col_id']
    collection = TreeCollection.objects.get( id = col_id )
    response = HttpResponse(mimetype='text/plain')
    if collection.format == "phylip":
        ext = 'nwk'
    else:
        ext = 'nex'
    response['Content-Disposition'] = 'attachment; filename=phyloexplorer_collection-%s.%s' % (col_id, ext)
    response.write( collection.get_collection_string() )
    return response

def downloadNCBITree( request ):
    col_id = request.session['current_col_id']
    collection = TreeCollection.objects.get( id = col_id )
    response = HttpResponse(mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=ncbi_collection-%s.nwk' % col_id
    response.write( collection.get_reference_tree_as_nwk() )
    return response



########################################
#   Needed fonctions (not views)       #
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

def _get_image_url( taxon ):
    global taximage_url
    taxon = "_".join(taxon.split()).strip().capitalize()
    if not taximage_url.has_key( taxon ):
        conn = httplib.HTTPConnection("species.wikimedia.org")
        conn.request("GET", "/wiki/"+taxon)
        f = conn.getresponse().read()
        for line in f.split("\n"):
            if "thumbinner" in line:
                url_img = line.split("thumbinner")[1].split("<img")[1].split("src=\"")[1].split("\"")[0].strip()
                conn.close()    
                taximage_url[taxon] = """<img src="%s" class="imgTaxa" />""" % url_img
                return taximage_url[taxon]
        conn.close()    
        conn = httplib.HTTPConnection("en.wikipedia.org")
        conn.request("GET", "/wiki/"+taxon)
        f = conn.getresponse().read()
        for line in f.split("\n"):
            if "class=\"image\"" in line and not "<img alt=\"\"" in line:
                url_img = line.split("class=\"image\"")[1].split("src=\"")[1].split("\"")[0].strip()
                conn.close()    
                taximage_url[taxon] = """<img src="%s" class="imgTaxa" />""" % url_img
                return taximage_url[taxon]
        conn.close()    
        taximage_url[taxon] = "Image not found"
    return taximage_url[taxon]



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
                result += "<tt>"+base+"</tt>&nbsp;"+bar+"&nbsp;<tt>("+str(nbtree)+" trees)</tt><br />\n"
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
                result += "<tt>"+base+"&nbsp;"+bar+"&nbsp;("+str(nbtree)+" taxa)</tt><br />\n"
    return result

#
# Display Tree
#

def _display_tree( tree, source=None, root = "",  mydepth = 0, lastnode = 'root', blockname = "" ):
    """
    Pretty print of the tree in HTML.

    @root (string): parent name
    @mydepth (int): depth in the tree
    @return (string): the display in html format
    """
    result = ""
    blocknum = 0
    if not root:
        root = Taxonomy.objects.get( name = 'root' )
        if source:
            result += "<a class='genre' name='genre' href='"+source.target_url+ \
              root.fromsource_set.get( source = source ).taxon_id_in_source+\
              "'>"+root.name.capitalize()+"</a><br />\n"
        else:
            result += "<a class='genre' name='genre' href=''>"+root.name.capitalize()+"</a><br />\n"
        result += """<span class="treeline">|</span><br />\n"""
        lastnode = root
    # Create tree display
    for node in tree.successors( root ):
        dispnode = node.name
        dispnode = dispnode.replace( "<", "&lt;" )
        dispnode = dispnode.replace( ">", "&gt;" )
        nb_inter_parents = 0
        # Create div for interparents (parents beetween nodes)
        if node._meta.module_name != 'badtaxa':
            if TAXOREF.is_scientific_name( node.name ):
                if lastnode in node.parents:
                    inter_parents = TAXOREF.get_interval_parents( lastnode, node )
                    nb_inter_parents = len( inter_parents )
                    blocknum += 1
                    blockname += str( blocknum )
                    result += "<div id='%s' class='interparents'><tt>" % blockname
                    if len( inter_parents ):
                        result += """<span class="treeline">|</span> """*mydepth
                        result +=  ("""<span class="treeline">|</span> """*mydepth).join(
                          _link_genre_tree(i,source,blockname) for i in inter_parents ) 
                    result += "</tt></div>" 
        # Create arborescence display
        depth = 0
        while depth != mydepth :
            result += """<span class="treeline">|</span> """
            depth += 1
        subnodes = tree.successors( node )
        if subnodes: # it's a genre
            result += _link_genre_tree( node, source, blockname, True, nb_inter_parents)
            result += _display_tree( tree, source, node, depth + 1, 
              lastnode = node, blockname = blockname+"a")
        else: # it's a species (ie taxon)
            if TAXOREF.is_bad_taxon( node.name ):
                result += "+-<font color='red'><b>"+node.name.capitalize()+"</b></font><br />\n"
            elif TAXOREF.is_homonym( node.name ):
                result += "+-<font color='orange'><b>"+node.name.capitalize()+"</b></font><br />\n"
            elif TAXOREF.is_common( node.name ):
                result += "+-<font color='violet'><b>"+node.name.capitalize()+"</b></font><br />\n"
            elif TAXOREF.is_synonym( node.name ):
                result += "+-<font color='gray'><b>"+node.name.capitalize()+"</b></font><br />\n"
            else:
                result += _link_species_tree( node, source, blockname, nb_inter_parents)
    return result

def _link_species_tree( node, source, blockname, nb_inter_parents ):
    dispnode = node.name.capitalize()
    dispnode = dispnode.replace( "<", "&lt;" )
    dispnode = dispnode.replace( ">", "&gt;" )
    result = ""
    if TAXOREF.is_homonym( node.name ):
        style = 'class="species_homonym"'
    else:
        style = 'class="species"'
    if source:
        result += """+-<a id="%s" %s onmouseover="go('%s');" target='_blank' href="%s%s"> %s </a>""" % (
          node.fromsource_set.get( source = source ).taxon_id_in_source,
          style,                        
          node.name,
          source.target_url,
          node.fromsource_set.get( source = source ).taxon_id_in_source,
          dispnode.capitalize() )
    else:
        result += """+-<a %s onmouseover="go('%s');" href=""> %s </a>""" % (
            style,
            node.name,
            dispnode.capitalize() )
    if nb_inter_parents:
        result += """<a id="a-%s" class='showparents'
          onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
            blockname,
            blockname )
    else:
        result += "<br />\n"
    return result

def _link_genre_tree( node, source, blockname, isinterparent=False, nb_inter_parents=0 ):
    dispnode = node.name
    dispnode = dispnode.replace( "<", "&lt;" )
    dispnode = dispnode.replace( ">", "&gt;" )
    result = ""
    if source:
        result += """+-<a id="%s" class="genre" name="genre" onmouseover="go('%s')" 
          href="%s%s" target='_blank'> %s </a>""" % (
          node.fromsource_set.get( source = source ).taxon_id_in_source,
          dispnode,
          source.target_url,
          node.fromsource_set.get( source = source ).taxon_id_in_source,
          dispnode.capitalize())
    else:
        result += """+-<a class="genre" name="genre" onmouseover="go('%s')" href=""> %s </a>""" % (
          dispnode,
          dispnode.capitalize())
    if isinterparent and nb_inter_parents:
        result += """<a id="a-%s" class='showparents'
          onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
            blockname,
            blockname )
    else:
        result += "<br />\n"
    return result

#
# Display itis tree stats
#

def display_tree_stats( collection, allparents = False ):
    """
    Display NCBI arborescence with stats
    """
    if collection.trees.all().count():
        tree = collection.get_reference_arborescence()
        if len(tree):
            list_taxa_collection = collection.taxa.all()
            d_stats = collection.get_statistics()
            return _display_itis_tree( collection, list_taxa_collection, d_stats, tree, root = 'root' )
        else:
            return ""
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

def _display_itis_tree( collection, list_taxa_collection, d_stats, tree, root = "",  mydepth = 0, lastnode = 'root', blockname = "" ):
    """
    Pretty print of the tree in HTML.

    @root (string): parent name
    @mydepth (int): depth in the tree
    @return (string): the display in html format
    """
    result = ""
    blocknum = 0
    # Create root node display
    if root == "root":
        nb_taxa = collection.taxa.all().count()
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
            # Create div for interparents (parents beetween nodes)
            if len(n) == 2:
                result += _display_itis_tree( collection, list_taxa_collection, d_stats, tree,  node, mydepth, 
                  lastnode = node, blockname = blockname+"a")
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
                  lastnode = node, blockname = blockname+"a")
                result += """</span>\n"""
            else: # it's a species (ie taxon)
                result += _link_itis_species( d_stats, collection, node, True, blockname, nb_inter_parents)
    return result

def _link_itis_species( d_stats, collection, node, stat=False, blockname="", nb_inter_parents=0 ):
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
      "",#self.NCBI,
      "",#self.reference.TAXONOMY[bdnode]["id"],
      dispnode.capitalize() )
    if stat:
        result += """(<a title='%s' href="statistics?query_tree=%%7B%s%%7D">%s</a>)\n""" % (
          "Restrict your collection to these trees",
          node.name,
          len(d_stats[node.id]['trees_list']) )
    if nb_inter_parents:
        result += """<a id="a-%s" class='showparents'
          onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
            blockname,
            blockname )
    elif stat:
        result += "<br />\n"
    return result

def _link_itis_genre( d_stats, collection, node, blockname, isinterparent=False, nb_inter_parents=0, stat = 0  ):
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
    result += """<a id="%s" %s name="genre" onmouseover="go('%s')" 
      href="%s%s" target='_blank'> %s </a>""" % (
      node.id,
      style,
      node.name,
      "",#self.NCBI,
      "",#self.reference.TAXONOMY[bdnode]["id"],
      dispnode.capitalize())
    result += """
    (<a class="nolink" title='%s'>%s</a>/
    <a title="%s" href="statistics?query_tree=%%7B%s%%7D">%s</a>)\n""" % (
      ",".join( d_stats[node.id]['scientific_taxon_list']),
      len( d_stats[node.id]['scientific_taxon_list'] ),
      "Restrict your collection to these trees",
      node.name,
      len( d_stats[node.id]['trees_list'] ) )
    if isinterparent and nb_inter_parents:
        result += """<a id="a-%s" class='showparents'
          onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
            blockname,
            blockname )
    else:
        result += "<br />\n"
    return result


