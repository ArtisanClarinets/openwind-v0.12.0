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

from openwind.inversion import InverseFrequentialResponse
from openwind import (ImpedanceComputation, InstrumentGeometry, Player,
                      InstrumentPhysics)


frequencies = np.linspace(100, 500, 3)
temperature = 25
losses = True
player = Player()

class InversionConstrained(unittest.TestCase):
    """
    Test the inversion with constraints
    """

    def __init__(self, *args, **kwargs):
        super(InversionConstrained, self).__init__(*args, **kwargs)
        self.frequencies = np.linspace(100, 500, 3)
        self.temperature = 25
        self.losses = True
        self.player = Player()
        self.target_mb = [[0, 0.5, 2e-3, 20e-3, 'linear']]
        self.target_holes = [['label', 'position', 'radius', 'chimney'],
                             ['hole1', .25, 3e-3, 5e-3],
                             ['hole2', .35, 8e-3, 7e-3],
                             ['hole3', .45, 15e-3, 7e-3]
                            ]
        self.fingerings = [['label', 'A', 'B', 'C', 'D'],
                           ['hole1', 'x', 'x', 'o', 'o'],
                           ['hole2', 'x', 'o', 'x', 'o'],
                           ['hole3', 'o', 'x', 'x', 'x']]
        self.notes = ['A', 'B', 'C', 'D']


    def create_targets(self, N_holes):

        target_computation = ImpedanceComputation(self.frequencies,
                                                  self.target_mb,
                                                  self.target_holes[:2+N_holes],
                                                  self.fingerings[:2+N_holes],
                                                  temperature=self.temperature,
                                                  losses=self.losses)

        notes = target_computation.get_all_notes()
        if N_holes<1:
            notes = notes[0]

        Ztargets = list()
        for note in notes:
            target_computation.set_note(note)
            Ztargets.append(target_computation.impedance/target_computation.Zc)
        return Ztargets

    def test_length_constraint(self):
        inverse_geom = [[0, '0.25', 2e-3, 10e-3, 'linear'],
                        ['0.25', '~0.26', 20e-3, 10e-3, 'linear']]
        Lmax = 0.1
        instru_geom = InstrumentGeometry(inverse_geom)
        instru_phy = InstrumentPhysics(instru_geom, self.temperature, self.player, self.losses)
        inverse = InverseFrequentialResponse(instru_phy, self.frequencies, self.create_targets(0))

        my_shape = instru_geom.main_bore_shapes[1] # get the shape on which apply the constrain
        my_shape.create_length_constraint(Lmin=0, Lmax=np.inf) # create the constrain with the appropriate method
        instru_geom.constrain_parts_length(Lmax=Lmax)

        result = inverse.optimize_freq_model(algorithm='SLSQP')
        self.assertLess(my_shape.get_length(), Lmax, msg='The final length does not respect the constraint: '
                        '{} < {}'.format(my_shape.get_length(), Lmax))

    @unittest.skip("Test really too long!!")
    def test_spline_nodes_constraint(self):
        inverse_geom = [[0, '0<~0.25', 2e-3, 7.5e-3, 'linear'],
                        ['0<~0.25', '~.5', 7.5e-3, 20e-3, 'spline', '~0.26', '~0.28',12e-3, 10e-3]]

        instru_geom = InstrumentGeometry(inverse_geom) # instanciate the InstruGeom
        instru_phy = InstrumentPhysics(instru_geom, self.temperature, self.player, self.losses) # instanciate InstruPhy
        inverse = InverseFrequentialResponse(instru_phy, self.frequencies, self.create_targets(0)) # instanciate the InverseFreqResp

        Lmin = 1e-3
        my_spline = instru_geom.main_bore_shapes[1] # get the Main Bore shape on which apply the constrain
        my_spline.create_nodes_distance_constraints(Dmin=Lmin) # create the constrain => this is automatically added to the OptimParam object

        # Lmax = 1
        # instru_geom.constrain_parts_length(Lmin=Lmin) # creation from the `InstrumentGeometry` class
        result = inverse.optimize_freq_model(algorithm='SLSQP') # optimization with SLSQP algo

        nodes_dist = np.diff([X.get_value() for X in my_spline.X])
        self.assertTrue(np.all(nodes_dist>Lmin), 'The nodes distance cosntraint is not respected')


    def test_conicity_constraint(self):
        inverse_geom = [[0, '0.25', 2e-3, 10e-3, 'linear'],
                        ['0.25', '~0.37', 10e-3, '~16e-3', 'linear']]

        instru_geom = InstrumentGeometry(inverse_geom)
        instru_phy = InstrumentPhysics(instru_geom, self.temperature, self.player, self.losses)
        inverse = InverseFrequentialResponse(instru_phy, self.frequencies, self.create_targets(0))

        instru_geom.constrain_parts_length() # constrain the length to be positive
        my_cone = instru_geom.main_bore_shapes[1] # get the shape to constrain
        my_cone.create_conicity_constraint(Cmin=-np.inf, Cmax=np.inf, keep_constant=True) # create the constraint on conicity

        init_conicity = my_cone.get_conicity_at(0)

        result = inverse.optimize_freq_model(algorithm='SLSQP')

        self.assertAlmostEqual(init_conicity, my_cone.get_conicity_at(0), msg='The conicity constraint is not respected')

    @unittest.skip("Test too long")
    def test_hole_radius_pos_constraint(self):
        inverse_geom =  [[0, '0.05<~0.3', 2e-3, '0<~10e-3', 'linear']]
        inverse_hole = [['label', 'position', 'radius', 'chimney'],
                        ['hole1', '.05<~0.1%<.27', '1e-3<~1.75e-3%<2e-3', 5e-3],
                        ['hole2', '~0.22%', '~4e-3%', 7e-3]]
        instru_geom = InstrumentGeometry(inverse_geom, inverse_hole, self.fingerings[:3])
        instru_phy = InstrumentPhysics(instru_geom, self.temperature, self.player, self.losses)
        inverse = InverseFrequentialResponse(instru_phy, self.frequencies, self.create_targets(2), notes=self.notes)
        result = inverse.optimize_freq_model(algorithm='SLSQP')
        hole1 = instru_geom.holes[0]
        tol = 1e-7
        self.assertLess(hole1.position.get_value(), .27*(1+tol))
        self.assertLess(hole1.shape.get_radius_at(0), 2e-3*(1+tol))
        self.assertGreater(hole1.position.get_value(), 5e-2*(1-tol))

    def test_hole_centers_distance(self):
        inverse_hole = [['label', 'position', 'radius', 'chimney'],
                        ['hole1', '0<~.25<.5', 2.5e-3, 5e-3],
                        ['hole2', '~.30%', 2.5e-3, 7e-3],
                        ['hole3', '0<~.35<.5', 2.5e-3, 7e-3]
                        ]
        instru_geom = InstrumentGeometry(self.target_mb, inverse_hole, self.fingerings)
        instru_geom.constrain_all_holes_distance(Lmin=1e-2, Lmax=0.07)
        instru_phy = InstrumentPhysics(instru_geom, self.temperature, self.player, self.losses)
        inverse = InverseFrequentialResponse(instru_phy, self.frequencies, self.create_targets(3), notes=self.notes)
        result = inverse.optimize_freq_model(algorithm='SLSQP')
        tol = 1e-7
        self.assertLess(instru_geom.holes[1].position.get_value() - instru_geom.holes[0].position.get_value(), .07*(1+tol))
        self.assertLess(instru_geom.holes[2].position.get_value() - instru_geom.holes[1].position.get_value(), .07*(1+tol))

    @staticmethod
    def edges_distances(hole1, hole2):
        return hole2.position.get_value() - hole2.shape.get_radius_at(0) - hole1.position.get_value() - hole1.shape.get_radius_at(0)

    @unittest.skip("Test too long")
    def test_hole_edges_distance(self):
        inverse_hole = [['label', 'position', 'radius', 'chimney'],
                        ['hole1', '0<~.25<.5', 2.5e-3, 5e-3],
                        ['hole2', '~.30%', 2.5e-3, 7e-3],
                        ['hole3', '0<~.35<.5', '~10e-3%', 7e-3]
                        ]
        instru_geom = InstrumentGeometry(self.target_mb, inverse_hole, self.fingerings)
        instru_geom.constrain_all_holes_distance(Lmin=1e-2, Lmax=0.07, edges=True)
        instru_geom.constrain_2_holes_distance('hole1', 'hole3', Lmin=1e-2, Lmax=0.1, edges=True)

        instru_phy = InstrumentPhysics(instru_geom, self.temperature, self.player, self.losses)
        inverse = InverseFrequentialResponse(instru_phy, self.frequencies, self.create_targets(3), notes=self.notes)
        result = inverse.optimize_freq_model(algorithm='SLSQP')
        tol = 1e-7
        self.assertLess(self.edges_distances(instru_geom.holes[0], instru_geom.holes[1]), .09*(1+tol))
        self.assertLess(self.edges_distances(instru_geom.holes[1], instru_geom.holes[2]), .09*(1+tol))
        self.assertLess(self.edges_distances(instru_geom.holes[0], instru_geom.holes[2]), .15*(1+tol))

if __name__ == '__main__':
    unittest.main()
    # suite = unittest.TestSuite()
    # import time
# =============================================================================
#     # good
# =============================================================================
    # suite.addTest(InversionConstrained("test_length_constraint"))
    # suite.addTest(InversionConstrained("test_hole_centers_distance"))
    # suite.addTest(InversionConstrained("test_conicity_constraint"))
# =============================================================================
#     # BAD
# =============================================================================
    # suite.addTest(InversionConstrained("test_hole_edges_distance"))
# =============================================================================
#     # really Bad
# =============================================================================
    # suite.addTest(InversionConstrained("test_hole_radius_pos_constraint"))
    # suite.addTest(InversionConstrained("test_spline_nodes_constraint"))
    # runner = unittest.TextTestRunner()
    # t0 = time.time()
    # runner.run(suite)
    # print(time.time()-t0)
