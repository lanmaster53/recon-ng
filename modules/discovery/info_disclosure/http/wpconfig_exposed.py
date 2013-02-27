import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Exposed WordPress Config Page Checker',
                     'Author': 'Jay Turla (@shipcod3)',
                     'Description': 'Checks the hosts for possible exposed wp-config files which contains WordPress MySQL configuration.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                                  'Reference: http://feross.org/cmsploit/',
                                  'Google Dork: inurl:(wp-config.conf | wp-config.txt) ext:(conf | txt | config)',
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.wpconfig()
    
    def wpconfig(self):
        verbose = self.options['verbose']['value']
        
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return

        protocols = ['http', 'https']
        files = [
                 ('wp-config.txt'), ('wp-config.php~'), ('wp-config.php~'), ('#wp-config.php#'), ('wp-config.php.save'),
                 ('wp-config.php.swp'), ('wp-config.php.swo'), ('wp-config.php~'), ('wp-config.conf'),
                ]
        ############################################
        # wp-config.php~ == Vim, Gedit             # 
        # #wp-config.php# == Emacs                 #
        # wp-config.php.save == Nano               #
        # wp-config.php.swp == Vim (swap file)     #
        # wp-config.php.swo == Vim (swap file)     #
        ############################################
        cnt = 0
        for host in hosts:
            for proto in protocols:
                for filename in files:
                    url = '%s://%s/%s' % (proto, host, filename)
                    try:
                        resp = self.request(url, redirect=False)
                        code = resp.status_code
                    except KeyboardInterrupt:
                        print ''
                        return
                    except:
                        code = 'Error'
                    if code == 200 and '<?php' in resp.text:
                        self.alert('%s => %s. Possible exposed wp-config (WP MySQL config) page found!' % (url, code))
                        cnt += 1
                    else:
                        if verbose: self.output('%s => %s' % (url, code))
        self.output('%d Exposed wp-config pages found' % (cnt))
