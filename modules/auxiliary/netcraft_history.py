import framework
# unique to module
import os
import re
import hashlib
import urllib

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'database', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Hosting History',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Description': 'Checks Netcraft for the Hosting History of given target.',
                     'Comments': [
                                  'Source options: database, <hostname>, <path/to/infile>',
                                 ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.netcraft()

    def netcraft(self):
        verbose = self.options['verbose']['value']
        cookies = {}

        # handle sources
        source = self.options['source']['value']
        if source == 'database':
            hosts = [x[0] for x in self.query('SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')]
            if len(hosts) == 0:
                self.error('No hosts in the database.')
                return
        elif os.path.exists(source): hosts = open(source).read().split()
        else: hosts = [source]

        for host in hosts:
            url = 'http://uptime.netcraft.com/up/graph?site=%s' % (host)
            if verbose: self.output('URL: %s' % url)
            try: content = self.request(url, cookies=cookies)
            except KeyboardInterrupt:
                print ''
            except Exception as e:
                self.error(e.__str__())
            if not content: break

            if 'set-cookie' in content.headers:
                # we have a cookie to set!
                if verbose: self.output('Setting cookie...')
                cookie = content.headers['set-cookie']
                # this was taken from the netcraft page's JavaScript, no need to use big parsers just for that
                # grab the cookie sent by the server, hash it and send the response
                challenge_token = (cookie.split('=')[1].split(';')[0])
                response = hashlib.sha1(urllib.unquote(challenge_token))
                cookies = {
                            'netcraft_js_verification_response': '%s' % response.hexdigest(),
                            'netcraft_js_verification_challenge': '%s' % challenge_token,
                            'path' : '/'
                          }

                # Now we can request the page again
                if verbose: self.output('URL: %s' % url)
                try: content = self.request(url, cookies=cookies)
                except KeyboardInterrupt:
                    print ''
                except Exception as e:
                    self.error(e.__str__())

            content = content.text
            
            # Sorry for this... Apparently groups are overwritten if I use '+' 
            # to repeat the groups. Need a more elegant approach...
            history = re.findall(r'''
                    (?:<tr\ class="TBtr">|<tr\ class="TRtr2">)     # Identify the position
                    (?:\s*<td.*?>(.*?)<\/td>)                      # OS
                    (?:\s*<td.*?>(.*?)<\/td>)                      # SERVER
                    (?:\s*<td.*?>(.*?)<\/td>)                      # Last Changed
                    (?:\s*<td.*?>(.*?)<\/td>)                      # IP
                    (?:\s*<td.*?>.*?<a.*?\">(.*?)<\/a>)            # Block owner
                 ''', content, re.VERBOSE)

            if len(history) > 0:
                self.output("-------------------------------------------------------------------------------")
                self.output("|       OS      |     Server    |  Last Changed |      IP       |     Owner    ")
                self.output("-------------------------------------------------------------------------------")

                # Strip, padd and substrings each entry to make a pretty table
                for history in history:
                    self.output("".join(['| %s ' % v.strip().ljust(13)[:13] for v in history]))
                    
                self.output("-------------------------------------------------------------------------------")
            else:
                self.alert('No results found')
    


