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
from gi.repository import Gtk

import terminatorlib.plugin as plugin

from terminatorlib.util import err, dbg
from terminatorlib.terminator import Terminator
from terminatorlib.config import Config
from terminatorlib.terminal_popup_menu import TerminalPopupMenu

PLUGIN_NAME = 'Triggers'
AVAILABLE = [PLUGIN_NAME]
available = [PLUGIN_NAME]
keepassSupport = True

try:
  from pykeepass import PyKeePass
except ImportError:
  keepassSupport = False

try:
    import pynotify
except ImportError:
    err('Triggers plugin unavailable: pynotify unavailable')

class TriggersCommandResult(object):
  def __init__(self):
    self._result = None

  def set_result(self, result):
    self._result = result

  def get_result(self):
    return self._result

# Difines action commands
class TriggersCommand(cmd.Cmd):
  def __init__(self, keepassDb=''):
    cmd.Cmd.__init__(self)
    self.keepassMaterPassword = ''
    self.keepassDb = keepassDb
    self.lastPasswordSelect = ''

  def do_exec(self, line):
    process = subprocess.Popen(line.split(), stdout=subprocess.PIPE)
    output, _ = process.communicate()
    res = output.rstrip().split('\n')
    if len(res) > 0:
      return res[-1]
    return ''

  def ask_password(self):
    passwordInput = Gtk.Entry()
    passwordInput.set_visibility(False)

    def get_response(dialog,response_id):
      if response_id == 1:
        self.keepassMaterPassword = passwordInput.get_text()

    def activate(entry):
      self.keepassMaterPassword = passwordInput.get_text()
      
    dbox = Gtk.Dialog(("Input keepass master password"), None, Gtk.DialogFlags.MODAL)

    dbox.add_action_widget(passwordInput,0);

    dbox.add_button("OK", 1);
    dbox.add_button("CANCEL",2);
    dbox.set_default_response(1);
    dbox.set_focus(passwordInput) 

    dbox.connect("response", get_response)
    passwordInput.connect("activate", activate)
    dbox.show_all()
    dbox.run()
    dbox.destroy()

  def _get_passwords_from_keepass(self):
    kp = PyKeePass(self.keepassDb, password=self.keepassMaterPassword)
    return kp.entries

  def do_keepass(self, args):
    if not keepassSupport:
      err('triggers plugin: Keepass is not supported. Please install module pykeepass')
      return
    if not self.keepassDb:
      err('triggers plugin: Keepass support was disabled because no option keepassDb in plugin configuration')
      return

    # we will remember password for keepass in memory for prevent ask password each time
    if not self.keepassMaterPassword:
      self.ask_password()

    # see https://github.com/EliverLara/terminator-themes/blob/master/plugin/terminator-themes.py
    dbox = Gtk.Dialog(("Select password"), None, Gtk.DialogFlags.MODAL)
    main_container = Gtk.HBox(spacing=7)
    dbox.vbox.pack_start(main_container, True, True, 0)

    passwords = self._get_passwords_from_keepass()
    liststore = Gtk.ListStore(int, str, str, str)

    # create the TreeView using liststore
    treeview = Gtk.TreeView()
    treeview.set_model(model=liststore)  
    
    def password_search(search_entry):
      search_text = search_entry.get_text()
      liststore.clear()
      for idx, passwd in enumerate(passwords):
        if search_text.lower() in passwd.username.lower():
          liststore.append((idx, passwd.username, passwd.title, passwd.group.name))
      treeview.set_cursor(0)

    searchInput = Gtk.SearchEntry()
    searchInput.set_text(self.lastPasswordSelect)
    searchInput.set_can_focus(True)
    searchInput.set_visible(True)
    searchInput.set_hexpand(False)
    searchInput.set_vexpand(False)
    searchInput.connect('search_changed', password_search)

    dbox.vbox.pack_start(searchInput, True, True, 0)

    # create the TreeViewColumns to display the data
    columns = [
      Gtk.TreeViewColumn('#id', Gtk.CellRendererText(),
                                    text=0),
      Gtk.TreeViewColumn('Login', Gtk.CellRendererText(),
                                    text=1),
      Gtk.TreeViewColumn('Description', Gtk.CellRendererText(),
                                    text=2),
      Gtk.TreeViewColumn('Group', Gtk.CellRendererText(),
                                    text=3),
    ]

    for idx, passwd in enumerate(passwords):
      liststore.append((idx, passwd.username, passwd.title, passwd.group.name))

    treeview.set_cursor(0)

    # add columns to treeview
    for col in columns:
      treeview.append_column(col)

    #dbox.vbox.pack_start(main_container, True, True, 0)
    dbox.vbox.pack_start(treeview, True, True, 0)

    dbox.add_button("OK", 1)
    dbox.add_button("CANCEL",2)
    dbox.set_default_response(1)

    result = TriggersCommandResult()

    def get_response(dialog,response_id, res):
      if response_id == 1:
        sel = treeview.get_selection()
        tm, ti = sel.get_selected()
        id = tm.get_value(ti, 0)
        res.set_result(passwords[id].password)

    def activate(entry, res):
      sel = treeview.get_selection()
      tm, ti = sel.get_selected()
      id = tm.get_value(ti, 0)
      res.set_result(passwords[id].password)
      dbox.destroy()

    dbox.connect("response", get_response, result)
    searchInput.connect("activate", activate, result)

    self.dbox = dbox
    dbox.show_all()
    dbox.run()

    del(self.dbox)
    dbox.destroy()

    return result.get_result()

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
    self.dialog_in_process = set()
    keepassDb = ''
    if 'keepassDb' in self.config:
      keepassDb = self.config['keepassDb']
    self.triggersCommand = TriggersCommand(keepassDb)
                    
  def update_watches(self):
    for terminal in Terminator().terminals:
      if terminal not in self.watches:
        self.watches[terminal] = terminal.get_vte().connect('contents-changed', self.check_input, terminal)

  def check_input(self, _vte, terminal):
    if terminal in self.dialog_in_process:
      return True
    self.dialog_in_process.add(terminal)
    self.update_watches()
    last_line = self.get_last_line(terminal)

    if last_line:        
        dbg('Check line: {}'.format(last_line))

        for expect,cmd in self.triggers.items():
          if re.match(expect, last_line):
            try:
              res = self.triggersCommand.onecmd(cmd['action'])
            except Exception as e:
              err("Error while execute command {}: {}".format(cmd['action'], str(e)))
              break
            dbg('Match {}. Result: {}'.format(expect, res))
            self.insert_to_terminal(terminal, res, cmd['new_line'])
            break
    self.dialog_in_process.remove(terminal)
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
      if not isinstance(v, dict):
        continue
      dbg("Load trigger [{}]".format(k))
      if 'action' not in v or 'expect' not in v:
        continue
      newLine = False
      if 'new_line' in v:
        newLine = v['new_line']
      self.triggers[v['expect']] = {'new_line': newLine, 'action': v['action']}