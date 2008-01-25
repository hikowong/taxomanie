#!/usr/bin/env python
#-*- coding: utf-8 -*-

## Copyright © 2005 Joël Maïzi, joel.maizi@lirmm.fr

## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import unittest
import sys
sys.path.insert( 0, "../src" )
from species import Species

class testSpecies( unittest.TestCase ):
    """ Class test of Bla  """
    def setUp( self ):
        pass

    def tearDown( self ):
        pass
   
    def test_nameCorrect( self ):
        """ Test with a correct name """
        rattus = Species( "rattus" )
        self.assertEqual( rattus.checkName( "rattus" ), [] )

    def test_nameIncorrect( self ):
        """ Test with an incorrect name """
        ratus = Species( "ratus" )
        self.assertEqual( ratus.checkName( "rattus" ), ['matus', 'rats', 'catus',
        'rarus', 'atus', 'aratus', 'gratus', 'ravus', 'rattus', 'artus',
        'latus'] )
#        print ratus.pickName( "rattus" )

    def test_getParent( self ):
        """ get the parent of species """
        ratus = Species( "rattus" )
        print ratus.getParent()

    
if __name__ == '__main__':
    unittest.main()

