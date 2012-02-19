=========
hero_init
=========

Introduction
============

**hero_init** is an initiative and damage tracker for the HERO System
roleplaying game, providing the gamemaster with tools to quickly manage combat
and disseminate combat information to players. GMs can script combat scenarios
ahead of time, while players can view pertinent combat information on their
smartphones or tablets.

Features include:

* Command-line and Gtk 3 gamemaster consoles.

* Quick input using miniature command-line interpreter.

* All GM commands can be scripted ahead of time for quick combat setup.

* Embedded web server provides players with health and initiative information for their characters while maintaining surprise about non-player characters.
  
* Designed to require only minimal dependencies for easy installation.

Installation
============

Right now, this section is pretty bare, as I have only tested **hero_init** on
my own (Linux) machines.

Linux
-----

1. Download the `latest version of hero_init`_ from GitHub.
2. Extract the tarball (note that GitHub changes the filename each version,
   so you type whatever you downloaded instead of "e165c97")::

    $ tar xf cgranade-hero_init-e165c97.tar.gz
    $ cd cgranade-hero_init-e165c97
    
3. Run either "hero_init.py" for the command-line front end, or
   "gtk_hero_init.py" for the graphical frontend (requires Gtk v3.0 or later
   along with PyGObject --- both of these are standard in most recent Linux
   distributions)::
   
    $ python hero_init.py
    $ python gtk_hero_init.py
   

.. _`latest version of hero_init`: https://github.com/cgranade/hero_init/tarball/master

Mac OS X
--------

TODO

Windows
-------

TODO


Usage
=====

**hero_init** is controlled via the miniature command-line interpreter provided
with either the command-line or graphical frontends. Interactive help has not
yet been implemented in the graphical front end, but in the command-line
frontend, a list of commands may always be obtained by running ``help``. Likewise,
documentation on a specific command can be obtained by running ``help cmd``,
where *cmd* is the name of the command.

Commands
--------

``add`` *id* *name* *spd* *dex* *stun* *body* *end*
  Adds a new combatant, named *name*, to the current combat. The new combatant
  will be referred to by the ID given by *id* in any context where the GM
  selects a particular combatant.
  
  The combatant will have SPD *spd* and DEX *dex*, and will have maximum
  characteristic values given by *stun*, *body* and *end*.
  
``ls``
  Lists all combatants (useful only at the command-line).
  
``lsseg``
  Lists all combatants moving in the current segment
  (useful only at the command-line).
  
``next`` or ``n``
  Advances time to the next action and shows which combatants get to move in the
  that DEX.
 
``dmg`` or ``d`` *id* *characteristic* *amt*
  Damages the given *characteristic* of combatant *id* by *amt*. If
  *characteristic* is not given, defaults to damaging STUN.  
  
``abort`` *id*
  Causes the combatant given by *id* to abort their next phase.
  
``setpc`` *id* *is_pc*
  Sets combatant *id* as being a player character if *is_pc* is True-like.
  By default, all combatants are not marked as PCs. Any PC combatant's details
  may be viewed from the embedded webserver if it is running.
  
``setspd`` *id* *newspd*
  Changes the speed of combatant *id* and sets their next action accordingly.
  
``run`` *file*
  Loads the specified file and executes each command at the **hero_init** shell.
  Useful for describing combat scenarios ahead-of-time. (And yes, a script
  loaded in this way can call other scripts.)

``server start`` or ``server stop``
  Starts or stops an embedded webserver on port 8080. This webserver does not
  implement any security, and will provide anyone with combat details on all
  player characters, but not on any non-player characters. The webserver is
  intended for use with phones or tablets, but will also work in desktop and
  laptop browsers.

``lightning`` *id* *descript* *dex bonus*
  Augments the given combatant with the Lightning Reflexes talent at a given
  DEX bonus. Note that this command is still not very robust, and may not
  perform exactly as intended yet.
  
``exit``
  Closes the frontend, stopping the embedded webserver if needed.

Limitations
===========

Currently, the command-line parser does not support any arguments with spaces.
In particular, this means that no character's name may have spaces.
