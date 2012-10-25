import cmd

class base_cmd(cmd.Cmd):
    def __init__(self, params):
        cmd.Cmd.__init__(self)
        self.prompt = (params)
        self.options = {}

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