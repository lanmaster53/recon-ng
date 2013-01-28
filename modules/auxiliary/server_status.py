import framework
# unique to module
import os

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option(self.options, 'source', 'database', 'yes', 'source of module input')
        self.register_option(self.options, 'verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Apache Server-Status Page Scanner',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Checks all of the hosts stored in the database for a \'server-status\' page.',
                     'Comments': [
                                  'Source options: database, <hostname>, <path/to/infile>',
                                  'http://blog.sucuri.net/2012/10/popular-sites-with-apache-server-status-enabled.html',
                                  'http://httpd.apache.org/docs/2.2/mod/mod_status.html',
                                  'Google dork: intitle:"Apache Status" inurl:"server-status"'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.check_for_status()
    
    def check_for_status(self):
        verbose = self.options['verbose']['value']
        
        # handle sources
        source = self.options['source']['value']
        if source == 'database':
            hosts = [x[0] for x in self.query('SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')]
            if len(hosts) == 0:
                self.error('No hosts in the database.')
                return
        elif os.path.exists(source): hosts = open(source).read().split()
        else: hosts = [source]

        # check all hosts for server-status pages
        protocols = ['http', 'https']
        cnt = 0
        for host in hosts:
            for proto in protocols:
                url = '%s://%s/server-status/' % (proto, host)
                try:
                    resp = self.request(url, redirect=False)
                    code = resp.status_code
                except KeyboardInterrupt:
                    print ''
                    code = None
                    return
                except:
                    code = 'Error'
                if code == 200:
                    self.alert('%s => %s. Possible server status page found!' % (url, code))
                    cnt += 1
                else:
                    if verbose: self.output('%s => %s' % (url, code))
        self.output('%d Server Status pages found.' % (cnt))