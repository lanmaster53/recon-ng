#!/usr/bin/env python

""" Docstring """

__author__    = "Tim Tomes (@LaNMaSteR53)"
__email__     = "tjt1980[at]gmail.com"
__version__   = "0.09"
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

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import cmd
import datetime
import os
import sys
import imp
import sqlite3
import traceback
import __builtin__
sys.path.append('./base/')
import _cmd
# prep python path for supporting modules
sys.path.append('./libs/')

# define colors for output
# note: color in prompt effects
# rendering of command history
# native
__builtin__.N  = "\033[m"
# orange
__builtin__.O  = "\033[33m"
# blue
__builtin__.B  = "\033[34m"
# red
__builtin__.R  = "\033[31m"
# set global framework options
__builtin__.goptions = {
                        'dbfilename': './data/data.db',
                        'keyfilename': './data/api.keys',
                        'domain': 'sans.org',
                        'company': 'SANS',
                        'user-agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)',
                        'proxy': False,
                        'proxyhost': '127.0.0.1:8080'
                        }

class Shell(_cmd.base_cmd):
    def __init__(self):
        self.name = 'recon-ng'#os.path.basename(__file__).split('.')[0]
        prompt = '%s > ' % (self.name)
        _cmd.base_cmd.__init__(self, prompt)
        self.do_info.__func__.__doc__ = """Displays framework info"""
        self.options = self.goptions
        self.loadmodules()
        self.show_banner()
        self.init_db()

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def loadmodules(self):
        # add logic to NOT break when a module fails, but alert which module fails
        self.loaded = []
        for dirpath, dirnames, filenames in os.walk('./modules/'):
            if len(filenames) > 0:
                cnt = 0
                for filename in [f for f in filenames if f.endswith('.py')]:
                    # this (as opposed to sys.path.append) allows for module reloading
                    modulename = filename.split('.')[0]
                    modulepath = os.path.join(dirpath, filename)
                    ModuleFile = open(modulepath, 'rb')
                    try:
                        imp.load_source(modulename, modulepath, ModuleFile)
                        __import__(modulename)
                        cnt += 1
                    except:
                        print '-'*60
                        traceback.print_exc(file=sys.stdout)
                        print '-'*60
                        self.error('Unable to load module: %s' % (modulename))
                self.loaded.append((dirpath.split('/')[-1], cnt))

    def show_banner(self):
        print ''
        print '    _/_/_/    _/_/_/_/    _/_/_/    _/_/    _/      _/              _/      _/    _/_/_/'
        print '   _/    _/  _/        _/        _/    _/  _/_/    _/              _/_/    _/  _/       '
        print '  _/_/_/    _/_/_/    _/        _/    _/  _/  _/  _/  _/_/_/_/_/  _/  _/  _/  _/  _/_/  '
        print ' _/    _/  _/        _/        _/    _/  _/    _/_/              _/    _/_/  _/    _/   '
        print '_/    _/  _/_/_/_/    _/_/_/    _/_/    _/      _/              _/      _/    _/_/_/    '
        print ''
        print '{0:^{1}}'.format('%s[%s v%s Copyright (C) %s, %s]%s' % (O, self.name, __version__, datetime.datetime.now().year, __author__, N), 96)
        print ''
        for module in self.loaded:
            print '%s[%d] %s modules%s' % (B, module[1], module[0], N)
        print ''

    def init_db(self):
        conn = sqlite3.connect(self.options['dbfilename'])
        c = conn.cursor()
        c.execute('create table if not exists hosts (host text, address text)')
        c.execute('create table if not exists contacts (fname text, lname text, email text, status text, title text)')
        conn.commit()
        conn.close()

    #==================================================
    # FRAMEWORK METHODS
    #==================================================

    def do_reload(self, params):
        """Reloads all modules"""
        self.loadmodules()

    def do_info(self, params):
        """Displays framework information"""
        print 'Framework information.'

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
                value = options[1]
                # make sure database file is valid
                if name == 'dbfilename':
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

    def do_list(self, params):
        """Lists framework items"""
        options = params.split()
        if len(options) == 0: self.help_list()
        else:
            option = options[0]
            if option == 'modules':
                print ''
                print 'Modules:'
                print '===================='
                for dirpath, dirnames, filenames in os.walk('./modules/'):
                    if len(filenames) > 0:
                        dir = dirpath.split('/')[-1]
                        print '%s/' % (dir)
                        #print '{:=^25}'.format(' %s ' % (dir))
                        for filename in [f for f in filenames if f.endswith('.py')]:
                            module = filename.split('.')[0]
                            print '    -%s' % (module)
                            #print os.path.join(dir, filename.split('.')[0])
                        print '===================='
                print ''
            elif option == 'hosts' or option == 'contacts':
                columns = '*'
                if len(options) > 1:
                    columns = options[1]
                self.do_query('SELECT %s from %s ORDER BY 1' % (columns, option))
            else: self.error('Invalid option: %s' % (params))

    def do_load(self, params):
        """Loads selected module"""
        options = params.split()
        if len(options) == 0:
            self.help_load()
        else:
            try:
                y = sys.modules[params].Module('%s [%s] > ' % (self.name, params))
                try: y.cmdloop()
                except KeyboardInterrupt: sys.stdout.write('\n')
                except:# Exception as e:
                    print '-'*60
                    traceback.print_exc(file=sys.stdout)
                    print '-'*60
                    #self.error('%s: \'%s\'' % (type(e).__name__, e.message))
            except KeyError: self.error('Invalid module name.')
            except AttributeError: self.error('Invalid module name.')

    #==================================================
    # HELP METHODS
    #==================================================

    def help_list(self):
        print 'Usage: list <option> <column1,column2,...>'
        print''
        print 'Options:'
        print '========'
        print 'modules    Lists available modules.'
        print 'hosts*     Lists harvested hosts from the database.    columns=[host,address]'
        print 'contacts*  Lists harvested contacts from the database. columns=[fname,lname,email,title]'
        print ''
        print '* sorted by first column'
        print ''

    def help_load(self):
        print 'Usage: load <module>'
        self.do_list('modules')

if __name__ == '__main__':
    try:
        import readline
    except ImportError:
        print "[!] Module \'readline\' not available. Tab complete disabled."
    else:
        import rlcompleter
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
    x = Shell()
    try: x.cmdloop()
    except KeyboardInterrupt: sys.stdout.write('\n')