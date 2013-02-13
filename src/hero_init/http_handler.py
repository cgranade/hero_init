#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# http_handler.py: Main server logic for player character displays.
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

import os
import json
import mimetypes
import urllib2
import SimpleHTTPServer
import zipfile
from contextlib import contextmanager

from combat_model import *

## CLASSES #####################################################################

class HeroEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Combatant):
            return {
                'name': obj.name,
                'spd':  obj.spd,
                'dex':  obj.dex,
                'stun': obj.stun,
                'body': obj.body,
                'end':  obj.end,
                'seg': [
                    States.reverse_mapping[seg].lower()
                    for seg in obj._segment
                ], # TODO: use reverse_mapping on segments.
                'status': obj.status,
                'kind': obj.kind,
                'current': obj.is_current
            }
            
        elif isinstance(obj, Characteristic):
            return {
                'cur': obj.cur,
                'max': obj.max
            }
            
        else:
            return super(HeroEncoder, self).default(obj)    

# Load resources from hero_init._static.
this_dir, this_fname = os.path.split(__file__)
if this_dir.endswith(".zip"):
    # We've been frozen, so handle things differently!
    our_zip = zipfile.ZipFile(this_dir, 'r')
    
    @contextmanager
    def open_resource(respath):
        with our_zip.open("hero_init/_static/" + res_path) as f:
            yield f
            
else:
    static_dir = os.path.join(this_dir, "_static")

    @contextmanager
    def open_resource(respath):
        with open(os.path.join(static_dir, respath), 'r') as f:
            yield f

def make_http_handler(model):
    # This way, the request handler will close over the value of model.
    # We also want to close over some common resources.
    
    with open_resource("index.html") as f:
        index = ""
        for line in f:
            index += line

    class HeroHTTPHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    
        ## METHODS #############################################################
        
        def do_GET(self):
            if self.path == "/":
                # Send main mobile site.
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write(index)
                
            elif self.path.startswith("/static/"):
                res_path = self.path.partition("/static/")[2]
                mime = mimetypes.guess_type(res_path)[0]
                print "static_dir == " + static_dir
                print "Loading {}, type={}".format(res_path, mime)
                self.send_response(200)
                self.send_header('Content-type', mime)
                self.end_headers()
                with open_resource(res_path) as f:
                    for line in f:
                        self.wfile.write(line)
                
            
            elif self.path.startswith("/api"):
                json_resp = None
                
                api_path = urllib2.unquote(self.path).partition("/api")[2]
                if api_path.startswith("/pcs"):
                    pc_path = api_path.partition("/pcs")[2]
                    if len(pc_path) == 0:
                        # List all PCs.
                        # FIXME: shouldn't use _combatants, as it's kind of
                        #        private.
                        json_resp = [
                            combatant
                            for combatant in model._combatants
                            if combatant.kind == "PC"
                        ]
                    else:
                        pc_name = pc_path.partition("/")[2]
                        print(pc_name)
                        try:
                            json_resp = iter(
                                combatant
                                for combatant in model._combatants
                                if combatant.kind == "PC"
                                and combatant.name == pc_name
                            ).next()
                        except StopIteration:
                            json_resp = None
                        
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(json_resp, cls=HeroEncoder))
                
            else:
                self.send_response(404)
                self.end_headers()
                return
                
    return HeroHTTPHandler
    
