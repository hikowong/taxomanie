#
# TaxonomyReference
#

def test_taxonomy_reference():
    return """

All objects that inerits from TaxonomyReference will have some more methods.
Those methods provide informations from the taxonomy.

>>> from djangophylocore.models import *
>>> taxoref = TaxonomyReference()


Working with names
------------------

>>> taxoref.is_valid_name( 'rattus' )
True
>>> taxoref.is_valid_name( 'rattus other' )
False

>>> taxoref.is_scientific_name( 'rattus' )
True
>>> taxoref.is_scientific_name( 'antilocapra anteflexa' )
False

>>> taxoref.is_common( 'rat' )
True
>>> taxoref.is_common( 'rat noir' )
False

>>> taxoref.is_synonym( 'nannomys' )
True
>>> taxoref.is_synonym( 'rattus' )
False

>>> taxoref.is_homonym( 'echinops' )
True
>>> taxoref.is_homonym( 'echinops <plant>' )
False

>>> taxoref.is_bad_taxa( 'rattus' )
False
>>> taxoref.is_bad_taxa( 'abadname' )
True
>>> abadname = BadTaxa.objects.create( name = 'abadname' )
>>> taxoref.is_bad_taxa( 'abadname' )
True

>>> taxoref.get_name_from_common( 'mouse' )
[<Taxa: mus musculus>]
>>> taxoref.get_name_from_common( 'mus' )
[]

>>> taxoref.get_name_from_synonym( 'nannomys' )
[<Taxa: mus>]
>>> taxoref.get_name_from_synonym( 'mus' )
[]

>>> taxoref.get_name_from_homonym( 'echinops' )
[<Taxa: echinops <mammal>>, <Taxa: echinops <plant>>]
>>> taxoref.get_name_from_homonym( 'homo' )
[]

>>> taxoref.strip_taxa_name( "rattus" )
'rattus'
>>> taxoref.strip_taxa_name( "rattus_france" )
'rattus'
>>> taxoref.strip_taxa_name( "rattus france, delimiter=' '" )
'rattus'
>>> taxoref.strip_taxa_name( "mus_musculus" )
'mus musculus'
>>> taxoref.strip_taxa_name( "mus_musculus_france" )
'mus musculus'

>>> taxoref.strip_taxa_name( "rattus rattus france", delimiter=' ')
'rattus rattus'

'mus something foo' is not in our test database so we're falling down to 'mus'
>>> taxoref.strip_taxa_name( "mus something foo", delimiter=' ')
'mus'

>>> taxoref.correct( 'rattus' ) is None
True
>>> taxoref.correct( 'house mouse' )
[<Taxa: mus musculus>]
>>> taxoref.correct( 'echinops' )
[<Taxa: echinops <mammal>>, <Taxa: echinops <plant>>]
>>> taxoref.correct( 'nannomys' )
[<Taxa: mus>]
>>> taxoref.correct( 'taxa not in database' )
[0]

Getting django objects from name
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
>>> taxoref.get_object_from_name( 'mus' )
<Taxa: mus>
>>> taxoref.get_object_from_name( 'nannomys' )
<SynonymName: nannomys>
>>> taxoref.get_object_from_name( 'echinops' )
<HomonymName: echinops>
>>> taxoref.get_object_from_name( 'badname' )
<BadTaxa: badname (1)>

The name must be present into the database

>>> try:
...     taxoref.get_object_from_name( 'very badname' )
... except ValueError, e:
...     e
ValueError('very badname not found in the database',)

Working with taxa
-----------------

>>> root = Taxa.objects.get( name = 'root' )
>>> muridae = Taxa.objects.get( name = 'muridae' )
>>> mus = Taxa.objects.get( name = 'mus' )
>>> mus_musculus = Taxa.objects.get( name = 'mus musculus' )
>>> rattus = Taxa.objects.get( name = 'rattus' )
>>> echinops_plantae = Taxa.objects.get( name = 'echinops <plant>' )
>>> mammalia = Taxa.objects.get( name = 'mammalia' )

Getting interval parents
~~~~~~~~~~~~~~~~~~~~~~~~

>>> try:
...    taxoref.get_interval_parents( mus, rattus )
... except AssertionError,e:
...    str(e)
'mus is not a parent of rattus'
>>> try:
...     taxoref.get_interval_parents( mus_musculus, muridae )
... except AssertionError,e:
...     str(e)
'mus musculus is not a parent of muridae'
>>> taxoref.get_interval_parents( muridae, mus_musculus )
[<Taxa: mus>, <Taxa: murinae>]
>>> taxoref.get_interval_parents( mammalia, mus_musculus )
[<Taxa: mus>, <Taxa: murinae>, <Taxa: muridae>, <Taxa: muroidea>, <Taxa: sciurognathi>, <Taxa: rodentia>, <Taxa: glires>, <Taxa: euarchontoglires>, <Taxa: eutheria>, <Taxa: theria>]


Getting common parents
~~~~~~~~~~~~~~~~~~~~~~

>>> taxoref.get_common_parents( [root] )
[]
>>> taxoref.get_common_parents( [muridae] )
[<Taxa: muroidea>, <Taxa: sciurognathi>, <Taxa: rodentia>, <Taxa: glires>, <Taxa: euarchontoglires>, <Taxa: eutheria>, <Taxa: theria>, <Taxa: mammalia>, <Taxa: amniota>, <Taxa: tetrapoda>, <Taxa: sarcopterygii>, <Taxa: euteleostomi>, <Taxa: teleostomi>, <Taxa: gnathostomata <vertebrate>>, <Taxa: vertebrata>, <Taxa: craniata <chordata>>, <Taxa: chordata>, <Taxa: deuterostomia>, <Taxa: coelomata>, <Taxa: bilateria>, <Taxa: eumetazoa>, <Taxa: metazoa>, <Taxa: fungi/metazoa group>, <Taxa: eukaryota>, <Taxa: cellular organisms>, <Taxa: root>]
>>> taxoref.get_common_parents( [muridae, mus] )
[<Taxa: muroidea>, <Taxa: sciurognathi>, <Taxa: rodentia>, <Taxa: glires>, <Taxa: euarchontoglires>, <Taxa: eutheria>, <Taxa: theria>, <Taxa: mammalia>, <Taxa: amniota>, <Taxa: tetrapoda>, <Taxa: sarcopterygii>, <Taxa: euteleostomi>, <Taxa: teleostomi>, <Taxa: gnathostomata <vertebrate>>, <Taxa: vertebrata>, <Taxa: craniata <chordata>>, <Taxa: chordata>, <Taxa: deuterostomia>, <Taxa: coelomata>, <Taxa: bilateria>, <Taxa: eumetazoa>, <Taxa: metazoa>, <Taxa: fungi/metazoa group>, <Taxa: eukaryota>, <Taxa: cellular organisms>, <Taxa: root>]
>>> taxoref.get_common_parents( [mus, mus_musculus] )
[<Taxa: murinae>, <Taxa: muridae>, <Taxa: muroidea>, <Taxa: sciurognathi>, <Taxa: rodentia>, <Taxa: glires>, <Taxa: euarchontoglires>, <Taxa: eutheria>, <Taxa: theria>, <Taxa: mammalia>, <Taxa: amniota>, <Taxa: tetrapoda>, <Taxa: sarcopterygii>, <Taxa: euteleostomi>, <Taxa: teleostomi>, <Taxa: gnathostomata <vertebrate>>, <Taxa: vertebrata>, <Taxa: craniata <chordata>>, <Taxa: chordata>, <Taxa: deuterostomia>, <Taxa: coelomata>, <Taxa: bilateria>, <Taxa: eumetazoa>, <Taxa: metazoa>, <Taxa: fungi/metazoa group>, <Taxa: eukaryota>, <Taxa: cellular organisms>, <Taxa: root>]
>>> taxoref.get_common_parents( [mus_musculus, mus] )
[<Taxa: murinae>, <Taxa: muridae>, <Taxa: muroidea>, <Taxa: sciurognathi>, <Taxa: rodentia>, <Taxa: glires>, <Taxa: euarchontoglires>, <Taxa: eutheria>, <Taxa: theria>, <Taxa: mammalia>, <Taxa: amniota>, <Taxa: tetrapoda>, <Taxa: sarcopterygii>, <Taxa: euteleostomi>, <Taxa: teleostomi>, <Taxa: gnathostomata <vertebrate>>, <Taxa: vertebrata>, <Taxa: craniata <chordata>>, <Taxa: chordata>, <Taxa: deuterostomia>, <Taxa: coelomata>, <Taxa: bilateria>, <Taxa: eumetazoa>, <Taxa: metazoa>, <Taxa: fungi/metazoa group>, <Taxa: eukaryota>, <Taxa: cellular organisms>, <Taxa: root>]

Getting the first common parent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

>>> taxoref.get_first_common_parent( [mus] )
<Taxa: murinae>
>>> taxoref.get_first_common_parent( [mus, rattus] )
<Taxa: murinae>
>>> taxoref.get_first_common_parent( [rattus, mus] )
<Taxa: murinae>
>>> taxoref.get_first_common_parent( [mus, rattus, muridae] )
<Taxa: muroidea>
>>> taxoref.get_first_common_parent( [mus, muridae] )
<Taxa: muroidea>

Root has no parents
>>> taxoref.get_first_common_parent( [root] ) is None
True
>>> taxoref.get_first_common_parent( [root, mus] ) is None
True

Working with networkx.DiGraph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

>>> graph = taxoref.get_reference_arborescence( [mus, rattus, echinops_plantae] )
>>> graph.nodes()
[<Taxa: root>, <Taxa: fungi/metazoa group>, <Taxa: eutheria>, <Taxa: rodentia>, <Taxa: tetrapoda>, <Taxa: amniota>, <Taxa: theria>, <Taxa: sciurognathi>, <Taxa: euteleostomi>, <Taxa: streptophytina>, <Taxa: muroidea>, <Taxa: chordata>, <Taxa: euarchontoglires>, <Taxa: glires>, <Taxa: coelomata>, <Taxa: streptophyta>, <Taxa: tracheophyta>, <Taxa: spermatophyta>, <Taxa: echinops <plant>>, <Taxa: euphyllophyta>, <Taxa: core eudicotyledons>, <Taxa: eumetazoa>, <Taxa: carduoideae>, <Taxa: bilateria>, <Taxa: vertebrata>, <Taxa: teleostomi>, <Taxa: murinae>, <Taxa: magnoliophyta>, <Taxa: eukaryota>, <Taxa: eudicotyledons>, <Taxa: viridiplantae>, <Taxa: cardueae>, <Taxa: metazoa>, <Taxa: muridae>, <Taxa: embryophyta>, <Taxa: sarcopterygii>, <Taxa: gnathostomata <vertebrate>>, <Taxa: mammalia>, <Taxa: deuterostomia>, <Taxa: mus>, <Taxa: campanulids>, <Taxa: cellular organisms>, <Taxa: asterales>, <Taxa: asteraceae>, <Taxa: craniata <chordata>>, <Taxa: asterids>, <Taxa: rattus>]
>>> graph.edges()
[(<Taxa: root>, <Taxa: cellular organisms>), (<Taxa: fungi/metazoa group>, <Taxa: metazoa>), (<Taxa: eutheria>, <Taxa: euarchontoglires>), (<Taxa: rodentia>, <Taxa: sciurognathi>), (<Taxa: tetrapoda>, <Taxa: amniota>), (<Taxa: amniota>, <Taxa: mammalia>), (<Taxa: theria>, <Taxa: eutheria>), (<Taxa: sciurognathi>, <Taxa: muroidea>), (<Taxa: euteleostomi>, <Taxa: sarcopterygii>), (<Taxa: streptophytina>, <Taxa: embryophyta>), (<Taxa: muroidea>, <Taxa: muridae>), (<Taxa: chordata>, <Taxa: craniata <chordata>>), (<Taxa: euarchontoglires>, <Taxa: glires>), (<Taxa: glires>, <Taxa: rodentia>), (<Taxa: coelomata>, <Taxa: deuterostomia>), (<Taxa: streptophyta>, <Taxa: streptophytina>), (<Taxa: tracheophyta>, <Taxa: euphyllophyta>), (<Taxa: spermatophyta>, <Taxa: magnoliophyta>), (<Taxa: euphyllophyta>, <Taxa: spermatophyta>), (<Taxa: core eudicotyledons>, <Taxa: asterids>), (<Taxa: eumetazoa>, <Taxa: bilateria>), (<Taxa: carduoideae>, <Taxa: cardueae>), (<Taxa: bilateria>, <Taxa: coelomata>), (<Taxa: vertebrata>, <Taxa: gnathostomata <vertebrate>>), (<Taxa: teleostomi>, <Taxa: euteleostomi>), (<Taxa: murinae>, <Taxa: mus>), (<Taxa: murinae>, <Taxa: rattus>), (<Taxa: magnoliophyta>, <Taxa: eudicotyledons>), (<Taxa: eukaryota>, <Taxa: fungi/metazoa group>), (<Taxa: eukaryota>, <Taxa: viridiplantae>), (<Taxa: eudicotyledons>, <Taxa: core eudicotyledons>), (<Taxa: viridiplantae>, <Taxa: streptophyta>), (<Taxa: cardueae>, <Taxa: echinops <plant>>), (<Taxa: metazoa>, <Taxa: eumetazoa>), (<Taxa: muridae>, <Taxa: murinae>), (<Taxa: embryophyta>, <Taxa: tracheophyta>), (<Taxa: sarcopterygii>, <Taxa: tetrapoda>), (<Taxa: gnathostomata <vertebrate>>, <Taxa: teleostomi>), (<Taxa: mammalia>, <Taxa: theria>), (<Taxa: deuterostomia>, <Taxa: chordata>), (<Taxa: campanulids>, <Taxa: asterales>), (<Taxa: cellular organisms>, <Taxa: eukaryota>), (<Taxa: asterales>, <Taxa: asteraceae>), (<Taxa: asteraceae>, <Taxa: carduoideae>), (<Taxa: craniata <chordata>>, <Taxa: vertebrata>), (<Taxa: asterids>, <Taxa: campanulids>)]

>>> graph = taxoref.get_reference_arborescence( [mus, rattus, muridae] )
>>> graph.nodes()
[<Taxa: root>, <Taxa: fungi/metazoa group>, <Taxa: eutheria>, <Taxa: rodentia>, <Taxa: tetrapoda>, <Taxa: amniota>, <Taxa: theria>, <Taxa: sciurognathi>, <Taxa: euteleostomi>, <Taxa: muroidea>, <Taxa: chordata>, <Taxa: euarchontoglires>, <Taxa: glires>, <Taxa: coelomata>, <Taxa: eumetazoa>, <Taxa: bilateria>, <Taxa: vertebrata>, <Taxa: teleostomi>, <Taxa: murinae>, <Taxa: eukaryota>, <Taxa: metazoa>, <Taxa: muridae>, <Taxa: sarcopterygii>, <Taxa: gnathostomata <vertebrate>>, <Taxa: mammalia>, <Taxa: deuterostomia>, <Taxa: mus>, <Taxa: cellular organisms>, <Taxa: craniata <chordata>>, <Taxa: rattus>]
>>> graph.edges()
[(<Taxa: root>, <Taxa: cellular organisms>), (<Taxa: fungi/metazoa group>, <Taxa: metazoa>), (<Taxa: eutheria>, <Taxa: euarchontoglires>), (<Taxa: rodentia>, <Taxa: sciurognathi>), (<Taxa: tetrapoda>, <Taxa: amniota>), (<Taxa: amniota>, <Taxa: mammalia>), (<Taxa: theria>, <Taxa: eutheria>), (<Taxa: sciurognathi>, <Taxa: muroidea>), (<Taxa: euteleostomi>, <Taxa: sarcopterygii>), (<Taxa: muroidea>, <Taxa: muridae>), (<Taxa: chordata>, <Taxa: craniata <chordata>>), (<Taxa: euarchontoglires>, <Taxa: glires>), (<Taxa: glires>, <Taxa: rodentia>), (<Taxa: coelomata>, <Taxa: deuterostomia>), (<Taxa: eumetazoa>, <Taxa: bilateria>), (<Taxa: bilateria>, <Taxa: coelomata>), (<Taxa: vertebrata>, <Taxa: gnathostomata <vertebrate>>), (<Taxa: teleostomi>, <Taxa: euteleostomi>), (<Taxa: murinae>, <Taxa: mus>), (<Taxa: murinae>, <Taxa: rattus>), (<Taxa: eukaryota>, <Taxa: fungi/metazoa group>), (<Taxa: metazoa>, <Taxa: eumetazoa>), (<Taxa: muridae>, <Taxa: murinae>), (<Taxa: sarcopterygii>, <Taxa: tetrapoda>), (<Taxa: gnathostomata <vertebrate>>, <Taxa: teleostomi>), (<Taxa: mammalia>, <Taxa: theria>), (<Taxa: deuterostomia>, <Taxa: chordata>), (<Taxa: cellular organisms>, <Taxa: eukaryota>), (<Taxa: craniata <chordata>>, <Taxa: vertebrata>)]

"""
