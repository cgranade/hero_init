#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# hero_init.py: Initiative and damage tracking tool for HERO System 6e.
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

## TODO ##
# - Parse " " in command arguments.
# - Add comment handling.

## IMPORTS ##

import readline
import cmd

from constants import *
from combatant import *

from util import shlexify

## CLASSES ##

# TODO: command argument splitting is very poor right now.

class HeroShell(cmd.Cmd):
    intro = ""
    prompt_template = "hero_init {time} >>> "
    prompt = ""
    file = None
    server = None

    def __init__(self, combat=None, quiet=False, recv_method="thread"):
        self.combat = combat if combat is not None else Combat(segment=12)
        self.update_prompt()
        self.quiet = quiet
        self.recv_method = recv_method
        cmd.Cmd.__init__(self)

    def update_prompt(self):
        self.prompt = self.prompt_template.format(time=self.combat.now)

    def postcmd(self, stop, line):
        self.update_prompt()
        cmd.Cmd.postcmd(self, stop, line)

    def emptyline(self):
        # Override to prevent empty lines from repeating earlier commands.
        pass
    
    def do_exit(self, args):
        """
        exit - Exits the initiative tracker.
        """
        print ""
        import sys
        
        if self.server is not None:
            self.server.stop()
        
        sys.exit(0)
        
    do_EOF = do_exit

    @shlexify        
    def do_run(self, filename):
        """
        run [file] - Runs the given file containing hero_init commands. Useful
            to setup initial combat configurations.
        """
        try:
            with open(filename) as script_file:
                for line in script_file.readlines():
                    if len(line.strip()) != 0 and not line.strip().startswith("#"):
                        self.onecmd(line)
        except IOError as ioe:
            print "[ERROR] {0}".format(ioe)
        
        
    @shlexify
    def do_add(self, shortname, name, spd, dex, stun, body, end):
        """
        add [id] [name] [spd] [dex] [stun] [body] [end] - Adds a new combatant to the combat.
        """
        try:
            new_combatant = Combatant(
                combat=self.combat,
                shortname=shortname,
                name=name,
                spd=int(spd),
                dex=int(dex),
                maxstun=int(stun),
                maxbody=int(body),
                maxend=int(end)
            )
        except RuntimeError:
            print "ID {name} is duplicated.".format(name=shortname)
            
    def do_ls(self, args):
        """
        ls - Lists all current combatants.
        """
        if not self.quiet:
            print_combatants(self.combat.combatants.values())
        else:
            # This command is really stupid if quiet.
            pass
    
    def do_lsseg(self, args):
        """
        lsseg - Lists all combatants acting in the current segment.
        """
        if not self.quiet:
            print_combatants(self.combat.combatants_this_segment())
        else:
            pass
        
    def do_next(self, args):
        """
        next - Advances time and shows the next acting combatants.
        
        Aliases: n
        """
        self.combat.advance_time()
        if not self.quiet:
            print "Combatants this DEX:"
            print_combatants(self.combat.combatants_this_dex())
        else:
            pass
        
    do_n = do_next
        
        
    @shlexify
    def do_setspd(self, shortname, newspd):
        """
        setspd [id] [newspd] - Changes the SPD of a combatant and updates
            their next turn accordingly.
        """
        combatant = self.combat.combatants[shortname]
        combatant.change_speed(int(spd))
        
    @shlexify
    def do_setpc(self, shortname, is_pc):
        """
        setpc [id] [is pc] - Sets whether a combatant is a PC or not.
        """
        combatant = self.combat.combatants[shortname]
        combatant.pc = bool(is_pc)     
        
    @shlexify
    def do_dmg(self, shortname, amt, characteristic="STUN"):
        """
        dmg [id] [amt] [characteristic] - Damages a characteristic by the
            given amount.
        dmg [id] [amt] - Damages STUN by the given amount.
        
        Aliases: d
        """
        combatant = self.combat.combatants[shortname]
        characteristic = characteristic.upper()
        amt = int(amt)
            
        combatant.characteristics[characteristic].current -= amt
        
    do_d = do_dmg
        
    @shlexify
    def do_abort(self, shortname):
        """
        abort [name] - Aborts the phase of a combatant.
        """
        combatant = self.combat.combatants[shortname]
        combatant.abort_phase()
        
    @shlexify
    def do_lightning(self, shortname, descript, dexboost):
        """
        lightning [name] [action description] [dex bonus] - Adds a Lightning
            Reflexes power to the given combatant.
        """
        lightning_reflexes(
            combat=self.combat,
            combatant=self.combat.combatants[shortname],
            description=descript,
            dexboost=int(dexboost)
            )
        #print "[ERROR] Not yet implemented."
        
    @shlexify
    def do_server(self, mode="start"):
        """
        server start - Starts the embedded web server.
        server stop - Stops the embedded web server.
        """
        from hero_server import HeroServer
        
        if mode.strip() == "start":
            if self.server is None:
                self.server = HeroServer(self.combat, self.recv_method)
                self.server.start()
            else:
                print "[ERROR] Server has already been started."
        elif mode.strip() == "stop":
            if self.server is not None:
                self.server.stop()
                self.server = None
        
        
class Time(object):
    def __init__(self, rnd, seg, dex, comment=None, trigger_fn=None):
        self.rnd = rnd
        self.seg = seg
        self.dex = dex
        self.comment = comment
        self.trigger_fn = trigger_fn
        
    def __cmp__(self, other):
        s_rnd = self.rnd
        s_seg = self.seg
        s_dex = self.dex
        o_rnd = other.rnd
        o_seg = other.seg
        o_dex = other.dex
        
        if s_rnd != o_rnd:
            return cmp(s_rnd, o_rnd)
        if s_seg != o_seg:
            return cmp(s_seg, o_seg)
        return -cmp(s_dex, o_dex)
        
    def trigger(self):
        if self.trigger_fn is not None:
            return self.trigger_fn()
        
    def as_tuple(self):
        return self.rnd, self.seg, self.dex
        
    def __repr__(self):
        partial_repr = "{rnd:>2}:{seg:>2}:{dex:>2}".format(
            rnd=self.rnd, seg=self.seg,
            dex=self.dex if self.dex != Infinity else " ∞")
        if self.comment is not None:
            partial_repr = partial_repr + " " + self.comment
        return partial_repr

class Combat(object):
    """
    Represents a combat, including time tracking and a list of combatants.
    """
    
    def __init__(self, segment=12, update_hook=None):
        """
        Initializes the combat to start in a given segment,
        and registers a function to be called whenever the combat changes.
        """
        self.now = Time(rnd=0, seg=segment, dex=Infinity)
        self.combatants = {}
        self.update_hooks = []
        if update_hook is not None:
            self.update_hooks.append(update_hook)
        
    def _update(self):
        for update_hook in self.update_hooks:
            update_hook()
        
    def _add_combatant(self, combatant):
        """
        Adds a combatant to the current combat. The shortname of the combatant
        must be unique, or else an error will be raised.
        """
        if combatant.shortname not in self.combatants:
            self.combatants[combatant.shortname] = combatant
            self._update()
        else:
            raise RuntimeError("ID {name} is duplicated.".format(name=combatant.shortname))
        
    def combatants_this_segment(self, strict=False):
        """
        Returns a list of combatants that have actions in the current segment.
        If strict = True, then the list returned will not include combatants
        with actions in the current DEX.
        """
        rnd, seg, dex = self.now.as_tuple()
        
        def moves_this_segment(combatant):
            c_rnd, c_seg, c_dex = combatant.next.as_tuple()
            if (rnd, seg) == (c_rnd, c_seg):
                return (
                    (dex >= c_dex) if not strict else (dex > c_dex)
                )
            else:
                return False
                
        return filter(moves_this_segment, self.combatants.values())
    
    def combatants_this_dex(self):
        """
        Returns a list of combatants with actions in the current DEX.
        """
        return filter(
            lambda combatant: combatant.next.dex == self.now.dex,
            self.combatants_this_segment())
        
    def get_all_pcs(self):
        """
        Returns a list of all combatants representing player characters.
        """
        return filter(
            lambda combatant: combatant.pc,
            self.combatants.values()
            )
        
    def get_now(self):
        return self.now
        
    def get_combatant_by_id(self, cmb_id):
        return self.combatants[cmb_id]
        
    def calc_next_segments(self):
        """
        Finds any combatants whose actions are in the past and updates their
        next segments accordingly.
        """
        dirty = False
        
        for combatant in self.combatants.values():
            if self.now >= combatant.next:
                dirty = True
                # If post_phase is False, then that indicates that there was
                # a trigger function set that cancelled the calculation of the 
                # next segment.
                if combatant.post_phase():
                    combatant.calc_next_segment()
                    
        if dirty:
            self._update()
        
    def advance_time(self):
        """
        Advances the current time, skipping ahead to the next combatant with an
        action.
        """
        self.calc_next_segments()
        combatants_left = self.combatants_this_segment(strict=True)
        
        if len(combatants_left) == 0:
            # Next segment.
            # self.segment = self.segment + 1
            self.now.seg = self.now.seg + 1
            if self.now.seg > 12:
                self.now.seg = 1
                self.now.rnd = self.now.rnd + 1
            self.now.dex = Infinity
            # Always advance time so we don't
            # sit at infininite dex.
            # FIXME: will behave badly if no combatants
            # exist, or if all combatants are SPD 0.
            self.advance_time()
            
        else:
            # Next combatant in the segment.
            dexs = map(lambda combatant: combatant.next.dex,
                combatants_left)
            self.now.dex = max(dexs)
            
        self._update()

        
## FUNCTIONS ##
        
def print_combatants(combatants):
    """
    Given a list of combatants, prints a table of information about those
    combatants.
    """
    print "\t{0:<20}{1:<24}\t{2}\t{3}\n\t{4:=<66}".format(
        "Name", "SPD", "DEX", "Next", ""
    )
    for combatant in combatants:
        print "\t{0}".format(combatant)
        
def spd_string(spd):
    """
    Returns a string indicating which segments correspond to a given value for
    SPD.
    """
    return " ".join(
        map(
            lambda seg: "X" if seg in SPEED_CHART[spd] else ".",
            range(1,13))
        )
        
def next_common_speed(rnd, curseg, oldspd, newspd):
    """
    Returns the next segment at which both of two different values of SPD get
    an action.
    """
    # FIXME: fails for SPD 0 and SPD 1.
    oldsegs = SPEED_CHART[oldspd]
    newsegs = SPEED_CHART[newspd]
    
    common_segs = filter(lambda seg: seg in newsegs, oldsegs)
    future_common_segs = filter(
        lambda seg: seg >= curseg,
        common_segs)
        
    if len(future_common_segs) == 0:
        return (rnd+1, min(common_segs))
    else:
        return (rnd, min(future_common_segs))
        
## MAIN TEST ##
        
if __name__ == "__main__":
    HeroShell().cmdloop()

