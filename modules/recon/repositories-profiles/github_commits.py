from recon.core.module import BaseModule
from urllib import quote_plus

class Module(BaseModule):
    meta = {
        'name': 'Github Commit Searcher',
        'author': 'Michael Henriksen (@michenriksen)',
        'description': 'Uses the Github API to gather user profiles from repository commits. Updates the \'profiles\' table with the results.',
        'required_keys': ['github_api'],
        'query': "SELECT DISTINCT owner, name FROM repositories WHERE resource LIKE 'Github' AND category LIKE 'repo'",
        'options': (
            ('maxpages', 1, True, 'maximum number of commit pages to process for each repository (0 = unlimited)'),
            ('author', True, True, 'extract author information'),
            ('committer', True, True, 'extract committer information'),
        ),
    }

    def module_run(self, repos):
        for repo in repos:
            commits = self.query_github_api(
                endpoint='/repos/%s/%s/commits' % (quote_plus(repo[0]), quote_plus(repo[1])),
                payload={},
                options={'max_pages': int(self.options['maxpages']) or None},
            )
            for commit in commits:
                for key in ('committer', 'author'):
                    if self.options[key] and key in commit and commit[key]:
                        url = commit[key]['html_url']
                        login = commit[key]['login']
                        self.add_profiles(username=login, url=url, resource='Github', category='coding')
                    if self.options[key] and key in commit['commit'] and commit['commit'][key]:
                        name = commit['commit'][key]['name']
                        email = commit['commit'][key]['email']
                        fname, mname, lname = self.parse_name(name)
                        self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, email=email, title='Github Contributor')
