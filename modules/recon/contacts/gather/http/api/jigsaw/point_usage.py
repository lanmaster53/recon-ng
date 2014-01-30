import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('username', None, 'yes', 'jigsaw account username')
        self.register_option('password', None, 'yes', 'jigsaw account password')
        self.info = {
                     'Name': 'Jigsaw - Point Usage Statistics Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the Jigsaw API for the point usage statistics of the given account.',
                     'Comments': []
                     }

    def module_run(self):
        username = self.options['username']
        password = self.options['password']
        key = self.get_key('jigsaw_api')

        url = 'https://www.jigsaw.com/rest/user.json'
        payload = {'token': key, 'username': username, 'password': password}
        resp = self.request(url, payload=payload, redirect=False)
        if resp.json: jsonobj = resp.json
        else:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return

        # handle output
        self.output('%d Jigsaw points remaining.' % (jsonobj['points']))
