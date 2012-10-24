#!/usr/bin/python -tt

import cmd
import rlcompleter
import readline
import os
import imp
import __builtin__
import sys

class Shell(cmd.Cmd):
    def __init__(self):
        self.name = 'recon-ng'#os.path.basename(__file__).split('.')[0]
        self.prompt = '%s > ' % (self.name)
        self.intro = banner
        self.nohelp = '[!] No help on %s'
        cmd.Cmd.__init__(self)
        self.loadmodules()

    def loadmodules(self):
        for dirpath, dirnames, filenames in os.walk('./modules/'):
            for filename in [f for f in filenames if f.endswith('.py')]:
                modulename = filename.split('.')[0]
                modulepath = os.path.join(dirpath, filename)
                ModuleFile = open(modulepath, 'rb')
                mod =  imp.load_source(modulename, modulepath, ModuleFile)
                __builtin__.__dict__.update(mod.__dict__)

    def default(self, line):
        print '[!] Unknown syntax: %s' % (line)

    def do_exit(self, params):
        return True

    def do_info(self, params):
        print 'This is the framework help.'

    def do_banner(self, params):
        print banner
    def help_banner(self):
        print 'Displays the banner.'

    def do_list(self, params):
        if params != 'modules': self.default('Invalid type')
        else:
            for dirpath, dirnames, filenames in os.walk('./modules/'):
                if len(filenames) > 0:
                    dir = dirpath.split('/')[-1]
                    print ''
                    print '%s modules:' % (dir)
                    print '=================='
                    for filename in [f for f in filenames if f.endswith('.py')]:
                        print filename.split('.')[0]
            print ''
    def help_list(self):
        print 'Usage: list modules'

    def do_load(self, params):
        try:
            y = sys.modules[params].Module('%s [%s] > ' % (self.name, params))
            y.cmdloop()
        except KeyError:
            self.default('Invalid module name.')
        except AttributeError:
            self.default('Invalid module class broken.')
    def help_load(self):
        print 'Usage: load [module]'

if __name__ == '__main__':
    banner = """
    _/_/_/    _/_/_/_/    _/_/_/    _/_/    _/      _/              _/      _/    _/_/_/   
   _/    _/  _/        _/        _/    _/  _/_/    _/              _/_/    _/  _/          
  _/_/_/    _/_/_/    _/        _/    _/  _/  _/  _/  _/_/_/_/_/  _/  _/  _/  _/  _/_/     
 _/    _/  _/        _/        _/    _/  _/    _/_/              _/    _/_/  _/    _/      
_/    _/  _/_/_/_/    _/_/_/    _/_/    _/      _/              _/      _/    _/_/_/       
"""
    readline.parse_and_bind("bind ^I rl_complete")
    x = Shell()
    x.cmdloop(x.intro)