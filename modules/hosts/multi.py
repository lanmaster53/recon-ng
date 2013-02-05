import framework
# unique to module
import sys
from os import path

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.info = {
                     'Name': 'Multi Hosts Module Runner',
                     'Author': 'Ethan Robish',
                     'Description': 'Provides a way to run multiple modules with one command.',
                     'Comments': []
                     }

        # find the name of this module
        self_name = path.basename(__file__).split('.')[0]
        # find the name of this module's prefix (eg. hosts_)
        prefix = params[params.find('[')+1:params.find(']')].replace(self_name, '')

        # find all modules that share this module's prefix
        self.all_modules = {}
        for name, module in sys.modules.items():
            if name.startswith(prefix) and name != prefix + self_name:
                self.all_modules[name] = module.Module('')

        # enable all modules by default
        self.enabled_module_names = set()
        self.do_enable('all')

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        prev_num_hosts = len(self.query('SELECT * FROM hosts'))
        num_errors = 0
        
        for name in self.enabled_module_names:
            self.output('-'*60)
            self.output('Running %s' % name)
            self.output('-'*60)
            self.all_modules[name].options = self.options
            try:
                self.all_modules[name].do_run('')
            #except KeyboardInterrupt:
            #    self.error('Keyboard interrupt encountered.')
            #    resp = raw_input('Do you wish to run the remainder of the modules? [Y/n]: ')
            #    if resp and resp.lower()[0] != 'y':
            #        break
            except:
                num_errors += 1
                self.error('%s encountered a fatal error!' % name)

        curr_num_hosts = len(self.query('SELECT * FROM hosts'))
        num_new_hosts = curr_num_hosts - prev_num_hosts

        self.output('-'*60)
        if num_errors > 0:
            self.error('%d modules encountered errors' % num_errors)

        self.alert('%d modules ran and %d NEW hosts found!' % (len(self.enabled_module_names) - num_errors, num_new_hosts))

    def do_enable(self, module):
        '''Enable a module to run'''
        if module == 'all':
            for name in self.all_modules:
                self.do_enable(name)
            return

        # do nothing if the module is already enabled
        if module in self.enabled_module_names:
            return

        self.enabled_module_names.add(module)
        self.register_all_options()

    def do_disable(self, module):
        '''Disable a module from running'''
        if module == 'all':
            for name in self.all_modules:
                self.do_disable(name)
            return

        # do nothing if the module is already disabled
        if module not in self.enabled_module_names:
            return

        self.enabled_module_names.remove(module)
        self.register_all_options()

    def do_modules(self, param):
        '''Shows all the modules available and their current states'''
        data = [['Module Name', 'Status']]
        for name in self.all_modules:
            if name in self.enabled_module_names:
                data.append([name, 'Enabled'])
            else:
                data.append([name, 'Disabled'])

        self.table(data, header=True)

    def register_all_options(self):
        '''Sets the current module's options to be the aggreate of all the enabled modules' options'''
        new_options = {}
        for mod_name in self.enabled_module_names:
            for opt_name, opt in self.all_modules[mod_name].options.items():
                # add the option if it doesn't already exist
                if opt_name not in new_options:
                    self.register_option(opt_name, opt['value'], opt['reqd'], opt['desc'], new_options)
                    
                    # preserve the option's old value, if it had one
                    if opt_name in self.options:
                        new_options[opt_name]['value'] = self.options[opt_name]['value']

        self.options = new_options

    def help_enable(self):
        print 'Usage: enable <module>|all'

    def help_disable(self):
        print 'Usage: disable <module>|all'

    def complete_enable(self, text, *ignored):
        return [x for x in self.all_modules if x not in self.enabled_module_names and x.startswith(text)]

    def complete_disable(self, text, *ignored):
        return [x for x in self.all_modules if x in self.enabled_module_names and x.startswith(text)]
