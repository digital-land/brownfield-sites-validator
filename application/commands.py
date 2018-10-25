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
from application.frontend.views import get_data_and_validate
from application.models import BrownfieldSiteValidation, Organisation

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

    features_url = '%s/feature/national-park-boundary.geojson' % s3_bucket_url
    load_features(features_url, org_feature_mappings)
    db.session.execute('CLUSTER organisation USING idx_organisation_geometry')

    urls = ['%s/%s' % (s3_bucket_url, file.key) for file in bucket.objects.filter(Prefix='publication/brownfield-sites')]

    for url in urls:

        try:
            content = requests.get(url).content.decode('utf-8')
            c = frontmatter.loads(content)
            publication = c.metadata['publication']
            organisation = c.metadata['organisation']
            copyright = c.metadata['copyright']
            licence = c.metadata['licence']
            data_url = c.metadata['data-url']
            suffix = c.metadata.get('suffix')

            geojson_url = '%s/feature/%s.geojson' % (s3_bucket_url, publication)
            geojson = requests.get(geojson_url).json()

            try:
                organisation = Organisation.query.get(organisation)
                organisation.brownfield_register_url = data_url
                organisation.brownfield_register_copyright = copyright
                organisation.brownfield_register_licence = licence
                organisation.brownfield_register_publication = publication
                organisation.brownfield_register_geojson = geojson
                organisation.brownfield_register_suffix = suffix

                db.session.add(organisation)
                db.session.commit()

            except Exception as e:
                print('Error saving site for', organisation)

        except Exception as e:
            print('Error loading', url, e)

    print('Done')


@click.command()
@with_appcontext
def validate():
    organisations = Organisation.query.all()
    for organisation in organisations:
        try:
            if organisation.brownfield_register_url is not None:
                print('Validating', organisation.brownfield_register_url)
                validation = get_data_and_validate(organisation, organisation.brownfield_register_url)
                print('Added data from',  organisation.brownfield_register_url)
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
            feature_id = id if id is not None else item
            try:
                org = Organisation.query.get(org_feature_mappings[feature_id])
                geojson = json.dumps(feature['geometry'])
                org.geometry = db.session.execute(json_to_geo_query % geojson).fetchone()[0]
                org.geojson = feature['geometry']
                db.session.add(org)
                db.session.commit()
            except KeyError as e:
                print('No organisation for feature', feature_id)
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
    db.session.query(BrownfieldSiteValidation).delete()
    db.session.query(Organisation).delete()

    db.session.commit()
    print('cleared db')