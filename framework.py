#!/usr/bin/env python

""" Docstring """

__author__  = "Tim Tomes (@LaNMaSteR53)"
__email__   = "tjt1980[at]gmail.com"
__credits__ = ""
__license__ = "GPL v2"
__version__ = "0.03"

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
# white
__builtin__.W  = "\033[0m"
# black
__builtin__.BK = "\033[30m"
# red
__builtin__.R  = "\033[31m"
# green
__builtin__.G  = "\033[32m"
# orange
__builtin__.O  = "\033[33m"
# blue
__builtin__.B  = "\033[34m"
# purple
__builtin__.P  = "\033[35m"
# cyan
__builtin__.C  = "\033[36m"
# gray
__builtin__.GR = "\033[37m"

#parser.parse_args(params.split())

class Shell(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.name = 'recon-ng'#os.path.basename(__file__).split('.')[0]
        self.prompt = '%s > ' % (self.name)
        self.nohelp = '[!] No help on %s'
        self.loaded = []
        self.loadmodules()
        self.show_banner()
        self.dbfilename = __builtin__.dbfilename
        self.init_db()

    def loadmodules(self):
        # add logic to NOT break when a module fails, but alert which module fails
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
                        self.default('Unable to load module: %s' % (modulename))
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
            print '%s[%d %s modules]%s' % (B, module[1], module[0], N)
        print ''

    def init_db(self):
        conn = sqlite3.connect(self.dbfilename)
        c = conn.cursor()
        c.execute('create table if not exists hosts (host text, address text)')
        c.execute('create table if not exists contacts (fname text, lname text, email text, title text)')
        conn.commit()
        conn.close()

    def default(self, line):
        print '[!] Unknown syntax: %s' % (line)

    def do_reload(self, params):
        self.loadmodules()

    def help_reload(self):
        print 'Reloads all modules.'

    def do_exit(self, params):
        return True

    def do_info(self, params):
        print 'Framework information.'

    def do_banner(self, params):
        self.show_banner()

    def help_banner(self):
        print 'Displays the banner.'

    def output(self, table, columns):
        conn = sqlite3.connect(self.dbfilename)
        c = conn.cursor()
        try: rows = c.execute('SELECT %s from %s' % (columns, table))
        except sqlite3.OperationalError:
            self.default('Invalid column name.')
            rows = []
        for row in rows:
            for item in row:
                sys.stdout.write('%s ' % item)
            sys.stdout.write('\n')
        conn.close()

    def do_list(self, params):
        options = params.split()
        if len(options) == 0: self.help_list()
        else:
            option = options[0]
            if option == 'modules':
                for dirpath, dirnames, filenames in os.walk('./modules/'):
                    if len(filenames) > 0:
                        dir = dirpath.split('/')[-1]
                        print ''
                        print '%s modules:' % (dir)
                        print '=================='
                        for filename in [f for f in filenames if f.endswith('.py')]:
                            print filename.split('.')[0]
                print ''
            elif option.startswith('hosts') or option.startswith('contacts'):
                columns = '*'
                if len(options) > 1:
                    columns = options[1]
                self.output(option, columns)
            else: self.default('Invalid option: %s' % (params))

    def help_list(self):
        print 'Usage: list <option> <column1,column2,...>'
        print''
        print 'Options:'
        print '========'
        print 'modules   Lists available modules.'
        print 'hosts     Lists harvested hosts from the database.    columns=[host,address]'
        print 'contacts  Lists harvested contacts from the database. columns=[fname,lname,email,title]'
        print''

    def do_load(self, params):
        options = params.split()
        if len(options) == 0: self.help_load()
        else:
            try:
                y = sys.modules[params].Module('%s [%s] > ' % (self.name, params))
                try: y.cmdloop()
                except KeyboardInterrupt: sys.stdout.write('\n')
                except:# Exception as e:
                    print '-'*60
                    traceback.print_exc(file=sys.stdout)
                    print '-'*60
                    #import pdb;pdb.set_trace()
                    #self.default('%s: \'%s\'' % (type(e).__name__, e.message))
            except KeyError: self.default('Invalid module name.')

    def help_load(self):
        print 'Usage: load <module>'

if __name__ == '__main__':
    __builtin__.dbfilename = './data.db'
    readline.parse_and_bind("bind ^I rl_complete")
    x = Shell()
    try: x.cmdloop()
    except KeyboardInterrupt: sys.stdout.write('\n')