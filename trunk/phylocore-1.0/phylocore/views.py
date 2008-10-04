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
        collection = TreeCollection.objects.create( original_collection_string = input, delimiter = delimiter )
        request.session['original_collection_id'] = collection.id
        request.session['collection'] = collection
        d_stat = collection.get_tree_size_distribution()
        d_stat = collection.get_taxon_frequency_distribution()
        request.session['last_query'] = ''
    collection = request.session['collection']
    context = {}
    # query
    query = None
    if 'query_tree' in request.GET: #FIXME POST
        if not request.session['last_query']:
            query = request.GET['query_tree']
        else:
            query = request.session['last_query'] +' and '+ request.GET['query_tree']
    elif 'query' in request.GET:
        query = request.GET['query']
    if query:
        request.session['last_query'] = query
        context['query'] = query
        collection = collection.get_collection_from_query( query )
    if 'clear_query' in request.GET:
        collection = TreeCollection.objects.get( id = request.session['original_collection_id'] )
    ## Dealing collection
    if not collection.trees.count(): #Empty collection
        context['not_empty_collection'] = False
        context['error_msg'] = "Empty collection"
    else:
        request.session['current_col_id'] = collection.id
        context['nb_taxa'] = collection.taxas.count()
        context['nb_trees'] = collection.trees.count()
        context['nb_badtaxa'] = collection.bad_taxas.count()
        context['nb_homonyms'] = collection.homonyms.count()
        context['nb_synonyms'] = collection.synonyms.count()
        context['not_empty_collection'] = True
        # stats
        d_stat = collection.get_tree_size_distribution()
        context['tree_size_distributions'] = get_tree_size_distribution( d_stat )
        d_stat = collection.get_taxon_frequency_distribution()
        context['taxon_frequency_distribution'] = get_taxon_frequency_distribution( d_stat )
        context['stats_tree'] = display_tree_stats( collection )
        # correct homonyms
        dict_homonyms = {}
        for homonym in collection.homonyms.all():
            dict_homonyms[homonym.name] = []
            for name in homonym.taxas.values('name'):
                dict_homonyms[homonym.name].extend( name.values() )
        context['dict_homonyms'] = dict_homonyms
        nb_bad_trees = collection.bad_trees.count()
        if nb_bad_trees:
            context['error_msg'] = "Warning : your collection have %s bad trees" % nb_bad_trees
    return render_to_response( 'statistics.html', context )

def browse( request ):
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
    try:
        context['tree'] = _display_tree( tree.arborescence, source )
    except:
        context['error_msg'] = "This tree contains error(s). Please, check the source"
    context['tree_string'] = tree.tree_string.replace( collection.delimiter, ' ' )
    context['current_tree_id'] = tree.id
    context['page'] = paginator.page( tree_index+1 )
    nb_trees = collection.trees.count()
    context['enable_select_tree_names'] = nb_trees < 100 and nb_trees > 1
    context['tree_names_list'] = [(tree.name, tree.id) for tree in collection.trees.iterator()]
    return render_to_response( 'check.html', context )#TODO Rename to browse

def recreate_collection( request ):
    new_nwk = request.session["collection"].original_collection_string
    request.session['original_collection_string'] = new_nwk
    for old_name, new_name in request.GET.iteritems():
        # FIXME
        #old_name = request.session['delimiter'].join( old_name.split() )
        #new_name = request.session['delimiter'].join( new_name.split() )
        new_nwk = new_nwk.replace( old_name, new_name ) 
    request.session['collection'].original_collection_string = new_nwk
    #request.session['collection'].regenerate_from_original_collection_string()
    request.session['collection'].save()
    # now what ? on recreer une collection ou on ecrase celle en cours ?
    return statistics( request )

def get_img_url( request, taxon ):
   return HttpResponse( _get_image_url( taxon )  )

########################################
#   Needed fonctions (not views)       #
########################################

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
        root = Taxa.objects.get( name = 'root' )
        if source:
            result += "<a class='genre' name='genre' href='"+source.target_url+ \
              root.fromsource_set.get( source = source ).taxa_id_in_source+\
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
            if TAXOREF.is_bad_taxa( node.name ):
                result += "+-<font color='red'><b>"+node.name.capitalize()+"</b></font><br />\n"
            elif TAXOREF.is_homonym( node ):
                result += "+-<font color='orange'><b>"+node.name.capitalize()+"</b></font><br />\n"
            elif TAXOREF.is_common( node ):
                result += "+-<font color='violet'><b>"+node.name.capitalize()+"</b></font><br />\n"
            elif TAXOREF.is_synonym( node ):
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
          node.fromsource_set.get( source = source ).taxa_id_in_source,
          style,                        
          node.name,
          source.target_url,
          node.fromsource_set.get( source = source ).taxa_id_in_source,
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
          node.fromsource_set.get( source = source ).taxa_id_in_source,
          dispnode,
          source.target_url,
          node.fromsource_set.get( source = source ).taxa_id_in_source,
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
        tree = TAXOREF.get_reference_arborescence( collection.taxas.all() )
        if not allparents:
            tree = _remove_single_parent( collection, tree )
        return _display_itis_tree( collection, tree, root = 'root' )
    return ''

def _remove_single_parent( collection, tree ):
    for node in tree:
        if node not in collection.taxas.all():
            n = tree.predecessors( node ) + tree.successors(node)
            if len(n) == 2:
                tree.delete_edge( n[0], node )
                tree.delete_edge( node, n[1] )
                tree.add_edge( n[0], n[1] )
    return tree

def _display_itis_tree( collection, tree, root = "",  mydepth = 0, lastnode = 'root', blockname = "" ):
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
        nb_taxas = collection.taxas.all().count()
        nb_trees =  collection.trees.all().count()
        result += "<a class='genre' href=''>Root</a> (%s/%s) = (%s species in %s trees)<br />\n" % (
          nb_taxas, nb_trees, nb_taxas, nb_trees )
        result += """<span class="treeline">|</span><br />\n"""
        root = Taxa.objects.get( name = 'root' )
    # Create tree display
    if root in tree.nodes():
        for node in tree.successors( root ):
            dispnode = node.name
            dispnode = dispnode.replace( "<", "&lt;" )
            dispnode = dispnode.replace( ">", "&gt;" )
            nb_inter_parents = 0
            # Create div for interparents (parents beetween nodes)
            if lastnode in node.parents:
                inter_parents = TAXOREF.get_interval_parents( lastnode, node )
                nb_inter_parents = len( inter_parents )
                blocknum += 1
                blockname += str( blocknum )
                result += "<div id='%s' class='interparents'><tt>" % blockname
                if len( inter_parents ):
                    result += """<span class="treeline">|</span> """*mydepth
                    result +=  ("""<span class="treeline">|</span> """*mydepth).join(
                      _link_itis_genre(collection, i,i,blockname) for i in inter_parents ) 
                result += "</tt></div>" 
            # Create arborescence display
            depth = 0
            while depth != mydepth :
                result += """<span class="treeline">|</span> """
                depth += 1
            subnodes = tree.successors( node )
            if subnodes: # it's a genre
                result += """<span genre="%s">\n""" % node.name
                if node in collection.taxas.all():
                    result += _link_itis_species( collection, node, True, blockname, nb_inter_parents)
                else:
                    result += _link_itis_genre( collection, node, blockname, True, nb_inter_parents, stat=True )
                result += _display_itis_tree( collection, tree,  node, depth + 1, 
                  lastnode = node, blockname = blockname+"a")
                result += """</span>\n"""
            else: # it's a species (ie taxon)
                result += _link_itis_species( collection, node, True, blockname, nb_inter_parents)
    return result

def _link_itis_species( collection, node, stat=False, blockname="", nb_inter_parents=0 ):
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
      node.name,#.capitalize().replace(" ", "_"),
      "",#self.NCBI,
      "",#self.reference.TAXONOMY[bdnode]["id"],
      dispnode.capitalize() )
    if stat:
        # XXX FIXME
        #taxa_from_genus = collection.get_taxa_from_genus( node.name )
#        result += """
#        (<a class="nolink" title='%s'>%s</a>/
#        <a title='%s' href="statistics?query=%%7B%s%%7D">%s</a>)\n""" % (
        result += """(<a title='%s' href="statistics?query_tree=%%7B%s%%7D">%s</a>)\n""" % (
          #",".join( [i.name for i in taxa_from_genus]) ,
          #taxa_from_genus.count(),
          "Restrict your collection to these trees",
          node.name,
          collection.trees.filter( taxas = node ).count() )#getNbTrees( bdnode ))
    if nb_inter_parents:
        result += """<a id="a-%s" class='showparents'
          onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
            blockname,
            blockname )
    elif stat:
        result += "<br />\n"
    return result

def _link_itis_genre( collection, node, blockname, isinterparent=False, nb_inter_parents=0, stat = 0  ):
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
    taxa_from_genus = collection.get_taxa_from_parents( node.name )
    result += """
    (<a class="nolink" title='%s'>%s</a>/
    <a title="%s" href="statistics?query_tree=%%7B%s%%7D">%s</a>)\n""" % (
      ",".join( [i.name for i in taxa_from_genus]),
      taxa_from_genus.count(),
      "Restrict your collection to these trees",
      node.name,
      #collection.trees.filter( taxas = node ).count() )#getNbTrees( bdnode ))
      collection.trees.filter(taxas__parents_relation_taxas__parent=node).distinct().count() )
    if isinterparent and nb_inter_parents:
        result += """<a id="a-%s" class='showparents'
          onClick="setInternNode('%s');"> show parents</a><br />\n""" % (
            blockname,
            blockname )
    else:
        result += "<br />\n"
    return result


