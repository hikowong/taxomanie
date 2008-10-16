#!/usr/bin/env python
#################################################
# Licence :
# Released under CeCILL license
# This program is Copyleft. You can disrtribued in
# order that you follow the CeCILL licence :
# http://www.cecill.info/
#
# Author:
# Nicolas Clairon : clairon [_at_] gmail.com
#################################################
""" Pylogenic trees manipulating fonctions """

def tidyNwk( nwk ):
    """ Strip all space and backline from newick string """
    nwk = nwk.replace( "\n", " " )
    while "  " in nwk:
        nwk = nwk.replace( "  ", " " )
    while '( ' in nwk:
        nwk = nwk.replace( '( ', '(' )
    while ' )' in nwk:
        nwk = nwk.replace( ' )', ')' )
    nwk = nwk.replace( ", (", ",(" )
    nwk = nwk.replace( " ,", "," )
    nwk = nwk.replace( ", ", "," )
    nwk = nwk.replace( ") ,", ")," )
    nwk = nwk.replace( ") )", "))" )
    nwk = nwk.replace( "( (", "((" )
    return nwk.strip()

def checkNwk( nwk ):
    """
    Check if nwk is in the correct newick format
    """
    try:
        nwk2list( nwk )
        return True
    except:
        return False
        
def removeNexusComments( nex ):
    """ remove all nexus comments """
    nwk_without_comment = ""
    for i in nex.split("["):
        if len(i.split("]")) > 1:
            nwk_without_comment += "".join( i.split("]")[1] )
        else:
            nwk_without_comment += i 
    return nwk_without_comment

def getParent(tree,node):
  """ Return the parent of the node """
  if tree == node:
    return ""
  for child in getChildren(tree):
    if child == node:
      return tree
    if node in child:
      parent = getParent(child,node)
  return parent


def getChildren(tree):
  """ Extract all first child of tree to a list """
  p = 0
  chaine = ""
  newarb = []
  for i in tree:
    if i == "(":
      p += 1
    if i == ")":
      p -= 1
    if (i == "," and p == 1) or (i == ")" and p == 0):
      newarb.append(chaine.strip())
      chaine = ""
      continue
    if i == "(" and p == 1:
      continue
    chaine += i
  return newarb

def getBrothers( tree, node ):
  """ return all node brothers in tree """
  tree = removeBootStraps( tree )
  return getChildren( getParent( tree, node ) )
 
def getNodes(tree):
  """ Return the nodes list of tree """
  listNodes = []
  if tree not in listNodes:
    listNodes.append(tree)
  for child in getChildren(tree):
    if child not in listNodes:
      listNodes.extend(getNodes(child))
  return listNodes

def getEdges(tree):
  """ Return the edges list in tree """
  if len(getChildren(tree)) == 0:
    return []
  listEdges = []
  for child in getChildren(tree):
    listEdges.append((tree,child))
    listEdges.extend(getEdges(child))
  return listEdges

def getTree(tree):
  """ Convert a newick string to a list :
     [ [nodelist] [edgeslist] ] """
  if len(getChildren(tree)) == 0:
    return [tree,[]]
  listEdges = []
  listNodes = [tree]
  for child in getChildren(tree):
    r = getTree(child)
    listNodes.extend(r[0])
    listEdges.append([tree,child])
    listEdges.extend(r[1])
  return [listNodes,listEdges]

def removeBootStraps(tree):
  """ Remove all bootstraps from tree """
  chaine = ""
  ignore = False
  for i in range(len(tree)):
    if tree[i] == ":":
      ignore = True
    if tree[i] == "," or tree[i] == ")":
      ignore = False
    if i > 0 and tree[i-1] == ')' and tree[i] not in "),":
      ignore = True
    if not ignore:
      chaine += tree[i]
  return chaine

#def getTaxa(tree):
#  """ Return the taxas list """
#  tree = removeBootStraps(tree).strip()
#  if len(getChildren(tree)) == 0:
#    return [tree]
#  l = []
#  for child in getChildren(tree):
#    l.extend(getTaxa(child))
#  return l

def getTaxa( tree ):
    return [i.strip() for i in removeBootStraps(tree.strip()).replace("(","").replace(")","").split(",")]

def getDepth(tree):
  """ Return the depth of the tree """
  if len(getChildren(tree)) == 0:
    return 0
  depth = 0
  for child in getChildren(tree):
    depth = max(getDepth(child),depth)
  return 1 + depth

def getTriplets(tree):
  """ Extract all triplets of the tree in the list listTriplets """
  listTriplets = []
  for child in getChildren(tree):
    listTaxasChild = getTaxa(child)
    listIn = []
    for i in listTaxasChild:
      for j in listTaxasChild:
        if i!=j and ([i,j] not in listIn) and ([j,i] not in listIn):
          listIn.append([i,j])
    listExt = [i for i in getTaxa(tree) if i not in listTaxasChild]
    for i in listExt:
      for j in listIn:
        chaine = "("+i+",("+j[0]+','+j[1]+"))"
        listTriplets.append(chaine)
    listTriplets.extend(getTriplets(child))
  return listTriplets

def countTriplets(tree):
  """ Count the number of triplets in the tree """
  listNodes = getNodes(tree)
  listNodes.remove(tree)
  for i in getTaxa(tree):
    listNodes.remove(i)
  result = 0
  for child in listNodes:
    nbTaxas = len(getTaxa(child))
    result += (nbTaxas * (nbTaxas-1) * (len(getTaxa(getParent(tree,child))) - nbTaxas)) / 2
  return result

def nwk2list( nwk ):
    """
    Take a newick string and return a python list

    @nwk: string
    @return: python list
    """
    nwk = removeBootStraps( nwk )
    nwk = nwk.replace( "(", "[" ).replace( ")", "]" )
    nwk = nwk.replace( ",", "','" ).replace( "]',", "]," ).replace(",'[",",[")
    nwk = nwk.replace("[","['").replace( "['[", "[[" )
    nwk = nwk.replace( "]", "']" ).replace( "]']", "]]")
    nwk = nwk.replace("['[", "[[" )
    nwk = nwk.replace("]']", "]]" )
    return eval( nwk )

def generateTree(nbTaxas, maxChildren = 2, name = 1):
  """ Generate randomly a pylogenic tree :
      nbTaxas : number of taxa wanted
      maxChildren : number for incertitude
      name : index of the name in the alphabet """
  from random import random
  import string
  assert(nbTaxas > 0)
  assert(maxChildren > 1)
  if nbTaxas == 1:
    # intToString
    strName = ""
    while name > 0:
      strName += str(string.ascii_lowercase[(name-1) % 26])
      name = (name-1)/26
    return strName
#     return intToString(name)
  if maxChildren > nbTaxas:
    maxChildren = nbTaxas
  numChildren = int(((maxChildren - 2) + 1) * random()) + 2
  coupes = []
  coupes.append(1)
  for i in xrange(numChildren - 1):
    rand = int(((nbTaxas - 2) + 1) * random()) + 2
    while rand in coupes:
      rand = int(((nbTaxas - 2) + 1) * random()) + 2
    coupes.append(rand)
  coupes.append(nbTaxas + 1)
  coupes.sort()
  results = "("
  for i in xrange(len(coupes) - 1):
    if i != 0:
      results += ","
    results += generateTree(coupes[i + 1] - coupes[i], maxChildren, name + coupes[i] - 1)
  results += ")"
  return results

####################################################################################################
""" Exemple of pylogenic trees """
a = "((a,b),c,(d,(e,f)))"
b = "((((a,b),c,d),(e,f)),g)"
c = "(((a,b),c,d),e,f,((g,h),i))"
d = "(t5:0.004647,t4:0.142159,((t6:0.142159,t1:0.047671)10:0.115,DinosauriaxDinosorus:0.545582)60:0.995353)"
####################################################################################################


