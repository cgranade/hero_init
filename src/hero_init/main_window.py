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
import socket
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
    
    shlexed_func._undec = func
    return shlexed_func

## FUNCTIONS ###################################################################

def get_local_hostname():
    # Try to just get the hostname from socket.
    hostname = socket.gethostbyname(socket.gethostname())
    
    # This sometimes returns 127.0.0.1, so if so we need to be more hackish.
    # See: http://stackoverflow.com/a/166589/267841
    if hostname == "127.0.0.1":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            hostname = s.getsockname()[0]
        finally:
            s.close()
            
    return hostname

## CLASSES #####################################################################

class MainWindow(QtGui.QMainWindow):

    ## CONSTRUCTOR #############################################################
    
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui =  ui.main_window.Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Setup table model.
        self.spd_model = SpeedChartModel()
        self.proxy_model = SpeedChartProxyModel(self)
        self.proxy_model.setSourceModel(self.spd_model)
        self.proxy_model.sort(0, QtCore.Qt.DescendingOrder)
        self.ui.tbl_spd_chart.setModel(self.proxy_model)
        
        # Set resize modes for the table view.
        # Name
        self.ui.tbl_spd_chart.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        # SPD
        self.ui.tbl_spd_chart.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Fixed)
        self.ui.tbl_spd_chart.horizontalHeader().resizeSection(1, 45)
        # DEX
        self.ui.tbl_spd_chart.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Fixed)
        self.ui.tbl_spd_chart.horizontalHeader().resizeSection(2, 45)
        for idx_header in xrange(3, 15):
            self.ui.tbl_spd_chart.horizontalHeader().setResizeMode(idx_header, QtGui.QHeaderView.Fixed)
            self.ui.tbl_spd_chart.horizontalHeader().resizeSection(idx_header, 25)
        # STUN
        self.ui.tbl_spd_chart.horizontalHeader().setResizeMode(15, QtGui.QHeaderView.Fixed)
        self.ui.tbl_spd_chart.horizontalHeader().resizeSection(15, 60)
        # BODY
        self.ui.tbl_spd_chart.horizontalHeader().setResizeMode(16, QtGui.QHeaderView.Fixed)
        self.ui.tbl_spd_chart.horizontalHeader().resizeSection(16, 60)
        # END
        self.ui.tbl_spd_chart.horizontalHeader().setResizeMode(17, QtGui.QHeaderView.Fixed)
        self.ui.tbl_spd_chart.horizontalHeader().resizeSection(17, 60)
        # Status
        self.ui.tbl_spd_chart.horizontalHeader().setResizeMode(18, QtGui.QHeaderView.Stretch)
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
    
    def disp_error(self, err_str):
        self.ui.lbl_cmd_hints.setText('<b>{}</b>'.format(err_str))
    
    def start_server(self, ip='', port=8080):
        if self._server is None:
            print "Starting server on port {}.".format(port)
            try:
                self._server = SocketServer.ThreadingTCPServer(
                    (ip, port), make_http_handler(self.spd_model)
                )
                self._server_thread = threading.Thread(
                    target=lambda: self._server.serve_forever()
                )
                self._server_thread.start()
                self.ui.lbl_server_status.setText(
                    'Online at <a href="{0}">{0}</a>'.format(
                        "http://{host}:{port}".format(
                            host=get_local_hostname(),
                            port=port
                        )
                    )
                )
            except Exception as ex:
                self.disp_error(str(ex))
            
    def stop_server(self):
        if self._server is not None:
            self._server.shutdown()
            self._server_thread.join()
            self._server = None
            self._server_thread = None
            self.ui.lbl_server_status.setText("Offline")
        
    ## EVENTS ##################################################################
        
    def on_model_change(self, *args):
        self.ui.lbl_now_turn.setText(str(self.spd_model.turn))
        self.ui.lbl_now_seg.setText(str(self.spd_model.segment))
        
        if self.spd_model.current_combatant is not None:
            # We have a combatant, so display their info.
            self.ui.lbl_now_name.setText(str(self.spd_model.current_combatant.name))
            self.ui.lbl_now_spd.setText(str(self.spd_model.current_combatant.spd))
            self.ui.lbl_now_dex.setText(str(self.spd_model.current_combatant.dex))
            self.ui.lbl_now_stun.setText(str(self.spd_model.current_combatant.stun))
            self.ui.lbl_now_body.setText(str(self.spd_model.current_combatant.body))
            self.ui.lbl_now_end.setText(str(self.spd_model.current_combatant.end))
        else:
            # No combatant; are we in post-12? Check if seg == 0.
            if self.spd_model.segment == 0:
                self.ui.lbl_now_name.setText(str("Post-Segment 12"))
            else:
                self.ui.lbl_now_name.setText(str("none"))
            # In either case, clear everything else.
            self.ui.lbl_now_spd.setText(str(""))
            self.ui.lbl_now_dex.setText(str(""))
            self.ui.lbl_now_stun.setText(str(""))
            self.ui.lbl_now_body.setText(str(""))
            self.ui.lbl_now_end.setText(str(""))
            
        
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
        "add": "add <name> <spd> <dex> <stun> <body> <end> [PC | NPC] [<status>] - Adds new combatant.",
        "del": "del <name> - Removes combatant.",
        "n": "n - Alias for 'next'.",
        "next": "next - Advances turn order.",
        "abort": "abort <name> - Aborts the next phase for a given combatant.",
        "d": "d <name> [S | B| E] <amount> - Alias for 'd'.",
        "dmg": "dmg <name> [S | B| E] <amount> - Applies damage.",
        "h": "h <name> [S | B| E] <amount> - Alias for 'h'.",
        "heal": "heal <name> [S | B| E] <amount> - Heals damage.",
        "stat": "stat <name> [<new_status>] - Changes or clears status string.",
        "chspd": "chspd <name> <new_spd> - Changes SPD of one combatant.",
        "run": "run <file> - Runs a hero_init script.",
        "skipto": "skipto <seg> - Skips turns until a given segment is reached.",
        "server": "server [start | stop] [<port>] - Starts or stops the embedded webserver."
    }
    VALID_CMDS = sorted(USAGES.keys()) # TODO: refer to Cmd class
    
    ## CONSTRUCTOR #############################################################
    
    def __init__(self, model, window):
        super(type(self), self).__init__()
        self._model = model
        self._window = window
    
    ## COMMANDS ################################################################
    
    @shlexify
    def do_add(self, name, spd, dex, stun, body, end, kind="PC", status=""):
        self._model.add_combatant(Combatant(name, spd, dex, stun, body, end, kind=kind, status=status))
        
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
    def do_dmg(self, name, char, amt):
        ABBREVS = {"S": "stun", "B": "body", "E": "end"}
        amt = int(amt)
        char = char.upper()
        if char not in "SBE":
            self._window.disp_error("Characteristic abbreviation {} not recognized.".format(char))
            return
            
        with self._model.modify_combatant(name) as cmb:
            getattr(cmb, ABBREVS[char]).cur -= amt
        
    do_d = do_dmg
    
    @shlexify
    def do_heal(self, name, char, amt):
        # Dirty hack to bypass shlexification.
        self.do_dmg._undec(self, name, char, -int(amt))
        
    do_h = do_heal
                    
    @shlexify
    def do_stat(self, name, *args):
        stat = "" if len(args) == 0 else " ".join(args)
        with self._model.modify_combatant(name) as cmb:
            cmb.status = stat
                    
    @shlexify
    def do_next(self):
        self._model.next()
    do_n = do_next
    
    @shlexify
    def do_skipto(self, seg):
        seg = int(seg)
        self._model.skip_to(seg)
    
    @shlexify
    def do_abort(self, name):
        try:
            self._model.abort_phase(name)
        except RuntimeError as ex:
            self._window.disp_error(str(ex))
        
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
   
def main():
    app = QtGui.QApplication(sys.argv)
    main_win = MainWindow()
    app.lastWindowClosed.connect(main_win.stop_server)
    main_win.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()

