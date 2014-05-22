from __future__ import print_function

__author__    = 'Tim Tomes (@LaNMaSteR53)'
__email__     = 'tjt1980[at]gmail.com'

import errno
import imp
import json
import os
import random
import re
import shutil
import sys
import traceback
import __builtin__
# framework libs
import framework

# set the __version__ variable based on the VERSION file
execfile(sys.path[0]+'/VERSION')

# spooling system
def spool_print(*args, **kwargs):
    if framework.Framework.spool:
        framework.Framework.spool.write('%s\n' % (args[0]))
        framework.Framework.spool.flush()
    if 'console' in kwargs and kwargs['console'] is False:
        return
    # new print function must still use the old print function via the backup
    __builtin__._print(*args, **kwargs)
# make a builtin backup of the original print function
__builtin__._print = print
# override the builtin print function with the new print function
__builtin__.print = spool_print

#=================================================
# BASE CLASS
#=================================================

class Recon(framework.Framework):

    def __init__(self, mode):
        self.mode = mode
        self.name = 'recon-ng'
        self.prompt_template = '%s[%s] > '
        self.base_prompt = self.prompt_template % ('', self.name)
        framework.Framework.__init__(self, (self.base_prompt, 'base'))
        # establish dynamic paths for framework elements
        self.app_path = framework.Framework.app_path = sys.path[0]+'/'
        self.data_path = framework.Framework.data_path = self.app_path+'data/'
        self.core_path = framework.Framework.core_path = self.app_path+'core/'
        self.options = self.global_options
        self.init_home()
        self.init_global_options()
        self.load_modules()
        if self.mode == Mode.CONSOLE: self.show_banner()
        self.init_workspace('default')

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def version_check(self):
        try:
            pattern = "'(\d+\.\d+\.\d+[^']*)'"
            remote = re.search(pattern, self.request('https://bitbucket.org/LaNMaSteR53/recon-ng/raw/master/VERSION').raw).group(1)
            local = re.search(pattern, open('VERSION').read()).group(1)
            if remote != local:
                self.alert('Your version of Recon-ng does not match the latest release.')
                self.alert('Please update or use the \'--no-check\' switch to continue using the old version.')
                if remote.split('.')[0] != local.split('.')[0]:
                    self.alert('Read the migration notes for pre-requisites before upgrading.')
                    self.output('Migration Notes: https://bitbucket.org/LaNMaSteR53/recon-ng/wiki/Usage%20Guide#!migration-notes')
                self.output('Remote version:  %s' % (remote))
                self.output('Local version:   %s' % (local))
            return local == remote
        except:
            return True

    def init_home(self):
        self.home = framework.Framework.home = '%s/.recon-ng' % os.path.expanduser('~')
        if not os.path.exists(self.home):
            os.makedirs(self.home)

    def init_global_options(self):
        self.register_option('debug', False,  'yes', 'enable debugging output')
        self.register_option('proxy', None, 'no', 'proxy server (address:port)')
        self.register_option('store_tables', True, 'yes', 'store module generated tables')
        self.register_option('timeout', 10, 'yes', 'socket timeout (seconds)')
        self.register_option('user-agent', 'Recon-ng/v%s' % (__version__.split('.')[0]), 'yes', 'user-agent string')
        self.register_option('verbose', True,  'yes', 'enable verbose output')

    def load_modules(self, reload=False):
        self.loaded_category = {}
        self.loaded_modules = framework.Framework.loaded_modules
        if reload: self.output('Reloading...')
        for path in ['%s/modules/' % x for x in (self.app_path, self.home)]:
            for dirpath, dirnames, filenames in os.walk(path):
                # remove hidden files and directories
                filenames = [f for f in filenames if not f[0] == '.']
                dirnames[:] = [d for d in dirnames if not d[0] == '.']
                if len(filenames) > 0:
                    mod_category = re.search('/modules/([^/]*)', dirpath).group(1)
                    if not mod_category in self.loaded_category: self.loaded_category[mod_category] = []
                    for filename in [f for f in filenames if f.endswith('.py')]:
                        # this (as opposed to sys.path.append) allows for module reloading
                        mod_name = filename.split('.')[0]
                        mod_dispname = '/'.join(re.split('/modules/', dirpath)[-1].split('/') + [mod_name])
                        mod_loadname = mod_dispname.replace('/', '_')
                        mod_loadpath = os.path.join(dirpath, filename)
                        mod_file = open(mod_loadpath, 'rb')
                        try:
                            imp.load_source(mod_loadname, mod_loadpath, mod_file)
                            __import__(mod_loadname)
                            self.loaded_category[mod_category].append(mod_loadname)
                            self.loaded_modules[mod_dispname] = mod_loadname
                        except:
                            print('-'*60)
                            traceback.print_exc()
                            print('-'*60)
                            self.error('Unable to load module: %s' % (mod_name))

    def menu_egg(self, params):
        eggs = [
                'Really? A menu option? Try again.',
                'You clearly need \'help\'.',
                'That makes no sense to me.',
                '*grunt* *grunt* Nope. I got nothin\'.',
                'Wait for it...',
                'This is not the Social Engineering Toolkit.',
                'Don\'t you think if that worked the numbers would at least be in order?',
                'Reserving that option for the next-NEXT generation of the framework.',
                'You\'ve clearly got the wrong framework. Attempting to start SET...',
                'Your mother called. She wants her menu driven UI back.',
                'What\'s the samurai password?'
                ]
        print(random.choice(eggs))
        return 

    def create_db(self):
        self.query('CREATE TABLE IF NOT EXISTS domains (domain TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS companies (company TEXT, description TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS netblocks (netblock TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS locations (latitude TEXT, longitude TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS vulnerabilities (host TEXT, reference TEXT, example TEXT, publish_date TEXT, category TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS ports (ip_address TEXT, host TEXT, port TEXT, protocol TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS hosts (host TEXT, ip_address TEXT, region TEXT, country TEXT, latitude TEXT, longitude TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS contacts (first_name TEXT, middle_name TEXT, last_name TEXT, email TEXT, title TEXT, region TEXT, country TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS creds (username TEXT, password TEXT, hash TEXT, type TEXT, leak TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS leaks (leak_id TEXT, description TEXT, source_refs TEXT, leak_type TEXT, title TEXT, import_date TEXT, leak_date TEXT, attackers TEXT, num_entries TEXT, score TEXT, num_domains_affected TEXT, attack_method TEXT, target_industries TEXT, password_hash TEXT, targets TEXT, media_refs TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS pushpins (source TEXT, screen_name TEXT, profile_name TEXT, profile_url TEXT, media_url TEXT, thumb_url TEXT, message TEXT, latitude TEXT, longitude TEXT, time TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS dashboard (module TEXT PRIMARY KEY, runs INT)')
        self.query_keys('CREATE TABLE IF NOT EXISTS keys (name TEXT PRIMARY KEY, value TEXT)')
        self.query('PRAGMA user_version = 2')

    def migrate(self):
        db_version = self.query('PRAGMA user_version')[0][0]
        if db_version == 0:
            # add mname column to contacts table
            tmp = self.random_str(20)
            self.query('ALTER TABLE contacts RENAME TO %s' % (tmp))
            self.query('CREATE TABLE contacts (fname TEXT, mname TEXT, lname TEXT, email TEXT, title TEXT, region TEXT, country TEXT)')
            self.query('INSERT INTO contacts (fname, lname, email, title, region, country) SELECT fname, lname, email, title, region, country FROM %s' % (tmp))
            self.query('DROP TABLE %s' % (tmp))
            self.query('PRAGMA user_version = 1')
        if db_version == 1:
            # rename name columns
            tmp = self.random_str(20)
            self.query('ALTER TABLE contacts RENAME TO %s' % (tmp))
            self.query('CREATE TABLE contacts (first_name TEXT, middle_name TEXT, last_name TEXT, email TEXT, title TEXT, region TEXT, country TEXT)')
            self.query('INSERT INTO contacts (first_name, middle_name, last_name, email, title, region, country) SELECT fname, mname, lname, email, title, region, country FROM %s' % (tmp))
            self.query('DROP TABLE %s' % (tmp))
            # rename pushpin table
            tmp = self.random_str(20)
            self.query('ALTER TABLE pushpin RENAME TO %s' % (tmp))
            self.query('CREATE TABLE pushpins (source TEXT, screen_name TEXT, profile_name TEXT, profile_url TEXT, media_url TEXT, thumb_url TEXT, message TEXT, latitude TEXT, longitude TEXT, time TEXT)')
            self.query('INSERT INTO pushpins (source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time) SELECT source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time FROM %s' % (tmp))
            self.query('DROP TABLE %s' % (tmp))
            # add new tables
            self.query('CREATE TABLE IF NOT EXISTS domains (domain TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS companies (company TEXT, description TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS netblocks (netblock TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS locations (latitude TEXT, longitude TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS vulnerabilities (host TEXT, reference TEXT, example TEXT, publish_date TEXT, category TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS ports (ip_address TEXT, host TEXT, port TEXT, protocol TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS leaks (leak_id TEXT, description TEXT, source_refs TEXT, leak_type TEXT, title TEXT, import_date TEXT, leak_date TEXT, attackers TEXT, num_entries TEXT, score TEXT, num_domains_affected TEXT, attack_method TEXT, target_industries TEXT, password_hash TEXT, targets TEXT, media_refs TEXT)')
            self.query_keys('CREATE TABLE IF NOT EXISTS keys (name TEXT PRIMARY KEY, value TEXT)')
            self.query('PRAGMA user_version = 2')
        # migrate keys
        key_path = '%s/keys.dat' % (self.home)
        if os.path.exists(key_path):
            try:
                key_data = json.loads(open(key_path, 'rb').read())
                for key in key_data:
                    self.add_key(key, key_data[key])
                os.remove(key_path)
            except:
                self.error('Corrupt key file. Manual migration required.')

    #==================================================
    # WORKSPACE METHODS
    #==================================================

    def init_workspace(self, workspace):
        workspace = '%s/workspaces/%s' % (self.home, workspace)
        new = False
        try:
            os.makedirs(workspace)
            new = True
        except OSError as e:
            if e.errno != errno.EEXIST:
                self.error(e.__str__())
                return False
        # set workspace attributes
        self.workspace = framework.Framework.workspace = workspace
        self.prompt = self.prompt_template % (self.base_prompt[:-3], self.workspace.split('/')[-1])
        # configure new database or conduct migrations
        self.create_db() if new else self.migrate()
        # load workspace configuration
        self.init_global_options()
        self.load_config()
        return True

    def delete_workspace(self, workspace):
        path = '%s/workspaces/%s' % (self.home, workspace)
        try:
            shutil.rmtree(path)
        except OSError:
            return False
        if workspace == self.workspace.split('/')[-1]:
            self.init_workspace('default')
        return True

    def get_workspaces(self):
        dirnames = []
        path = '%s/workspaces' % (self.home)
        for name in os.listdir(path):
            if os.path.isdir('%s/%s' % (path, name)):
                dirnames.append(name)
        return dirnames

    #==================================================
    # SHOW METHODS
    #==================================================

    def show_banner(self):
        banner = open(self.core_path+'banner').read()
        banner_len = len(max(banner.split('\n'), key=len))
        print(banner)
        print('{0:^{1}}'.format('%s[%s v%s, %s]%s' % (framework.Colors.O, self.name, __version__, __author__, framework.Colors.N), banner_len+8)) # +8 compensates for the color bytes
        print('')
        counts = [(len(self.loaded_category[x]), x) for x in self.loaded_category]
        count_len = len(max([str(x[0]) for x in counts], key=len))
        for count in sorted(counts, reverse=True):
            cnt = '[%d]' % (count[0])
            print('%s%s %s modules%s' % (framework.Colors.B, cnt.ljust(count_len+2), count[1].title(), framework.Colors.N))
            # create dynamic easter egg command based on counts
            setattr(self, 'do_%d' % count[0], self.menu_egg)
        print('')

    #==================================================
    # COMMAND METHODS
    #==================================================

    def do_reload(self, params):
        '''Reloads all modules'''
        self.load_modules(True)

    def do_workspaces(self, params):
        '''Manages workspaces'''
        if not params:
            self.help_workspaces()
            return
        params = params.split()
        arg = params.pop(0).lower()
        if arg == 'list':
            self.table([[x] for x in self.get_workspaces()], header=['Workspaces'])
        elif arg in ['add', 'select']:
            if len(params) == 1:
                if not self.init_workspace(params[0]):
                    self.output('Unable to initialize \'%s\' workspace.' % (params[0]))
            else: print('Usage: workspace [add|select] <name>')
        elif arg == 'delete':
            if len(params) == 1:
                if not self.delete_workspace(params[0]):
                    self.output('Unable to delete \'%s\' workspace.' % (params[0]))
            else: print('Usage: workspace delete <name>')
        else:
            self.help_workspaces()

    def do_load(self, params):
        '''Loads specified module'''
        try: self.validate_options()
        except framework.FrameworkException as e:
            self.error(e.message)
            return
        if not params:
            self.help_load()
            return
        # finds any modules that contain params
        modules = [params] if params in self.loaded_modules else [x for x in self.loaded_modules if params in x]
        # notify the user if none or multiple modules are found
        if len(modules) != 1:
            if not modules:
                self.error('Invalid module name.')
            else:
                self.output('Multiple modules match \'%s\'.' % params)
                self.show_modules(modules)
            return
        modulename = modules[0]
        loadedname = self.loaded_modules[modulename]
        prompt = self.prompt_template % (self.prompt[:-3], modulename.split('/')[-1])
        # notify the user if runtime errors exist in the module
        try: y = sys.modules[loadedname].Module((prompt, modulename))
        except Exception:
            if self.options['debug']:
                print('%s%s' % (framework.Colors.R, '-'*60))
                traceback.print_exc()
                print('%s%s' % ('-'*60, framework.Colors.N))
            self.error('ModuleError: %s' % (traceback.format_exc().splitlines()[-1]))
            return
        # return the loaded module if in command line mode
        if self.mode == Mode.CLI: return y
        try: y.cmdloop()
        except KeyboardInterrupt:
            print('')
    do_use = do_load

    #==================================================
    # HELP METHODS
    #==================================================

    def help_workspaces(self):
        print(getattr(self, 'do_workspaces').__doc__)
        print('')
        print('Usage: workspaces [list|add|delete|select]')
        print('')

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_workspaces(self, text, line, *ignored):
        args = line.split()
        options = ['list', 'add', 'delete', 'select']
        if 1 < len(args) < 4:
            if args[1].lower() in options[2:]:
                return [x for x in self.get_workspaces() if x.startswith(text)]
            if args[1].lower() in options[:2]:
                return []
        return [x for x in options if x.startswith(text)]

#=================================================
# SUPPORT CLASSES
#=================================================

class Mode(object):
   '''Contains constants that represent the state of the interpreter.'''
   CONSOLE = 0
   CLI     = 1
   GUI     = 2
   
   def __init__(self):
       raise NotImplementedError('This class should never be instantiated.')
