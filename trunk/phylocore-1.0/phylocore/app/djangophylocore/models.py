#-*- coding: utf-8 -*-

from django.db import models
from django.db.models import signals, Q
from django.conf import settings
from django.db import transaction
from django.db import connection

from lib.phylogelib import getTaxa, getChildren, removeBootStraps
from lib.phylogelib import getBrothers, removeNexusComments
from lib.phylogelib import tidyNwk, checkNwk
from lib.nexus import Nexus
import datetime, re, sys, os, codecs

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
        if Taxonomy.objects.filter( name = name,
          type_name = 'scientific name' ).count():
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
        return Taxonomy.objects.filter( taxa_from_common__common__name = common_name )

    def get_name_from_synonym( self, synonym ):
        """
        return all taxa which have synonym
        """
        return Taxonomy.objects.filter( taxa_from_synonym__synonym__name = synonym )

    def get_name_from_homonym( self, homonym ):
        """
        return all taxa which have homonym
        """
        return Taxonomy.objects.filter( taxa_from_homonym__homonym__name = homonym )

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
            return Taxonomy.objects.filter( name = taxa_name )
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
                        from lib.spell import correct
                        #from phylocore.spellcheck import SpellCheck
                        #splchk = SpellCheck( self.TAXONOMY.iterkeys() )
                        #return splchk.correct( name )
                        return list(correct( name ))
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
#                 Taxonomy                       #
##################################################

class Taxonomy( models.Model ):
    name = models.CharField( max_length = 200 )
    type_name = models.CharField( max_length = 50 )
    rank = models.ForeignKey( Rank, related_name = 'taxas', null = True )
    parent = models.ForeignKey( 'self', related_name = 'direct_children', null = True )
    _parents = models.ManyToManyField( 'self', through = 'ParentsRelation', related_name = 'children', symmetrical=False )
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'type_name']

    def __unicode__( self ):
        return "%s (%s)" % ( self.name, self.type_name )

    def get_homonyms( self ):
        return Taxonomy.objects.filter( homonym_from_taxa__taxa = self )
    homonyms = property( get_homonyms )

    def get_synonyms( self ):
        return Taxonomy.objects.filter( synonym_from_taxa__taxa = self )
    synonyms = property( get_synonyms )

    def get_commons( self ):
        return Taxonomy.objects.filter( common_from_taxa__taxa = self )
    commons = property( get_commons )

    def get_scientific_names( self ):
        if self.type_name == 'homonym':
            return Taxonomy.objects.filter( taxa_from_homonym__homonym = self )
        elif self.type_name == 'synonym':
            return Taxonomy.objects.filter( taxa_from_synonym__synonym = self )
        elif self.type_name == 'common':
            return Taxonomy.objects.filter( taxa_common_from__common = self )
        else:
            return Taxonomy.objects.none()
    scientifics = property( get_scientific_names )

    def get_parents( self, regenerate = False ):
        if regenerate:
            self.regenerate_parents()    
        return [i.parent for i in self.parents_relation_taxas.all()]
    parents = property( get_parents )

    def get_children( self, regenerate = False ):
        if regenerate:
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
    taxa = models.ForeignKey( Taxonomy, related_name='parents_relation_taxas' )
    parent = models.ForeignKey( Taxonomy, related_name = 'parents_relation_parents' )
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

class RelCommonTaxa( models.Model ):
    common = models.ForeignKey( Taxonomy, related_name='common_from_taxa' )
    taxa = models.ForeignKey( Taxonomy, related_name = 'taxa_from_common' )
    language = models.CharField( max_length = 80, null = True )
    class Meta:
        ordering = ['taxa','common']
        unique_together = ('common', 'taxa')

    def __unicode__( self ):
        return "%s -> (%s)" % ( self.common, self.taxa )

##################################################
#               Synonym staffs                   #
##################################################

class RelSynonymTaxa( models.Model ):
    synonym = models.ForeignKey( Taxonomy, related_name='synonym_from_taxa' )
    taxa = models.ForeignKey( Taxonomy, related_name = 'taxa_from_synonym' )
    class Meta:
        ordering = ['taxa','synonym']
        unique_together = ('synonym', 'taxa')

    def __unicode__( self ):
        return "%s -> (%s)" % ( self.synonym, self.taxa )

##################################################
#               Homonym staffs                   #
##################################################

class RelHomonymTaxa( models.Model ):
    homonym = models.ForeignKey( Taxonomy, related_name='homonym_from_taxa' )
    taxa = models.ForeignKey( Taxonomy, related_name = 'taxa_from_homonym' )
    class Meta:
        ordering = ['taxa','homonym']
        unique_together = ('homonym', 'taxa')

    def __unicode__( self ):
        return "%s -> (%s)" % ( self.homonym, self.taxa )

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
    taxa = models.ForeignKey( Taxonomy, related_name = 'taxonomy_occurences' )
    tree = models.ForeignKey( 'Tree', related_name = 'taxonomy_occurences' )
    user_taxa_name = models.CharField( max_length = 200, null = True )
    nb_occurence = models.IntegerField( default = 0 )
    class Meta:
        unique_together = ( 'taxa', 'tree', 'user_taxa_name' )

    def __unicode__( self ):
        return u'%s (%s) %s' % ( self.taxa, self.nb_occurence, self.tree )

class Tree( models.Model, TaxonomyReference ):
    name = models.CharField( max_length = 80, null=True )
    delimiter = models.CharField( max_length = 5, default=' ' )
    tree_string = models.TextField()
    rooted = models.BooleanField( null = True )
    description = models.TextField( null = True )
    created = models.DateTimeField()
    updated = models.DateTimeField()
    is_valid = models.BooleanField( default = False )
    _from_collection = models.BooleanField( default = False )
    #
    collection = models.ForeignKey( 'TreeCollection', related_name = 'trees', null = True)
    bad_taxas = models.ManyToManyField( BadTaxa, related_name = 'trees'  )
    taxa_ids = []

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

    @transaction.commit_on_success
    def save( self, dont_generate = False, **kwargs ):
        regenerate = False
        if not self.id: # if instance is not in the database
            regenerate = True
        super( Tree, self ).save( **kwargs )
        if regenerate and not dont_generate:
            self.generate_tree_infos()

    @transaction.commit_on_success
    def generate_tree_infos( self ):
        if [i for i in ('(',')',',') if i in self.delimiter]:
            raise ValueError, '"%s" is a bad delimiter' % self.delimiter
        tree = self.tree_string.lower()#.replace( self.delimiter, ' ' )
        if checkNwk( tidyNwk( tree ) ):
            self.is_valid = True
            self.save( dont_generate = True )
        taxas_list = getTaxa( tree ) # set( getTaxa( tree ) )
        self.taxa_ids = {}
        for taxa_name in taxas_list:
            if taxa_name.strip():
                user_taxa_name = taxa_name
                taxa_name = self.strip_taxa_name( taxa_name ).replace( self.delimiter, ' ' )
                taxo_list = Taxonomy.objects.filter( name = taxa_name )
                if not taxo_list:
                    t, created = BadTaxa.objects.get_or_create( name = user_taxa_name )
                    # Enable login of reccurence
                    # TODO mettre un signal pour incrementer l'occurence
                    t.nb_occurence += 1
                    t.save()
#                    ###
                    self.bad_taxas.add( t )
                else:
                    for taxo in taxo_list:
                        if self._from_collection:
                            self.taxa_ids[taxo.id] = user_taxa_name
                        else:
                            tto, created = TaxonomyTreeOccurence.objects.get_or_create( 
                              taxa = taxo, tree = self, user_taxa_name = user_taxa_name )
                            tto.nb_occurence += 1
                            tto.save()

    def __get_relation( self ):
        class Meta: pass
        model_rel =  type( 'RelTreeColTaxa%s' % self.collection.id, #name.capitalize(),
          (AbstractTreeColTaxa,), {'__module__': Taxonomy.__module__, 'Meta':Meta})
        return model_rel.objects.filter( tree = self )
    rel = property( __get_relation )

    def get_taxas( self ):
        if not self._from_collection:
            return Taxonomy.objects.filter( taxonomy_occurences__tree = self )
        return Taxonomy.objects.extra( where = ['djangophylocore_taxonomy.id IN (SELECT taxa_id from djangophylocore_reltreecoltaxa%s WHERE tree_id = %s)' % (self.collection.id, self.id)] )
    taxas = property( get_taxas )

    def get_ambiguous( self ):
        """
        return a queryset of taxonomy objects wich are not scientific name
        """
        return self.taxas.exclude( type_name = 'scientific name' )
    ambiguous = property( get_ambiguous )

    def get_scientific_names( self ):
        return self.taxas.filter( type_name = 'scientific name' )
    scientifics = property( get_scientific_names )
        
    def get_synonyms( self ):
        return self.taxas.filter( type_name = 'synonym' )
    synonyms = property( get_synonyms )

    def get_commons( self ):
        return self.taxas.filter( type_name = 'common' )
    commons = property( get_commons )

    def get_homonyms( self ):
        return self.taxas.filter( type_name = 'homonym' )
    homonyms = property( get_homonyms )

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
                parent_name = Taxonomy.objects.get( name = 'root' )
            else:
                if not self.__rel_name.has_key( tree ):
                    taxa_list = self.__get_django_objects_from_nwk( tree )
                    stn_list = Taxonomy.objects.filter( type_name = 'scientific name' )
                    parent_name = self.get_first_common_parent(stn_list)
                else:
                    parent_name = self.__rel_name[tree]
            for child_name in getChildren( tree ):
                if getChildren( child_name ): # child is a node
                    taxa_list = self.__get_django_objects_from_nwk( child_name )
                    stn_list = Taxonomy.objects.filter( type_name = 'scientific name' )
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
        parent = Taxonomy.objects.get( name = parent_name )
        return len( [t for t in self.taxas if parent in t.parents] )
        return self.taxas.filter( parents_relation_taxas__parent__name = parent_name ).count()

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
        print "+++++++++++++++++++++++++++++++++"
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
            print res
        print "-------------------------------------"
        if res:
            try:
                return eval( res )
            except:
                raise SyntaxError, "bad query %s" % query
        raise SyntaxError, "bad query %s" % query

##################################################
#               TreeCollection                   #
##################################################

class TreeCollection( models.Model ):
    name = models.CharField( max_length = 80, null= True )
    original_collection_string = models.TextField( null = True ) # source
    delimiter = models.CharField( max_length = 5, default=' ' )
    description = models.TextField( null = True)
    format = models.CharField( max_length = 20, null = True )
    created = models.DateTimeField()
    updated = models.DateTimeField()

    def __unicode__( self ):
        return "%s (%s)" % ( self.name, self.format )

    @transaction.commit_on_success
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

    def __create_relation( self, name, dump ):
        cursor = connection.cursor()
        cursor.execute( """ CREATE TABLE "djangophylocore_reltreecoltaxa%s" (
            "id" integer NOT NULL PRIMARY KEY,
            "collection_id" integer NOT NULL REFERENCES "djangophylocore_treecollection" ("id"),
            "tree_id" integer NOT NULL REFERENCES "djangophylocore_tree" ("id"),
            "taxa_id" integer NULL REFERENCES "djangophylocore_taxonomy" ("id"),
            "user_taxa_name" varchar(200) NULL
        );""" % name )
        codecs.open( '/tmp/rel_%s.dmp' % name, encoding='utf-8', mode='w').write( ''.join( dump ) )
        if settings.DATABASE_NAME == ':memory:':
            db_name = settings.TEST_DATABASE_NAME
        else:
            db_name = settings.DATABASE_NAME
        if settings.DATABASE_ENGINE == 'sqlite3':
            os.system( "sqlite3 -separator '|' %s '.import /tmp/rel_%s.dmp djangophylocore_reltreecoltaxa%s'" % (
              db_name, name, name ) )
        elif settings.DATABASE_ENGINE == 'mysql':
            cmd = """mysql -u %s -p%s %s -e "LOAD DATA LOCAL INFILE '/tmp/rel_%s.dmp' INTO TABLE djangophylocore_reltreecoltaxa%s FIELDS TERMINATED BY '|';" """ % ( settings.DATABASE_USER, settings.DATABASE_PASSWORD, nb_name, name, name )
        else:
            raise RuntimeError, "%s engine not supported" % settings.DATABASE_ENGINE
        os.system( 'rm /tmp/rel_%s.dmp' % name )

    def __get_relation( self ):
        class Meta: pass
        model_rel =  type( 'RelTreeColTaxa%s' % self.id, #name.capitalize(),
          (AbstractTreeColTaxa,), {'__module__': Taxonomy.__module__, 'Meta':Meta})
        return model_rel.objects.filter( collection = self )
    rel = property( __get_relation )

    @transaction.commit_manually
    def regenerate_from_original_collection_string( self ):
        # TODO mettre un signal sur cette method quand
        # original_collection_string change
        #if self.trees.count():
        #    Tree.objects.filter( collections = self ).delete()
        if settings.DEBUG and settings.DATABASE_ENGINE == 'sqlite3':
            if hasattr( settings, 'BOOST_SQLITE' ):
                if settings.BOOST_SQLITE:
                    cursor = connection.cursor()
                    cursor.execute('PRAGMA temp_store = MEMORY;')
                    cursor.execute('PRAGMA synchronous=OFF')
        #
        index = 0
        dump = []
        nwk_collection = self.original_collection_string
        # Nexus collection
        if nwk_collection[:6].lower().strip() == "#nexus":
            nex = Nexus( nwk_collection )
            self.format = 'nexus'
            self.save( dont_regenerate = True )
#            if settings.DEBUG:
#                i = 0
#                NB_LINE = len( nex.collection )
            for name, (tree, rooted) in nex.collection.iteritems():
                t = Tree( name = name, tree_string = tree, rooted = rooted,
                  delimiter = self.delimiter, _from_collection = True,
                  collection = self )
                t.save()
                if not t.taxa_ids:
                    index += 1
                    dump.append( '%s|%s|%s||\n' % (index, self.id, t.id ) )
                else:
                    for taxa_id in t.taxa_ids:
                        index += 1
                        # index, collection_id, tree_id, taxa_id, user_taxa_name
                        dump.append(  '%s|%s|%s|%s|%s\n' % (index, self.id,
                          t.id, taxa_id, t.taxa_ids[taxa_id] ) )
#                if settings.DEBUG:
#                    i += 1
#                    sys.stdout.write("\r[%s] %s%% " % ( str(i), str( i*100.0/NB_LINE)  ) )
#                    sys.stdout.flush()
        # Phylip collection
        else:
            self.format = 'phylip'
            self.save( dont_regenerate = True )
            name = 0
            l_trees = nwk_collection.strip().split(";")
#            if settings.DEBUG:
#                i = 0
#                NB_LINE = len( l_trees )
            for nwktree in l_trees:
                tree = removeBootStraps( tidyNwk( nwktree.strip().lower())).strip()
                if tree:
                    name += 1
                    t = Tree( name = name, tree_string = tree, rooted = False, 
                      delimiter = self.delimiter, _from_collection = True,
                      collection = self )
                    t.save()
                    if not t.taxa_ids:
                        index += 1
                        dump.append( '%s|%s|%s||\n' % (index, self.id, t.id ) )
                    else:
                        for taxa_id in t.taxa_ids:
                            index += 1
                            # index, collection_id, tree_id, taxa_id, user_taxa_name
                            dump.append(  '%s|%s|%s|%s|%s\n' % (index,
                              self.id, t.id, taxa_id, t.taxa_ids[taxa_id] ) )
#                if settings.DEBUG:
#                    i += 1
#                    sys.stdout.write("\r[%s] %s%% " % ( str(i), str( i*100.0/NB_LINE)  ) )
#                    sys.stdout.flush()
        self.__create_relation( str(self.id), dump )

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
        return Taxonomy.objects.extra( where = ['id IN (SELECT taxa_id from djangophylocore_reltreecoltaxa%s)' % self.id] )
    taxas = property( get_taxas )

    def get_ambiguous( self ):
        """
        return a queryset of non scientific name taxonomy objects
        """
        return self.taxas.exclude( type_name = 'scientific name' )
    ambiguous = property( get_ambiguous )

    def get_bad_taxas( self ):
        id_list = [i[0] for i in self.trees.values_list( 'id' ) if i[0]]
        return BadTaxa.objects.filter( trees__id__in = id_list ).distinct()
    bad_taxas = property( get_bad_taxas )

    def get_scientific_names( self ):
        return self.taxas.filter( type_name = 'scientific name').distinct()
    scientifics = property( get_scientific_names )

    def get_synonyms( self ):
        return self.taxas.filter( type_name = 'synonym').distinct()
    synonyms = property( get_synonyms )

    def get_homonyms( self ):
        return self.taxas.filter( type_name = 'homonym' ).distinct()
    homonyms = property( get_homonyms )

    def get_common_names( self ):
        return self.taxas.filter( type_name = 'common' ).distinct()
    commons = property( get_common_names )

    def get_bad_trees( self ):
        return self.trees.filter( is_valid = False )
    bad_trees = property( get_bad_trees )

    def _get_query_stats( self ):
        """
        proceure parcours_prof_suffixe(T : arbre )

            si non EstVide(T) alors

                    parcours_prof_suffixe(FilsGauche(T));
                    parcours_prof_suffixe(FilsDroit(T));
                    traiter_racine(T);

            fin si
        """
        raise NotImplementedError
        tree = self.get_reference_arborescence()
        def traitement( node ):
            for child in tree.successors_iter( Taxonomy.objects.get( name = 'root') ):
                nb_occurence += self._get_query_stats( child )
            stats[child.id] = nb_occurence



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
        return TreeCollection.objects.create( delimiter = self.delimiter, 
          original_collection_string = ';'.join( [i.tree_string for i in self.query( query )] ) )
        
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
        id_list = [i.id for i in Taxonomy.objects.get( name = parent_name ).direct_children.all()]
        return self.taxas.filter( id__in = id_list )

    def get_nb_trees( self, taxa ):
        """
        return the number of trees in collection wich contain taxa
        """
        return len(set([i[0] for i in self.rel.filter( taxa = taxa ).values_list( 'tree' )]))

    def get_filtered_collection_string( self, taxa_name_list ):
        """
        return a collections string wich have been striped of all taxa present
        in the taxa_name_list
        """
        if self.format == 'nexus':
            new_col = "#NEXUS\nBEGIN TREES;\n"
        else:
            new_col = ''
        for tree in self.trees.all():
            new_tree = tidyNwk( tree.tree_string ).lower()
            for taxa_name in taxa_name_list:
                user_taxa_list = [i.user_taxa_name for i in tree.rel.filter( taxa__name = taxa_name )]
                if not user_taxa_list: # if taxa_name not in taxonomy (bad taxa)
                    user_taxa_list = [taxa_name] # buid user_taxa_list from scratch
                for taxon in user_taxa_list:  # For taxa in user_name taxon
                    # while taxa user name exists, remove it
                    #taxon = self.delimiter.join( taxon.split() )
                    while taxon in getTaxa( new_tree ):
                        list_taxa = getBrothers(new_tree, taxon )
                        list_brother = getBrothers(new_tree, taxon )
                        if taxon in list_brother:
                            list_brother.remove( taxon )
                            if len( list_brother ) > 1:
                                new_tree = new_tree.replace( "("+",".join(list_taxa)+")", "("+",".join( list_brother)+")")
                            else:
                                new_tree = new_tree.replace( "("+",".join(list_taxa)+")", ",".join( list_brother ))
                        else:
                            new_tree = ""
            # Recreate nexus collection
            if new_tree:
                if len( getTaxa( new_tree ) ) == 1:
                    if self.format == 'nexus':
                        new_col += "Tree "+str(tree.name)+" = ("+new_tree+");\n"
                    else:
                        new_col += "("+new_tree+");\n"
                else:
                    if self.format == 'nexus':
                        new_col += "Tree "+str(tree.name)+" = "+new_tree+";\n"
                    else:
                        new_col += new_tree+";\n"
        if self.format == 'nexus':
            new_col += "END;\n"
        return new_col

    def get_restricted_collection( self, taxa_name_list ):
        """
        return a collection string wich contains only the taxa present in
        taxa_list
        """
        remove_taxa_list = [i.name for i in self.taxas.exclude( name__in = taxa_name_list )] 
        new_nwk = self.get_filtered_collection_string( remove_taxa_list )
        return TreeCollection.objects.create( delimiter = self.delimiter, original_collection_string = new_nwk )

    def get_corrected_collection_string( self, tuple_list ):
        """
        return a collection with correction from tuple_list:

        col_string = col.get_corrected_collection_string( [('echinops', 'echinops <plant>'), ('ratis', 'rattus' )] )
        """
        if self.format == 'nexus':
            new_col = "#NEXUS\nBEGIN TREES;\n"
        else:
            new_col = ''
        for tree in self.trees.all():
            new_tree = removeBootStraps( tidyNwk( tree.tree_string ).lower() )
            for bad_taxon, taxon in tuple_list:
                while bad_taxon in getTaxa( new_tree ):
                    list_taxa = getBrothers(new_tree, bad_taxon )
                    list_brother = getBrothers(new_tree, bad_taxon )
                    if bad_taxon in list_brother:
                        list_brother.remove( bad_taxon )
                        list_brother.append( taxon )
                        if len( list_brother ) > 1:
                            new_tree = new_tree.replace( "("+",".join(list_taxa)+")", "("+",".join( list_brother)+")")
                        else:
                            new_tree = new_tree.replace( "("+",".join(list_taxa)+")", ",".join( list_brother ))
                    else:
                        new_tree = ""
            # Recreate nexus collection
            if new_tree:
                if len( getTaxa( new_tree ) ) == 1:
                    if self.format == 'nexus':
                        new_col += "Tree "+str(tree.name)+" = ("+new_tree+");\n"
                    else:
                        new_col += "("+new_tree+");\n"
                else:
                    if self.format == 'nexus':
                        new_col += "Tree "+str(tree.name)+" = "+new_tree+";\n"
                    else:
                        new_col += new_tree+";\n"
        if self.format == 'nexus':
            new_col += "END;\n"
        return new_col

    def get_corrected_collection( self, tuple_list ):
        """
        return a collection with correction from tuple_list. tuple_list take
        the following format : [(bad_name1, good_name1), (bad_name2, good_name2)...]

        newcol = col.get_corrected_collection( [('echinops', 'echinops <plant>'), ('ratis', 'rattus' )] )
        """
        new_nwk = self.get_corrected_collection_string( tuple_list )
        return TreeCollection.objects.create( delimiter = self.delimiter, original_collection_string = new_nwk )

    def get_autocorrected_collection( self ):
        list_correction =  [(i.user_taxa_name, i.taxa.scientifics.get().name)\
          for i in self.rel.filter( taxa__in = self.taxas.exclude( type_name = 'scientific name' ) )\
            if i.taxa.scientifics.count() == 1] 
        return self.get_corrected_collection( list_correction ), list_correction

    def get_reference_arborescence( self ):
        """
        Take a taxa list, search in reference all parents names and
        return a networkx.DiGraph tree.
        """
        import networkx as NX
        tree = NX.DiGraph() 
        taxa_list = self.taxas.filter( type_name = 'scientific name' ).iterator
        already_done = set([])
        for taxa in taxa_list():
            while taxa.name != 'root' and taxa not in already_done:
                #if taxa.parent in already_done:
                #    break
                tree.add_edge( taxa.parent, taxa )
                already_done.add( taxa )
                taxa = taxa.parent
        return tree

class AbstractTreeColTaxa( models.Model ):
    collection = models.ForeignKey( TreeCollection )#, related_name = 'rel' )
    tree = models.ForeignKey( Tree )#, related_name = 'rel' )
    taxa = models.ForeignKey( Taxonomy )#, related_name = 'rel', null = True )
    user_taxa_name = models.CharField( max_length = 200, null = True )
                
    class Meta:
        abstract = True
    def __unicode__( self ):
        return u"%s|%s|%s" % (self.collection.id, self.tree.id, self.taxa.name)

#############################################
#                Signals                    #
#############################################

def fill_created_updated_fields( sender, instance, signal, *args, **kwargs ):
    if not instance.id:
        instance.created = datetime.datetime.now()
    instance.updated = datetime.datetime.now()
signals.pre_save.connect(fill_created_updated_fields, sender=Tree)
signals.pre_save.connect(fill_created_updated_fields, sender=TreeCollection)


#def build_taxonomy_toc():
#    TAXONOMY_TOC = {}
#    for taxa in Taxonomy.objects.all().iterator():
#        TAXONOMY_TOC[taxa.name] = taxa.id
#    print "++++++++++++++++++++++++++++++++++ok++++++++++++++++++++++++++++++"
#    return TAXONOMY_TOC
#
#TAXONOMY_TOC = build_taxonomy_toc()
