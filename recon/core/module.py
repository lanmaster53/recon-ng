from __future__ import print_function
import cookielib
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
import urllib
import urlparse
# framework libs
from recon.core import framework

#=================================================
# MODULE CLASS
#=================================================

class BaseModule(framework.Framework):

    def __init__(self, params, query=None):
        framework.Framework.__init__(self, params)
        self.options = framework.Options()
        # register a data source option if a default query is specified in the module
        if self.meta.get('query'):
            self._default_source = self.meta.get('query')
            self.register_option('source', 'default', True, 'source of input (see \'show info\' for details)')
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
                    self.error('\'%s\' key not set. %s module will likely fail at runtime. See \'keys add\'.' % (key, self._modulename.split('/')[-1]))
        self._reload = 0

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def _migrate_key(self, key):
        '''migrate key from old .dat file'''
        key_path = os.path.join(self._home, 'keys.dat')
        if os.path.exists(key_path):
            try:
                key_data = json.loads(open(key_path, 'rb').read())
                if key_data.get(key):
                    self.add_key(key, key_data.get(key))
            except:
                self.error('Corrupt key file. Manual migration of \'%s\' required.' % (key))

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

    #==================================================
    # OPTIONS METHODS
    #==================================================

    def _get_source(self, params, query=None):
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
        if not sources:
            raise framework.FrameworkException('Source contains no input.')
        return sources

    #==================================================
    # 3RD PARTY API METHODS
    #==================================================

    def get_explicit_oauth_token(self, resource, scope, authorize_url, access_url):
        token_name = resource+'_token'
        token = self.get_key(token_name)
        if token:
            return token
        import urllib
        import webbrowser
        import socket
        client_id = self.get_key(resource+'_api')
        client_secret = self.get_key(resource+'_secret')
        port = 31337
        redirect_uri = 'http://localhost:%d' % (port)
        payload = {'response_type': 'code', 'client_id': client_id, 'scope': scope, 'state': self.get_random_str(40), 'redirect_uri': redirect_uri}
        authorize_url = '%s?%s' % (authorize_url, urllib.urlencode(payload))
        w = webbrowser.get()
        w.open(authorize_url)
        # open a socket to receive the access token callback
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.listen(1)
        conn, addr = sock.accept()
        data = conn.recv(1024)
        conn.sendall('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><head><title>Recon-ng</title></head><body>Response received. Return to Recon-ng.</body></html>')
        conn.close()
        # process the received data
        if 'error_description' in data:
            self.error(urllib.unquote_plus(re.search('error_description=([^\s&]*)', data).group(1)))
            return None
        authorization_code = re.search('code=([^\s&]*)', data).group(1)
        payload = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': redirect_uri, 'client_id': client_id, 'client_secret': client_secret}
        resp = self.request(access_url, method='POST', payload=payload)
        if 'error' in resp.json:
            self.error(resp.json['error_description'])
            return None
        access_token = resp.json['access_token']
        self.add_key(token_name, access_token)
        return access_token

    def get_twitter_oauth_token(self):
        token_name = 'twitter_token'
        token = self.get_key(token_name)
        if token:
            return token
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

    def get_pwnedlist_leak(self, leak_id):
        # check if the leak has already been retrieved
        leak = self.query('SELECT * FROM leaks WHERE leak_id=?', (leak_id,))
        if leak:
            leak = dict(zip([x[0] for x in self.get_columns('leaks')], leak[0]))
            del leak['module']
            return leak
        # set up the API call
        key = self.get_key('pwnedlist_api')
        secret = self.get_key('pwnedlist_secret')
        url = 'https://api.pwnedlist.com/api/1/leaks/info'
        base_payload = {'leakId': leak_id}
        payload = self.build_pwnedlist_payload(base_payload, 'leaks.info', key, secret)
        # make the request
        resp = self.request(url, payload=payload)
        if resp.status_code != 200:
            self.error('Error retrieving leak data.\n%s' % (resp.text))
            return
        leak = resp.json['leaks'][0]
        # normalize the leak for storage
        normalized_leak = {}
        for item in leak:
            value = leak[item]
            if type(value) == list:
                value = ', '.join(value)
            normalized_leak[item] = value
        return normalized_leak

    def search_twitter_api(self, payload, limit=False):
        headers = {'Authorization': 'Bearer %s' % (self.get_twitter_oauth_token())}
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        results = []
        while True:
            resp = self.request(url, payload=payload, headers=headers)
            if limit:
                # app auth rate limit for search/tweets is 450/15min
                time.sleep(2)
            jsonobj = resp.json
            for item in ['error', 'errors']:
                if item in jsonobj:
                    raise framework.FrameworkException(jsonobj[item])
            results += jsonobj['statuses']
            if 'next_results' in jsonobj['search_metadata']:
                max_id = urlparse.parse_qs(jsonobj['search_metadata']['next_results'][1:])['max_id'][0]
                payload['max_id'] = max_id
                continue
            break
        return results

    def search_shodan_api(self, query, limit=0):
        api_key = self.get_key('shodan_api')
        url = 'https://api.shodan.io/shodan/host/search'
        payload = {'query': query, 'key': api_key}
        results = []
        cnt = 0
        page = 1
        self.verbose('Searching Shodan API for: %s' % (query))
        while True:
            time.sleep(1)
            resp = self.request(url, payload=payload)
            if resp.json == None:
                raise framework.FrameworkException('Invalid JSON response.\n%s' % (resp.text))
            if 'error' in resp.json:
                raise framework.FrameworkException(resp.json['error'])
            if not resp.json['matches']:
                break
            # add new results
            results.extend(resp.json['matches'])
            # increment and check the limit
            cnt += 1
            if limit == cnt:
                break
            # next page
            page += 1
            payload['page'] = page
        return results

    def search_bing_api(self, query, limit=0):
        url = 'https://api.cognitive.microsoft.com/bing/v7.0/search'
        payload = {'q': query, 'count': 50, 'offset': 0, 'responseFilter': 'WebPages'}
        headers = {'Ocp-Apim-Subscription-Key': self.get_key('bing_api')}
        results = []
        cnt = 0
        self.verbose('Searching Bing API for: %s' % (query))
        while True:
            resp = self.request(url, payload=payload, headers=headers)
            if resp.json == None:
                raise framework.FrameworkException('Invalid JSON response.\n%s' % (resp.text))
            #elif 'error' in resp.json:
            elif resp.status_code == 401:
                raise framework.FrameworkException('%s: %s' % (resp.json['statusCode'], resp.json['message']))
            # add new results, or if there's no more, return what we have...
            if 'webPages' in resp.json:
                results.extend(resp.json['webPages']['value'])
            else:
                return results
            # increment and check the limit
            cnt += 1
            if limit == cnt:
                break
            # check for more pages
            # https://msdn.microsoft.com/en-us/library/dn760787.aspx
            if payload['offset'] > (resp.json['webPages']['totalEstimatedMatches'] - payload['count']):
                break
            # set the payload for the next request
            payload['offset'] += payload['count']
        return results

    def search_google_api(self, query, limit=0):
        api_key = self.get_key('google_api')
        cse_id = self.get_key('google_cse')
        url = 'https://www.googleapis.com/customsearch/v1'
        payload = {'alt': 'json', 'prettyPrint': 'false', 'key': api_key, 'cx': cse_id, 'q': query}
        results = []
        cnt = 0
        self.verbose('Searching Google API for: %s' % (query))
        while True:
            resp = self.request(url, payload=payload)
            if resp.json == None:
                raise framework.FrameworkException('Invalid JSON response.\n%s' % (resp.text))
            # add new results
            if 'items' in resp.json:
                results.extend(resp.json['items'])
            # increment and check the limit
            cnt += 1
            if limit == cnt:
                break
            # check for more pages
            if not 'nextPage' in resp.json['queries']:
                break
            payload['start'] = resp.json['queries']['nextPage'][0]['startIndex']
        return results

    def search_github_api(self, query):
        self.verbose('Searching Github for: %s' % (query))
        results = self.query_github_api(endpoint='/search/code', payload={'q': query})
        # reduce the nested lists of search results and return
        results = [result['items'] for result in results]
        return [x for sublist in results for x in sublist]

    def query_github_api(self, endpoint, payload={}, options={}):
        opts = {'max_pages': None}
        opts.update(options)
        headers = {'Authorization': 'token %s' % (self.get_key('github_api'))}
        base_url = 'https://api.github.com'
        url = base_url + endpoint
        results = []
        page = 1
        while True:
            # Github rate limit is 30 requests per minute
            time.sleep(2) # 60s / 30r = 2s/r
            payload['page'] = page
            resp = self.request(url=url, headers=headers, payload=payload)
            # check for errors
            if resp.status_code != 200:
                # skip 404s returned for no results
                if resp.status_code != 404:
                    self.error('Message from Github: %s' % (resp.json['message']))
                break
            # some APIs return lists, and others a single dictionary
            method = 'extend'
            if type(resp.json) == dict:
                method = 'append'
            getattr(results, method)(resp.json)
            # paginate
            if 'link' in resp.headers and 'rel="next"' in resp.headers['link'] and (opts['max_pages'] is None or page < opts['max_pages']):
                page += 1
                continue
            break
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

    def show_inputs(self):
        if hasattr(self, '_default_source'):
            try:
                self._validate_options()
                inputs = self._get_source(self.options['source'], self._default_source)
                self.table([[x] for x in inputs], header=['Module Inputs'])
            except Exception as e:
                self.output(e.__str__())
        else:
            self.output('Source option not available for this module.')

    def show_source(self):
        for path in [os.path.join(x, 'modules', self._modulename) +'.py' for x in (self.app_path, self._home)]:
            if os.path.exists(path):
                filename = path
        with open(filename) as f:
            content = f.readlines()
            nums = [str(x) for x in range(1, len(content)+1)]
            num_len = len(max(nums, key=len))
            for num in nums:
                print('%s|%s' % (num.rjust(num_len), content[int(num)-1]), end='')

    def show_info(self):
        self.meta['path'] = os.path.join('modules', self._modulename) + '.py'
        print('')
        # meta info
        for item in ['name', 'path', 'author', 'version']:
            if self.meta.get(item):
                print('%s: %s' % (item.title().rjust(10), self.meta[item]))
        # required keys
        if self.meta.get('required_keys'):
            print('%s: %s' % ('keys'.title().rjust(10), ', '.join(self.meta.get('required_keys'))))
        print('')
        # description
        if 'description' in self.meta:
            print('Description:')
            print('%s%s' % (self.spacer, textwrap.fill(self.meta['description'], 100, subsequent_indent=self.spacer)))
            print('')
        # options
        print('Options:', end='')
        self.show_options()
        # sources
        if hasattr(self, '_default_source'):
            print('Source Options:')
            print('%s%s%s' % (self.spacer, 'default'.ljust(15), self._default_source))
            print('%s%sstring representing a single input' % (self.spacer, '<string>'.ljust(15)))
            print('%s%spath to a file containing a list of inputs' % (self.spacer, '<path>'.ljust(15)))
            print('%s%sdatabase query returning one column of inputs' % (self.spacer, 'query <sql>'.ljust(15)))
            print('')
        # comments
        if 'comments' in self.meta:
            print('Comments:')
            for comment in self.meta['comments']:
                prefix = '* '
                if comment.startswith('\t'):
                    prefix = self.spacer+'- '
                    comment = comment[1:]
                print('%s%s' % (self.spacer, textwrap.fill(prefix+comment, 100, subsequent_indent=self.spacer)))
            print('')

    def show_globals(self):
        self.show_options(self._global_options)

    #==================================================
    # COMMAND METHODS
    #==================================================

    def do_reload(self, params):
        '''Reloads the current module'''
        self._reload = 1
        return True

    def do_run(self, params):
        '''Runs the module'''
        try:
            self._summary_counts = {}
            self._validate_options()
            pre = self.module_pre()
            params = [pre] if pre is not None else []
            # provide input if a default query is specified in the module
            if hasattr(self, '_default_source'):
                objs = self._get_source(self.options['source'], self._default_source)
                params.insert(0, objs)
            self.module_run(*params)
            self.module_post()
        except KeyboardInterrupt:
            print('')
        except Exception:
            self.print_exception()
        finally:
            # print module summary
            if self._summary_counts:
                self.heading('Summary', level=0)
                for table in self._summary_counts:
                    new = self._summary_counts[table][0]
                    cnt = self._summary_counts[table][1]
                    if new > 0:
                        method = getattr(self, 'alert')
                    else:
                        method = getattr(self, 'output')
                    method('%d total (%d new) %s found.' % (cnt, new, table))
                self._summary_counts = {}
            # update the dashboard
            self.query('INSERT OR REPLACE INTO dashboard (module, runs) VALUES (\'%(x)s\', COALESCE((SELECT runs FROM dashboard WHERE module=\'%(x)s\')+1, 1))' % {'x': self._modulename})

    def module_pre(self):
        pass

    def module_run(self):
        pass

    def module_post(self):
        pass
