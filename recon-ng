#!/usr/bin/env python3

import argparse
import re
import sys
# prevent creation of compiled bytecode files
sys.dont_write_bytecode = True
from recon.core import base
from recon.core.framework import Colors

def recon_ui(args):
    # set up command completion
    try:
        import readline
    except ImportError:
        print(f"{Colors.R}[!] Module 'readline' not available. Tab complete disabled.{Colors.N}")
    else:
        import rlcompleter
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind('bind ^I rl_complete')
        else:
            readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(re.sub('[/-]', '', readline.get_completer_delims()))
        # for possible future use to format command completion output
        #readline.set_completion_display_matches_hook(display_hook)
    # process toggle flag arguments
    flags = {
        'check': args.check if not args.stealth else False,
        'analytics': args.analytics if not args.stealth else False,
        'marketplace': args.marketplace if not args.stealth else False,
        'accessible' : args.accessible
    }
    # instantiate framework
    x = base.Recon(**flags)
    # check for and run script session
    if args.script_file:
        x._do_script_execute(args.script_file)
    # launch the interactive session
    options = [base.Mode.CONSOLE]
    if args.workspace:
        options.append(args.workspace)
    try:
        x.start(*options)
    except KeyboardInterrupt:
        print('')

description = f"%(prog)s - {base.__author__}"
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-w', help='load/create a workspace', metavar='workspace', dest='workspace', action='store')
parser.add_argument('-r', help='load commands from a resource file', metavar='filename', dest='script_file', action='store')
parser.add_argument('--no-version', help='disable version check', dest='check', default=True, action='store_false')
parser.add_argument('--no-analytics', help='disable analytics reporting', dest='analytics', default=True, action='store_false')
parser.add_argument('--no-marketplace', help='disable remote module management', dest='marketplace', default=True, action='store_false')
parser.add_argument('--stealth', help='disable all passive requests (--no-*)', dest='stealth', default=False, action='store_true')
parser.add_argument('--accessible', help='Use accessible outputs when available', dest='accessible', default=False, action='store_true')
parser.add_argument('--version', help='displays the current version', action='version', version=base.__version__)
args = parser.parse_args()
recon_ui(args)
