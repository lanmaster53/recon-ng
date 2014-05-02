from __future__ import print_function
import cmd
import json
import os
import random
import re
import socket
import sqlite3
import string
import subprocess
import sys
# prep python path for supporting modules
sys.path.append('./libs/')
import dragons
import mechanize

#=================================================
# SUPPORT CLASSES
#=================================================

class FrameworkException(Exception):
    pass

class Colors(object):
    N = '\033[m' # native
    R = '\033[31m' # red
    G = '\033[32m' # green
    O = '\033[33m' # orange
    B = '\033[34m' # blue

class Options(dict):

    def __init__(self, *args, **kwargs):
        self.required = {}
        self.description = {}
        
        super(Options, self).__init__(*args, **kwargs)
           
    def __setitem__(self, name, value):
        super(Options, self).__setitem__(name, self._autoconvert(value))
           
    def __delitem__(self, name):
        super(Options, self).__delitem__(name)
        if name in self.required:
            del self.required[name]
        if name in self.description:
            del self.description[name]
        
    def _boolify(self, value):
        # designed to throw an exception if value is not a string representation of a boolean
        return {'true':True, 'false':False}[value.lower()]

    def _autoconvert(self, value):
        if value in (None, True, False):
            return value
        elif (isinstance(value, basestring)) and value.lower() in ('none', "''", '""'):
            return None
        orig = value
        for fn in (self._boolify, int, float):
            try:
                value = fn(value)
                break
            except ValueError: pass
            except KeyError: pass
            except AttributeError: pass
        if type(value) is int and '.' in str(orig):
            return float(orig)
        return value
        
    def init_option(self, name, value=None, required=False, description=''):
        self[name] = value
        self.required[name] = required
        self.description[name] = description

    def serialize(self):
        data = {}
        for key in self:
            data[key] = self[key]
        return data

#=================================================
# FRAMEWORK CLASS
#=================================================

class Framework(cmd.Cmd):
    # mode flags
    script = 0
    load = 0
    # framework variables
    global_options = Options()
    keys = {}
    loaded_modules = {}
    workspace = ''
    home = ''
    record = None
    spool = None

    def __init__(self, params):
        cmd.Cmd.__init__(self)
        self.prompt = (params[0])
        self.modulename = params[1]
        self.ruler = '-'
        self.spacer = '  '
        self.nohelp = '%s[!] No help on %%s%s' % (Colors.R, Colors.N)
        self.do_help.__func__.__doc__ = '''Displays this menu'''
        self.doc_header = 'Commands (type [help|?] <topic>):'
        self.rpc_cache = []

    #==================================================
    # CMD OVERRIDE METHODS
    #==================================================

    def default(self, line):
        self.do_shell(line)

    def emptyline(self):
        # disables running of last command when no command is given
        # return flag to tell interpreter to continue
        return 0

    def precmd(self, line):
        if Framework.load:
            print('\r', end='')
        if Framework.script:
            print('%s' % (line))
        if Framework.record:
            recorder = open(Framework.record, 'ab')
            recorder.write(('%s\n' % (line)).encode('utf-8'))
            recorder.flush()
            recorder.close()
        if Framework.spool:
            Framework.spool.write('%s%s\n' % (self.prompt, line))
            Framework.spool.flush()
        return line

    def onecmd(self, line):
        cmd, arg, line = self.parseline(line)
        if not line:
            return self.emptyline()
        if line == 'EOF':
            # reset stdin for raw_input
            sys.stdin = sys.__stdin__
            Framework.script = 0
            Framework.load = 0
            return 0
        if cmd is None:
            return self.default(line)
        self.lastcmd = line
        if cmd == '':
            return self.default(line)
        else:
            try:
                func = getattr(self, 'do_' + cmd)
            except AttributeError:
                return self.default(line)
            return func(arg)

    # make help menu more attractive
    def print_topics(self, header, cmds, cmdlen, maxcol):
        if cmds:
            self.stdout.write("%s\n"%str(header))
            if self.ruler:
                self.stdout.write("%s\n"%str(self.ruler * len(header)))
            for cmd in cmds:
                self.stdout.write("%s %s\n" % (cmd.ljust(15), getattr(self, 'do_' + cmd).__doc__))
            self.stdout.write("\n")

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def to_unicode_str(self, obj, encoding='utf-8'):
        # checks if obj is a string and converts if not
        if not isinstance(obj, basestring):
            obj = str(obj)
        obj = self.to_unicode(obj, encoding)
        return obj

    def to_unicode(self, obj, encoding='utf-8'):
        # checks if obj is a unicode string and converts if not
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding)
        return obj

    def is_writeable(self, filename):
        try:
            fp = open(filename, 'ab')
            fp.close()
            return True
        except IOError:
            return False

    def random_str(self, length):
        return ''.join(random.choice(string.lowercase) for i in range(length))

    #==================================================
    # OUTPUT METHODS
    #==================================================

    def error(self, line):
        '''Formats and presents errors.'''
        if not re.search('[.,;!?]$', line):
            line += '.'
        line = line[:1].upper() + line[1:]
        print('%s[!] %s%s' % (Colors.R, self.to_unicode(line), Colors.N))

    def output(self, line):
        '''Formats and presents normal output.'''
        print('%s[*]%s %s' % (Colors.B, Colors.N, self.to_unicode(line)))

    def alert(self, line):
        '''Formats and presents important output.'''
        print('%s[*]%s %s' % (Colors.G, Colors.N, self.to_unicode(line)))

    def verbose(self, line):
        '''Formats and presents output if in verbose mode.'''
        if self.global_options['verbose']:
            self.output(line)

    def heading(self, line, level=1):
        '''Formats and presents styled header text'''
        line = self.to_unicode(line)
        print('')
        if level == 0:
            print(self.ruler*len(line))
            print(line.upper())
            print(self.ruler*len(line))
        if level == 1:
            print('%s%s' % (self.spacer, line.title()))
            print('%s%s' % (self.spacer, self.ruler*len(line)))

    def table(self, data, header=[], title='', store=False):
        '''Accepts a list of rows and outputs a table.'''
        tdata = list(data)
        if header:
            tdata.insert(0, header)
        if len(set([len(x) for x in tdata])) > 1:
            raise FrameworkException('Row lengths not consistent.')
        lens = []
        cols = len(tdata[0])
        # create a list of max widths for each column
        for i in range(0,cols):
            lens.append(len(max([self.to_unicode_str(x[i]) if x[i] != None else '' for x in tdata], key=len)))
        # calculate dynamic widths based on the title
        title_len = len(title)
        tdata_len = sum(lens) + (3*(cols-1))
        diff = title_len - tdata_len
        if diff > 0:
            diff_per = diff / cols
            lens = [x+diff_per for x in lens]
            diff_mod = diff % cols
            for x in range(0, diff_mod):
                lens[x] += 1
        # build ascii table
        if len(tdata) > 0:
            separator_str = '%s+-%s%%s-+' % (self.spacer, '%s---'*(cols-1))
            separator_sub = tuple(['-'*x for x in lens])
            separator = separator_str % separator_sub
            data_str = '%s| %s%%s |' % (self.spacer, '%s | '*(cols-1))
            # top of ascii table
            print('')
            print(separator)
            # ascii table data
            if title:
                print('%s| %s |' % (self.spacer, title.center(tdata_len)))
                print(separator)
            if header:
                rdata = tdata.pop(0)
                data_sub = tuple([rdata[i].center(lens[i]) for i in range(0,cols)])
                print(data_str % data_sub)
                print(separator)
            for rdata in tdata:
                data_sub = tuple([self.to_unicode_str(rdata[i]).ljust(lens[i]) if rdata[i] != None else ''.ljust(lens[i]) for i in range(0,cols)])
                print(data_str % data_sub)
            # bottom of ascii table
            print(separator)
            print('')
        if store:
            # store the table
            table = title if title else self.modulename.split('/')[-1]
            self.add_table(table, data, header)

    def add_table(self, *args, **kwargs):
        raise NotImplementedError('Method reserved for subclasses.')

    #==================================================
    # DATABASE METHODS
    #==================================================

    def query(self, query, values=()):
        '''Queries the database and returns the results as a list.'''
        if self.global_options['debug']: self.output(query)
        conn = sqlite3.connect('%s/data.db' % (self.workspace))
        cur = conn.cursor()
        if values:
            if self.global_options['debug']: self.output(repr(values))
            cur.execute(query, values)
        else:
            cur.execute(query)
        # a rowcount of -1 typically refers to a select statement
        if cur.rowcount == -1:
            rows = cur.fetchall()
            results = rows
        # a rowcount of 1 == success and 0 == failure
        else:
            conn.commit()
            results = cur.rowcount
        conn.close()
        return results

    def get_columns(self, table):
        return [(x[1],x[2]) for x in self.query('PRAGMA table_info(\'%s\')' % (table))]

    def get_tables(self):
        return [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'') if x[0] not in ['dashboard']]

    #==================================================
    # ADD METHODS
    #==================================================

    def add_domains(self, domain):
        '''Adds a domain to the database and returns the affected row count.'''
        data = dict(
            domain = self.to_unicode(domain)
        )
        return self.insert('domains', data, (data.keys()))

    def add_companies(self, company, description=None):
        '''Adds a company to the database and returns the affected row count.'''
        data = dict(
            company = self.to_unicode(company),
            description = self.to_unicode(description)
        )
        return self.insert('companies', data, ('company'))

    def add_netblocks(self, netblock):
        '''Adds a netblock to the database and returns the affected row count.'''
        data = dict(
            netblock = self.to_unicode(netblock)
        )
        return self.insert('netblocks', data, (data.keys()))

    def add_locations(self, latitude, longitude):
        '''Adds a location to the database and returns the affected row count.'''
        data = dict(
            latitude = self.to_unicode(latitude),
            longitude = self.to_unicode(longitude)
        )
        return self.insert('locations', data, (data.keys()))

    def add_hosts(self, host, ip_address=None, region=None, country=None, latitude=None, longitude=None):
        '''Adds a host to the database and returns the affected row count.'''
        data = dict(
            host = self.to_unicode(host),
            ip_address = self.to_unicode(ip_address),
            region = self.to_unicode(region),
            country = self.to_unicode(country),
            latitude = self.to_unicode(latitude),
            longitude = self.to_unicode(longitude),
        )
        return self.insert('hosts', data, ('host', 'ip_address'))

    def add_contacts(self, first_name, last_name, title, middle_name=None, email=None, region=None, country=None):
        '''Adds a contact to the database and returns the affected row count.'''
        data = dict(
            first_name = self.to_unicode(first_name),
            middle_name = self.to_unicode(middle_name),
            last_name = self.to_unicode(last_name),
            title = self.to_unicode(title),
            email = self.to_unicode(email),
            region = self.to_unicode(region),
            country = self.to_unicode(country),
        )
        return self.insert('contacts', data, ('first_name', 'middle_name', 'last_name', 'title', 'email'))

    def add_creds(self, username, password=None, hashtype=None, leak=None):
        '''Adds a credential to the database and returns the affected row count.'''
        data = {}
        data['username'] = self.to_unicode(username)
        if password and not self.is_hash(password): data['password'] = self.to_unicode(password)
        if password and self.is_hash(password): data['hash'] = self.to_unicode(password)
        if hashtype: data['type'] = self.to_unicode(hashtype)
        if leak: data['leak'] = self.to_unicode(leak)
        return self.insert('creds', data, data.keys())

    def add_leaks(self, leak_id, description, source_refs, leak_type, title, import_date, leak_date, attackers, num_entries, score, num_domains_affected, attack_method, target_industries, password_hash, targets, media_refs):
        '''Adds a leak to the database and returns the affected row count.'''
        data = dict(
            leak_id = self.to_unicode(leak_id),
            description = self.to_unicode(description),
            source_refs = self.to_unicode(source_refs),
            leak_type = self.to_unicode(leak_type),
            title = self.to_unicode(title),
            import_date = self.to_unicode(import_date),
            leak_date = self.to_unicode(leak_date),
            attackers = self.to_unicode(attackers),
            num_entries = self.to_unicode(num_entries),
            score = self.to_unicode(score),
            num_domains_affected = self.to_unicode(num_domains_affected),
            attack_method = self.to_unicode(attack_method),
            target_industries = self.to_unicode(target_industries),
            password_hash = self.to_unicode(password_hash),
            targets = self.to_unicode(targets),
            media_refs = self.to_unicode(media_refs)
        )
        return self.insert('leaks', data, data.keys())

    def add_pushpins(self, source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time):
        '''Adds a pushpin to the database and returns the affected row count.'''
        data = dict(
            source = self.to_unicode(source),
            screen_name = self.to_unicode(screen_name),
            profile_name = self.to_unicode(profile_name),
            profile_url = self.to_unicode(profile_url),
            media_url = self.to_unicode(media_url),
            thumb_url = self.to_unicode(thumb_url),
            message = self.to_unicode(message),
            latitude = self.to_unicode(latitude),
            longitude = self.to_unicode(longitude),
            time = self.to_unicode(time),
        )
        return self.insert('pushpins', data, data.keys())

    def insert(self, table, data, unique_columns=[]):
        '''Inserts items into database and returns the affected row count.
        table - the table to insert the data into
        data - the information to insert into the database table in the form of a dictionary
               where the keys are the column names and the values are the column values
        unique_columns - a list of column names that should be used to determine if the.
                         information being inserted is unique'''

        # sanitize the inputs to remove NoneTypes, blank strings, and zeros
        columns = [x for x in data.keys() if data[x]]
        unique_columns = [x for x in unique_columns if x in columns]
        # exit if there is nothing left to insert
        if not columns: return 0

        if not unique_columns:
            query = u'INSERT INTO "%s" ("%s") VALUES (%s)' % (
                table,
                '", "'.join(columns),
                ', '.join('?'*len(columns))
            )
        else:
            query = u'INSERT INTO "%s" ("%s") SELECT %s WHERE NOT EXISTS(SELECT * FROM "%s" WHERE %s)' % (
                table,
                '", "'.join(columns),
                ', '.join('?'*len(columns)),
                table,
                ' and '.join(['"%s"=?' % (column) for column in unique_columns])
            )

        values = tuple([data[column] for column in columns] + [data[column] for column in unique_columns])

        rowcount = self.query(query, values)

        # build RPC response
        for key in data.keys():
            if not data[key]:
                del data[key]
        self.rpc_cache.append(data)

        return rowcount

    #==================================================
    # OPTIONS METHODS
    #==================================================

    def register_option(self, name, value, reqd, desc):
        self.options.init_option(name=name.lower(), value=value, required=reqd, description=desc)
        # needs to be optimized rather than ran on every register
        self.load_config()

    def validate_options(self):
        for option in self.options:
            # if value type is bool or int, then we know the options is set
            if not type(self.options[option]) in [bool, int]:
                if self.options.required[option].lower() == 'yes' and not self.options[option]:
                    raise FrameworkException('Value required for the \'%s\' option.' % (option))
        return

    def load_config(self):
        config_path = '%s/config.dat' % (self.workspace)
        # don't bother loading if a config file doesn't exist
        if os.path.exists(config_path):
            # retrieve saved config data
            config_file = open(config_path, 'rb')
            try:
                config_data = json.loads(config_file.read())
            except ValueError:
                # file is corrupt, nothing to load, exit gracefully
                pass
            else:
                # set option values
                for key in self.options:
                    try:
                        self.options[key] = config_data[self.modulename][key]
                    except KeyError:
                        # invalid key, contnue to load valid keys
                        continue
            finally:
                config_file.close()

    def save_config(self, name):
        config_path = '%s/config.dat' % (self.workspace)
        # create a config file if one doesn't exist
        open(config_path, 'ab').close()
        # retrieve saved config data
        config_file = open(config_path, 'rb')
        try:
            config_data = json.loads(config_file.read())
        except ValueError:
            # file is empty or corrupt, nothing to load
            config_data = {}
        config_file.close()
        # create a container for the current module
        if self.modulename not in config_data:
            config_data[self.modulename] = {}
        # set the new option value in the config
        config_data[self.modulename][name] = self.options[name]
        # remove the option if it has been unset
        if config_data[self.modulename][name] is None:
            del config_data[self.modulename][name]
        # remove the module container if it is empty
        if not config_data[self.modulename]:
            del config_data[self.modulename]
        # write the new config data to the config file
        config_file = open(config_path, 'wb')
        json.dump(config_data, config_file, indent=4)
        config_file.close()

    #==================================================
    # API KEY METHODS
    #==================================================

    def list_keys(self):
        tdata = []
        for key in sorted(self.keys):
            tdata.append([key, self.keys[key]])
        if tdata:
            self.table(tdata, header=['Name', 'Value'])
        else: self.output('No API keys stored.')

    def save_keys(self):
        key_path = '%s/keys.dat' % (self.home)
        key_file = open(key_path, 'wb')
        json.dump(self.keys, key_file)
        key_file.close()

    def get_key(self, name):
        try:
            return self.keys[name]
        except KeyError:
            raise FrameworkException('API key \'%s\' not found. Add API keys with the \'keys add\' command.' % (name))

    def add_key(self, name, value):
        self.keys[name] = value
        self.save_keys()

    def delete_key(self, name):
        try:
            del self.keys[name]
        except KeyError:
            raise FrameworkException('API key \'%s\' not found.' % (name))
        else:
            self.save_keys()

    #==================================================
    # REQUEST METHODS
    #==================================================

    def request(self, url, method='GET', timeout=None, payload=None, headers=None, cookiejar=None, auth=None, content='', redirect=True):
        request = dragons.Request()
        request.user_agent = self.global_options['user-agent']
        request.debug = self.global_options['debug']
        request.proxy = self.global_options['proxy']
        request.timeout = timeout or self.global_options['timeout']
        request.redirect = redirect
        return request.send(url, method=method, payload=payload, headers=headers, cookiejar=cookiejar, auth=auth, content=content)

    def browser(self):
        '''Returns a mechanize.Browser object configured with the framework's global options.'''
        br = mechanize.Browser()
        # set the user-agent header
        br.addheaders = [('User-agent', self.global_options['user-agent'])]
        # set debug options
        if self.global_options['debug']:
            br.set_debug_http(True)
            br.set_debug_redirects(True)
            br.set_debug_responses(True)
        # set proxy
        if self.global_options['proxy']:
            br.set_proxies({'http': self.global_options['proxy'], 'https': self.global_options['proxy']})
        # additional settings
        br.set_handle_robots(False)
        # set timeout
        socket.setdefaulttimeout(self.global_options['timeout'])
        return br

    #==================================================
    # SHOW METHODS
    #==================================================

    def get_show_names(self):
        # Any method beginning with "show_" will be parsed
        # and added as a subcommand for the show command.
        prefix = 'show_'
        return [x[len(prefix):] for x in self.get_names() if x.startswith(prefix)]

    def show_modules(self, param):
        # process parameter according to type
        if type(param) is list:
            modules = param
        elif param:
            modules = [x for x in Framework.loaded_modules if x.startswith(param)]
            if not modules:
                self.error('Invalid module category.')
                return
        else:
            modules = Framework.loaded_modules
        # display the modules
        key_len = len(max(modules, key=len)) + len(self.spacer)
        last_category = ''
        for module in sorted(modules):
            category = module.split('/')[0]
            if category != last_category:
                # print header
                last_category = category
                self.heading(last_category)
            # print module
            print('%s%s' % (self.spacer*2, module))
        print('')

    def show_workspaces(self):
        dirnames = []
        path = '%s/workspaces' % (self.home)
        for name in os.listdir(path):
            if os.path.isdir('%s/%s' % (path, name)):
                dirnames.append([name])
        self.table(dirnames, header=['Workspaces'])

    def show_dashboard(self):
        rows = self.query('SELECT * FROM dashboard ORDER BY 1')
        if rows:
            # display activity table
            tdata = []
            for row in rows:
                tdata.append(row)
            self.table(tdata, header=['Module', 'Runs'], title='Activity Summary')
            # display summary results table
            tables = self.get_tables()
            tdata = []
            for table in tables:
                count = self.query('SELECT COUNT(*) FROM "%s"' % (table))[0][0]
                tdata.append([table.title(), count])
            self.table(tdata, header=['Category', 'Quantity'], title='Results Summary')
        else:
            print('\n%sThis workspace has no record of activity.\n' % (self.spacer))

    def show_schema(self):
        '''Displays the database schema'''
        tables = self.get_tables()
        for table in tables:
            columns = self.get_columns(table)
            self.table(columns, title=table)

    def show_options(self, options=None):
        '''Lists options'''
        if options is None:
            options = self.options
        if options:
            pattern = '%s%%s  %%s  %%s  %%s' % (self.spacer)
            key_len = len(max(options, key=len))
            if key_len < 4: key_len = 4
            val_len = len(max([self.to_unicode_str(options[x]) for x in options], key=len))
            if val_len < 13: val_len = 13
            print('')
            print(pattern % ('Name'.ljust(key_len), 'Current Value'.ljust(val_len), 'Req', 'Description'))
            print(pattern % (self.ruler*key_len, (self.ruler*13).ljust(val_len), self.ruler*3, self.ruler*11))
            for key in sorted(options):
                value = options[key] if options[key] != None else ''
                reqd = options.required[key]
                desc = options.description[key]
                print(pattern % (key.upper().ljust(key_len), self.to_unicode_str(value).ljust(val_len), reqd.ljust(3), desc))
            print('')
        else:
            print('')
            print('%sNo options available for this module.' % (self.spacer))
            print('')

    #==================================================
    # COMMAND METHODS
    #==================================================

    def do_exit(self, params):
        '''Exits current prompt level'''
        return True

    # alias for exit
    def do_back(self, params):
        '''Exits current prompt level'''
        return True

    def do_set(self, params):
        '''Sets module options'''
        options = params.split()
        if len(options) < 2:
            self.help_set()
            return
        name = options[0].lower()
        if name in self.options:
            value = ' '.join(options[1:])
            self.options[name] = value
            print('%s => %s' % (name.upper(), value))
            self.save_config(name)
        else: self.error('Invalid option.')

    def do_unset(self, params):
        '''Unsets module options'''
        self.do_set('%s %s' % (params, 'None'))

    def do_keys(self, params):
        '''Manages framework API keys'''
        if not params:
            self.help_keys()
            return
        params = params.split()
        arg = params.pop(0).lower()
        if arg == 'list':
            self.list_keys()
        elif arg in ['add', 'update']:
            if len(params) == 2:
                self.add_key(params[0], params[1])
                self.output('Key \'%s\' added.' % (params[0]))
            else: print('Usage: keys [add|update] <name> <value>')
        elif arg == 'delete':
            if len(params) == 1:
                try:
                    self.delete_key(params[0])
                except FrameworkException as e:
                    self.error(e.__str__())
                else:
                    self.output('Key \'%s\' deleted.' % (params[0]))
            else: print('Usage: keys delete <name>')
        else:
            self.help_keys()

    def do_query(self, params):
        '''Queries the database'''
        if not params:
            self.help_query()
            return
        conn = sqlite3.connect('%s/data.db' % (self.workspace))
        cur = conn.cursor()
        if self.global_options['debug']: self.output(params)
        try: cur.execute(params)
        except sqlite3.OperationalError as e:
            self.error('Invalid query. %s %s' % (type(e).__name__, e.message))
            return
        if cur.rowcount == -1 and cur.description:
            tdata = cur.fetchall()
            if not tdata:
                self.output('No data returned.')
            else:
                header = tuple([x[0] for x in cur.description])
                self.table(tdata, header=header)
                self.output('%d rows returned' % (len(tdata)))
        else:
            conn.commit()
            self.output('%d rows affected.' % (cur.rowcount))
        conn.close()

    def do_show(self, params):
        '''Shows various framework items'''
        if not params:
            self.help_show()
            return
        _params = params
        params = params.lower().split()
        arg = params[0]
        params = ' '.join(params[1:])
        if arg in self.get_show_names():
            func = getattr(self, 'show_' + arg)
            if arg == 'modules':
                func(params)
            else:
                func()
        elif _params in self.get_tables():
            self.do_query('SELECT ROWID, * FROM "%s" ORDER BY 2' % (_params))
        else:
            self.help_show()

    def do_add(self, params):
        '''Adds items to the database'''
        # get table names for which data can be added
        tables = self.get_tables()
        if params in tables:
            columns = self.get_columns(params)
            item = {}
            # prompt user for data
            for column in columns:
                try:
                    item[column[0]] = raw_input('%s (%s): ' % column)
                except KeyboardInterrupt:
                    print('')
                    return
            # add the item to the database
            func = getattr(self, 'add_' + params)
            func(**item)
        else:
            self.help_add()

    def do_del(self, params):
        '''Deletes items from the database'''
        # get table names for which data can be deleted
        tables = self.get_tables()
        if params in tables:
            try:
                rowid = raw_input('rowid (INT): ')
            except KeyboardInterrupt:
                print('')
                return
            # delete the item from the database
            self.query('DELETE FROM %s WHERE ROWID IS ?' % (params), (rowid,))
        else:
            self.help_del()

    def do_search(self, params):
        '''Searches available modules'''
        if not params:
            self.help_search()
            return
        text = params.split()[0]
        self.output('Searching for \'%s\'...' % (text))
        modules = [x for x in Framework.loaded_modules if text in x]
        if not modules:
            self.error('No modules found containing \'%s\'.' % (text))
        else:
            self.show_modules(modules)

    def do_record(self, params):
        '''Records commands to a resource file'''
        if not params:
            self.help_record()
            return
        arg = params.lower()
        if arg.split()[0] == 'start':
            if not Framework.record:
                if len(arg.split()) > 1:
                    filename = ' '.join(arg.split()[1:])
                    if not self.is_writeable(filename):
                        self.output('Cannot record commands to \'%s\'.' % (filename))
                    else:
                        Framework.record = filename
                        self.output('Recording commands to \'%s\'.' % (Framework.record))
                else: self.help_record()
            else: self.output('Recording is already started.')
        elif arg == 'stop':
            if Framework.record:
                self.output('Recording stopped. Commands saved to \'%s\'.' % (Framework.record))
                Framework.record = None
            else: self.output('Recording is already stopped.')
        elif arg == 'status':
            status = 'started' if Framework.record else 'stopped'
            self.output('Command recording is %s.' % (status))
        else:
            self.help_record()

    def do_spool(self, params):
        '''Spools output to a file'''
        if not params:
            self.help_spool()
            return
        arg = params.lower()
        if arg.split()[0] == 'start':
            if not Framework.spool:
                if len(arg.split()) > 1:
                    filename = ' '.join(arg.split()[1:])
                    if not self.is_writeable(filename):
                        self.output('Cannot spool output to \'%s\'.' % (filename))
                    else:
                        Framework.spool = open(filename, 'ab')
                        self.output('Spooling output to \'%s\'.' % (Framework.spool.name))
                else: self.help_spool()
            else: self.output('Spooling is already started.')
        elif arg == 'stop':
            if Framework.spool:
                self.output('Spooling stopped. Output saved to \'%s\'.' % (Framework.spool.name))
                Framework.spool = None
            else: self.output('Spooling is already stopped.')
        elif arg == 'status':
            status = 'started' if Framework.spool else 'stopped'
            self.output('Output spooling is %s.' % (status))
        else:
            self.help_spool()

    def do_shell(self, params):
        '''Executes shell commands'''
        proc = subprocess.Popen(params, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        self.output('Command: %s' % (params))
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        if stdout: print('%s%s%s' % (Colors.O, stdout, Colors.N), end='')
        if stderr: print('%s%s%s' % (Colors.R, stderr, Colors.N), end='')

    def do_resource(self, params):
        '''Executes commands from a resource file'''
        if not params:
            self.help_resource()
            return
        if os.path.exists(params):
            sys.stdin = open(params)
            Framework.script = 1
        else:
            self.error('Script file \'%s\' not found.' % (params))

    def do_load(self, params):
        '''Loads selected module'''
        if not params:
            self.help_load()
            return
        # finds any modules that contain params
        modules = [params] if params in Framework.loaded_modules else [x for x in Framework.loaded_modules if params in x]
        # notify the user if none or multiple modules are found
        if len(modules) != 1:
            if not modules:
                self.error('Invalid module name.')
            else:
                self.output('Multiple modules match \'%s\'.' % params)
                self.show_modules(modules)
            return
        import StringIO
        # compensation for stdin being used for scripting and loading
        if Framework.script:
            end_string = sys.stdin.read()
        else:
            end_string = 'EOF'
            Framework.load = 1
        sys.stdin = StringIO.StringIO('load %s\n%s' % (modules[0], end_string))
        return True
    do_use = do_load

    def do_pdb(self, params):
        '''Starts a Python Debugger session'''
        import pdb
        pdb.set_trace()

    #==================================================
    # HELP METHODS
    #==================================================

    def help_keys(self):
        print(getattr(self, 'do_keys').__doc__)
        print('')
        print('Usage: keys [list|add|delete|update]')
        print('')

    def help_load(self):
        print(getattr(self, 'do_load').__doc__)
        print('')
        print('Usage: [load|use] <module>')
        print('')
    help_use = help_load

    def help_record(self):
        print(getattr(self, 'do_record').__doc__)
        print('')
        print('Usage: record [start <filename>|stop|status]')
        print('')

    def help_spool(self):
        print(getattr(self, 'do_spool').__doc__)
        print('')
        print('Usage: spool [start <filename>|stop|status]')
        print('')

    def help_resource(self):
        print(getattr(self, 'do_resource').__doc__)
        print('')
        print('Usage: resource <filename>')
        print('')

    def help_query(self):
        print(getattr(self, 'do_query').__doc__)
        print('')
        print('Usage: query <sql>')
        print('')
        print('SQL Examples:')
        print('%s%s' % (self.spacer, 'SELECT columns|* FROM table_name'))
        print('%s%s' % (self.spacer, 'SELECT columns|* FROM table_name WHERE some_column=some_value'))
        print('%s%s' % (self.spacer, 'DELETE FROM table_name WHERE some_column=some_value'))
        print('%s%s' % (self.spacer, 'INSERT INTO table_name (column1, column2,...) VALUES (value1, value2,...)'))
        print('%s%s' % (self.spacer, 'UPDATE table_name SET column1=value1, column2=value2,... WHERE some_column=some_value'))
        print('')

    def help_search(self):
        print(getattr(self, 'do_search').__doc__)
        print('')
        print('Usage: search <string>')
        print('')

    def help_set(self):
        print(getattr(self, 'do_set').__doc__)
        print('')
        print('Usage: set <option> <value>')
        self.show_options()

    def help_unset(self):
        print(getattr(self, 'do_unset').__doc__)
        print('')
        print('Usage: unset <option>')
        self.show_options()

    def help_shell(self):
        print(getattr(self, 'do_shell').__doc__)
        print('')
        print('Usage: [shell|!] <command>')
        print('...or just type a command at the prompt.')
        print('')

    def help_show(self):
        options = sorted(self.get_show_names() + self.get_tables())
        print(getattr(self, 'do_show').__doc__)
        print('')
        print('Usage: show [%s]' % ('|'.join(options)))
        print('')

    def help_add(self):
        options = sorted(self.get_tables())
        print(getattr(self, 'do_add').__doc__)
        print('')
        print('Usage: add [%s]' % ('|'.join(options)))
        print('')

    def help_del(self):
        options = sorted(self.get_tables())
        print(getattr(self, 'do_del').__doc__)
        print('')
        print('Usage: del [%s]' % ('|'.join(options)))
        print('')

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_keys(self, text, line, *ignored):
        args = line.split()
        options = ['list', 'add', 'delete', 'update']
        if len(args) > 1:
            if args[1].lower() in options[2:]:
                return [x for x in self.keys.keys() if x.startswith(text)]
            if args[1].lower() in options[:2]:
                return
        return [x for x in options if x.startswith(text)]

    def complete_load(self, text, *ignored):
        return [x for x in Framework.loaded_modules if x.startswith(text)]
    complete_use = complete_load

    def complete_record(self, text, *ignored):
        return [x for x in ['start', 'stop', 'status'] if x.startswith(text)]
    complete_spool = complete_record

    def complete_set(self, text, *ignored):
        return [x.upper() for x in self.options if x.upper().startswith(text.upper())]
    complete_unset = complete_set

    def complete_show(self, text, line, *ignored):
        args = line.split()
        if len(args) > 1 and args[1].lower() == 'modules':
            if len(args) > 2: return [x for x in Framework.loaded_modules if x.startswith(args[2])]
            else: return [x for x in Framework.loaded_modules]
        options = sorted(self.get_show_names() + self.get_tables())
        return [x for x in options if x.startswith(text)]

    def complete_add(self, text, *ignored):
        tables = sorted(self.get_tables())
        return [x for x in tables if x.startswith(text)]
    complete_del = complete_add
