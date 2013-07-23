#!/usr/bin/env python

import optparse
import sys
# prep python path for base module
sys.path.append('./core/')
import base

def recon_cli(opts):
    x = base.Recon(mode=1)
    # set the given workspace
    if opts.workspace: x.do_set('workspace %s' % (opts.workspace))
    # set given global options
    for option in opts.goptions:
        param = ' '.join(option.split('='))
        x.do_set(param)
    # if requested, show global options and exit
    if opts.gshow:
        x.do_show('options')
        return
    # if requested, show modules and exit
    if opts.show_modules:
        x.do_show('modules')
        return
    # exit if module not specified
    if not opts.module:
        print '%s[!] Module required.%s' % (R, N)
        return
    # load the module
    y = x.do_load(opts.module)
    # exit if module not successfully loaded
    if not y: return
    # set given module options
    for option in opts.options:
        param = ' '.join(option.split('='))
        y.do_set(param)
    # if requested, show module options and exit
    if opts.show:
        y.do_show('options')
        return
    # run the module
    y.do_run(None)

usage = './%prog [options]'
description = '%%prog - %s %s' % (base.__author__, base.__email__)
parser = optparse.OptionParser(usage=usage, description=description, version=base.__version__)
parser.add_option('-w', help='load/create a workspace', metavar='workspace', dest='workspace', type='string', action='store')
parser.add_option('-G', help='show available global options', dest='gshow', default=False, action='store_true')
parser.add_option('-g', help='set a global option (can be used more than once)', metavar='name=value', dest='goptions', default=[], type='string', action='append')
parser.add_option('-M', help='show modules', dest='show_modules', default=False, action='store_true')
parser.add_option('-m', help='specify the module', metavar='module', dest='module', type='string', action='store')
parser.add_option('-O', help='show available module options', dest='show', default=False, action='store_true')
parser.add_option('-o', help='set a module option (can be used more than once)', metavar='name=value', dest='options', default=[], type='string', action='append')
(opts, args) = parser.parse_args()
recon_cli(opts)
