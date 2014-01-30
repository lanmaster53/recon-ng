import module
# unique to module
import datetime

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('filename', '%s/results.html' % (self.workspace), 'yes', 'path and filename for report output')
        self.register_option('sanitize', True, 'yes', 'mask sensitive data in the report')
        self.register_option('company', self.global_options['company'], 'yes', 'name for the report header')
        self.register_option('creator', None, 'yes', 'name for the report footer')
        self.info = {
                     'Name': 'HTML Report Generator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Creates a HTML report.',
                     'Comments': []
                     }

    def build_table(self, table):
        table_content = ''
        table_show = '<a id="show-%s" href="javascript:showhide(\'%s\');"><p>[+] %s</p></a>' % (table, table, table.replace('_', ' ').title())
        table_hide = '<a id="hide-%s" href="javascript:showhide(\'%s\');"><p>[-] %s</p><hr></a>' % (table, table, table.replace('_', ' ').title())
        columns = [x[1] for x in self.query('PRAGMA table_info(\'%s\')' % (table))]
        row_headers = '<tr><th>%s</th></tr>' % ('</th><th>'.join(columns))
        rows = self.query('SELECT "%s" FROM "%s" ORDER BY 1' % ('", "'.join(columns), table))
        if not rows: return ''
        row_content = ''
        for row in rows:
            values = [self.to_unicode_str(x) if x != None else u'' for x in row]
            if table == 'creds' and self.options['sanitize']:
                values[1] = '%s%s%s' % (values[1][:1], '*'*(len(values[1])-2), values[1][-1:])
            row_content += '<tr><td>%s</td></tr>\n' % ('</td><td>'.join([self.html_escape(x) for x in values]))
        table_content += '<div class="container">\n%s\n%s\n<table id="%s">\n%s\n%s</table>\n</div><br />\n' % (table_show, table_hide, table, row_headers, row_content)
        return table_content

    def module_run(self):
        # validate that file can be created
        filename = self.options['filename']
        outfile = open(filename, 'w')
        table_content = ''

        # html template
        template = open('data/template_html.html').read()

        # custom summary results table
        table_show = '<a id="show-summary" href="javascript:showhide(\'summary\');"><p>[+] Summary</p></a>'
        table_hide = '<a id="hide-summary" href="javascript:showhide(\'summary\');"><p>[-] Summary</p><hr></a>'
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'') if x[0] not in ['leaks', 'dashboard']]
        row_headers = '<tr><th>table</th><th>count</th></tr>'
        row_content = ''
        for table in tables:
            count = self.query('SELECT COUNT(*) FROM "%s"' % (table))[0][0]
            row_content += '<tr><td>%s</td><td class="centered">%s</td></tr>\n' % (table, count)
        table_content += '<div class="container">\n%s\n%s\n<table id="summary">\n%s\n%s</table>\n</div><br />\n' % (table_show, table_hide, row_headers, row_content)

        # main content tables
        tables = ['hosts', 'contacts', 'creds']
        for table in tables:
            table_content += self.build_table(table)

        # table of leaks associated with creds
        leaks = self.query('SELECT DISTINCT leak FROM creds WHERE leak IS NOT NULL')
        if leaks:
            columns = [x[1] for x in self.query('PRAGMA table_info(leaks)')]
            if columns:
                table_content += '<div class="container">\n'
                table_content += '<a id="show-leaks" href="javascript:showhide(\'leaks\');"><p>[+] Associated Leaks</p></a>\n'
                table_content += '<a id="hide-leaks" href="javascript:showhide(\'leaks\');"><p>[-] Associated Leaks</p></a>\n'
                table_content += '<div id="leaks">\n'
                for leak in [x[0] for x in leaks]:
                    row_content = ''
                    row = self.query('SELECT * FROM leaks WHERE leak_id=?', (leak,))[0]
                    values = [self.html_escape(x) if x != None else '' for x in row]
                    for i in range(0,len(columns)):
                        row_content += '<tr><td><strong>%s</strong></td><td>%s</td></tr>\n' % (columns[i], values[i])
                    table_content += '<hr>\n<table class="leak">\n%s</table>\n' % (row_content)
                table_content += '</div>\n</div><br />'
            else:
                self.output('Associate leak data omitted. Please run the \'leaks_dump\' module to populate the database and try again.')

        # all other tables
        # build exclusions list by extending the list from above
        tables.extend(['leaks', 'dashboard', 'pushpin'])
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'') if x[0] not in tables]
        for table in tables:
            table_content += self.build_table(table)

        title = self.options['company'].title()
        creator = self.options['creator'].title()
        created = datetime.datetime.now().strftime('%a, %b %d %Y %H:%M:%S')
        markup = template % (title, table_content, creator, created)
        outfile.write(markup.encode('utf-8'))
        outfile.close()
        self.output('Report generated at \'%s\'.' % (filename))
