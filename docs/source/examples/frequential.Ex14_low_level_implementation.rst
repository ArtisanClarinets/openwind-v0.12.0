Ex. 14: Low Level Implementation
================================

This presents low level implementation.

Source file available
`here <https://gitlab.inria.fr/openwind/openwind/-/blob/master/examples/frequential/Ex14_low_level_implementation.py>`__.

Imports
-------

.. code:: python

    import numpy as np
    import matplotlib.pyplot as plt
    from openwind import (ImpedanceComputation, InstrumentGeometry, Player,
                          InstrumentPhysics, FrequentialSolver)
    fs = np.arange(100, 5010, 10) # frequencies of interest: 100Hz to 5kHz by steps of 10Hz

Instead of using impedance computation, it can be usefull to use a lower
level of implementation giving more possibilities. This process is the
one implemented in
`ImpedanceComputation <../modules/openwind.impedance_computation.html>`__ module.

Geometry
--------

The first step is to load and process the instrument geometrical file
with the
`InstrumentGeometry <../modules/openwind.technical.instrument_geometry.html>`__ module. 
Here must be sepcified the option about the geoemtry (unit, etc)

.. code:: python

    geom_options = {'unit':'m', 'diameter':False}
    files = ('Oboe_instrument.txt','Oboe_holes.txt')
    instr_geom = InstrumentGeometry(*files, **geom_options)
    instr_geom.plot_InstrumentGeometry()
    plt.show()

The Physical Modelling
----------------------

Now physical models must be associated to this geometry, including,
visco-thermal losses radiation, etc. This is perform through the
`InstrumentPhysics <../modules/openwind.continuous.instrument_physics.html>`__
module. First, it is necessary to create a “player” using the default
value : unitary flow for impedance computation

.. code:: python

    player = Player()

Choose the physics of the instrument from its geometry. Default models
are chosen when they are not specified. Here losses = True means that
Zwikker-Koster model is solved.

.. code:: python

    phy_options = dict(temperature=25, losses=True, radiation_category='infinite_flanged',
                       matching_volume=True)
    instr_physics = InstrumentPhysics(instr_geom, player=player,
                                      **phy_options)

Solve The Equations In The Frequency Domain
-------------------------------------------

The penultimate step is to perform the discretisation of the pipes and
put all parts together ready to be solved. This is done by the
`FrequentialSolver <../modules/openwind.frequential.frequential_solver.html>`__
module. Here must be specified the mesh options and the computation
method.

.. code:: python

    freq_options  = dict(compute_method='FEM', l_ele=1e-2, order=4)
    freq_model = FrequentialSolver(instr_physics, fs, **freq_options)

Finally we solve the linear system underlying the impedance computation.
Here are specified interpolation option.

.. code:: python

    interp_options = dict(interp=True, interp_grid=1e-3)
    freq_model.solve(**interp_options)

Comparison With High Level
--------------------------

To perform the similar computation with high level implementation:

.. code:: python

    high_level = ImpedanceComputation(fs, *files, **geom_options, **phy_options,
                                      **freq_options, **interp_options)
    figure = plt.figure()
    freq_model.plot_impedance(figure=figure, label='Low level implementation')
    high_level.plot_impedance(figure=figure, label='High level implementation')
    plt.show()
    deviation = np.linalg.norm(freq_model.impedance - high_level.impedance)/np.linalg.norm(freq_model.impedance)
    print(f'The relative deviation between the two compuations: {deviation:.0e}')
