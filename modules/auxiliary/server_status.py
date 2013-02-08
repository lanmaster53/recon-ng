import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.classify = 'active'
        self.info = {
                     'Name': 'Apache Server-Status Page Scanner',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Classification': '%s Reconnaissance' % (self.classify.title()),
                     'Description': 'Checks hosts for a \'server-status\' page.',
                     'Comments': [
                                  'Source options: db, <hostname>, <path/to/infile>',
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
        
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return

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
                    return
                except:
                    code = 'Error'
                if code == 200 and '>Apache Status<' in resp.text:
                    self.alert('%s => %s. Possible Apache Status page found!' % (url, code))
                    cnt += 1
                else:
                    if verbose: self.output('%s => %s' % (url, code))
        self.output('%d Server Status pages found.' % (cnt))