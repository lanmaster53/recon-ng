#!/usr/bin/env python3

import argparse
import sys
# prevent creation of compiled bytecode files
sys.dont_write_bytecode = True
from recon.core import base
from recon.core.framework import Colors

def output(string):
    print(f"{Colors.B}[*]{Colors.N} {string}")

def recon_cli(args):
    # process toggle flag arguments
    flags = {
        'check': args.check if not args.stealth else False,
        'analytics': args.analytics if not args.stealth else False,
        'marketplace': args.marketplace if not args.stealth else False,
    }
    # instantiate framework
    x = base.Recon(**flags)
    options = [base.Mode.CLI]
    if args.workspace:
        options.append(args.workspace)
    x.start(*options)
    # set given workspace
    if args.workspace:
        x._init_workspace(args.workspace)
        print(f"WORKSPACE => {args.workspace}")
    # run given global commands
    for command in args.global_commands:
        print(f"GLOBAL COMMAND => {command}")
        x.onecmd(command)
    # set given global options
    for option in args.goptions:
        param = ' '.join(option.split('='))
        x._do_options_set(param)
    # if requested, show global options and exit
    if args.gshow:
        x._do_options_list('')
        return
    # if requested, show modules and exit
    if args.show_modules:
        x._do_modules_search('')
        return
    # exit if module not specified
    if not args.module:
        output('No module provided.')
        return
    # load the module
    y = x._do_modules_load(args.module)
    # exit if module not successfully loaded
    if not y: return
    print(f"MODULE => {args.module}")
    # run given module commands
    for command in args.module_commands:
        print(f"MODULE COMMAND => {command}")
        y.onecmd(command)
    # set given module options
    for option in args.options:
        param = ' '.join(option.split('='))
        y._do_options_set(param)
    # if requested, show module options and exit
    if args.show:
        y._do_options_list('')
        return
    if args.run:
        # run the module
        y.do_run(None)

description = f"%(prog)s - {base.__author__}"
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-w', help='load/create a workspace', metavar='workspace', dest='workspace', action='store')
parser.add_argument('-C', help='runs a command at the global context', metavar='command', dest='global_commands' ,default=[], action='append')
parser.add_argument('-c', help='runs a command at the module context (pre-run)', metavar='command', dest='module_commands' ,default=[], action='append')
parser.add_argument('-G', help='show available global options', dest='gshow', default=False, action='store_true')
parser.add_argument('-g', help='set a global option (can be used more than once)', metavar='name=value', dest='goptions', default=[], action='append')
parser.add_argument('-M', help='show modules', dest='show_modules', default=False, action='store_true')
parser.add_argument('-m', help='specify the module', metavar='module', dest='module', action='store')
parser.add_argument('-O', help='show available module options', dest='show', default=False, action='store_true')
parser.add_argument('-o', help='set a module option (can be used more than once)', metavar='name=value', dest='options', default=[], action='append')
parser.add_argument('-x', help='run the module', dest='run', default=False, action='store_true')
parser.add_argument('--no-version', help='disable version check', dest='check', default=True, action='store_false')
parser.add_argument('--no-analytics', help='disable analytics reporting', dest='analytics', default=True, action='store_false')
parser.add_argument('--no-marketplace', help='disable remote module management', dest='marketplace', default=True, action='store_false')
parser.add_argument('--stealth', help='disable all passive requests (--no-*)', dest='stealth', default=False, action='store_true')
parser.add_argument('--version', help='displays the current version', action='version', version=base.__version__)
args = parser.parse_args()
recon_cli(args)
