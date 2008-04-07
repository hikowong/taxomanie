import os, sys, shutil

please_install = "Before installing PhyloExplorer, please install the"

print "Checking pleet..."
try:
    import pleet
    print "ok"
except ImportError:
    sys.exit( please_install+" pleet library" )
print "Checking networkx..."
try:
    import networkx
    print "ok"
except ImportError:
    sys.exit( please_install+" networkx library" )
print "Checking cherrypy..."
try:
    import cherrypy
    print "ok"
except ImportError:
    sys.exit( please_install+" cherrypy library" )
print "Checking phylocore..."
try:
    import phylocore
    print "ok"
except ImportError:
    sys.exit( please_install+" phylocore library" )

try:
    path = sys.argv[1]
except:
    path = "/usr"

data_path = path+"/share/phyloexplorer"
bin_path = path+"/bin/"
#python_version = "".join( os.popen( "python -V" ).read().split() ).split(".")[:-1]
#python_version = ".".join( 
#  "".join( os.popen("python -V 2>&1").read().split() ).split(".")[:-1]).lower()

#lib_path = path+"/lib/"+python_version+"/site-packages/phylocore"

os.system( "mkdir -p "+data_path )
os.system( "mkdir -p "+bin_path )
#os.system( "mkdir -p "+lib_path )
os.system( "mkdir -p "+data_path+"/etc" )
os.system( "mkdir -p "+data_path+"/templates" )
#os.system( "mkdir -p "+data_path+"/tools" )
os.system( "mkdir -p "+data_path+"/data" )

os.system( "cp -vf src/phyloexplorer.py "+bin_path+"/phyloexplorer" )
os.system( "chmod 755 "+bin_path+"/phyloexplorer" )

os.system( "cp -rfv src/templates/*.html "+data_path+"/templates" )
os.system( "cp -rfv src/templates/*.js "+data_path+"/templates" )
os.system( "cp -rfv src/templates/*.jpg "+data_path+"/templates" )
os.system( "cp -rfv src/templates/site.css "+data_path+"/templates" )
os.system( "cp -rfv src/templates/favicon.ico "+data_path+"/templates" )
#os.system( "cp -rfv src/tools/preproc.py "+data_path+"/tools" )
#os.system( "chmod 755 "+data_path+"/tools/preproc.py" )
#os.system( "cp -rfv src/tools/taxonomy.csv "+data_path )

os.system( "cp -vf src/etc/phyloexplorer.conf "+data_path+"/etc" )

#os.system( "cp -rfv src/__init__.py "+lib_path )
#os.system( "cp -rfv src/taxonomyreference.py "+lib_path )
#os.system( "cp -rfv src/treecollection.py "+lib_path )
#os.system( "cp -rfv src/phylogenetictree.py "+lib_path )
#os.system( "cp -rfv src/lib/phylogelib.py "+lib_path )

print
print "Installation completed"
#print "Please update the NCBI database by launching preproc.py in %s/tools" % data_path



