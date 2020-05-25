#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
# Copyright (C) 2011-2019 Heiko 'riot' Weinen <riot@c-base.org> and others.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

from setuptools import setup, find_packages

setup(
    name="avio",
    version="2.0.0",
    description="AVIO is a collection of general purpose audio/video/midi/controller "
                "components for Isomer",
    author="Heiko 'riot' Weinen",
    author_email="riot@c-base.org",
    url="https://github.com/ri0t/avio",
    license="GNU Affero General Public License v3",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        # 'Framework :: Isomer :: 1',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Multimedia',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Multimedia :: Graphics :: Capture',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Analysis',
        'Topic :: Multimedia :: Sound/Audio :: Capture/Recording',
        'Topic :: Multimedia :: Sound/Audio :: Conversion',
        'Topic :: Multimedia :: Sound/Audio :: MIDI',
        'Topic :: Multimedia :: Sound/Audio :: Mixers',
        'Topic :: Multimedia :: Sound/Audio :: Players',
        'Topic :: Multimedia :: Sound/Audio :: Sound Synthesis',
        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Video :: Capture',
        'Topic :: Multimedia :: Video :: Conversion',
        'Topic :: Multimedia :: Video :: Display'
    ],
    packages=find_packages(),
    package_data={'avio': ['../docs/*', '../frontend/*']},
    include_package_data=True,
    long_description=""""AVIO
====

AVIO stands for Audio Video Input Output.

This software package contains general purpose modules for working (and playing!)
with mixed media data. It strives to cover most of the available dataformats and their
various input and output methods.
For example, there is a HID (Joysticks, Gamepads, etc) input component that you can wire
up to transmit its data to a MIDI output to generate general MIDI modulation data or
even notes. Other components work with image or video data.

Read the paper online: https://riot.crew.c-base.org/avio.pdf

This software package is a plugin module for Isomer.
""",
    dependency_links=[],
    install_requires=[
        'pygame>=1.9.1release',
        'isomer>=1.0',
        'isomer-camera>=0.0.1',
        'isomer-audio>=0.0.1',
        'isomer-protocols>=0.0.1'
    ],
    entry_points="""[isomer.schemata]
      [isomer.components]
      midiinput=avio.midi:MidiInput
      midioutput=avio.midi:MidiOutput
      hidcontroller=avio.controller:HIDController
      trigger=avio.trigger:Trigger
      combotrigger=avio.combotrigger:ComboTrigger
      gifplayer=avio.gifplayer:GIFPlayer
      bpm=avio.bpm:BPM
      [isomer.management]
      [isomer.provisions]
    """,
    test_suite="tests.main.main",
)
