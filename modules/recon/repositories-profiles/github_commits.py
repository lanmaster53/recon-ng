from recon.core.module import BaseModule
from urllib import quote_plus

class Module(BaseModule):
    meta = {
        'name': 'Github Commit Searcher',
        'author': 'Michael Henriksen (@michenriksen)',
        'description': 'Uses the Github API to gather user profiles from repository commits. Updates the \'profiles\' table with the results.',
        'query': "SELECT DISTINCT owner, name FROM repositories WHERE resource LIKE 'Github' AND category LIKE 'repo'",
        'options': (
            ('maxpages', 1, True, 'Maximum number of commit pages to process for each repository (0 = unlimited)'),
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
                    if key in commit:
                        url = commit[key]['url']
                        login = commit[key]['login']
                        self.output('%s (%s)' % (login, url))
                        self.add_profiles(username=login, url=url, resource='Github', category='coding')
                    if key in commit['commit']:
                        name = commit['commit'][key]['name']
                        email = commit['commit'][key]['email']
                        self.output('%s (%s)' % (name, email))
                        fname, mname, lname = self.parse_name(name)
                        self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, email=email, title='Github Contributor')
