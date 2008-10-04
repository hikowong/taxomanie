#
# Taxa
#

def test_taxa():
    return """
>>> from djangophylocore.models import *

>>> taxa = Taxa.objects.get( name = 'echinops <plant>' )
>>> taxa.homonyms.all()
[<HomonymName: echinops>]
>>> taxa.rank
<Rank: genus>

>>> taxa = Taxa.objects.get( name = 'mus' )
>>> taxa.synonyms.all()
[<SynonymName: nannomys>]

>>> taxa = Taxa.objects.get( name = 'mus musculus' )
>>> taxa
<Taxa: mus musculus>
>>> taxa.homonyms.all()
[]
>>> taxa.synonyms.all()
[]
>>> taxa.commons.all()
[<CommonName: house mouse (english)>, <CommonName: mouse (english)>]
>>> taxa.rank
<Rank: species>

Dealing with parents
~~~~~~~~~~~~~~~~~~~~

Get the first parent

>>> taxa.parent
<Taxa: mus>

Parent can be chained

>>> taxa.parent.parent
<Taxa: murinae>

Get all parents by order (closest to furthest). 'parents' attribute is a
simple liste containing Taxa

>>> taxa.parents
[<Taxa: mus>, <Taxa: murinae>, <Taxa: muridae>, <Taxa: muroidea>, <Taxa: sciurognathi>, <Taxa: rodentia>, <Taxa: glires>, <Taxa: euarchontoglires>, <Taxa: eutheria>, <Taxa: theria>, <Taxa: mammalia>, <Taxa: amniota>, <Taxa: tetrapoda>, <Taxa: sarcopterygii>, <Taxa: euteleostomi>, <Taxa: teleostomi>, <Taxa: gnathostomata <vertebrate>>, <Taxa: vertebrata>, <Taxa: craniata <chordata>>, <Taxa: chordata>, <Taxa: deuterostomia>, <Taxa: coelomata>, <Taxa: bilateria>, <Taxa: eumetazoa>, <Taxa: metazoa>, <Taxa: fungi/metazoa group>, <Taxa: eukaryota>, <Taxa: cellular organisms>, <Taxa: root>]
>>> list( reversed( taxa.parents ) )
[<Taxa: root>, <Taxa: cellular organisms>, <Taxa: eukaryota>, <Taxa: fungi/metazoa group>, <Taxa: metazoa>, <Taxa: eumetazoa>, <Taxa: bilateria>, <Taxa: coelomata>, <Taxa: deuterostomia>, <Taxa: chordata>, <Taxa: craniata <chordata>>, <Taxa: vertebrata>, <Taxa: gnathostomata <vertebrate>>, <Taxa: teleostomi>, <Taxa: euteleostomi>, <Taxa: sarcopterygii>, <Taxa: tetrapoda>, <Taxa: amniota>, <Taxa: mammalia>, <Taxa: theria>, <Taxa: eutheria>, <Taxa: euarchontoglires>, <Taxa: glires>, <Taxa: rodentia>, <Taxa: sciurognathi>, <Taxa: muroidea>, <Taxa: muridae>, <Taxa: murinae>, <Taxa: mus>]

'root' doesn't have parents

>>> root = Taxa.objects.get( name = 'root' )
>>> root.parents
[]

# get info from sources
#>>> taxa.get_id_in_source( 'ncbi' )
#u'2334'

Dealing with rank
-----------------

>>> species = Rank.objects.get( name = 'species' )
>>> species.taxas.all()
[<Taxa: antilocapra americana>, <Taxa: avenella flexuosa>, <Taxa: echinops ritro>, <Taxa: echinops telfairi>, <Taxa: monarcha axillaris>, <Taxa: mus musculus>, <Taxa: rattus rattus>]

>>> genus = Rank.objects.get( name = 'genus' )
>>> genus.taxas.all()
[<Taxa: antilocapra>, <Taxa: avenella>, <Taxa: echinops <mammal>>, <Taxa: echinops <plant>>, <Taxa: monarcha <aves>>, <Taxa: mus>, <Taxa: rattus>]

"""

