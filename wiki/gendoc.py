
from phylocore_ncbi import *

objects = [TaxonomyReference, Taxonomy, Tree, TreeCollection]

def print_method( method_name, method ):
    result = []
    result.append( "*"+method_name+"*" )
    result.append( "{{{" )
    result.append( method.__doc__ )
    result.append( "}}}" )
    result.append( "" )
    return "\n".join( result )

head = """#summary API reference

This page reference the most common objects api. 
For more information please read the
[http://www.djangoproject.com django documentation] or the unittest
"""


big_result = [head]
for obj in objects:
    result = []
    not_documented = []
    properties = []
    result.append( "="+obj.__name__+"=" )
    result.append( "" )
    result.append( "{{{" )
    result.append( obj.__doc__ )
    result.append( "}}}" )
    result.append( "" )
    for method_name,method in obj.__dict__.iteritems():
        if method_name[0] != "_":
            if type( method ) is property:
                properties.append( (method_name, method) )
            elif method.__doc__:
                result.append( print_method( method_name, method ) )
            else:
                not_documented.append( method_name ) 
    result.append( "" )
    result.append( "===Properties===" )
    result.append( "" )
    for method_name, method in properties:
        if method.__doc__:
            result.append( print_method( method_name, method ) )
        else:
            not_documented.append( method_name ) 
    print obj.__name__,": not_documented :",  not_documented
    big_result.append( "\n".join( result ) )
open( "API.wiki", 'w' ).write(  "\n".join( big_result ))
    #open( obj.__name__.capitalize()+".wiki", 'w' ).write(  "\n".join( result ))

