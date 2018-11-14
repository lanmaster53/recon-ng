from __future__ import print_function
from contextlib import closing
import cmd
import codecs
import inspect
import json
import os
import random
import re
import socket
import sqlite3
import string
import subprocess
import sys
import traceback
# framework libs
from recon.utils.requests import Request

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
    prompt = '>>>'
    # mode flags
    _script = 0
    _load = 0
    # framework variables
    _global_options = Options()
    _loaded_modules = {}
    app_path = ''
    data_path = ''
    core_path = ''
    workspace = ''
    _home = ''
    _record = None
    _spool = None
    _summary_counts = {}

    def __init__(self, params):
        cmd.Cmd.__init__(self)
        self._modulename = params
        self.ruler = '-'
        self.spacer = '  '
        self.time_format = '%Y-%m-%d %H:%M:%S'
        self.nohelp = '%s[!] No help on %%s%s' % (Colors.R, Colors.N)
        self.do_help.__func__.__doc__ = '''Displays this menu'''
        self.doc_header = 'Commands (type [help|?] <topic>):'
        self.rpc_cache = []
        self._exit = 0

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
        if Framework._load:
            print('\r', end='')
        if Framework._script:
            print('%s' % (line))
        if Framework._record:
            recorder = codecs.open(Framework._record, 'ab', encoding='utf-8')
            recorder.write(('%s\n' % (line)).encode('utf-8'))
            recorder.flush()
            recorder.close()
        if Framework._spool:
            Framework._spool.write('%s%s\n' % (self.prompt, line))
            Framework._spool.flush()
        return line

    def onecmd(self, line):
        cmd, arg, line = self.parseline(line)
        if not line:
            return self.emptyline()
        if line == 'EOF':
            # reset stdin for raw_input
            sys.stdin = sys.__stdin__
            Framework._script = 0
            Framework._load = 0
            print('')
            return 1
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

    def is_hash(self, hashstr):
        hashdict = [
            {'pattern': '^[a-fA-F0-9]{32}$', 'type': 'MD5'},
            {'pattern': '^[a-fA-F0-9]{16}$', 'type': 'MySQL'},
            {'pattern': '^\*[a-fA-F0-9]{40}$', 'type': 'MySQL5'},
            {'pattern': '^[a-fA-F0-9]{40}$', 'type': 'SHA1'},
            {'pattern': '^[a-fA-F0-9]{56}$', 'type': 'SHA224'},
            {'pattern': '^[a-fA-F0-9]{64}$', 'type': 'SHA256'},
            {'pattern': '^[a-fA-F0-9]{96}$', 'type': 'SHA384'},
            {'pattern': '^[a-fA-F0-9]{128}$', 'type': 'SHA512'},
            {'pattern': '^\$[PH]{1}\$.{31}$', 'type': 'phpass'},
            {'pattern': '^\$2[ya]?\$.{56}$', 'type': 'bcrypt'},
        ]
        for hashitem in hashdict:
            if re.match(hashitem['pattern'], hashstr):
                return hashitem['type']
        return False

    def get_random_str(self, length):
        return ''.join(random.choice(string.lowercase) for i in range(length))

    def _is_writeable(self, filename):
        try:
            fp = open(filename, 'a')
            fp.close()
            return True
        except IOError:
            return False

    def _parse_rowids(self, rowids):
        xploded = []
        rowids = [x.strip() for x in rowids.split(',')]
        for rowid in rowids:
            try:
                if '-' in rowid:
                    start = int(rowid.split('-')[0].strip())
                    end = int(rowid.split('-')[-1].strip())
                    xploded += range(start, end+1)
                else:
                    xploded.append(int(rowid))
            except ValueError:
                continue
        return sorted(list(set(xploded)))

    #==================================================
    # OUTPUT METHODS
    #==================================================

    def print_exception(self, line=''):
        stack_list = [x.strip() for x in traceback.format_exc().strip().splitlines()]
        line = ' '.join([x for x in [stack_list[-1], line] if x])
        if self._global_options['verbosity'] == 1:
            if len(stack_list) > 3:
                line = os.linesep.join((stack_list[-1], stack_list[-3]))
        elif self._global_options['verbosity'] == 2:
            print('%s%s' % (Colors.R, '-'*60))
            traceback.print_exc()
            print('%s%s' % ('-'*60, Colors.N))
        self.error(line)

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
        if self._global_options['verbosity'] >= 1:
            self.output(line)

    def debug(self, line):
        '''Formats and presents output if in debug mode (very verbose).'''
        if self._global_options['verbosity'] >= 2:
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

    def table(self, data, header=[], title=''):
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

    #==================================================
    # DATABASE METHODS
    #==================================================

    def query(self, query, values=(), path=''):
        '''Queries the database and returns the results as a list.'''
        if not path:
            path = os.path.join(self.workspace, 'data.db')
        self.debug('DATABASE => %s' % (path))
        self.debug('QUERY => %s' % (query))
        with sqlite3.connect(path) as conn:
            # coerce all text to bytes (str) for internal processing
            conn.text_factory = bytes
            with closing(conn.cursor()) as cur:
                if values:
                    self.debug('VALUES => %s' % (repr(values)))
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
                return results

    def get_columns(self, table):
        return [(x[1],x[2]) for x in self.query('PRAGMA table_info(\'%s\')' % (table))]

    def get_tables(self):
        return [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'') if x[0] not in ['dashboard']]

    #==================================================
    # ADD METHODS
    #==================================================

    def _display(self, data, rowcount, pattern=None, keys=None):
        display = self.alert if rowcount else self.verbose
        if pattern and keys:
            values = tuple([data[key] or '<blank>' for key in keys])
            display(pattern % values)
        else:
            for key in sorted(data.keys()):
                display('%s: %s' % (key.title(), data[key]))
            display(self.ruler*50)

    def add_domains(self, domain=None, mute=False):
        '''Adds a domain to the database and returns the affected row count.'''
        data = dict(
            domain = domain
        )
        rowcount = self.insert('domains', data.copy(), data.keys())
        if not mute: self._display(data, rowcount, '[domain] %s', data.keys())
        return rowcount

    def add_companies(self, company=None, description=None, mute=False):
        '''Adds a company to the database and returns the affected row count.'''
        data = dict(
            company = company,
            description = description
        )
        rowcount = self.insert('companies', data.copy(), ('company',))
        if not mute: self._display(data, rowcount, '[company] %s - %s', data.keys())
        return rowcount

    def add_netblocks(self, netblock=None, mute=False):
        '''Adds a netblock to the database and returns the affected row count.'''
        data = dict(
            netblock = netblock
        )
        rowcount = self.insert('netblocks', data.copy(), data.keys())
        if not mute: self._display(data, rowcount, '[netblock] %s', data.keys())
        return rowcount

    def add_locations(self, latitude=None, longitude=None, street_address=None, mute=False):
        '''Adds a location to the database and returns the affected row count.'''
        data = dict(
            latitude = latitude,
            longitude = longitude,
            street_address = street_address
        )
        rowcount = self.insert('locations', data.copy(), data.keys())
        if not mute: self._display(data, rowcount, '[location] %s, %s - %s', data.keys())
        return rowcount

    def add_vulnerabilities(self, host=None, reference=None, example=None, publish_date=None, category=None, status=None, mute=False):
        '''Adds a vulnerability to the database and returns the affected row count.'''
        data = dict(
            host = host,
            reference = reference,
            example = example,
            publish_date = publish_date.strftime(self.time_format) if publish_date else None,
            category = category,
            status = status
        )
        rowcount = self.insert('vulnerabilities', data.copy(), data.keys())
        if not mute: self._display(data, rowcount)
        return rowcount

    def add_ports(self, ip_address=None, host=None, port=None, protocol=None, mute=False):
        '''Adds a port to the database and returns the affected row count.'''
        data = dict(
            ip_address = ip_address,
            port = port,
            host = host,
            protocol = protocol
        )
        rowcount = self.insert('ports', data.copy(), ('ip_address', 'port', 'host'))
        if not mute: self._display(data, rowcount, '[port] %s (%s/%s) - %s', ('ip_address', 'port', 'protocol', 'host'))
        return rowcount

    def add_hosts(self, host=None, ip_address=None, region=None, country=None, latitude=None, longitude=None, mute=False):
        '''Adds a host to the database and returns the affected row count.'''
        data = dict(
            host = host,
            ip_address = ip_address,
            region = region,
            country = country,
            latitude = latitude,
            longitude = longitude
        )
        rowcount = self.insert('hosts', data.copy(), ('host', 'ip_address'))
        if not mute: self._display(data, rowcount, '[host] %s (%s)', ('host', 'ip_address'))
        return rowcount

    def add_contacts(self, first_name=None, middle_name=None, last_name=None, email=None, title=None, region=None, country=None, mute=False):
        '''Adds a contact to the database and returns the affected row count.'''
        data = dict(
            first_name = first_name,
            middle_name = middle_name,
            last_name = last_name,
            title = title,
            email = email,
            region = region,
            country = country
        )
        rowcount = self.insert('contacts', data.copy(), ('first_name', 'middle_name', 'last_name', 'title', 'email'))
        if not mute: self._display(data, rowcount, '[contact] %s %s (%s) - %s', ('first_name', 'last_name', 'email', 'title'))
        return rowcount

    def add_credentials(self, username=None, password=None, _hash=None, _type=None, leak=None, mute=False):
        '''Adds a credential to the database and returns the affected row count.'''
        data = dict (
            username = username,
            password = password,
            hash = _hash,
            type = _type,
            leak = leak
        )
        if password and not _hash:
            hash_type = self.is_hash(password)
            if hash_type:
                data['hash'] = password
                data['type'] = hash_type
                data['password'] = None
        # add email usernames to contacts
        if username is not None and '@' in username:
            self.add_contacts(first_name=None, last_name=None, title=None, email=username)
        rowcount = self.insert('credentials', data.copy(), data.keys())
        if not mute: self._display(data, rowcount, '[credential] %s: %s', ('username', 'password'))
        return rowcount

    def add_leaks(self, leak_id=None, description=None, source_refs=None, leak_type=None, title=None, import_date=None, leak_date=None, attackers=None, num_entries=None, score=None, num_domains_affected=None, attack_method=None, target_industries=None, password_hash=None, password_type=None, targets=None, media_refs=None, mute=False):
        '''Adds a leak to the database and returns the affected row count.'''
        data = dict(
            leak_id = leak_id,
            description = description,
            source_refs = source_refs,
            leak_type = leak_type,
            title = title,
            import_date = import_date,
            leak_date = leak_date,
            attackers = attackers,
            num_entries = num_entries,
            score = score,
            num_domains_affected = num_domains_affected,
            attack_method = attack_method,
            target_industries = target_industries,
            password_hash = password_hash,
            password_type = password_type,
            targets = targets,
            media_refs = media_refs
        )
        rowcount = self.insert('leaks', data.copy(), data.keys())
        if not mute: self._display(data, rowcount)
        return rowcount

    def add_pushpins(self, source=None, screen_name=None, profile_name=None, profile_url=None, media_url=None, thumb_url=None, message=None, latitude=None, longitude=None, time=None, mute=False):
        '''Adds a pushpin to the database and returns the affected row count.'''
        data = dict(
            source = source,
            screen_name = screen_name,
            profile_name = profile_name,
            profile_url = profile_url,
            media_url = media_url,
            thumb_url = thumb_url,
            message = message,
            latitude = latitude,
            longitude = longitude,
            time = time.strftime(self.time_format)
        )
        rowcount = self.insert('pushpins', data.copy(), data.keys())
        if not mute: self._display(data, rowcount)
        return rowcount

    def add_profiles(self, username=None, resource=None, url=None, category=None, notes=None, mute=False):
        '''Adds a profile to the database and returns the affected row count.'''
        data = dict(
            username = username,
            resource = resource,
            url = url,
            category = category,
            notes = notes
        )
        rowcount = self.insert('profiles', data.copy(), ('username', 'url'))
        if not mute: self._display(data, rowcount, '[profile] %s - %s (%s)', ('username', 'resource', 'url'))
        return rowcount

    def add_repositories(self, name=None, owner=None, description=None, resource=None, category=None, url=None, mute=False):
        '''Adds a repository to the database and returns the affected row count.'''
        data = dict(
            name = name,
            owner = owner,
            description = description,
            resource = resource,
            category = category,
            url = url
        )
        rowcount = self.insert('repositories', data.copy(), data.keys())
        if not mute: self._display(data, rowcount, '[repository] %s - %s', ('name', 'description'))
        return rowcount

    def insert(self, table, data, unique_columns=[]):
        '''Inserts items into database and returns the affected row count.
        table - the table to insert the data into
        data - the information to insert into the database table in the form of a dictionary
               where the keys are the column names and the values are the column values
        unique_columns - a list of column names that should be used to determine if the
                         information being inserted is unique'''
        # set module to the calling module unless the do_add command was used
        data['module'] = 'user_defined' if 'do_add' in [x[3] for x in inspect.stack()] else self._modulename.split('/')[-1]
        # sanitize the inputs to remove NoneTypes, blank strings, and zeros
        columns = [x for x in data.keys() if data[x]]
        # make sure that module is not seen as a unique column
        unique_columns = [x for x in unique_columns if x in columns and x != 'module']
        # exit if there is nothing left to insert
        if not columns: return 0
        # convert all bytes (str) to unicode for external processing
        for column in columns:
            data[column] = self.to_unicode(data[column])

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

        # increment summary tracker
        if table not in self._summary_counts:
            self._summary_counts[table] = [0,0]
        self._summary_counts[table][0] += rowcount
        self._summary_counts[table][1] += 1

        # build RPC response
        for key in data.keys():
            if not data[key]:
                del data[key]
        self.rpc_cache.append(data)

        return rowcount

    #==================================================
    # OPTIONS METHODS
    #==================================================

    def register_option(self, name, value, required, description):
        self.options.init_option(name=name.lower(), value=value, required=required, description=description)
        # needs to be optimized rather than ran on every register
        self._load_config()

    def _validate_options(self):
        for option in self.options:
            # if value type is bool or int, then we know the options is set
            if not type(self.options[option]) in [bool, int]:
                if self.options.required[option] is True and not self.options[option]:
                    raise FrameworkException('Value required for the \'%s\' option.' % (option.upper()))
        return

    def _load_config(self):
        config_path = os.path.join(self.workspace, 'config.dat')
        # don't bother loading if a config file doesn't exist
        if os.path.exists(config_path):
            # retrieve saved config data
            with open(config_path) as config_file:
                try:
                    config_data = json.loads(config_file.read())
                except ValueError:
                    # file is corrupt, nothing to load, exit gracefully
                    pass
                else:
                    # set option values
                    for key in self.options:
                        try:
                            self.options[key] = config_data[self._modulename][key]
                        except KeyError:
                            # invalid key, contnue to load valid keys
                            continue

    def _save_config(self, name):
        config_path = os.path.join(self.workspace, 'config.dat')
        # create a config file if one doesn't exist
        open(config_path, 'a').close()
        # retrieve saved config data
        with open(config_path) as config_file:
            try:
                config_data = json.loads(config_file.read())
            except ValueError:
                # file is empty or corrupt, nothing to load
                config_data = {}
        # create a container for the current module
        if self._modulename not in config_data:
            config_data[self._modulename] = {}
        # set the new option value in the config
        config_data[self._modulename][name] = self.options[name]
        # remove the option if it has been unset
        if config_data[self._modulename][name] is None:
            del config_data[self._modulename][name]
        # remove the module container if it is empty
        if not config_data[self._modulename]:
            del config_data[self._modulename]
        # write the new config data to the config file
        with open(config_path, 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

    #==================================================
    # API KEY METHODS
    #==================================================

    def get_key(self, name):
        rows = self._query_keys('SELECT value FROM keys WHERE name=? AND value NOT NULL', (name,))
        if not rows:
            return None
        return rows[0][0]

    def add_key(self, name, value):
        result = self._query_keys('UPDATE keys SET value=? WHERE name=?', (value, name))
        if not result:
            return self._query_keys('INSERT INTO keys VALUES (?, ?)', (name, value))
        return result

    def delete_key(self, name):
        #return self._query_keys('UPDATE keys SET value=NULL WHERE name=?', (name,))
        return self._query_keys('DELETE FROM keys WHERE name=?', (name,))

    def _query_keys(self, query, values=()):
        path = os.path.join(self._home, 'keys.db')
        result = self.query(query, values, path)
        # filter out tokens when not called from the get_key method
        if type(result) is list and 'get_key' not in [x[3] for x in inspect.stack()]:
            result = [x for x in result if not x[0].endswith('_token')]
        return result

    def _list_keys(self):
        keys = self._query_keys('SELECT * FROM keys')
        tdata = []
        for key in sorted(keys):
            tdata.append(key)
        if tdata:
            self.table(tdata, header=['Name', 'Value'])

    #==================================================
    # REQUEST METHODS
    #==================================================

    def request(self, url, method='GET', timeout=None, payload=None, headers=None, cookiejar=None, auth=None, content='', redirect=True, agent=None):
        request = Request()
        request.user_agent = agent or self._global_options['user-agent']
        request.debug = True if self._global_options['verbosity'] >= 2 else False
        request.proxy = self._global_options['proxy']
        request.timeout = timeout or self._global_options['timeout']
        request.redirect = redirect
        return request.send(url, method=method, payload=payload, headers=headers, cookiejar=cookiejar, auth=auth, content=content)

    #==================================================
    # SHOW METHODS
    #==================================================

    def show_modules(self, param):
        # process parameter according to type
        if type(param) is list:
            modules = param
        elif param:
            modules = [x for x in Framework._loaded_modules if x.startswith(param)]
            if not modules:
                self.error('Invalid module category.')
                return
        else:
            modules = Framework._loaded_modules
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
            self.output('This workspace has no record of activity.')

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
            print(pattern % ('Name'.ljust(key_len), 'Current Value'.ljust(val_len), 'Required', 'Description'))
            print(pattern % (self.ruler*key_len, (self.ruler*13).ljust(val_len), self.ruler*8, self.ruler*11))
            for key in sorted(options):
                value = options[key] if options[key] != None else ''
                reqd = 'no' if options.required[key] is False else 'yes'
                desc = options.description[key]
                print(pattern % (key.upper().ljust(key_len), self.to_unicode_str(value).ljust(val_len), self.to_unicode_str(reqd).ljust(8), desc))
            print('')
        else:
            print('')
            print('%sNo options available for this module.' % (self.spacer))
            print('')

    def show_keys(self):
        self.do_keys('list')

    def _get_show_names(self):
        # Any method beginning with "show_" will be parsed
        # and added as a subcommand for the show command.
        prefix = 'show_'
        return [x[len(prefix):] for x in self.get_names() if x.startswith(prefix)]

    #==================================================
    # COMMAND METHODS
    #==================================================

    def do_exit(self, params):
        '''Exits the framework'''
        self._exit = 1
        return True

    # alias for exit
    def do_back(self, params):
        '''Exits the current context'''
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
            self._save_config(name)
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
            self._list_keys()
        elif arg == 'add':
            if len(params) == 2:
                if self.add_key(params[0], params[1]):
                    self.output('Key \'%s\' added.' % (params[0]))
            else: print('\nUsage: keys add <name> <value>\n')
        elif arg == 'delete':
            if len(params) == 1:
                if self.delete_key(params[0]):
                    self.output('Key \'%s\' deleted.' % (params[0]))
            else: print('\nUsage: keys delete <name>\n')
        else:
            self.help_keys()

    def do_query(self, params):
        '''Queries the database'''
        if not params:
            self.help_query()
            return
        with sqlite3.connect(os.path.join(self.workspace, 'data.db')) as conn:
            conn.text_factory = bytes
            with closing(conn.cursor()) as cur:
                self.debug('QUERY => %s' % (params))
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

    def do_show(self, params):
        '''Shows various framework items'''
        if not params:
            self.help_show()
            return
        _params = params
        params = params.lower().split()
        arg = params[0]
        params = ' '.join(params[1:])
        if arg in self._get_show_names():
            func = getattr(self, 'show_' + arg)
            if arg == 'modules':
                func(params)
            else:
                func()
        elif _params in self.get_tables():
            self.do_query('SELECT ROWID, * FROM "%s"' % (_params))
        else:
            self.help_show()

    def do_add(self, params):
        '''Adds records to the database'''
        table = ''
        # search params for table names
        for table_name in self.get_tables():
            if params.startswith(table_name):
                params = params[len(table_name)+1:]
                table = table_name
                break
        if table:
            # validate add_* method for table
            if not hasattr(self, 'add_' + table):
                self.error('Cannot add records to dynamicly created tables.')
                return
            columns = [x for x in self.get_columns(table) if x[0] != 'module']
            # sanitize column names to avoid conflicts with builtins in add_* method
            sanitize_column = lambda x: '_'+x if x in ['hash', 'type'] else x
            record = {}
            # build record from parameters
            if params:
                # parse params into values by delim
                values = params.split('~')
                # validate parsed value input
                if len(columns) == len(values):
                    # assign each value to a column
                    for i in range(0,len(columns)):
                        record[sanitize_column(columns[i][0])] = values[i]
                else:
                    self.error('Columns and values length mismatch.')
                    return
            # build record from interactive input
            else:
                for column in columns:
                    try:
                        # prompt user for data
                        value = raw_input('%s (%s): ' % column)
                        record[sanitize_column(column[0])] = value
                    except KeyboardInterrupt:
                        print('')
                        return
                    finally:
                        # ensure proper output for resource scripts
                        if Framework._script:
                            print('%s' % (value))
            # add record to the database
            func = getattr(self, 'add_' + table)
            record['mute'] = True
            func(**record)
        else:
            self.help_add()

    def do_delete(self, params):
        '''Deletes records from the database'''
        table = ''
        # search params for table names
        for table_name in self.get_tables():
            if params.startswith(table_name):
                params = params[len(table_name)+1:]
                table = table_name
                break
        if table:
            # get rowid from parameters
            if params:
                rowids = self._parse_rowids(params)
            # get rowid from interactive input
            else:
                try:
                    # prompt user for data
                    params = raw_input('rowid(s) (INT): ')
                    rowids = self._parse_rowids(params)
                except KeyboardInterrupt:
                    print('')
                    return
                finally:
                    # ensure proper output for resource scripts
                    if Framework._script:
                        print('%s' % (params))
            # delete record(s) from the database
            for rowid in rowids:
                self.query('DELETE FROM %s WHERE ROWID IS ?' % (table), (rowid,))
        else:
            self.help_delete()

    def do_search(self, params):
        '''Searches available modules'''
        if not params:
            self.help_search()
            return
        text = params.split()[0]
        self.output('Searching for \'%s\'...' % (text))
        modules = [x for x in Framework._loaded_modules if text in x]
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
            if not Framework._record:
                if len(arg.split()) > 1:
                    filename = ' '.join(arg.split()[1:])
                    if not self._is_writeable(filename):
                        self.output('Cannot record commands to \'%s\'.' % (filename))
                    else:
                        Framework._record = filename
                        self.output('Recording commands to \'%s\'.' % (Framework._record))
                else: self.help_record()
            else: self.output('Recording is already started.')
        elif arg == 'stop':
            if Framework._record:
                self.output('Recording stopped. Commands saved to \'%s\'.' % (Framework._record))
                Framework._record = None
            else: self.output('Recording is already stopped.')
        elif arg == 'status':
            status = 'started' if Framework._record else 'stopped'
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
            if not Framework._spool:
                if len(arg.split()) > 1:
                    filename = ' '.join(arg.split()[1:])
                    if not self._is_writeable(filename):
                        self.output('Cannot spool output to \'%s\'.' % (filename))
                    else:
                        Framework._spool = codecs.open(filename, 'ab', encoding='utf-8')
                        self.output('Spooling output to \'%s\'.' % (Framework._spool.name))
                else: self.help_spool()
            else: self.output('Spooling is already started.')
        elif arg == 'stop':
            if Framework._spool:
                self.output('Spooling stopped. Output saved to \'%s\'.' % (Framework._spool.name))
                Framework._spool = None
            else: self.output('Spooling is already stopped.')
        elif arg == 'status':
            status = 'started' if Framework._spool else 'stopped'
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
            Framework._script = 1
        else:
            self.error('Script file \'%s\' not found.' % (params))

    def do_load(self, params):
        '''Loads selected module'''
        if not params:
            self.help_load()
            return
        # finds any modules that contain params
        modules = [params] if params in Framework._loaded_modules else [x for x in Framework._loaded_modules if params in x]
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
        if Framework._script:
            end_string = sys.stdin.read()
        else:
            end_string = 'EOF'
            Framework._load = 1
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
        print('Usage: keys [list|add|delete]')
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
        print('SQL examples:')
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
        options = sorted(self._get_show_names() + self.get_tables())
        print(getattr(self, 'do_show').__doc__)
        print('')
        print('Usage: show [%s]' % ('|'.join(options)))
        print('')

    def help_add(self):
        print(getattr(self, 'do_add').__doc__)
        print('')
        print('Usage: add <table> [values]')
        print('')
        print('optional arguments:')
        print('%svalues => \'~\' delimited string representing column values (exclude rowid, module)' % (self.spacer))
        print('')

    def help_delete(self):
        print(getattr(self, 'do_delete').__doc__)
        print('')
        print('Usage: delete <table> [rowid(s)]')
        print('')
        print('optional arguments:')
        print('%srowid(s) => \',\' delimited values or \'-\' delimited ranges representing rowids' % (self.spacer))
        print('')

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_keys(self, text, line, *ignored):
        args = line.split()
        options = ['list', 'add', 'delete']
        if 1 < len(args) < 4:
            if args[1].lower() in options[1:]:
                return [x[0] for x in self._query_keys('SELECT name FROM keys') if x[0].startswith(text)]
            if args[1].lower() in options[:1]:
                return []
        return [x for x in options if x.startswith(text)]

    def complete_load(self, text, *ignored):
        return [x for x in Framework._loaded_modules if x.startswith(text)]
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
            if len(args) > 2: return [x for x in Framework._loaded_modules if x.startswith(args[2])]
            else: return [x for x in Framework._loaded_modules]
        options = sorted(self._get_show_names() + self.get_tables())
        return [x for x in options if x.startswith(text)]

    def complete_add(self, text, *ignored):
        tables = sorted(self.get_tables())
        return [x for x in tables if x.startswith(text)]
    complete_delete = complete_add
