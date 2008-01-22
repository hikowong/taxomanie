
from species import Species

def createTree( name ):
    child = Species( name = name )
    parent = child.getParent()
    LIST_PARENT = []
    if name != "root":
        parent.setChild( child )
    if parent not in LIST_PARENT:
        LIST_PARENT.append( parent )
    while parent.name != "root":
        child = parent
        parent = child.getParent()
        parent.setChild( child )
        if parent not in LIST_PARENT:
            LIST_PARENT.append( parent )
    return LIST_PARENT


def getCommonParent( a, b ):
    a = Species( name = a )
    b = Species( name = b )
    list_parents_a = createTree( a.name )
    parent_b = b.getParent()
    while parent_b.name != "root":
        child = parent_b
        parent_b = child.getParent()
        for parent_a in list_parents_a:
            if parent_b == parent_a:
                return parent_b

print getCommonParent( "rattus", "conus rattus" )


