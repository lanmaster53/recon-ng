import module
# unique to module
import urllib
import json

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL')
        self.register_option('site_db', self.data_path+'/profiler_sites.json', True, 'JSON file containing known sites and response codes')
        self.info = {
            'Name': 'OSINT HUMINT Profile Collector',
            'Author':'Micah Hoffman (@WebBreacher)',
            'Description': 'Takes each username from the profiles table and searches a variety of web sites for those users.',
            'Comments': [
                'Note: The global timeout option may need to be increased to support slower sites.',
                'Warning: Using this module behind a filtering proxy may cause false negatives as some of these sites may be blocked.'
            ]
        }

    def module_run(self, usernames):
        # create sites lookup table
        with open(self.options['site_db']) as db_file:
            site_db = json.load(db_file)
        self.output('We have %s sites that we will check for your usernames. This will take a while.' % len(site_db["sites"]))

        for user in usernames: 
            flag = False
            self.heading('Looking up data for: %s' % user)
            for site in site_db["sites"]:
                url = site['u'] % urllib.quote(user)
                self.verbose('Checking: %s' % site['r'])
                try:
                    resp = self.request(url, redirect=False)
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e:
                    self.error('%s: %s' % (url, e.__str__()))
                    continue
                if resp.status_code == int(site['gRC']):
                    self.debug('Codes matched %s %s' % (resp.status_code, site['gRC']))
                    if site['gRT'] in resp.text or site['gRT'] in resp.headers:
                        self.alert('Probable match: %s' % url)
                        self.add_profiles(username=user, url=url, resource=site['r'], category=site['c'])
                        flag = True
            if flag: self.query('DELETE FROM profiles WHERE username = ? and url IS NULL', (user,))