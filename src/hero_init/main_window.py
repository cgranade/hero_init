#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# main_window.py: Main window for Qt-based UI.
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
from PySide import QtCore, QtGui

import ui.main_window

import shlex, cmd, contextlib
from functools import wraps

## DECORATORS ##################################################################

def shlexify(func):
    @wraps(func)
    def shlexed_func(*args):
        head = args[0:-1]
        tail = args[-1]
        return func(*(head + tuple(shlex.split(tail))))
    
    return shlexed_func

## CLASSES #####################################################################

class MainWindow(QtGui.QMainWindow):

    ## CONSTRUCTOR #############################################################
    
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui =  ui.main_window.Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Setup table model.
        self.spd_model = SpeedChartModel()
        self.ui.tbl_spd_chart.setModel(self.spd_model)
        self.ui.tbl_spd_chart.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        
        # Connect signals and slots.
        self.ui.le_cmd.returnPressed.connect(self.on_cmd_go)
        self.ui.le_cmd.textChanged.connect(self.on_cmd_edit)
        self.ui.btn_cmd.clicked.connect(self.on_cmd_go)
        self.spd_model.dataChanged.connect(self.on_model_change)
        self.spd_model.modelReset.connect(self.on_model_change)
        
        # Setup command interface.
        self.cmd = MainCommand(self.spd_model)
        
    ## PROPERTIES ##############################################################
    
    @property
    def cmd_text(self):
        return str(self.ui.le_cmd.text())
    @cmd_text.setter
    def cmd_text(self, newval):
        self.ui.le_cmd.setText(str(newval))
        
    @property
    def cmd_hint(self):
        return str(self.ui.lbl_cmd_hints.text())
    @cmd_hint.setter
    def cmd_hint(self, newval):
        self.ui.lbl_cmd_hints.setText(newval)
        
    ## EVENTS ##################################################################
        
    def on_model_change(self, *args):
        self.ui.lbl_now_turn.setText(str(self.spd_model.turn))
        self.ui.lbl_now_seg.setText(str(self.spd_model.segment))
        if self.spd_model.current_combatant is not None:
            self.ui.lbl_now_name.setText(str(self.spd_model.current_combatant.name))
            self.ui.lbl_now_spd.setText(str(self.spd_model.current_combatant.spd))
            self.ui.lbl_now_dex.setText(str(self.spd_model.current_combatant.dex))
            self.ui.lbl_now_stun.setText(str(self.spd_model.current_combatant.stun))
            self.ui.lbl_now_body.setText(str(self.spd_model.current_combatant.body))
            self.ui.lbl_now_end.setText(str(self.spd_model.current_combatant.end))
        
    def on_cmd_edit(self):
        cmd = self.cmd_text
        cmd_parts = cmd.split(" ", 2)
        cmd_name = cmd_parts[0] if len(cmd_parts) > 0 else ""
        if cmd_name in self.cmd.VALID_CMDS:
            self.cmd_hint = self.cmd.USAGES[cmd_name]
        else:
            self.cmd_hint = "Available commands: " + ", ".join(self.cmd.VALID_CMDS)
        
    def on_cmd_go(self):
        cmd = self.cmd_text
        self.cmd_text = ""
        
        # Check that the command is good.
        cmd_parts = cmd.split(" ", 2)
        cmd_name = cmd_parts[0].strip() if len(cmd_parts) > 0 else ""
        if cmd_name in self.cmd.VALID_CMDS:
            self.cmd.onecmd(cmd)
        else:
            print "Error!", '"{}"'.format(cmd_name), self.cmd.VALID_CMDS, len(cmd_name)

class MainCommand(cmd.Cmd):
    
    ## CONSTANTS ###############################################################
    
    # TODO: populate from methods.
    USAGES = {
        "add": "add <name> <spd> <dex> <stun> <body> <end> [<status>]",
        "del": "del <name>",
        "next": "next",
        "run": "run <file>",
        "chspd": "chspd <name> <new_spd>",
    }
    VALID_CMDS = USAGES.keys() # TODO: refer to Cmd class
    
    ## CONSTRUCTOR #############################################################
    
    def __init__(self, model):
        super(type(self), self).__init__()
        self._model = model
    
    ## COMMANDS ################################################################
    
    @shlexify
    def do_add(self, name, spd, dex, stun, body, end, status=""):
        self._model.add_combatant(Combatant(name, spd, dex, stun, body, end, status))
        
    @shlexify
    def do_run(self, filename):
        with open(filename, "r") as f:
            for line in f:
                if not line.strip().startswith("#"):
                    self.onecmd(line)
                    
    @shlexify
    def do_del(self, name):
        self._model.del_combatant(name)
                    
    @shlexify
    def do_next(self):
        self._model.next()
        
    @shlexify
    def do_chspd(self, name, new_spd):
        with self._model.modify_combatant(name) as combatant:
            combatant.change_spd(int(new_spd))

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
    def __init__(self, name, spd, dex, stun, body, end, status=""):
        self._name = name
        self._spd = int(spd)
        self._dex = int(dex)
        self._stun = Characteristic(stun)
        self._body = Characteristic(body)
        self._end = Characteristic(end)
        self._status = status
        self._segment = [None] * 12
        
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
    
   
## MAIN ########################################################################
   
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())

