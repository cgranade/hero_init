#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# hero_server.py: Server for reporting player character status to player phones.
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

import BaseHTTPServer as serv
import threading
import urlparse as up


from SocketServer import ThreadingMixIn
from multiprocessing import Process, Pipe

from hero_init import SPEED_CHART

## CONSTANTS ##

# Template for player character selection menu.
#
# Variables:
#     pc_list_content -
#         <li> items corresponding to the list of player characters.
PC_SELECT_PAGE_TEMPLATE = r"""
<!DOCTYPE html> 
<html> 
	<head> 
	<title>HeroInit</title> 
	
	<meta name="viewport" content="width=device-width, initial-scale=1"> 

	<link rel="stylesheet" href="http://code.jquery.com/mobile/1.0.1/jquery.mobile-1.0.1.min.css" />
	<script src="http://code.jquery.com/jquery-1.6.4.min.js"></script>
	<script src="http://code.jquery.com/mobile/1.0.1/jquery.mobile-1.0.1.min.js"></script>
</head> 

<body> 

    <div data-role="header">
		<h1>HeroInit: Select Player Character</h1>
	</div><!-- /header -->

	<div data-role="content">	
		<ul data-role="listview" data-theme="g">
	        {pc_list_content}
        </ul>		
	</div><!-- /content -->

	<!--<div data-role="footer">
		<h4>Page Footer</h4>
	</div>--><!-- /footer -->

</body>
</html>
"""

# FIXME: currently info is updated by refreshing the page.
#        This is a terrible way of doing things!

# Template for player character status page.
#
# Variables:
#     pc_name -
#         Name of the player character represented on the status page.
#     moves_this_dex -
#         Banner present when the represented player character has an action in
#         the current DEX.
#     now -
#         String representing the current time.
#     next_turn -
#         String representing the time at which the player character gets their
#         next action.
#     segment_list -
#         List of segments in which the player character gets to act.
#     pc_characteristics -
#         String representing <li> items the various characteristics of the
#         player character.
PC_DETAILS_PAGE_TEMPLATE = r"""
<!DOCTYPE html> 
<html> 
	<head> 
	<title>{pc_name} Status</title> 
	
	<meta name="viewport" content="width=device-width, initial-scale=1"> 

	<link rel="stylesheet" href="http://code.jquery.com/mobile/1.0.1/jquery.mobile-1.0.1.min.css" />
	<script src="http://code.jquery.com/jquery-1.6.4.min.js"></script>
	<script src="http://code.jquery.com/mobile/1.0.1/jquery.mobile-1.0.1.min.js"></script>
</head> 

<body> 

    <div data-role="header">
		<h1 id="pc_name">{pc_name}</h1>
	</div><!-- /header -->

    <div data-role="content">
    
		<ul data-role="listview" data-inset="true" data-count-theme="a">
		    <li data-role="list-divider">Initiative</li>
		    {moves_this_dex}
		    <li>
		        <p><strong>Current time:</strong></p>
		        <p>{now}</p>
		    </li>
		    <li>
		        <p><strong>Next action:</strong></p>
		        <p>{next_turn}</p>
	        </li>
	        <li>
	            <p><strong>Segments:</strong></p>
	            <p>{segment_list}</p>
	        </li>
		    <li data-role="list-divider">Characteristics</li>
	        {pc_characteristics}
        </ul>		
        
	</div><!-- /content -->

    <script type="text/javascript">
        setTimeout("window.location.reload()", 2000);
    </script>

</body>
</html>
"""

# Template for player character characteristic display.
#
# Variables:
#     name -
#         Name of the characteristic.
#     cur -
#         Current value of the characteristic.
#     max -
#         Maximum value of the characteristic.
PC_CHARACTERISTIC_TEMPLATE = """
    <li>{name}  <span class="ui-li-count">{cur}/{max}</span></li>
"""
## CLASSES ##

def combatant_as_li(combatant):
    """
    Returns a <li> representing a combatant, with a link to their player
    character status page.
    """
    return '<li><a href="pc/{0.shortname}">{0.name}</a></li>'.format(combatant)

class HeroHandler(serv.BaseHTTPRequestHandler):
    def __init__(self, combat, *args):
        self.combat = combat
        serv.BaseHTTPRequestHandler.__init__(self, *args)
        
    #def log_message(self, *args):
    #    pass
        
    def log_request(self, *args):
        pass

    def do_GET(self):
        parsed_path = up.urlparse(self.path)
        
        if parsed_path.path == "/":
        
            self.send_response(200)
            self.end_headers()
            
            self.wfile.write(PC_SELECT_PAGE_TEMPLATE.format(
                pc_list_content = "\n".join(map(combatant_as_li,
                self.combat.get_all_pcs()
            ))))
            
        elif parsed_path.path.startswith("/pc/"):
            
            pathparts = parsed_path.path.split("/")
            pc_id = pathparts[-1]
            
            
            try:
                combatant = self.combat.get_combatant_by_id(pc_id)
                
                
                self.send_response(200)
                self.end_headers()
                        
                if combatant in self.combat.combatants_this_dex():
                    moves_this_dex = '<li data-theme="e" data-icon="alert">You have an action this DEX!</li>'
                else:
                    moves_this_dex = ""
                        
                pc_characteristics = "\n".join(map(
                    lambda characteristic: PC_CHARACTERISTIC_TEMPLATE.format(
                        name=characteristic.name,
                        max=characteristic.maxval,
                        cur=characteristic.current
                    ),
                    combatant.characteristics.values()
                    ))
                        
                self.wfile.write(PC_DETAILS_PAGE_TEMPLATE.format(
                    pc_name = combatant.name,
                    next_turn = combatant.next,
                    now = repr(self.combat.get_now()).replace(" ∞", "&#8734;"),
                    segment_list=", ".join(map(str, SPEED_CHART[combatant.spd])),
                    pc_characteristics=pc_characteristics,
                    moves_this_dex = moves_this_dex
                ))
                
                
            except ValueError:
                self.send_response(404)
                self.end_headers()
                
                self.wfile.write("{pc_id} not in combat.".format(pc_id=pc_id))
        
        return


# Trigger functions cause problems, so we need to strip them.
# We also need to make sure we send a copy.
def prep_combatant_list(combatant_list):
    return map(lambda combatant: combatant.snapshot(), combatant_list)

class CombatReciever(threading.Thread):
    def __init__(self, combat, pipe):
        threading.Thread.__init__(self)
        self.combat = combat
        self.pipe = pipe
        self.stopflag = False
        
    def recvonce(self):
        if not self.pipe.poll(0.01):
            return
            
        cmd = self.pipe.recv()
        if cmd == "get_now":
            self.pipe.send(self.combat.get_now())
        elif cmd == "get_by_id":
            cmb_id = self.pipe.recv()
            self.pipe.send(self.combat.get_combatant_by_id(cmb_id).snapshot())
        elif cmd == "combatants_this_dex":
            self.pipe.send(prep_combatant_list(self.combat.combatants_this_dex()))
        elif cmd == "get_all_pcs":
            res = self.combat.get_all_pcs()
            self.pipe.send(prep_combatant_list(res))
            
        return True
        
    def stop(self):
        self.stopflag = True
        
    def run(self):
        self.stopflag = False
        while not self.stopflag:
            self.recvonce()
                
class CombatProxy(object):
    def __init__(self, pipe):
        self.pipe = pipe
    
    def get_now(self):
        self.pipe.send("get_now")
        return self.pipe.recv()
        
    def get_combatant_by_id(self, cmb_id):
        self.pipe.send("get_by_id")
        self.pipe.send(cmb_id)
        return self.pipe.recv()
        
    def combatants_this_dex(self):
        self.pipe.send("combatants_this_dex")
        return self.pipe.recv()
        
    def get_all_pcs(self):
        self.pipe.send("get_all_pcs")
        return self.pipe.recv()

class HeroServer(object):
    def __init__(self, combat, recv_method="thread"):
        self.combat = combat
        self.is_child = False
        self.child_proc = None
        
        self.recv_method = recv_method
        
    def mk_handler(self, *args):
        return HeroHandler(self.combat, *args)
        
    def stop(self):
        if not self.is_child and self.child_proc is not None:
            # FIXME: do this without terminating by communicating gracefully.
            self.child_proc.terminate()
            self.child_proc = None
            self.parent_conn = None
            self.child_conn = None
        else:
            print "[ERROR] WTF is even happening here? Why is the child stop() being called?"
        
    def start(self):
        if not self.is_child and self.child_proc is None:
            self.parent_conn, self.child_conn = Pipe()
            
            self.child_proc = Process(target=self.run)
            self.child_proc.start()
            
            
        
            if self.recv_method == "thread":
                self.combat_receiver = CombatReciever(self.combat, self.parent_conn)
                self.combat_receiver.start()
            elif self.recv_method == "gtk":
                print "[WARNING] gtk recv_method is currently broken."
                self.combat_receiver = CombatReciever(self.combat, self.parent_conn)
                from gi.repository import GLib
                GLib.idle_add(self.combat_receiver.recvonce)
        else:
            print "[ERROR] Cannot start twice."
        
    def run(self):
        self.is_child = True
        self.combat = CombatProxy(self.child_conn)
        # TODO: make the server name and port customizable.
        
        self.http = ThreadedHTTPServer(('', 8080), self.mk_handler)
        
        self.http.serve_forever()
    

class ThreadedHTTPServer(ThreadingMixIn, serv.HTTPServer):
    """Handle requests in a separate thread."""
        
## MAIN ##
        
if __name__ == "__main__":
    pass
