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

    TEST = True
    TBI = {}
    TBN = {}
    NAMES = "names.dmp"
    NODES = "nodes.dmp"
        
    def handle_noargs(self, **options):
        global DUMP_PATH
        verbose = options.get("verbose", False)
        if verbose:
            print "loading taxonomy, please wait, it can take a while..."
        os.system( 'rm %s/*' % DUMP_PATH )
        self.download_ncbi( verbose )
        self.generate_structure( verbose )
        if verbose:
            print "making rank.dmp"
        self.make_rank()
        if verbose:
            print "making taxa.dmp"
        self.make_taxa()
        if verbose:
            print "making synonym"
        self.make_taxonomy( 'synonym', 'synonymname.dmp', 'synonym.dmp' )
        if verbose:
            print "making homonym"
        self.make_taxonomy( 'homonym', 'homonymname.dmp', 'homonym.dmp' )
        if verbose:
            print "making common"
        self.make_taxonomy( 'common', 'commonname.dmp', 'common.dmp' )
        if verbose:
            print "making parents"
        self.make_parents()
        # generate taxonomy
        if verbose:
            print "making taxonomy"
        open( os.path.join( DUMP_PATH, './taxonomy.dmp' ), 'w').write( '' )
        file = open( os.path.join( DUMP_PATH, './taxonomy.dmp' ), 'a' )
        index = 1
        index = self.generate_homonyms(file, index)
        index = self.generate_synonyms(file, index)
        index = self.generate_commons(file, index)
        index = self.generate_scientific(file, index)
        if verbose:
            print '%s items in the taxonomy' % index
        os.system( 'rm nodes.dmp names.dmp' )
        os.system( 'rm taxdump.tar.gz' )
 
    def download_ncbi( self, verbose ):
        if not os.path.exists( './names.dmp' ) and not os.path.exists( './nodes.dmp' ):
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
        for line in file( self.NAMES ).readlines():
            id = line.split("|")[0].strip()
            name = line.split("|")[1].strip().lower()
            homonym = line.split("|")[2].strip().lower()
            type_name = line.split("|")[3].strip()
            synonym = "synonym" in type_name
            common = "common name" in type_name
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
                # Creating TAXONOMY_BY_NAME
                if homonym:
                    self.TBN[homonym] = {}
                    self.TBN[homonym]["id"] = id
                    self.TBN[homonym]["homonym"] = name
                else:
                    self.TBN[name] = {}
                    self.TBN[name]["id"] = id
        if verbose:
            print "Adding synonyms, homonyms and common names..."
        # Adding synonyms, homonyms and common names
        for line in file( self.NAMES ).readlines():
            type_name = line.split("|")[3].strip()
            synonym = "synonym" in type_name
            common = "common name" in type_name
            homonym = line.split("|")[2].strip().lower()
            id = line.split("|")[0].strip()
            if synonym or common:
                name = line.split("|")[1].strip().lower()
                base_name = self.TBI[id]["name"]
                if synonym:
                    if not self.TBN[base_name].has_key( "synonym" ):
                        self.TBN[base_name]["synonym"] = []
                    if not self.TBI[id].has_key( "synonym" ):
                        self.TBI[id]["synonym"] = []
                    self.TBN[base_name]["synonym"].append( name )
                    self.TBI[id]["synonym"].append( name )
                if common:
                    if not self.TBN[base_name].has_key( "common" ):
                        self.TBN[base_name]["common"] = []
                    if not self.TBI[id].has_key( "common" ):
                        self.TBI[id]["common"] = []
                    self.TBN[base_name]["common"].append( name )
                    self.TBI[id]["common"].append( name )
            if type_name == "scientific name" and homonym:
                name = line.split("|")[1].strip().lower()
                self.TBI[id]["homonym"].append( name )
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
        #
        # Test TBI
        #
        if self.TEST:
            TBT = {}
            TAXOTEST = open( 'taxonomy_test.csv' ).readlines()
            for line in TAXOTEST:
                taxa_id, taxa_name, parent_name, homonym_name, parents_list, synonym_list, common_list = line.split( '|' )
                TBT[taxa_id] = self.TBI[taxa_id]
                for parent_id in self.TBI[taxa_id]['parents']:
                    TBT[parent_id] = self.TBI[parent_id]
            self.TBI = TBT

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

    def make_taxa( self ):
        global DUMP_PATH
        # Taxa.dmp
        list_line = []
        for species in self.TBI.keys():
            line = '%s|%s|%s|%s' % (
              species,
              self.TBI[species]['name'],
              self.RANK[self.TBI[species]['rank']],
              self.TBI[species]['parent']
            )
            list_line.append( line )
        open( os.path.join( DUMP_PATH, 'taxa.dmp' ), 'w' ).write( '\n'.join( list_line ) )

    def make_taxonomy( self, name, name_file, relation_file ):
        global DUMP_PATH
        # synonymname.dmp
        synonym_index = {}
        list_synonymname = []
        index = 0
        for species in self.TBI.keys():
            for synonym in self.TBI[species][name]:
                index += 1
                if synonym not in synonym_index:
                    synonym_index[synonym] = index
                    if name == 'common':
                        line = '%s|%s|english' % ( index, synonym.strip("'") )
                    else:
                        line = '%s|%s' % ( index, synonym.strip("'") )
                    list_synonymname.append( line )
        open( os.path.join( DUMP_PATH, name_file ), 'w' ).write( '\n'.join( list_synonymname ) )
        # synonym.dmp
        list_synonym = []
        already_done = []
        index = 0
        for species in self.TBI.keys():
            for synonym in self.TBI[species][name]:
                if name == 'common':
                    if (synonym_index[synonym], species) in already_done:
                        continue
                index += 1
                line = '%s|%s|%s' % ( index, synonym_index[synonym], species )
                list_synonym.append( line )
                if name == 'common':
                    already_done.append( (synonym_index[synonym], species ) )
        open( os.path.join( DUMP_PATH, relation_file ), 'w' ).write( '\n'.join( list_synonym ) )

    def make_parents( self ):
        global DUMP_PATH
        id_rel = 0
        list_parents = []
        for species in self.TBI.keys():
            index = 0
            for parent_id in self.TBI[species]["parents"]:
                id_rel += 1
                line = '%s|%s|%s|%s' % ( id_rel,species, parent_id, index ) 
                list_parents.append( line )
                index += 1
        open( os.path.join( DUMP_PATH, 'parentsrelation.dmp' ), 'w' ).write( '\n'.join( list_parents ) )
                    
    def generate_homonyms( self, file, index):
        global DUMP_PATH
        homonyms = open( os.path.join( DUMP_PATH, 'homonymname.dmp') ).readlines()
        my_set = set()
        for homonym in homonyms:
            homonym_name = homonym.split('|')[1].strip()
            if not homonym_name in my_set:
                index += 1
                file.write( '%s|%s|%s\n' % ( index, homonym_name,  'homonym' ) )
                my_set.add( homonym_name )
        return index

    def generate_synonyms( self, file, index):
        global DUMP_PATH
        synonyms = open( os.path.join( DUMP_PATH, 'synonymname.dmp') ).readlines()
        my_set = set()
        for synonym in synonyms:
            synonym_name = synonym.split('|')[1].strip()
            if not synonym_name in my_set:
                index += 1
                file.write( '%s|%s|%s\n' % ( index, synonym_name, 'synonym' ) )
                my_set.add( synonym_name )
        return index

    def generate_commons( self, file, index ):
        global DUMP_PATH
        commons = open(os.path.join( DUMP_PATH,  'commonname.dmp') ).readlines()
        my_set = set()
        for common in commons:
            common_name = common.split('|')[1].strip()
            if not common_name in my_set:
                index += 1
                file.write( '%s|%s|%s\n' % ( index, common_name, 'common' ) )
                my_set.add( common_name )
        return index

    def generate_scientific( self, file, index ):
        global DUMP_PATH
        taxas = open( os.path.join( DUMP_PATH, 'taxa.dmp' )).readlines()
        for taxa in taxas:
            index += 1
            file.write( '%s|%s|%s\n' % ( index, taxa.split('|')[1].strip(), 'scientific name' ) )
        return index


