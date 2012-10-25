import cmd
import rlcompleter
import readline
import os
import sys
import imp
import traceback

#parser.parse_args(params.split())

class Shell(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.name = 'recon-ng'#os.path.basename(__file__).split('.')[0]
        self.prompt = '%s > ' % (self.name)
        self.nohelp = '[!] No help on %s'
        self.loadmodules()

    def loadmodules(self):
        # add logic to NOT break when a module fails, but alert which module fails
        imp.load_source('_cmd', './base/_cmd.py', open('./base/_cmd.py', 'rb'))
        for dirpath, dirnames, filenames in os.walk('./modules/'):
            for filename in [f for f in filenames if f.endswith('.py')]:
                modulename = filename.split('.')[0]
                modulepath = os.path.join(dirpath, filename)
                ModuleFile = open(modulepath, 'rb')
                imp.load_source(modulename, modulepath, ModuleFile)
                __import__(modulename)

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

    def do_modules(self, params):
        for dirpath, dirnames, filenames in os.walk('./modules/'):
            if len(filenames) > 0:
                dir = dirpath.split('/')[-1]
                print ''
                print '%s modules:' % (dir)
                print '=================='
                for filename in [f for f in filenames if f.endswith('.py')]:
                    print filename.split('.')[0]
        print ''

    def help_modules(self):
        print 'List available modules.'

    def do_load(self, params):
        try:
            y = sys.modules[params].Module('%s [%s] > ' % (self.name, params))
            y.cmdloop()
        except KeyboardInterrupt: sys.stdout.write('\n')
        except Exception as e:
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60
            #import pdb;pdb.set_trace()
            #self.default('%s: \'%s\'' % (type(e).__name__, e.message))

    def help_load(self):
        print 'Usage: load <module>'

if __name__ == '__main__':
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