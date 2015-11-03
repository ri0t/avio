AVIO
====

The AVIO Suite is an experimental approach to the concept of a live stage
performance. AVIO stands for "Audio Visual Input Output" and the suite is
a component (event) based agglomeration of tools to work with Controller,
Midi, Audio and Visual data.

Installation
============

You should have python-pygame (1.9.1) installed from your Distribution.
The package will additionally require and install circuits, an event driven
component framework with minimal overhead.

Then run:

 .. code-block:: bash

    $ python setup.py install

If you prefer working safe and sane, use a virtualenvironment:

 .. code-block:: bash

    $ virtualenv avio --system-site-packages
    $ source avio/bin/activate

Or if you have (you should ;) virtualenvwrapper:

 .. code-block:: bash

    $ mkvirtenv avio --system-site-packages
    $ workon avio

Saves that much typing. Then install AVIO:

 .. code-block:: bash

    $ pip install .

If you intend to develop on it, use:

 .. code-block:: bash
    $ python setup.py develop

Running
=======

Activate your virtual environment as above, (change to the AVIO source
directory) and run it thus:

 .. code-block:: bash

    $ ./avio

On the first start - or if there is no configuration at all - AVIO will
create a configuration in ~/.avio

You should edit the default router configuration to suit your controller
and needs.
A detailed explanation on how to write router scenes will follow.

Arguments
=========

AVIO offers a few command line arguments:

* -h                Display help text
* --io              Display IO port tables for MIDI and Controllers
* --mididev         Select a midi device (pick one from the --io command)
* --gui             Run the (experimental) GUI
* --program $NAME   Load router program configuration from ~/.avio/router_$NAME.json

Controlling
===========

Keyboard
--------

The GUI window currently accepts these keystrokes:

* q     Close the application (without asking)

More to come.

The window (obviously) has to be active, to receive keystrokes.

Joysticks & Gamepads
--------------------

They are currently statically mapped. Only axes work.
You can adjust the mapping in the router source code. This will be
enhanced, it is (as almost everything here) WiP.


License
=======

Copyright (C) 2015 riot <riot@c-base.org>

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
