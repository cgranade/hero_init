#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# gtk_hero_init.py: GTK+3 frontend to the HeroInit tool.
##
# © 2012 Christopher E. Granade (cgranade@gmail.com).
# Licensed under the GPL version 2.
##
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##

## IMPORTS ##

from hero_init import *

from gi.repository import Gtk, GObject

## CLASSES ##

class HeroInitApp(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self,
            application_id="apps.cgranade.hero_init",
            )
        
        self.connect("activate", self.on_activate)
        
        self.window = None # <- set in on_activate.
        self.combat = Combat(update_hook=self.update_hook)
        self.shell  = HeroShell(combat=self.combat, quiet=True, recv_method="thread")
        
    def update_hook(self):
        if self.window is not None:
            self.window.update()
        
    def on_activate(self, data=None):
        self.window = MainWindow(self)
        self.window.show_all()
        self.add_window(self.window)

def add_combatant_to_grid(idx, combatant, grid):
        
    # TODO:  highlight currently acting characters
    # FIXME: fix spacing between widgets
        
    N_ROWS = 2
    N_COLS = 4
        
    name_label = Gtk.Label(combatant.name)
    name_label.set_markup("<b>{0.name}</b>".format(combatant))
    grid.attach(name_label, 0, idx * N_ROWS, 1, 1)
    
    spd_label = Gtk.Label(spd_string(combatant.spd))
    grid.attach(spd_label, 1, idx * N_ROWS, 1, 1)
    
    grid.attach(Gtk.Label("Next turn: "), 2, idx * N_ROWS, 1, 1)
    grid.attach(Gtk.Label(str(combatant.next)), 3, idx * N_ROWS, 1, 1)
    
    characteristics_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    for characteristic in combatant.characteristics.values():
        characteristics_box.pack_start(
            Gtk.Label("{0.name}: {0.current}/{0.maxval}".format(characteristic)),
            False, False, 16)
    grid.attach(characteristics_box, 0, 1 + idx*N_ROWS, N_COLS, 1)

class MainWindow(Gtk.Window):
    def __init__(self, app):
        self.app = app
        Gtk.Window.__init__(self, title="Hello World")
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.main_box)
        
        self.now_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.pack_start(self.now_box, True, True, 6)
        
        self.now_box.pack_start(Gtk.Label("Current Time:"), False, False, 12)
        self.now_label = Gtk.Label(str(self.app.combat.now))
        self.now_box.pack_start(self.now_label, False, False, 0)
        
        self.combatants_frame = Gtk.Frame(label="Combatants")
        self.main_box.pack_start(self.combatants_frame, True, True, 0)
        
        self.combatants_window = Gtk.ScrolledWindow()
        self.combatants_frame.add(self.combatants_window)
        self.combatants_frame.set_shadow_type(Gtk.ShadowType.IN)
        self.combatants_window.set_policy(True, False)
        
        self.combatants_grid = Gtk.Grid()
        self.combatants_window.add_with_viewport(self.combatants_grid)
        
        self.entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.pack_start(self.entry_box, False, False, 0)
        
        self.entry_box.pack_start(Gtk.Label(">>>"), False, False, 6)
        
        self.cmd_entry = Gtk.Entry()
        self.cmd_entry.connect('activate', self.on_cmd_activate)
        self.entry_box.pack_start(self.cmd_entry, True, True, 6)
        
        self.button = Gtk.Button(label="→")
        self.button.connect("clicked", self.on_cmd_activate)
        self.entry_box.pack_start(self.button, False, False, 6)
    
    def _clear_combatants_list(self):
        for child in self.combatants_grid.get_children():
            child.destroy()
    
    def update(self):
        self._clear_combatants_list()
        
        self.now_label.set_text(str(self.app.combat.now))
        
        combatants_list = sorted(self.app.combat.combatants.values(),
            key=lambda combatant: combatant.next,
            reverse=False)
            
        for idx, combatant in enumerate(combatants_list):
            add_combatant_to_grid(idx, combatant, self.combatants_grid)
            
        self.combatants_grid.show_all()
        
    def on_cmd_activate(self, widget):
        self.app.shell.onecmd(self.cmd_entry.get_text())
        self.cmd_entry.set_text("")
        

## MAIN ##

if __name__ == "__main__":
    import sys
    GObject.threads_init()
    app = HeroInitApp()
    app.run(sys.argv)
    
