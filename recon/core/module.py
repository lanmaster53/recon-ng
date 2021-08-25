from requests.exceptions import Timeout
import html
import http.cookiejar
import io
import os
import re
import socket
import sqlite3
import sys
import textwrap
import yaml
# framework libs
from recon.core import framework
from recon.utils import validators

#=================================================
# MODULE CLASS
#=================================================

class BaseModule(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.options = framework.Options()
        # update the meta dictionary by merging the class variable with any frontmatter
        self.meta = self._merge_dicts(self.meta, self._parse_frontmatter())
        # register a data source option if a default query is specified in the module
        if self.meta.get('query'):
            self._default_source = self.meta.get('query')
            self.register_option('source', 'default', True, 'source of input (see \'info\' for details)')
        # register all other specified options
        if self.meta.get('options'):
            for option in self.meta.get('options'):
                self.register_option(*option)
        # register any required keys
        if self.meta.get('required_keys'):
            self.keys = {}
            for key in self.meta.get('required_keys'):
                # add key to the database
                self._query_keys('INSERT OR IGNORE INTO keys (name) VALUES (?)', (key,))
                # migrate the old key if needed
                self._migrate_key(key)
                # add key to local keys dictionary
                # could fail to load on exception here to prevent loading modules
                # without required keys, but would need to do it in a separate loop
                # so that all keys get added to the database first. for now, the
                # framework will warn users of the missing key, but allow the module
                # to load.
                self.keys[key] = self.get_key(key)
                if not self.keys.get(key):
                    self.error(f"'{key}' key not set. {self._modulename.split('/')[-1]} module will likely fail at runtime. See 'keys add'.")
        self._reload = 0

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def _merge_dicts(self, x, y):
        # start with x's keys and values
        z = x.copy()
        # modify z with y's keys and values
        z.update(y)
        return z

    def _parse_frontmatter(self):
        rel_path = '.'.join([self._modulename, 'py'])
        abs_path = os.path.join(self.mod_path, rel_path)
        with open(abs_path) as fp:
            state = False
            yaml_src = ''
            for line in fp:
                 if line == '---\n':
                      state = not state
                      continue
                 if state:
                      yaml_src += line
        return yaml.safe_load(yaml_src) or {}

    def _migrate_key(self, key):
        '''migrate key from old .dat file'''
        key_path = os.path.join(self.home_path, 'keys.dat')
        if os.path.exists(key_path):
            try:
                key_data = json.loads(open(key_path, 'rb').read())
                if key_data.get(key):
                    self.add_key(key, key_data.get(key))
            except:
                self.error(f"Corrupt key file. Manual migration of '{key}' required.")

    def ascii_sanitize(self, s):
        return ''.join([char for char in s if ord(char) in [10,13] + range(32, 126)])

    def html_unescape(self, s):
        '''Unescapes HTML markup and returns an unescaped string.'''
        return html.unescape(s)

    def html_escape(self, s):
        escapes = {
            '&': '&amp;',
            '"': '&quot;',
            "'": '&apos;',
            '>': '&gt;',
            '<': '&lt;',
            }
        return ''.join(escapes.get(c,c) for c in s)

    def cidr_to_list(self, string):
        import ipaddress
        return [str(ip) for ip in ipaddress.ip_network(string)]

    def hosts_to_domains(self, hosts, exclusions=[]):
        domains = []
        for host in hosts:
            elements = host.split('.')
            # recursively walk through the elements
            # extracting all possible (sub)domains
            while len(elements) >= 2:
                # account for domains stored as hosts
                if len(elements) == 2:
                    domain = '.'.join(elements)
                else:
                    # drop the host element
                    domain = '.'.join(elements[1:])
                if domain not in domains + exclusions:
                    domains.append(domain)
                del elements[0]
        return domains

    def _validate_input(self):
        validator_type = self.meta.get('validator')
        if not validator_type:
            # passthru, no validator required
            self.debug('No validator required.')
            return
        validator = None
        validator_name = validator_type.capitalize() + 'Validator'
        for obj in [self, validators]:
            if hasattr(obj, validator_name):
                validator = getattr(validators, validator_name)()
        if not validator:
            # passthru, no validator defined
            self.debug('No validator defined.')
            return
        inputs = self._get_source(self.options['source'], self._default_source)
        for _input in inputs:
            validator.validate(_input)
            self.debug('All inputs validated.')

    #==================================================
    # OPTIONS METHODS
    #==================================================

    def _get_source(self, params, query=None):
        prefix = params.split()[0].lower()
        if prefix in ['query', 'default']:
            query = ' '.join(params.split()[1:]) if prefix == 'query' else query
            try:
                results = self.query(query)
            except sqlite3.OperationalError as e:
                raise framework.FrameworkException(f"Invalid source query. {type(e).__name__} {e}")
            if not results:
                sources = []
            elif len(results[0]) > 1:
                sources = [x[:len(x)] for x in results]
                #raise framework.FrameworkException('Too many columns of data as source input.')
            else:
                sources = [x[0] for x in results]
        elif os.path.exists(params):
            sources = open(params).read().split()
        else:
            sources = [params]
        if not sources:
            raise framework.FrameworkException('Source contains no input.')
        return sources

    #==================================================
    # REQUEST METHODS
    #==================================================

    def make_cookie(self, name, value, domain, path='/'):
        return http.cookiejar.Cookie(
            version=0, 
            name=name, 
            value=value,
            port=None, 
            port_specified=False,
            domain=domain, 
            domain_specified=True, 
            domain_initial_dot=False,
            path=path, 
            path_specified=True,
            secure=False,
            expires=None,
            discard=False,
            comment=None,
            comment_url=None,
            rest=None
        )

    #==================================================
    # COMMAND METHODS
    #==================================================

    def do_goptions(self, params):
        '''Manages the global context options'''
        if not params:
            self.help_goptions()
            return
        arg, params = self._parse_params(params)
        if arg in self._parse_subcommands('goptions'):
            return getattr(self, '_do_goptions_'+arg)(params)
        else:
            self.help_goptions()

    def _do_goptions_list(self, params):
        '''Shows the global context options'''
        self._list_options(self._global_options)

    def _do_goptions_set(self, params):
        '''Sets a global context option'''
        option, value = self._parse_params(params)
        if not (option and value):
            self._help_goptions_set()
            return
        name = option.upper()
        if name in self._global_options:
            self._global_options[name] = value
            print(f"{name} => {value}")
            self._save_config(name, 'base', self._global_options)
        else:
            self.error('Invalid option name.')

    def _do_goptions_unset(self, params):
        '''Unsets a global context option'''
        option, value = self._parse_params(params)
        if not option:
            self._help_goptions_unset()
            return
        name = option.upper()
        if name in self._global_options:
            self._do_goptions_set(' '.join([name, 'None']))
        else:
            self.error('Invalid option name.')

    def _do_modules_load(self, params):
        '''Loads a module'''
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
        # compensation for stdin being used for scripting and loading
        if framework.Framework._script:
            end_string = sys.stdin.read()
        else:
            end_string = 'EOF'
            framework.Framework._load = 1
        sys.stdin = io.StringIO(f"modules load {modules[0]}{os.linesep}{end_string}")
        return True

    def do_reload(self, params):
        '''Reloads the loaded module'''
        self._reload = 1
        return True

    def do_info(self, params):
        '''Shows details about the loaded module'''
        print('')
        # meta info
        for item in ['name', 'author', 'version']:
            print(f"{item.title().rjust(10)}: {self.meta[item]}")
        # required keys
        if self.meta.get('required_keys'):
            print(f"{'keys'.title().rjust(10)}: {', '.join(self.meta.get('required_keys'))}")
        print('')
        # description
        print('Description:')
        print(f"{self.spacer}{textwrap.fill(self.meta['description'], 100, subsequent_indent=self.spacer)}")
        print('')
        # options
        print('Options:', end='')
        self._list_options()
        # sources
        if hasattr(self, '_default_source'):
            print('Source Options:')
            print(f"{self.spacer}{'default'.ljust(15)}{self._default_source}")
            print(f"{self.spacer}{'<string>'.ljust(15)}string representing a single input")
            print(f"{self.spacer}{'<path>'.ljust(15)}path to a file containing a list of inputs")
            print(f"{self.spacer}{'query <sql>'.ljust(15)}database query returning one column of inputs")
            print('')
        # comments
        if self.meta.get('comments'):
            print('Comments:')
            for comment in self.meta['comments']:
                prefix = '* '
                if comment.startswith('\t'):
                    prefix = self.spacer+'- '
                    comment = comment[1:]
                print(f"{self.spacer}{textwrap.fill(prefix+comment, 100, subsequent_indent=self.spacer)}")
            print('')

    def do_input(self, params):
        '''Shows inputs based on the source option'''
        if hasattr(self, '_default_source'):
            try:
                self._validate_options()
                inputs = self._get_source(self.options['source'], self._default_source)
                self.table([[x] for x in inputs], header=['Module Inputs'])
            except Exception as e:
                self.output(e.__str__())
        else:
            self.output('Source option not available for this module.')

    def run(self):
        self._validate_options()
        self._validate_input()
        self._summary_counts = {}
        pre = self.module_pre()
        params = [pre] if pre is not None else []
        # provide input if a default query is specified in the module
        if hasattr(self, '_default_source'):
            objs = self._get_source(self.options['source'], self._default_source)
            params.insert(0, objs)
        # update the dashboard before running the module
        # data is added at runtime, so even if an error occurs, any new items
        # must be accounted for by a module execution attempt
        self.query(f"INSERT OR REPLACE INTO dashboard (module, runs) VALUES ('{self._modulename}', COALESCE((SELECT runs FROM dashboard WHERE module='{self._modulename}')+1, 1))")
        self.module_run(*params)
        self.module_post()

    def do_run(self, params):
        '''Runs the loaded module'''
        try:
            self.run()
        except KeyboardInterrupt:
            print('')
        except (Timeout, socket.timeout):
            self.print_exception()
            self.error('A request took too long to complete. If the issue persists, increase the global TIMEOUT option.')
        except (framework.FrameworkException, validators.ValidationException):
            self.print_exception()
        except Exception:
            self.print_exception()
            self.error('Something broken? See https://github.com/lanmaster53/recon-ng/wiki/Troubleshooting#issue-reporting.')
        finally:
            # print module summary
            if self._summary_counts:
                self.heading('Summary', level=0)
                for table in self._summary_counts:
                    new = self._summary_counts[table]['new']
                    cnt = self._summary_counts[table]['count']
                    if new > 0:
                        method = getattr(self, 'alert')
                    else:
                        method = getattr(self, 'output')
                    method(f"{cnt} total ({new} new) {table} found.")

    #==================================================
    # HELP METHODS
    #==================================================

    def help_goptions(self):
        print(getattr(self, 'do_goptions').__doc__)
        print(f"{os.linesep}Usage: goptions <{'|'.join(self._parse_subcommands('goptions'))}> [...]{os.linesep}")

    def _help_goptions_set(self):
        print(getattr(self, '_do_goptions_set').__doc__)
        print(f"{os.linesep}Usage: goptions set <option> <value>{os.linesep}")

    def _help_goptions_unset(self):
        print(getattr(self, '_do_goptions_unset').__doc__)
        print(f"{os.linesep}Usage: goptions unset <option>{os.linesep}")

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_goptions(self, text, line, *ignored):
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._parse_subcommands('goptions')
        if arg in subs:
            return getattr(self, '_complete_goptions_'+arg)(text, params)
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_goptions_list(self, text, *ignored):
        return []

    def _complete_goptions_set(self, text, *ignored):
        return [x for x in self._global_options if x.startswith(text.upper())]
    _complete_goptions_unset = _complete_goptions_set

    def complete_reload(self, text, *ignored):
        return []
    complete_info = complete_input = complete_run = complete_reload

    #==================================================
    # HOOK METHODS
    #==================================================

    def module_pre(self):
        pass

    def module_run(self):
        pass

    def module_post(self):
        pass
