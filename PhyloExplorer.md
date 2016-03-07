# About #

PhyloExplorer is a free, simple to use web service facilitating the management and enrichment of phylogenetic tree collections.

Given an input collection of rooted trees, PhyloExplorer provides facilities for correcting erroneous or ambiguous taxon names,
for identifying related trees in TreeBASE, for obtaining statistics describing the collection, and a query language to extract
taxonomically relevant parts of the collection. PhyloExplorer is also available as a standalone version that includes both a
webserver identical to this one and package of Python libraries and database files that can be directly used by users with
computing skills.

# Launching PhyloExplorer #

You can use phyloExplorer on the following web server http://www.ncbi.orthomam.univ-montp2.fr/phyloexplorer/ or install your own local version

You must install and configure PhyloCore before using PhyloExplorer

To launch phyloexplorer server, go to taxomanie-1.0 and type:

```
python phyloexplorer.py start
```

To see Phyloexplorer in action with NCBI go to:

> http://127.0.0.1:8000/phyloexplorer

To see Phyloexplorer in action with ITIS go to:

> http://127.0.0.1:8001/phyloexplorer


to stop the server type:
```
python phyloexplorer.py stop
```

## Configuring PhyloExplorer ##

You can configure the server address to feed your needs.

Go to phyloexplorer directory and edit the phyloconf.py file.