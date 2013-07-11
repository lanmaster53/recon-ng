#!/usr/bin/env python

__author__    = 'Tim Tomes (@LaNMaSteR53)'
__email__     = 'tjt1980[at]gmail.com'
__version__   = '1.40'

import datetime
import os
import errno
import json
import sys
import imp
import sqlite3
import traceback
import __builtin__
import framework

# define colors for output
# note: color in prompt effects
# rendering of command history
__builtin__.N  = '\033[m' # native
__builtin__.R  = '\033[31m' # red
__builtin__.G  = '\033[32m' # green
__builtin__.O  = '\033[33m' # orange
__builtin__.B  = '\033[34m' # blue

# mode flags
__builtin__.script = 0
__builtin__.record = 0

# set global framework options
__builtin__.goptions = {}
__builtin__.keys = {}
__builtin__.loaded_modules = {}
__builtin__.workspace = ''

class Recon(framework.module):
    def __init__(self):
        self.name = 'recon-ng' #os.path.basename(__file__).split('.')[0]
        prompt = '%s > ' % (self.name)
        framework.module.__init__(self, (prompt, 'core'))
        self.init_goptions()
        self.options = self.goptions
        self.load_modules()
        self.load_keys()
        self.show_banner()
        self.init_workspace()

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def init_goptions(self):
        self.register_option('workspace', 'default', 'yes', 'current workspace name', self.goptions)
        self.register_option('rec_file', './data/cmd.rc', 'yes', 'path to resource file for \'record\'', self.goptions)
        self.register_option('domain', None, 'no', 'target domain', self.goptions)
        self.register_option('company', None, 'no', 'target company name', self.goptions)
        self.register_option('latitude', None, 'no', 'target latitudinal position', self.goptions)
        self.register_option('longitude', None, 'no', 'target longitudinal position', self.goptions)
        self.register_option('user-agent', 'Recon-ng/%s' % (__version__), 'yes', 'user-agent string', self.goptions)
        self.register_option('proxy', False, 'yes', 'proxy all requests', self.goptions)
        self.register_option('proxy_server', '127.0.0.1:8080', 'yes', 'proxy server', self.goptions)
        self.register_option('socket_timeout', 10, 'yes', 'socket timeout in seconds', self.goptions)
        self.register_option('verbose', True,  'yes', 'enable verbose output', self.goptions)
        self.register_option('debug', False,  'yes', 'enable debugging output', self.goptions)

    def load_modules(self, reload=False):
        self.loaded_category = {}
        self.loaded_modules = __builtin__.loaded_modules
        if reload: self.output('Reloading...')
        for dirpath, dirnames, filenames in os.walk('./modules/'):
            if len(filenames) > 0:
                mod_category = dirpath.split('/')[2]
                if not mod_category in self.loaded_category: self.loaded_category[mod_category] = []
                for filename in [f for f in filenames if f.endswith('.py')]:
                    # this (as opposed to sys.path.append) allows for module reloading
                    mod_name = filename.split('.')[0]
                    mod_dispname = '%s%s%s' % (self.module_delimiter.join(dirpath.split('/')[2:]), self.module_delimiter, mod_name)
                    mod_loadname = mod_dispname.replace(self.module_delimiter, '_')
                    mod_loadpath = os.path.join(dirpath, filename)
                    mod_file = open(mod_loadpath, 'rb')
                    try:
                        imp.load_source(mod_loadname, mod_loadpath, mod_file)
                        __import__(mod_loadname)
                        self.loaded_category[mod_category].append(mod_loadname)
                        self.loaded_modules[mod_dispname] = mod_loadname
                    except:
                        print '-'*60
                        traceback.print_exc()
                        print '-'*60
                        self.error('Unable to load module: %s' % (mod_name))

    def load_keys(self):
        key_path = './data/keys.dat'
        if os.path.exists(key_path):
            try:
                key_data = json.loads(open(key_path, 'rb').read())
                for key in key_data: self.keys[key] = key_data[key]
            except:
                self.error('Corrupt key file.')

    def show_banner(self):
        banner = open('./core/banner').read()
        banner_len = len(max(banner.split('\n'), key=len))
        print banner
        print '{0:^{1}}'.format('%s[%s v%s Copyright (C) %s, %s]%s' % (O, self.name, __version__, datetime.datetime.now().year, __author__, N), banner_len+8) # +8 compensates for the color bytes
        print ''
        counts = [(len(self.loaded_category[x]), x) for x in self.loaded_category]
        count_len = len(max([str(x[0]) for x in counts], key=len))
        for count in sorted(counts, reverse=True):
            cnt = '[%d]' % (count[0])
            print '%s%s %s modules%s' % (B, cnt.ljust(count_len+2), count[1].title(), N)
        print ''

    def init_workspace(self, workspace=None):
        workspace = workspace if workspace is not None else self.options['workspace']['value']
        workspace = './workspaces/%s' % (workspace)
        try:
            os.makedirs(workspace)
        except OSError as e:
            if e.errno != errno.EEXIST:
                self.error(e.__str__())
                return False
        conn = sqlite3.connect('%s/data.db' % (workspace))
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS hosts (host TEXT, ip_address TEXT, region TEXT, country TEXT, latitude TEXT, longitude TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS contacts (fname TEXT, lname TEXT, email TEXT, title TEXT, region TEXT, country TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS creds (username TEXT, password TEXT, hash TEXT, type TEXT, leak TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS pushpin (source TEXT, screen_name TEXT, profile_name TEXT, profile_url TEXT, media_url TEXT, thumb_url TEXT, message TEXT, latitude TEXT, longitude TEXT, time TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS dashboard (module TEXT PRIMARY KEY, runs INT)')
        conn.commit()
        conn.close()
        self.workspace = __builtin__.workspace = workspace
        self.init_goptions()
        self.load_config()
        return True

    def load_config(self):
        config_path = '%s/config.dat' % (self.workspace)
        if os.path.exists(config_path):
            try:
                config_data = json.loads(open(config_path, 'rb').read())
                for key in config_data: self.options[key] = config_data[key]
            except:
                self.error('Corrupt config file.')

    def save_config(self):
        config_path = '%s/config.dat' % (self.workspace)
        config_file = open(config_path, 'wb')
        json.dump(self.options, config_file)
        config_file.close()

    #==================================================
    # COMMAND METHODS
    #==================================================

    def do_reload(self, params):
        '''Reloads all modules'''
        self.load_modules(True)

    def do_info(self, params):
        '''Displays module information'''
        options = params.split()
        if len(options) == 0:
            self.help_info()
        else:
            try:
                modulename = self.loaded_modules[params]
                y = sys.modules[modulename].Module((None, params))
                y.do_info(None)
            except (KeyError, AttributeError):
                self.error('Invalid module name.')

    def do_banner(self, params):
        '''Displays the banner'''
        self.show_banner()

    def do_set(self, params):
        '''Sets global options'''
        options = params.split()
        if len(options) < 2: self.help_set()
        else:
            name = options[0].lower()
            if name in self.options:
                value = ' '.join(options[1:])
                init = False
                # validate workspace
                if name == 'workspace':
                    if not self.init_workspace(value):
                        self.error('Unable to create \'%s\' workspace.' % (value))
                        return
                self.options[name]['value'] = self.autoconvert(value)
                print '%s => %s' % (name.upper(), value)
                self.save_config()
            else: self.error('Invalid option.')

    def do_load(self, params, cli=False):
        '''Loads selected module'''
        if params.lower() == 'useless':
            self.output('Thank you, Kevin Fiscus!')
            import webbrowser
            w = webbrowser.get()
            w.open('http://www.theuselessweb.com/')
            return
        try: self.validate_options()
        except framework.FrameworkException as e:
            self.error(e.message)
            return
        options = params.split()
        if len(options) == 0:
            self.help_load()
        else:
            modules = []
            try:
                # finds any modules that contain params
                modules = [params] if params in self.loaded_modules else [x for x in self.loaded_modules if params in x]
                # raise AssertionError if multiple modules are found
                assert len(modules) == 1
                modulename = modules[0]
                loadedname = self.loaded_modules[modulename]
                prompt = '%s [%s] > ' % (self.name, modulename.split(self.module_delimiter)[-1])
                y = sys.modules[loadedname].Module((prompt, modulename))
                if cli: return y
                try: y.cmdloop()
                except KeyboardInterrupt: print ''
            except (KeyError, AttributeError, AssertionError):
                if not modules:
                    self.error('Invalid module name.')
                else:
                    self.output('Multiple modules match \'%s\'.' % params)
                    self.display_modules(modules)

    # alias for load
    def do_use(self, params):
        '''Loads selected module'''
        options = params.split()
        if len(options) == 0:
            self.help_use()
        else:
            self.do_load(params)

    def do_run(self, params):
        '''Not available'''
        self.output('Command \'run\' reserved for future use.')

    #==================================================
    # HELP METHODS
    #==================================================

    def help_search(self):
        print 'Usage: search <string>'

    def help_load(self):
        print 'Usage: load <module>'

    def help_use(self):
        print 'Usage: use <module>'

    def help_info(self):
        print 'Usage: info <module>'

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_set(self, text, line, *ignored):
        args = line.split()
        if len(args) > 1 and args[1].lower() == 'workspace':
            return [name for name in os.listdir('./workspaces') if name.startswith(text) and os.path.isdir('./workspaces/%s' % (name))]
        return [x for x in self.options if x.startswith(text)]

    def complete_load(self, text, *ignored):
        return [x for x in self.loaded_modules if x.startswith(text)]
    complete_info = complete_use = complete_load
