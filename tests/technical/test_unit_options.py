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

import unittest
import numpy as np
from pathlib import Path
from openwind.technical import InstrumentGeometry
from openwind.technical.parser import parse_lines, check_version


parent_path = str(Path(__file__).parent.absolute().parent)
path = parent_path + '/models/'

class UnitOptionsTest(unittest.TestCase):


    def get_main_bore(self, unit_coef, diam_coef):
        geom  = [[0.00000*unit_coef,	   0.00090*unit_coef,	   0.00870*unit_coef*diam_coef,	   0.00460*unit_coef*diam_coef,	     'Circle',	  -0.01000*unit_coef],
                 [0.00090*unit_coef,	   0.00140*unit_coef,	   0.00460*unit_coef*diam_coef,	   0.00240*unit_coef*diam_coef,	     'Circle',	   0.00700*unit_coef],
                 [0.00140*unit_coef,	   0.01000*unit_coef,	   0.00240*unit_coef*diam_coef,	   0.00300*unit_coef*diam_coef,	       'Cone'],
                 [0.01000*unit_coef,	   0.03000*unit_coef,	   0.00420*unit_coef*diam_coef,	   0.00500*unit_coef*diam_coef,	       'Cone'],
                 [0.03000*unit_coef,	   0.10000*unit_coef,	   0.00500*unit_coef*diam_coef,	   0.00500*unit_coef*diam_coef,	     'Spline',	   0.04000*unit_coef,	   0.07000*unit_coef,	   0.00600*unit_coef*diam_coef,	   0.00400*unit_coef*diam_coef	],
                 [0.10000*unit_coef,	   0.12000*unit_coef,	   0.00500*unit_coef*diam_coef,	   0.01000*unit_coef*diam_coef,	'Exponential'],
                 [0.12000*unit_coef,	   0.14000*unit_coef,	   0.01000*unit_coef*diam_coef,	   0.05000*unit_coef*diam_coef,	     'Bessel',	   0.80000],
                 ]

        holes_valves = [['label', 'variety', 'x', 'l', 'r', 'reconnection'],
                        ['p1', 'valve', 0.015*unit_coef, 0.055*unit_coef, 0.0025*unit_coef*diam_coef, 0.016*unit_coef],
                        ['h1', 'hole', 0.022*unit_coef, 0.003*unit_coef, 0.0025*unit_coef*diam_coef, '/']]
        return geom, holes_valves


    def check_mb_equal(self, instru1, instru2):
        self.assertEqual(instru1.get_main_bore_length(), instru2.get_main_bore_length())
        positions = np.linspace(0, instru1.get_main_bore_length(), 100)
        for pos in positions:
            self.assertAlmostEqual(instru1.get_main_bore_radius_at(pos), instru2.get_main_bore_radius_at(pos), 15)

    def check_side_equal(self, instru1, instru2):
        side1_tot = instru1.holes + instru1.valves
        side2_tot = instru2.holes + instru2.valves

        for side1, side2 in zip(side1_tot, side2_tot):
            self.assertEqual(side1.position.get_value(),
                             side2.position.get_value())
            self.assertEqual(side1.shape.get_length(),
                             side2.shape.get_length())
            self.assertEqual(side1.shape.get_radius_at(.5),
                             side2.shape.get_radius_at(.5))

    def check_mb_list_equals(self, str_comp, list_ref):
        list_comp = parse_lines(str_comp.splitlines())
        for k, line in enumerate(list_comp):
            # test the numeric values
            num_val = [float(a) for a in line[:4] + line[5:]]
            ref_val = [a for a in list_ref[k][:4] + list_ref[k][5:]]
            for j in range(len(num_val)):
                self.assertEqual(num_val[j], ref_val[j])
            # test the shape type
            self.assertEqual(line[4], list_ref[k][4])

    def check_side_list_equal(self, str_comp, list_ref):
        list_comp = parse_lines(str_comp.splitlines())
        for k, line in enumerate(list_comp[1:]):
            num_val = [float(a) for a in line[2:-1]]
            ref_val = [a for a in list_ref[k][2:-1]]
            for j in range(len(num_val)):
                self.assertEqual(num_val[j], ref_val[j])
            if line[-1] != '/':
                self.assertEqual(float(line[-1]), list_ref[k][-1])


    def test_main_bore_list(self):
        mb_mm_diam = self.get_main_bore(1000, 2)[0]
        mb_m_rad = self.get_main_bore(1, 1)[0]

        instru_mm_diam = InstrumentGeometry(mb_mm_diam, unit='mm', diameter=True)
        instru_m_rad = InstrumentGeometry(mb_m_rad)

        self.check_mb_equal(instru_mm_diam, instru_m_rad)

    def test_hole_list(self):
        mb_mm_diam, hv_mm_diam = self.get_main_bore(1000, 2)
        mb_m_rad, hv_m_rad = self.get_main_bore(1, 1)

        instru_mm_diam = InstrumentGeometry(mb_mm_diam, hv_mm_diam, unit='mm', diameter=True)
        instru_m_rad = InstrumentGeometry(mb_m_rad, hv_m_rad)

        self.check_side_equal(instru_mm_diam, instru_m_rad)

    def test_external_file_mb(self):
        mb_m_rad = self.get_main_bore(1, 1)[0]
        instru_m_rad = InstrumentGeometry(mb_m_rad)

        ext_m_rad = InstrumentGeometry(path + 'Instru_m_rad_MainBore.txt')
        self.check_mb_equal(ext_m_rad, instru_m_rad)
        ext_mm_diam = InstrumentGeometry(path + 'Instru_mm_diam_MainBore.txt')
        self.check_mb_equal(ext_mm_diam, instru_m_rad)

    def test_external_file_hole(self):
        mb_m_rad, hv_m_rad = self.get_main_bore(1, 1)
        instru_m_rad = InstrumentGeometry(mb_m_rad, hv_m_rad)

        ext_m_rad = InstrumentGeometry(path + 'Instru_m_rad_MainBore.txt', path + 'Instru_m_rad_SideComp.txt')
        self.check_side_equal(ext_m_rad, instru_m_rad)

        ext_mm_diam = InstrumentGeometry(path + 'Instru_mm_diam_MainBore.txt', path + 'Instru_mm_diam_SideComp.txt')
        self.check_side_equal(ext_mm_diam, instru_m_rad)

        ext_mixed = InstrumentGeometry(path + 'Instru_mm_diam_MainBore.txt', path + 'Instru_m_rad_SideComp.txt')
        self.check_mb_equal(ext_m_rad, ext_mixed)
        self.check_side_equal(ext_mixed, instru_m_rad)

    def test_print(self):
        mb_mm_diam, hv_mm_diam = self.get_main_bore(1000, 2)
        mb_m_rad, hv_m_rad = self.get_main_bore(1, 1)

        instru_m_rad = InstrumentGeometry(mb_m_rad, hv_m_rad)

        mm_diam_printed = instru_m_rad.print_main_bore_shape(unit='mm', diameter=True)
        self.check_mb_list_equals(mm_diam_printed, mb_mm_diam)
        m_rad_printed = instru_m_rad.print_main_bore_shape(unit='m', diameter=False)
        self.check_mb_list_equals(m_rad_printed, mb_m_rad)

        holes_mm_diam_printed = instru_m_rad.print_side_components(unit='mm', diameter=True)
        self.check_side_list_equal(holes_mm_diam_printed, hv_mm_diam[1:])
        holes_m_rad_printed = instru_m_rad.print_side_components(unit='m', diameter=False)
        self.check_side_list_equal(holes_m_rad_printed, hv_m_rad[1:])

    def test_version(self):
        with self.assertWarns(Warning):
            check_version('1000.2')

if __name__ == "__main__":
    unittest.main()
