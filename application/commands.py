import json

import boto3
import click
import frontmatter
import requests
from flask.cli import with_appcontext

from application.extensions import db
from application.frontend.views import _get_data_and_validate
from application.models import BrownfieldSitePublication


@click.command()
@with_appcontext
def load():

    from flask import current_app
    from application.extensions import db

    s3_region = current_app.config['S3_REGION']
    s3_bucket = current_app.config['S3_BUCKET']
    s3_bucket_url = 'http://%s.s3.amazonaws.com' % s3_bucket
    s3 = boto3.resource('s3', region_name=s3_region)
    bucket = s3.Bucket(s3_bucket)
    urls = ['%s/%s' % (s3_bucket_url, file.key) for file in bucket.objects.filter(Prefix='publication/brownfield-sites')]

    for url in urls:

        try:
            content = requests.get(url).content.decode('utf-8')
            c = frontmatter.loads(content)
            publication = c.metadata['publication']
            organisation = c.metadata['organisation']
            data_url = c.metadata['data-url']

            geojson_url = '%s/feature/%s.geojson' % (s3_bucket_url, publication)
            geojson = requests.get(geojson_url).json()

            brownfield_site = BrownfieldSitePublication(publication=publication,
                                                        organisation=organisation,
                                                        data_url=data_url,
                                                        geojson=geojson)
            db.session.add(brownfield_site)
            db.session.commit()

        except Exception as e:
            print('Error loading', url, e)

    print('Done')


@click.command()
@with_appcontext
def validate():
    sites = BrownfieldSitePublication.query.all()
    for site in sites:
        print('Validating', site.data_url)
        try:
            validation = _get_data_and_validate(site.data_url)
            site.validation_result = validation.to_dict()
            db.session.add(site)
            db.session.commit()
            print('Added data from', site.data_url)
        except Exception as e:
            print('error', e)

    print('Done')