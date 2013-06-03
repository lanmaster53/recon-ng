import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('filename', '%s/results.html' % (self.workspace), 'yes', 'path and filename for report output')
        self.register_option('sanitize', True, 'yes', 'mask sensitive data in the report')
        self.register_option('company', self.goptions['company']['value'], 'yes', 'name for report header')
        self.info = {
                     'Name': 'HTML Report Generator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Creates a HTML report.',
                     'Comments': []
                     }

    def build_table(self, table):
        table_content = ''
        table_show = '<p><a id="show-%s" href="javascript:showhide(\'%s\');">[+] %s</a></p>' % (table, table, table.upper().replace('_', ' '))
        table_hide = '<p><a id="hide-%s" href="javascript:showhide(\'%s\');">[-] %s</a></p>' % (table, table, table.upper().replace('_', ' '))
        columns = [x[1] for x in self.query('PRAGMA table_info(%s)' % (table))]
        row_headers = '<tr><th>%s</th></tr>' % ('</th><th>'.join(columns))
        rows = self.query('SELECT %s FROM %s ORDER BY 1' % (', '.join(columns), table))
        if not rows: return ''
        row_content = ''
        for row in rows:
            values = [self.to_unicode_str(x) if x != None else u'' for x in row]
            if table == 'creds' and self.options['sanitize']['value']:
                values[1] = '%s%s%s' % (values[1][:1], '*'*(len(values[1])-2), values[1][-1:])
            row_content += '<tr><td>%s</td></tr>\n' % ('</td><td>'.join(values))
        table_content += '<div class="table_container">\n%s\n%s\n<table id="%s">\n%s\n%s</table>\n</div>\n' % (table_show, table_hide, table, row_headers, row_content)
        return table_content

    def module_run(self):
        # validate that file can be created
        filename = self.options['filename']['value']
        outfile = open(filename, 'w')
        # html template
        template = """
<!DOCTYPE HTML>
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<title>Recon-ng Reconnaissance Report</title>
<script type="text/javascript">
function showhide(id) {
    obj = document.getElementById(id);
    hide = document.getElementById("hide-" + id);
    show = document.getElementById("show-" + id);
    if (obj.style.display == "none") {
        show.removeAttribute('style');
        hide.removeAttribute('style');
        obj.removeAttribute('style');
    } else {
        obj.style.display = "none";
        hide.style.display = "none";
        show.style.display = "inline";
    }
}
</script>
<style>
body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: .75em;
    color: black;
    background-color: white;
    text-align: center;
}
.main {
    display: inline-block;
    margin-left: auto;
    margin-right: auto;
    width: 100%%;
}
.title {
    font-size: 3em;
}
.subtitle {
    font-size: 2em;
}
table {
    margin-left: auto; 
    margin-right: auto;
    white-space: nowrap;
}
td, th {
    padding: 2px 20px;
    border-style: solid;
    border-width: 1px;
    color: black;
    background-color: white;
}
td {
    text-align: left;
}
.table_container {
    margin: 10px 0;
}
.leak {
    width: 1200px;
    white-space: normal;
}
.spacer {
    height: 1em;
    border: 0px;
    background-color: transparent;
}
a[id*="-"] {
    color: black;
    text-decoration: none;
    font-weight: bold;
    font-size: 1.25em;
}
a[id*="show-"] {
    display: none;
}
</style>
</head>
<body>
    <div class="main">
        <div class='title'>%s</div>
        <div class='subtitle'>Recon-ng Reconnaissance Report</div>
        <div>
<!-- START -->
%s
<!-- END -->
        </div>
    </div>
</body>
</html>
"""

        # dashboard table
        table_content = self.build_table('dashboard')

        # custom summary results table
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'') if x[0] not in ['leaks', 'dashboard']]
        row_headers = '<tr><th>table</th><th>count</th></tr>'
        row_content = ''
        for table in tables:
            count = self.query('SELECT COUNT(*) FROM %s' % (table))[0][0]
            row_content += '<tr><td>%s</td><td>%s</td></tr>\n' % (table, count)
        table_content += '<div class="table_container">\n<p><a id="show-summary" href="javascript:showhide(\'summary\');">[+] SUMMARY</a></p>\n<table id="summary">\n<caption><a id="hide-summary" href="javascript:showhide(\'summary\');">[-] SUMMARY</a></caption>\n%s\n%s</table>\n</div>\n' % (row_headers, row_content)

        # main content tables
        tables = ['hosts', 'contacts', 'creds']
        for table in tables:
            table_content += self.build_table(table)

        # table of leaks associated with creds
        leaks = self.query('SELECT DISTINCT leak FROM creds WHERE leak IS NOT NULL')
        if leaks:
            columns = [x[1] for x in self.query('PRAGMA table_info(leaks)')]
            if columns:
                table_content += '<p><a id="show-leaks" href="javascript:showhide(\'leaks\');">[+] ASSOCIATED LEAKS</a></p>\n'
                table_content += '<p><a id="hide-leaks" href="javascript:showhide(\'leaks\');">[-] ASSOCIATED LEAKS</a></p>\n'
                table_content += '<div id="leaks">\n'
                for leak in [x[0] for x in leaks]:
                    row_content = ''
                    row = self.query('SELECT * FROM leaks WHERE leak_id = \'%s\'' % (leak))[0]
                    values = [x if x != None else '' for x in row]
                    for i in range(0,len(columns)):
                        row_content += '<tr><td><strong>%s</strong></td><td>%s</td></tr>\n' % (columns[i], values[i])
                    row_content += '<tr><td class="spacer"></td></tr>\n'
                    table_content += '<div class="table_container">\n<table class="leak">\n%s</table>\n</div>\n' % (row_content)
                table_content += '</div>\n'
            else:
                self.output('Associate leak data omitted. Please run the \'leaks_dump\' module to populate the database and try again.')

        # all other tables
        tables.extend(['leaks', 'dashboard'])
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'') if x[0] not in tables]
        for table in tables:
            table_content += self.build_table(table)

        markup = template % (self.options['company']['value'].title(), table_content)
        outfile.write(markup.encode('utf-8'))
        outfile.close()
        self.output('Report generated at \'%s\'.' % (filename))
