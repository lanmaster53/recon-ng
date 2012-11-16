import cmd
import sqlite3
import os
import sys
import textwrap
import socket
import datetime
import subprocess
import __builtin__
# prep python path for supporting modules
sys.path.append('./libs/')
import requests

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

    def add_host(self, host, address=''):
        host = self.sanitize(host)
        address = self.sanitize(address)
        return self.query(u'INSERT INTO hosts (host,address) SELECT "{0}","{1}" WHERE NOT EXISTS(SELECT * FROM hosts WHERE host="{0}" and address="{1}")'.format(host, address))

    def add_contact(self, fname, lname, title, email=''):
        fname = self.sanitize(fname)
        lname = self.sanitize(lname)
        title = self.sanitize(title)
        email = self.sanitize(email)
        return self.query(u'INSERT INTO contacts (fname,lname,title,email) SELECT "{0}","{1}","{2}","{3}" WHERE NOT EXISTS(SELECT * FROM contacts WHERE fname="{0}" and lname="{1}" and title="{2}" and email="{3}")'.format(fname, lname, title, email))

    def add_cred(self, username, password='', breach=''):
        username = self.sanitize(username)
        password = self.sanitize(password)
        breach = self.sanitize(breach)
        return self.query(u'INSERT INTO creds (username,password,breach) SELECT "{0}","{1}","{2}" WHERE NOT EXISTS(SELECT * FROM creds WHERE username="{0}" and password="{1}" and breach="{2}")'.format(username, password, breach))

    def query(self, params, return_results=True):
        # based on the do_ouput method
        if not params:
            self.help_query()
            return
        results = []
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        try: c.execute(params)
        except sqlite3.OperationalError as e:
            self.error('Invalid query. %s %s' % (type(e).__name__, e.message))
            return
        # a rowcount of -1 typically refers to a select statement
        if c.rowcount == -1:
            rows = c.fetchall()
            for row in rows:
                row = filter(None, row)
                if row:
                    results.append(row)
            if return_results: return results
            # print columns with headers if results are not returned
            delim = ' '
            columns = [column[0] for column in c.description]
            print delim.join(columns)
            print delim.join([self.ruler*len(column) for column in columns])
            for row in results:
                print delim.join(row)
            self.output('%d rows listed.' % (len(results)))
        # a rowcount of 1 == success and 0 == failure
        else:
            conn.commit()
            if return_results: return c.rowcount
            self.output('%d rows effected.' % (c.rowcount))
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

    def request(self, url, method='GET', payload={}, headers={}, cookies={}, redirect=True):
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
        return resp

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

    def help_shell(self):
        print 'Usage: [shell|!] <command>'
        print '...or just type a command at the prompt.'

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_set(self, text, *ignored):
        return [x for x in self.options.keys() if x.startswith(text)]