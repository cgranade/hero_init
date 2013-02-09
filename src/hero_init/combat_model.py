#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# combat_model.py: Classes and constants for modeling HERO System combats.
##
# © 2013 Christopher E. Granade (cgranade@gmail.com)
#     
# This file is a part of the hero_init project.
# Licensed under the AGPL version 3.
##
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
##

## IMPORTS #####################################################################

import sys
import contextlib
from PySide import QtCore, QtGui

## CLASSES #####################################################################

COMBATANT_KINDS = [
    "PC", "NPC"
]

STATES = {
    "NONE":   0,
    "FUTURE": 1,
    "NOW":    2,
    "ABORT":  3
}

SPEED_CHART = (
    (0, ) * 12,
    # 1   2   3   4   5   6   7   8   9  10  11  12
    ( 0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0), #  1
    ( 0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  1), #  2
    ( 0,  0,  0,  1,  0,  0,  0,  1,  0,  0,  0,  1), #  3
    ( 0,  0,  1,  0,  0,  1,  0,  0,  1,  0,  0,  1), #  4
    ( 0,  0,  1,  0,  1,  0,  0,  1,  0,  1,  0,  1), #  5
    ( 0,  1,  0,  1,  0,  1,  0,  1,  0,  1,  0,  1), #  6
    ( 0,  1,  0,  1,  0,  1,  1,  0,  1,  0,  1,  1), #  7
    ( 0,  1,  1,  0,  1,  1,  0,  1,  1,  0,  1,  1), #  8
    ( 0,  1,  1,  1,  0,  1,  1,  1,  0,  1,  1,  1), #  9
    ( 0,  1,  1,  1,  1,  1,  0,  1,  1,  1,  1,  1), # 10
    ( 0,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1), # 11
    ( 1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1), # 12
)

class Characteristic(object):
    def __init__(self, current, maxval=None):
        if isinstance(current, str):
            parts = [s.strip() for s in current.split("/", 2)]
            if len(parts) == 1:
                parts = parts * 2
            current, maxval = map(int, parts)
            
        self._cur = current
        self._max = maxval if maxval is not None else current
        
    def __str__(self):
        return "{cur}/{max}".format(cur=self._cur, max=self._max)

class Combatant(object):
    def __init__(self, name, spd, dex, stun, body, end, status="", kind="PC"):
        self._name = name
        self._spd = int(spd)
        self._dex = int(dex)
        self._stun = Characteristic(stun)
        self._body = Characteristic(body)
        self._end = Characteristic(end)
        self._status = status
        self._segment = [None] * 12
        self._kind = kind        
        
        self._next_turn()
        
    def _next_turn(self):
        self._segment = list(SPEED_CHART[self.spd])
        
    @property
    def name(self):
        return self._name
    @property
    def spd(self):
        return self._spd
    @property
    def dex(self):
        return self._dex
    @property
    def stun(self):
        return self._stun
    @property
    def body(self):
        return self._body
    @property
    def end(self):
        return self._end
    @property
    def status(self):
        return self._status
        
    def __getitem__(self, idx):
        assert idx <= 12 and idx >= 1, idx
        return self._segment[idx - 1] # Segments are 1-based!
        
    def __setitem__(self, idx, state):
        # TODO: make sure the new state is valid.
        assert idx <= 12 and idx >= 1, idx
        self._segment[idx - 1] = state # Segments are 1-based!
        
    def change_spd(self, newspd):
        # FIXME: doesn't handle NOW states properly.
        assert newspd >= 0 and newspd <= 12, newspd
        old_spd = self.spd
        self._spd = newspd
        newseg = list(SPEED_CHART[newspd])
        
        # Go through the segments in the new and old lists,
        # and don't allow the combatant to move unless both lists have
        # a FUTURE. We can do this by erasing all elements of newseg
        # that come before we find a FUTURE in the old speed chart.
        for idx, old in enumerate(self._segment):
            # Check see if the old SPD chart gives us this segment.
            if old != STATES["FUTURE"]:
                # Nope. Erase the state in the newseg, then.
                newseg[idx] = STATES["NONE"]
            else:
                # Yep. We're done here.
                break
        
        # If we're here, either we found one, or there were no valid
        # segments. Either way, newseg should be accurate.
        self._segment = newseg

class SpeedChartModel(QtCore.QAbstractTableModel):
    
    FORMATTERS = [
        lambda C: C.name,
        lambda C: C.spd,
        lambda C: C.dex,
    ] + [
        # Trick to "capture" generator index.
        (lambda seg: (lambda C: C[seg]))(segment)
        for segment in xrange(1, 13)
    ] + [
        lambda C: str(C.stun),
        lambda C: str(C.body),
        lambda C: str(C.end),
        lambda C: C.status,
    ]
    
    HEADER_NAMES = [
        "Name", "SPD", "DEX",
    ] + [
        str(segment) for segment in xrange(1, 13)
    ] + [
        "STUN", "BODY", "END", "Status"
    ]

    def __init__(self, parent=None):
        super(SpeedChartModel, self).__init__(parent)
        self._combatants = []
        
        self._now = (1, 1)
        self._current_combatant = None
        
    ## PROPERTIES ##############################################################
        
    @property
    def n_combatants(self):
        return len(self._combatants)
        
    @property
    def turn(self):
        return self._now[0]
    
    @property
    def segment(self):
        return self._now[1]
        
    @property
    def current_combatant(self):
        return self._current_combatant
        
    ## QT MODEL CONTRACT #######################################################    
    
    def rowCount(self, parent=None):
        return self.n_combatants
        
    def columnCount(self, parent=None):
        return 19
        
    def data(self, index, role):
        if not index.isValid():
            return None
        
        if index.row() >= self.n_combatants or index.row() < 0:
            return None
            
        if role == QtCore.Qt.DisplayRole:
            return self.FORMATTERS[index.column()](self._combatants[index.row()])
        
        return None
        
    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
            
        if orientation == QtCore.Qt.Horizontal:
            return self.HEADER_NAMES[section]
        
        return None
        
    ## PRIVATE METHODS #########################################################
    
    def _increment(self):
        turn, seg = self._now
        if seg == 12:
            self._now = (turn + 1, 1)
            for combatant in self._combatants:
                combatant._next_turn()
        else:
            self._now = (turn, seg + 1)
        
    ## PUBLIC METHODS ##########################################################
    
    def add_combatant(self, combatant):
        # FIXME: doesn't check for duplicates!
        self.beginResetModel()
        self._combatants.append(combatant)
        self.endResetModel()
        
    def del_combatant(self, name):
        self.beginResetModel()
        self._combatants.remove(self.get_combatant(name))
        self.endResetModel()
    
    def get_combatant(self, key):
        # FIXME: slow as fuck.
        for combatant in self._combatants:
            if combatant.name == key:
                return combatant
                
    @contextlib.contextmanager
    def modify_combatant(self, key):
        self.beginResetModel() # ← I really shouldn't do this.
        yield self.get_combatant(key)
        self.endResetModel()
        
    def next(self):
        self.beginResetModel() # This is really lazy...
    
        # Remove the current combatant's turn.
        if self._current_combatant is not None:
            self._current_combatant[self.segment] = STATES["NONE"]
            
        # Find the next combatant.
        # This will be the highest DEX combatant with a turn in the FUTURE
        # of this segment.
        # If we don't find a segment, we increment.
        while True:
            cmbs_this_seg = [cmb for cmb in self._combatants if cmb[self.segment] == STATES["FUTURE"]]
            if cmbs_this_seg:
                # We found something, so break!
                break
            else:
                self._increment()
            
        best_dex = max([cmb.dex for cmb in cmbs_this_seg])
        # FIXME: the following ignores ties!
        next_cmb = iter(cmb for cmb in cmbs_this_seg if cmb.dex == best_dex).next()
        next_cmb[self.segment] = STATES["NOW"]
        self._current_combatant = next_cmb
        
        # Notify that the data has changed.
        self.endResetModel()

