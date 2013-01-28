import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('filename', './data/results.html', 'yes', 'path and filename for report output')
        self.register_option('sanitize', True, 'yes', 'mask sensitive data in the report')
        self.info = {
                     'Name': 'HTML Report Generator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Creates a HTML report.',
                     'Comments': []
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.generate_report()

    def sanitize_html(self, htmlstring):
        # escape HTML with entities
        escapes = {'"': '&quot;',
                   "'": '&#39;',
                   '<': '&lt;',
                   '>': '&gt;'}
        #for seq, esc in escapes.iteritems():
        #    htmlstring = htmlstring.replace(seq, esc)
        htmlstring = ''.join([char for char in htmlstring if ord(char) >= 32 and ord(char) <= 126])
        return htmlstring

    def generate_report(self):
        filename = self.options['filename']['value']
        try:
            outfile = open(filename, 'wb')
            outfile.close()
        except:
            self.error('Invalid path or filename.')
            return

        # get data from database
        hosts = self.query('SELECT * FROM hosts ORDER BY host')
        contacts = self.query('SELECT * FROM contacts ORDER BY fname')
        creds = self.query('SELECT DISTINCT username, password, hash, type  FROM creds ORDER BY username')

        # template
        template = """
<!DOCTYPE HTML>
<html>
<head>
<title>Recon-ng Reconnaissance Report</title>
<style>
body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: .75em;
    text-align: center;
}
.main {
    display: inline-block;
    margin-left: auto;
    margin-right: auto;
}
caption {
    font-weight: bold;
    font-size: 1.25em;
}
table {
    margin-left: auto; 
    margin-right: auto;
}
td, th {
    padding: 2px 20px;
    border-style: solid;
    border-width: 1px;
}
td {
    text-align: left;
}
.table_container {
    margin: 10px 0;
}
</style>
</head>
<body>
    <div class="main">
        <div><h1>Recon-ng Reconnaissance Report</h1></div>
        <div>
            <div class="table_container">%s</div>
            <div class="table_container">%s</div>
            <div class="table_container">%s</div>
        </div>
    </div>
</body>
</html>"""

        # build the report
        outfile = open(filename, 'wb')

        # hosts markup
        hosts_content = ''
        if hosts:
            hosts_content = '<table><caption>HOSTS</caption><tr><th>Hostname</th><th>IP Address</th></tr>'
            for host in hosts:
                host = [x if x != None else '' for x in host]
                hosts_content += '<tr><td>%s</td><td>%s</td></tr>' % (host[0], host[1])
            hosts_content += '</table>'

        # contacts markup
        contacts_content = ''
        if contacts:
            contacts_content = '<table><caption>CONTACTS</caption><tr><th>First Name</th><th>Last Name</th><th>Email/Username</th><th>Title</th></tr>'
            for contact in contacts:
                contact = [x if x != None else '' for x in contact]
                contacts_content += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (contact[0], contact[1], contact[2], contact[3])
            contacts_content += '</table>'

        # creds markup
        creds_content = ''
        if creds:
            creds_content = '<table><caption>CREDENTIALS</caption><tr><th>Username</th><th>Password</th><th>Hash</th><th>Hash Type</th></tr>'
            for cred in creds:
                cred = [x if x != None else '' for x in cred]
                password = cred[1]
                hashstr = cred[2]
                if self.options['sanitize']['value']:
                    password = '%s%s%s' % (password[:1], '*'*(len(password)-2), password[-1:])
                    hashstr = '%s%s%s' % (hashstr[:8], '*'*(len(hashstr)-16), hashstr[-8:])
                creds_content += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (cred[0], password, hashstr, cred[3])
            creds_content += '</table>'

        content = template % (hosts_content, contacts_content, creds_content)
        outfile.write(self.sanitize_html(content))
        outfile.close()
        self.output('Report generated at \'%s\'.' % (filename))