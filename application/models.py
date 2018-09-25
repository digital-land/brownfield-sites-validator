from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB


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


class BrownfieldSitePublication(db.Model):

    publication = db.Column(db.String(64), primary_key=True)
    organisation_id = db.Column(db.String(64), ForeignKey('organisation.organisation',
                                                          name='brownfield_publication_organisation_fkey'))
    data_url = db.Column(db.Text)
    geojson = db.Column(JSONB)
    validation_result = db.Column(JSONB)