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
Created on Mon Jun 19 14:55:02 2023

@author: alexis
"""

import numpy as np
from numpy import sqrt, diag
import numpy.linalg
from scipy.linalg import block_diag

import warnings

from openwind.discretization import DiscretizedPipe
from openwind.temporal import TemporalComponent


class TemporalTonehole(TemporalComponent):
    """Implicit scheme for simulation of Junction + Pipe + Radiation."""

    def __init__(self, tonehole, ends, t_solver=None, **discr_params):
        TemporalComponent.__init__(self, tonehole, t_solver)
        print("Using implicit tonehole!")
        warnings.warn('The use of implicit scheme for the tonehole is not yet really robust.'
                      'In particular this can fail if the holes are opening state of the hole varies during the simulation.')
        self._end1, self._end2 = ends

        self._opening_factor = 1.0

        self.junct, self.pipe, self.rad = tonehole.junct, tonehole.pipe, tonehole.rad

        # Compute all the matrices needed (junction mass+interconnexion,
        # pipe mass+gradient+endpoint matrices, radiation coefficients)

        # Junction matrices
        self.update_junction_coef()

        # Pipe FEM matrices
        self.update_pipe_coef(**discr_params)

        # Radiation coefficients
        self.update_rad_coefficients()

        self.Xsize = self.nL2 + self.nH1 + 2 + 1
        self.Uextsize = 2
        self.Uinsize = 4

        self.set_matrices_no_rad()
        self.set_matrices_rad()

    def set_matrices_rad(self):
        """
        Set matrices dependent to radiating condition (alpha, beta)

        Returns
        -------
        None.

        """
        nH1, nL2 = self.nH1, self.nL2
        M_J, T_J, E_3, E_12 = self.junction_matrices

        # Endpoint evaluation vectors E_-, E_+
        E_mp = np.zeros((nL2 + nH1, 2))
        E_mp[nL2, 0] = 1
        E_mp[-1, 1] = 1

        # Assemble the matrices

        self.Gin = np.block(
            [[-E_mp, np.zeros((nL2+nH1, 2))],
             [np.zeros((2, 2)), -T_J @ E_3, np.zeros((2,1))],
             [np.zeros((1,3)), np.array([[-sqrt(self.alpha)]])]])

        self.Rin = np.diag([0,0,0,self.beta/self.Zplus])

        assert self.Gin.shape == (self.Xsize, self.Uinsize)
        assert self.Rin.shape == (self.Uinsize, self.Uinsize)
        self._should_recompute_coefs = True

    def set_matrices_no_rad(self):
        """
        Set matrices independent of radiating condition (alpha, beta)


        """
        nH1, nL2 = self.nH1, self.nL2
        M_J, T_J, E_3, E_12 = self.junction_matrices


        # Assemble the matrices

        self.M = block_diag(diag(self.M_V), diag(self.M_P), M_J, np.array([[self.Zplus]]))

        # Check that the mass matrix is positive definite
        w, _ = numpy.linalg.eig(self.M)
        assert all(w > 0)

        self.J = np.block(
            [[np.zeros((nL2, nL2)),                  -self.Bh, np.zeros((nL2, 3))],
             [      self.Bh.T, np.zeros((nH1, nH1)), np.zeros((nH1, 3))],
             [  np.zeros((3, nL2)),   np.zeros((3, nH1)),    np.zeros((3,3))]])

        assert np.all(self.J.T == -self.J)


        self.Gext = np.block(
            [[np.zeros((nL2+nH1, 2))], [-T_J @ E_12], [np.zeros((1,2))]])


        self.Jin = np.array([[ 0, 0, 1, 0],
                             [ 0, 0, 0, 1],
                             [-1, 0, 0, 0],
                             [ 0,-1, 0, 0]])

        assert np.all(self.Jin.T == -self.Jin)

        assert self.M.shape == (self.Xsize, self.Xsize)
        assert self.Gext.shape == (self.Xsize, self.Uextsize)
        assert self.Jin.shape == (self.Uinsize, self.Uinsize)

        self.X = np.zeros(self.Xsize)


    def update_junction_coef(self):
        rho = self.pipe.get_physics().get_coefs(0, 'rho')[0]
        r_main = self._end1.t_pipe.pipe.get_radius_at(1)
        r_side = self.pipe.get_radius_at(0)
        m11, m12, m22 = self.junct.compute_passive_masses(r_main, r_side, rho)

        M_J = np.array([[m11,m12],[m12,m22]])
        T_J = np.array([[-1,0,1],[0,-1,1]])
        E_3 = np.array([[0],[0],[1]])
        E_12 = np.block([[np.eye(2)], [np.zeros((1,2))]])

        self.junction_matrices = (M_J, T_J, E_3, E_12)

    def update_pipe_coef(self, **discr_params):
        dpipe = DiscretizedPipe(self.pipe, **discr_params)
        self.M_V, self.M_P = dpipe.get_mass_matrices()
        self.Bh = dpipe.get_Bh().todense()
        self.nH1 = dpipe.nH1
        self.nL2 = dpipe.nL2

    def update_rad_coefficients(self):
        rho, c = self.pipe.get_physics().get_coefs(1, 'rho', 'c')
        r_rad = self.pipe.get_radius_at(1)
        alpha, beta, Zplus = self.rad.compute_temporal_coefs(r_rad, rho, c, self._opening_factor)
        assert Zplus > 0
        assert beta >= 0
        self.alpha, self.beta, self.Zplus = alpha, beta, Zplus

    def set_opening_factor(self, opening_factor):
        """Control opening and closing of the hole.

        Can be used during simulation. Energy-safe, as it only modifies
        the strength of the interaction with the tube.

        Parameters
        ----------
        opening_factor : float
            1 for an open hole, 0 for a closed hole, or any value in-between
            for a partly-closed hole
        """
        # Only update the factor if it changed significantly : too expensive (5,92 sec pour set_op contre 4,44)
        if not (abs(opening_factor - self._opening_factor) < 1e-5):
        #    np.isclose(opening_factor, self._opening_factor, atol=1e-5):
            self._opening_factor = opening_factor
            old_Zplus = self.Zplus
            self.update_rad_coefficients()
            assert self.Zplus == old_Zplus  # Zplus is not allowed to change!
            self.set_matrices_rad()


    def set_dt(self, dt):
        self.dt = dt
        self._should_recompute_coefs = True


    def _precompute_coefficients(self):

        dt = self.dt
        self.Aext = np.diag([self._end1.get_alpha(), self._end2.get_alpha()])
        assert self.Aext.shape == (self.Uextsize, self.Uextsize)

        # Assemble the matrix used in the left hand side of the update equation
        self.Lmat = np.block(
            [[self.M - dt/2*self.J,    -self.Gin,    -self.Gext @ self.Aext],
             [ dt/2*self.Gin.T,      self.Jin+self.Rin, np.zeros((4,2))],
             [ dt/2*self.Gext.T,     np.zeros((2,4)), np.eye(2)]])

        # NB: if we change the radiation coefficients, we must invert Lmat again!
        self.Lmatinv = numpy.linalg.inv(self.Lmat)

        # Assemble the right hand side matrix of the update equation
        self.RHSmat = np.block([[self.J, self.Gext],
                              [-self.Gin.T, np.zeros((4,2))],
                              [-self.Gext.T, np.zeros((2,2))]])

        # Calculate the matrix needed for the update
        self.updatemat = self.Lmatinv @ self.RHSmat
        # Initialize state variable
        self.Xn = np.zeros((self.Xsize,1))
        self._should_recompute_coefs = False

    def one_step(self):

        if self._should_recompute_coefs:
            self._precompute_coefficients()

        Uext_n = np.array([[self._end1.get_p_no_flow()], [self._end2.get_p_no_flow()]])
        b = np.block([[self.Xn], [Uext_n]])

        # Solve the linearly implicit relation
        sol = self.updatemat @ b

        # Extract the solution data
        deltaX = sol[0:self.Xsize]
        Xnp1 = self.Xn + self.dt*deltaX
        self.Uin = sol[self.Xsize:-2]
        Yext = sol[-2:]
        lambda_nph = -Yext

        # ========== DEBUG ==========
        # Check that the scheme is implemented correctly
        # Uext_nph = Uext_n + self.Aext*Yext
        # left1 = self.M @ (Xnp1 - self.Xn)/dt
        # right1 = self.J @ (Xnp1 + self.Xn)/2 + self.Gin @ Uin + self.Gext @ Uext_nph
        # err1 = np.max(abs(right1-left1))/np.max(abs(left1))
        # left2 = self.Jin @ Uin
        # right2 = -self.Gin.T @ (Xnp1 + self.Xn)/2 - self.Rin @ Uin
        # err2 = np.max(abs(right2-left2))/np.max(abs(left2))
        # left3 = Yext
        # right3 = -self.Gext.T @ (Xnp1 + self.Xn)/2
        # err3 = np.max(abs(right3-left3))/np.max(abs(left3))

        # # print(f"err1 = {err1:.5e}, err2 = {err2:.5e}, err3 = {err3:.5e}")
        # # if max(err1, err2, err3) > 1e-11:
        # #     raise ValueError("Error on scheme residual")

        # # Check the energy balance equation
        # En = 1/2 * self.Xn.T @ self.M @ self.Xn
        # Enp1 = 1/2 * Xnp1.T @ self.M @ Xnp1
        # deltaE = (Enp1 - En)/dt



        # err_nrj = float(abs(deltaE - (work - dissip)) / Enp1)
        # print(f"err_nrj = {err_nrj:.5e}")
        # if err_nrj > 1e-8:
        #     raise ValueError("Error on energy balance")
        # ========== /DEBUG ==========



        # Update the lagrange multipliers and state variable
        # print(lambda_nph)
        self._end1.update_flow(lambda_nph[0,0])
        self._end2.update_flow(lambda_nph[1,0])

        # ====== DEBUG ======
        # Check that the pipe-end pressure agrees with what we want
        # err_end1 = abs(Uext_nph[0] - self._end1.get_q_nph())/(abs(Uext_nph[0])+1e-100)
        # err_end2 = abs(Uext_nph[1] - self._end2.get_q_nph())/(abs(Uext_nph[1])+1e-100)
        # assert err_end1 < 1e-12, err_end1
        # assert err_end2 < 1e-12
        # ====== /DEBUG ======

        self.Xn = Xnp1

    def energy(self):
        return 1/2 * float(self.Xn.T @ self.M @ self.Xn)

    def dissipated_last_step(self):
        # work = -Uext_nph.T @ Yext
        dissip = float(self.Uin.T @ self.Rin @ self.Uin)
        # assert dissip >= 0
        self.dissip_last = dissip*self.dt
        return self.dissip_last

    def __str__(self):
        return "TemporalTonehole"

    def get_maximal_dt(self):
        return np.inf

    def reset_variables(self):
        self._should_recompute_coefs = True
        # raise NotImplementedError()
