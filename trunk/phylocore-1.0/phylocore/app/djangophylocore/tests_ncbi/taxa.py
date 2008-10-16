#
# Taxonomy
#

def test_taxa():
    return """
>>> from djangophylocore.models import *

>>> taxa = Taxonomy.objects.get( name = 'echinops <plant>' )
>>> taxa.homonyms.all()
[<Taxonomy: echinops (homonym)>]
>>> taxa.rank
<Rank: genus>

>>> taxa = Taxonomy.objects.get( name = 'echinops' )
>>> taxa.scientifics.all()
[<Taxonomy: echinops <mammal> (scientific name)>, <Taxonomy: echinops <plant> (scientific name)>]


>>> taxa = Taxonomy.objects.get( name = 'mus' )
>>> taxa.children.all()
[<Taxonomy: mus musculus (scientific name)>]
>>> taxa.synonyms.all()
[<Taxonomy: nannomys (synonym)>]

>>> taxa = Taxonomy.objects.get( name = 'mus musculus' )
>>> taxa
<Taxonomy: mus musculus (scientific name)>
>>> taxa.homonyms.all()
[]
>>> taxa.synonyms.all()
[]
>>> taxa.commons.all()
[<Taxonomy: house mouse (common)>, <Taxonomy: mouse (common)>]
>>> taxa.rank
<Rank: species>

Dealing with parents
~~~~~~~~~~~~~~~~~~~~

Get the first parent

>>> taxa.parent
<Taxonomy: mus (scientific name)>

Parent can be chained

>>> taxa.parent.parent
<Taxonomy: murinae (scientific name)>

Get all parents by order (closest to furthest). 'parents' attribute is a
simple liste containing taxa

>>> taxa.parents
[<Taxonomy: mus (scientific name)>, <Taxonomy: murinae (scientific name)>, <Taxonomy: muridae (scientific name)>, <Taxonomy: muroidea (scientific name)>, <Taxonomy: sciurognathi (scientific name)>, <Taxonomy: rodentia (scientific name)>, <Taxonomy: glires (scientific name)>, <Taxonomy: euarchontoglires (scientific name)>, <Taxonomy: eutheria (scientific name)>, <Taxonomy: theria (scientific name)>, <Taxonomy: mammalia (scientific name)>, <Taxonomy: amniota (scientific name)>, <Taxonomy: tetrapoda (scientific name)>, <Taxonomy: sarcopterygii (scientific name)>, <Taxonomy: euteleostomi (scientific name)>, <Taxonomy: teleostomi (scientific name)>, <Taxonomy: gnathostomata <vertebrate> (scientific name)>, <Taxonomy: vertebrata (scientific name)>, <Taxonomy: craniata <chordata> (scientific name)>, <Taxonomy: chordata (scientific name)>, <Taxonomy: deuterostomia (scientific name)>, <Taxonomy: coelomata (scientific name)>, <Taxonomy: bilateria (scientific name)>, <Taxonomy: eumetazoa (scientific name)>, <Taxonomy: metazoa (scientific name)>, <Taxonomy: fungi/metazoa group (scientific name)>, <Taxonomy: eukaryota (scientific name)>, <Taxonomy: cellular organisms (scientific name)>, <Taxonomy: root (scientific name)>]

>>> list( reversed( taxa.parents ) )
[<Taxonomy: root (scientific name)>, <Taxonomy: cellular organisms (scientific name)>, <Taxonomy: eukaryota (scientific name)>, <Taxonomy: fungi/metazoa group (scientific name)>, <Taxonomy: metazoa (scientific name)>, <Taxonomy: eumetazoa (scientific name)>, <Taxonomy: bilateria (scientific name)>, <Taxonomy: coelomata (scientific name)>, <Taxonomy: deuterostomia (scientific name)>, <Taxonomy: chordata (scientific name)>, <Taxonomy: craniata <chordata> (scientific name)>, <Taxonomy: vertebrata (scientific name)>, <Taxonomy: gnathostomata <vertebrate> (scientific name)>, <Taxonomy: teleostomi (scientific name)>, <Taxonomy: euteleostomi (scientific name)>, <Taxonomy: sarcopterygii (scientific name)>, <Taxonomy: tetrapoda (scientific name)>, <Taxonomy: amniota (scientific name)>, <Taxonomy: mammalia (scientific name)>, <Taxonomy: theria (scientific name)>, <Taxonomy: eutheria (scientific name)>, <Taxonomy: euarchontoglires (scientific name)>, <Taxonomy: glires (scientific name)>, <Taxonomy: rodentia (scientific name)>, <Taxonomy: sciurognathi (scientific name)>, <Taxonomy: muroidea (scientific name)>, <Taxonomy: muridae (scientific name)>, <Taxonomy: murinae (scientific name)>, <Taxonomy: mus (scientific name)>]


'root' doesn't have parents

>>> root = Taxonomy.objects.get( name = 'root' )
>>> root.parents
[]

# get info from sources
#>>> taxa.get_id_in_source( 'ncbi' )
#u'2334'

Dealing with rank
-----------------

>>> species = Rank.objects.get( name = 'species' )
>>> species.taxas.all()
[<Taxonomy: antilocapra americana (scientific name)>, <Taxonomy: avenella flexuosa (scientific name)>, <Taxonomy: echinops ritro (scientific name)>, <Taxonomy: echinops telfairi (scientific name)>, <Taxonomy: monarcha axillaris (scientific name)>, <Taxonomy: mus musculus (scientific name)>, <Taxonomy: rattus rattus (scientific name)>]

>>> genus = Rank.objects.get( name = 'genus' )
>>> genus.taxas.all()
[<Taxonomy: antilocapra (scientific name)>, <Taxonomy: avenella (scientific name)>, <Taxonomy: echinops <mammal> (scientific name)>, <Taxonomy: echinops <plant> (scientific name)>, <Taxonomy: monarcha <aves> (scientific name)>, <Taxonomy: mus (scientific name)>, <Taxonomy: rattus (scientific name)>]


"""

