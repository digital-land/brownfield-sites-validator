import datetime

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from application.extensions import db


class Organisation(db.Model):

    organisation = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))
    website = db.Column(db.String(256))
    geometry = db.Column(Geometry(srid=4326))
    geojson = db.Column(JSONB)

    brownfield_register_publication = db.Column(db.String(64))
    brownfield_register_url = db.Column(db.Text)
    brownfield_register_copyright = db.Column(db.String(64))
    brownfield_register_licence = db.Column(db.String(64))
    brownfield_register_suffix = db.Column(db.String(64))
    brownfield_register_geojson = db.Column(JSONB)

    validation_results = db.relationship('BrownfieldSiteValidation',
                                          back_populates='organisation',
                                          order_by='BrownfieldSiteValidation.created_date')

    @property
    def validation(self):
        if self.validation_results:
            return self.validation_results[0]
        else:
            return None


class BrownfieldSiteValidation(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    data_source = db.Column(db.Text)
    result = db.Column(JSONB)
    data = db.Column(JSONB)
    created_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

    organisation_id = db.Column(db.String(64), ForeignKey('organisation.organisation'))
    organisation = relationship('Organisation', back_populates="validation_results")

    def geojson(self):
        geo = {'features': [], 'type': 'FeatureCollection'}
        for d in self.data:
            feature = {
                'geometry': {
                    'coordinates': [
                        float(d['GeoX']),
                        float(d['GeoY'])
                    ],
                    'type': 'Point'
                },
                'properties': {
                    'SiteNameAddress': d.get('SiteNameAddress', '')
                },
                'type': 'Feature'
            }
            geo['features'].append(feature)
        return geo
