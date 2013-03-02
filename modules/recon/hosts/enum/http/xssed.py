import framework
# unique to module
import re
import textwrap
import time

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'XSSed Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks XSSed.com for XSS records for the given domain and displays the first 20 results.',
                     'Comments': []
                     }
   
    def module_run(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']

        url = 'http://xssed.com/search?key=%s' % (domain)
        if verbose: self.output('URL: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        
        content = resp.text

        # Find if there are any results for the domain search
        results = re.findall(r"Results for.*", content)
       
        if results:
            rows = re.split('<br>', str(results))
            for row in rows:
                finding = re.findall(r"mirror/([0-9]+)/.+blank\\'>(.+?)</a>", row)
                if finding:
                    # Go fetch and parse the specific page for this item
                    urlDetail = 'http://xssed.com/mirror/%s/' % finding[0][0]
                    try: respDetail = self.request(urlDetail)
                    except KeyboardInterrupt:
                        print ''
                        return
                    except Exception as e:
                        self.error(e.__str__())
                        continue
                    
                    # Parse the response and get the details
                    details = []
                    for line in respDetail.text.split('\n'):
                        if "row3" in line:
                            try: 
                                a = re.search(r'">(.+)</th', line.strip())
                                details.append(a.group(1))
                            except: pass
                    # Output the results in table format
                    status = re.search(r';([UNFIXED]+)',details[2]).group(1)
                    self.output('Mirror: %s' % (urlDetail))
                    self.output(details[4])
                    self.output(textwrap.fill(details[7], 100, initial_indent='', subsequent_indent=self.spacer*2))
                    self.output(details[0])
                    self.output(details[1])
                    self.output(details[5])
                    self.output('Status: %s' % (status))
                    print self.ruler*50
                    time.sleep(1) # results in 503 errors if not throttled
        else:
            self.output('No results found')
