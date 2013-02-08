import framework
# unique to module
import re
import urllib2

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'XSSed Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks XSSed site for XSS records for given target and displays first 20 hits.',
                     'Comments': []
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.xssed()

    def xssed(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']

        url = 'http://xssed.com/search?key=%s' % (domain)
        if verbose: self.output('URL for XSSED.com: %s' % url)
        try: resp = urllib2.urlopen(url)
        except KeyboardInterrupt:
            print ''
        except Exception as e:
            self.error(e.__str__())
            return
        
        content = resp.read()

        # Find if there are any results for the domain search
        results = re.findall(r"Results for.*", content)
        if results:
            rows = re.split('<br>', str(results))
            for row in rows:
                finding = re.findall(r"mirror/([0-9]+)/.+blank\\'>(.+?)</a>", row)
                if finding:
                    # Now go fetch and parse the specific page for this item
                    urlDetail = 'http://xssed.com/mirror/%s/' % finding[0][0]
                    try: respDetail = urllib2.urlopen(urlDetail)
                    except KeyboardInterrupt:
                        print ''
                    except Exception as e:
                        self.error(e.__str__())
                    if not respDetail: return
                    
                    # Parse the response and get the details
                    details = []
                    for line in respDetail.readlines():
                        if "row3" in line:
                            try: 
                                a = re.search(r'">(.+)</th', line.strip())
                                details.append(a.group(1))
                            except: pass
                    # Output the results
                    status = re.search(r';([UNFIXED]+)$',details[2])
                    self.output(details[4])
                    self.output('  '+details[7])
                    self.output('  '+details[0].replace('&nbsp;', ' '))
                    self.output('  '+details[1].replace('&nbsp;', ' '))
                    self.output('  '+details[5])
                    self.output('  STATUS: '+status.group(1))
                    self.error(' ')                    
        else:
            self.output('No results found')
        
