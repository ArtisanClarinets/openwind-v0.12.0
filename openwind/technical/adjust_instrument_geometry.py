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

import numpy as np
import warnings
import matplotlib.pyplot as plt
from scipy.optimize import least_squares, minimize, Bounds

from openwind.technical import InstrumentGeometry
# from openwind.algo_optimization import LevenbergMarquardt


class AdjustInstrumentGeometry:
    """
    Adjust one instrument geometry on another one.

    The adjustement of the two
    :py:class:`InstrumentGeometry <openwind.technical.instrument_geometry.InstrumentGeometry>`
    is based only on geometrical aspects. The norm of the deviation between the
    radius at the same points is minimized.

    .. warning::
        - Only the main bore is adjusted.
        - The two main bore pipes must have the same total length.

    Parameters
    ----------

    mm_adjust: :py:class:`InstrumentGeometry \
    <openwind.technical.instrument_geometry.InstrumentGeometry>`
        The geometry which must be adjusted (typically the simplest one)

    mm_target: :py:class:`InstrumentGeometry \
    <openwind.technical.instrument_geometry.InstrumentGeometry>`
        The target geometry, typically the more complex as a measured one

    """

    def __init__(self, mm_adjust, mm_target):
        ltot1 = mm_target.get_main_bore_length()
        ltot2 = mm_adjust.get_main_bore_length()
        if not np.isclose(ltot1, ltot2):
            raise ValueError("The two geometry must have the same total"
                             " length! Here {:.2e} and {:.2e}"
                             .format(ltot1, ltot2))
        self.x_evaluate = np.arange(0, ltot2, 5e-4)
        self.mm_adjust = mm_adjust
        self.mm_target = mm_target

    def _get_radius_mm(self, instrument_geometry):
        """
        Get the radius of the considered geometry at the position x_evaluate.

        Parameters
        ----------
        instrument_geometry : :py:class:`InstrumentGeometry \
        <openwind.technical.instrument_geometry.InstrumentGeometry>`
            The geometry for which the radius is estimated.

        Returns
        -------
        radius : np.array
            The array of the radius values.

        """
        radius = np.zeros_like(self.x_evaluate)
        for shape in instrument_geometry.main_bore_shapes:
            x_min, x_max = shape.get_endpoints_position()
            x_norm = ((self.x_evaluate - x_min.get_value()) /
                      (x_max.get_value() - x_min.get_value()))
            x_in = np.where(np.logical_and(x_norm >= 0, x_norm <= 1))
            radius[x_in] = shape.get_radius_at(x_norm[x_in])
        return radius

    def _get_diff_radius_mm(self, diff_index):
        """
        The radius differentiation w.r. to one design parameter.

        Only the radius of the mm_adjust is needed and computed...

        Parameters
        ----------
        diff_index : int
            The index of the design parameter considered in `optim_params` of
            the adjusted :py:class:`InstrumentGeometry \
            <openwind.technical.instrument_geometry.InstrumentGeometry>`.

        Returns
        -------
        diff_radius : np.array
            The value of the differentiation at each point.

        """
        diff_radius = np.zeros_like(self.x_evaluate)
        for shape in self.mm_adjust.main_bore_shapes:
            x_min, x_max = shape.get_endpoints_position()
            x_norm = ((self.x_evaluate - x_min.get_value()) /
                      (x_max.get_value() - x_min.get_value()))
            x_in = np.where(np.logical_and(x_norm >= 0, x_norm <= 1))
            diff_radius[x_in] = shape.get_diff_radius_at(x_norm[x_in],
                                                         diff_index)
        return diff_radius

    def _compute_residu(self, radius_adjust, radius_target):
        """
        Compute the residue between the radii.

        It is simply the difference between the two radius vector.

        Parameters
        ----------
        radius_adjust : np.array
            The radius array corresponding to the adjusted geometry.
        radius_target : np.array
            The radius array corresponding to the target geometry.

        Returns
        -------
        np.array
            The residue vector.

        """
        return radius_adjust - radius_target

    def get_residual(self, params):
        """
        Compute the residual between the two geometries.

        Parameters
        ----------
        params : np.array, list
            The value of the design parameters for which must be estimated the
            cost, the gradient and the hessian.

        Returns
        -------
        residual : array
            The residual.
        """
        self.mm_adjust.optim_params.set_active_values(params)
        radius_target = self._get_radius_mm(self.mm_target)
        radius_adjust = self._get_radius_mm(self.mm_adjust)
        residual = self._compute_residu(radius_adjust, radius_target)
        return residual

    def get_jacobian(self, params):
        """
        The jacobian of the residual.

        Parameters
        ----------
        params : np.array, list
            The value of the design parameters for which must be estimated the
            cost, the gradient and the hessian.

        Returns
        -------
        jacob : np.array
            The jacobian.
        """
        self.mm_adjust.optim_params.set_active_values(params)
        nderiv = len(self.mm_adjust.optim_params.get_active_values())
        jacob = np.zeros([len(self.x_evaluate), nderiv])
        for diff_index in range(nderiv):
            jacob[:, diff_index] = self._get_diff_radius_mm(diff_index)
        return jacob

    def _get_cost_grad_hessian(self, params):
        """
        Compute the cost, the gradient and the hessian of the problem.

        Parameters
        ----------
        params : np.array, list
            The value of the design parameters for which must be estimated the
            cost, the gradient and the hessian.

        Returns
        -------
        cost : float
            The cost.
        gradient : np.array
            The gradient vector.
        hessian : np.array
            The hessian matrix.

        """
        residual = self.get_residual(params)
        jacobian = self.get_jacobian(params)
        cost = 0.5*np.linalg.norm(residual)**2
        gradient = jacobian.T.dot(residual)
        hessian = jacobian.T.dot(jacobian)
        return cost, gradient#, hessian

    def optimize_geometry(self, max_iter=100, minstep_cost=1e-8, tresh_grad=1e-10,
                     iter_detailed=False):
        """
        Minimize the radius deviation between the two geometries.

        The minimmization used the Levenberg-Marquardt algorithm to reduce
        the mean-square deviation between the radius of the two geometries.

        Parameters
        ----------
        max_iter : int, optional
            The maximal number of iteration. The default is 100.
        minstep_cost : float, optional
            The minimal realtive evolution of the cost. The default is 1e-8.
        tresh_grad : float, optional
            The minimal value of the gradient. The default is 1e-10.
        iter_detailed : boolean, optional
            If the detail of each iteration is printed. The default is False.

        Returns
        -------
        :py:class:`InstrumentGeometry <openwind.technical.instrument_geometry.InstrumentGeometry>`
            The adjusted geometry

        """
        lb, ub = tuple(zip(*self.mm_adjust.optim_params.get_active_bounds()))
        cons = self.mm_adjust.optim_params.get_active_constraints_for_algo('SLSQP')
        if all(np.isinf(lb+ub)) and len(cons)==0:
            algo = 'lm'
        elif len(cons)==0:
            algo = 'trf'
        else:
            algo = 'SLSQP'
        if algo in ['lm', 'trf']:
            result = least_squares(self.get_residual,
                               self.mm_adjust.optim_params.get_active_values(),
                               jac=self.get_jacobian, bounds=(lb, ub),
                               verbose=1, method=algo, ftol=minstep_cost,
                               max_nfev=max_iter, gtol=tresh_grad)
            print('Residual error; {:.2e}'.format(result.cost))
        else:
            bounds_obj = Bounds(lb, ub, keep_feasible=True)
            options = {'disp': True, 'maxiter': max_iter, 'ftol': minstep_cost}
            result = minimize(self._get_cost_grad_hessian,
                              self.mm_adjust.optim_params.get_active_values(),
                              method=algo, jac=True, bounds=bounds_obj,
                              options=options, constraints=cons)
            print('Residual error; {:.2e}'.format(result.fun))
        # result = LevenbergMarquardt(self._get_cost_grad_hessian,
        #                                   self.mm_adjust.optim_params.values,
        #                                   max_iter, minstep_cost,
        #                                   tresh_grad, iter_detailed)

        return self.mm_adjust



def protogeometry_design(start, end, segments=[], N_subsegments=[], types=['cone'],
                         r_start=None, r_end=None, target_geom=None):
    """
        Easy creation of a proto-geometry to be optimized.

        By default, all the parameters, are variables (positions, radii and
        additional parameters (e.g., alpha parameter for Bessel types) as well).

        Parameters
        ----------
        start : int, float
            Starting point of the geometry (fixed position).

        end : int, float
            End point of the geometry.

        segments : list of integers or list of floats
            Fixed position of different segments.

        N_subsegments : list of integers
            Number of floating subsegments for each segment.

        types : list of strings or lists
            Types of floating subsegments.
            Length must match the number of segments, each element of the list
            corresponds to a segment.
            If an element is a string, all subsegments in corresponding segment
            will be of the type descibed by that string ;
            If an element is a list, its length must match the number of
            subsegment in the corresponding segment.

            Possible types are : 'linear', 'circle', 'exponential', 'bessel',
            'spline' and 'splineX', where X is an integer and describes the
            number of knots in the spline.
            'spline' is equivalent to 'spline3' and describes a spline with a
            starting point/knot, an ending point/knot, and a knot in the
            middle (3 knots in total)

        Returns
        -------
        List describing the main bore of an instrument geometry.

    """


    Nseg = len(segments) + 1 # number of segments

    # set the number of subsegments
    if isinstance(N_subsegments, int):
        N_subsegments = [N_subsegments] * Nseg
    elif len(N_subsegments) == 0:
        N_subsegments = [1] * Nseg
    elif len(N_subsegments) == 1:
        N_subsegments = N_subsegments * Nseg
    elif len(N_subsegments) != Nseg:
        raise ValueError('length of N_subsegments must match the number of '+
                        'segments, or be equal to 1 (describing all segments).')

    # set segment type
    if isinstance(types, str):
        types = [types] * Nseg
    elif len(types) == 1:
        types = types * Nseg
    elif len(types) != Nseg:
        raise ValueError('length of types must match the number of '+
                        'segments, or be equal to 1 (describing all segments).')

    # set subsegment type
    for ii, t in enumerate(types):
        if isinstance(t, list) and len(t) == N_subsegments[ii]:  # type is list, length matches
            pass
        elif isinstance(t, str):
            types[ii] = [t] * N_subsegments[ii]  # type is string
        elif len(types[ii]) == 1:
            types[ii] = t * N_subsegments[ii]  # type is list of length 1
        else:
            raise ValueError('type must be a list of strings or lists.')

    sec_pos = []
    fixed_points = [start, *segments, end]
    for ii in range(Nseg):
        sec_pos.append(np.linspace(fixed_points[ii],
                                   fixed_points[ii+1],
                                   N_subsegments[ii]+1))

    if target_geom is not None:
        rad = target_geom.get_main_bore_radius_at

    proto_geom = list()
    if r_start:
        Rr = float(r_start)
    else:
        Rr = 5e-3

    for ii in range(len(sec_pos)):
        for jj in range(N_subsegments[ii]):
            seg_type = types[ii][jj]

            xL, xR = (sec_pos[ii][jj], sec_pos[ii][jj+1])
            shape_pos = [f'~{xL}', f'~{xR}']

            if target_geom is None:
                Rl=Rr
                if seg_type == 'bessel': # bessel does not accept cylindrical shape
                    Rr*=2
            else:
                Rl = rad(xL)
                Rr = rad(xR)
            shape_radius = [f'0<~{Rl}', f'0<~{Rr}']

            if seg_type in ['linear', 'cone', 'exponential']:
                shape_params = [seg_type]  # [r1, r2]
            elif seg_type == 'circle':
                circle_radius = (xR-xL) # by default twice the minimal radius
                shape_params = ['circle', f'~-{circle_radius}']  # [y1, y2, R]
            elif seg_type == 'bessel':  # alpha will be variable
                shape_params = ['bessel', '0.1<~1<2']  # [r1, r2, alpha]
            elif seg_type[:6] == 'spline':
                if seg_type == 'spline':
                    Nspline = 3
                else:
                    try:
                        Nspline = int(seg_type[6:])
                    except ValueError:
                        raise ValueError(str(seg_type) + ' is not of type ' +
                                         'splineX, where X is an integer.')
                shape_params = ['spline']  # [r1, r2]
                spline_pos = [str(kk) for kk in np.linspace(xL, xR, Nspline)[1:-1]]
                if target_geom is None:
                    spline_rad = [str(kk) for kk in np.linspace(Rl, Rr, Nspline)[1:-1]]
                else:
                    spline_rad = [str(rad(kk)) for kk in np.linspace(xL, xR, Nspline)[1:-1]]
                shape_params.extend([f'~{kk}' for kk in spline_pos])
                shape_params.extend([f'0<~{kk}' for kk in spline_rad])
            else:
                raise ValueError(f'Unknown type: {seg_type}')

            proto_geom.append(shape_pos + shape_radius + shape_params)

    # deal with start/end
    proto_geom[0][0] = proto_geom[0][0].replace('~','') #input position not variable.
    if r_start:
        proto_geom[0][2] = str(r_start)
    if r_end:
        proto_geom[-1][3] = r_end
    isntru_geom = InstrumentGeometry(proto_geom)
    # add positive length constraints (and spline nodes order)
    isntru_geom.constrain_parts_length()
    return isntru_geom

if __name__ == '__main__':
    """
    An example for which a spline with 4 points is adjusted on a geometry
    composed of 10 conical parts.
    """
    # the target geometry composed of ten conical parts
    x_targ = np.linspace(0, .1, 10)
    r_targ = np.linspace(5e-3, 1e-2, 10) - 2e-3*np.sin(x_targ*2*np.pi*10)
    Geom = np.array([x_targ, r_targ]).T.tolist()
    mm_target_test = InstrumentGeometry(Geom)

    # the geometry which will be adjusted
    mm_adjust_test = InstrumentGeometry([[0, .1, 5e-3, '~5e-3', 'spline',
                                          '.03', '.06', '~7e-3', '~4e-3']])

    # plot initial state
    fig = plt.figure()
    mm_target_test.plot_InstrumentGeometry(figure=fig, label='target')
    mm_adjust_test.plot_InstrumentGeometry(figure=fig, label='initial',
                                           linestyle='--')

    # the optimization
    test = AdjustInstrumentGeometry(mm_adjust_test, mm_target_test)
    adjusted = test.optimize_geometry(iter_detailed=True)

    # plot final state
    adjusted.plot_InstrumentGeometry(figure=fig, label='final', linestyle=':')
