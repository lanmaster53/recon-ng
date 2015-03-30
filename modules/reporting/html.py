from recon.core.module import BaseModule
import codecs
import datetime
import os

class Module(BaseModule):

    meta = {
        'name': 'HTML Report Generator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Creates a HTML report.',
        'options': (
            ('sanitize', True, True, 'mask sensitive data in the report'),
            ('customer', None, True, 'customer name for the report header'),
            ('creator', None, True, 'creator name for the report footer'),
            ('filename', os.path.join(BaseModule.workspace, 'results.html'), True, 'path and filename for report output'),
        ),
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
            if table == 'credentials' and values[1] and self.options['sanitize']:
                values[1] = '<omitted>'
            row_content += '<tr><td>%s</td></tr>\n' % ('</td><td>'.join([self.html_escape(x) for x in values]))
        table_content += '<div class="container">\n%s\n%s\n<table name="table" id="%s">\n%s\n%s</table>\n</div><br />\n' % (table_show, table_hide, table, row_headers, row_content)
        return table_content

    def module_run(self):
        filename = self.options['filename']
        with codecs.open(filename, 'wb', encoding='utf-8') as outfile:
            table_content = ''
            # html template
            template = open(os.path.join(self.data_path, 'template_html.html')).read()
            # custom summary results table
            table_show = '<a id="show-summary" href="javascript:showhide(\'summary\');"><p>[+] Summary</p></a>'
            table_hide = '<a id="hide-summary" href="javascript:showhide(\'summary\');"><p>[-] Summary</p><hr></a>'
            tables = self.get_tables()
            row_headers = '<tr><th>table</th><th>count</th></tr>'
            row_content = ''
            for table in tables:
                query = 'SELECT COUNT(*) FROM "%s"' % (table)
                if table == 'leaks':
                    query = 'SELECT COUNT(DISTINCT leak) FROM credentials WHERE leak IS NOT NULL'
                count = self.query(query)[0][0]
                row_content += '<tr><td>%s</td><td class="centered">%s</td></tr>\n' % (table, count)
            table_content += '<div class="container">\n%s\n%s\n<table id="summary">\n%s\n%s</table>\n</div><br />\n' % (table_show, table_hide, row_headers, row_content)
            # main content tables
            tables = ['domains', 'companies', 'netblocks', 'locations', 'hosts', 'contacts', 'credentials']
            for table in tables:
                table_content += self.build_table(table)
            # table of leaks associated with credentials
            leaks = self.query('SELECT DISTINCT leak FROM credentials WHERE leak IS NOT NULL')
            if leaks:
                if self.query('SELECT COUNT(*) FROM leaks')[0][0]:
                    columns = [x[1] for x in self.query('PRAGMA table_info(leaks)')]
                    table_content += '<div class="container">\n'
                    table_content += '<a id="show-leaks" href="javascript:showhide(\'leaks\');"><p>[+] Associated Leaks</p></a>\n'
                    table_content += '<a id="hide-leaks" href="javascript:showhide(\'leaks\');"><p>[-] Associated Leaks</p></a>\n'
                    table_content += '<div name="table" id="leaks">\n'
                    for leak in [x[0] for x in leaks]:
                        row_content = ''
                        row = self.query('SELECT * FROM leaks WHERE leak_id=?', (leak,))[0]
                        values = [self.html_escape(x) if x != None else '' for x in row]
                        for i in range(0,len(columns)):
                            row_content += '<tr><td><strong>%s</strong></td><td>%s</td></tr>\n' % (columns[i], values[i])
                        table_content += '<hr>\n<table class="leak">\n%s</table>\n' % (row_content)
                    table_content += '</div>\n</div><br />'
                else:
                    self.output('Associated leak data omitted. Please run the \'leaks_dump\' module to populate the database and try again.')
            # all other tables
            # build exclusions list by extending the list from above
            tables.extend(['leaks', 'pushpins', 'dashboard'])
            tables = [x for x in self.get_tables() if x not in tables]
            for table in tables:
                table_content += self.build_table(table)
            title = self.options['customer']
            creator = self.options['creator']
            created = datetime.datetime.now().strftime('%a, %b %d %Y %H:%M:%S')
            markup = template % (title, table_content, creator, created)
            outfile.write(markup)
        self.output('Report generated at \'%s\'.' % (filename))
