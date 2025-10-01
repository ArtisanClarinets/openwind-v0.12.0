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
from numpy.polynomial import polynomial as P

from openwind.algo_optimization import (Steepest, LevenbergMarquardt,
                                                  GaussNewton, QuasiNewtonBFGS)

# %% probleme 1D
print('----------------\n 1D-optimization \n ----------------')

x_init = np.array([10])
x_0 = 3.2
A = 10
B = 5
# A(x-x_0)**2 + B
coef = [A*x_0**2 + B, -2*x_0*A, A]
def get_cost_grad_1D(x):
    value = P.Polynomial(coef)
    gradient = P.Polynomial(P.polyder(coef))
    cost = 0.5*(value(x)[0] - B)**2
    return cost, gradient(x)

def get_cost_grad_hessian_1D(x):
    cost, gradient = get_cost_grad_1D(x)
    deriv_second = P.Polynomial(P.polyder(coef, m=2))
    hessian = np.array([[deriv_second(x)[0]]])
    return cost, gradient, hessian

print("\nLevenberg-Marquardt:")
res_LM = LevenbergMarquardt(get_cost_grad_hessian_1D, x_init, disp=False)
deviation_cost_LM = res_LM.cost
deviation_param_LM = (res_LM.x[0] - x_0)/x_0
n_iter_LM = res_LM.nit
if n_iter_LM > 5 or deviation_cost_LM > 1e-20:
    raise ValueError('Levenberg-Marquardt does not process correctly.')

print("\nGauss-Newton:")
res_GN = GaussNewton(get_cost_grad_hessian_1D, x_init, disp=False)
deviation_cost_GN = res_GN.cost
deviation_param_GN = (res_GN.x[0] - x_0)/x_0
n_iter_GN = res_GN.nit
if n_iter_GN > 1 or deviation_cost_GN > 1e-20:
    raise ValueError('Gauss-Newton does not process correctly.')

print("\nQuasi-Newton BFGS / linesearch:")
res_QN = QuasiNewtonBFGS(get_cost_grad_1D, x_init, steptype='linesearch', disp=False)
deviation_cost_QN = res_QN.cost
deviation_param_QN = (res_QN.x[0] - x_0)/x_0
n_iter_QN = res_QN.nit
if n_iter_QN > 2 or deviation_cost_QN > 1e-20:
    raise ValueError('Quasi-Newton BFGS (linesearch) does not process correctly.')

print("\nQuasi-Newton BFGS / Back-tracking")
res_QN_BT = QuasiNewtonBFGS(get_cost_grad_1D, x_init, disp=False, steptype='backtracking')
deviation_cost_QN_BT = res_QN_BT.cost
deviation_param_QN_BT = (res_QN_BT.x[0] - x_0)/x_0
n_iter_QN_BT = res_QN_BT.nit
if n_iter_QN_BT > 10 or deviation_cost_QN_BT > 1e-7:
    raise ValueError('Quasi-Newton BFGS (Back-tracking) does not process correctly.')

print("\nSteepest descend / linesearch:")
res_steep = Steepest(get_cost_grad_1D, x_init, steptype='linesearch', disp=False)
deviation_cost_steep = res_steep.cost
deviation_param_steep = (res_steep.x[0] - x_0)/x_0
n_iter_steep = res_steep.nit
if n_iter_steep > 2 or deviation_cost_steep > 1e-7:
    raise ValueError('Steepes descend (linesearch) does not process correctly.')

print("\nSteepes descend / Back-tracking")
res_steep_BT = Steepest(get_cost_grad_1D, x_init, disp=False, steptype='backtracking')
deviation_cost_steep_BT = res_steep_BT.cost
deviation_param_steep_BT = (res_steep_BT.x[0] - x_0)/x_0
n_iter_steep_BT = res_steep_BT.nit - 1

# %% Probleme ND
N = 10
print('\n----------------\n {:d}D-optimization \n----------------'.format(N))
np.random.seed(42)
Mrand = np.random.normal(size=(N, N))
quadM = Mrand.T.dot(Mrand)
#print(quadM)

#quadM = np.array([[3.19028313, 2.73104755],
#               [2.73104755, 2.72095267]])


def get_cost_gradient_ND(x):
    cost = 0.5*(x.T.dot(quadM.dot(x)))
    gradient = quadM.dot(x)
    return cost, gradient

def get_cost_gradient_hessian_ND(x):
    cost, gradient = get_cost_gradient_ND(x)
    return cost, gradient, quadM

#x_init = np.array([0.56938285, 0.36907012])
x_init = np.random.normal(size=N)

print("\nLevenberg-Marquardt")
res_LM = LevenbergMarquardt(get_cost_gradient_hessian_ND, x_init, disp=False)
deviation_cost_LM = res_LM.cost
n_iter_LM = res_LM.nit
if n_iter_LM > 20 or deviation_cost_LM > 1e-10:
    raise ValueError('Levenberg-Marquardt does not process correctly.')

print("\nGauss-Newton")
res_GN = GaussNewton(get_cost_gradient_hessian_ND, x_init, disp=False)
deviation_cost_GN = res_GN.cost
n_iter_GN = res_GN.nit
if n_iter_GN > 1 or deviation_cost_GN > 1e-20:
    raise ValueError('Gauss-Newton does not process correctly.')

print("\nQuasi-Newton BFGS / linesearch")
res_QN = QuasiNewtonBFGS(get_cost_gradient_ND, x_init, disp=False, steptype='linesearch')
deviation_cost_QN = res_QN.cost
n_iter_QN = res_QN.nit
if n_iter_QN > 20 or deviation_cost_QN > 1e-10:
    raise ValueError('Quasi-Newton BFGS (linesearch) does not process correctly.')

print("\nQuasi-Newton BFGS / Back-tracking")
res_QN_BT = QuasiNewtonBFGS(get_cost_gradient_ND, x_init, disp=False, steptype='backtracking')
deviation_cost_QN_BT = res_QN_BT.cost
n_iter_QN_BT = res_QN_BT.nit

# print("\nSteepes descend / linesearch")
# param_evol_steep, cost_evol_steep = Steepest(get_cost_gradient_ND, x_init, disp=False, steptype='linesearch')
# deviation_cost_steep = cost_evol_steep[-1]
# deviation_param_steep = (param_evol_steep[-1][0] - x_0)/x_0

# print("\nSteepes descend / Back-tracking")
# param_evol_steep_BT, cost_evol_steep_BT = Steepest(get_cost_gradient_ND, x_init, disp=False, steptype='backtracking')
# deviation_cost_steep_BT = cost_evol_steep_BT[-1]
# #deviation_param_steep_BT = (param_evol_steep_BT[-1][0] - x_0)/x_0
