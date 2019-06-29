# TerminatorTriggers
Terminator plugin for automatically make predefined action if last terminal line contain pattern

## INSTALLATION

Put this .py in /usr/share/terminator/terminatorlib/plugins/triggers.py or ~/.config/terminator/plugins/triggers.py.

## CONFIGURATION

Plugin section in .config/terminator/config :
[plugins]
[[Triggers]]

Configuration keys :
- [[[name_of_pattern]]] - using only for grouping
- new_line - add new line char after auto input
- expect - regexp for text in line with cursor position. If regexp is matching apply `action`
- action - execute action if `expect` was matched.


Actions:
- input [some text] - insert line defined in input derective
- exec [command with arguments] - exec command and input last line of stdout to terminal. Be aware: new line of stdout will be removed


Configuration example:

```
[plugins]
[[Triggers]]
[[[input_password]]]
new_line = True
expect = "^Password:\s+$"
action = input mysuperpassword
[[[input_token]]]
new_line = True
expect = "Token:\s+$"
action = exec get_my_token.sh --service google.com
```

## DEVELOPMENT
Development resources for the Python Terminator class and the 'libvte' Python bindings can be found here:

  For terminal.* methods, see:
    - http://bazaar.launchpad.net/~gnome-terminator/terminator/trunk/view/head:/terminatorlib/terminal.py
    - and: apt-get install libvte-dev; less /usr/include/vte-0.0/vte/vte.h

  For terminal.get_vte().* methods, see:
    - https://github.com/linuxdeepin/python-vte/blob/master/python/vte.defs
    - and: apt-get install libvte-dev; less /usr/share/pygtk/2.0/defs/vte.defs

## DEBUGGING
  To debug the plugin, start Terminator from another terminal emulator
  like this:

     $ terminator --debug-classes=Triggers
     ...

## AUTHORS
  The plugin bysed on idea of plugin HostWatch that was developed by GratefulTony (https://github.com/GratefulTony/TerminatorHostWatch),
  Watchers plugin is developing by Stan Putrya (https://github.com/svagner/TerminatorTriggers)
