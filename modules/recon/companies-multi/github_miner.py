from recon.core.module import BaseModule
from urllib import quote_plus

class Module(BaseModule):
    meta = {
        'name': 'Github Resource Miner',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Uses the Github API to enumerate repositories and member profiles associated with a company search string. Updates the respective tables with the results.',
        'required_keys': ['github_api'],
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL',
    }

    def module_run(self, companies):
        for company in companies:
            self.heading(company, level=0)
            # enumerate members
            members = self.query_github_api('/orgs/%s/members' % (quote_plus(company)))
            for member in members:
                data = {
                    'username': member['login'],
                    'url': member['html_url'],
                    'notes': company,
                    'resource': 'Github',
                    'category': 'coding',
                }
                self.add_profiles(**data)
            # enumerate repositories
            repos = self.query_github_api('/orgs/%s/repos' % (quote_plus(company)))
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
