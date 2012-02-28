#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# util.py: Useful but miscellaneous utilities.
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

import shlex
from functools import wraps

def shlexify(func):
    @wraps(func)
    def shlexed_func(*args):
        head = args[0:-1]
        tail = args[-1]
        return func(*(head + tuple(shlex.split(tail))))
    
    return shlexed_func
    
if __name__ == "__main__":
    @shlexify
    def test_func(dummy, arg1, arg2, arg3):
        print "dummy: {dummy}".format(dummy=dummy)
        print arg1, "*", arg2, "*", arg3
        
    test_func('dummy', 'a "b c d" e')
    
