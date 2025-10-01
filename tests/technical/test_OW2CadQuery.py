#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2019-2025, INRIA
#
# This file is part of Openwind.
#
# Openwind is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Openwind is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openwind.  If not, see <https://www.gnu.org/licenses/>.
#
# For more informations about authors, see the CONTRIBUTORS file

"""
This file test the generation 3D-file from geometry file with openwind.
"""

import unittest
from pathlib import Path
import os

from openwind import InstrumentGeometry
from openwind.technical import OWtoCadQuery
import cadquery

parent_path = str(Path(__file__).parent.absolute().parent)
path = os.path.join(parent_path, 'models')

class UnitOptionsTest(unittest.TestCase):

    def test_mainbore_complex_shape(self):
        my_instru = InstrumentGeometry(os.path.join(path, 'Instru_m_rad_MainBore.txt'))
        my_instru3D = OWtoCadQuery(my_instru, wall_width=3, step=5)
        self.assertTrue(isinstance(my_instru3D.get_3Dobject(),
                                   cadquery.occ_impl.shapes.Shape),
                        )

    def test_holes_leveled(self):
        ig = InstrumentGeometry(os.path.join(path, 'bizarophone_single_file_mm.ow'))
        my_instru3D = OWtoCadQuery(ig, wall_width=3, step=5,
                                   leveled_chimney=True)
        self.assertTrue(isinstance(my_instru3D.get_3Dobject(),
                                   cadquery.occ_impl.shapes.Shape),
                        )

    def test_holes_putting_out(self):
        ig = InstrumentGeometry(os.path.join(path, 'bizarophone_single_file_mm.ow'))
        my_instru3D = OWtoCadQuery(ig, wall_width=3, step=5,
                                   leveled_chimney=False,
                                   chim_width=2,
                                   angles=[180,45],
                                   )
        self.assertTrue(isinstance(my_instru3D.get_3Dobject(),
                                   cadquery.occ_impl.shapes.Shape),
                        )

if __name__ == "__main__":
    unittest.main()
