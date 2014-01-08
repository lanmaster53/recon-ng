from __future__ import print_function
import cmd
import random
import string
import sqlite3
import re
import os
import sys
import struct
import textwrap
import socket
import time
import hmac
import hashlib
import HTMLParser
import subprocess
import traceback
import webbrowser
import urllib
import urllib2
import cookielib
import json
import __builtin__
# prep python path for supporting modules
sys.path.append('./libs/')
import aes
import requests_

class module(cmd.Cmd):
    def __init__(self, params):
        cmd.Cmd.__init__(self)
        self.prompt = (params[0])
        self.modulename = params[1]
        self.ruler = '-'
        self.spacer = '  '
        self.module_delimiter = '/' # match line ~21 recon-ng.py
        self.nohelp = '%s[!] No help on %%s%s' % (R, N)
        self.do_help.__func__.__doc__ = '''Displays this menu'''
        self.doc_header = 'Commands (type [help|?] <topic>):'
        self.goptions = __builtin__.goptions
        self.keys = __builtin__.keys
        self.workspace = __builtin__.workspace
        self.home = __builtin__.home
        self.options = {}
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
        if __builtin__.load:
            sys.stdout.write('\r')#%s\r' % (' '*100))
        if __builtin__.script:
            sys.stdout.write('%s\n' % (line))
        if __builtin__.record:
            recorder = open(__builtin__.record, 'ab')
            recorder.write(('%s\n' % (line)).encode('utf-8'))
            recorder.flush()
            recorder.close()
        if __builtin__.spool:
            __builtin__.spool.write('%s%s\n' % (self.prompt, line))
            __builtin__.spool.flush()
        return line

    def onecmd(self, line):
        cmd, arg, line = self.parseline(line)
        if not line:
            return self.emptyline()
        if line == 'EOF':
            # reset stdin for raw_input
            sys.stdin = sys.__stdin__
            __builtin__.script = 0
            __builtin__.load = 0
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

    def boolify(self, s):
        return {'true': True, 'false': False}[s.lower()]

    def autoconvert(self, s):
        if s.lower() in ['none', "''", '""']:
            return None
        for fn in (self.boolify, int, float):
            try: return fn(s)
            except ValueError: pass
            except KeyError: pass
        return s

    def display_modules(self, modules):
        key_len = len(max(modules, key=len)) + len(self.spacer)
        last_category = ''
        for module in sorted(modules):
            category = module.split(self.module_delimiter)[0]
            if category != last_category:
                # print header
                last_category = category
                self.heading(last_category)
            # print module
            print('%s%s' % (self.spacer*2, module))
        print('')

    def display_workspaces(self):
        dirnames = []
        path = '%s/workspaces' % (self.home)
        for name in os.listdir(path):
            if os.path.isdir('%s/%s' % (path, name)):
                dirnames.append([name])
        dirnames.insert(0, ['Workspaces'])
        self.table(dirnames, header=True)

    def display_dashboard(self):
        # display activity table
        self.heading('Activity Summary')
        rows = self.query('SELECT * FROM dashboard ORDER BY 1')
        tdata = [['Module', 'Runs']]
        for row in rows:
            tdata.append(row)
        if rows:
            self.table(tdata, header=True)
        else:
            print('\n%sThis workspace has no record of activity.' % (self.spacer))
        # display sumary results table
        self.heading('Results Summary')
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'')]
        tdata = [['Category', 'Quantity']]
        for table in tables:
            if not table in ['leaks', 'dashboard']:
                count = self.query('SELECT COUNT(*) FROM "%s"' % (table))[0][0]
                tdata.append([table.title(), count])
        self.table(tdata, header=True)

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

    def ascii_sanitize(self, s):
        return ''.join([char for char in s if ord(char) in [10,13] + range(32, 126)])

    def html_unescape(self, s):
        '''Unescapes HTML markup and returns an unescaped string.'''
        h = HTMLParser.HTMLParser()
        return h.unescape(s)
        #p = htmllib.HTMLParser(None)
        #p.save_bgn()
        #p.feed(s)
        #return p.save_end()

    def html_escape(self, s):
        escapes = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&apos;",
            ">": "&gt;",
            "<": "&lt;",
            }
        return "".join(escapes.get(c,c) for c in s)

    def is_hash(self, hashstr):
        hashdict = [
            {"pattern": "[a-fA-F0-9]", "len": 16},
            {"pattern": "[a-fA-F0-9]", "len": 32},
            {"pattern": "[a-fA-F0-9]", "len": 40},
            {"pattern": "^\*[a-fA-F0-9]", "len": 41},
            {"pattern": "[a-fA-F0-9]", "len": 56},
            {"pattern": "[a-fA-F0-9]", "len": 64},
            {"pattern": "[a-fA-F0-9]", "len": 96},
            {"pattern": "[a-fA-F0-9]", "len": 128}
        ]
        for hashitem in hashdict:
            if len(hashstr) == hashitem["len"] and re.match(hashitem["pattern"], hashstr):
                return True
        return False

    def aes_decrypt(self, ciphertext, key, iv):
        decoded = ciphertext.decode('base64')
        password = aes.decryptData(key, iv.encode('utf-8') + decoded)
        return unicode(password, 'utf-8')

    def cidr_to_list(self, string):
        # references:
        # http://boubakr92.wordpress.com/2012/12/20/convert-cidr-into-ip-range-with-python/
        # http://stackoverflow.com/questions/8338655/how-to-get-list-of-ip-addresses
        # parse address and cidr
        (addrString, cidrString) = string.split('/')
        # split address into octets and convert cidr to int
        addr = addrString.split('.')
        cidr = int(cidrString)
        # initialize the netmask and calculate based on cidr mask
        mask = [0, 0, 0, 0]
        for i in range(cidr):
            mask[i/8] = mask[i/8] + (1 << (7 - i % 8))
        # initialize net and binary and netmask with addr to get network
        net = []
        for i in range(4):
            net.append(int(addr[i]) & mask[i])
        # duplicate net into broad array, gather host bits, and generate broadcast
        broad = list(net)
        brange = 32 - cidr
        for i in range(brange):
            broad[3 - i/8] = broad[3 - i/8] + (1 << (i % 8))
        # print information, mapping integer lists to strings for easy printing
        #mask = ".".join(map(str, mask))
        net = ".".join(map(str, net))
        broad = ".".join(map(str, broad))
        ips = []
        f = struct.unpack('!I',socket.inet_pton(socket.AF_INET,net))[0]
        l = struct.unpack('!I',socket.inet_pton(socket.AF_INET,broad))[0]
        while f <= l:
            ips.append(socket.inet_ntop(socket.AF_INET,struct.pack('!I',f)))
            f = f + 1
        return ips

    def api_guard(self, num):
        try:
            ans = raw_input('This operation will decrement the allotted quota by %d. Do you want to continue? [Y/N]: ' % (num))
            if ans.upper() != 'Y': return False
        except KeyboardInterrupt:
            print('')
            return False
        return True

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
        print('%s[!] %s%s' % (R, self.to_unicode(line), N))

    def output(self, line):
        '''Formats and presents normal output.'''
        print('%s[*]%s %s' % (B, N, self.to_unicode(line)))

    def alert(self, line):
        '''Formats and presents important output.'''
        print('%s[*]%s %s' % (G, N, self.to_unicode(line)))

    def verbose(self, line):
        '''Formats and presents output if in verbose mode.'''
        if self.goptions['verbose']['value']:
            self.output(line)

    def heading(self, line, level=1):
        '''Formats and presents styled banner text'''
        line = self.to_unicode(line)
        print('')
        if level == 0:
            print(self.ruler*len(line))
            print(line.upper())
            print(self.ruler*len(line))
        if level == 1:
            print('%s%s' % (self.spacer, line.title()))
            print('%s%s' % (self.spacer, self.ruler*len(line)))

    def table(self, data, header=False):
        '''Accepts a list of rows and outputs a table.'''
        tdata = list(data)
        if len(set([len(x) for x in tdata])) > 1:
            raise FrameworkException('Row lengths not consistent.')
        lens = []
        cols = len(tdata[0])
        for i in range(0,cols):
            lens.append(len(max([self.to_unicode_str(x[i]) if x[i] != None else '' for x in tdata], key=len)))
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

    def display_schema(self):
        '''Displays the database schema'''
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'')]
        for table in tables:
            columns = [(x[1],x[2]) for x in self.query('PRAGMA table_info(\'%s\')' % (table))]
            name_len = len(max([x[0] for x in columns], key=len))
            type_len = len(max([x[1] for x in columns], key=len))
            print('')
            print('%s+%s+' % (self.spacer, self.ruler*(name_len+type_len+5)))
            print('%s| %s |' % (self.spacer, table.center(name_len+type_len+3)))
            print('%s+%s+' % (self.spacer, self.ruler*(name_len+type_len+5)))
            for column in columns:
                print('%s| %s | %s |' % (self.spacer, column[0].ljust(name_len), column[1].center(type_len)))
            print('%s+%s+' % (self.spacer, self.ruler*(name_len+type_len+5)))
        print('')

    def add_host(self, host, ip_address=None, region=None, country=None, latitude=None, longitude=None):
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

    def add_contact(self, fname, lname, title, email=None, region=None, country=None):
        '''Adds a contact to the database and returns the affected row count.'''
        data = dict(
            fname = self.to_unicode(fname),
            lname = self.to_unicode(lname),
            title = self.to_unicode(title),
            email = self.to_unicode(email),
            region = self.to_unicode(region),
            country = self.to_unicode(country),
        )

        return self.insert('contacts', data, ('fname', 'lname', 'title', 'email'))

    def add_cred(self, username, password=None, hashtype=None, leak=None):
        '''Adds a credential to the database and returns the affected row count.'''
        data = {}
        data['username'] = self.to_unicode(username)
        if password and not self.is_hash(password): data['password'] = self.to_unicode(password)
        if password and self.is_hash(password): data['hash'] = self.to_unicode(password)
        if hashtype: data['type'] = self.to_unicode(hashtype)
        if leak: data['leak'] = self.to_unicode(leak)

        return self.insert('creds', data, data.keys())

    def add_pushpin(self, source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time):
        '''Adds a contact to the database and returns the affected row count.'''
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

        return self.insert('pushpin', data, data.keys())

    def add_table(self, table, data, header=False):
        '''Adds a table to the database and populates it with data.
        table - the name of the table to create.
        header - whether or not the first row of tdata consists of headers.
        data - the information to insert into the database table.'''

        reserved = ['leaks']
        tdata = list(data)
        table = self.to_unicode_str(table).lower()
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'')]
        if table in tables + reserved:
            raise FrameworkException('Table \'%s\' already exists or is a reserved table name' % (table))
        # create database table
        if header:
            rdata = tdata.pop(0)
            columns = [self.to_unicode_str(x).lower() for x in rdata]
        else:
            columns = ['column_%s' % (i) for i in range(0,len(tdata[0]))]
        metadata = ', '.join(['\'%s\' TEXT' % (x) for x in columns])
        self.query('CREATE TABLE IF NOT EXISTS \'%s\' (%s)' % (table, metadata))
        # insert rows into database table
        for rdata in tdata:
            data = {}
            for i in range(0, len(columns)):
                data[columns[i]] = self.to_unicode(rdata[i])
            self.insert(table, data)
        self.verbose('\'%s\' table created in the database' % (table))

    def add_column(self, table, column):
        '''Adds a column to a database table.'''
        column = self.to_unicode_str(column).lower()
        columns = [x[1] for x in self.query('PRAGMA table_info(\'%s\')' % (table))]
        if not columns:
            raise FrameworkException('Table \'%s\' does not exist' % (table))
        if column in columns:
            raise FrameworkException('Column \'%s\' already exists in table \'%s\'' % (column, table))
        self.query('ALTER TABLE "%s" ADD COLUMN \'%s\' TEXT' % (table, column))
        self.verbose('\'%s\' column created in the \'%s\' table' % (column, table))

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

    def query(self, query, values=()):
        '''Queries the database and returns the results as a list.'''
        if self.goptions['debug']['value']: self.output(query)
        conn = sqlite3.connect('%s/data.db' % (self.workspace))
        cur = conn.cursor()
        if values:
            if self.goptions['debug']['value']: self.output(repr(values))
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

    #==================================================
    # OPTIONS METHODS
    #==================================================

    def display_options(self, params):
        '''Lists options'''
        spacer = self.spacer
        if self.options:
            pattern = '%s%%s  %%s  %%s  %%s' % (spacer)
            key_len = len(max(self.options, key=len))
            if key_len < 4: key_len = 4
            val_len = len(max([self.to_unicode_str(self.options[x]['value']) for x in self.options], key=len))
            if val_len < 13: val_len = 13
            print('')
            print(pattern % ('Name'.ljust(key_len), 'Current Value'.ljust(val_len), 'Req', 'Description'))
            print(pattern % (self.ruler*key_len, (self.ruler*13).ljust(val_len), self.ruler*3, self.ruler*11))
            for key in sorted(self.options):
                value = self.options[key]['value'] if self.options[key]['value'] != None else ''
                reqd = self.options[key]['reqd']
                desc = self.options[key]['desc']
                print(pattern % (key.upper().ljust(key_len), self.to_unicode_str(value).ljust(val_len), reqd.ljust(3), desc))
            print('')
        else:
            if params != 'info': print('')
            print('%sNo options available for this module.' % (spacer))
            print('')

    def register_option(self, name, value, reqd, desc, options=None):
        # can't use not because empty dictonary would eval as true
        if options == None: options = self.options
        options[name.lower()] = {'value':value, 'reqd':reqd, 'desc':desc}

    def validate_options(self):
        for option in self.options:
            # if value type is bool or int, then we know the options is set
            if not type(self.options[option]['value']) in [bool, int]:
                if self.options[option]['reqd'].lower() == 'yes' and not self.options[option]['value']:
                    raise FrameworkException('Value required for the \'%s\' option.' % (option))
        return

    def get_source(self, params, query=None):
        prefix = params.split()[0].lower()
        if prefix in ['query', 'db']:
            query = ' '.join(params.split()[1:]) if prefix == 'query' else query
            try: results = self.query(query)
            except sqlite3.OperationalError as e:
                raise FrameworkException('Invalid source query. %s %s' % (type(e).__name__, e.message))
            if not results:
                sources = []
            elif len(results[0]) > 1:
                raise FrameworkException('Too many columns of data as source input.')
            else: sources = [x[0] for x in results]
        elif os.path.exists(params):
            sources = open(params).read().split()
        else:
            sources = [params]
        return [self.to_unicode(x) for x in sources]

    #==================================================
    # API KEY METHODS
    #==================================================

    def display_keys(self):
        tdata = []
        for key in sorted(self.keys):
            tdata.append([key, self.keys[key]])
        if tdata:
            tdata.insert(0, ['Name', 'Value'])
            self.table(tdata, header=True)
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
    # 3RD PARTY API METHODS
    #==================================================

    def get_twitter_oauth_token(self):
        token_name = 'twitter_token'
        try:
            return self.get_key(token_name)
        except:
            pass
        twitter_key = self.get_key('twitter_api')
        twitter_secret = self.get_key('twitter_secret')
        url = 'https://api.twitter.com/oauth2/token'
        auth = (twitter_key, twitter_secret)
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
        payload = {'grant_type': 'client_credentials'}
        resp = self.request(url, method='POST', auth=auth, headers=headers, payload=payload)
        if 'errors' in resp.json:
            raise FrameworkException('%s, %s' % (resp.json['errors'][0]['message'], resp.json['errors'][0]['label']))
        access_token = resp.json['access_token']
        self.add_key(token_name, access_token)
        return access_token

    def build_pwnedlist_payload(self, payload, method, key, secret):
        timestamp = int(time.time())
        payload['ts'] = timestamp
        payload['key'] = key
        msg = '%s%s%s%s' % (key, timestamp, method, secret)
        hm = hmac.new(secret.encode('utf-8'), msg, hashlib.sha1)
        payload['hmac'] = hm.hexdigest()
        return payload

    def search_shodan_api(self, query, limit=0):
        api_key = self.get_key('shodan_api')
        url = 'http://www.shodanhq.com/api/search'
        payload = {'q': query, 'key': api_key}
        results = []
        cnt = 1
        page = 1
        self.verbose('Searching Shodan API for: %s' % (query))
        while True:
            resp = self.request(url, payload=payload)
            if resp.json == None:
                raise FrameworkException('Invalid JSON response.\n%s' % (resp.text))
            if 'error' in resp.json:
                raise FrameworkException(resp.json['error'])
            if not resp.json['matches']:
                break
            # add new results
            results.extend(resp.json['matches'])
            # check limit
            if limit == cnt:
                break
            cnt += 1
            # next page
            page += 1
            payload['page'] = page
        return results

    def search_bing_api(self, query, limit=0):
        api_key = self.get_key('bing_api')
        url = 'https://api.datamarket.azure.com/Data.ashx/Bing/Search/v1/Web'
        payload = {'Query': query, '$format': 'json'}
        results = []
        cnt = 1
        self.verbose('Searching Bing API for: %s' % (query))
        while True:
            resp = None
            resp = self.request(url, payload=payload, auth=(api_key, api_key))
            if resp.json == None:
                raise FrameworkException('Invalid JSON response.\n%s' % (resp.text))
            # add new results
            if 'results' in resp.json['d']:
                results.extend(resp.json['d']['results'])
            # check limit
            if limit == cnt:
                break
            cnt += 1
            # check for more pages
            if not '__next' in resp.json['d']:
                break
            payload['$skip'] = resp.json['d']['__next'].split('=')[-1]
        return results

    def search_google_api(self, query, limit=0):
        api_key = self.get_key('google_api')
        cse_id = self.get_key('google_cse')
        url = 'https://www.googleapis.com/customsearch/v1'
        payload = {'alt': 'json', 'prettyPrint': 'false', 'key': api_key, 'cx': cse_id, 'q': query}
        results = []
        cnt = 1
        self.verbose('Searching Google API for: %s' % (query))
        while True:
            resp = None
            resp = self.request(url, payload=payload)
            if resp.json == None:
                raise FrameworkException('Invalid JSON response.\n%s' % (resp.text))
            # add new results
            if 'items' in resp.json:
                results.extend(resp.json['items'])
            # check limit
            if limit == cnt:
                break
            cnt += 1
            # check for more pages
            if not 'nextPage' in resp.json['queries']:
                break
            payload['start'] = resp.json['queries']['nextPage'][0]['startIndex']
        return results

    #==================================================
    # REQUEST METHODS
    #==================================================

    def make_cookie(self, name, value, domain, path='/'):
        return cookielib.Cookie(
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

    def request(self, url, method='GET', timeout=None, payload=None, headers=None, cookiejar=None, auth=None, redirect=True):
        request = requests_.Request()
        request.user_agent = self.goptions['user-agent']['value']
        request.debug = self.goptions['debug']['value']
        request.proxy = self.goptions['proxy']['value']
        request.timeout = timeout or self.goptions['timeout']['value']
        request.redirect = redirect
        return request.send(url, method=method, payload=payload, headers=headers, cookiejar=cookiejar, auth=auth)

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

    def do_info(self, params):
        '''Displays module information'''
        if params: self.alert('Command parameters ignored in module context.')
        self.info['Path'] = 'modules/%s.py' % (self.modulename)
        print('')
        # meta
        for item in ['Name', 'Path', 'Author']:
            print('%s: %s' % (item.rjust(10), self.info[item]))
        print('')
        # options
        print('Options:')
        self.display_options('info')
        # description
        print('Description:')
        print('%s%s' % (self.spacer, textwrap.fill(self.info['Description'], 100, subsequent_indent=self.spacer)))
        print('')
        # comments
        if self.info['Comments']:
            print('Comments:')
            for comment in self.info['Comments']:
                print('%s%s' % (self.spacer, textwrap.fill('* %s' % (comment), 100, subsequent_indent=self.spacer)))
            print('')

    def do_set(self, params):
        '''Sets module options'''
        options = params.split()
        if len(options) < 2:
            self.help_set()
            return
        name = options[0].lower()
        if name in self.options:
            value = ' '.join(options[1:])
            print('%s => %s' % (name.upper(), value))
            self.options[name]['value'] = self.autoconvert(value)
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
            self.display_keys()
            return
        elif arg in ['add', 'update']:
            if len(params) == 2:
                self.add_key(params[0], params[1])
                self.output('Key \'%s\' added.' % (params[0]))
            else: print('Usage: keys [add|update] <name> <value>')
            return
        elif arg == 'delete':
            if len(params) == 1:
                try:
                    self.delete_key(params[0])
                except FrameworkException as e:
                    self.error(e.__str__())
                else:
                    self.output('Key \'%s\' deleted.' % (params[0]))
            else: print('Usage: keys delete <name>')
            return

    def do_query(self, params):
        '''Queries the database'''
        if not params:
            self.help_query()
            return
        conn = sqlite3.connect('%s/data.db' % (self.workspace))
        cur = conn.cursor()
        if self.goptions['debug']['value']: self.output(params)
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
                tdata.insert(0, header)
                self.table(tdata, header=True)
                self.output('%d rows returned' % (len(tdata)-1)) # -1 to account for header row
        else:
            conn.commit()
            self.output('%d rows affected.' % (cur.rowcount))
        conn.close()
        return

    def do_show(self, params):
        '''Shows various framework items'''
        if not params:
            self.help_show()
            return
        arg = params.lower()
        if arg.split()[0] == 'modules':
            if len(arg.split()) > 1:
                param = arg.split()[1]
                modules = [x for x in __builtin__.loaded_modules if x.startswith(param)]
                if not modules:
                    self.error('Invalid module category.')
                    return
            else:
                modules = __builtin__.loaded_modules
            self.display_modules(modules)
            return
        elif arg == 'options':
            self.display_options(None)
            return
        elif arg == 'dashboard':
            self.display_dashboard()
            return
        elif arg == 'workspaces':
            self.display_workspaces()
            return
        elif arg == 'schema':
            self.display_schema()
            return
        elif arg in [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'')]:
            self.do_query('SELECT * FROM "%s" ORDER BY 1' % (arg))
            return

    def do_search(self, params):
        '''Searches available modules'''
        if not params:
            self.help_search()
            return
        text = params.split()[0]
        self.output('Searching for \'%s\'...' % (text))
        modules = [x for x in __builtin__.loaded_modules if text in x]
        if not modules:
            self.error('No modules found containing \'%s\'.' % (text))
        else:
            self.display_modules(modules)

    def do_record(self, params):
        '''Records commands to a resource file'''
        if not params:
            self.help_record()
            return
        arg = params.lower()
        if arg.split()[0] == 'start':
            if not __builtin__.record:
                if len(arg.split()) > 1:
                    filename = ' '.join(arg.split()[1:])
                    if not is_writeable(filename):
                        self.output('Cannot record commands to \'%s\'.' % (filename))
                    else:
                        __builtin__.record = filename
                        self.output('Recording commands to \'%s\'.' % (__builtin__.record))
                else: self.help_record()
            else: self.output('Recording is already started.')
        elif arg == 'stop':
            if __builtin__.record:
                self.output('Recording stopped. Commands saved to \'%s\'.' % (__builtin__.record))
                __builtin__.record = None
            else: self.output('Recording is already stopped.')
        elif arg == 'status':
            status = 'started' if __builtin__.record else 'stopped'
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
            if not __builtin__.spool:
                if len(arg.split()) > 1:
                    filename = ' '.join(arg.split()[1:])
                    if not is_writeable(filename):
                        self.output('Cannot spool output to \'%s\'.' % (filename))
                    else:
                        __builtin__.spool = open(filename, 'ab')
                        self.output('Spooling output to \'%s\'.' % (__builtin__.spool.name))
                else: self.help_spool()
            else: self.output('Spooling is already started.')
        elif arg == 'stop':
            if __builtin__.spool:
                self.output('Spooling stopped. Output saved to \'%s\'.' % (__builtin__.spool.name))
                __builtin__.spool = None
            else: self.output('Spooling is already stopped.')
        elif arg == 'status':
            status = 'started' if __builtin__.spool else 'stopped'
            self.output('Output spooling is %s.' % (status))
        else:
            self.help_spool()

    def do_shell(self, params):
        '''Executes shell commands'''
        proc = subprocess.Popen(params, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        self.output('Command: %s' % (params))
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        if stdout: sys.stdout.write('%s%s%s' % (O, stdout, N))
        if stderr: sys.stdout.write('%s%s%s' % (R, stderr, N))

    def do_run(self, params):
        '''Runs the module'''
        try:
            self.validate_options()
            self.module_run()
        except KeyboardInterrupt:
            print('')
        except socket.timeout as e:
            self.error('Request timeout. Consider adjusting the global \'TIMEOUT\' option.')
        except Exception as e:
            if self.goptions['debug']['value']:
                print('%s%s' % (R, '-'*60))
                traceback.print_exc()
                print('%s%s' % ('-'*60, N))
            self.error(e.__str__())
        finally:
            self.query('INSERT OR REPLACE INTO dashboard (module, runs) VALUES (\'%(x)s\', COALESCE((SELECT runs FROM dashboard WHERE module=\'%(x)s\')+1, 1))' % {'x': self.modulename})

    def module_run(self):
        pass

    def do_resource(self, params):
        '''Executes commands from a resource file'''
        if not params:
            self.help_resource()
            return
        if os.path.exists(params):
            sys.stdin = open(params)
            __builtin__.script = 1
            return
        else:
            self.error('Script file \'%s\' not found.' % (params))
            return

    def do_load(self, params):
        '''Loads selected module'''
        if not params:
            self.help_load()
            return
        # finds any modules that contain params
        modules = [params] if params in __builtin__.loaded_modules else [x for x in __builtin__.loaded_modules if params in x]
        # notify the user if none or multiple modules are found
        if len(modules) != 1:
            if not modules:
                self.error('Invalid module name.')
            else:
                self.output('Multiple modules match \'%s\'.' % params)
                self.display_modules(modules)
            return
        import StringIO
        # compensation for stdin being used for scripting and loading
        if __builtin__.script:
            end_string = sys.stdin.read()
        else:
            end_string = 'EOF'
            __builtin__.load = 1
        sys.stdin = StringIO.StringIO('load %s\n%s' % (modules[0], end_string))
        return True
    do_use = do_load

    #==================================================
    # HELP METHODS
    #==================================================

    def help_keys(self):
        print('Usage: keys [list|add|delete|update]')

    def help_load(self):
        print('Usage: [load|use] <module>')
    help_use = help_load

    def help_record(self):
        print('Usage: record [start <filename>|stop|status]')

    def help_spool(self):
        print('Usage: spool [start <filename>|stop|status]')

    def help_resource(self):
        print('Usage: resource <filename>')

    def help_query(self):
        print('Usage: query <sql>')
        print('')
        print('SQL Examples:')
        print('%s%s' % (self.spacer, 'SELECT columns|* FROM table_name'))
        print('%s%s' % (self.spacer, 'SELECT columns|* FROM table_name WHERE some_column=some_value'))
        print('%s%s' % (self.spacer, 'DELETE FROM table_name WHERE some_column=some_value'))
        print('%s%s' % (self.spacer, 'INSERT INTO table_name (column1, column2,...) VALUES (value1, value2,...)'))
        print('%s%s' % (self.spacer, 'UPDATE table_name SET column1=value1, column2=value2,... WHERE some_column=some_value'))

    def help_search(self):
        print('Usage: search <string>')

    def help_set(self):
        print('Usage: set <option> <value>')
        self.display_options(None)

    def help_unset(self):
        print('Usage: unset <option>')
        self.display_options(None)

    def help_shell(self):
        print('Usage: [shell|!] <command>')
        print('...or just type a command at the prompt.')

    def help_show(self):
        print('Usage: show [modules|options|dashboard|workspaces|schema|<table>]')

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
        return [x for x in __builtin__.loaded_modules if x.startswith(text)]
    complete_info = complete_use = complete_load

    def complete_record(self, text, *ignored):
        return [x for x in ['start', 'stop', 'status'] if x.startswith(text)]
    complete_spool = complete_record

    def complete_set(self, text, *ignored):
        return [x for x in self.options if x.startswith(text)]
    complete_unset = complete_set

    def complete_show(self, text, line, *ignored):
        args = line.split()
        if len(args) > 1 and args[1].lower() == 'modules':
            if len(args) > 2: return [x for x in __builtin__.loaded_modules if x.startswith(args[2])]
            else: return [x for x in __builtin__.loaded_modules]
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'')]
        options = ['modules', 'options', 'workspaces', 'schema']
        options.extend(tables)
        return [x for x in options if x.startswith(text)]

#=================================================
# SUPPORT CLASSES AND FUNCTIONS
#=================================================

class FrameworkException(Exception):
    pass

def is_writeable(filename):
    try:
        fp = open(filename, 'ab')
        fp.close()
        return True
    except IOError:
        return False
