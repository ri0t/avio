# AVIO - The Python Audio Video Input Output Suite
# ================================================
# Copyright (C) 2015 riot <riot@c-base.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'riot'

from circuits import Event

# App/GUI management events

class guiresize(Event):
    def __init__(self, width, height, *args):
        super(guiresize, self).__init__(*args)
        self.height = height
        self.width = width


class quit(Event):
    def __init__(self, reason, *args):
        super(quit, self).__init__(*args)
        self.reason = reason

# Control events

class controlinput(Event):
    def __init__(self, inputevent, *args):
        super(controlinput, self).__init__(*args)
        self.input = inputevent


class joystickchange(controlinput):
    def __init__(self, *args):
        super(joystickchange, self).__init__(*args)


class midicc(Event):
    def __init__(self, cc, data, *args):
        super(midicc, self).__init__(*args)

        self.cc = cc
        self.data = data
