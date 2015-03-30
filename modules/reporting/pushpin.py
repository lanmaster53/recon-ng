from recon.core.module import BaseModule
import codecs
import os
import re
import time
import webbrowser

class Module(BaseModule):

    meta = {
        'name': 'PushPin Report Generator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Creates HTML media and map reports for all of the PushPins stored in the database.',
        'options': (
            ('latitude', None, True, 'latitude of the epicenter'),
            ('longitude', None, True, 'longitude of the epicenter'),
            ('radius', None, True, 'radius from the epicenter in kilometers'),
            ('map_filename', os.path.join(BaseModule.workspace, 'pushpin_map.html'), True, 'path and filename for pushpin map report'),
            ('media_filename', os.path.join(BaseModule.workspace, 'pushpin_media.html'), True, 'path and filename for pushpin media report'),
        ),
    }

    def remove_nl(self, x, repl=''):
        return re.sub('[\r\n]+', repl, self.html_escape(x))

    def build_content(self, sources):
        icons = {
            'flickr': 'http://maps.google.com/mapfiles/ms/icons/orange-dot.png',
            'instagram': 'http://maps.google.com/mapfiles/ms/icons/pink-dot.png',
            'picasa': 'http://maps.google.com/mapfiles/ms/icons/purple-dot.png',
            'shodan': 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png',
            'twitter': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
            'youtube': 'http://maps.google.com/mapfiles/ms/icons/red-dot.png',
        }
        media_content = ''
        map_content = ''
        map_arrays = ''
        map_checkboxes = ''
        for source in sources:
            count = source[0]
            source = source[1]
            map_arrays += 'var %s = [];\n' % (source.lower())
            map_checkboxes += '<input type="checkbox" id="%s" onchange="toggleMarkers(\'%s\');" checked="checked"/>%s<br />\n' % (source.lower(), source.lower(), source)
            media_content += '<div class="media_column %s">\n<div class="media_header"><div class="media_summary">%s</div>%s</div>\n' % (source.lower(), count, source.capitalize())
            items = self.query('SELECT * FROM pushpins WHERE source=?', (source,))
            items.sort(key=lambda x: x[9], reverse=True)
            for item in items:
                item = [self.to_unicode_str(x) if x != None else u'' for x in item]
                media_content += '<div class="media_row"><div class="prof_cell"><a href="%s" target="_blank"><img class="prof_img rounded" src="%s" /></a></div><div class="data_cell"><div class="trigger" id="trigger" lat="%s" lon="%s">[<a href="%s" target="_blank">%s</a>] %s<br /><span class="time">%s</span></div></div></div>\n' % (item[4], item[5], item[7], item[8], item[3], item[2], self.remove_nl(item[6], '<br />'), item[9])
                map_details = "<table><tr><td class='prof_cell'><a href='%s' target='_blank'><img class='prof_img rounded' src='%s' /></a></td><td class='data_cell'>[<a href='%s' target='_blank'>%s</a>] %s<br /><span class='time'>%s</span></td></tr></table>" % (item[4], item[5], item[3], self.remove_nl(item[2]), self.remove_nl(item[6], '<br />'), item[9])
                map_content += 'add_marker({position: new google.maps.LatLng(%s,%s),title:"%s",icon:"%s",map:map},{details:"%s"}, "%s");\n' % (item[7], item[8], self.remove_nl(item[2]), icons[source.lower()], map_details, source.lower())
            media_content += '</div>\n'
        return (media_content,), (map_content, map_arrays, map_checkboxes)

    def write_markup(self, template, filename, content):
        temp_content = open(template).read()
        page = temp_content % content
        with codecs.open(filename, 'wb', 'utf-8') as fp:
            fp.write(page)

    def module_run(self):
        sources = self.query('SELECT COUNT(source), source FROM pushpins GROUP BY source')
        media_content, map_content = self.build_content(sources)
        meta_content = (self.options['latitude'], self.options['longitude'], self.options['radius'])
        # create the media report
        media_content = meta_content + media_content
        media_filename = self.options['media_filename']
        self.write_markup(os.path.join(self.data_path, 'template_media.html'), media_filename, media_content)
        self.output('Media data written to \'%s\'' % (media_filename))
        # order the map_content tuple
        map_content = meta_content + map_content
        order=[4,0,1,2,3,5]
        map_content = tuple([map_content[i] for i in order])
        # create the map report
        map_filename = self.options['map_filename']
        self.write_markup(os.path.join(self.data_path, 'template_map.html'), map_filename, map_content)
        self.output('Mapping data written to \'%s\'' % (map_filename))
        # open the reports in a browser
        w = webbrowser.get()
        w.open(media_filename)
        time.sleep(2)
        w.open(map_filename)
