#!/usr/bin/env python

__author__    = 'Tim Tomes (@LaNMaSteR53)'
__email__     = 'tjt1980[at]gmail.com'
__version__   = '1.00'

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
__builtin__.record = 0

# set global framework options
__builtin__.goptions = {}

# set the module path delimiter
# delimiter only effects systems with GNU readline
# defaults to ':' for systems with libedit readline
__builtin__.module_delimiter = ':'

class Recon(framework.module):
    def __init__(self):
        self.name = 'recon-ng'#os.path.basename(__file__).split('.')[0]
        self.module_delimiter = __builtin__.module_delimiter
        prompt = '%s > ' % (self.name)
        framework.module.__init__(self, prompt)
        self.register_option('db_file', './data/data.db', 'yes', 'path to main database file', self.goptions)
        self.register_option('key_file', './data/keys.db', 'yes', 'path to API key database file', self.goptions)
        self.register_option('rec_file', './data/cmd.rc', 'yes', 'path to resource file for \'record\'', self.goptions)
        self.register_option('domain', '', 'no', 'target domain', self.goptions)
        self.register_option('company', '', 'no', 'target company name', self.goptions)
        self.register_option('user-agent', 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)', 'yes', 'user-agent string', self.goptions)
        self.register_option('proxy', False, 'yes', 'proxy all requests', self.goptions)
        self.register_option('proxy_server', '127.0.0.1:8080', 'yes', 'proxy server', self.goptions)
        self.register_option('socket_timeout', 10, 'yes', 'socket timeout in seconds', self.goptions)
        self.register_option('verbose', True,  'yes', 'verbose output', self.goptions)
        self.options = self.goptions
        self.load_modules()
        self.show_banner()
        self.init_db()

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def load_modules(self, reload=False):
        # add logic to NOT break when a module fails, but alert which module fails
        self.loaded_category = {}
        self.loaded_class = {}
        self.loaded_modules = []
        if reload: self.output('Reloading...')
        for dirpath, dirnames, filenames in os.walk('./modules/'):
            if len(filenames) > 0:
                mod_category = dirpath.split('/')[2]
                if not mod_category in self.loaded_category: self.loaded_category[mod_category] = []
                for filename in [f for f in filenames if f.endswith('.py')]:
                    # this (as opposed to sys.path.append) allows for module reloading
                    mod_name = filename.split('.')[0]
                    mod_loadname = '%s%s%s' % (self.module_delimiter.join(dirpath.split('/')[2:]), self.module_delimiter, mod_name)
                    mod_loadpath = os.path.join(dirpath, filename)
                    mod_file = open(mod_loadpath, 'rb')
                    try:
                        imp.load_source(mod_loadname, mod_loadpath, mod_file)
                        __import__(mod_loadname)
                        mod_class = sys.modules[mod_loadname].Module(None).classify
                        if not mod_class in self.loaded_class: self.loaded_class[mod_class] = []
                        self.loaded_class[mod_class].append(mod_loadname)
                        self.loaded_category[mod_category].append(mod_loadname)
                        self.loaded_modules.append(mod_loadname)
                    except:
                        print '-'*60
                        traceback.print_exc(file=sys.stdout)
                        print '-'*60
                        self.error('Unable to load module: %s' % (mod_name))

    def display_modules(self, modules):
        key_len = len(max(modules, key=len)) + len(self.spacer)
        last_category = ''
        for module in sorted(modules):
            category = module.split(self.module_delimiter)[0]
            if category != last_category:
                # print header
                print ''
                last_category = category
                print '%s%s:' % (self.spacer, last_category.title())
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
        for category in sorted(self.loaded_category.keys()):
            print '%s[%d] %s modules%s' % (B, len(self.loaded_category[category]), category, N)
        print ''

    def init_db(self):
        conn = sqlite3.connect(self.options['db_file']['value'])
        c = conn.cursor()
        c.execute('create table if not exists hosts (host text, address text)')
        c.execute('create table if not exists contacts (fname text, lname text, email text, title text)')
        c.execute('create table if not exists creds (username text, password text, hash text, type text, leak text)')
        conn.commit()
        conn.close()
        conn = sqlite3.connect(self.options['key_file']['value'])
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
                y = sys.modules[modulename].Module(None)
                try: y.do_info(modulename)
                except KeyboardInterrupt: print ''
                except:
                    print '-'*60
                    traceback.print_exc(file=sys.stdout)
                    print '-'*60
            except (KeyError, AttributeError):
                self.error('Invalid module name.')

    def do_banner(self, params):
        """Displays the banner"""
        self.show_banner()

    def do_set(self, params):
        """Sets global options"""
        options = params.split()
        if len(options) < 2: self.help_set()
        else:
            name = options[0].lower()
            if name in self.options:
                value = ' '.join(options[1:])
                # make sure database file is valid
                if name in ['db_file', 'key_file', 'rec_file']:
                    try:
                        conn = sqlite3.connect(value)
                        conn.close()
                        f = open(value)
                        f.close()
                    except:
                        self.error('Invalid path or name for \'%s\'.' % (name))
                        return
                    self.init_db()
                print '%s => %s' % (name.upper(), value)
                self.options[name]['value'] = self.autoconvert(value)
            else: self.error('Invalid option.')

    def do_modules(self, params):
        """Lists available modules"""
        if params:
            modules = [x for x in self.loaded_modules if x.startswith(params)]
            if not modules:
                self.error('Invalid module category.')
                return
        else:
            modules = self.loaded_modules
        self.display_modules(modules)

    def do_search(self, params):
        """Searches available modules"""
        if not params:
            self.help_search()
            return
        text = params.split()[0]
        self.output('Searching for \'%s\'' % (text))
        modules = [x for x in self.loaded_modules if text in x]
        if not modules:
            self.error('No modules found containing \'%s\'.' % (text))
        else:
            self.display_modules(modules)

    def do_load(self, params):
        """Loads selected module"""
        if not self.validate_options(): return
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
            __builtin__.module_delimiter = ':'
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
        readline.set_completer_delims(readline.get_completer_delims().replace(__builtin__.module_delimiter, ''))
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
