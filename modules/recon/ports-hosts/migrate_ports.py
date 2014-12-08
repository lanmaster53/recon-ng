import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.info = {
            'Name': 'Ports to Hosts Data Migrator',
            'Author': 'Tim Tomes (@LaNMaSteR53)',
            'Description': 'Adds a new host for all the hostnames stored in the \'ports\' table.',
        }

    def module_run(self):
        # ip address regex
        regex = '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
        # get a list of hosts that are not ip addresses
        hosts = [x[0] for x in self.query('SELECT DISTINCT host FROM ports WHERE host IS NOT NULL') if not re.match(regex, x[0])]
        for host in hosts:
            self.add_hosts(host=host)
            self.output('\'%s\' successfully migrated.' % (host))
