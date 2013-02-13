import framework
# unique to module
import re
from hashlib import sha1
from hmac import new as hmac
import socket

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('username', 'lanmaster53', 'yes', 'username to validate')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'NameChk.com Username Validator',
                     'Author': 'Tim Tomes (@LaNMaSteR53) and thrapt (thrapt@gmail.com)',
                     'Description': 'Leverages NameChk.com to validate the existance of usernames at specific web sites.',
                     'Comments': [
                                  'Note: The global socket_timeout may need to be increased to support slower sites.']
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.namechk()
    
    def namechk(self):
        username = self.options['username']['value']
        verbose = self.options['verbose']['value']

        # retrive list of sites
        url = 'http://namechk.com/Content/sites.min.js'
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        
        # extract sites info from the js file
        pattern = 'n:"(.+?)",r:\d+,i:(\d+)'
        sites = re.findall(pattern, resp.text)

        # output table of sites info
        if verbose:
            tdata = [['Code', 'Name']]
            for site in sites:
                tdata.append([site[1], site[0]])
            self.table(tdata, True)

        # retrive statuses
        key = "shhh it's :] super secret"
        url = 'http://namechk.com/check'

        # this header is required
        headers = {'X-Requested-With': 'XMLHttpRequest'}

        status_dict = {
                       '1': 'Available',
                       '2': 'User Exists!',
                       '3': 'Unknown',
                       '4': 'Indefinite'
                       }

        for site in sites:
            i = site[1]
            name = site[0]
            # build the hmac payload
            message = "POST&%s?i=%s&u=%s" % (url, i, username)
            b64_hmac_sha1 = '%s' % hmac(key, message, sha1).digest().encode('base64')[:-1]
            payload = {'i': i, 'u': username, 'o_0': b64_hmac_sha1}
            # build and send the request
            try: resp = self.request(url, method='POST', headers=headers, payload=payload)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error('%s: %s' % (name, e.__str__()))
                continue
            x = resp.text
            if int(x) > 0:
                status = status_dict[x]
                if int(x) == 2:
                    self.alert('%s: %s' % (name, status))
                else:
                    if verbose: self.output('%s: %s' % (name, status))
            else:
                self.error('%s: %s' % (name, 'Error'))
