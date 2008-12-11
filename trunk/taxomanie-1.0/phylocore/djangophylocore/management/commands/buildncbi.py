from django.core.management.base import NoArgsCommand
from optparse import make_option

import os
import sys
from django.conf import settings

localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)
DUMP_PATH = os.path.join( absDir,'..','..', 'dumps' ) 

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--verbose', '-v', action='store_true', dest='verbose', 
            help='Verbose operation'),
    )
    help = "Download and build the ncbi database"
    requires_model_validation = False

    TEST = False
    TBI = {}
    TBN = {}
    NAMES = "names.dmp"
    NODES = "nodes.dmp"

    def __generate_test_fixtures( self ):
       #
        # Test TBI
        #
        self.list_id = set([])
        TAXOTEST = open( 'taxonomy_test.csv' ).readlines()
        for line in TAXOTEST:
            taxa_id, taxa_name, parent_name, homonym_name, parents_list, synonym_list, common_list = line.split( '|' )
            self.list_id.add( taxa_id )
            for parent_id in self.TBI[taxa_id]['parents']:
                self.list_id.add( parent_id )
        #
        #
        #
 
    def handle_noargs(self, **options):
        global DUMP_PATH
        verbose = options.get("verbose", False)
        if verbose:
            print "loading taxonomy, please wait, it can take a while..."
        if not os.path.exists( DUMP_PATH ):
            os.system( 'mkdir %s' % DUMP_PATH )
        else:
            os.system( 'rm %s/*' % DUMP_PATH )
        os.system( 'rm taxdump.tar.gz' )
        self.download_ncbi( verbose )
        self.generate_structure( verbose )
        if self.TEST:
            self.__generate_test_fixtures()
        if verbose:
            print "making rank.dmp"
        self.make_rank()
        if verbose:
            print "making taxonomy.dmp"
        self.make_taxa()
        self.make_taxonomy_plus( verbose )
#        if verbose:
#            print "making synonym"
        #self.make_taxonomy( 'synonym', 'synonymname.dmp', 'synonym.dmp' )
#        self.make_taxonomy( 'synonym', 'relsynonymtaxa.dmp' )
#        if verbose:
#            print "making homonym"
#        self.make_taxonomy( 'homonym', 'relhomonymtaxa.dmp' )
#        if verbose:
#            print "making common"
#        self.make_taxonomy( 'common', 'relcommontaxa.dmp' )
        if verbose:
            print "making parents"
        self.make_parents()
        # generate taxonomy
#        if verbose:
#            print "making taxonomy"
#        open( os.path.join( DUMP_PATH, './taxonomy.dmp' ), 'w').write( '' )
#        file = open( os.path.join( DUMP_PATH, './taxonomy.dmp' ), 'a' )
#        index = 1
#        index = self.generate_homonyms(file, index)
#        index = self.generate_synonyms(file, index)
#        index = self.generate_commons(file, index)
#        index = self.generate_scientific(file, index)
#        if verbose:
#            print '%s items in the taxonomy' % index
        os.system( 'rm nodes.dmp names.dmp' )
        os.system( 'rm taxdump.tar.gz' )
 
    def download_ncbi( self, verbose ):
        if not os.path.exists( './taxdump.tar.gz' ):
            if verbose:
                print "Downloading NCBI database on the web"
            os.system( "curl -# ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz > taxdump.tar.gz ")
            #os.system( "wget ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz" )
        if verbose:
            print "Extracting database... please wait"
        os.system( "tar xf taxdump.tar.gz names.dmp nodes.dmp" )
 
    def generate_structure( self, verbose ):
        global DUMP_PATH
        def getParents( id, TBI ):
            lp = []
            while id != "1":
                id_parent = TBI[id]["parent"]
                lp.append( id_parent )
                id = id_parent
            return lp
        if verbose:
            print "Generating structure..."
        # Retrieving all scientific names
        index = 0
        for line in file( self.NAMES ).readlines():
            id = line.split("|")[0].strip()
            name = line.split("|")[1].strip().lower()
            homonym = line.split("|")[2].strip().lower()
            type_name = line.split("|")[3].strip()
            synonym = "synonym" in type_name
            common = "common name" in type_name
            self.index = int(id)
            if type_name == "scientific name":
                # Creating TAXONOMY_BY_ID
                self.TBI[id] = {}
                if homonym:
                    self.TBI[id]["name"] = homonym
                else:
                    self.TBI[id]["name"] = name
                self.TBI[id]["common"] = []
                self.TBI[id]["homonym"] = []
                self.TBI[id]["synonym"] = []
                self.TBI[id]["parent"] = []
                self.TBI[id]["parents"] = []
                self.TBI[id]["type_name"] = 'scientific name'
                # Creating TAXONOMY_BY_NAME
                if homonym:
                    self.TBN[homonym] = {}
                    self.TBN[homonym]["id"] = id
                    self.TBN[homonym]["homonym"] = name
                else:
                    self.TBN[name] = {}
                    self.TBN[name]["id"] = id
        if verbose:
            print "Extracting parents..."
        for node in file( self.NODES ).readlines():
            id = node.split("|")[0].strip()
            parent = node.split("|")[1].strip()
            rank = node.split('|')[2].strip()
            name = self.TBI[id]["name"]
            name = self.TBI[id]['rank'] = rank
            if not self.TBI.has_key( id ):
                self.TBI[id] = {}
            self.TBI[id]["parent"] = parent
            if not self.TBN.has_key( name ):
                self.TBN[name] = {}
            self.TBN[name]["parent"] = parent
        if verbose:
            print "Filling parents..."
        for node in file( self.NODES ).readlines():
            id = node.split("|")[0].strip()
            self.TBI[id]["parents"] = getParents( id, self.TBI )

    def make_taxonomy_plus( self, verbose ):
        if verbose:
            print "Adding synonyms, homonyms and common names..."
        # Adding synonyms, homonyms and common names
        index = self.index
        list_synonym = []
        list_common = []
        list_homonym = []
        list_relsynonymtaxa = []
        list_relcommontaxa = []
        list_relhomonymtaxa = []
        index_relsynonym = 0
        index_relcommon = 0
        index_relhomonym = 0
        homonym_toc = {}
        common_toc = {}
        synonym_toc = {}
        for line in file( self.NAMES ).readlines():
            type_name = line.split("|")[3].strip()
            synonym = "synonym" in type_name
            common = "common name" in type_name
            homonym = line.split("|")[2].strip().lower()
            id = line.split("|")[0].strip()
            if self.TEST:
                if id not in self.list_id:
                    continue
            name = line.split("|")[1].strip().lower()
            if synonym or common:
                if homonym: # We do not want synonym wich have homonym
                    continue
                base_name = self.TBI[id]["name"]
                if synonym:
                    if name not in synonym_toc:
                        index += 1
                        list_synonym.append( "%s|%s|synonym|2|\n" % ( index, name.replace( "(", "_" ).replace( ")", "_") ) )
                        synonym_toc[name] = index
                    index_relsynonym += 1
                    list_relsynonymtaxa.append(
                      "%s|%s|%s\n" % ( index_relsynonym, index, id ) )
                if common:
                    if name not in common_toc:
                        index += 1
                        list_common.append( "%s|%s|common|2|\n" % ( index, name.replace( "(", "_").replace( ")", "_") ) )
                        common_toc[name] = index
                    index_relcommon += 1
                    list_relcommontaxa.append(
                      "%s|%s|%s|english\n" % ( index_relcommon, index, id ) )
            if type_name == "scientific name" and homonym:
                if name not in homonym_toc:
                    index += 1
                    list_homonym.append( '%s|%s|homonym|2|\n' % ( index, name.replace( "(", "_" ).replace( ")", "_" ) ) )
                    homonym_toc[name] = index
                index_relhomonym += 1
                list_relhomonymtaxa.append(
                  "%s|%s|%s\n" % ( index_relhomonym, homonym_toc[name], id ) )
        taxonomy_file = open( os.path.join( DUMP_PATH, 'taxonomy.dmp' ), 'a' )
        taxonomy_file.write( ''.join( list_synonym ) )
        taxonomy_file.write( ''.join( list_common ) )
        taxonomy_file.write( ''.join( list_homonym ) )
        taxonomy_file.close()
        open( os.path.join( DUMP_PATH, 'relsynonymtaxa.dmp' ), 'w' ).write(
          ''.join( list_relsynonymtaxa ) )
        open( os.path.join( DUMP_PATH, 'relcommontaxa.dmp' ), 'w' ).write(
          ''.join( list_relcommontaxa ) )
        open( os.path.join( DUMP_PATH, 'relhomonymtaxa.dmp' ), 'w' ).write(
          ''.join( list_relhomonymtaxa ) )

    ################################################
    #               Generating dumps               #
    ################################################
    RANK = {}
    def make_rank( self ):
        global DUMP_PATH
        l_rank = []
        list_line = []
        index = 0
        for species in self.TBI.keys():
            rank = self.TBI[species]['rank']
            if rank not in l_rank:
                index += 1
                line = '%s|%s' % ( index, rank )
                list_line.append( line )
                l_rank.append( rank )
                self.RANK[rank] = index
        open( os.path.join( DUMP_PATH, 'rank.dmp' ), 'w' ).write( '\n'.join( list_line ) )

    def make_taxa( self  ):
        global DUMP_PATH
        # Taxa.dmp
        list_line = []
        for species in self.TBI.keys():
            if self.TEST:
                if species not in self.list_id:
                    continue
            line = '%s|%s|%s|%s|%s\n' % (
              species,
              self.TBI[species]['name'].replace( "(", "_").replace(")","_"),
              self.TBI[species]['type_name'],
              self.RANK[self.TBI[species]['rank']],
              self.TBI[species]['parent']
            )
            list_line.append( line )
        open( os.path.join( DUMP_PATH, 'taxonomy.dmp' ), 'w' ).write( ''.join( list_line ) )

    def make_parents( self ):
        global DUMP_PATH
        id_rel = 0
        list_parents = []
        for species in self.TBI.keys():
            index = 0
            if self.TEST:
                if species not in self.list_id:
                    continue
            for parent_id in self.TBI[species]["parents"]:
                id_rel += 1
                line = '%s|%s|%s|%s\n' % ( id_rel,species, parent_id, index ) 
                list_parents.append( line )
                index += 1
        open( os.path.join( DUMP_PATH, 'parentsrelation.dmp' ), 'w' ).write( ''.join( list_parents ) )

