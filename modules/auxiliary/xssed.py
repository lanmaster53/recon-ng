import framework
# unique to module
import re
from bs4 import BeautifulSoup
import urllib

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'XSSed Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks XSSed site for XSS records for given target.',
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
        if verbose: self.output('URL: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
        except Exception as e:
            self.error(e.__str__())
        if not resp: exit(0)
        
        content = resp.text

        # Find if there are any results for the domain search
        results = re.findall(r"Results for.*", content)
        if results:
            rows = re.split('<br>', str(results))
            for row in rows:
                finding = re.findall(r"mirror/([0-9]+)/.+blank\\'>(.+?)</a>", row)
                if finding:
                    # Now go fetch and parse the specific page for this item
                    urlDetail = 'http://xssed.com/mirror/%s/' % finding[0][0]
                    try: respDetail = self.request(urlDetail)
                    except KeyboardInterrupt:
                        print ''
                    except Exception as e:
                        self.error(e.__str__())
                    if not respDetail: exit(0)
                    
                    #parse the response and get the details
                    soup = BeautifulSoup(respDetail.text)
                    data = [a.get_text() for a in soup.findAll("th", {"class":"row3"})]
                    self.output(data[8])
                    self.output('  '+data[0]+'; '+data[1]+'; '+data[3]+'; '+data[6])
                    
        else:
            self.output('No results found')
        
