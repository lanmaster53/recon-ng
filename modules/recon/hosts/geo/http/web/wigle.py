import module
# unique to module
from cookielib import CookieJar
import math
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('username', None, 'yes', 'wigle account username')
        self.register_option('password', None, 'yes', 'wigle account password')
        self.register_option('latitude', None, 'yes', 'latitude of center point')
        self.register_option('longitude', None, 'yes', 'longitude of center point')
        self.register_option('radius', 0.1, 'yes', 'radius in km from center point to search')
        self.info = {
                     'Name': 'WiGLE Access Point Finder',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages WiGLE.net to return a list of Access Points in promixity to the given location.',
                     'Comments': []
                     }

    # degrees to radians
    def deg2rad(self, degrees):
        return math.pi*degrees/180.0

    # radians to degrees
    def rad2deg(self, radians):
        return 180.0*radians/math.pi

    # Earth radius at a given latitude, according to the WGS-84 ellipsoid [m]
    def WGS84EarthRadius(self, lat):
        # Semi-axes of WGS-84 geoidal reference
        WGS84_a = 6378137.0  # Major semiaxis [m]
        WGS84_b = 6356752.3  # Minor semiaxis [m]
        # http://en.wikipedia.org/wiki/Earth_radius
        An = WGS84_a*WGS84_a * math.cos(lat)
        Bn = WGS84_b*WGS84_b * math.sin(lat)
        Ad = WGS84_a * math.cos(lat)
        Bd = WGS84_b * math.sin(lat)
        return math.sqrt( (An*An + Bn*Bn)/(Ad*Ad + Bd*Bd) )

    # Bounding box surrounding the point at given coordinates,
    # assuming local approximation of Earth surface as a sphere
    # of radius given by WGS84
    def boundingBox(self, latitudeInDegrees, longitudeInDegrees, halfSideInKm):
        lat = self.deg2rad(latitudeInDegrees)
        lon = self.deg2rad(longitudeInDegrees)
        halfSide = 1000*halfSideInKm

        # Radius of Earth at given latitude
        radius = self.WGS84EarthRadius(lat)
        # Radius of the parallel at given latitude
        pradius = radius*math.cos(lat)

        latMin = lat - halfSide/radius
        latMax = lat + halfSide/radius
        lonMin = lon - halfSide/pradius
        lonMax = lon + halfSide/pradius

        return (self.rad2deg(latMin), self.rad2deg(lonMin), self.rad2deg(latMax), self.rad2deg(lonMax))

    def module_run(self):
        coords = self.boundingBox(self.options['latitude'], self.options['longitude'], self.options['radius'])
        latrange1 = coords[0]
        longrange1 = coords[1]
        latrange2 = coords[2]
        longrange2 = coords[3]
        payload = {}
        payload['credential_0'] = self.options['username']
        payload['credential_1'] = self.options['password']
        payload['destination'] = '/'
        cookiejar = CookieJar()
        resp = self.request('https://wigle.net/gps/gps/main/login/', method='POST', payload=payload, redirect=False, cookiejar=cookiejar)
        cookiejar = resp.cookiejar
        payload = {}
        payload['latrange1'] = str(latrange1)
        payload['latrange2'] = str(latrange2)
        payload['longrange1'] = str(longrange1)
        payload['longrange2'] = str(longrange2)
        nodes = []
        page = 1
        while True:
            resp = self.request('https://wigle.net/gps/gps/main/confirmquery/', payload=payload, cookiejar=cookiejar)
            if 'too many queries' in resp.text:
                self.alert('You\'re account has reached its daily limit of API queries.')
                break
            header = re.findall('<th class="searchhead">(.*?)</th>', resp.text)
            pattern = '<tr class="search".*?href="(.*?)">Get Map</a></td>\s<td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>'
            nodes.extend(re.findall(pattern, resp.text.replace('&nbsp;', ''), re.DOTALL))
            if not 'Next100 >>' in resp.text:
                break
            payload['pagestart'] = page * 100
            page +=1
        if nodes:
            tdata = []
            for node in nodes:
                tdata.append([node[1], node[2], node[4], node[9], node[11], node[12], node[13], node[16]])
            self.table(tdata, header=header)
            self.output('%d access points found.' % (len(nodes)-1))
        else:
            self.output('No access points found.')
