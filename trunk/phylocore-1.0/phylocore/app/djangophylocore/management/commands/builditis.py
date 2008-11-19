from django.core.management.base import NoArgsCommand
from optparse import make_option

import os
import sys, csv
from django.conf import settings

localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)
DUMP_PATH = os.path.join( absDir,'..','..', 'dumps' ) 
REL_ID = 0

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--verbose', '-v', action='store_true', dest='verbose', 
            help='Verbose operation'),
    )
    help = "Download and build the ncbi database"
    requires_model_validation = False

    def handle_noargs(self, **options):
        global DUMP_PATH
        verbose = options.get("verbose", False)
        if verbose:
            print "loading taxonomy, please wait, it can take a while..."
        if not os.path.exists( DUMP_PATH ):
            os.system( 'mkdir %s' % DUMP_PATH )
        else:
            os.system( 'rm %s/*' % DUMP_PATH )
        path = '/home/namlook/Bureau/ITIS_VR/itis/itis/itis_fic_utils'
        synonym_file_path = os.path.join( path, 'synonym_links' )
        taxonomic_units_path  = os.path.join( path, 'taxonomic_units' )
        taxon_unit_types_path  = os.path.join( path, 'taxon_unit_types' )
        vernaculars_path  = os.path.join( path, 'vernaculars' )
        kingdoms_path  = os.path.join( path, 'kingdoms' )
        # building
        # kingdoms
        d_kingdom = self.getKingdom( kingdoms_path )
        # synonyms
        syn_tax = self.getSynonym( synonym_file_path )
        #return correct_tax, tax_name, tax_id
        #correct_tax = tax_name = tax_id = getCorrectTaxa("/Users/vranwez/Desktop/ITIS/itis_fic_utils/taxonomic_units")
        taxa_sons={}
        correct_taxa, max_id = self.getCorrectTaxa(taxonomic_units_path, taxa_sons, syn_tax)
        ## recuperation des taxa valid ayant un pere valid 
        reachable_taxa={}
        taxa_homo={}
        #202420
        self.compute_reachable_taxa(correct_taxa, taxa_sons, "0", reachable_taxa, taxa_homo)
        ancestor_file = open( os.path.join( DUMP_PATH, 'parentsrelation.dmp' ), 'a')
        self.compute_write_ancestor( taxa_sons,"0",[],ancestor_file)
        ancestor_file.close()
        ## recuperation des homonyms
        homonyms = {}
        for tax_name, tax_id in taxa_homo.items():
            if len( tax_id ) > 1:
#                print tax_name + " : "
                for id in tax_id:
                    if not tax_name in homonyms:
                        homonyms[tax_name] = []
#                    print "\t"+id
                    homonyms[tax_name].append( id )
        # getting rank
        rank = self.getRank( taxon_unit_types_path )
        # getting common names
        common_name = self.getCommonName( vernaculars_path )
        #for tax_id, tax_info in correct_tax_tree.items():
        #    parent_id = tax_info["parent_id"]
        #    print tax_id + " "+parent_id 
        self.generating_dumps( max_id, reachable_taxa, rank, common_name,
          homonyms, syn_tax, taxa_sons, d_kingdom, correct_taxa, taxa_sons )
        os.system( 'iconv -f iso8859-15 -t utf-8 %s > %s' % (os.path.join(
          DUMP_PATH, 'taxonomy.dmp' ), os.path.join( DUMP_PATH, 'taxonomy.dmp_utf-8' )))
        os.system( 'mv %s %s' % ( os.path.join( DUMP_PATH,
          'taxonomy.dmp_utf-8' ), os.path.join( DUMP_PATH, 'taxonomy.dmp' ) ))

    def generating_dumps( self, max_id, taxonomy, rank, common_name, homonyms,
      synonyms, ancestors, d_kingdom, correct_taxa, taxa_sons ):
        # rank
        open( os.path.join( DUMP_PATH, 'rank.dmp' ), 'w' ).write( '\n'.join( ['|'.join( i ) for i in rank.items()] )+'\n')
        # scientifics
        result = []
        TAXONOMY_TOC = set([])
        for taxa_id in taxonomy:
            if taxonomy[taxa_id]['name'] in homonyms:
                if taxonomy[taxa_id]['credibility_rating'] == 'TWG standards met':
                    taxonomy[taxa_id]['name'] = "%s <%s>" % (taxonomy[taxa_id]['name'], d_kingdom[taxonomy[taxa_id]['kingdom']] )
        homonyms = {}
        self.compute_reachable_taxa(correct_taxa, taxa_sons, "0", taxonomy, homonyms)
        for taxa_id in taxonomy:
            if not taxonomy[taxa_id]['name'] in TAXONOMY_TOC:
                result.append( "%s|%s|scientific name|%s|%s\n" % ( taxa_id,
                  taxonomy[taxa_id]['name'], taxonomy[taxa_id]['rank'], taxonomy[taxa_id]['parent_id'] ) )
                TAXONOMY_TOC.add( taxonomy[taxa_id]['name'] )
        open( os.path.join( DUMP_PATH, 'taxonomy.dmp' ), 'w' ).write( ''.join( result ) )
        # homonyms
        result_taxonomy = []
        result_rel = []
        index = 0
        for homonym_name in homonyms:
            assert homonym_name not in TAXONOMY_TOC
            max_id += 1
            result_taxonomy.append( "%s|%s|homonym|300|\n" % ( max_id, homonym_name ) )
            TAXONOMY_TOC.add( homonym_name )
            for taxa_id in homonyms[homonym_name]:
                index += 1
                result_rel.append( "%s|%s|%s\n" % (index, max_id, taxa_id ) )
        open( os.path.join( DUMP_PATH, 'taxonomy.dmp' ), 'a' ).write( ''.join( result_taxonomy ) )
        open( os.path.join( DUMP_PATH, 'relhomonymtaxa.dmp' ), 'w' ).write( ''.join( result_rel ) )
        # common names
        result_taxonomy = []
        result_rel = []
        index = 0
        already_done = set([])
        for name in common_name:
            if name not in TAXONOMY_TOC:
                max_id += 1
                result_taxonomy.append( "%s|%s|common|300|\n" % ( max_id, name ) )
                TAXONOMY_TOC.add( name )
                for common in common_name[name]:
                    index += 1
                    if not (max_id, common['id'] ) in already_done:
                        result_rel.append( "%s|%s|%s|%s\n" % (index, max_id, common['id'], common['langage'] ) )
                        already_done.add( (max_id, common['id']) )
            else:
                print "%s is already in toc" % name
        open( os.path.join( DUMP_PATH, 'taxonomy.dmp' ), 'a' ).write( ''.join( result_taxonomy ) )
        open( os.path.join( DUMP_PATH, 'relcommontaxa.dmp' ), 'w' ).write( ''.join( result_rel ) )
 

    def getCorrectTaxa( self, taxonomic_units_file, taxa_sons, syn_tax ):
        #fichier_csv=open(taxonomic_units_file, "rb")
        #fichier = csv.reader(fichier_csv, delimiter='|')
        fichier = open( taxonomic_units_file ).readlines()
        correct_tax = {}
        #mis en 1ere ligne du fichier
        #correct_tax["0"] = {"name": "root", "parent_id": "0", "rank": ""}
        ## recuperation des taxa valid
        ligne = "0||root||||||||valid||TWG standards met|unknown|unknown||1996-06-13 14:51:08|0|||5|10|10/27/1999|".split('|')
        max_id=0
        correct_tax[ligne[0]] = {"name": ligne[2] , "parent_id": ligne[17],
        "rank": ligne[21], 'kingdom': ligne[20], 'credibility_rating':ligne[12]}
        for ligne in fichier:
            ligne = ligne.lower().split('|')
            tax_id = ligne[0]
            valid = ligne[10]
            tax_name = " ".join( [ligne[2], ligne[4], ligne[6], ligne[8]]).strip()
            tax_parent_id = ligne[17]
            rank = ligne[21]
            kingdom = ligne[20]
            credibility_rating = ligne[12]
            if int(tax_id) > int(max_id):
                    max_id = tax_id
            if valid in ('accepted', 'valid'): # or ligne[11] in ('synonym')):
                tax_parent_id = syn_tax.get(tax_parent_id, tax_parent_id)
                # verification que pas de syno pour les taxa valid
                if tax_id in syn_tax:
                    print "valid with syno " + tax_id
                if tax_parent_id:
                    correct_tax[tax_id] = {"name": tax_name, "parent_id": tax_parent_id,
                      "rank": rank, 'kingdom': kingdom, 'credibility_rating': credibility_rating }
                    if not tax_parent_id in taxa_sons:
                        taxa_sons[tax_parent_id]=[]    
                    taxa_sons[tax_parent_id].append(tax_id)
                    #print "add  %s %s len taxa sons %i" %(tax_parent_id, tax_id, len(taxa_sons))
        #fichier_csv.close()    
        return correct_tax, int(max_id)

    def compute_reachable_taxa( self, correct_taxa, taxa_sons, taxa_id, reachable_taxa, taxa_homo):
        taxa_info = correct_taxa[taxa_id]
        reachable_taxa[taxa_id]=taxa_info
        taxa_name = taxa_info["name"];
        if not taxa_name in taxa_homo:
            taxa_homo[taxa_name]=[]    
        taxa_homo[taxa_name].append(taxa_id)
        if taxa_id in taxa_sons:
            for son_id in taxa_sons[taxa_id]:
                if son_id != taxa_id: # pb de la racine 0
                    self.compute_reachable_taxa(correct_taxa,taxa_sons,son_id,reachable_taxa,taxa_homo)

    def getKingdom( self, kingdom_file ):
        fichier = open( kingdom_file ).readlines()
        kingdom = {}
        for ligne in fichier:
            ligne = ligne.lower().split('|')
            kingdom[ligne[0]] = ligne[1]
        return kingdom

    def getRank( self, rank_file ):
        #fichier_csv=open(rank_file, "rb")
        #fichier = csv.reader(fichier_csv, delimiter='|')
        fichier = open( rank_file ).readlines()
        rank = {}
        for ligne in fichier:
            ligne = ligne.lower().split('|')
            rank[ligne[1]] = ligne[2]
        #fichier_csv.close()
        return rank

    def getCommonName( self, common_name_file):
        #fichier_csv=open(common_name_file, "rb")
        #fichier = csv.reader(fichier_csv, delimiter='|')
        fichier  = open( common_name_file ).readlines()
        common_name = {}
        for ligne in fichier:
            ligne = ligne.lower().split('|')
            if ligne[1] not in common_name:
                common_name[ligne[1]] = []
            common_name[ligne[1]].append( {"id":ligne[0],"langage":ligne[2]} )
        #fichier_csv.close()
        return common_name

    def getSynonym( self, syn_file):
        #fichier_csv=open(syn_file, "rb")
        #fichier = csv.reader(fichier_csv, delimiter='|')
        fichier = open( syn_file ).readlines()
        syn_tax = {}
        for ligne in fichier:
            ligne = ligne.lower().split('|')
            syn_tax[ligne[0]] = ligne[1]
        #fichier_csv.close()
        return syn_tax

    def compute_write_ancestor( self, taxa_sons, taxa_id, ancestor, ancestor_file ):
        global REL_ID
        #print "compute anc"
        index = 0
        for a in ancestor:
            REL_ID += 1
            ancestor_file.write("%s|%s|%s|%s\n" % ( REL_ID, taxa_id, a, index ))
            index += 1
        new_anc = ancestor[:]
        new_anc.insert( 0, taxa_id )
        if taxa_id in taxa_sons:
            for son_id in taxa_sons[taxa_id]:
                if son_id != taxa_id: # pb de la racine 0
                    self.compute_write_ancestor( taxa_sons, son_id, new_anc, ancestor_file )
            
    

