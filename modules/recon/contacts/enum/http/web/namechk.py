import framework
# unique to module
import re
from hashlib import sha1
from hmac import new as hmac
import socket

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('username', None, 'yes', 'username to validate')
        self.info = {
                     'Name': 'NameChk.com Username Validator',
                     'Author': 'Tim Tomes (@LaNMaSteR53) and thrapt (thrapt@gmail.com)',
                     'Description': 'Leverages NameChk.com to validate the existance of usernames at specific web sites.',
                     'Comments': [
                                  'Note: The global timeout option may need to be increased to support slower sites.']
                     }

    def module_run(self):
        username = self.options['username']

        # retrive list of sites
        url = 'http://namechk.com/Content/sites.min.js'
        resp = self.request(url)
        
        # extract sites info from the js file
        pattern = 'n:"(.+?)",r:\d+,i:(\d+)'
        sites = re.findall(pattern, resp.text)

        # output table of sites info
        if self.global_options['verbose']:
            tdata = []
            for site in sites:
                tdata.append([site[1], site[0]])
            self.table(tdata, header=['Code', 'Name'])

        # retrive statuses
        key = "1Sx8srDg1u57Ei2wqX65ymPGXu0f7uAig13u"
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
                raise KeyboardInterrupt
            except Exception as e:
                self.error('%s: %s' % (name, e.__str__()))
                continue
            x = resp.text
            if int(x) > 0:
                status = status_dict[x]
                if int(x) == 2:
                    self.alert('%s: %s' % (name, status))
                else:
                    self.verbose('%s: %s' % (name, status))
            else:
                self.error('%s: %s' % (name, 'Unknown error.'))
