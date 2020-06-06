AVIO
====

The AVIO Suite is an experimental approach to the concept of a live stage
performance. AVIO stands for "Audio Visual Input Output" and the suite is
a component (event) based agglomeration of tools to work with Controller,
Midi, Audio and Visual data.


Installation
============

Since, AVIO is a plugin collection for Isomer, you'll need a working Isomer
instance first.

Isomer
------

To install Isomer and create an instance to work with AVIO, follow the
`quick start tutorial <https://isomer.readthedocs.io/en/latest/start/index.html>`_.

The quickest way to get AVIO is through Isomer's builtin store system, but that
is not yet completely done, so right now, you'll have to do that manually:

Dependencies
------------

Before installing AVIO, you should furthermore have these packages installed:

* liblo-dev
* libportmidi-dev
* libsndfile1-dev
* python3-pygame
* python3-numpy
* python3-opencv

Install AVIO
------------

Once you have set up Isomer correctly use this command line to install it into your
default instance/environment:

.. code-block:: bash

    iso -e current instance install-module -i -s github https://github.com/ri0t/avio

This will (currently) require a frontend rebuild:

.. code-block:: bash

   iso -e current environment install-frontend

You can use `-i INSTANCENAME` and `-e ENVIRONMENTNAME` to specify which instance should
be used.

Running
=======

Restart your Isomer instance and log in to it, to access the AVIO modules.

Controlling
===========

MIDI
----

To actually use MIDI data e.g. in Bitwig Studio, you may need to
load the alsa midi loopback module:

 .. code-block:: bash
    
    sudo modprobe snd_virmidi

This should enable four virtual loopback devices. With a tool like
patchage, you can now route AVIO's output midi channel to a loopback
device, which you can select as MIDI input in BWS.

Joysticks & Gamepads
--------------------

tbd

User Interface
--------------

tbd

Development
===========

First, you'll need `Isomer set up for development
<https://isomer.readthedocs.io/en/latest/dev/general/environment.html>`_.

Then, manually grab AVIO:

.. code-block:: bash

   git clone https://github.com/ri0t/avio avio

Then run (probably best done in your Isomer virtual environment):

 .. code-block:: bash

    cd avio
    python setup.py develop



License
=======

Copyright (C) 2015-2020 riot <riot@c-base.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

3rd Party Licenses
==================

Includes a few fonts from the ttf-aenigma pack, a great font pack
sporting 465 free TrueType fonts by Brian Ken.
