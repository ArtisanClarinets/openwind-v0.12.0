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

from openwind.technical.player import Player
from openwind.technical import InstrumentGeometry
from openwind.continuous import InstrumentPhysics
from openwind.inversion import InverseFrequentialResponse


# %%
observable = 'impedance'
# frequencies = np.linspace(20, 200, 10)
frequencies = np.array([100.])
temperature = 20
losses = True
nondim = True
radiation = 'planar_piston'
noise_ratio = 1e-5

lengthElem = 0.05
order_optim = 6
dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')

ref_sensitivies = np.array([[0.32070611, 9.80888374, 12.07511712, 59.64268046, 281.4303193 ]])
grad_ref = np.array([[ 4.08372296e-03 +0.0504954j , -1.54635215e-01 -1.54172236j,
                      8.69512388e-02 +1.90546006j,  1.05803216e+00 +9.36184428j,
                      -5.01332687e+00-44.17249018j]])

grad_flow_ref = np.array([[[2.52870208e-15-6.30613555e-16j,
                            -7.68636347e-14+2.07706594e-14j,
                            1.26835039e-10-2.49662473e-11j,
                            4.66237632e-13-1.32272412e-13j,
                            -2.20005748e-12+6.24897426e-13j]],

                          [[-4.46655942e+00+1.28025852e-02j,
                            1.36578033e+02-3.02361320e+00j,
                            4.13710256e+00+7.42707094e-03j,
                            1.51255826e+02-7.85955545e+00j,
                            -7.11039002e+02+3.75780684e+01j]],

                          [[-4.14487528e+00-9.24415720e-03j,
                            1.29786123e+02-2.34071784e+00j,
                            4.13710256e+00+7.42707093e-03j,
                            1.51255826e+02-7.85955545e+00j,
                            -7.11039002e+02+3.75780684e+01j]],

                          [[-3.85719301e+00-2.80122066e-02j,
                            1.28966251e+02-2.16599741e+00j,
                            4.13710256e+00+7.42707093e-03j,
                            1.51255826e+02-7.85955545e+00j,
                            -7.11039002e+02+3.75780684e+01j]]])

grad_pres_ref = np.array([[[3.20565591e-01-9.49267211e-03j,
                            -9.79717193e+00+4.79189351e-01j,
                            1.20749350e+01+6.63269597e-02j,
                            5.95301297e+01-3.66237448e+00j,
                            -2.80891033e+02+1.74141386e+01j]],

                          [[1.87013991e+00-2.09776643e-02j,
                            -5.71757588e+01+1.74355014e+00j,
                            4.13710256e+00+7.42707093e-03j,
                            1.51255826e+02-7.85955545e+00j,
                            -7.11039002e+02+3.75780684e+01j]],

                          [[7.95356545e+00-4.46616268e-02j,
                            -1.65979624e+02+4.29548505e+00j,
                            4.13710256e+00+7.42707093e-03j,
                            1.51255826e+02-7.85955545e+00j,
                            -7.11039002e+02+3.75780684e+01j]],

                          [[2.42113840e+02-9.69368160e+00j,
                            -7.10395583e+01-3.24384171e+00j,
                            4.13710256e+00+7.42707093e-03j,
                            1.51255826e+02-7.85955545e+00j,
                            -7.11039002e+02+3.75780684e+01j]]])

# %% with a junction
player = Player()
initial_geom = [[0, .1, 5e-3, '5e-3', 'linear'],
                [0.1, '~.25', '5e-3', '~5e-3', 'linear']]
initial_hole = [['~0.05', '~3e-3', '~2e-3', 'linear']]
Perce_modif = InstrumentGeometry(initial_geom, initial_hole)
optim_params = Perce_modif.optim_params
Perce_modif_Phy = InstrumentPhysics(Perce_modif, temperature, player, losses=losses, nondim=nondim, radiation_category=radiation, **dry_air)
inverse = InverseFrequentialResponse(Perce_modif_Phy, frequencies, np.zeros_like(frequencies), observable=observable, l_ele=lengthElem, order=order_optim)
inverse.solve()
imped = inverse.imped.copy()

sensitivities, grad_obs = inverse.compute_sensitivity_observable(interp=True, interp_grid=0.085)

#  Finite diff
dx = 1e-8
sens_FD = list()
init_params = optim_params.get_active_values()
for k in range(len(optim_params.get_active_values())):
    dev = np.zeros_like(init_params)
    dev[k] += dx
    inverse.modify_parts(init_params + dev)
    inverse.solve()
    imped_FOR = inverse.imped.copy()

    inverse.modify_parts(init_params - dev)
    inverse.solve()
    imped_BACK = inverse.imped.copy()

    finite_diff = (imped_FOR - imped_BACK)/(2*dx*imped)

    sens_FD.append(np.linalg.norm(finite_diff))

err = np.linalg.norm(sensitivities - np.array(sens_FD)) / np.linalg.norm(sens_FD)

if np.abs(err)>1e-9:
    raise ValueError('The sensitivity of the impedance is not well estimated:'
                     ' deviation {}.'.format(err))

err_ref = np.linalg.norm(sensitivities - ref_sensitivies) / np.linalg.norm(ref_sensitivies)

if np.abs(err_ref)>1e-9:
    raise ValueError('The sensitivity of the impedance is not consistent with'
                     'the previous version. deviation {}.'.format(err_ref))

err_grad_ref = np.linalg.norm(grad_obs - grad_ref)/np.linalg.norm(grad_ref)
if np.abs(err_grad_ref)>1e-9:
    raise ValueError('The gradient of the impedance is not consistent with'
                     'the previous version. deviation {}.'.format(err_grad_ref))


err_grad_flow_ref = np.linalg.norm(inverse.grad_flow - grad_flow_ref)/np.linalg.norm(grad_flow_ref)
if np.abs(err_grad_flow_ref)>1e-9:
    raise ValueError('The gradient of the flow is not consistent with'
                     'the previous version. deviation {}.'.format(err_grad_flow_ref))
err_grad_pres_ref = np.linalg.norm(inverse.grad_pressure - grad_pres_ref)/np.linalg.norm(grad_pres_ref)
if np.abs(err_grad_pres_ref)>1e-9:
    raise ValueError('The gradeint of the pressure is not consistent with'
                     'the previous version. deviation {}.'.format(err_grad_pres_ref))

# %% Without junction
indices = [True, False, True, True, True] # the conicity is here different
initial_geom = [[0, '~.25', '5e-3', '5e-3', 'linear']]
initial_hole = [['~0.05', '~3e-3', '~2e-3', 'linear']]
Perce_modif = InstrumentGeometry(initial_geom, initial_hole)
optim_params = Perce_modif.optim_params
Perce_modif_Phy = InstrumentPhysics(Perce_modif, temperature, player, losses=losses, nondim=nondim, radiation_category=radiation, **dry_air)
inverse = InverseFrequentialResponse(Perce_modif_Phy, frequencies, np.zeros_like(frequencies), observable=observable, l_ele=lengthElem, order=order_optim)
inverse.solve()
imped = inverse.imped.copy()

sensitivities, grad_obs = inverse.compute_sensitivity_observable(interp=True, interp_grid=0.085)

#  Finite diff
dx = 1e-8
sens_FD = list()
init_params = optim_params.get_active_values()
for k in range(len(optim_params.get_active_values())):
    dev = np.zeros_like(init_params)
    dev[k] += dx
    inverse.modify_parts(init_params + dev)
    inverse.solve()
    imped_FOR = inverse.imped.copy()

    inverse.modify_parts(init_params - dev)
    inverse.solve()
    imped_BACK = inverse.imped.copy()

    finite_diff = (imped_FOR - imped_BACK)/(2*dx*imped)

    sens_FD.append(np.linalg.norm(finite_diff))

err = np.linalg.norm(sensitivities - np.array(sens_FD)) / np.linalg.norm(sens_FD)

if np.abs(err)>1e-9:
    raise ValueError('The sensitivity of the impedance is not well estimated:'
                     ' deviation {}.'.format(err))

err_ref = np.linalg.norm(sensitivities - ref_sensitivies[0, indices]) / np.linalg.norm(ref_sensitivies[0, indices])

if np.abs(err_ref)>1e-9:
    raise ValueError('The sensitivity of the impedance is not consistent with'
                     'the previous version. deviation {}.'.format(err_ref))

err_grad_ref = np.linalg.norm(grad_obs - grad_ref[0, indices])/np.linalg.norm(grad_ref[0, indices])
if np.abs(err_grad_ref)>1e-9:
    raise ValueError('The gradient of the impedance is not consistent with'
                     'the previous version. deviation {}.'.format(err_grad_ref))

err_grad_flow_ref = np.linalg.norm(inverse.grad_flow - grad_flow_ref[:, :, indices])/np.linalg.norm(grad_flow_ref[:, :, indices])
if np.abs(err_grad_flow_ref)>1e-9:
    raise ValueError('The gradient of the flow is not consistent with'
                     'the previous version. deviation {}.'.format(err_grad_flow_ref))
err_grad_pres_ref = np.linalg.norm(inverse.grad_pressure - grad_pres_ref[:, :, indices])/np.linalg.norm(grad_pres_ref[:, :, indices])
if np.abs(err_grad_pres_ref)>1e-9:
    raise ValueError('The gradeint of the pressure is not consistent with'
                     'the previous version. deviation {}.'.format(err_grad_pres_ref))
