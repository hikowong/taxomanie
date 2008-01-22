#!/usr/bin/env python
#################################################
# Licence :
# Released under CeCILL license
# This program is Copyleft. You can disrtribued in
# order that you follow the CeCILL licence :
# http://www.cecill.info/
#
# Author:
# Nicolas Clairon : clairon _chez_ gmail __point__ com
#################################################
""" Pylogenic trees manipulating fonctions """
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
      newarb.append(chaine)
      chaine = ""
      continue
    if i == "(" and p == 1:
      continue
    chaine += i
  return newarb

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
  for i in tree:
    if i == ":":
      ignore = True
    if i == "," or i == ")":
      ignore = False
    if not ignore:
      chaine += i
  return chaine

# def generateTree(tree,G):
#   """ Convert a nwk string to a graph """
#   G.add_node(tree)
#   for child in getChildren(tree):
#     if len(child) == 1:
#       G.add_node(child)
#       G.add_edge((tree,child))
#     else:
#       G.add_node(child)
#       G.add_edge((tree,child))
#       generateTree(child,G)

# def getTaxas(tree):
#   """ Extract Taxas from tree to a list with no redondance """
#   tree = tree.replace("(","")
#   tree = tree.replace(")","")
#   tree = tree.replace(","," ")
#   return tree.split()

#def getTaxas(tree):
  #""" Extract Taxas from tree to a list with no redondance """
  #skip = False
  #chaine = ""
  #taxas = []
  #j = 0
  #for i in tree:
    #j+=1
    #if i==":":
      #skip = True
      #continue
    #if i == "," or i == ";" or j == len(tree):
      #skip = False
      #if chaine != "" and chaine not in taxas:
        #taxas.append(chaine)
        #chaine = ""
      #continue
    #if i == "(" or i == ")":
      #continue
    #if skip == False:
      #chaine += i
    #if skip == True:
      #if chaine != "" and chaine not in taxas:
        #taxas.append(chaine)
        #chaine = ""
  #return taxas

def getTaxa(tree):
  """ Return the taxas list """
  tree = removeBootStraps(tree)
  if len(getChildren(tree)) == 0:
    return [tree]
  l = []
  for child in getChildren(tree):
    l.extend(getTaxa(child))
  return l

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
    listTaxasChild = getTaxas(child)
    listIn = []
    for i in listTaxasChild:
      for j in listTaxasChild:
        if i!=j and ([i,j] not in listIn) and ([j,i] not in listIn):
          listIn.append([i,j])
    listExt = [i for i in getTaxas(tree) if i not in listTaxasChild]
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
  for i in getTaxas(tree):
    listNodes.remove(i)
  result = 0
  for child in listNodes:
    nbTaxas = len(getTaxas(child))
    result += (nbTaxas * (nbTaxas-1) * (len(getTaxas(getParent(tree,child))) - nbTaxas)) / 2
  return result

# def intToString(num):
#   import string
#   if num <= 0:
#     return ""
#   return str(string.ascii_lowercase[(num-1) % 26]) + intToString((num-1)/26)

# def intToString(num):
#   import string
#   name = ""
#   while num > 0:
#     name += str(string.ascii_lowercase[(num-1) % 26])
#     num = (num-1)/26
#   return name

# def generateTree(nbTaxas, name=1, maxChilds = 2):
#   from random import random
#   assert(nbTaxas > 0)
#   assert(maxChilds >1)
#   if nbTaxas == 1:
#     return intToString(name)
#   coupe = int((nbTaxas-1) * random()) + 1
#   return "("+generateTree(coupe, name,maxChilds)+","+generateTree(nbTaxas - coupe, name+coupe,maxChilds)+")"

def nwk2list( tree ):
    tree = removeBootStraps( tree )
    tree = tree.replace( "(", "[" ).replace( ")", "]" )
    tree = tree.replace( ",", "','" ).replace( "]',", "]," ).replace(",'[",",[")
    tree = tree.replace("[","['").replace( "['[", "[[" )
    tree = tree.replace( "]", "']" ).replace( "]']", "]]")
    tree = tree.replace("['[", "[[" )
    tree = tree.replace("]']", "]]" )
    return eval( tree )
 

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
