from __future__ import print_function
import cookielib
import dns.resolver
import hashlib
import hmac
import HTMLParser
import os
import re
import socket
import sqlite3
import struct
import sys
import textwrap
import time
import traceback
# framework libs
import aes
import framework

#=================================================
# MODULE CLASS
#=================================================

class Module(framework.Framework):

    def __init__(self, params, query=None):
        framework.Framework.__init__(self, params)
        self.options = framework.Options()
        # register a data source option if a default query is specified in the module
        if query is not None:
            self.default_source = query
            self.register_option('source', 'default', 'yes', 'source of input (see \'show info\' for details)')

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
            '&': '&amp;',
            '"': '&quot;',
            "'": '&apos;',
            '>': '&gt;',
            '<': '&lt;',
            }
        return ''.join(escapes.get(c,c) for c in s)

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
        #mask = '.'.join(map(str, mask))
        net = '.'.join(map(str, net))
        broad = '.'.join(map(str, broad))
        ips = []
        f = struct.unpack('!I',socket.inet_pton(socket.AF_INET,net))[0]
        l = struct.unpack('!I',socket.inet_pton(socket.AF_INET,broad))[0]
        while f <= l:
            ips.append(socket.inet_ntop(socket.AF_INET,struct.pack('!I',f)))
            f = f + 1
        return ips

    def parse_name(self, name):
        elements = [self.html_unescape(x) for x in name.strip().split()]
        # remove prefixes and suffixes
        names = []
        for i in range(0,len(elements)):
            # preserve initials
            if re.search(r'^\w\.$', elements[i]):
                elements[i] = elements[i][:-1]
            # remove unecessary prefixes and suffixes
            elif re.search(r'(?:\.|^the$|^jr$|^sr$|^I{2,3}$)', elements[i], re.IGNORECASE):
                continue
            names.append(elements[i])
        # make sense of the remaining elements
        if len(names) > 3:
            names[2:] = [' '.join(names[2:])]
        # clean up any remaining garbage characters
        names = [re.sub(r"[,']", '', x) for x in names]
        # set values and return names
        fname = names[0] if len(names) >= 1 else None
        mname = names[1] if len(names) >= 3 else None
        lname = names[-1] if len(names) >= 2 else None
        return fname, mname, lname

    def get_resolver(self):
        resolver = dns.resolver.get_default_resolver()
        resolver.nameservers = [self.global_options['nameserver']]
        resolver.lifetime = 3
        return resolver

    #==================================================
    # OUTPUT METHODS
    #==================================================

    def summarize(self, new, total):
        self.heading('Summary', level=0)
        if new > 0:
            method = getattr(self, 'alert')
        else:
            method = getattr(self, 'output')
        method('%d total (%d new) items found.' % (total, new))

    #==================================================
    # DATABASE METHODS
    #==================================================

    def add_table(self, table, data, header=[]):
        '''Adds a table to the database and populates it with data.
        table - the name of the table to create.
        header - whether or not the first row of tdata consists of headers.
        data - the information to insert into the database table.'''

        tdata = list(data)
        if header:
            tdata.insert(0, header)
        table = self.to_unicode_str(table).lower()
        tables = self.get_tables()
        if table in tables:
            raise framework.FrameworkException('Table \'%s\' already exists or is a reserved table name.' % (table))
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
        self.verbose('\'%s\' table created.' % (table))

    def add_column(self, table, column):
        '''Adds a column to a database table.'''
        column = self.to_unicode_str(column).lower()
        columns = [x[0] for x in self.get_columns(table)]
        if not columns:
            raise framework.FrameworkException('Table \'%s\' does not exist.' % (table))
        if column in columns:
            raise framework.FrameworkException('Column \'%s\' already exists in table \'%s\'.' % (column, table))
        self.query('ALTER TABLE "%s" ADD COLUMN \'%s\' TEXT' % (table, column))
        self.verbose('\'%s\' column created in the \'%s\' table.' % (column, table))

    #==================================================
    # OPTIONS METHODS
    #==================================================

    def get_source(self, params, query=None):
        prefix = params.split()[0].lower()
        if prefix in ['query', 'default']:
            query = ' '.join(params.split()[1:]) if prefix == 'query' else query
            try: results = self.query(query)
            except sqlite3.OperationalError as e:
                raise framework.FrameworkException('Invalid source query. %s %s' % (type(e).__name__, e.message))
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
        source = [self.to_unicode(x) for x in sources]
        if not source:
            raise framework.FrameworkException('Source contains no input.')
        return source

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
        url = 'https://api.shodan.io/shodan/host/search'
        payload = {'query': query, 'key': api_key}
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
        for path in ['%s/modules/%s.py' % (x, self.modulename) for x in (self.app_path, self.home)]:
            if os.path.exists(path):
                filename = path
        with open(filename) as f:
            content = f.readlines()
            nums = [str(x) for x in range(1, len(content)+1)]
            num_len = len(max(nums, key=len))
            for num in nums:
                print('%s|%s' % (num.rjust(num_len), content[int(num)-1]), end='')

    def show_info(self):
        self.info['Path'] = 'modules/%s.py' % (self.modulename)
        print('')
        # meta info
        for item in ['Name', 'Path', 'Author', 'Version']:
            if item in self.info:
                print('%s: %s' % (item.rjust(10), self.info[item]))
        #dirs = self.modulename.split('/')
        #if dirs[0] == 'recon':
        #    print('%s: %s => %s' % ('Transform'.rjust(10), dirs[1].upper(), dirs[2].upper()))
        print('')
        # description
        if 'Description' in self.info:
            print('Description:')
            print('%s%s' % (self.spacer, textwrap.fill(self.info['Description'], 100, subsequent_indent=self.spacer)))
            print('')
        # options
        print('Options:', end='')
        self.show_options()
        # sources
        if hasattr(self, 'default_source'):
            print('Source Options:')
            print('%s%s%s' % (self.spacer, 'default'.ljust(15), self.default_source))
            print('%s%sstring representing a single input' % (self.spacer, '<string>'.ljust(15)))
            print('%s%spath to a file containing a list of inputs' % (self.spacer, '<path>'.ljust(15)))
            print('%s%sdatabase query returning one column of inputs' % (self.spacer, 'query <sql>'.ljust(15)))
            print('')
        # comments
        if 'Comments' in self.info and self.info['Comments']:
            print('Comments:')
            for comment in self.info['Comments']:
                print('%s%s' % (self.spacer, textwrap.fill('* %s' % (comment), 100, subsequent_indent=self.spacer)))
            print('')

    def show_globals(self):
        self.show_options(self.global_options)

    #==================================================
    # COMMAND METHODS
    #==================================================

    def do_run(self, params):
        '''Runs the module'''
        try:
            self.validate_options()
            pre = self.module_pre()
            params = [pre] if pre is not None else []
            # provide input if a default query is specified in the module
            if hasattr(self, 'default_source'):
                #objs = [x[0] for x in self.query(self.default_source)]
                objs = self.get_source(self.options['source'], self.default_source)
                params.insert(0, objs)
            self.module_run(*params)
            self.module_post()
        except KeyboardInterrupt:
            print('')
        except socket.timeout as e:
            self.error('Request timeout. Consider adjusting the global \'TIMEOUT\' option.')
        except Exception as e:
            if self.global_options['debug']:
                print('%s%s' % (framework.Colors.R, '-'*60))
                traceback.print_exc()
                print('%s%s' % ('-'*60, framework.Colors.N))
            self.error(e.__str__())
        finally:
            self.query('INSERT OR REPLACE INTO dashboard (module, runs) VALUES (\'%(x)s\', COALESCE((SELECT runs FROM dashboard WHERE module=\'%(x)s\')+1, 1))' % {'x': self.modulename})

    def module_pre(self):
        pass

    def module_run(self):
        pass

    def module_post(self):
        pass
