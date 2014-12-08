import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL')
        self.info = {
            'Name': 'Contacts to Domains Data Migrator',
            'Author': 'Tim Tomes (@LaNMaSteR53)',
            'Description': 'Adds a new domain for all the hostnames associated with email addresses stored in the \'contacts\' table.',
            'Comments': [
                'This modules considers that everything after the first element could contain other hosts besides the current. Therefore, hosts > 2 domains deep will create domains > 2 elements in length.',
            ]
        }

    def module_run(self, emails):
        # extract the host portion of each email address
        hosts = [x.split('@')[1] for x in emails]
        with open(self.data_path+'/suffixes.txt') as f:
            suffixes = [line.strip().lower() for line in f if len(line)>0 and line[0] is not '#']
        domains = self.hosts_to_domains(hosts, suffixes)
        for domain in domains:
            self.add_domains(domain=domain)
            self.output('\'%s\' successfully migrated.' % (domain))
