import cmd
import sqlite3
import os
import sys
import __builtin__

class base_cmd(cmd.Cmd):
    def __init__(self, params):
        cmd.Cmd.__init__(self)
        self.prompt = (params)
        self.options = {}
        self.dbfilename = __builtin__.dbfilename
        self.keyfile = __builtin__.keyfilename

    def default(self, line):
        print '[!] Unknown syntax: %s' % (line)

    def boolify(self, s):
        return {'true': True, 'false': False}[s.lower()]
    
    def autoconvert(self, s):
        for fn in (self.boolify, int, float):
            try: return fn(s)
            except ValueError: pass
            except KeyError: pass
        return s

    def add_host(self, host, address=''):
        conn = sqlite3.connect(self.dbfilename)
        c = conn.cursor()
        hosts = [x[0] for x in c.execute('SELECT host from hosts ORDER BY host').fetchall()]
        if not host in hosts:
            c.execute('INSERT INTO hosts VALUES (?, ?)', (host, address))
        conn.commit()
        conn.close()

    def add_contact(self, fname, lname, title, email=''):
        conn = sqlite3.connect(self.dbfilename)
        c = conn.cursor()
        contacts = c.execute('SELECT fname, lname, title from contacts ORDER BY fname').fetchall()
        if not (fname, lname, title) in contacts:
            c.execute('INSERT INTO contacts VALUES (?, ?, ?, ?)', (fname, lname, email, title))
        conn.commit()
        conn.close()

    def get_key(self, key_name, key_text='API Key'):
        if os.path.exists(self.keyfile):
            for line in open(self.keyfile):
                key, value = line.split('::')[0], line.split('::')[1]
                if key == key_name:
                    return value.strip()
        try: key = raw_input("Enter %s (blank to skip): " % (key_text))
        except KeyboardInterrupt:
            sys.stdout.write('\n')
            key = ''
        if key:
            file = open(self.keyfile, 'a')
            file.write('%s::%s\n' % (key_name, key))
            file.close()
        return key

    def unescape(self, s):
        import htmllib
        p = htmllib.HTMLParser(None)
        p.save_bgn()
        p.feed(s)
        return p.save_end()
    
    def sanitize(self, s):
        return ''.join([char for char in s if ord(char) >= 32 and ord(char) <= 126])

    def get_token(self, key_name):
        if os.path.exists(self.keyfile):
            for line in open(self.keyfile):
                key, value = line.split('::')[0], line.split('::')[1]
                if key == key_name:
                    return value.strip()
        return ''
    
    def add_token(self, key_name, key_value):
        keys = []
        if os.path.exists(self.keyfile):
            # remove the old key if duplicate
            for line in open(self.keyfile):
                key = line.split('::')[0]
                if key != key_name:
                    keys.append(line)
        keys = ''.join(keys)
        file = open(self.keyfile, 'w')
        file.write(keys)
        file.write('%s::%s\n' % (key_name, key_value))
        file.close()

    def do_exit(self, params):
        return True

    def do_set(self, params):
        options = params.split()
        if len(options) < 2: self.help_set()
        else:
            name = options[0]
            if name in self.options.keys():
                value = options[1]
                print '%s => %s' % (name, value)
                self.options[name] = self.autoconvert(value)
            else: self.default('Invalid option.')

    def help_set(self):
        print 'Usage: set <option> <value>'

    def do_options(self, params):
        print ''
        print 'Options:'
        print '========'
        for key in self.options.keys():
            value = self.options[key]
            print '%s %s %s' % (key.ljust(12), type(value).__name__.ljust(5), str(value))
        print ''

    def help_options(self):
        print 'Lists available options.'