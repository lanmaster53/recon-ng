import cmd
import rlcompleter
import readline
import os
import sys
import imp
import sqlite3
import traceback
import __builtin__

#parser.parse_args(params.split())
# Figure out a way to declare the db filename once, dynamically. Options in main loop?

class Shell(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.name = 'recon-ng'#os.path.basename(__file__).split('.')[0]
        self.prompt = '%s > ' % (self.name)
        self.nohelp = '[!] No help on %s'
        self.loadmodules()
        self.dbfilename = __builtin__.dbfilename
        self.init_db()

    def loadmodules(self):
        # add logic to NOT break when a module fails, but alert which module fails
        imp.load_source('_cmd', './base/_cmd.py', open('./base/_cmd.py', 'rb'))
        for dirpath, dirnames, filenames in os.walk('./modules/'):
            for filename in [f for f in filenames if f.endswith('.py')]:
                modulename = filename.split('.')[0]
                modulepath = os.path.join(dirpath, filename)
                ModuleFile = open(modulepath, 'rb')
                try:
                    imp.load_source(modulename, modulepath, ModuleFile)
                    __import__(modulename)
                except:
                    print '-'*60
                    traceback.print_exc(file=sys.stdout)
                    print '-'*60
                    self.default('Unable to load module: %s' % (modulename))

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
        print banner

    def help_banner(self):
        print 'Displays the banner.'

    def output(self, table):
        conn = sqlite3.connect(self.dbfilename)
        c = conn.cursor()
        for row in c.execute('SELECT * from %s' % (table)):
            for item in row:
                sys.stdout.write('%s ' % item)
            sys.stdout.write('\n')
        conn.close()

    def do_list(self, params):
        if params == 'modules':
            for dirpath, dirnames, filenames in os.walk('./modules/'):
                if len(filenames) > 0:
                    dir = dirpath.split('/')[-1]
                    print ''
                    print '%s modules:' % (dir)
                    print '=================='
                    for filename in [f for f in filenames if f.endswith('.py')]:
                        print filename.split('.')[0]
            print ''
        elif params == 'hosts' or params == 'contacts':
            self.output(params)
        else: self.default('Invalid option: %s' % (params))

    def help_list(self):
        print 'Usage: list <option>'
        print''
        print 'Options:'
        print '========'
        print 'modules   Lists available modules.'
        print 'hosts     Lists harvested hosts from the database.'
        print 'contacts  Lists harvested contacts from the database.'
        print''

    def do_load(self, params):
        try:
            y = sys.modules[params].Module('%s [%s] > ' % (self.name, params))
            y.cmdloop()
        except KeyboardInterrupt: sys.stdout.write('\n')
        except:# Exception as e:
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60
            #import pdb;pdb.set_trace()
            #self.default('%s: \'%s\'' % (type(e).__name__, e.message))

    def help_load(self):
        print 'Usage: load <module>'

if __name__ == '__main__':
    __builtin__.dbfilename = './data.db'
    banner = """
    _/_/_/    _/_/_/_/    _/_/_/    _/_/    _/      _/              _/      _/    _/_/_/   
   _/    _/  _/        _/        _/    _/  _/_/    _/              _/_/    _/  _/          
  _/_/_/    _/_/_/    _/        _/    _/  _/  _/  _/  _/_/_/_/_/  _/  _/  _/  _/  _/_/     
 _/    _/  _/        _/        _/    _/  _/    _/_/              _/    _/_/  _/    _/      
_/    _/  _/_/_/_/    _/_/_/    _/_/    _/      _/              _/      _/    _/_/_/       
"""
    readline.parse_and_bind("bind ^I rl_complete")
    print banner
    x = Shell()
    try: x.cmdloop()
    except KeyboardInterrupt: sys.stdout.write('\n')