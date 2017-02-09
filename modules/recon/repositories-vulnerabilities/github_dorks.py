from recon.core.module import BaseModule
import os

class Module(BaseModule):
    meta = {
        'name': 'Github Dork Analyzer',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Uses the Github API to search for possible vulnerabilites in source code by leveraging Github Dorks and the \'repo\' search operator. Updates the \'vulnerabilities\' table with the results.',
        'required_keys': ['github_api'],
        'query': "SELECT DISTINCT owner || '/' || name FROM repositories WHERE name IS NOT NULL AND resource LIKE 'Github' AND category LIKE 'repo'",
        'options': (
            ('dorks', os.path.join(BaseModule.data_path, 'github_dorks.txt'), True, 'file containing a list of Github dorks'),
        ),
    }

    def module_run(self, repos):
        with open(self.options['dorks']) as fp:
            # create list of dorks and filter out comments
            dorks = [x.strip() for x in fp.read().splitlines() if x and not x.startswith('#')]
        for repo in repos:
            self.heading(repo, level=0)
            for dork in dorks:
                query = 'repo:%s %s' % (repo, dork)
                for result in self.search_github_api(query):
                    data = {
                        'reference': query,
                        'example': result['html_url'],
                        'category': 'Github Dork',
                    }
                    self.add_vulnerabilities(**data)
