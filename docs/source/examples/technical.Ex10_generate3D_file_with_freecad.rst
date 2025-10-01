
Ex. 10: Generate 3D file with FreeCAD
=====================================

.. warning::
  This feature is still being tested. It should work well on Ubuntu, but I am having some problems on Windows, possibly due to a conflict between Anaconda environement and FreeCAD.

This document presents a way to generate 3D file (.step or .stl) using the software FreeCAD, directly from openwind geometry file.

I. Install FreeCAD
--------------------

The first thing to do is to download and install FreeCAD. The minimal version needed is 0.19 (the ones before used Python2 incompatible with openwind).
You can download it on the `official website <https://www.freecadweb.org/downloads.php>`_ or follow the instruction of the  `wiki <https://wiki.freecadweb.org/Installing>`_ to do it manually.

a. On ubuntu
^^^^^^^^^^^^

As it is necessary to install other python package, do not use the appimage or the snap installation. You can either install freecad through conda (if you install openwind with conda) or use simply:

.. code-block:: shell

   sudo apt-get install freecad


c. FreeCAD Options:
^^^^^^^^^^^^^^^^^^^

To have more information about what is happening and eventual issues you can open the panels "Report view" and "Python console" (\ ``View\Panels``\ ).

II. Test communication between FreeCAD and Openwind
---------------------------------------------------

Once FreeCAD is installed, it is great to test that it has been installed in the same environement than the one use with openwind (or that all the necessary package). 

In the Python console of FreeCAD you can try to import openwind:

.. code-block:: python

   import openwind

if no error message appears, it means that you have successfully import openwind and you should be able to use generate 3D files without any problem.
If you have an error, it is not necessary a problem (maybe you downloaded openwind from sources), but you need to test that the necessary packages are installed (see "requirements.txt" file):

.. code-block:: python

   import numpy
   import matplotlib
   import scipy
   import packaging
   import h5py

If you successfully import these packages you should be able to use the following macro. If it is not the case, it means that you have to install these packages on the same environnement than FreeCAD.

a. Additional packages on ubuntu
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FreeCAD can be installed on the default environnement of the machine. You could try:

.. code-block:: shell

   sudo apt install python3-h5py

idem for all other requirements.


III. With the GUI
-----------------


#. Start **FreeCAD**
#. Go to ``Macro\Macro...``
#. Modify the ``User macros locations`` to the folder ``../openwind/openwind``
#. ``Execute`` the macro ``macro_OW2Freecad.py``
#. A dialog box named **OpenWind to FreeCAD** should open

.. image :: https://files.inria.fr/openwind/pictures/GUI.png
  :width: 1000
  :align: center

a. Description of the GUI
^^^^^^^^^^^^^^^^^^^^^^^^^


* Input files

  * In the first field you must indicate the path to the **main bore file** as used in openwind. The ``explore`` button open a file explorer box to help you. You can chose text files (".txt" or ".csv") or openwind file (".ow").
  * In the second field you can indicate a path to a **hole file** if necessary (let it empty if the instrument has no side holes or if you use ".ow" file)

* Output files

  * enter the name of the file (you can use the ``explore`` button). If you chose the extension ".stl", the generated object will be automatically meshed and ready to be imported in 3D-printer software. The extension ".step" is better if you want to modify the 3D object afterward.

* Options: different options for the rendered geometry.

  * the wall width of the main bore in millimeter
  * with this macro only, conical pipes are generated. The non-conical parts (horn, spline, etc), are sliced with the specified step size
  * if the option "the chimney are flush with the ext. wall" is turn on, the wall width of the main bore will be locally adapted to fit the desired chimney height. If the option is not check, an aditional pipe with a given wall width will be used to shape the chimney.
  * if the previous option is not actiavted, the wall width of the chimney pipe
  * the angle of each hole around the main bore in degree (typically 180 for a thumb and 315 for right little finger). No value, or one value per hole separated by a semi-column (;) must be given.

b. Generation
^^^^^^^^^^^^^


* Once you click on the ``OK`` button the generation starts. It can be long especially if:

  * the "fluch" option is not activated, 
  * if the output format ".stl" is chosen (due to the mesh generation)

* Some progressing indication are given in the "report view" panel
* If the generation is successful, a popup window open, with the output path.
