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

from openwind.design import (FixedParameter, VariableParameter,
                             OptimizationParameters,
                             Cone, Spline, Bessel, Circle, Exponential,
                             ShapeSlice)

class DesignTest(unittest.TestCase):

    def assert_correct_values(self, shape, x, r, tol=1e-13, msg=None):
        """Make sure that the radii at given positions is r."""
        print(shape)
        x_norm = shape.get_xnorm_from_position(np.array(x))
        r_estimated = shape.get_radius_at(x_norm)
        error = np.max(np.abs(r_estimated - r))
        self.assertLess(error, tol, msg)

    def assert_correct_diff(self, shape, optim_params,
                            dv=5e-7, tol=1e-9):
        """Compare get_diff_radius with the rate of change of get_radius.

        Also test diff_radius_wr_x_norm if available.

        Make sure that
            (f(v+dv) - f(v-dv)) / (2*dv) = f'(v) +- tol
        for each possible optimization parameter v.
        """
        # Check get_diff_radius_at
        x = np.linspace(0, 1, 20)
        for i in range(len(optim_params.values)):
            r_prime = shape.get_diff_radius_at(x, i)

            v = optim_params.values[i]
            optim_params.values[i] = v + dv
            r_plus = shape.get_radius_at(x)
            optim_params.values[i] = v - dv
            r_minus = shape.get_radius_at(x)
            optim_params.values[i] = v

            slope = (r_plus - r_minus) / (2*dv)
            # plt.figure()
            # plt.plot(slope)
            # plt.plot(r_prime)
            err = np.max(np.abs(slope - r_prime))
            self.assertLess(err, tol, "diff_index="+str(i))

        # Check diff_radius_wr_x_norm if available
        try:
            x = np.linspace(dv, 1-dv, 20)
            dr_dx = shape.diff_radius_wr_x_norm(x)
            rm = shape.get_radius_at(x - dv)
            rp = shape.get_radius_at(x + dv)
            slope = (rp - rm) / (2*dv)
            err = np.max(np.abs(slope - dr_dx))
            self.assertLess(err, tol, "diff_radius_wr_x_norm")
        except NotImplementedError:
            pass

    def comp_shape_diff_conicity(self, shape, optim_params, rtol=1e-8,
                                 atol=1e-8):
        dv = 1e-7
        x_norm = np.linspace(0, 1, 10)
        for k, value in enumerate(optim_params.values):
             optim_params.values[k] = value + dv
             cp = shape.get_conicity_at(x_norm)
             optim_params.values[k] = value - dv
             cm = shape.get_conicity_at(x_norm)
             optim_params.values[k] = value
             c_FDM = (cp - cm)/(2*dv)
             c_ana = shape.get_diff_conicity_at(x_norm, k)
             msgD = 'Absolute error: {}'.format(np.array(c_FDM-c_ana))
             self.assertTrue(np.allclose(c_FDM, c_ana, rtol=rtol, atol=atol),
                             msg=msgD)

    def assert_diff_conicity_wr_x(self, shape, rtol=1e-8, atol=1e-8):
        dv = 1e-7
        x_norm = np.linspace(dv, 1-dv, 100)
        dcon_dx = shape.diff_conicity_wr_xnorm(x_norm)
        con_m = shape.get_conicity_at(x_norm - dv)
        con_p = shape.get_conicity_at(x_norm + dv)
        slope = (con_p - con_m) / (2*dv)
        msgD = 'Absolute error: {}'.format(np.array(slope-dcon_dx))
        self.assertTrue(np.allclose(slope, dcon_dx, rtol=rtol, atol=rtol),
                        msg=msgD)

    def test_cone(self):
        optim_params = OptimizationParameters()
        x_values, r_values = [0.79653412, 0.92612135], [0.11736642, 0.62053786]
        params = [VariableParameter(v, optim_params)
                  for v in x_values + r_values]
        cone = Cone(*params)
        self.assert_correct_diff(cone, optim_params)
        self.assert_correct_values(cone, x_values, r_values)
        self.comp_shape_diff_conicity(cone, optim_params)
        self.assert_diff_conicity_wr_x(cone)


    def test_spline(self):
        optim_params = OptimizationParameters()
        x_values = [0.1624749325963741, 0.387341043094921,
                    0.45770046812141096, 0.52044591332053053,
                    0.6786009844119112, 0.7859793259238746]
        r_values = [0.9284416 , 0.5700363,
                    0.81573615, 0.37675722,
                    0.33007408, 0.84520458]
        params = [VariableParameter(v, optim_params)
                  for v in x_values+r_values]
        spline = Spline(*params)
        self.assert_correct_diff(spline, optim_params)
        self.assert_correct_values(spline, x_values, r_values)
        self.comp_shape_diff_conicity(spline, optim_params)
        self.assert_diff_conicity_wr_x(spline)

    def test_bessel(self):
        optim_params = OptimizationParameters()
        values = [0.46297437, 0.70553924, 0.3369718 , 0.6169474]
        for alpha in [0.156745, 0.90017919, 1.90017919, 10.7919]:
            params = [VariableParameter(v, optim_params) for v in values+[alpha]]
            bessel = Bessel(*params)
            self.assert_correct_values(bessel, values[0:2], values[2:4],
                                       msg="alpha=%f.3"%alpha)
            # Ensure conicity is correct
            self.assert_correct_diff(bessel, optim_params, tol=1e-8)
            self.comp_shape_diff_conicity(bessel, optim_params, rtol=1e-7,
                                          atol=1e-7)
            self.assert_diff_conicity_wr_x(bessel, rtol=1e-7, atol=1e-7)

    def test_circle(self):
        optim_params = OptimizationParameters()
        values = [0.46297437, 0.70553924, 0.3369718 , 0.46169474]
        for circle_radius in [0.97394094, 5.84932719, -40.01186041]:
            params = [VariableParameter(v, optim_params) for v in values+[circle_radius]]
            circle = Circle(*params)
            self.assert_correct_diff(circle, optim_params, tol=1e-7)
            self.assert_correct_values(circle, values[0:2], values[2:4],
                                       msg="circle_radius=%f.3"%circle_radius)
            self.comp_shape_diff_conicity(circle, optim_params)
            self.assert_diff_conicity_wr_x(circle)

    def test_exponential(self):
        optim_params = OptimizationParameters()
        values = [0.11700419, 0.6032161, 0.19375763 , 0.46169474]
        params = [VariableParameter(v, optim_params) for v in values]
        exponential = Exponential(*params)
        self.assert_correct_diff(exponential, optim_params)
        self.assert_correct_values(exponential, values[0:2], values[2:4])
        self.comp_shape_diff_conicity(exponential, optim_params)
        self.assert_diff_conicity_wr_x(exponential)

    def test_slice(self):
        optim_params = OptimizationParameters()
        x_values = [0.1624749325963741, 0.387341043094921,
                    0.45770046812141096, 0.52044591332053053,
                    0.6786009844119112, 0.7859793259238746]
        r_values = [0.9284416 , 0.5700363,
                    0.81573615, 0.37675722,
                    0.33007408, 0.84520458]
        params = [VariableParameter(v, optim_params)
                  for v in x_values+r_values]
        spline = Spline(*params)

        x_range = [0.5176539, 0.7584416]
        X_range = [VariableParameter(v, optim_params) for v in x_range]
        shape_slice = ShapeSlice(spline, X_range)
        self.assert_correct_diff(shape_slice, optim_params)
        self.assert_correct_values(shape_slice, x_values[3:5], r_values[3:5])
        self.comp_shape_diff_conicity(shape_slice, optim_params)
        self.assert_diff_conicity_wr_x(shape_slice)


    def test_old(self):
        """Old test for some of the possible cases."""
        test_ok = True
        optim_params = OptimizationParameters()

        x_val = [0, 0.05, 0.075, 0.1, 0.15]
        r_val = [.004, .001, .01, .003, .005]

        # Build a conical furstum where the second radius is variable
        Xcone = [FixedParameter(x) for x in x_val[:2]]
        Rcone = [FixedParameter(r_val[0])]
        Rcone.append(VariableParameter(r_val[1], optim_params))
        Part_cone = Cone(*(Xcone+Rcone))

        # Build a spline where the first point is shared with the conical part and
        # where the second position is variable
        Xspline = [Xcone[1]]
        Xspline.append(VariableParameter(x_val[2], optim_params))
        Xspline.append(FixedParameter(x_val[3]))
        Xspline.append(FixedParameter(x_val[4]))

        Rspline = [Rcone[1]]
        Rspline.append(FixedParameter(r_val[2]))
        Rspline.append(FixedParameter(r_val[3]))
        Rspline.append(FixedParameter(r_val[4]))
        Part_spline = Spline(*(Xspline+Rspline))

        # Compute the radii along the axis
        x = np.linspace(0, 1, 1000, endpoint=False)
        r_cone = Part_cone.get_radius_at(x)
        r_spline = Part_spline.get_radius_at(x)

        # Differentiate with respect to the shared radius
        dr = 1e-8
        optim_params.values[0] += dr
        r_cone1 = Part_cone.get_radius_at(x)
        r_spline1 = Part_spline.get_radius_at(x)
        optim_params.values[0] += -dr

        finite_diff_r_cone = (r_cone1-r_cone)/dr
        finite_diff_r_spline = (r_spline1-r_spline)/dr

        dr_cone = Part_cone.get_diff_radius_at(x, 0)
        dr_spline = Part_spline.get_diff_radius_at(x, 0)

        err_cone = dr_cone - finite_diff_r_cone
        err_spline = dr_spline - finite_diff_r_spline

        if np.max(np.abs(err_cone)) > 1e-9:
            test_ok = False
            print("The derivative of the cone radii is wrong.")
        if np.max(np.abs(err_spline)) > 1e-9:
            test_ok = False
            print("The derivative of the spline radii with respect to one radius is wrong.")

        # Differentiate with respect to the position of a construction point of the spline

        dx = 1e-8
        optim_params.values[1] += dx
        r_cone_dx = Part_cone.get_radius_at(x)
        r_spline_dx = Part_spline.get_radius_at(x)
        optim_params.values[1] += -dx

        optim_params.values[1] += -dx
        r_cone_dx_back = Part_cone.get_radius_at(x)
        r_spline_dx_back = Part_spline.get_radius_at(x)
        optim_params.values[1] += dx

        finite_diff_r_cone_dx = (r_cone_dx-r_cone_dx_back)/(2*dx)
        finite_diff_r_spline_dx = (r_spline_dx-r_spline_dx_back)/(2*dx)

        dr_cone_dx = Part_cone.get_diff_radius_at(x, 1)
        dr_spline_dx = Part_spline.get_diff_radius_at(x, 1)

        err_cone_dx = dr_cone_dx - finite_diff_r_cone_dx
        err_spline_dx = dr_spline_dx - finite_diff_r_spline_dx

        if np.max(np.abs(err_cone_dx)) > 1e-9:
            test_ok = False
            print("The derivative of the cone radii is wrong.")
        if np.max(np.abs(err_spline_dx)) > 1e-9:
            test_ok = False
            print("The derivative of the spline radii with respect to the position of one parameter point is wrong.")

        self.assertTrue(test_ok)




if __name__ == '__main__':
    unittest.main()
