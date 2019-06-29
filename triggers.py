#!/usr/bin/python
#
# HostWatch Terminator Plugin
# Copyright (C) 2019 Stan Putrya
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
NAME
  triggers.py - Terminator plugin for automatically make predefined action if last terminal line contain pattern

DESCRIPTION
  This plugin monitors the last line of each terminator terminal, and 
  applies a action that was defined in config. 

INSTALLATION
  
  Put this .py in /usr/share/terminator/terminatorlib/plugins/triggers.py 
  or ~/.config/terminator/plugins/triggers.py.

CONFIGURATION

  Plugin section in .config/terminator/config :
  [plugins]
    [[Triggers]]
  
  Configuration keys :
  - 
   
DEVELOPMENT
  Development resources for the Python Terminator class and the 'libvte' Python 
  bindings can be found here:

  For terminal.* methods, see: 
    - http://bazaar.launchpad.net/~gnome-terminator/terminator/trunk/view/head:/terminatorlib/terminal.py
    - and: apt-get install libvte-dev; less /usr/include/vte-0.0/vte/vte.h

  For terminal.get_vte().* methods, see:
    - https://github.com/linuxdeepin/python-vte/blob/master/python/vte.defs
    - and: apt-get install libvte-dev; less /usr/share/pygtk/2.0/defs/vte.defs

DEBUGGING
  To debug the plugin, start Terminator from another terminal emulator 
  like this:

     $ terminator --debug-classes=Triggers
     ...

AUTHORS
  The plugin bysed on idea of plugin HostWatch that was developed by GratefulTony (https://github.com/GratefulTony/TerminatorHostWatch), 
  Watchers plugin is developing by Stan Putrya (https://github.com/svagner/TerminatorTriggers)
"""

import re
import os
import cmd
import subprocess

import terminatorlib.plugin as plugin

from terminatorlib.util import err, dbg
from terminatorlib.terminator import Terminator
from terminatorlib.config import Config

PLUGIN_NAME = 'Triggers'
AVAILABLE = [PLUGIN_NAME]
available = [PLUGIN_NAME]

try:
    import pynotify
except ImportError:
    err('Triggers plugin unavailable: pynotify unavailable')

# Difines action commands
class TriggersCommand(cmd.Cmd):
  def do_exec(self, line):
    process = subprocess.Popen(line.split(), stdout=subprocess.PIPE)
    output, _ = process.communicate()
    res = output.rstrip().split('\n')
    if len(res) > 0:
      return res[-1]
    return ''

  def do_input(self, line):
      return line

class Triggers(plugin.Plugin):
  watches = {}
  config={}
  capabilities = ['input_watch']
  
  def __init__(self):
    self.config = Config().plugin_get_config(self.__class__.__name__)
    self.triggers = {}
    self.watches = {}
    self.load_triggers()
    self.update_watches()
                    
  def update_watches(self):
    for terminal in Terminator().terminals:
      if terminal not in self.watches:
        self.watches[terminal] = terminal.get_vte().connect('contents-changed', self.check_input, terminal)

  def check_input(self, _vte, terminal):
    self.update_watches()
    last_line = self.get_last_line(terminal)

    if last_line:        
        dbg('Check line: {}'.format(last_line))

        for expect,cmd in self.triggers.items():
          if re.match(expect, last_line):
            res = TriggersCommand().onecmd(cmd['action'])
            dbg('Match {}. Result: {}'.format(expect, res))
            self.insert_to_terminal(terminal, res, cmd['new_line'])
    return True

  def insert_to_terminal(self, terminal, text, new_line = False):
    if not isinstance(text, str):
      dbg('Incorrect input for terminal (should be string): {}'.format(text))
      return
    if len(text) == 0:
      dbg('Incorrect input for terminal (empty string)')
      return
    vte = terminal.get_vte()
    pty = vte.get_pty()
    fd = pty.get_fd()
    text = text.rstrip()
    if new_line:
      text += '\n'
    os.write(fd, text)

  def get_last_line(self, terminal):
    vte = terminal.get_vte()

    cursor = vte.get_cursor_position()
    column_count = vte.get_column_count()
    row_position = cursor[1]
      
    start_row = row_position
    start_col = 0
    end_row = row_position
    end_col = column_count
    is_interesting_char = lambda a, b, c, d: True
      
    lines= vte.get_text_range(start_row, start_col, end_row, end_col, is_interesting_char)

    return lines[0].split('\n')[-1]

  def load_triggers(self):
    for k,v in self.config.items():
      dbg("Load trigger [{}]".format(k))
      if 'action' not in v or 'expect' not in v:
        continue
      newLine = False
      if 'new_line' in v:
        newLine = v['new_line']
      self.triggers[v['expect']] = {'new_line': newLine, 'action': v['action']}