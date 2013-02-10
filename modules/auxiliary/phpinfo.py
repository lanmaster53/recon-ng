import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.classify = 'active'
        self.info = {
                     'Name': 'phpinfo() Page Checker',
                     'Author': 'Jay Turla (@shipcod3)',
                     'Classification': '%s Reconnaissance' % (self.classify.title()),
                     'Description': 'Checks the hosts for phpinfo() page which outputs information about PHP configuration',
                     'Comments': [
                                  'Source options: db, <hostname>, <path/to/infile>',
                                  'Reference: http://php.net/manual/en/function.phpinfo.php',
                                  'Google Dorks: inurl:phpinfo.php',
                                  'inurl:test.php + intitle:phpinfo()',
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.check_for_phpinfo()
    
    def check_for_phpinfo(self):
        verbose = self.options['verbose']['value']
        
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return

        # check all hosts for phpinfo() page under phpinfo.php and test.php files
        protocols = ['http', 'https']
        files = [('phpinfo.php'), ('test.php')]
        cnt = 0
        for host in hosts:
            for proto in protocols:
					for (filename) in files:
						url = '%s://%s/%s' % (proto, host, filename)
						try:
							resp = self.request(url, redirect=False)
							code = resp.status_code
						except KeyboardInterrupt:
							print ''
							return
						except:
							code = 'Error'
						if code == 200 and 'phpinfo()' in resp.text:
							self.alert('%s => %s. phpinfo() page found!' % (url, code))
							cnt += 1
						else:
							if verbose: self.output('%s => %s' % (url, code))
        self.output('%d phpinfo() pages found' % (cnt))
