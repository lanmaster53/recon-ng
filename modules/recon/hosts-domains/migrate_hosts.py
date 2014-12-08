import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL')
        self.info = {
            'Name': 'Hosts to Domains Data Migrator',
            'Author': 'Tim Tomes (@LaNMaSteR53)',
            'Description': 'Adds a new domain for all the hostnames stored in the \'hosts\' table.',
            'Comments': [
                'This modules considers that everything after the first element could contain other hosts besides the current. Therefore, hosts > 2 domains deep will create domains > 2 elements in length.',
            ]
        }

    def module_run(self, hosts):
        # ip address regex
        regex = '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
        # only migrate hosts that aren't ip addresses
        hosts = [x for x in hosts if not re.match(regex, x[0])]
        with open(self.data_path+'/suffixes.txt') as f:
            suffixes = [line.strip().lower() for line in f if len(line)>0 and line[0] is not '#']
        domains = self.hosts_to_domains(hosts, suffixes)
        for domain in domains:
            self.add_domains(domain=domain)
            self.output('\'%s\' successfully migrated.' % (domain))
