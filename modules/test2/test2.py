#!/usr/bin/python -tt

import cmd

class Module(cmd.Cmd):
    def __init__(self, params):
        self.prompt = (params)
        cmd.Cmd.__init__(self)

    def do_exit(self, params):
        return True

    def do_info(self, params):
        print 'This is the module 2\'s help.'

    def do_test(self, params):
        print 'test2: ' + params
    def help_test(self):
        print 'Echos back your input.'
        print 'Usage: test [string]'