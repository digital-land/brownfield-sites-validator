import csv
import datetime
import io

import pyproj
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSON

from application.extensions import db
from application.utils import ordered_brownfield_register_fields


class StaticContent(db.Model):

    filename = db.Column(db.Text, primary_key=True)
    content = db.Column(db.Text)

class BrownfieldSiteRegister(db.Model):

    organisation = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))
    website = db.Column(db.String(256))
    geometry = db.Column(Geometry(srid=4326))
    geojson = db.Column(JSON)

    publication = db.Column(db.String(64))
    register_url = db.Column(db.Text)
    publication_copyright = db.Column(db.String(64))
    publication_licence = db.Column(db.String(64))
    publication_suffix = db.Column(db.String(64))
    register_geojson = db.Column(JSON)

    data_source = db.Column(db.Text)
    validation_result = db.Column(JSON)
    validation_data = db.Column(JSON)
    validation_created_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

    def validation_has_geo_fixes(self):
        return self.validation_result['has_geo_fixes']

    def validation_geojson(self, with_fixes=False):
        geo = {'features': [], 'type': 'FeatureCollection'}
        for d in self.validation_data:
            if d.get('content'):
                content = d['content']
            else:
                content = d
            longitude = float(content['GeoX'].strip())
            latitude = float(content['GeoY'].strip())

            coord_ref_system = content.get('CoordinateReferenceSystem')

            if coord_ref_system == 'ETRS89' and not (-5.5 < longitude < 2):
                if (-5.5 < latitude < 2) and (49 < longitude < 60):
                    # probably a swapped lat/long
                    longitude, latitude = latitude, longitude
                else:
                    etrs89 = pyproj.Proj(init='epsg:3035')
                    wgs84 = pyproj.Proj(init='epsg:4326')
                    longitude, latitude = pyproj.transform(etrs89, wgs84, longitude, latitude)

            if coord_ref_system == 'OSGB36' or (longitude > 10000.0 and coord_ref_system != 'ETRS89'):
                bng = pyproj.Proj(init='epsg:27700')
                wgs84 = pyproj.Proj(init='epsg:4326')
                longitude, latitude = pyproj.transform(bng, wgs84, longitude, latitude)

            if with_fixes and self.has_geo_fixes():
                lng_fix = [f for f in d['validation_result']['GeoX'] if f.get('warning') and f.get('warning').get('type') == 'LOCATION_WARNING']
                lat_fix = [f for f in d['validation_result']['GeoY'] if f.get('warning') and f.get('warning').get('type') == 'LOCATION_WARNING']

                longitude = lng_fix[0]['fix'] if lng_fix else longitude
                latitude = lat_fix[0]['fix'] if lat_fix else latitude

            feature = {
                'geometry': {
                    'coordinates': [
                        longitude,
                        latitude
                    ],
                    'type': 'Point'
                },
                'properties': {
                    'SiteReference': content.get('SiteReference', ''),
                    'SiteNameAddress': content.get('SiteNameAddress', ''),
                    'PlanningStatus': content.get('PlanningStatus', '')
                },
                'type': 'Feature'
            }
            geo['features'].append(feature)
        return geo

    def get_fixed_data(self):
        output = io.StringIO()
        writer = csv.DictWriter(output, ordered_brownfield_register_fields, lineterminator='\n')
        writer.writeheader()
        for row in self.validation_data:
            original_data = row['content']
            fixed_data = {}
            for key, val in original_data.items():
                fix = self._get_any_fixes(key, row['validation_result'])
                if fix is not None:
                    fixed_data[key] = fix
                else:
                    fixed_data[key] = val

            fixed_data = self.clean(fixed_data)
            writer.writerow(fixed_data)
        return output.getvalue()

    @staticmethod
    def _get_any_fixes(key, validation_result):
        candidates = validation_result.get(key)
        if candidates is not None:
            for c in candidates:
                if c.get('fix') is not None:
                    return c.get('fix')
        return None

    @staticmethod
    def clean(fixed_data):
        cleaned = {}
        for key in fixed_data.keys():
            if key in ordered_brownfield_register_fields:
                cleaned[key] = fixed_data[key]
        return cleaned
