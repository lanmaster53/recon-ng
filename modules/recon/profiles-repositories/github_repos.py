from recon.core.module import BaseModule
from urllib import quote_plus

class Module(BaseModule):
    meta = {
        'name': 'Github Code Enumerator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Uses the Github API to enumerate repositories and gists owned by a Github user. Updates the \'repositories\' table with the results.',
        'required_keys': ['github_api'],
        'query': "SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL AND resource LIKE 'Github'",
    }

    def module_run(self, users):
        for user in users:
            self.heading(user, level=0)
            # enumerate repositories
            repos = self.query_github_api('/users/%s/repos' % (quote_plus(user)))
            for repo in repos:
                data = {
                    'name': repo['name'],
                    'owner': repo['owner']['login'],
                    'description': repo['description'],
                    'url': repo['html_url'],
                    'resource': 'Github',
                    'category': 'repo',
                }
                self.add_repositories(**data)
            # enumerate gists
            gists = self.query_github_api('/users/%s/gists' % (quote_plus(user)))
            for gist in gists:
                files = gist['files'].values()
                for _file in files:
                    data = {
                        'name': _file['filename'],
                        'owner': gist['owner']['login'],
                        'description': gist['description'],
                        'url': _file['raw_url'],
                        'resource': 'Github',
                        'category': 'gist',
                    }
                    self.add_repositories(**data)
