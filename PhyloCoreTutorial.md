# Introduction #

There is two version of phylocore : phylocore\_ncbi and phylocore\_itis. You can use both at the same time :

```
>>> import phylocore_ncbi as ncbi
>>> import phylocore_itis as itis

>>> nb_ncbi_species = ncbi.Taxonomy.objects.all().count()
>>> nb_itis_species = itis.Taxonomy.objects.all().count()

>>> nb_ncbi_species == nb_itis_species
False
```

If you want to work with only one taxonomy, you can import all objects at the same time:

```
>>> from phylocore_ncbi import *
```

# Working with Taxa #

To get a taxa from his name do:

```
>>> taxa = Taxonomy.objects.get( name = 'mus musculus' )
>>> taxa
<Taxa: mus musculus>
```

from this taxa, you will be able to get all the homonym, synonym and common names:

```
>>> taxa.homonyms.all()
[]
>>> taxa.synonyms.all()
[]
>>> taxa.commons.all()
[<CommonName: mouse (english)>, <CommonName: rat noir (french)>]
```

## Dealing with parents ##

Getting the first parent:

```
>>> taxa.parent
<Taxa: mus>
```

Parents can be chained:

```
>>> taxa.parent.parent
<Taxa: murinae>
```

Get all parents by order (closest to furthest).

```
>>> taxa.parents.all()
[<Taxa: mus>, <Taxa: murinae>, <Taxa: eukaryota>, <Taxa: root>]
>>> list( reversed( taxa.parents.all() ) )
[<Taxa: root>, <Taxa: eukaryota>, <Taxa: murinae>, <Taxa: mus>]
```

'root' doesn't have parents

```
>>> root = Taxonomy.objects.get( name = 'root' )
>>> root.parents
[]
```

## Dealing with rank ##

You can know the rank of a taxa.

```
>>> taxa.rank
<Rank: species>
```

and you can get all taxa from a specify rank

```
>>> species = Rank.objects.get( name = 'species' )
>>> species.taxa.all()
[<Taxa: echinops <plant>>, <Taxa: echinops <mammal>>, <Taxa: mus musculus>]

>>> genus = Rank.objects.get( name = 'genus' )
>>> genus.taxa.all()
[<Taxa: rattus>, <Taxa: mus>]
```

# Working with tree #

Now we know about taxa, we can create trees. A Tree object is created by passing a newick format string. In the following example, we create a newick tree with one homonym (echinops), 3 scientific names, and one bad taxa name

```
>>> nwk_tree = "(echinops,(rattus,(mus,(mus musculus),badname)))"
```

Now we can create our tree:

```
>>> tree = Tree.objects.create( source = nwk_tree, name = "example1")
```

The `is_valid` attribute tell us if our tree was well formated or not

```
>>> tree.is_valid
True
```

Now we want all (good named) taxa list:

```
>>> tree.taxa.all()
[<Taxa: rattus>, <Taxa: mus>, <Taxa: mus musculus>]
```

We can get informations from bad taxa names and homonyms:

```
>>> tree.bad_taxa.all()
[<BadTaxa: badname>]
>>> tree.homonyms.all()
[<HomonymName: echinops>]
```

There is no synonyms or commons names:

```
>>> tree.synonyms.count()
0L
>>> tree.commons.count()
0L
```

Let's try now to get all taxa wich correspond to echinops :

```
>>> homonym = tree.homonyms.all()[0]
>>> homonym.taxa.all()
[<Taxa: echinops <animalia>], [Taxa: echinops <plantae>]
```

we can retrieve all ambiguous name easily:

```
>>> tree.ambiguous.all()
[<Taxonomy: echinops (homonym)>]
```

# Working with TreeCollection #

## Creation of a simple collection ##

A TreeCollection can take a collection in a nexus or phylip format

```
>>> simple_col = "(mus,antilocapra anteflexa,rat noir,echinops,blabla);(mus, (rat noir);"
>>> col = TreeCollection.objects.create( name = 'simple', source = simple_col )
```

Juste like Tree objects, we have access to all taxa:

```
>>> col.taxonomy_objects.all()
[<Taxonomy: antilocapra anteflexa (synonym)>, <Taxonomy: echinops (homonym)>, <Taxonomy: mus (scientific name)>, <Taxonomy: rat noir (common)>]
>>> col.ambiguous.all()
[<Taxonomy: antilocapra anteflexa (synonym)>, <Taxonomy: echinops (homonym)>, <Taxonomy: rat noir (common)>]
>>> col.taxa.all()
[<Taxa: mus>]
>>> col.homonyms.all()
[<HomonymName: echinops>]
>>> col.synonyms.all()
[<SynonymName: antilocapra anteflexa>]
>>> col.commons.all()
[<CommonName: rat noir (french)>]
>>> col.bad_taxa.all()
[<BadTaxa: blabla (1)>]
```

We can have also informations about trees :

```
>>> col.trees.all()
[<Tree: 1>, <Tree: 2>]
>>> col.trees.count()
2L
```

More interresting, we can get all invalid trees :

```
>>> col.trees.filter( is_valid = False )
[<Tree: 2>]
```

or good

```
>>> col.trees.filter( is_valid = True )
[<Tree: 1>]
```

## Adding trees in the collection ##

We can add a tree into our collection realy easily:

```
>>> tree = Tree.objects.create( name = 'newtree', source = "(mus musculus, rattus rattus )" )
>>> col.trees.add( tree )
```

Tree collection can be created by insering trees

```
>>> newcol = TreeCollection.object.create()
>>> newcol.trees = [tree1, tree2, tree3, tree4]
```

And get a nexus format string from this new collection :

```
>>> tree_col.get_collection_string()
```

## Making queries ##

We can make queries to get some trees that match it.

```
>>> simple_col = "(mus,echinops <plantae>,rattus);(mus, rattus);"
>>> col = TreeCollection.objects.create( name = 'query_col', source = simple_col )
```

Get all trees wich contain at least on taxa wich are a muridae

```
>>> col.query( '{muridae} > 1' )
[<Tree: 1>, <Tree: 2>]
```

Get all trees wich contain at least on taxa wich are a muridae and wich not have plantae taxa

```
>>> col.query( '{muridae}> 1 and not {plantae}' )
[<Tree: 2>]
```

All of those previous results are list objects. Sometime it's necessary to get a collection instead :

```
>>> filtered_col = col.get_collection_from_query( '{plantae}' )
>>> filtered_col.trees.all()
[<Tree: 1>]
```