import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.classify = 'passive'
        self.info = {
                     'Name': 'XSSed Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks XSSed.com site for XSS records for given domain and displays first 20 hits.',
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
                    except Exception as e:
                        self.error(e.__str__())
                    if not respDetail: return
                    
                    # Parse the response and get the details
                    details = []
                    for line in respDetail.text.split('\n'):
                        if "row3" in line:
                            try: 
                                a = re.search(r'">(.+)</th', line.strip())
                                details.append(a.group(1))
                            except: pass
                            
                    # Output the results in table format
                    status = re.search(r';([UNFIXED]+)$',details[2])
                                          
                    tdata = [] 
                    tdata.append(['Category', 'Details Retrieved'])
                    tdata.append(details[4].split(":",1))                           # Domain
                    
                    # Line wrapping for long XSS URLs that break table formatting
                    urlMaxLen = 80
                    xssUrlLen = len(details[7].split(":",1)[1])
                    if xssUrlLen > urlMaxLen:
                        wrappedLines = []
                        for line in details[7].split(":",1)[1].strip().split('\n'):
                            while True:
                                wrappedLines.append(line[:urlMaxLen])
                                line = line[urlMaxLen:]
                                if not line: break
                        counter = 1
                        for item in wrappedLines:
                            if counter == 1:
                                tdata.append(['URL:', ' ' + item])
                            else:
                                tdata.append(["URL (con't):", '   ' + item])
                            counter += 1
                    else:
                        tdata.append(details[7].split(":",1))                       # URL
                        
                    tdata.append(details[0].replace('&nbsp;', ' ').split(":",1))    # Date submitted
                    tdata.append(details[1].replace('&nbsp;', ' ').split(":",1))    # Date Published
                    tdata.append(details[5].split(":",1))                           # Category
                    tdata.append(['STATUS', ' ' + status.group(1)])                 # Fixed
                    self.table(tdata, True)   
                        
        else:
            self.output('No results found')
        
