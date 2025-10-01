Ex. 9: Generate 3D-file with Cadquery
=====================================

This file, describe how to generate 3D-file from geometry file with
openwind.

Source file available
`here <https://gitlab.inria.fr/openwind/openwind/-/blob/master/examples/technical/Ex9_Generate_3D-file_with_CadQuery.py>`__.

This example uses the :py:class:`OWtoCadQuery <openwind.technical.ow_to_cadquery.OWtoCadQuery>` class.

Imports
-------

.. code:: python

    from openwind import InstrumentGeometry
    from openwind.technical.ow_to_cadquery import OWtoCadQuery
    import matplotlib.pyplot as plt

Instrument With Holes Flush With The Pipe Wall
----------------------------------------------

Firstly, it is necessary to instantiate an ``InstrumentGeometry``.

.. code:: python

    mb_path = '../examples/technical/Ex2_instrument.txt'
    holes_path = '../examples/technical/Ex2_holes.txt'
    my_instru = InstrumentGeometry(mb_path, holes_path)
    my_instru.plot_InstrumentGeometry()
    plt.show()

We can then generate the 3D object with the following options: 

- ``wall_width``: the thickness of the main bore wall in mm 
- ``angles``: the angle at which the holes are placed around the main pipe. 
- ``leveled_chimney``: whether the chimney holes are flush with the main pipe wall.

In this case, we want a wall that is 3 mm thick with a
levelled chimney (the wall thickness will be locally adapted to fit the
height of the chimney). The first hole is for the thumb and is placed at
180°, while the last hole is for the little finger on the right hand and
is placed at 45°.

.. code:: python

    my_instru3D = OWtoCadQuery(my_instru,
                               wall_width=3,
                               angles=[180,0,0,0,0,0,0,0,45],
                               leveled_chimney=True,
                               )

This object can now be exported as a 3D file. The file format is
determined by the extension. If the format requires the object to be
meshed (e.g. ‘.stl’), it may be useful to specify the desired tolerance:

- ``tolerance``: The deflection tolerance in mm 
- ``angularTolerance``: The angular tolerance in radians (0.1 rad ~ 6°).

.. code:: python

    my_instru3D.export('instru1_leveled_hole.stl', tolerance=2)

Instrument With Holes Whose Chimney Protrudes Beyond The Wall Of The Pipe.
--------------------------------------------------------------------------

If the ``leveled_chimney`` option is set to ``False``, all the chimney
pipes will be designed using dedicated pipes. The thickness of these
pipes can be specified.

.. code:: python

    my_instru3D_with_chimney = OWtoCadQuery(my_instru,
                                            wall_width=3,
                                            angles=[180,0,0,0,0,0,0,0,45],
                                            leveled_chimney=False,
                                            chim_width=2, #thickness of the chimney pipes set to 2mm
                                            )
    my_instru3D_with_chimney.export('instru1_chim_pipe.step')

Brass Instruments
-----------------

The non-conical parts of the instruments are sliced into small conical
pipes. The option ``step`` allows you to set the length of these slices.
Unfortunately, it is not yet possible to account for valves (pistons) or
to fold the instruments. Therefore, this tool is very limited for brass
instruments.

.. code:: python

    brass_geom = [[0,  .1, 5e-3, 3e-3, 'linear'],
                  [.1, 1.3, 5e-3, 5e-2, 'bessel', .4]]
    valves_geom = [['variety',  'label',    'position', 'reconnection', 'radius',   'length'],
                   ['valve',    'piston1',   0.1,       .125,            3e-3,       0.11],
                   ['valve',    'piston2',  0.15,        .155,           5e-3,       0.07],
                   ['valve',    'piston3',  0.29,       .32,            2e-3,       0.22],]
    my_brass = InstrumentGeometry(brass_geom, valves_geom)
    my_brass.plot_InstrumentGeometry()
    plt.show()
    my_brass3D = OWtoCadQuery(my_brass,
                              step=5, #step length set to 5mm
                              )
    my_brass3D.export('unfolded_brass.step')

Visualization
-------------

Once you have saved the 3D object, you can visualise it using your
preferred software. However, it is also possible to generate a 3D plot.
Plotly is necessary as Matplotlib is not particularly efficient for 3D
plots.

.. code:: python

    try:
        import plotly.offline as py
        fig = my_instru3D_with_chimney.plot_3Dobject() #generate the figure
        py.plot(fig, filename='test.html') # display it in a webpage
    except ImportError as err:
        msg = "The 3D visualization requires plotly."
        raise ImportError(msg) from err
