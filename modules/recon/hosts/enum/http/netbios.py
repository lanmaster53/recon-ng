import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of target IP addresses')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'w3dt.net NetBIOS Lookup',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Attempts to retrieve NetBIOS information from the host using w3dt.net',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                 ]
                     }
   
    def module_run(self):
        verbose = self.options['verbose']['value']
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')
        if not hosts: return

        for host in hosts:
            # request NetBIOS info
            url = 'https://w3dt.net/tools/netbios/?submit=Scan!&clean_opt=1&host=%s' % (host)
            if verbose: self.output('URL: %s' % url)
            try: resp = self.request(url, timeout=60)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return

            # extract and present results
            content = resp.text
            result = re.search(r'<pre>(.+)--------------', content, re.S)
            if result:
                self.output("NetBIOS is enabled\n%s" % result.group(1))
            else:
                self.output('w3dt.net was unable to retrieve NetBIOS information from %s.' % host)
