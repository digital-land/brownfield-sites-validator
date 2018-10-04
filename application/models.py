import datetime

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from application.extensions import db


class Organisation(db.Model):

    organisation = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))
    website = db.Column(db.String(256))

    feature_id = db.Column(db.String(256), ForeignKey('feature.feature', name='organisation_feature_fkey'))
    feature = db.relationship('Feature', uselist=False)

    publication = db.relationship('BrownfieldSitePublication', backref='organisation', uselist=False)


class Feature(db.Model):

    feature = db.Column(db.String(256), primary_key=True)
    item = db.Column(db.String(256))
    data = db.Column(JSONB)
    geometry = db.Column(Geometry(srid=4326))
    name = db.Column(db.Text)
    publication = db.Column(db.String(64))
    geojson = db.Column(JSONB)


class BrownfieldSitePublication(db.Model):

    publication = db.Column(db.String(64), primary_key=True)
    organisation_id = db.Column(db.String(64), ForeignKey('organisation.organisation',
                                                          name='brownfield_publication_organisation_fkey'))
    geojson = db.Column(JSONB)
    data_url = db.Column(db.Text)

    # Check this - not sure it's the right thing?
    validation_results = relationship('ValidationResult', order_by='ValidationResult.created_date')

    @property
    def validation(self):
        if self.validation_results:
            return self.validation_results[0]
        else:
            return None


class ValidationResult(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(JSONB)
    data = db.Column(JSONB)
    created_date = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

    brownfield_site_publication_id = db.Column(db.String(64), ForeignKey('brownfield_site_publication.publication'))

    def geojson(self):
        data = {'features': [], 'type': 'FeatureCollection'}
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
                    'SiteNameAddress': d['SiteNameAddress']
                },
                'type': 'Feature'
            }

            data['features'].append(feature)

        return data