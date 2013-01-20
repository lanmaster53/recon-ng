import cmd
import sqlite3
import re
import os
import sys
import textwrap
import socket
import datetime
import subprocess
import __builtin__
# prep python path for supporting modules
sys.path.append('./libs/')
#import requests
import urllib
import urllib2
import json

class module(cmd.Cmd):
    def __init__(self, params):
        cmd.Cmd.__init__(self)
        self.prompt = (params)
        self.ruler = '-'
        self.spacer = '  '
        self.nohelp = '%s[!] No help on %%s%s' % (R, N)
        self.do_help.__func__.__doc__ = """Displays this menu"""
        try: self.do_run.__func__.__doc__ = """Runs the module"""
        except: pass
        self.doc_header = 'Commands (type [help|?] <topic>):'
        self.goptions = __builtin__.goptions
        self.options = {}

    #==================================================
    # OVERRIDE METHODS
    #==================================================

    def default(self, line):
        self.do_shell(line)
        self.log('Shell: %s' % (line))
        #self.log('Error: Unknown syntax: %s' % (line))
        #print '%s[!] Unknown syntax: %s%s' % (R, line, N)

    def precmd(self, line):
        self.log('Command: %s' % (line))
        return line

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

    def error(self, line):
        self.log('Error: %s' % (line))
        print '%s[!] %s%s' % (R, line, N)

    def output(self, line):
        print '%s[*]%s %s' % (B, N, line)

    def alert(self, line):
        print '%s[*]%s %s' % (G, N, line)

    def boolify(self, s):
        return {'true': True, 'false': False}[s.lower()]
    
    def autoconvert(self, s):
        if s.lower() in ['none', "''", '""']:
            return ''
        for fn in (self.boolify, int, float):
            try: return fn(s)
            except ValueError: pass
            except KeyError: pass
        return s

    def sanitize(self, obj, encoding='utf-8'):
        # checks if obj is unicode and converts if not
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding)
        return obj

    def add_host(self, host, address=None):
        host    = self.sanitize(host)
        address = self.sanitize(address)
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        try: c.execute(u'INSERT INTO hosts (host,address) SELECT ?, ? WHERE NOT EXISTS(SELECT * FROM hosts WHERE host=?)', (host, address, host))
        except sqlite3.OperationalError as e:
            self.error('Invalid query. %s %s' % (type(e).__name__, e.message))
            return
        conn.commit()
        conn.close()
        return c.rowcount

    def add_contact(self, fname, lname, title, email=None):
        fname = self.sanitize(fname)
        lname = self.sanitize(lname)
        title = self.sanitize(title)
        email = self.sanitize(email)
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        try: c.execute(u'INSERT INTO contacts (fname,lname,title,email) SELECT ?, ?, ?, ? WHERE NOT EXISTS(SELECT * FROM contacts WHERE fname=? and lname=? and title=?)', (fname, lname, title, email, fname, lname, title))
        except sqlite3.OperationalError as e:
            self.error('Invalid query. %s %s' % (type(e).__name__, e.message))
            return
        conn.commit()
        conn.close()
        return c.rowcount

    def add_cred(self, username, password=None, hashtype=None, leak=None):
        username = self.sanitize(username)
        password = self.sanitize(password)
        leak   = self.sanitize(leak)
        query = u'INSERT INTO creds (username,password,type,leak) SELECT ?, ?, ?, ? WHERE NOT EXISTS(SELECT * FROM creds WHERE username=? and password=? and type=? and leak=?)'
        if password:
            if self.is_hash(password):
                query = u'INSERT INTO creds (username,hash,type,leak) SELECT ?, ?, ?, ? WHERE NOT EXISTS(SELECT * FROM creds WHERE username=? and hash=? and type=? and leak=?)'
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        try: c.execute(query, (username, password, hashtype, leak, username, password, hashtype, leak))
        except sqlite3.OperationalError as e:
            self.error('Invalid query. %s %s' % (type(e).__name__, e.message))
            return
        conn.commit()
        conn.close()
        return c.rowcount

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

    def query(self, params, return_results=True):
        # based on the do_ouput method
        if not params:
            self.help_query()
            return
        if not return_results:
            # use sqlite to format and output the query
            cmd = 'sqlite3 -column -header %s "%s"' % (self.goptions['dbfilename'], params)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = p.communicate()
            if output:
                print ''
                print output.strip()
                print ''
            if error:
                self.error('Invalid query. %s' % error.strip())
                self.help_query()
                self.do_schema(None)
            return
        else:
            conn = sqlite3.connect(self.goptions['dbfilename'])
            c = conn.cursor()
            try: c.execute(params)
            except sqlite3.OperationalError as e:
                self.error('Invalid query. %s %s' % (type(e).__name__, e.message))
                return
            # a rowcount of -1 typically refers to a select statement
            if c.rowcount == -1:
                rows = c.fetchall()
                return rows
            # a rowcount of 1 == success and 0 == failure
            else:
                conn.commit()
                return c.rowcount
            conn.close()

    def manage_key(self, key_name, key_text):
        key = self.get_key_from_file(key_name)
        if not key:
            key = self.get_key_from_user(key_text)
            if not key:
                self.error('No %s.' % (key_text))
                return
            self.add_key_to_file(key_name, key)
        return key

    def get_key_from_file(self, key_name):
        if os.path.exists(self.goptions['keyfilename']):
            for line in open(self.goptions['keyfilename']):
                key, value = line.split('::')[0], line.split('::')[1]
                if key == key_name:
                    return value.strip()
        else:
            self.error('Invalid keyfile path or name.')
        return False

    def get_key_from_user(self, key_text='API Key'):
        try: key = raw_input("Enter %s (blank to skip): " % (key_text))
        except KeyboardInterrupt:
            print ''
            key = False
        return key

    def add_key_to_file(self, key_name, key_value):
        keys = []
        if os.path.exists(self.goptions['keyfilename']):
            # remove the old key if duplicate
            for line in open(self.goptions['keyfilename']):
                key = line.split('::')[0]
                if key != key_name:
                    keys.append(line)
        keys = ''.join(keys)
        try:
            file = open(self.goptions['keyfilename'], 'w')
            file.write(keys)
            file.write('%s::%s\n' % (key_name, key_value))
            file.close()
            self.output('\'%s\' key added to \'%s\'.' % (key_name, self.goptions['keyfilename']))
        except:
            self.error('Invalid keyfile path or name.')

    def unescape(self, s):
        import htmllib
        p = htmllib.HTMLParser(None)
        p.save_bgn()
        p.feed(s)
        return p.save_end()

    """def request(self, url, method='GET', payload={}, headers={}, cookies={}, redirect=True):
        # build kwargs for request call
        kwargs = {}
        headers['User-Agent'] = self.goptions['user-agent']
        kwargs['headers'] = headers                         # set custom headers
        kwargs['allow_redirects'] = redirect                # set redirect action
        kwargs['cookies'] = cookies                         # set custom cookies
        kwargs['verify'] = False                            # ignore SSL errors
        kwargs['timeout'] = self.goptions['socket_timeout'] # set socket connection timeout
        if self.goptions['proxy']:
            proxies = {'http': self.goptions['proxy_http'], 'https': self.goptions['proxy_https']}
            kwargs['proxies'] = proxies                     # set proxies
        # handle method and make request
        if method == 'GET':
            kwargs['params'] = payload                      # set get parameters for request
            resp = requests.get(url, **kwargs)
        elif method == 'POST':
            kwargs['data'] = payload                        # set post data for request
            resp = requests.post(url, **kwargs)
        else: raise Exception('Request method \'%s\' is not a supported method.' % (method))
        ##### BUG WARNING #####
        if self.goptions['proxy'] and url.lower().startswith('https'):
            self.alert('A known bug in the requests library prevents proper proxying of HTTPS requests.')
            self.alert('Enable support for invisible proxying (Burp) or set the \'proxy\' global option to \'False\'.')
            self.alert('This warning will disappear when the bug is fixed. I apologize for the inconvenience.')
        #######################
        return resp"""

    def request(self, url, method='GET', payload={}, headers={}, cookies={}, redirect=True):
        
        # set request arguments
        # process user-agent header
        headers['User-Agent'] = self.goptions['user-agent']
        # process payload
        payload = urllib.urlencode(payload)
        # process cookies
        if len(cookies.keys()) > 0:
            cookie_value = '; '.join('%s=%s' % (key, cookies[key]) for key in cookies.keys())
            headers['Cookie'] = cookie_value
        # process socket timeout
        socket.setdefaulttimeout(self.goptions['socket_timeout'])
        
        # set handlers
        handlers = [] #urllib2.HTTPHandler(debuglevel=1)
        # process redirect and add handler
        if redirect == False:
            handlers.append(NoRedirectHandler)
        # process proxies and add handler
        if self.goptions['proxy']:
            proxies = {'http': self.goptions['proxy_http'], 'https': self.goptions['proxy_https']}
            handlers.append(urllib2.ProxyHandler(proxies))
        
        # install opener
        opener = urllib2.build_opener(*handlers)
        urllib2.install_opener(opener)
        
        # process method and make request
        if method == 'GET':
            req = urllib2.Request('%s?%s' % (url, payload), headers=headers)
        elif method == 'POST':
            req = urllib2.Request(url, data=payload, headers=headers)
        else:
            raise Exception('Request method \'%s\' is not a supported method.' % (method))
        try:
            resp = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            resp = e
        
        # build response object
        # creates anonymous inline object
        response = lambda: None
        response.text = resp.read()
        response.status_code = resp.getcode()
        try:
            response.json = json.loads(response.text)
        except:
            pass
        return response

    def log(self, str):
        logfile = open(self.goptions['logfilename'], 'ab')
        logfile.write('[%s] %s\n' % (datetime.datetime.now(), str))
        logfile.close()

    #==================================================
    # FRAMEWORK METHODS
    #==================================================

    def do_exit(self, params):
        """Exits current prompt level"""
        return True

    def do_info(self, params):
        """Displays module information"""
        pattern = '%s%s:'
        print ''
        print pattern % (self.spacer, 'Name')
        print pattern[:-1] % (self.spacer*2, self.info['Name'])
        print ''
        print pattern % (self.spacer, 'Author')
        print pattern[:-1] % (self.spacer*2, self.info['Author'])
        print ''
        print pattern % (self.spacer, 'Description')
        print pattern[:-1] % (self.spacer*2, textwrap.fill(self.info['Description'], 100, initial_indent='', subsequent_indent=self.spacer*2))
        print ''
        print pattern % (self.spacer, 'Options')
        self.do_options('info')
        if self.info['Comments']:
            print pattern % (self.spacer, 'Comments')
            for comment in self.info['Comments']:
                print pattern[:-1] % (self.spacer*2, textwrap.fill(comment, 100, initial_indent='', subsequent_indent=self.spacer*2))
            print ''

    def do_options(self, params):
        """Lists options"""
        spacer = self.spacer
        if params == 'info':
            spacer = self.spacer*2
        if self.options.keys():
            pattern = '%s%%s\t%%s\t%%s' % (spacer)
            key_len = len(max(self.options.keys(), key=len))
            print ''
            print pattern % ('Name'.ljust(key_len), 'Type'.ljust(4), 'Current Value')
            print pattern % (self.ruler*key_len, self.ruler*4, self.ruler*13)
            for key in sorted(self.options.keys()):
                value = self.options[key]
                print pattern % (key.ljust(key_len), type(value).__name__[:4].lower().ljust(4), str(value))
            print ''
        else:
            if params != 'info': print ''
            print '%sNo options available for this module.' % (spacer)
            print ''

    def do_set(self, params):
        """Sets module options"""
        options = params.split()
        if len(options) < 2: self.help_set()
        else:
            name = options[0]
            if name in self.options.keys():
                value = ' '.join(options[1:])
                print '%s => %s' % (name, value)
                self.options[name] = self.autoconvert(value)
            else: self.error('Invalid option.')

    def do_schema(self, params):
        """Displays the database schema"""
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        c.execute('SELECT name FROM sqlite_master WHERE type=\'table\'')
        tables = [x[0] for x in c.fetchall()]
        for table in tables:
            print ''
            print '%s+---------------------+' % (self.spacer)
            print '%s| %s |' % (self.spacer, table.center(19))
            print '%s+---------------------+' % (self.spacer)
            c.execute("PRAGMA table_info(%s)" % (table))
            columns = [(x[1],x[2]) for x in c.fetchall()]
            for column in columns:
                print '%s| %s | %s |' % (self.spacer, column[0].ljust(8), column[1].center(8))
            print '%s+---------------------+' % (self.spacer)
        print ''

    def do_query(self, params):
        """Queries the database"""
        self.query(params, False)

    def do_shell(self, params):
        """Executed shell commands"""
        proc = subprocess.Popen(params, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        self.output('Command: %s' % (params))
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        if stdout: sys.stdout.write('%s%s%s' % (O, stdout, N))
        if stderr: sys.stdout.write('%s%s%s' % (R, stderr, N))

    #==================================================
    # HELP METHODS
    #==================================================

    def help_set(self):
        print 'Usage: set <option> <value>'
        self.do_options(None)

    def help_query(self):
        print 'Usage: query <sql>'
        print ''
        print 'SQL Examples:'
        print '%s%s' % (self.spacer, 'SELECT <columns|*> FROM <tablename>')
        print '%s%s' % (self.spacer, 'SELECT <columns|*> FROM <tablename> WHERE <columnname>=<string>')

    def help_shell(self):
        print 'Usage: [shell|!] <command>'
        print '...or just type a command at the prompt.'

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_set(self, text, *ignored):
        return [x for x in self.options.keys() if x.startswith(text)]

#=================================================
# CUSTOM CLASSES & WRAPPERS
#=================================================

class NoRedirectHandler(urllib2.HTTPRedirectHandler):

    def http_error_302(self, req, fp, code, msg, headers):
        pass

    http_error_301 = http_error_303 = http_error_307 = http_error_302

class resp_obj:

    text = None
    status_code = None
    json = None
