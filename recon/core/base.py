__author__    = 'Tim Tomes (@lanmaster53)'

from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
import errno
import imp
import json
import os
import random
import re
import shutil
import sys
import yaml
import builtins

# import framework libs
from recon.core import framework
from recon.core.constants import BANNER, BANNER_SMALL

# set the __version__ variable based on the VERSION file
exec(open(os.path.join(Path(os.path.abspath(__file__)).parents[2], 'VERSION')).read())

# using stdout to spool causes tab complete issues
# therefore, override print function
# use a lock for thread safe console and spool output
from threading import Lock
_print_lock = Lock()
# spooling system
def spool_print(*args, **kwargs):
    with _print_lock:
        if framework.Framework._spool:
            framework.Framework._spool.write(f"{args[0]}{os.linesep}")
            framework.Framework._spool.flush()
        # disable terminal output for server jobs
        if framework.Framework._mode == Mode.JOB:
            return
        # new print function must still use the old print function via the backup
        builtins._print(*args, **kwargs)
# make a builtin backup of the original print function
builtins._print = print
# override the builtin print function with the new print function
builtins.print = spool_print

#=================================================
# BASE CLASS
#=================================================

class Recon(framework.Framework):

    repo_url = 'https://raw.githubusercontent.com/lanmaster53/recon-ng-modules/master/'

    def __init__(self, check=True, analytics=True, marketplace=True, accessible=False):
        framework.Framework.__init__(self, 'base')
        self._name = 'recon-ng'
        self._prompt_template = '{}[{}] > '
        self._base_prompt = self._prompt_template.format('', self._name)
        # set toggle flags
        self._check = check
        self._analytics = analytics
        self._marketplace = marketplace
        self._accessible = accessible
        # set path variables
        self.app_path = framework.Framework.app_path = sys.path[0]
        self.core_path = framework.Framework.core_path = os.path.join(self.app_path, 'core')
        self.home_path = framework.Framework.home_path = os.path.join(os.path.expanduser('~'), '.recon-ng')
        self.mod_path = framework.Framework.mod_path = os.path.join(self.home_path, 'modules')
        self.data_path = framework.Framework.data_path = os.path.join(self.home_path, 'data')
        self.spaces_path = framework.Framework.spaces_path = os.path.join(self.home_path, 'workspaces')

    def start(self, mode, workspace='default'):
        # initialize framework components
        self._mode = framework.Framework._mode = mode
        self._init_global_options()
        self._init_home()
        self._init_workspace(workspace)
        self._check_version()
        if self._mode == Mode.CONSOLE:
            self._print_banner()
            self.cmdloop()

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def _init_global_options(self):
        self.options = self._global_options
        self.register_option('nameserver', '8.8.8.8', True, 'default nameserver for the resolver mixin')
        self.register_option('proxy', None, False, 'proxy server (address:port)')
        self.register_option('threads', 10, True, 'number of threads (where applicable)')
        self.register_option('timeout', 10, True, 'socket timeout (seconds)')
        self.register_option('user-agent', f"Recon-ng/v{__version__.split('.')[0]}", True, 'user-agent string')
        self.register_option('verbosity', 1, True, 'verbosity level (0 = minimal, 1 = verbose, 2 = debug)')

    def _init_home(self):
        # initialize home folder
        if not os.path.exists(self.home_path):
            os.makedirs(self.home_path)
        # initialize keys database
        self._query_keys('CREATE TABLE IF NOT EXISTS keys (name TEXT PRIMARY KEY, value TEXT)')
        # initialize module index
        self._fetch_module_index()

    def _check_version(self):
        if self._check:
            pattern = r"'(\d+\.\d+\.\d+[^']*)'"
            remote = 0
            local = 0
            try:
                remote = re.search(pattern, self.request('GET', 'https://raw.githubusercontent.com/lanmaster53/recon-ng/master/VERSION').text).group(1)
                local = re.search(pattern, open('VERSION').read()).group(1)
            except Exception as e:
                self.error(f"Version check failed ({type(e).__name__}).")
                #self.print_exception()
            if remote != local:
                self.alert('Your version of Recon-ng does not match the latest release.')
                self.alert('Please consider updating before further use.')
                self.output(f"Remote version:  {remote}")
                self.output(f"Local version:   {local}")
        else:
            self.alert('Version check disabled.')

    def _print_banner(self):
        banner = BANNER
        banner_len = len(max(banner.split(os.linesep), key=len))
        author = '{0:^{1}}'.format(f"{framework.Colors.O}[{self._name} v{__version__}, {__author__}]{framework.Colors.N}", banner_len + 8)
        if self._accessible:
            banner = BANNER_SMALL
            author = f"{framework.Colors.O}{self._name}, version {__version__}, by {__author__}{framework.Colors.N}"
        print(banner)
        print(author)
        print('')
        counts = [(len(self._loaded_category[x]), x) for x in self._loaded_category]
        if counts:
            count_len = len(max([self.to_unicode_str(x[0]) for x in counts], key=len))
            for count in sorted(counts, reverse=True):
                cnt = f"[{count[0]}]"
                print(f"{framework.Colors.B}{cnt.ljust(count_len+2)} {count[1].title()} modules{framework.Colors.N}")
                # create dynamic easter egg command based on counts
                setattr(self, f"do_{count[0]}", self._menu_egg)
        else:
            self.alert('No modules enabled/installed.')
        print('')

    def _send_analytics(self, cd):
        if self._analytics:
            try:
                cid_path = os.path.join(self.home_path, '.cid')
                if not os.path.exists(cid_path):
                    # create the cid and file
                    import uuid
                    with open(cid_path, 'w') as fp:
                        fp.write(self.to_unicode_str(uuid.uuid4()))
                with open(cid_path) as fp:
                    cid = fp.read().strip()
                params = {
                        'v': 1,
                        'tid': 'UA-52269615-2',
                        'cid': cid,
                        't': 'screenview',
                        'an': 'Recon-ng',
                        'av': __version__,
                        'cd': cd
                        }
                self.request('GET', 'https://www.google-analytics.com/collect', params=params)
            except Exception as e:
                self.debug(f"Analytics failed ({type(e).__name__}).")
                #self.print_exception()
                return
        else:
            self.debug('Analytics disabled.')

    def _menu_egg(self, params):
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
            '1980 called. They want there menu driven UI back.',
        ]
        print(random.choice(eggs))
        return

    #==================================================
    # WORKSPACE METHODS
    #==================================================

    def _init_workspace(self, workspace):
        if not workspace:
            return
        path = os.path.join(self.spaces_path, workspace)
        self.workspace = framework.Framework.workspace = path
        if not os.path.exists(path):
            os.makedirs(path)
            self._create_db()
        else:
            self._migrate_db()
        # set workspace prompt
        self.prompt = self._prompt_template.format(self._base_prompt[:-3], self.workspace.split('/')[-1])
        # load workspace configuration
        self._load_config()
        # reload modules after config to populate options
        self._load_modules()
        return True

    def remove_workspace(self, workspace):
        path = os.path.join(self.spaces_path, workspace)
        try:
            shutil.rmtree(path)
        except OSError:
            return False
        if workspace == self.workspace.split('/')[-1]:
            self._init_workspace('default')
        return True

    def _get_workspaces(self):
        workspaces = []
        path = self.spaces_path
        for name in os.listdir(path):
            if os.path.isdir(os.path.join(path, name)):
                workspaces.append(name)
        return workspaces

    def _get_snapshots(self):
        snapshots = []
        for f in os.listdir(self.workspace):
            if re.search(r'^snapshot_\d{14}.db$', f):
                snapshots.append(f)
        return snapshots

    def _create_db(self):
        self.query('CREATE TABLE IF NOT EXISTS domains (domain TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS companies (company TEXT, description TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS netblocks (netblock TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS locations (latitude TEXT, longitude TEXT, street_address TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS vulnerabilities (host TEXT, reference TEXT, example TEXT, publish_date TEXT, category TEXT, status TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS ports (ip_address TEXT, host TEXT, port TEXT, protocol TEXT, banner TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS hosts (host TEXT, ip_address TEXT, region TEXT, country TEXT, latitude TEXT, longitude TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS contacts (first_name TEXT, middle_name TEXT, last_name TEXT, email TEXT, title TEXT, region TEXT, country TEXT, phone TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS credentials (username TEXT, password TEXT, hash TEXT, type TEXT, leak TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS leaks (leak_id TEXT, description TEXT, source_refs TEXT, leak_type TEXT, title TEXT, import_date TEXT, leak_date TEXT, attackers TEXT, num_entries TEXT, score TEXT, num_domains_affected TEXT, attack_method TEXT, target_industries TEXT, password_hash TEXT, password_type TEXT, targets TEXT, media_refs TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS pushpins (source TEXT, screen_name TEXT, profile_name TEXT, profile_url TEXT, media_url TEXT, thumb_url TEXT, message TEXT, latitude TEXT, longitude TEXT, time TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS profiles (username TEXT, resource TEXT, url TEXT, category TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS repositories (name TEXT, owner TEXT, description TEXT, resource TEXT, category TEXT, url TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS dashboard (module TEXT PRIMARY KEY, runs INT)')
        self.query('PRAGMA user_version = 10')

    def _migrate_db(self):
        db_version = lambda self: self.query('PRAGMA user_version')[0][0]
        db_orig = db_version(self)
        if db_version(self) == 0:
            # add mname column to contacts table
            tmp = self.get_random_str(20)
            self.query(f"ALTER TABLE contacts RENAME TO {tmp}")
            self.query('CREATE TABLE contacts (fname TEXT, mname TEXT, lname TEXT, email TEXT, title TEXT, region TEXT, country TEXT)')
            self.query(f"INSERT INTO contacts (fname, lname, email, title, region, country) SELECT fname, lname, email, title, region, country FROM {tmp}")
            self.query(f"DROP TABLE {tmp}")
            self.query('PRAGMA user_version = 1')
        if db_version(self) == 1:
            # rename name columns
            tmp = self.get_random_str(20)
            self.query(f"ALTER TABLE contacts RENAME TO {tmp}")
            self.query('CREATE TABLE contacts (first_name TEXT, middle_name TEXT, last_name TEXT, email TEXT, title TEXT, region TEXT, country TEXT)')
            self.query(f"INSERT INTO contacts (first_name, middle_name, last_name, email, title, region, country) SELECT fname, mname, lname, email, title, region, country FROM {tmp}")
            self.query(f"DROP TABLE {tmp}")
            # rename pushpin table
            self.query('ALTER TABLE pushpin RENAME TO pushpins')
            # add new tables
            self.query('CREATE TABLE IF NOT EXISTS domains (domain TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS companies (company TEXT, description TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS netblocks (netblock TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS locations (latitude TEXT, longitude TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS vulnerabilities (host TEXT, reference TEXT, example TEXT, publish_date TEXT, category TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS ports (ip_address TEXT, host TEXT, port TEXT, protocol TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS leaks (leak_id TEXT, description TEXT, source_refs TEXT, leak_type TEXT, title TEXT, import_date TEXT, leak_date TEXT, attackers TEXT, num_entries TEXT, score TEXT, num_domains_affected TEXT, attack_method TEXT, target_industries TEXT, password_hash TEXT, targets TEXT, media_refs TEXT)')
            self.query('PRAGMA user_version = 2')
        if db_version(self) == 2:
            # add street_address column to locations table
            self.query('ALTER TABLE locations ADD COLUMN street_address TEXT')
            self.query('PRAGMA user_version = 3')
        if db_version(self) == 3:
            # account for db_version bug
            if 'creds' in self.get_tables():
                # rename creds table
                self.query('ALTER TABLE creds RENAME TO credentials')
            self.query('PRAGMA user_version = 4')
        if db_version(self) == 4:
            # add status column to vulnerabilities table
            if 'status' not in [x[0] for x in self.get_columns('vulnerabilities')]:
                self.query('ALTER TABLE vulnerabilities ADD COLUMN status TEXT')
            # add module column to all tables
            for table in ['domains', 'companies', 'netblocks', 'locations', 'vulnerabilities', 'ports', 'hosts', 'contacts', 'credentials', 'leaks', 'pushpins']:
                if 'module' not in [x[0] for x in self.get_columns(table)]:
                    self.query(f"ALTER TABLE {table} ADD COLUMN module TEXT")
            self.query('PRAGMA user_version = 5')
        if db_version(self) == 5:
            # add profile table
            self.query('CREATE TABLE IF NOT EXISTS profiles (username TEXT, resource TEXT, url TEXT, category TEXT, notes TEXT, module TEXT)')
            self.query('PRAGMA user_version = 6')
        if db_version(self) == 6:
            # add repositories table
            self.query('CREATE TABLE IF NOT EXISTS repositories (name TEXT, owner TEXT, description TEXT, resource TEXT, category TEXT, url TEXT, module TEXT)')
            self.query('PRAGMA user_version = 7')
        if db_version(self) == 7:
            # add password_type column to leaks table
            self.query('ALTER TABLE leaks ADD COLUMN password_type TEXT')
            self.query('UPDATE leaks SET password_type=\'unknown\'')
            self.query('PRAGMA user_version = 8')
        if db_version(self) == 8:
            # add banner column to ports table
            self.query('ALTER TABLE ports ADD COLUMN banner TEXT')
            # add notes column to all tables
            for table in ['domains', 'companies', 'netblocks', 'locations', 'vulnerabilities', 'ports', 'hosts', 'contacts', 'credentials', 'leaks', 'pushpins', 'profiles', 'repositories']:
                if 'notes' not in [x[0] for x in self.get_columns(table)]:
                    self.query(f"ALTER TABLE {table} ADD COLUMN notes TEXT")
            self.query('PRAGMA user_version = 9')
        if db_version(self) == 9:
            # add phone column to contacts table
            self.query('ALTER TABLE contacts ADD COLUMN phone TEXT')
            self.query('PRAGMA user_version = 10')
        if db_orig != db_version(self):
            self.alert(f"Database upgraded to version {db_version(self)}.")

    #==================================================
    # MODULE METHODS
    #==================================================

    def _request_file_from_repo(self, path):
        resp = self.request('GET', urljoin(self.repo_url, path))
        if resp.status_code != 200:
            raise framework.FrameworkException(f"Invalid response from module repository ({resp.status_code}).")
        return resp

    def _write_local_file(self, path, content):
        dirpath = os.path.sep.join(path.split(os.path.sep)[:-1])
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(path, 'w') as outfile:
            outfile.write(content)

    def _remove_empty_dirs(self, base_path):
        for root, dirs, files in os.walk(base_path, topdown=False):
            for rel_path in dirs:
                abs_path = os.path.join(root, rel_path)
                if os.path.exists(abs_path):
                    if not os.listdir(abs_path):
                        os.removedirs(abs_path)

    def _fetch_module_index(self):
        if self._marketplace:
            content = '[]'
            self.debug('Fetching index file...')
            try:
                resp = self._request_file_from_repo('modules.yml')
            except Exception as e:
                self.error(f"Unable to synchronize module index. ({type(e).__name__})")
                #self.print_exception()
                return
            content = resp.text
            path = os.path.join(self.home_path, 'modules.yml')
            self._write_local_file(path, content)
        else:
            self.alert('Marketplace disabled.')

    def _update_module_index(self):
        self.debug('Updating index file...')
        # initialize module index
        self._module_index = []
        # load module index from local copy
        path = os.path.join(self.home_path, 'modules.yml')
        if os.path.exists(path):
            with open(path, 'r') as infile:
                self._module_index = yaml.safe_load(infile)
            # add status to index for each module
            for module in self._module_index:
                status = 'not installed'
                if module['path'] in self._loaded_category.get('disabled', []):
                    status = 'disabled'
                elif module['path'] in self._loaded_modules.keys():
                    status = 'installed'
                    loaded = self._loaded_modules[module['path']]
                    if loaded.meta['version'] != module['version']:
                        status = 'outdated'
                module['status'] = status

    def _search_module_index(self, s):
        keys = ('path', 'name', 'description', 'status')
        modules = []
        for module in self._module_index:
            for key in keys:
                if re.search(s, module[key]):
                    modules.append(module)
                    break
        return modules

    def _get_module_from_index(self, path):
        for module in self._module_index:
            if module['path'] == path:
                return module
        return None

    def _install_module(self, path):
        # download supporting data files
        downloads = {}
        files = self._get_module_from_index(path).get('files', [])
        for filename in files:
            try:
                resp = self._request_file_from_repo('/'.join(['data', filename]))
            except:
                self.error(f"Supporting file download for {path} failed: ({filename})")
                self.error('Module installation aborted.')
                raise
            abs_path = os.path.join(self.data_path, filename)
            downloads[abs_path] = resp.text
        # download the module
        rel_path = '.'.join([path, 'py'])
        try:
            resp = self._request_file_from_repo('/'.join(['modules', rel_path]))
        except:
            self.error(f"Module installation failed: {path}")
            raise
        abs_path = os.path.join(self.mod_path, rel_path)
        downloads[abs_path] = resp.text
        # install the module
        for abs_path, content in downloads.items():
            self._write_local_file(abs_path, content)
        self.output(f"Module installed: {path}")

    def _remove_module(self, path):
        # remove the module
        rel_path = '.'.join([path, 'py'])
        abs_path = os.path.join(self.mod_path, rel_path)
        os.remove(abs_path)
        # remove supporting data files
        files = self._get_module_from_index(path).get('files', [])
        for filename in files:
            abs_path = os.path.join(self.data_path, filename)
            if os.path.exists(abs_path):
                os.remove(abs_path)
        self.output(f"Module removed: {path}")

    def _load_modules(self):
        self._loaded_category = {}
        self._loaded_modules = framework.Framework._loaded_modules = {}
        # crawl the module directory and build the module tree
        for dirpath, dirnames, filenames in os.walk(self.mod_path, followlinks=True):
            # remove hidden files and directories
            filenames = [f for f in filenames if not f[0] == '.']
            dirnames[:] = [d for d in dirnames if not d[0] == '.']
            if len(filenames) > 0:
                for filename in [f for f in filenames if f.endswith('.py')]:
                    self._load_module(dirpath, filename)
        # cleanup module directory
        self._remove_empty_dirs(self.mod_path)
        # update module index
        self._update_module_index()

    def _load_module(self, dirpath, filename):
        mod_name = filename.split('.')[0]
        mod_category = re.search('/modules/([^/]*)', dirpath).group(1)
        mod_dispname = '/'.join(re.split('/modules/', dirpath)[-1].split('/') + [mod_name])
        mod_loadname = mod_dispname.replace('/', '_')
        mod_loadpath = os.path.join(dirpath, filename)
        mod_file = open(mod_loadpath)
        try:
            # import the module into memory
            mod = imp.load_source(mod_loadname, mod_loadpath, mod_file)
            __import__(mod_loadname)
            # add the module to the framework's loaded modules
            self._loaded_modules[mod_dispname] = sys.modules[mod_loadname].Module(mod_dispname)
            self._categorize_module(mod_category, mod_dispname)
            # return indication of success to support module reload
            return True
        except ImportError as e:
            # notify the user of missing dependencies
            self.error(f"Module '{mod_dispname}' disabled. Dependency required: '{self.to_unicode_str(e)[16:]}'")
        except:
            # notify the user of errors
            self.print_exception()
            self.error(f"Module '{mod_dispname}' disabled.")
        # remove the module from the framework's loaded modules
        self._loaded_modules.pop(mod_dispname, None)
        self._categorize_module('disabled', mod_dispname)

    def _categorize_module(self, category, module):
        if not category in self._loaded_category:
            self._loaded_category[category] = []
        self._loaded_category[category].append(module)

    #==================================================
    # COMMAND METHODS
    #==================================================

    def do_index(self, params):
        '''Creates a module index (dev only)'''
        mod_path, file_name = self._parse_params(params)
        if not mod_path:
            self.help_index()
            return
        self.output('Building index markup...')
        yaml_objs = []
        modules = [m for m in self._loaded_modules.items() if mod_path in m[0] or mod_path == 'all']
        for path, module in sorted(modules, key=lambda k: k[0]):
            yaml_obj = {}
            # not in meta
            yaml_obj['path'] = path
            yaml_obj['last_updated'] = datetime.strftime(datetime.now(), '%Y-%m-%d')
            # meta required
            yaml_obj['author'] = module.meta.get('author')
            yaml_obj['name'] = module.meta.get('name')
            yaml_obj['description'] = module.meta.get('description')
            yaml_obj['version'] = module.meta.get('version', '1.0')
            # meta optional
            #yaml_obj['comments'] = module.meta.get('comments', [])
            yaml_obj['dependencies'] = module.meta.get('dependencies', [])
            yaml_obj['files'] = module.meta.get('files', [])
            #yaml_obj['options'] = module.meta.get('options', [])
            #yaml_obj['query'] = module.meta.get('query', '')
            yaml_obj['required_keys'] = module.meta.get('required_keys', [])
            yaml_objs.append(yaml_obj)
        if yaml_objs:
            markup = yaml.safe_dump(yaml_objs)
            print(markup)
            # write to file if index name provided
            if file_name:
                with open(file_name, 'w') as outfile:
                    outfile.write(markup)
                self.output('Module index created.')
        else:
            self.output('No modules found.')

    def do_marketplace(self, params):
        '''Interfaces with the module marketplace'''
        if not self._marketplace:
            self.alert('Marketplace disabled.')
            return
        if not params:
            self.help_marketplace()
            return
        arg, params = self._parse_params(params)
        if arg in self._parse_subcommands('marketplace'):
            return getattr(self, '_do_marketplace_'+arg)(params)
        else:
            self.help_marketplace()

    def _do_marketplace_refresh(self, params):
        '''Refreshes the marketplace index'''
        self._fetch_module_index()
        self._update_module_index()
        self.output('Marketplace index refreshed.')

    def _do_marketplace_search(self, params):
        '''Searches marketplace modules'''
        modules = [m for m in self._module_index]
        if params:
            self.output(f"Searching module index for '{params}'...")
            modules = self._search_module_index(params)
        if modules:
            rows = []
            for module in sorted(modules, key=lambda m: m['path']):
                row = []
                for key in ('path', 'version', 'status', 'last_updated'):
                    row.append(module[key])
                row.append('*' if module['dependencies'] else '')
                row.append('*' if module['required_keys'] else '')
                rows.append(row)
            header = ('Path', 'Version', 'Status', 'Updated', 'D', 'K')
            self.table(rows, header=header)
            print(f"{self.spacer}D = Has dependencies. See info for details.")
            print(f"{self.spacer}K = Requires keys. See info for details.{os.linesep}")
        else:
            self.error('No modules found.')
            self._help_marketplace_search()

    def _do_marketplace_info(self, params):
        '''Shows detailed information about available modules'''
        if not params:
            self._help_marketplace_info()
            return
        modules = [m for m in self._module_index if params in m['path'] or params == 'all']
        if modules:
            for module in modules:
                rows = []
                for key in ('path', 'name', 'author', 'version', 'last_updated', 'description', 'required_keys', 'dependencies', 'files', 'status'):
                    row = (key, module[key])
                    rows.append(row)
                self.table(rows)
        else:
            self.error('Invalid module path.')

    def _do_marketplace_install(self, params):
        '''Installs modules from the marketplace'''
        if not params:
            self._help_marketplace_install()
            return
        modules = [m for m in self._module_index if params in m['path'] or params == 'all']
        if modules:
            for module in modules:
                self._install_module(module['path'])
            self._do_modules_reload('')
        else:
            self.error('Invalid module path.')

    def _do_marketplace_remove(self, params):
        '''Removes marketplace modules from the framework'''
        if not params:
            self._help_marketplace_remove()
            return
        modules = [m for m in self._module_index if m['status'] in ('installed', 'disabled') and (params in m['path'] or params == 'all')]
        if modules:
            for module in modules:
                self._remove_module(module['path'])
            self._do_modules_reload('')
        else:
            self.error('Invalid module path.')

    def do_workspaces(self, params):
        '''Manages workspaces'''
        if not params:
            self.help_workspaces()
            return
        arg, params = self._parse_params(params)
        if arg in self._parse_subcommands('workspaces'):
            return getattr(self, '_do_workspaces_'+arg)(params)
        else:
            self.help_workspaces()

    def _do_workspaces_list(self, params):
        '''Lists existing workspaces'''
        rows = []
        for workspace in self._get_workspaces():
            db_path = os.path.join(self.spaces_path, workspace, 'data.db')
            modified = datetime.fromtimestamp(os.path.getmtime(db_path)).strftime('%Y-%m-%d %H:%M:%S')
            rows.append((workspace, modified))
        rows.sort(key=lambda x: x[0])
        self.table(rows, header=['Workspaces', 'Modified'])

    def _do_workspaces_create(self, params):
        '''Creates a new workspace'''
        if not params:
            self._help_workspaces_create()
            return
        if not self._init_workspace(params):
            self.output(f"Unable to create '{params}' workspace.")

    def _do_workspaces_load(self, params):
        '''Loads an existing workspace'''
        if not params:
            self._help_workspaces_load()
            return
        if params in self._get_workspaces():
            if not self._init_workspace(params):
                self.output(f"Unable to initialize '{params}' workspace.")
        else:
            self.output('Invalid workspace name.')

    def _do_workspaces_remove(self, params):
        '''Removes an existing workspace'''
        if not params:
            self._help_workspaces_remove()
            return
        if not self.remove_workspace(params):
            self.output(f"Unable to remove '{params}' workspace.")

    def do_snapshots(self, params):
        '''Manages workspace snapshots'''
        if not params:
            self.help_snapshots()
            return
        arg, params = self._parse_params(params)
        if arg in self._parse_subcommands('snapshots'):
            return getattr(self, '_do_snapshots_'+arg)(params)
        else:
            self.help_snapshots()

    def _do_snapshots_list(self, params):
        '''Lists existing database snapshots'''
        snapshots = self._get_snapshots()
        if snapshots:
            self.table([[x] for x in snapshots], header=['Snapshots'])
        else:
            self.output('This workspace has no snapshots.')

    def _do_snapshots_take(self, params):
        '''Takes a snapshot of the current database'''
        ts = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
        snapshot = f"snapshot_{ts}.db"
        src = os.path.join(self.workspace, 'data.db')
        dst = os.path.join(self.workspace, snapshot)
        shutil.copyfile(src, dst)
        self.output(f"Snapshot created: {snapshot}")

    def _do_snapshots_load(self, params):
        '''Loads an existing database snapshot'''
        if not params:
            self._help_snapshots_load()
            return
        if params in self._get_snapshots():
            src = os.path.join(self.workspace, params)
            dst = os.path.join(self.workspace, 'data.db')
            shutil.copyfile(src, dst)
            self.output(f"Snapshot loaded: {params}")
        else:
            self.error(f"No snapshot named '{params}'.")

    def _do_snapshots_remove(self, params):
        '''Removes an existing snapshot'''
        if not params:
            self._help_snapshots_remove()
            return
        if params in self._get_snapshots():
            os.remove(os.path.join(self.workspace, params))
            self.output(f"Snapshot removed: {params}")
        else:
            self.error(f"No snapshot named '{params}'.")

    def _do_modules_load(self, params):
        '''Loads a module'''
        # validate global options before loading the module
        try:
            self._validate_options()
        except framework.FrameworkException as e:
            self.error(e)
            return
        if not params:
            self._help_modules_load()
            return
        # finds any modules that contain params
        modules = self._match_modules(params)
        # notify the user if none or multiple modules are found
        if len(modules) != 1:
            if not modules:
                self.error('Invalid module name.')
            else:
                self.output(f"Multiple modules match '{params}'.")
                self._list_modules(modules)
            return
        # load the module
        mod_dispname = modules[0]
        # loop to support reload logic
        while True:
            y = self._loaded_modules[mod_dispname]
            # send analytics information
            mod_loadpath = os.path.abspath(sys.modules[y.__module__].__file__)
            self._send_analytics(mod_dispname)
            # return the loaded module if not in console mode
            if self._mode != Mode.CONSOLE:
                return y
            # begin a command loop
            y.prompt = self._prompt_template.format(self.prompt[:-3], mod_dispname.split('/')[-1])
            try:
                y.cmdloop()
            except KeyboardInterrupt:
                print('')
            if y._exit == 1:
                return True
            if y._reload == 1:
                self.output('Reloading module...')
                # reload the module in memory
                is_loaded = self._load_module(os.path.dirname(mod_loadpath), os.path.basename(mod_loadpath))
                if is_loaded:
                    # reload the module in the framework
                    continue
                # shuffle category counts?
            break

    def _do_modules_reload(self, params):
        '''Reloads installed modules'''
        self.output('Reloading modules...')
        self._load_modules()

    #==================================================
    # HELP METHODS
    #==================================================

    def help_index(self):
        print(getattr(self, 'do_index').__doc__)
        print(f"{os.linesep}Usage: index <module|all> <index>{os.linesep}")

    def help_marketplace(self):
        print(getattr(self, 'do_marketplace').__doc__)
        print(f"{os.linesep}Usage: marketplace <{'|'.join(self._parse_subcommands('marketplace'))}> [...]{os.linesep}")

    def _help_marketplace_search(self):
        print(getattr(self, '_do_marketplace_search').__doc__)
        print(f"{os.linesep}Usage: marketplace search [<regex>]{os.linesep}")

    def _help_marketplace_info(self):
        print(getattr(self, '_do_marketplace_info').__doc__)
        print(f"{os.linesep}Usage: marketplace info <<path>|<prefix>|all>{os.linesep}")

    def _help_marketplace_install(self):
        print(getattr(self, '_do_marketplace_install').__doc__)
        print(f"{os.linesep}Usage: marketplace install <<path>|<prefix>|all>{os.linesep}")

    def _help_marketplace_remove(self):
        print(getattr(self, '_do_marketplace_remove').__doc__)
        print(f"{os.linesep}Usage: marketplace remove <<path>|<prefix>|all>{os.linesep}")

    def help_workspaces(self):
        print(getattr(self, 'do_workspaces').__doc__)
        print(f"{os.linesep}Usage: workspaces <{'|'.join(self._parse_subcommands('workspaces'))}> [...]{os.linesep}")

    def _help_workspaces_create(self):
        print(getattr(self, '_do_workspaces_create').__doc__)
        print(f"{os.linesep}Usage: workspace create <name>{os.linesep}")

    def _help_workspaces_load(self):
        print(getattr(self, '_do_workspaces_load').__doc__)
        print(f"{os.linesep}Usage: workspace load <name>{os.linesep}")

    def _help_workspaces_remove(self):
        print(getattr(self, '_do_workspaces_remove').__doc__)
        print(f"{os.linesep}Usage: workspace remove <name>{os.linesep}")

    def help_snapshots(self):
        print(getattr(self, 'do_snapshots').__doc__)
        print(f"{os.linesep}Usage: snapshots <{'|'.join(self._parse_subcommands('snapshots'))}> [...]{os.linesep}")

    def _help_snapshots_load(self):
        print(getattr(self, '_do_snapshots_load').__doc__)
        print(f"{os.linesep}Usage: snapshots load <name>{os.linesep}")

    def _help_snapshots_remove(self):
        print(getattr(self, '_do_snapshots_remove').__doc__)
        print(f"{os.linesep}Usage: snapshots remove <name>{os.linesep}")

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_index(self, text, line, *ignored):
        if len(line.split(' ')) == 2:
            return [x for x in self._loaded_modules if x.startswith(text)]
        return []

    def complete_marketplace(self, text, line, *ignored):
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._parse_subcommands('marketplace')
        if arg in subs:
            return getattr(self, '_complete_marketplace_'+arg)(text, params)
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_marketplace_refresh(self, text, *ignored):
        return []
    _complete_marketplace_search = _complete_marketplace_refresh

    def _complete_marketplace_info(self, text, *ignored):
        return [x['path'] for x in self._module_index if x['path'].startswith(text)]
    _complete_marketplace_install = _complete_marketplace_info

    def _complete_marketplace_remove(self, text, *ignored):
        return [x['path'] for x in self._module_index if x['status'] == 'installed' and x['path'].startswith(text)]

    def complete_workspaces(self, text, line, *ignored):
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._parse_subcommands('workspaces')
        if arg in subs:
            return getattr(self, '_complete_workspaces_'+arg)(text, params)
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_workspaces_list(self, text, *ignored):
        return []
    _complete_workspaces_create = _complete_workspaces_list

    def _complete_workspaces_load(self, text, *ignored):
        return [x for x in self._get_workspaces() if x.startswith(text)]
    _complete_workspaces_remove = _complete_workspaces_load

    def complete_snapshots(self, text, line, *ignored):
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._parse_subcommands('snapshots')
        if arg in subs:
            return getattr(self, '_complete_snapshots_'+arg)(text, params)
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_snapshots_list(self, text, *ignored):
        return []
    _complete_snapshots_take = _complete_snapshots_list

    def _complete_snapshots_load(self, text, *ignored):
        return [x for x in self._get_snapshots() if x.startswith(text)]
    _complete_snapshots_remove = _complete_snapshots_load

    def _complete_modules_reload(self, text, *ignored):
        return []

#=================================================
# SUPPORT CLASSES
#=================================================

class Mode(object):
   '''Contains constants that represent the state of the interpreter.'''
   CONSOLE = 0
   CLI     = 1
   WEB     = 2
   JOB     = 3
   
   def __init__(self):
       raise NotImplementedError('This class should never be instantiated.')
