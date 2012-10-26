#!/usr/bin/env python

""" Docstring """

__author__  = "Tim Tomes (@LaNMaSteR53)"
__email__   = "tjt1980[at]gmail.com"
__credits__ = ""
__license__ = "GPL v2"
__version__ = "0.06"

import cmd
import rlcompleter
import readline
import os
import sys
import imp
import sqlite3
import traceback
import __builtin__

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
                        'user-agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)'
                        }

#parser.parse_args(params.split())

class Shell(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.name = 'recon-ng'#os.path.basename(__file__).split('.')[0]
        self.prompt = '%s > ' % (self.name)
        self.nohelp = '%s[!] No help on %%s%s' % (R, N)
        self.options = __builtin__.goptions
        self.loadmodules()
        self.show_banner()
        self.init_db()

    def loadmodules(self):
        # add logic to NOT break when a module fails, but alert which module fails
        self.loaded = []
        imp.load_source('_cmd', './base/_cmd.py', open('./base/_cmd.py', 'rb'))
        for dirpath, dirnames, filenames in os.walk('./modules/'):
            if len(filenames) > 0:
                cnt = 0
                for filename in [f for f in filenames if f.endswith('.py')]:
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
        print '    _/_/_/    _/_/_/_/    _/_/_/    _/_/    _/      _/              _/      _/    _/_/_/   '
        print '   _/    _/  _/        _/        _/    _/  _/_/    _/              _/_/    _/  _/          '
        print '  _/_/_/    _/_/_/    _/        _/    _/  _/  _/  _/  _/_/_/_/_/  _/  _/  _/  _/  _/_/     '
        print ' _/    _/  _/        _/        _/    _/  _/    _/_/              _/    _/_/  _/    _/      '
        print '_/    _/  _/_/_/_/    _/_/_/    _/_/    _/      _/              _/      _/    _/_/_/       '
        print ''
        print '%s[%s v%s]%s' % (O, self.name, __version__, N)
        for module in self.loaded:
            print '%s[%d] %s modules%s' % (B, module[1], module[0], N)
        print ''

    def init_db(self):
        conn = sqlite3.connect(self.options['dbfilename'])
        c = conn.cursor()
        c.execute('create table if not exists hosts (host text, address text)')
        c.execute('create table if not exists contacts (fname text, lname text, email text, title text)')
        conn.commit()
        conn.close()

    def default(self, line):
        print '%s[!] Unknown syntax: %s%s' % (R, line, N)

    def error(self, line):
        print '%s[!] %s%s' % (R, line, N)

    def do_reload(self, params):
        """Reloads all modules."""
        self.loadmodules()

    def do_exit(self, params):
        """Exits the framework."""
        return True

    def do_info(self, params):
        print 'Framework information.'

    def do_banner(self, params):
        """Displays the banner."""
        self.show_banner()

    def boolify(self, s):
        return {'true': True, 'false': False}[s.lower()]
    
    def autoconvert(self, s):
        for fn in (self.boolify, int, float):
            try: return fn(s)
            except ValueError: pass
            except KeyError: pass
        return s

    def do_goptions(self, params):
        """Lists global options."""
        print ''
        print 'Global Options:'
        print '==============='
        for key in self.options.keys():
            value = self.options[key]
            print '%s %s %s' % (key.ljust(12), type(value).__name__.ljust(5), str(value))
        print ''

    def do_setg(self, params):
        options = params.split()
        if len(options) < 2:
            self.help_setg()
            self.do_goptions(None)
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

    def help_setg(self):
        print 'Usage: set <option> <value>'

    def output(self, table, columns):
        conn = sqlite3.connect(self.options['dbfilename'])
        c = conn.cursor()
        try: rows = c.execute('SELECT %s from %s ORDER BY %s' % (columns, table, '1'))
        except sqlite3.OperationalError:
            self.error('Invalid column name.')
            rows = []
        for row in rows:
            row = filter(None, row)
            print ' '.join(row)
        conn.close()

    def do_list(self, params):
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
                        #print '{:=^25}'.format(' %s ' % (dir))
                        for filename in [f for f in filenames if f.endswith('.py')]:
                            print os.path.join(dir, filename.split('.')[0])
                        print '===================='
                print ''
            elif option.startswith('hosts') or option.startswith('contacts'):
                columns = '*'
                if len(options) > 1:
                    columns = options[1]
                self.output(option, columns)
            else: self.error('Invalid option: %s' % (params))

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

    def do_load(self, params):
        options = params.split()
        if len(options) == 0:
            self.help_load()
            self.do_list('modules')
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

    def help_load(self):
        print 'Usage: load <module>'

if __name__ == '__main__':
    readline.parse_and_bind("bind ^I rl_complete")
    x = Shell()
    try: x.cmdloop()
    except KeyboardInterrupt: sys.stdout.write('\n')