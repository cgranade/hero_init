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

* Qt-based GUI built using `PySide`_.

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

1. Ensure that you have `PySide`_ installed.
2. Download the `latest version of hero_init`_ from GitHub.
3. Extract the tarball (note that GitHub changes the filename each version,
   so you type whatever you downloaded instead of "e165c97")::

    $ tar xf cgranade-hero_init-e165c97.tar.gz
    $ cd cgranade-hero_init-e165c97
    
4. Run the ``hero_init`` package in ``src/``.
   
    $ python src/hero_init
   
.. _PySide: http://qt-project.org/wiki/Get-PySide
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
at the bottom of the main window. Interactive help on these commands appears below
the command-line.

Individual combatants are referred to either by their full names (in quotes if need
be), or by a prefix that uniquely identifies that combatant. For instance, if
*Alice* and *Bob* are combatants, ``h A S 12`` will heal (``h``) Alice
of 12 STUN damage.

Commands
--------

Managing Combatants
~~~~~~~~~~~~~~~~~~~

``add`` *name* *spd* *dex* *stun* *body* *end* [PC | NPC] [*status*]
  Adds a new combatant, named *name*, to the current combat.
  
  The combatant will have SPD *spd* and DEX *dex*, and will have maximum
  characteristic values given by *stun*, *body* and *end*. The combatant
  will be an NPC unless specified by the string ``PC``. The *status* argument
  sets an optional status string for that combatant.
  
``del`` *name*
  Removes one combatant from the combat.
  
Time and SPD
~~~~~~~~~~~~

{``next`` | ``n``}
  Advances to the next turn.

``abort`` *name*
  Causes *name* to abort their next phase, if possible. Otherwise, a warning
  is displayed indicating why the abort is illegal.

``chdex`` - not yet implemented

``chspd`` *name* *new_spd*
  Sets the SPD value for *name* to the value given, and changes their
  placement on the segment chart accordingly.

Damage and Healing
~~~~~~~~~~~~~~~~~~

{``dmg`` | ``d``} *name* { ``S`` | ``B``| ``E`` } *amt*
  Applies damage of *amt* to *name*'s STUN, BODY or END.

{``heal`` | ``h``} *name* { ``S`` | ``B``| ``E`` } *amt*
  Heals damage of *amt* to *name*'s STUN, BODY or END.

Scripting
~~~~~~~~~

``run`` *file*
  Loads the specified file and executes each command at the **hero_init** shell.
  Useful for describing combat scenarios ahead-of-time. (And yes, a script
  loaded in this way can call other scripts.)

Embedded Server
~~~~~~~~~~~~~~~

{``server start`` port | ``server stop``}
  Starts or stops an embedded webserver on port 8080, or the specified *port*.
  This webserver does not implement any security, and will provide anyone with
  combat details on all player characters, but not on any non-player characters.
  The webserver is intended for use with phones or tablets, but will also work
  in desktop and laptop browsers.

