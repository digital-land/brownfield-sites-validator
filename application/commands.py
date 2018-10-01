import csv
import json
from contextlib import closing
from urllib.request import urlopen

import ijson
from ijson import common

import boto3
import click
import frontmatter
import requests
from flask.cli import with_appcontext

from application.extensions import db
from application.frontend.views import _get_data_and_validate
from application.models import BrownfieldSitePublication, Organisation, Feature, ValidationResult

json_to_geo_query = "SELECT ST_SetSRID(ST_GeomFromGeoJSON('%s'), 4326);"


def floaten(event):
    if event[1] == 'number':
        return (event[0], event[1], float(event[2]))
    else:
        return event


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

    org_feature_mappings = {}

    item_url = '%s/organisation.tsv' % s3_bucket_url
    print('Loading', item_url)
    with closing(requests.get(item_url, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            org = row['organisation']
            if 'local-authority' in org or 'national-park' in org:
                if not db.session.query(Organisation).get(org):
                    organisation = Organisation(organisation=org,
                                                name=row['name'],
                                                website=row['website'])
                    db.session.add(organisation)
                    db.session.commit()

                    if row.get('feature') is not None:
                        org_feature_mappings[row.get('feature')] = org

    features_url = '%s/feature/local-authority-districts.geojson' % s3_bucket_url
    load_features(features_url, org_feature_mappings)

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

            if BrownfieldSitePublication.query.get(publication) is None:
                try:
                    organisation = Organisation.query.get(organisation)
                    brownfield_site = BrownfieldSitePublication(publication=publication,
                                                                organisation=organisation,
                                                                data_url=data_url,
                                                                geojson=geojson)
                    db.session.add(brownfield_site)
                    db.session.commit()

                except Exception as e:
                    print('Error saving site for', organisation)

        except Exception as e:
            print('Error loading', url, e)

    print('Done')

    db.session.execute('CLUSTER feature USING idx_feature_geometry')


@click.command()
@with_appcontext
def validate():
    sites = BrownfieldSitePublication.query.all()
    for site in sites:
        try:
            print('Validating', site.data_url)
            validation = _get_data_and_validate(site.data_url)
            site.validation_result = validation.to_dict()
            db.session.add(site)
            db.session.commit()
            print('Added data from', site.data_url)

        except Exception as e:
            print('error', e)

    print('Done')


def load_features(features_url, org_feature_mappings):

    print('Loading', features_url)

    try:
        if features_url.startswith('http'):
            f = urlopen(features_url)
        else:
            f = open(features_url, 'rb')
        events = map(floaten, ijson.parse(f))
        data = common.items(events, 'features.item')

        for feature in data:
            id = feature['properties'].get('feature')
            item = 'item:%s' % feature['properties'].get('item')
            publication = feature['properties'].get('publication')
            feature_id = id if id is not None else item

            if Feature.query.get(feature_id) is None:
                try:
                    org = Organisation.query.get(org_feature_mappings[feature_id])
                    geojson = json.dumps(feature['geometry'])
                    geometry = db.session.execute(json_to_geo_query % geojson).fetchone()[0]

                    feature = Feature(feature=feature_id,
                                      item=item,
                                      publication=publication,
                                      geometry=geometry,
                                      geojson=feature['geometry'])

                    org.feature_id = feature_id

                    db.session.add(feature)
                    db.session.add(org)

                    db.session.commit()
                except Exception as e:
                    print(e)

    except Exception as e:
        print(e)
        print('Error loading', features_url)
    finally:
        try:
            f.close()
        except:
            pass


@click.command()
@with_appcontext
def clear():
    db.session.query(ValidationResult).delete()
    db.session.query(BrownfieldSitePublication).delete()
    db.session.query(Organisation).delete()
    db.session.query(Feature).delete()
    db.session.commit()
    print('cleared db')