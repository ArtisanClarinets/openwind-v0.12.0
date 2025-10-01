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

from pathlib import Path
from openwind.technical import InstrumentGeometry
import numpy as np

parent_path = str(Path(__file__).parent.absolute().parent)
path = parent_path + '/models/'

class InstrumentGeometryTest(unittest.TestCase):

    def test_simple_parts(self):
        mm = InstrumentGeometry(path + 'mkmodel_test1')
        mm = InstrumentGeometry(path + 'mkmodel_test2')

        conical_geom = [[0, 5e-3], [0.1, 6e-3], [0.2, 4e-3]]
        mm = InstrumentGeometry(conical_geom)
        self.assertEqual(len(mm.main_bore_shapes), 2)
        self.assertEqual(mm.holes, [])

        with self.assertRaises(ValueError):
            # x values can't go backward
            wrong_geom = [[0, 1], [1, 1], [0.5, 1]]
            mm = InstrumentGeometry(wrong_geom)


    def test_complex_parts(self):
        mm = InstrumentGeometry(path + 'complex_parts_example.csv')

        complex_geom = [[0, 5e-3],
                        [0.1, 6e-3],
                        [0.1, 0.2, 5e-3, 6e-3, 'spline', 0.15, 0.17, 7e-3, 2e-3],
                        [0.2, 0.3, 5e-3, 4e-3, 'circle', 6e-3]]
        mm = InstrumentGeometry(complex_geom)


    def test_holes(self):
        mm = InstrumentGeometry(path + 'mkmodel_test2', path + 'mkmodel_test_holes1')
        mm = InstrumentGeometry(path + 'mkmodel_test2', path + 'bizarophone_holes')

    def test_valves(self):
        InstrumentGeometry(path + 'mkmodel_test2', path + 'test_valves')
        wrong_geom = [['label', 'variety', 'x', 'r', 'l'],
                      ['piston', 'valve', .1, 3.3, 0.1]]
        self.assertRaises(ValueError, InstrumentGeometry,
                          path + 'mkmodel_test2', wrong_geom)

    def test_conical_holes_valves(self):
        ins1 = InstrumentGeometry(path + 'mkmodel_test2', path + 'conical_holes_valves.txt')
        
        holes2 = [['label',     'position', 'length',    'radius',   'radius_out'],
                 ['hole_cone2', .1,          5e-3,       4e-3,       2e-3],
                 ['hole_cyl2', .15,          5e-3,       4e-3,       4e-3],
                 ['hole_inv_cone2', .17,          5e-3,       2e-3,       4e-3],
                 ]
        ins2 = InstrumentGeometry([[0, .25, 5e-3, 5e-3, 'linear']], holes2 )
        ins3 = ins1 + ins2

    def test_fingering_chart(self):
        mm = InstrumentGeometry(path + 'mkmodel_test2', path + 'bizarophone_holes', path + 'bizarophone_fingering_chart')
        fing = mm.fingering_chart.fingering_of('do')
        self.assertTrue(fing.is_hole_open('b_flat_hole'))
        self.assertFalse(fing.is_hole_open('g_hole'))
        with self.assertRaises(ValueError):
            fing.is_hole_open('some_unknown_hole')

    def test_labels(self):
        shape = [[0, 1], [1, 1]]
        holes = [['label', 'x', 'l', 'r'],
                 ['first_hole', 0.1, 0.1, 0.1],
                 ['second_hole', 0.2, 0.3, 0.5]]
        mm = InstrumentGeometry(shape, holes)
        self.assertEqual(mm.get_hole_labels(), ['first_hole', 'second_hole'])

        # Two holes with the same label
        bad_holes = [['label', 'x', 'l', 'r'],
                 ['one',   0.5, 0.1, 0.2],
                 ['one',   0.6, 0.2, 0.3]]
        with self.assertRaises(ValueError):
            mm = InstrumentGeometry(shape, bad_holes)

    def test_negative_radius(self):
        shape = [[0, 1], [0.2, -0.1]]
        with self.assertRaises(ValueError):
            mm = InstrumentGeometry(shape)

    def test_extract(self):
        shape = [[0, 0.1], [1, 0.2]]
        holes = [['label', 'x', 'l', 'r'],
                 ['first_hole', 0.1, 0.1, 0.01],
                 ['second_hole', 0.2, 0.3, 0.05]]
        x_cut = 0.15
        instru_geom = InstrumentGeometry(shape, holes)
        cut_geom = instru_geom.extract(x_cut, 2)
        self.assertAlmostEqual(instru_geom.get_main_bore_length(),
                               cut_geom.get_main_bore_length() + x_cut,
                               places=10)
        x_test = np.linspace(x_cut, instru_geom.get_main_bore_length(), 14)
        r_ori = instru_geom.get_main_bore_radius_at(x_test)
        r_cut = cut_geom.get_main_bore_radius_at(x_test)

        self.assertTrue(np.allclose(r_ori, r_cut, rtol=1e-14,
                                    atol=1e-14), msg='The slicing does not conserve the radius.')

    def test_extract_valve(self):
        shape = [[0, 0.1], [1, 0.2]]
        valves = [['label', 'variety', 'x', 'r', 'l', 'reconnection'],
                  ['piston1', 'valve', .1, 2e-3, 0.11, 0.15]]
        x_cut = 0.15
        instru_geom = InstrumentGeometry(shape, valves)
        cut_geom = instru_geom.extract(x_cut, 2)
        self.assertAlmostEqual(instru_geom.get_main_bore_length(),
                               cut_geom.get_main_bore_length() + x_cut,
                               places=10)
        x_test = np.linspace(x_cut, instru_geom.get_main_bore_length(), 14)
        r_ori = instru_geom.get_main_bore_radius_at(x_test)
        r_cut = cut_geom.get_main_bore_radius_at(x_test)

        self.assertTrue(np.allclose(r_ori, r_cut, rtol=1e-14,
                                    atol=1e-14), msg='The slicing does not conserve the radius.')
        # assert impossibiity to slice in the middle of a valve
        self.assertRaises(ValueError, instru_geom.extract, 0.12, 2)

    def test_add(self):
        shape1 = [[0, 0.1], [1, 0.2]]
        holes1 = [['label', 'variety', 'x', 'r', 'l', 'reconnection'],
                 ['first_hole', 'hole', 0.1, 0.1, 0.01, '/'],
                 ['second_valve', 'valve', 0.2, 0.3, 0.05, 0.22]]
        shape2 = [[0, 0.7, 0.1, 0.2, 'exponential']]
        holes2 = [['label', 'x', 'l', 'r'],
                 ['3rd_hole', 0.1, 0.1, 0.01]]
        geom1 = InstrumentGeometry(shape1, holes1)
        geom2 = InstrumentGeometry(shape2, holes2)
        geom_tot = geom1 + geom2

        self.assertEqual(len(geom_tot.holes) + len(geom_tot.valves), len(geom1.holes) + len(geom2.holes) + len(geom1.valves) + len(geom2.valves),
                         'The addition of geometries does not conserve the number of holes')
        self.assertEqual(geom_tot.get_main_bore_length(), geom1.get_main_bore_length() + geom2.get_main_bore_length(),
                         'The addition of geometries does not conserve the length')

    def test_extract_add(self):
        shape = [[0, 1, 0.01, 0.1, 'bessel', 0.2]]
        holes = [['label', 'x', 'l', 'r'],
                 ['first_hole', 0.1, 0.1, 0.01],
                 ['second_hole', 0.7, 0.3, 0.05]]
        geom = InstrumentGeometry(shape, holes)
        x_cut = 0.5
        slice1 = geom.extract(-np.inf, x_cut)
        slice2 = geom.extract(x_cut, np.inf)
        tot = slice1 + slice2

        x_test = np.linspace(0, geom.get_main_bore_length(), 10)

        r_ori = geom.get_main_bore_radius_at(x_test)
        r_tot = tot.get_main_bore_radius_at(x_test)

        self.assertTrue(np.allclose(r_ori, r_tot, rtol=1e-5, atol=1e-7),
                        msg='The slicing/addition does not conserve the radius.')

        pos_holes_ori = [hole.position.get_value() for hole in geom.holes]
        pos_holes_tot = [hole.position.get_value() for hole in tot.holes]


        self.assertTrue(np.all(pos_holes_ori == pos_holes_tot),
                        msg='The slicing/addition does not conserve the holes positions.')

    def test_bell_fing_chart(self):
        shape = [[0, 1], [1, 1]]
        holes = [['label', 'x', 'l', 'r'],
                 ['first_hole', 0.1, 0.1, 0.1],
                 ['second_hole', 0.2, 0.3, 0.5]]
        fing_chart = [['label', 'A', 'B'],
                      ['first_hole', 'x', 'o'],
                      ['bell', 'o', 'x']]
        mm = InstrumentGeometry(shape, holes, fing_chart)
        
    def test_single_file(self):
        separate = InstrumentGeometry(path + 'mkmodel_test2', path + 'bizarophone_holes', path + 'bizarophone_fingering_chart')
        separate.write_single_file(path + 'bizarophone_single_file_mm', unit='mm')
        single = InstrumentGeometry(path + 'bizarophone_single_file_mm.ow')
        
        x_test = np.linspace(0, single.get_main_bore_length(), 14)
        r_single = single.get_main_bore_radius_at(x_test)
        r_separate = separate.get_main_bore_radius_at(x_test)

        self.assertTrue(np.allclose(r_single, r_separate, rtol=1e-14,
                                    atol=1e-14), msg='The instrument from single or separate file are different.')

if __name__ == "__main__":
    unittest.main()
