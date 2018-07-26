from sqlalchemy.dialects.postgresql import JSONB

from application.extensions import db


class BrownfieldSitePublication(db.Model):

    publication = db.Column(db.String(64), primary_key=True)
    organisation = db.Column(db.String(64))
    data_url = db.Column(db.Text)
    geojson = db.Column(JSONB)
    validation_result = db.Column(JSONB)