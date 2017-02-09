from recon.core.module import BaseModule
from urllib import quote_plus

class Module(BaseModule):
    meta = {
        'name': 'Github Profile Harvester',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Uses the Github API to gather user info from harvested profiles. Updates the \'contacts\' table with the results.',
        'required_keys': ['github_api'],
        'query': "SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL AND resource LIKE 'Github'",
    }

    def module_run(self, usernames):
        for username in usernames:
            users = self.query_github_api(endpoint='/users/%s' % (quote_plus(username)))
            # should only be one result, but loop just in case
            for user in users:
                name = user['name']
                fname, mname, lname = self.parse_name(name or '')
                email = user['email']
                title = 'Github Contributor'
                if user['company']:
                    title += ' at %s' % (user['company'])
                region = user['location']
                # don't add if lacking meaningful data
                if any((fname, lname, email)):
                    self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, email=email, title=title, region=region)
