import cmd
import sqlite3
import __builtin__

class base_cmd(cmd.Cmd):
    def __init__(self, params):
        cmd.Cmd.__init__(self)
        self.prompt = (params)
        self.options = {}
        self.dbfilename = __builtin__.dbfilename

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
        c.execute('INSERT INTO hosts VALUES (?, ?)', (host, address))
        conn.commit()
        conn.close()

    def add_contact(self, fname, lname, title, email=''):
        conn = sqlite3.connect(self.dbfilename)
        c = conn.cursor()
        c.execute('INSERT INTO contacts VALUES (?, ?, ?, ?)', (fname, lname, email, title))
        conn.commit()
        conn.close()

    def do_exit(self, params):
        return True

    def do_set(self, params):
        name = params.split()[0]
        if name in self.options.keys():
            value = params.split()[1]
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