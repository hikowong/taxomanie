
from species import Species

TREE = {}
LIST_PARENT = []

def createTree( name ):
    child = Species( name = name )
    parent = child.getParent()
    if name != "root":
        parent.setChild( child )
   # if parent not in LIST_PARENT:
   #     LIST_PARENT.append( parent )
    while parent.name != "root":
        child = parent
        parent = child.getParent()
        parent.setChild( child )
        print parent.name
   #     if parent not in LIST_PARENT:
   #         LIST_PARENT.append( parent )
    return parent

PARENT = createTree( "root" )
#print LIST_PARENT
