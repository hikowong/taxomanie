This page reference the most common objects api.
For more information please read the
[django documentation](http://www.djangoproject.com) or the unittest

# TaxonomyReference #

```

    This object provides some useful methods in order to deal with taxonomy
    
```

**get\_common\_parents**
```

        select * from djangophylocore_parentsrelation where parent_id IN (select parent_id from djangophylocore_parentsrelation where taxa_id = 10114 except select parent_id from djangophylocore_parentsrelation where taxa_id = 9989 ) and taxa_id = 10114;
        
```

**is\_common**
```

        return True if name is a common name
        return False otherwise
        
```

**strip\_taxon\_name**
```

        Strip Taxon name in order to keep the root name and to remove
        all user staff.
        
```

**get\_object\_from\_name**
```

        return the django object from taxon name.

        Name is checked in this order :
          * scientific name
          * synonym
          * homonym
          * common
          * bad taxa
        if the name is not found, a RuntimeError is raised as it must never be
        append
        
```

**get\_interval\_parents**
```

        return parents list beetween 2 taxa.
        Note that taxon1 must be a parent of taxon2
        
```

**get\_name\_from\_synonym**
```

        return all taxa which have synonym
        
```

**get\_first\_common\_parent**
```

        return the first common parent of taxa_list
        if root is passed to the list, None is returned as root has no parents
        
```

**get\_reference\_graph**
```

        Take a taxa list, search in reference all parents names and
        return a networkx.DiGraph tree.
        
```

**is\_synonym**
```

        return True if name is a synonym
        return False otherwise
        
```

**get\_name\_from\_common**
```

        return all taxa which have common_name
        
```

**get\_name\_from\_homonym**
```

        return all taxa which have homonym
        
```

**is\_bad\_taxon**
```

        return True if name is a bad taxon name
        return False otherwise
        
```

**is\_scientific\_name**
```

        return True if name is a scientific name
        return False otherwise
        
```

**is\_valid\_name**
```

        return True if name is in the taxonomy
        return False otherwise
        
```

**correct**
```

        return all scientific names associated to name as a query_set

        The name will be checked in the following order:
        - if name is a scientific name then return None
        - check if name is a homonym
        - check if name is a synonym
        - check if name is a common name
        - check if name is a misspell name
        if no result is found, an empty list is returned

        if guess is True, the system will try to correct the name 
        
```

**is\_homonym**
```

        return True if name is an homonym
        return False otherwise
        
```


### Properties ###

# Taxonomy #

```

    A Taxonomy object represent an element in the taxonomy. It can be a
    scientific name or a synonym, an homonym or a common name. All taxa wich
    are present of the taxonomy reference (itis, ncbi...) is a Taxonomy
    object.

    This object herites from TaxonomyReference

    This object is a Django model. See the django documentation for more
    details.

    >>> mus = Taxonomy.objects.get( name = "mus" )

    # Get all scientific names
    >>> scientific_names = Taxonomy.objects.filter( type_name = "scientific name" )
    
```

**regenerate\_parents**
```

        Regenerate parents list of the taxa. This method is useful if we add
        taxa by hand to the taxonomy.
        
```


### Properties ###

**synonyms**
```

        return a queryset of all synonyms related to the Taxonomy object

        >>> taxon = Taxonomy.objects.get( name = 'mus' )
        >>> taxon.synonyms.all()
        [<Taxonomy: nannomys (synonym)>]
        
```

**homonyms**
```

        return a queryset of all homonyms related to the Taxonomy object

        >>> taxon = Taxonomy.objects.get( name = 'echinops <plant>' )
        >>> taxon.homonyms.all()
        [<Taxonomy: echinops (homonym)>]
        
```

**parents**
```

        return a queryset of all parents related to the Taxonomy object

        >>> taxon = Taxonomy.objects.get( name = 'mus musculus' )
        >>> taxon.parent
        <Taxonomy: mus (scientific name)>
        
```

**commons**
```

        return a queryset of all commons related to the Taxonomy object

        >>> taxon = Taxonomy.objects.get( name = 'mus musculus' )
        >>> taxon.commons.all()
        [<Taxonomy: house mouse (common)>, <Taxonomy: mouse (common)>]
        
```

**scientifics**
```

        return a queryset of all scientific names related to the Taxonomy object

        >>> taxon = Taxonomy.objects.get( name = 'echinops' )
        >>> taxon.scientifics.all()
        [<Taxonomy: echinops <mammal> (scientific name)>, <Taxonomy: echinops <plant> (scientific name)>]
        
```

# Tree #

```

    This object represents a phylogenetic tree. It can be valid (well formed)
    or not. If not, the column_error attribute will indicate the index of the
    failure in the source.

    the _from_collection attribute indicates if the Tree was build from a
    TreeCollection or not.

    This object herites from TaxonomyReference

    This object is a Django model. See the django documentation for more
    details.

    >>> nwk_tree = "( echinops, (rattus, ( mus, azerty, black rat ), nannomys ))"
    >>> tree = Tree.objects.create( source = nwk_tree, name = "2")
    >>> tree.is_valid
    True
    >>> tree.scientifics.all()
    [<Taxonomy: mus (scientific name)>, <Taxonomy: rattus (scientific name)>]
    >>> tree.bad_taxa.all()
    [<BadTaxa: azerty (0)>]
    >>> tree.synonyms.all()
    [<Taxonomy: nannomys (synonym)>]
    >>> tree.homonyms.all()
    [<Taxonomy: echinops (homonym)>]
    >>> tree.commons.all()
    [<Taxonomy: black rat (common)>]

    # Getting all taxon list
    >>> tree.taxa.all()
    [<Taxonomy: black rat (common)>, <Taxonomy: echinops (homonym)>, <Taxonomy:
    mus (scientific name)>, <Taxonomy: nannomys (synonym)>, <Taxonomy: rattus
    (scientific name)>]

    # Getting ambiguous taxa (synonms, commons, homonyms...)
    >>> tree.ambiguous.all() [<Taxonomy: black rat (common)>, <Taxonomy: echinops (homonym)>, <Taxonomy: nannomys (synonym)>]
    
```

**get\_reference\_tree\_as\_nwk**
```

        return the reference arborescence in a newick string
        If internal_label is True, then display internal_label.
        
```

**print\_error**
```

        display where the error is in the source

        >>> tree.print_error()
        (,(mus, rattus)
         ^
        
```

**generate\_tree\_infos**
```

        This method will extract all taxa name from source  and wrap them
        into Taxonomy objects. Those taxonomy objects will be linked to the
        tree.
        
```

**eval\_query**
```

        test if a query match the tree. The query format is a python
        boolean expression with taxa name beetween braces :

        tree.eval_query( "{muridae} > 2 and {primates}" )

        will return true if tree have more than 2 taxa wich have muridae as parents
        and at least 1 taxon wich have a primate as parents.

        if a taxa_list is not null, the query can have another variable
        {usertaxa}. this variable represente all taxa passed in the list.

        tree.eval_query( "{muridae} => 4 and {usertaxa} > 2", ['rattus', 'mus', 'pan', 'boss'] )

        will return true if tree have at least 4 taxa wich are muridae and
        more than 2 taxa wich are in the usertaxa_list 
        
```

**save**
```

        save the tree into the database. If dont_generate is True, the method
        will call generate_tree_info method.
        
```

**get\_ambiguous**
```

        return a queryset of taxonomy objects wich are not scientific name
        
```

**get\_nb\_taxa\_from\_parent**
```

        return the number of taxa wich have `parent_name` for parent
        
```

**taxon\_ids**
```
list() -> new list
list(sequence) -> new list initialized from sequence's items
```

**get\_tree\_as\_nwk**
```

        return the newick format of the tree. 
        If internal_label is True, then display internal_label.
        
```

**get\_reference\_arborescence**
```

        return a netorkX oriented graph wich represente the arborescence of
        the reference taxonomy (itis, ncbi...) of the list of taxa
        
```


### Properties ###

**taxa**
```

        return a queryset of all taxa included ambiguous names and scientific names
        
        >>> tree.taxa.all()
        [<Taxonomy: black rat (common)>, <Taxonomy: echinops (homonym)>, <Taxonomy: mus (scientific name)>, <Taxonomy: nannomys (synonym)>, <Taxonomy: rattus (scientific name)>]
        
```

**arborescence**
```

        return a NetworkX oriented graph from the tree
        
```

**synonyms**
```

        return a queryset of  all synonym names

        >>> tree.synonyms.all()
        [<Taxonomy: nannomys (synonym)>]
        
```

**homonyms**
```

        return a queryset of all homonym names

        >>> tree.homonyms.all()
        [<Taxonomy: echinops (homonym)>]
        
```

**ambiguous**
```

        return a queryset of all ambiguous names (homonym, synonym and common names)
        
        >>> tree.ambiguous.all()
        [<Taxonomy: black rat (common)>, <Taxonomy: echinops (homonym)>, <Taxonomy: nannomys (synonym)>]
        
```

**commons**
```

        return a queryset of  all common names

        >>> tree.commons.all()
        [<Taxonomy: black rat (common)>]
        
```

**scientifics**
```

        return a queryset of all scientific names

        >>> tree.scientifics.all()
        [<Taxonomy: mus (scientific name)>, <Taxonomy: rattus (scientific name)>]
        
```

# TreeCollection #

```

    This object represent a collection of phylogenetic trees.

    Two formats are supported : phylip and nexus. The format is automatiquely
    detected.

    This object herites from TaxonomyReference

    This object is a Django model. See the django documentation for more
    details.

    >>> simple_col = "(mus,nannomys,black rat,echinops,blabla);(mus, black rat);"
    >>> col = TreeCollection.objects.create( name = 'simple', source = simple_col )
    >>> col.format
    'phylip'

    # Deeling with taxa
    >>> col.taxa.all()
    [<Taxonomy: black rat (common)>, <Taxonomy: echinops (homonym)>, <Taxonomy: mus (scientific name)>, <Taxonomy: nannomys (synonym)>]
    >>> col.ambiguous.all()
    [<Taxonomy: black rat (common)>, <Taxonomy: echinops (homonym)>, <Taxonomy: nannomys (synonym)>]
    >>> col.scientifics.all()
    [<Taxonomy: mus (scientific name)>]
    >>> col.homonyms.all()
    [<Taxonomy: echinops (homonym)>]
    >>> col.synonyms.all()
    [<Taxonomy: nannomys (synonym)>]
    >>> col.commons.all()
    [<Taxonomy: black rat (common)>]
    >>> col.bad_taxa.all()
    [<BadTaxa: blabla (0)>]

    # working with tree
    >>> col.trees.all()
    [<Tree: 1>, <Tree: 2>]
    >>> col.trees.count()
    2L
    
```

**get\_reference\_tree\_as\_nwk**
```

        return the reference arborescence in a newick string
        
```

**regenerate\_collection\_string\_from\_trees**
```

        regenerate source from trees in the collection
        
```

**get\_restricted\_collection**
```

        return a collection string wich contains only the taxon present in
        taxon_name_list
        
```

**get\_corrected\_collection**
```

        return a corrected collection where `correction` is a dictionary
        
            {'bad_name': 'good_name'}

        newcol = col.get_corrected_collection( {'echinops': 'echinops <plant>', 'ratis': 'rattus' } )
        
```

**query**
```

        query the collection in order to extract a targeted trees list.

        The query format is a python boolean expression with taxa name
        beetween braces :

        >>> col.query( "{muridae} > 2 and {primates}" )
        [<Tree: 1>, <Tree: 4>]

        will return a list of trees wich have more than 2 taxa wich have
        muridae as parents and at least 1 taxon wich have a primate as
        parents.

        if a taxa_list is not null, the query can have another variable
        {usertaxa}. this variable represente all taxa passed in the list.

        tree.eval_query( "{muridae} => 4 and {usertaxa} > 2", ['rattus', 'mus', 'pan', 'boss'] )

        will return true if tree have at least 4 taxa wich are muridae and
        more than 2 taxa wich are in the usertaxa_list 
        
```

**get\_collection\_string**
```

        Generate from trees the collection_string into the source format.
        
```

**get\_nb\_trees**
```

        return the number of trees in collection wich contain taxon
        
```

**get\_taxon\_from\_parents**
```

        return taxon in collection wich are for parent 'parent_name'
        
```

**get\_corrected\_collection\_string**
```

        return a corrected source string where `correction` is a dictionary
        
            {'bad_name': 'good_name'}

        new_source_string = col.get_corrected_collection( {'echinops': 'echinops <plant>', 'ratis': 'rattus' } )
        
```

**save**
```

        save the collection into the database. If dont_regenerate is False, it
        will call the regenerate_from_source method
        
```

**get\_statistics**
```

        return a dictionary with useful statistic informations.

        The dictionary structure take this form:
           
           {
              taxon_id: {
               'degree': degree_number,
               'scientific_taxon_list': set([]),
               'trees_list': set([]),
               'user_taxon_list': set([])
              },
            }

        i.e.:
        {
             349722: {'degree': 1,
                'scientific_taxon_list': set([u'carpomys']),
                'trees_list': set([6216, 6204, 6206]),
                'user_taxon_list': set([u'carpomys'])
             },
             359160: {'degree': 2,
                'scientific_taxon_list': set([u'oryza sativa']),
                'trees_list': set([6214]),
                'user_taxon_list': set([u'oryza sativa lhb'])
             },
            376913: {'degree': 2,
                'scientific_taxon_list': set([u'homo sapiens']),
                'trees_list': set([6214]),
                'user_taxon_list': set([u'homo sapiens cyg', u'homo sapiens mb',
                  u'homo sapiens ngb', u'homo sapiens hbt', u'homo sapiens hbb',
                  u'homo sapiens hba', u'homo sapiens hbg', u'homo sapiens hbd',
                  u'homo sapiens hbe'])
            },
        }
        
```

**get\_collection\_from\_query**
```

        return a new collection with all trees that match the query
        
```

**get\_tree\_size\_distribution**
```
 return stat of Tree Size Distribution 
```

**get\_matrix**
```

        return the matrix wich described the presence of taxa in trees
        
```

**get\_user\_taxon\_names**
```

        return the user taxon names list
        
```

**get\_reference\_arborescence**
```

        Take a taxon list, search in reference all parents names and
        return a networkx.DiGraph tree.
        
```

**regenerate\_from\_source**
```

        This method will parse the source in order to extract all trees and
        taxa. Those objects are linked to the collection.
        
```

**get\_taxon\_frequency\_distribution**
```

        return stat of taxon frequency distribution
        
```

**get\_autocorrected\_collection**
```

        get a new collection wich have all single ambiguous taxa corrected
        
```

**query\_treebase**
```

        query the treebase collection in order to extract a targeted trees list.

        The query format is a python boolean expression with taxa name
        beetween braces :

        >>> col.query( "{muridae} > 2 and {primates}" )
        [<Tree: 1>, <Tree: 4>]

        will return a list of treebase's trees wich have more than 2 taxa wich have
        muridae as parents and at least 1 taxon wich have a primate as
        parents.

        The special keyword {usertaxa} represent all the taxa present in the
        user collection.

        >>> tree.eval_query( "{muridae} => 4 and {usertaxa} > 2" )

        will return a treebase's trees list wich have at least 4 muridae and
        at least 2 taxa which are present in the user collection.
        
```

**get\_taxon\_name\_from\_parents**
```

        return a taxon names list wich have `parent_name` for parent
        
```

**get\_filtered\_collection\_string**
```

        return a collections string wich have been striped of all taxa present
        in the taxon_name_list
        
```


### Properties ###

**taxa**
```

        return a queryset of all taxa from the collection (included ambiguous one)

        >>> col.taxa.all()
        [<Taxonomy: black rat (common)>, <Taxonomy: echinops (homonym)>, <Taxonomy: mus (scientific name)>, <Taxonomy: nannomys (synonym)>]
        
```

**synonyms**
```

        return a queryset of all synonym names of the collection

        >>> col.synonyms.all()
        [<Taxonomy: nannomys (synonym)>]
        
```

**bad\_trees**
```

        return a queryset of all bad (misformed) trees present in the
        collection

        >>> col.bad_trees.all()
        [<Tree: 2>, <Tree: 4>]
        
```

**homonyms**
```

        return a queryset of all homonym names of the collection

        >>> col.homonyms.all()
        [<Taxonomy: echinops (homonym)>]
        
```

**bad\_taxa**
```

        return a queryset of bad taxa

        >>> col.bad_taxa.all()
        [<BadTaxa: blabla (0)>]
        
```

**ambiguous**
```

        return a queryset of non scientific name taxonomy objects
        
        >>> col.ambiguous.all()
        [<Taxonomy: black rat (common)>, <Taxonomy: echinops (homonym)>, <Taxonomy: nannomys (synonym)>]
        
```

**commons**
```

        return a queryset of all common names of the collection

        >>> col.commons.all()
        [<Taxonomy: black rat (common)>]
        
```

**scientifics**
```

        return a queryset of all scientific names of the collection

        >>> col.scientifics.all()
        [<Taxonomy: mus (scientific name)>]
        
```