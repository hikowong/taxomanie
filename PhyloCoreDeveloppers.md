# Introduction #

You'll find in this page all information for programming with PhyloCore.

# Filling Database #


The database is fill with the `./manage.py loadtaxonomy` command. This command
will search for dumps files (actually csv files) in djangophylocore/dumps.

## Generating dumps files ##

If you want to include your database into phyloexplorer, you must create your dump file and follow certains rules when creating those dump files.

### rank.dmp ###
```
id|name
```

you must have an 'no rank' rank

### taxonomy.dmp ###
```
id|taxa_name|type_name|rank_id|parent_id
```

`type_name` must be 'scientific name', 'synonym', 'common' or 'homonym'

note that if you don't have rank put the 'no rank' rank id

### parentsrelation.dmp ###
```
id|taxa_id|parent_id|index
```

where `taxa_id` and `parent_id` are from taxonomy.dmp and index is the depth of the parent from the taxa.

Exemple:
```
index of (mus, murinae) -> 1
index of (mus, rodontia) -> 2...
```

### relsynonymtaxa.dmp ###

```
id|synonym_id|taxa_id
```

where `synonym_id` and `taxa_id` are from taxonomy.dmp

### relhomonymtaxa.dmp ###
```
id|homonym_id|taxa_id
```

where `homonym_id` and `taxa_id` are from taxonomy.dmp

### relcommontaxa.dmp ###
```
id|common_id|taxa_id|langage
```

where `common_id` and `taxa_id` are from taxonomy.dmp

exemple:
```
1|2|4|french
```