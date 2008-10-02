#-*- coding: utf-8 -*-

from django.db import models
from django.db.models import signals, Q

from lib.phylogelib import getTaxa, getChildren, removeBootStraps, removeNexusComments
from lib.phylogelib import tidyNwk, checkNwk
from lib.nexus import Nexus
import datetime, re

##################################################
#             TaxonomyReference                  #
##################################################

class TaxonomyReference( object ):

    #
    # Name related
    #

    def is_valid_name( self, name ):
        """
        return True if name is in the taxonomy
        return False otherwise
        """
        if Taxonomy.objects.filter( name = name ):
            return True
        return False

    def is_scientific_name( self, name ):
        """
        return True if name is a scientific name
        return False otherwise
        """
        if Taxa.objects.filter( name = name ).count():
            return True
        return False

    def is_homonym( self, name ):
        """
        return True if name is an homonym
        return False otherwise
        """
        if Taxonomy.objects.filter( 
          name = name, type_name = 'homonym' ).count():
            return True
        return False

    def is_synonym( self, name ):
        """
        return True if name is a synonym
        return False otherwise
        """
        if Taxonomy.objects.filter(
          name = name, type_name = 'synonym' ).count():
            return True
        return False

    def is_common( self, name ):
        """
        return True if name is a common name
        return False otherwise
        """
        if Taxonomy.objects.filter( 
          name = name, type_name = 'common').count():
            return True
        return False

    def is_bad_taxa( self, name ):
        """
        return True if name is a bad taxa name
        return False otherwise
        """
        if BadTaxa.objects.filter(name = name).count():
            return True
        elif not self.is_valid_name( name = name ):
            return True
        else:
            return False

    def get_name_from_common( self, common_name ):
        """
        return all taxa which have common_name
        """
        return Taxa.objects.filter( commons__name = common_name )

    def get_name_from_synonym( self, synonym ):
        """
        return all taxa which have synonym
        """
        return Taxa.objects.filter( synonyms__name = synonym )

    def get_name_from_homonym( self, homonym ):
        """
        return all taxa which have homonym
        """
        return Taxa.objects.filter( homonyms__name = homonym )

    def get_object_from_name( self, taxa_name ):
        """
        return the django object from taxa name.

        Name is checked in this order :
          * scientific name
          * synonym
          * homonym
          * common
          * bad taxa
        if the name is not found, a RuntimeError is raised as it must never be
        append
        """
        if not self.is_valid_name( taxa_name ):
            if BadTaxa.objects.filter( name = taxa_name ).count():
                return BadTaxa.objects.get( name = taxa_name )
            raise ValueError, '%s not found in the database' % taxa_name
        else:
            if self.is_scientific_name( taxa_name ):
                return Taxa.objects.get( name = taxa_name )
            elif self.is_synonym( taxa_name ):
                return SynonymName.objects.get( name = taxa_name )
            elif self.is_homonym( taxa_name ):
                return HomonymName.objects.get( name = taxa_name )
            elif self.is_common( taxa_name ):
                return CommonName.objects.get( name = taxa_name )
        # We never should be here
        raise RuntimeError, 'Something very wrong appened'

    def strip_taxa_name( self, taxa_name, delimiter='_' ):
        """
        Strip Taxon name in order to keep the root name and to remove
        all user staff.
        """
        name = " ".join( taxa_name.replace(delimiter," ").split()[:2] )
        if not self.is_valid_name( name ):
            return name.split()[0]
        return name
 
    def correct( self, name, guess = False ):
        # TODO TEST
        """
        return all scientific names associated to name as a query_set

        The name will be checked in the following order:
        - if name is a scientific name then return None
        - check if name is a homonym
        - check if name is a synonym
        - check if name is a common name
        - check if name is a misspell name
        if no result is found, an empty list is returned

        if guess is True, the system will try to correct the name 
        """
        if self.is_scientific_name( name ):
            return None
        else:
            homonyms_list = self.get_name_from_homonym( name )
            if homonyms_list:
                return homonyms_list
            else:
                synonym_list = self.get_name_from_synonym( name )
                if synonym_list:
                    return synonym_list
                else:
                    common_list = self.get_name_from_common( name )
                    if common_list:
                        return common_list
                    elif guess:
                        from phylocore.spellcheck import SpellCheck
                        splchk = SpellCheck( self.TAXONOMY.iterkeys() )
                        return splchk.correct( name )
                    else:
                        return [0]

    #
    # Taxa related
    #

    def __sort( self, x, y ):
        return len( y.parents ) - len( x.parents )

    def get_common_parents( self, taxa_list ):
        """
        return a list of all common parents beetween 2 taxa.
        Note that taxa1 and taxa2 must be Taxa objects
        """
        if taxa_list:
            if len( taxa_list ) == 1:
                return taxa_list[0].parents
            first_taxa, second_taxa = taxa_list[:2]
            intersection = set( first_taxa.parents ).intersection( set( second_taxa.parents) ) 
            for taxa in taxa_list[2:]:
                intersection.intersection_update( set( taxa.parents) ) 
            return  sorted( list( intersection ), self.__sort  )
        return []

    def get_first_common_parent( self, taxa_list ):
        """
        return the first common parent of taxa_list
        if root is passed to the list, None is returned as root has no parents
        """
        common_parents = self.get_common_parents( taxa_list )
        if common_parents:
            return self.get_common_parents( taxa_list )[0]
        else:
            return None

    def get_interval_parents( self, taxa1, taxa2 ):
        """
        return parents list beetween 2 taxa.
        Note that taxa1 must be a parent of taxa2
        """
        assert taxa1 in taxa2.parents, "%s is not a parent of %s" % (taxa1, taxa2) 
        difference = set( taxa2.parents ).difference( set( taxa1.parents ) )
        return sorted( list( difference ), self.__sort )[:-1]

    def get_reference_arborescence( self, taxa_list ):
        """
        Take a taxa list, search in reference all parents names and
        return a networkx.DiGraph tree.
        """
        import networkx as NX
        tree = NX.DiGraph()
        for taxa in taxa_list:
            parents = taxa.parents
            for parent in parents:
                tree.add_edge( parent, taxa )
                taxa = parent
        return tree


##################################################
#                 Taxonomy                       #
##################################################

class Taxonomy( models.Model ):
    name = models.CharField( max_length = 200 )
    type_name = models.CharField( max_length = 50 )
    trees = models.ManyToManyField( 'Tree', through='TaxonomyTreeOccurence')
    class Meta:
        ordering = ['name']
        unique_together = ('name', 'type_name')

    def __unicode__( self ):
        return "%s (%s)" % ( self.name, self.type_name )

##################################################
#                 Rank                           #
##################################################

class Rank( models.Model ):
    """
    Species, genus, kingdom...
    """
    name = models.CharField( max_length = 80 )
    class Meta:
        ordering = ['name']

    def __unicode__( self ):
        return "%s" % self.name

##################################################
#                    Taxa                        #
##################################################

# get all taxa wich are murinae : Taxa.objects.filter( # parents_relation_taxas__parent__name = 'murinae' )

class Taxa( models.Model ):
    name = models.CharField( max_length = 200, unique = True ) # scientific name
    rank = models.ForeignKey( Rank, related_name = 'taxas', null = True )
    parent = models.ForeignKey( 'self', related_name = 'direct_children', null = True )
    #
    #sources = models.ManyToManyField( 'Source', through = 'FromSource' )
    homonyms = models.ManyToManyField( 'HomonymName', through = 'Homonym', related_name = 'taxas' )
    synonyms = models.ManyToManyField( 'SynonymName', through = 'Synonym', related_name = 'taxas' )
    commons = models.ManyToManyField( 'CommonName', through = 'Common', related_name = 'taxas' )
    _parents = models.ManyToManyField( 'self', through = 'ParentsRelation', related_name = 'taxas', symmetrical=False )
    class Meta:
        ordering = ['name']
    
    def __unicode__( self ):
        return self.name

    def get_parents( self ):
        if not hasattr( self, '__parents_generated'):
            if not self._parents.count():
                self.regenerate_parents()    
            setattr( self,'__parents_generated', True )
        return [i.parent for i in self.parents_relation_taxas.all()]
    parents = property( get_parents )

    def get_children( self ):
        return [i.taxa for i in self.parents_relation_parents.all()]
    children = property( get_children )

    def get_id_in_source( self, source_name ):
        return self.fromsource_set.get( source__name = source_name ).taxa_id_in_source
     
    def regenerate_parents( self ):
        """
        Regenerate parents list of the taxa
        This method is useful if we add taxa by hand
        """
        ParentsRelation.objects.filter( taxa = self ).delete() 
        if self.name != 'root':
            parent = self.parent
            index = 0
            while parent.name != 'root':
                ParentsRelation.objects.create( 
                    taxa = self,
                    parent = Taxa.objects.get( name = parent.name ),
                    index = index )
                parent = parent.parent
                index += 1
            ParentsRelation.objects.create( 
                taxa = self,
                parent = Taxa.objects.get( name = 'root'),
                index = index )

##################################################
#           ParentsRelation                      #
##################################################

class ParentsRelation( models.Model ):
    taxa = models.ForeignKey( Taxa, related_name='parents_relation_taxas' )
    parent = models.ForeignKey( Taxa, related_name = 'parents_relation_parents' )
    index = models.IntegerField()
    class Meta:
        unique_together = ('taxa', 'parent' )
        ordering = ['index']

    def __unicode__( self ):
        return "%s > %s (%s)" % (self.parent, self.taxa, self.index )

##################################################
#               Source staffs                    #
##################################################

#class Source( models.Model ):
#    """
#    Cet objet décrit la provenance du taxon
#    """
#    name = models.CharField( max_length = 200, unique = True )
#    description = models.TextField( null = True )
#    web_site_url = models.URLField( verify_exists = True, null=True )
#    target_url = models.URLField( null = True )
#
#    def __unicode__( self ):
#        return self.name
#
#class FromSource( models.Model ):
#    taxa = models.ForeignKey( Taxa )
#    source = models.ForeignKey( Source )
#    taxa_id_in_source = models.CharField( max_length = 200 )
#    taxa_name_in_source = models.CharField( max_length = 200 )
#    class Meta:
#        unique_together = ('source', 'taxa',
#          'taxa_id_in_source', 'taxa_name_in_source')
#
#    def __unicode__( self ):
#        return "%s (%s:%s)" % ( self.source, self.taxa_id_in_source,
#          self.taxa_name_in_source )

##################################################
#               Common staffs                    #
##################################################

class CommonName( models.Model ):
    name = models.CharField( max_length = 200 )
    language = models.CharField( max_length = 80, null = True )
    class Meta:
        ordering = ['name']

    def __unicode__( self ):
        return "%s (%s)" % ( self.name, self.language )

class Common( models.Model ):
    common_name = models.ForeignKey( CommonName, related_name='commons' )
    taxa = models.ForeignKey( Taxa )
    class Meta:
        ordering = ['common_name']
        unique_together = ('common_name', 'taxa')

    def __unicode__( self ):
        return "%s -> (%s)" % ( self.common_name, self.taxa )

##################################################
#               Synonym staffs                   #
##################################################

class SynonymName( models.Model ):
    name = models.CharField( max_length = 200)
    class Meta:
        ordering = ['name']

    def __unicode__( self ):
        return "%s" % ( self.name )

class Synonym( models.Model ):
    synonym_name = models.ForeignKey( SynonymName, related_name='synonyms' )
    taxa = models.ForeignKey( Taxa )
    class Meta:
        ordering = ['synonym_name']
        unique_together = ('synonym_name', 'taxa')

    def __unicode__( self ):
        return "%s -> (%s)" % ( self.synonym_name, self.taxa )

##################################################
#               Homonym staffs                   #
##################################################

class HomonymName( models.Model ):
    name = models.CharField( max_length = 200)
    class Meta:
        ordering = ['name']

    def __unicode__( self ):
        return "%s" % ( self.name )

class Homonym( models.Model ):
    homonym_name = models.ForeignKey( HomonymName, related_name='homonyms' )
    taxa = models.ForeignKey( Taxa )
    class Meta:
        ordering = ['homonym_name']
        unique_together = ('homonym_name', 'taxa')

    def __unicode__( self ):
        return "%s -> (%s)" % ( self.homonym_name, self.taxa )

##################################################
#                   BadTaxa                      #
##################################################

class BadTaxa( models.Model ):
    name = models.CharField( max_length = 200, unique = True )
    nb_occurence = models.IntegerField( default = 0 )
    class Meta:
        ordering = ['name']

    def __unicode__( self ):
        return "%s (%s)" % ( self.name, self.nb_occurence )

##################################################
#           Phylogenetic Tree                    #
##################################################

class TaxonomyTreeOccurence( models.Model ):
    taxonomy = models.ForeignKey( Taxonomy, related_name = 'taxonomy_occurences' )
    tree = models.ForeignKey( 'Tree', related_name = 'taxonomy_occurences' )
    nb_occurence = models.IntegerField( default = 0 )
    class Meta:
        unique_together = ( 'taxonomy', 'tree' )

    def __unicode__( self ):
        return u'%s (%s) %s' % ( self.taxonomy, self.nb_occurence, self.tree )

# get all taxa from tree wich are 'muridae' for parent
# tree.taxas.filter( parents_relation_taxas__parent__name = 'muridae' )

class Tree( models.Model, TaxonomyReference ):
    name = models.CharField( max_length = 80, null=True )
    delimiter = models.CharField( max_length = 5, default=' ' )
    tree_string = models.TextField()
    rooted = models.BooleanField( null = True )
    description = models.TextField( null = True )
    created = models.DateTimeField()
    updated = models.DateTimeField()
    is_valid = models.BooleanField( default = False )
    #
    bad_taxas = models.ManyToManyField( BadTaxa, related_name = 'trees'  )
    taxas = models.ManyToManyField( Taxa, related_name = 'trees' )
    homonyms = models.ManyToManyField( HomonymName, related_name = 'trees' )
    synonyms = models.ManyToManyField( SynonymName, related_name = 'trees' )
    commons = models.ManyToManyField( CommonName, related_name = 'trees')
    taxonomy_objects = models.ManyToManyField( Taxonomy, through = 'TaxonomyTreeOccurence' )

    def __unicode__( self ):
        return "%s" % ( self.name )

    def __get_django_objects_from_nwk( self, nwk_tree ):
        """
        return django objects list related to the name of taxa
        assuming that all taxa names are in database (including bad one)
        """
        nwk_tree = nwk_tree.replace( self.delimiter, ' ' )
        taxa_name_list = getTaxa( nwk_tree )
        objects_list = []
        for taxa_name in taxa_name_list:
            objects_list.append( self.get_object_from_name( taxa_name ) )
        return objects_list

    def save( self, dont_generate = False, **kwargs ):
        regenerate = False
        if not self.id: # if instance is not in the database
            regenerate = True
        super( Tree, self ).save( **kwargs )
        if regenerate and not dont_generate:
            self.generate_tree_infos()

    def generate_tree_infos( self ):
        if  [i for i in ('(',')',',') if i in self.delimiter]:
            raise ValueError, '"%s" is a bad delimiter' % self.delimiter
        tree = self.tree_string.lower().replace( self.delimiter, ' ' )
        if checkNwk( tidyNwk( tree ) ):
            self.is_valid = True
            self.save( dont_generate = True )
        for taxa_name in getTaxa( tree ):#set( getTaxa( tree ) ):
            if taxa_name.strip():
                taxa_name = self.strip_taxa_name( taxa_name )
                taxo_list = Taxonomy.objects.filter( name = taxa_name )
                if not taxo_list:
                    t, created = BadTaxa.objects.get_or_create( name = taxa_name )
                    # Enable login of reccurence
                    # TODO mettre un signal pour incrementer l'occurence
                    t.nb_occurence += 1
                    t.save()
                    ###
                    self.bad_taxas.add( t )
                else:
                    for taxo in taxo_list:
                        tto, created = TaxonomyTreeOccurence.objects.get_or_create( taxonomy = taxo, tree = self )
                        tto.nb_occurence += 1
                        tto.save()
                        if taxo.type_name == 'scientific name':
                            taxa = Taxa.objects.filter( name = taxo.name )[0]
                            self.taxas.add( taxa )
                        elif taxo.type_name == 'synonym':
                            taxa = SynonymName.objects.filter( name = taxo.name)[0]
                            self.synonyms.add( taxa )
                        elif taxo.type_name == 'homonym':
                            taxa = HomonymName.objects.filter( name = taxo.name)[0]
                            self.homonyms.add( taxa )
                        elif taxo.type_name == 'common':
                            taxa = CommonName.objects.filter( name = taxo.name)[0]
                            self.commons.add( taxa )
                        else:
                            raise RuntimeError, "%s has no or bad type_name" % taxo.name
            

    def __get_scientific_taxa( self, taxa_list ):
        return [taxa for taxa in taxa_list if taxa._meta.module_name == 'taxa']

    def get_ambiguous( self ):
        """
        return a queryset of taxonomy objects wich are not scientific name
        """
        return self.taxonomy_objects.exclude( type_name = 'scientific name' )
    ambiguous = property( get_ambiguous )

    def __generate_arborescence( self, tree=None ):
        if tree is None:
            # Init attributes
            import networkx as NX
            self.__networkx_tree = NX.DiGraph()
            tree = self.tree_string
            self.__children = []
            self.__last_child = ""
            self.__rel_name = {}
            self.__miss_spelled = {}
        if getChildren( tree ):
            if tree == self.tree_string:
                parent_name = Taxa.objects.get( name = 'root' )
            else:
                if not self.__rel_name.has_key( tree ):
                    taxa_list = self.__get_django_objects_from_nwk( tree )
                    stn_list = self.__get_scientific_taxa( taxa_list )
                    parent_name = self.get_first_common_parent(stn_list)
                else:
                    parent_name = self.__rel_name[tree]
            for child_name in getChildren( tree ):
                if getChildren( child_name ): # child is a node
                    taxa_list = self.__get_django_objects_from_nwk( child_name )
                    stn_list = self.__get_scientific_taxa( taxa_list )
                    child = self.get_first_common_parent(stn_list)
                    if child is None:
                        child = parent_name
                    if child not in self.__children:
                        self.__children.append( parent_name )
                    self.__rel_name[child_name] = child
                    self.__children.append( child )
                    self.__last_child = child
                    self.__networkx_tree.add_edge( parent_name, child )
                    self.__generate_arborescence( tree = child_name )
                else: # child is a taxon
                    child_name = child_name.replace( self.delimiter, ' ' )
                    child = self.get_object_from_name( child_name )
                    if child is None:
                        child = parent_name
                    self.__networkx_tree.add_edge( parent_name, child )

    def get_arborescence( self ):
        if not hasattr( self, '__networkx_tree' ):
            self.__generate_arborescence()
        return self.__networkx_tree
    arborescence = property( get_arborescence )

    def get_nb_taxa_from_parent( self, parent_name ):
        return self.taxas.filter( 
          parents_relation_taxas__parent__name = parent_name ).count()

    def eval_query( self, query, usertaxa_list=[] ):
        """
        test if a query match the tree. The query format is a python
        boolean expression with taxa name beetween braces :

        tree.eval_query( "{muridae} > 2 and {primates}" )

        will return true if tree have more than 2 taxas wich have muridae as parents
        and at least 1 taxa wich have a primate as parents.

        if a taxa_list is not null, the query can have another variable
        {usertaxa}. this variable represente all taxa passed in the list.

        tree.eval_query( "{muridae} => 4 and {usertaxa} > 2", ['rattus', 'mus', 'pan', 'boss'] )

        will return true if tree have at least 4 taxa wich are muridae and
        more than 2 taxa wich are in the usertaxa_list 
        """
        res = query.strip()
        for pattern in re.findall("{([^}]+)}", query):
            striped_pattern = pattern.strip().lower()
            if not striped_pattern == 'usertaxa' and not self.is_valid_name( striped_pattern ):
                raise NameError, striped_pattern
            if striped_pattern == 'usertaxa':
                if usertaxa_list:
                    query = Q()
                    for taxa_name in usertaxa_list:
                        query |= Q( name = taxa_name )
                    nb_occurence = self.taxas.filter( query ).count()
                else:
                    nb_occurence = 0
            else:
                nb_occurence = self.get_nb_taxa_from_parent( striped_pattern )
            res = res.replace("{"+pattern+"}", str(nb_occurence) )
        if res:
            try:
                return eval( res )
            except:
                raise SyntaxError, "bad query %s" % query
        raise SyntaxError, "bad query %s" % query

##################################################
#               TreeCollection                   #
##################################################

# get all trees wich have 'muridae' taxa
# col.trees.filter( taxas__parents_relation_taxas__parent__name = 'muridae' )

class TreeCollection( models.Model ):
    name = models.CharField( max_length = 80, null= True, unique=True )
    original_collection_string = models.TextField( null = True )
    delimiter = models.CharField( max_length = 5, default=' ' )
    description = models.TextField( null = True)
    format = models.CharField( max_length = 20, null = True )
    created = models.DateTimeField()
    updated = models.DateTimeField()
    trees = models.ManyToManyField( Tree, related_name = 'collections' )

    def __unicode__( self ):
        return "%s (%s)" % ( self.name, self.format )

    def get_ambiguous( self ):
        """
        return a queryset of non scientific name taxonomy objects
        """
        return self.taxonomy_objects.exclude( type_name = 'scientific name' )
    ambiguous = property( get_ambiguous )

    def save( self, collection_changed = False, dont_regenerate = False,  **kwargs ):
        collection_string_changed = False
        if not collection_changed and not dont_regenerate:
            if self.id: # if instance is in the database
                if TreeCollection.objects.get( id = self.id).original_collection_string != self.original_collection_string:
                    collection_string_changed = True
            else:
                collection_string_changed = True
        super( TreeCollection, self ).save( **kwargs )
        if self.original_collection_string and collection_string_changed and not dont_regenerate:
            self.regenerate_from_original_collection_string()

    def regenerate_collection_string_from_trees( self ):
        """
        regenerate original_collection_string from trees in the collection
        """
        self.original_collection_string = self.get_collection_string()
        self.save( collection_changed = True )

    def regenerate_from_original_collection_string( self ):
        # TODO mettre un signal sur cette method quand
        # original_collection_string change
        if self.trees.count():
            Tree.objects.filter( collections = self ).delete()
        nwk_collection = self.original_collection_string
        # Nexus collection
        if nwk_collection[:6].lower().strip() == "#nexus":
            nex = Nexus( nwk_collection )
            self.format = 'nexus'
            self.save( dont_regenerate = True )
            for name, (tree, rooted) in nex.collection.iteritems():
                t = Tree.objects.create( name = name, tree_string = tree,
                  rooted = rooted, delimiter = self.delimiter )
                self.trees.add( t )
        # Phylip collection
        else:
            self.format = 'phylip'
            self.save( dont_regenerate = True )
            name = 0
            for nwktree in nwk_collection.strip().split(";"):
                tree = removeBootStraps( tidyNwk( nwktree.strip().lower())).strip()
                if tree:
                    name += 1
                    t = Tree.objects.create( name = name, tree_string = tree,
                      rooted = False, delimiter = self.delimiter )
                    self.trees.add( t )

    def get_collection_string( self ):
        """
        Generate from trees the collection_string in specified format.
        Formats are 'phylip' (default) or 'nexus'
        """
        result = []
        for (name, tree_string, rooted) in self.trees.values_list( 'name', 'tree_string', 'rooted' ):
            if rooted: rooted = '[&R]'
            else: rooted = ''
            if self.format == 'nexus':
                result.append( 'TREE %s = %s %s' % (name, rooted, tree_string ) )
            else:
                result.append( tree_string.strip() )
        if self.format == 'nexus':
            return "#NEXUS\n\nBEGIN TREES;\n\n"+";\n".join( result )+"\n\nEND;\n"
        else:
            return ";\n".join( result )+';'

    def get_taxas( self ):
        return Taxa.objects.filter( trees__collections = self ).distinct()
    taxas = property( get_taxas )

    def get_bad_taxas( self ):
        return BadTaxa.objects.filter( trees__collections = self).distinct()
    bad_taxas = property( get_bad_taxas )

    def get_synonyms( self ):
        return SynonymName.objects.filter( trees__collections = self).distinct()
    synonyms = property( get_synonyms )

    def get_homonyms( self ):
        return HomonymName.objects.filter( trees__collections = self).distinct()
    homonyms = property( get_homonyms )

    def get_common_names( self ):
        return CommonName.objects.filter( trees__collections = self).distinct()
    commons = property( get_common_names )

    def get_taxonomy_objects( self ):
        return Taxonomy.objects.filter( trees__collections = self ).distinct()
    taxonomy_objects = property( get_taxonomy_objects )

    def get_bad_trees( self ):
        return self.trees.filter( is_valid = False )
    bad_trees = property( get_bad_trees )

    def query( self, query, usertaxa_list = [] ):
        """
        return a list of trees matching the query. You can pass usertaxa_list
        in order to use the {usertaxa} variable (see Tree.eval_query for more
        details)
        """
        trees_list = set([])
        for tree in self.trees.all():
            if tree.eval_query( query, usertaxa_list ):
                trees_list.add( tree )
        return list( trees_list )

    def get_collection_from_query( self, query ):
        """
        return a new collection with all trees that match the query
        """
        collection = TreeCollection.objects.create()
        collection.trees = self.query( query )
        collection.regenerate_collection_string_from_trees()
        return collection
        
    def get_tree_size_distribution( self ):
        """ return stat of Tree Size Distribution """
        stat = {}
        for tree in self.trees.all():
            nbtaxa = tree.taxas.all().count()
            if not stat.has_key( nbtaxa ):
                stat[nbtaxa] = 0
            stat[nbtaxa] += 1
        if not stat.keys():
            raise ValueError, "your collection must have trees"
        nbmax = max( stat.keys() )
        ratio = int( nbmax*10.0/100) or 1 # 1 to prevent crash in xrange
        result_stat = {}
        for i in xrange( 0, nbmax+1, ratio):
            result_stat[i] = 0
        for i,j in stat.iteritems():
            for key in result_stat.keys():
                if key <= i < key+ratio:
                    result_stat[key] += j
        return result_stat

    def get_taxon_frequency_distribution( self ):
        stat = {}
        for tree in self.trees.all():
            already_done = set()
            for taxon in tree.taxas.all():
                if taxon not in already_done:
                    if not stat.has_key( taxon ):
                        stat[taxon] = 0
                    stat[taxon] += 1    
                    already_done.add( taxon )
        if not stat.values():
            raise ValueError, "your collection must have trees"
        nbmax = max( stat.values() )
        ratio = int( nbmax*10.0/100) or 1
        result_stat = {}
        for i in xrange( 0, nbmax+1, ratio):
            result_stat[i] = 0
        for i in stat.values():
            for key in result_stat.keys():
                if key <= i < key+ratio:
                    result_stat[key] += 1
        return result_stat

    def get_taxa_from_parents( self, parent_name ):
        """
        return taxa in collection wich are for parent 'parent_name'
        """
        return self.taxas.filter( parents_relation_taxas__parent__name = parent_name )

#############################################
#                Signals                    #
#############################################

def fill_created_updated_fields( sender, instance, signal, *args, **kwargs ):
    if not instance.id:
        instance.created = datetime.datetime.now()
    instance.updated = datetime.datetime.now()
signals.pre_save.connect(fill_created_updated_fields, sender=Tree)
signals.pre_save.connect(fill_created_updated_fields, sender=TreeCollection)



