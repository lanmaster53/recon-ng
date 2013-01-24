#!/usr/bin/env python

""" Docstring """

__author__    = "Tim Tomes (@LaNMaSteR53)"
__email__     = "tjt1980[at]gmail.com"
__version__   = "1.00"
__copyright__ = "Copyright (C) 2012, Tim Tomes"
__license__   = "GPLv3"
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

See <http://www.gnu.org/licenses/> for a copy of the GNU General
Public License
"""

import cmd
import datetime
import os
import sys
import imp
import sqlite3
import traceback
import __builtin__
# prep python path for core modules
sys.path.append('./core/')
import framework

# define colors for output
# note: color in prompt effects
# rendering of command history
__builtin__.N  = "\033[m" # native
__builtin__.R  = "\033[31m" # red
__builtin__.G  = "\033[32m" # green
__builtin__.O  = "\033[33m" # orange
__builtin__.B  = "\033[34m" # blue
# mode flags
__builtin__.script = 0
# set global framework options
__builtin__.goptions = {
                        'db_file': './data/data.db',
                        'key_file': './data/keys.db',
                        'log_file': './data/cmd.log',
                        'domain': '',
                        'company': '',
                        'user-agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',#'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)',
                        'proxy': False,
                        'proxy_http': '127.0.0.1:8080',
                        'proxy_https': '127.0.0.1:8080',
                        "socket_timeout": 10,
                        'verbose': True
                        }

class Recon(framework.module):
    def __init__(self):
        self.name = 'recon-ng'#os.path.basename(__file__).split('.')[0]
        prompt = '%s > ' % (self.name)
        framework.module.__init__(self, prompt)
        self.options = self.goptions
        self.load_modules()
        self.show_banner()
        self.init_db()

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def load_modules(self, reload=False):
        # add logic to NOT break when a module fails, but alert which module fails
        self.loaded_summary = []
        self.loaded_modules = []
        for dirpath, dirnames, filenames in os.walk('./modules/'):
            if len(filenames) > 0:
                cnt = 0
                for filename in [f for f in filenames if f.endswith('.py')]:
                    # this (as opposed to sys.path.append) allows for module reloading
                    modulename = '%s_%s' % ('_'.join(dirpath.split('/')[2:]), filename.split('.')[0])
                    modulepath = os.path.join(dirpath, filename)
                    ModuleFile = open(modulepath, 'rb')
                    try:
                        if reload: self.output('Reloading %s...' % (modulename))
                        imp.load_source(modulename, modulepath, ModuleFile)
                        __import__(modulename)
                        cnt += 1
                        self.loaded_modules.append(modulename)
                    except:
                        print '-'*60
                        traceback.print_exc(file=sys.stdout)
                        print '-'*60
                        self.error('Unable to load module: %s' % (modulekey))
                self.loaded_summary.append(('/'.join(dirpath.split('/')[2:]), cnt))

    def display_modules(self, modules):
        key_len = len(max(modules, key=len)) + len(self.spacer)
        last_category = ''
        for module in sorted(modules):
            category = module.split('_')[0]
            if category != last_category:
                # print header
                print ''
                last_category = category
                print '%s%s%s:' % (self.spacer, last_category[0].upper(), last_category[1:])
                print '%s%s' % (self.spacer, self.ruler*key_len)
            # print module
            print '%s%s' % (self.spacer*2, module)
        print ''

    def show_banner(self):
        banner = open('./core/banner').read()
        banner_len = len(max(banner.split('\n'), key=len))
        print banner
        print '{0:^{1}}'.format('%s[%s v%s Copyright (C) %s, %s]%s' % (O, self.name, __version__, datetime.datetime.now().year, __author__, N), banner_len+8) # +8 compensates for the color bytes
        print ''
        for module in self.loaded_summary:
            print '%s[%d] %s modules%s' % (B, module[1], module[0], N)
        print ''

    def init_db(self):
        conn = sqlite3.connect(self.options['db_file'])
        c = conn.cursor()
        c.execute('create table if not exists hosts (host text, address text)')
        c.execute('create table if not exists contacts (fname text, lname text, email text, title text)')
        c.execute('create table if not exists creds (username text, password text, hash text, type text, leak text)')
        conn.commit()
        conn.close()
        conn = sqlite3.connect(self.options['key_file'])
        c = conn.cursor()
        c.execute('create table if not exists keys (name text primary key, value text)')
        conn.commit()
        conn.close()

    #==================================================
    # FRAMEWORK METHODS
    #==================================================

    def do_reload(self, params):
        """Reloads all modules"""
        self.load_modules(True)

    def do_info(self, params):
        """Displays module information"""
        options = params.split()
        if len(options) == 0:
            self.help_info()
        else:
            try:
                modulename = params
                y = sys.modules[modulename].Module('%s [%s] > ' % (self.name, params))
                try: y.do_info(modulename)
                except KeyboardInterrupt: print ''
                except:
                    print '-'*60
                    traceback.print_exc(file=sys.stdout)
                    print '-'*60
            except KeyError: self.error('Invalid module name.')
            except AttributeError: self.error('Invalid module name.')

    def do_banner(self, params):
        """Displays the banner"""
        self.show_banner()

    def do_set(self, params):
        """Sets global options"""
        options = params.split()
        if len(options) < 2: self.help_set()
        else:
            name = options[0]
            if name in self.options.keys():
                value = ' '.join(options[1:])
                # make sure database file is valid
                if name == 'db_file':
                    try:
                        conn = sqlite3.connect(value)
                        conn.close()
                    except:
                        self.error('Invalid database path or name.')
                        return
                self.options[name] = self.autoconvert(value)
                __builtin__.goptions = self.options
                print '%s => %s' % (name, value)
                self.init_db()
            else: self.error('Invalid option.')

    def do_modules(self, params):
        """Lists available modules"""
        if params:
            modules = [x for x in self.loaded_modules if x.startswith(params)]
        else:
            modules = self.loaded_modules
        self.display_modules(modules)

    def do_search(self, params):
        """Searches available modules"""
        if not params:
            self.help_search()
            return
        str = params.split()[0]
        self.output('Searching for \'%s\'' % (str))
        modules = [x for x in self.loaded_modules if str in x]
        self.display_modules(modules)

    def do_load(self, params):
        """Loads selected module"""
        options = params.split()
        if len(options) == 0:
            self.help_load()
        else:
            try:
                modulename = params
                y = sys.modules[modulename].Module('%s [%s] > ' % (self.name, params))
                try: y.cmdloop()
                except KeyboardInterrupt: print ''
                except:
                    print '-'*60
                    traceback.print_exc(file=sys.stdout)
                    print '-'*60
            except KeyError: self.error('Invalid module name.')
            except AttributeError: self.error('Invalid module name.')

    # alias for load
    def do_use(self, params):
        """Loads selected module"""
        options = params.split()
        if len(options) == 0:
            self.help_use()
        else:
            self.do_load(params)

    #==================================================
    # HELP METHODS
    #==================================================

    def help_search(self):
        print 'Usage: search <string>'

    def help_load(self):
        print 'Usage: load <module>'
        self.do_modules(None)

    def help_use(self):
        print 'Usage: use <module>'
        self.do_modules(None)

    def help_info(self):
        print 'Usage: info <module>'
        self.do_modules(None)

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_load(self, text, *ignored):
        return [x for x in self.loaded_modules if x.startswith(text)]
    complete_modules = complete_info = complete_use = complete_load

if __name__ == '__main__':
    # help and non-interactive options
    import optparse
    usage = "%%prog [options]\n\n%%prog - %s %s" % (__author__, __email__)
    parser = optparse.OptionParser(usage=usage, version=__version__)
    parser.add_option('-r', help='resource file for scripted session', metavar='filename', dest='script_file', type='string', action='store')
    (opts, args) = parser.parse_args()
    # set up command completion
    try:
        import readline
    except ImportError:
        print "%s[!] Module \'readline\' not available. Tab complete disabled.%s" % (R, N)
    else:
        import rlcompleter
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
    # check for and run script session
    if opts.script_file:
        try:
            sys.stdin = open(opts.script_file)
            __builtin__.script = 1
        except:
            print '%s[!] %s%s' % (R, 'Script file not found.', N)
            sys.exit()
    x = Recon()
    try: x.cmdloop()
    except KeyboardInterrupt: print ''