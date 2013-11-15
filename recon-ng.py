#!/usr/bin/env python

import optparse
import sys
# prep python path for base module
sys.path.append('./core/')
import base

def recon_ui(opts):
    # set up command completion
    try:
        import readline
    except ImportError:
        print '%s[!] Module \'readline\' not available. Tab complete disabled.%s' % (R, N)
    else:
        import rlcompleter
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind('bind ^I rl_complete')
        else:
            readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(readline.get_completer_delims().replace('/', ''))
        # for possible future use to format command completion output
        #readline.set_completion_display_matches_hook(display_hook)
    x = base.Recon()
    # check for and load workspace
    if opts.workspace: x.do_workspace(opts.workspace)
    # check for and run script session
    if opts.script_file: x.do_resource(opts.script_file)
    try: x.cmdloop()
    except KeyboardInterrupt: print ''

usage = './%prog [options]'
description = '%%prog - %s %s' % (base.__author__, base.__email__)
parser = optparse.OptionParser(usage=usage, description=description, version=base.__version__)
parser.add_option('-w', help='load/create a workspace', metavar='workspace', dest='workspace', type='string', action='store')
parser.add_option('-r', help='load commands from a resource file', metavar='filename', dest='script_file', type='string', action='store')
(opts, args) = parser.parse_args()
recon_ui(opts)
