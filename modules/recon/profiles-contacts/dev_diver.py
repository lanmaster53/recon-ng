from recon.core.module import BaseModule
import json
import re
import time
import urllib

class Module(BaseModule):

    meta = {
        'name': 'Dev Diver Repository Activity Examiner',
        'author': 'Micah Hoffman (@WebBreacher)',
        'description': 'Searches public code repositories for information about a given username.',
        'query': 'SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL',
    }

    # Add a method for each repository
    def github(self, username):
        self.verbose('Checking Github...')
        url = 'https://api.github.com/users/%s' % (username)
        resp = self.request(url)
        data = resp.json
        if data.has_key('login'):
            self.alert('Github username found - (%s)' % url)
            # extract data from the optional fields
            gitName    = data['name'] if data.has_key('name') else None
            gitCompany = data['company'] if data.has_key('company') else None
            gitBlog    = data['blog'] if data.has_key('blog') else None
            gitLoc     = data['location'] if data.has_key('location') else None
            gitEmail   = data['email'] if data.has_key('email') else None
            gitBio     = data['bio'] if data.has_key('bio') else None
            gitJoin    = data['created_at'].split('T')
            gitUpdate  = data['updated_at'].split('T')
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'Github'])
            tdata.append(['User Name', data['login']])
            tdata.append(['Real Name', gitName]) if gitName else None
            tdata.append(['Profile URL', data['html_url']])
            tdata.append(['Avatar URL', data['avatar_url']])
            tdata.append(['Location', gitLoc])
            tdata.append(['Company', gitCompany])
            tdata.append(['Blog URL', gitBlog])
            tdata.append(['Email', gitEmail])
            tdata.append(['Bio', gitBio])
            tdata.append(['Followers', data['followers']])
            tdata.append(['ID', data['id']])
            tdata.append(['Joined', gitJoin[0]])
            tdata.append(['Updated', gitUpdate[0]])
            self.table(tdata, title='Github')
            # add the pertinent information to the database
            if not gitName: gitName = username
            fname, mname, lname = self.parse_name(gitName)
            self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title='Github Contributor')
        else:
            self.output('Github username not found.')

    def bitbucket(self, username):
        self.verbose('Checking Bitbucket...')
        url = 'https://bitbucket.org/api/2.0/users/%s' % (username)
        resp = self.request(url)
        data = resp.json
        if data.has_key('username'):
            self.alert('Bitbucket username found - (%s)' % url)
            # extract data from the optional fields
            bbName = data['display_name']
            bbJoin = data['created_on'].split('T')
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'Bitbucket'])
            tdata.append(['User Name', data['username']])
            tdata.append(['Display Name', bbName])
            tdata.append(['Location', data['location']])
            tdata.append(['Joined', bbJoin[0]])
            tdata.append(['Personal URL', data['website']])
            tdata.append(['Bitbucket URL', data['links']['html']['href']])
            #tdata.append(['Avatar URL', data['user']['avatar']]) # This works but is SOOOO long it messes up the table
            self.table(tdata, title='Bitbucket')
            # add the pertinent information to the database
            if not bbName: bbName = username
            fname, mname, lname = self.parse_name(bbName)
            self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title='Bitbucket Contributor')
        else:
            self.output('Bitbucket username not found.')


    def sourceforge(self, username):
        self.verbose('Checking SourceForge...')
        url = 'http://sourceforge.net/u/%s/profile/' % (username)
        resp = self.request(url)
        sfName = re.search('<title>(.+) / Profile', resp.text)
        if sfName:
            self.alert('Sourceforge username found - (%s)' % url)
            # extract data
            sfJoin = re.search('<dt>Joined:</dt><dd>\s*(\d\d\d\d-\d\d-\d\d) ', resp.text)
            sfLocation = re.search('<dt>Location:</dt><dd>\s*(\w.*)', resp.text)
            sfGender = re.search('<dt>Gender:</dt><dd>\s*(\w.*)', resp.text)
            sfProjects = re.findall('class="project-info">\s*<a href="/p/.+/">(.+)</a>', resp.text)
            # establish non-match values
            sfName = sfName.group(1)
            sfJoin = sfJoin.group(1) if sfJoin else None
            sfLocation = sfLocation.group(1) if sfLocation else None
            sfGender = sfGender.group(1) if sfGender else None
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'Sourceforge'])
            tdata.append(['Name', sfName])
            tdata.append(['Profile URL', url])
            tdata.append(['Joined', sfJoin])
            tdata.append(['Location', sfLocation])
            tdata.append(['Gender', sfGender])
            for sfProj in sfProjects:
                tdata.append(['Projects', sfProj])
            self.table(tdata, title='Sourceforge')
            # add the pertinent information to the database
            if not sfName: sfName = username
            fname, mname, lname = self.parse_name(sfName)
            self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title='Sourceforge Contributor')
        else:
            self.output('Sourceforge username not found.')

    def codeplex(self, username):
        self.verbose('Checking CodePlex...')
        url = 'http://www.codeplex.com/site/users/view/%s' % (username)
        resp = self.request(url)
        cpName = re.search('<h1 class="user_name" style="display: inline">(.+)</h1>', resp.text)
        if cpName:
            self.alert('CodePlex username found - (%s)' % url)
            # extract data
            cpJoin = re.search('Member Since<span class="user_float">([A-Z].+[0-9])</span>', resp.text)
            cpLast = re.search('Last Visit<span class="user_float">([A-Z].+[0-9])</span>', resp.text)
            cpCoordinator = re.search('(?s)<p class="OverflowHidden">(.*?)</p>', resp.text)
            # establish non-match values
            cpName = cpName.group(1) if cpName else None
            cpJoin = cpJoin.group(1) if cpJoin else 'January 1, 1900'
            cpLast = cpLast.group(1) if cpLast else 'January 1, 1900'
            cpCoordinator = cpCoordinator.group(1) if cpCoordinator else ''
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'CodePlex'])
            tdata.append(['Name', cpName])
            tdata.append(['Profile URL', url])
            tdata.append(['Joined', time.strftime('%Y-%m-%d', time.strptime(cpJoin, '%B %d, %Y'))])
            tdata.append(['Date Last', time.strftime('%Y-%m-%d', time.strptime(cpLast, '%B %d, %Y'))])
            cpCoordProject = re.findall('<a href="(http://.+)/" title=".+">(.+)<br /></a>', cpCoordinator)
            for cpReposUrl, cpRepos in cpCoordProject:
                tdata.append(['Project', '%s (%s)' % (cpRepos, cpReposUrl)])
            self.table(tdata, title='CodePlex')
            # add the pertinent information to the database
            if not cpName: cpName = username
            fname, mname, lname = self.parse_name(cpName)
            self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title='CodePlex Contributor')
        else:
            self.output('CodePlex username not found.')

    def gitorious(self, username):
        self.verbose('Checking Gitorious...')
        url = 'https://gitorious.org/~%s' % (username)
        resp = self.request(url)
        if re.search('href="/~%s" class="avatar"' % (username), resp.text):
            self.alert('Gitorious username found - (%s)' % url)
            # extract data
            gitoName = re.search('<strong>([^<]*)</strong>\s+</li>\s+<li class="email">', resp.text)
            # Gitorious URL encodes the user's email to obscure it...lulz. No problem.
            gitoEmailRaw = re.search("eval\(decodeURIComponent\('(.+)'", resp.text)
            gitoEmail = re.search(r'mailto:([^\\]+)', urllib.unquote(gitoEmailRaw.group(1))) if gitoEmailRaw else None
            gitoJoin = re.search('Member for (.+)', resp.text)
            gitoPersonalUrl = re.search('rel="me" href="(.+)">', resp.text)
            gitoProjects = re.findall('<tr class="project">\s+<td>\s+<a href="/([^"]*)">([^<]*)</a>\s+</td>\s+</tr>', resp.text)
            # establish non-match values
            gitoName = gitoName.group(1) if gitoName else None
            gitoEmail = gitoEmail.group(1) if gitoEmail else None
            gitoJoin = gitoJoin.group(1) if gitoJoin else None
            gitoPersonalUrl = gitoPersonalUrl.group(1) if gitoPersonalUrl else None
            # build and display a table of the results
            tdata = []
            tdata.append(['Resource', 'Gitorious'])
            tdata.append(['Name', gitoName])
            tdata.append(['Profile URL', url])
            tdata.append(['Membership', gitoJoin])
            tdata.append(['Email', gitoEmail])
            tdata.append(['Personal URL', gitoPersonalUrl])
            for gitoProjUrl, gitoProjName in gitoProjects:
                tdata.append(['Project', '%s (https://gitorious.org/%s)' % (gitoProjName, gitoProjUrl)])
            self.table(tdata, title='Gitorious')
            # add the pertinent information to the database
            if not gitoName: gitoName = username
            fname, mname, lname = self.parse_name(gitoName)
            self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title='Gitorious Contributor', email=gitoEmail)
        else:
            self.output('Gitorious username not found.')

    def module_run(self, usernames):
        for username in usernames:
            # Check each repository
            self.github(username)
            self.bitbucket(username)
            self.sourceforge(username)
            self.codeplex(username)
            self.gitorious(username)
