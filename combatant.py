#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# combatant.py: Model of a combatant in HERO System 6e.
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

import hero_init as hi
from constants import *

## FUNCTIONS ##

def lightning_reflexes(combat, combatant, description, dexboost):
    # FIXME: does not support multiple applications of lightning_reflexes.
    
    from functools import wraps
    
    @wraps(combatant.calc_next_segment)
    def modified_calc_next_segment(*args, **kwargs):
        regular_next = combatant._hidden_calc_next_segment(*args, **kwargs)
        def trigger():
            # FIXME: prompt the DM whether the lightning_reflexes action
            #        was taken or not.
            combatant.next = regular_next
            
            # Return False to indicate that this trigger is handling the
            # calculation of the next segment automatically.
            # See Combatant.post_phase() for details.
            return False
            
        combatant.next = hi.Time(
            regular_next.rnd,
            regular_next.seg,
            regular_next.dex + dexboost,
            comment=description,
            trigger_fn=trigger)
            
        return combatant.next
            
    combatant._hidden_calc_next_segment = combatant.calc_next_segment
    combatant.calc_next_segment = modified_calc_next_segment
    
    old_turn = combatant.next
    hypothetical_lightning_turn = combatant.calc_next_segment()
    
    if hypothetical_lightning_turn >= combat.now:
        combatant.next = hypothetical_lightning_turn
    else:
        combatant.next = old_turn

## CLASSES ##

class Characteristic(object):
    def __init__(self, name, maxval=None, current=None):
        self.name = name
        self.maxval = maxval
        self.current = current if current is not None else maxval

class Combatant(object):
    def __init__(self, combat,
            shortname, name,
            spd, dex,
            maxstun,
            maxbody,
            maxend,
            pc=False
        ):
        
        self.shortname = shortname
        self.name   = name
        self.combat = combat
        self.spd    = spd
        self.dex    = dex
        
        self.pc     = pc
        
        self.characteristics = {
            'STUN': Characteristic('STUN', maxstun),
            'BODY': Characteristic('BODY', maxbody),
            'END' : Characteristic('END',  maxend)
        }
        
        
        if combat is not None:
            self.next   = self.calc_next_segment(inc_this=True)        
            combat._add_combatant(self)
        else:
            self.next = None
            self.combat = None

    def snapshot(self):
        from copy import copy
        
        copyself = Combatant(
            combat=None,
            shortname=self.shortname,
            name=self.name,
            spd=self.spd,
            dex=self.dex,
            maxstun=0,
            maxbody=0,
            maxend=0,
            pc=self.pc
            )
            
        copyself.next = copy(self.next)
        if copyself.next.trigger_fn is not None:
            copyself.next.trigger_fn = None
        
        copyself.characteristics = self.characteristics
        
        return copyself
        
    def change_speed(self, newspd):
        newrnd, newseg = next_common_speed(
            rnd=self.combat.now.rnd,
            curseg=self.combat.now.seg,
            oldspd=self.spd,
            newspd=newspd
            )
            
        self.next = hi.Time(newrnd, newseg, self.dex)
        self.spd = newspd
        
        self.combat._update()
        
    def calc_next_segment(self, inc_this=None, now=None):
        segs = SPEED_CHART[self.spd]
        if now is None:
            now  = self.combat.now

        if inc_this is None:
            # Only consider this turn if the combatant moves later in the turn.
            # Otherwise, we assume that his/her action has completed.
            inc_this = self.next.dex < self.combat.now.dex
        
        filt_fn = (
            (lambda seg: seg > now.seg) if not inc_this else
            (lambda seg: seg >= now.seg))
        
        segs_left = filter(filt_fn, segs)
        
        if len(segs_left) == 0:
            self.next = hi.Time(self.combat.now.rnd + 1, segs[0], self.dex)
        else:
            self.next = hi.Time(self.combat.now.rnd, segs_left[0], self.dex)
            
        return self.next
        
    def abort_phase(self):
        self.calc_next_segment(inc_this=False, now=self.next[1])
        self.combat._update()
        
    def post_phase(self):
        """
        Called whenever a phase is completed.
        Does by default; intended to be changed by powers.
        
        Return False from this method to cancel advancing to the next segment
        automatically.
        """
        ret = self.next.trigger()
        if ret is not None:
            return ret
        else:
            return True

    def __repr__(self):
        char_str = "   ".join([
            "{name}: {cur}/{max}".format(name=key, cur=val.current, max=val.maxval)
            for key, val in self.characteristics.items()
        ])
        return "{name:<20}{spd}\t{dex}\t{next}\n\t\t{characteristics}".format(
            name=self.name, spd=hi.spd_string(self.spd),
            dex=self.dex,
            next=self.next,
            characteristics=char_str
        )

