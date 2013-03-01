import framework
# unique to module
import re
import json

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', self.goptions['domain']['value'], 'yes', 'target IP address')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name':        'Maxmind GeoIP',
                     'Author':      'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Checks maxmind.com for a given host\'s location.',
                     'Comments': []
                     }
   
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.maxmind()

    def maxmind(self):
        verbose = self.options['verbose']['value']
        host    = self.options['host']['value']

        # request the scan
        details = [['Host Info', 'Value']]
        url = 'http://www.maxmind.com/geoip/city_isp_org/%s?demo=1' % (host)
        if verbose: self.output('URL for maxmind.com: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return

        # extract results
        try:
            content = resp.text
            results = json.loads(content)
        except Exception as e:
            self.error(e.__str__())
            return

        # store results
        if results:
            for key in results:
                details.append([key, results[key]])

        # Output the results in table format
        if len(details) > 1:
            self.table(details, True)
        else:
            self.output('maxmind.com was unable to determine the location of the host.')
