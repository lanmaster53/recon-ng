import cmd
import sqlite3
import os
import sys
import urllib2
import socket
import datetime
import subprocess
import __builtin__

class base_cmd(cmd.Cmd):
    def __init__(self, params):
        cmd.Cmd.__init__(self)
        self.prompt = (params)
        self.nohelp = '%s[!] No help on %%s%s' % (R, N)
        self.do_help.__func__.__doc__ = """Displays this menu"""
        self.do_info.__func__.__doc__ = """Displays module info"""
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
        self.log('%s => Shell' % (line))
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

    def add_host(self, host, addr=''):
        host = self.sanitize(host)
        addr = self.sanitize(addr)
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        hosts = [x[0] for x in c.execute('SELECT host from hosts ORDER BY host').fetchall()]
        if not host in hosts:
            c.execute('INSERT INTO hosts VALUES (?, ?)', (host, addr))
        conn.commit()
        conn.close()

    def add_contact(self, fname, lname, title, email='', status=''):
        fname = self.sanitize(fname)
        lname = self.sanitize(lname)
        title = self.sanitize(title)
        email = self.sanitize(email)
        status = self.sanitize(status)
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        contacts = c.execute('SELECT fname, lname, title from contacts ORDER BY fname').fetchall()
        if not (fname, lname, title) in contacts:
            c.execute('INSERT INTO contacts VALUES (?, ?, ?, ?, ?)', (fname, lname, email, status, title))
        conn.commit()
        conn.close()

    def manage_key(self, key_name, key_text=''):
        key = self.get_key_from_file(key_name)
        if not key:
            key = self.get_key_from_user(key_text)
            if not key:
                self.error('No API Key.')
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
            sys.stdout.write('\n')
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
            print '[*] \'%s\' key added to \'%s\'.' % (key_name, self.goptions['keyfilename'])
        except:
            self.error('Invalid keyfile path or name.')

    def unescape(self, s):
        import htmllib
        p = htmllib.HTMLParser(None)
        p.save_bgn()
        p.feed(s)
        return p.save_end()

    # proxy currently only works for http connections, not https
    def urlopen(self, req):
        req.add_header('User-Agent', self.goptions['user-agent'])
        if self.goptions['proxy']:
            opener = urllib2.build_opener(AvoidRedirectHandler, urllib2.ProxyHandler({'http': self.goptions['proxyhost']}))
            socket.setdefaulttimeout(8)
        else: opener = urllib2.build_opener(AvoidRedirectHandler)
        urllib2.install_opener(opener)
        return urllib2.urlopen(req)

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

    def do_options(self, params):
        """Lists options"""
        if self.options.keys():
            pattern = '%s\t%s\t%s'
            key_len = len(max(self.options.keys(), key=len))
            print ''
            print pattern % ('Name'.ljust(key_len), 'Type'.ljust(4), 'Current Value')
            print pattern % ('='*key_len, '='*4, '='*13)
            for key in sorted(self.options.keys()):
                value = self.options[key]
                print pattern % (key.ljust(key_len), type(value).__name__[:4].lower().ljust(4), str(value))
            print ''
        else:
            print '[*] No options available for this module.'

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

    def do_query(self, params, return_results=False):
        # based on the do_ouput method
        """Queries the database"""
        if not params:
            self.help_query()
            return
        results = []
        if not params.lower().startswith('select'):
            self.error('SELECT statements only.')
        else:
            conn = sqlite3.connect(self.goptions['dbfilename'])
            c = conn.cursor()
            try: rows = c.execute(params).fetchall()
            except sqlite3.OperationalError as e:
                self.error('Invalid query. %s %s' % (type(e).__name__, e.message))
                rows = []
            for row in rows:
                row = filter(None, row)
                if row:
                    results.append(row)
            conn.close()
        if return_results: return results
        # print columns with headers if results are not returned
        delim = ' '
        columns = [column[0] for column in c.description]
        print delim.join(columns)
        print delim.join(['='*len(column) for column in columns])
        for row in results:
            print delim.join(row)
        print '[*] %d rows listed.' % (len(results))

    def do_shell(self, params):
        """Executed shell commands"""
        proc = subprocess.Popen(params, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        print '[*] Command: %s' % (params)
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

class AvoidRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        pass
    http_error_301 = http_error_303 = http_error_307 = http_error_302