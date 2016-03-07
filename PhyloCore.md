PhyloCore library provides tools for manipulating tree collections and taxonomic information. It can be use either with NCBI http://www.ncbi.nlm.nih.gov/Taxonomy/ or ITIS [Itis database](http://www.itis.gov/) taxonomic database  .

Main features of PhyloCore are:
  * Taxon manipulation:
    * Getting all scientific names of taxa
    * Getting synonyms, homonyms and commons name from a scientific taxa name
    * Getting parents and children
    * Getting rank
  * Tree manipulations:
    * Getting all taxa (Taxa objects) from newick tree format
    * Getting synonyms, commons names and homonyms from tree
    * Getting NetworkX arborescence (useful for graph manipulations)
  * Tree collection mapulations:
    * Support of phylip and nexus format
    * Getting bad formated tree names
    * Getting statistics (number for taxa, number of synonyms...)
    * Getting trees/taxa matrix

# DjangoPhylocore vs PhyloCore #

DjangoPhylocore can not easily be used outside a django project. We thus create PhyloCore,  a wrapper against DjangoPhylocore, that provides the same functionnalities and can be uses outside a django project. In short, if you developpe a web application upon django, use DjangoPhylocore, otherwise use PhyloCore.

PhyloCore is declined in two version : phylocore\_ncbi and phylocore\_itis.
The only difference is the taxonomy underlying.

# Dependencies #
PhyloCore relies on Django wich is written in Python. So, you need Python and Django.

PhyloCore is using a database for dealing with taxonomy. Please install SQLite3 or MySQL
and their python wrapper : [mysql-python](http://sourceforge.net/projects/mysql-python) for MySQL or [pysqlite](http://initd.org/pub/software/pysqlite/) for sqlite...

[NetworkX](http://networkx.lanl.gov/) for the graph manipulations. If you have easy\_install you can install it via `easy_install networkx` as root.

[Pyparsing](http://pyparsing.wikispaces.com/) for parsing newick collection (`easy_install pyparsing`)

You can check whether those dependencies have been successfully installed by typing those
lines into the python interpreter:

```
>>> import sqlite3
>>> import django
>>> import networkx
>>> import pyparsing
```

In order to get matrix working, you will need the "convert" program from [ImageMagick](http://www.imagemagick.org/script/index.php) or cairo python librairieshttp://cairographics.org/pycairo/.

# Installation #
First of all, download an install [Django 1.0](http://www.djangoproject.com/download/).

Then, checkout the svn repository:
```
svn checkout http://taxomanie.googlecode.com/svn/trunk/ taxomanie
```

Go to the PhyloCore folder and launch the `install` script:
```
cd taxomanie/taxomanie-1.0
sudo ./install
```

This will create symbolic link into your $PYTHONPATH (/usr/local/lib/pythonX.X/site-packages)

### Installing NCBI taxonomy ###

Go to phyloexplorer/ncbi to install NCBI taxonomy and type those commands :

```
python manage.py install -v
```

This will download the taxonomy from the web and build the database.

### Installing ITIS taxonomy ###

Go to phyloexplorer/itis to install ITIS taxonomy and type those commands :

```
python manage.py install -v
```
This will download the taxonomy from the web and build the database.

### Verification ###

In order to verify that the installation goes well, put this line into your shell:

for ncbi:
```
( cd /tmp ; python -c "from phylocore_ncbi import *" )
```


for itis:
```
( cd /tmp ; python -c "from phylocore_itis import *" )
```

if nothing shows up then you're good. Congratulation !

## Using mysql ##

By default, PhyloCore is configured for sqlite3.
If you want to use mysql (for deploying reasons), you have to go to
phylocore/phylocore\_ncbi and/or phylocore/phylocore\_itis and edit the
setting.py file.

Change 'sqlite3' by 'mysql' and fill the line bellow.

Create the database

```
mysql -u user -p -e "CREATE DATABASE database_name CHARACTER SET utf8;"
```

**Utf-8 is important as django stores all it's data into this charset.**

Then install the taxonomy into the database by typing

```
python manage.py install -v
```

### configuring matrix image conversion ###

Insert in the taxomanie-1.0/phyloexplorer/ncbi/settings.py and taxomanie-1.0/phyloexplorer/itis/settings.py setting files the following line :

```
CONVERT_SVG_BIN = 'convert'
```

this tell phyloexplorer which conversion program to use (here the convert command from image magick). You can use all commands (prog) with the followinging syntax :

```
prog img.svg img.png
```

As an alternative to imagemagick you can for instance use the script provided with phyloexplorer that rely on the cairo library. In this case add the following line in your setting files

```
CONVERT_SVG_BIN = 'svg2png'
```
and ensure that svg2png is in your PATH

# Going further #

Using PhyloExplorer

Next, follow the [tutorial](PhyloCoreTutorial.md).

Developpers, follow the [developpers guide](PhyloCoreDeveloppers.md).