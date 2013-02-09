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
import SocketServer
import threading
from PySide import QtCore, QtGui

import ui.main_window

import shlex, cmd, contextlib
from functools import wraps

from combat_model import *
from http_handler import *

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
        self.cmd = MainCommand(self.spd_model, self)
        
        # Prepare for serving via HTTP.
        self._server = None
        
    ## DESTRUCTOR ##############################################################
    
    def __del__(self):
        self.stop_server()
        
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
        
    ## METHODS #################################################################
    
    def start_server(self, ip='', port=8080):
        if self._server is None:
            print "Starting server on port {}.".format(port)
            self._server = SocketServer.ThreadingTCPServer(
                (ip, port), make_http_handler(self.spd_model)
            )
            self._server_thread = threading.Thread(
                target=lambda: self._server.serve_forever()
            )
            self._server_thread.start()
            
    def stop_server(self):
        if self._server is not None:
            self._server.shutdown()
            self._server_thread.join()
            self._server = None
            self._server_thread = None
        
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
        "add": "add <name> <spd> <dex> <stun> <body> <end> [PC | NPC] [<status>]",
        "del": "del <name>",
        "next": "next",
        "run": "run <file>",
        "chspd": "chspd <name> <new_spd>",
        "server": "server [start | stop] [<port>]"
    }
    VALID_CMDS = USAGES.keys() # TODO: refer to Cmd class
    
    ## CONSTRUCTOR #############################################################
    
    def __init__(self, model, window):
        super(type(self), self).__init__()
        self._model = model
        self._window = window
    
    ## COMMANDS ################################################################
    
    @shlexify
    def do_add(self, name, spd, dex, stun, body, end, kind="PC", status=""):
        self._model.add_combatant(Combatant(name, spd, dex, stun, body, end, kind, status))
        
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
            
    @shlexify
    def do_server(self, what, port=None):
        if what == "start":
            extra_args = {}
            if port is not None:
                extra_args['port'] = int(port)
            self._window.start_server(**extra_args)
        if what == "stop":
            self._window.stop_server()
   
## MAIN ########################################################################
   
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    main_win = MainWindow()
    app.lastWindowClosed.connect(main_win.stop_server)
    main_win.show()
    sys.exit(app.exec_())

