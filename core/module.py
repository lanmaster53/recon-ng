from __future__ import print_function
import cookielib
import hashlib
import hmac
import HTMLParser
import os
import random
import re
import socket
import sqlite3
import string
import struct
import sys
import textwrap
import time
import traceback
import framework
# prep python path for supporting modules
sys.path.append('./libs/')
import aes

#=================================================
# MODULE CLASS
#=================================================

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.options = framework.Options()

    #==================================================
    # SUPPORT METHODS
    #==================================================

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
    # DATABASE METHODS
    #==================================================

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

    def add_table(self, table, data, header=[]):
        '''Adds a table to the database and populates it with data.
        table - the name of the table to create.
        header - whether or not the first row of tdata consists of headers.
        data - the information to insert into the database table.'''

        reserved = ['leaks']
        tdata = list(data)
        if header:
            tdata.insert(0, header)
        table = self.to_unicode_str(table).lower()
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'')]
        if table in tables + reserved:
            raise framework.FrameworkException('Table \'%s\' already exists or is a reserved table name' % (table))
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
            raise framework.FrameworkException('Table \'%s\' does not exist' % (table))
        if column in columns:
            raise framework.FrameworkException('Column \'%s\' already exists in table \'%s\'' % (column, table))
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

    #==================================================
    # OPTIONS METHODS
    #==================================================

    def get_source(self, params, query=None):
        prefix = params.split()[0].lower()
        if prefix in ['query', 'db']:
            query = ' '.join(params.split()[1:]) if prefix == 'query' else query
            try: results = self.query(query)
            except sqlite3.OperationalError as e:
                raise framework.FrameworkException('Invalid source query. %s %s' % (type(e).__name__, e.message))
            if not results:
                sources = []
            elif len(results[0]) > 1:
                raise framework.FrameworkException('Too many columns of data as source input.')
            else: sources = [x[0] for x in results]
        elif os.path.exists(params):
            sources = open(params).read().split()
        else:
            sources = [params]
        return [self.to_unicode(x) for x in sources]

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
            raise framework.FrameworkException('%s, %s' % (resp.json['errors'][0]['message'], resp.json['errors'][0]['label']))
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
                raise framework.FrameworkException('Invalid JSON response.\n%s' % (resp.text))
            if 'error' in resp.json:
                raise framework.FrameworkException(resp.json['error'])
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
                raise framework.FrameworkException('Invalid JSON response.\n%s' % (resp.text))
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
                raise framework.FrameworkException('Invalid JSON response.\n%s' % (resp.text))
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

    #==================================================
    # SHOW METHODS
    #==================================================

    def show_source(self):
        filename = 'modules/%s.py' % (self.modulename)    
        print(open(filename).read())

    def show_info(self):
        self.info['Path'] = 'modules/%s.py' % (self.modulename)
        print('')
        # meta
        for item in ['Name', 'Path', 'Author']:
            print('%s: %s' % (item.rjust(10), self.info[item]))
        print('')
        # options
        print('Options:', end='')
        self.show_options()
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

    #==================================================
    # COMMAND METHODS
    #==================================================

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
            if self.global_options['debug']:
                print('%s%s' % (R, '-'*60))
                traceback.print_exc()
                print('%s%s' % ('-'*60, N))
            self.error(e.__str__())
        finally:
            self.query('INSERT OR REPLACE INTO dashboard (module, runs) VALUES (\'%(x)s\', COALESCE((SELECT runs FROM dashboard WHERE module=\'%(x)s\')+1, 1))' % {'x': self.modulename})

    def module_run(self):
        pass