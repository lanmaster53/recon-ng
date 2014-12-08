import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.info = {
            'Name': 'Jigsaw - Point Usage Statistics Fetcher',
            'Author': 'Tim Tomes (@LaNMaSteR53)',
            'Description': 'Queries the Jigsaw API for the point usage statistics of the given account.',
        }

    def module_run(self):
        username = self.get_key('jigsaw_username')
        password = self.get_key('jigsaw_password')
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
