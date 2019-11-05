import codecs
import collections
import csv
import os
import tempfile

from cchardet import UniversalDetector
from flask import current_app
from werkzeug.utils import secure_filename
from application.validation.schema import brownfield_site_schema


class FileTypeException(Exception):

    def __init__(self, message):
        self.message = message


original_brownfield_register_fields = ['OrganisationURI',
                                       'OrganisationLabel',
                                       'SiteReference',
                                       'PreviouslyPartOf',
                                       'SiteNameAddress',
                                       'SitePlanURL',
                                       'CoordinateReferenceSystem',
                                       'GeoX',
                                       'GeoY',
                                       'Hectares',
                                       'OwnershipStatus',
                                       'Deliverable',
                                       'PlanningStatus',
                                       'PermissionType',
                                       'PermissionDate',
                                       'PlanningHistory',
                                       'ProposedForPIP',
                                       'MinNetDwellings',
                                       'DevelopmentDescription',
                                       'NonHousingDevelopment',
                                       'Part2',
                                       'NetDwellingsRangeFrom',
                                       'NetDwellingsRangeTo',
                                       'HazardousSubstances',
                                       'SiteInformation',
                                       'Notes',
                                       'FirstAddedDate',
                                       'LastUpdatedDate']

temp_fields_seen_in_register = ['OrganisationURI',
                                'OrganisationLabel',
                                'SiteReference',
                                'name',
                                'notes',
                                'FirstaddedDate']


def brownfield_standard_fields():
  deprecated_fields = set(original_brownfield_register_fields) - set(current_standard_fields)
  return {
    "expected": sorted(current_standard_fields),
    "deprecated": deprecated_fields
  }

current_standard_fields = [item['name'] for item in brownfield_site_schema['fields']]
columns_to_ignore = set(original_brownfield_register_fields) - set(current_standard_fields)


# To do: should this be somewhere else?
def check_headers(report):
  bf_fields = brownfield_standard_fields()
  report_headers = report.headers()
  headers_status = "Headers correct"

  for header in bf_fields["expected"]:
    if header not in report_headers:
      return "Missing headers"
  for header in bf_fields["deprecated"]:
    if header in report_headers:
      return "Warnings"
  if report.additional_headers().length > 0:
    return "Extra headers"


def to_boolean(value):
    if value is None:
        return False
    if str(value).lower() in ['1', 't', 'true', 'y', 'yes', 'on']:
        return True
    return False


def convert_to_csv_if_needed(filename):
    import subprocess
    try:
        if filename.endswith('.xls'):
            with open(f'{filename}.csv', 'w') as out:
                subprocess.check_call(['in2csv', filename], stdout=out)
            return f'{filename}.csv', filename.split('.')[-1]
        elif filename.endswith('.xlsm'):
            with open(f'{filename}.csv', 'w') as out:
                subprocess.check_call(['xlsx2csv', filename], stdout=out)
            return f'{filename}.csv' 'xlsm'
        else:
            return filename, 'csv'
    except Exception as e:
        msg = 'Could not convert %s into csv' % filename
        raise FileTypeException(msg)


def extract_and_normalise_data(upload_data):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = f'{temp_dir}/data'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = secure_filename(upload_data.filename)
        file = os.path.join(output_dir, filename)
        upload_data.save(file)
        try:
            file, file_type = convert_to_csv_if_needed(file)
            data, headers_found, additional_headers, planning_authority = process_csv_file(file)
            return {'data': data,
                    'headers_found': headers_found,
                    'additional_headers': additional_headers,
                    'file_type': file_type,
                    'planning_authority': planning_authority}
        except Exception as e:
            current_app.logger.exception(e)
            raise e


def process_csv_file(csv_file):
    # TODO fixup column names
    # TODO get planning authority name from opendatacommunities
    rows = []
    encoding = detect_encoding(csv_file)
    planning_authority = None
    with codecs.open(csv_file, encoding=encoding['encoding']) as f:
        reader = csv.DictReader(f)
        additional_headers = set(reader.fieldnames) - set(current_standard_fields)
        for row in reader:
            r = collections.OrderedDict()
            if planning_authority is None:
                planning_authority = row.get('OrganisationLabel', 'Unknown')
            for column in brownfield_standard_fields()['expected']:
                r[column] = row.get(column, None)
            rows.append(r)
    return rows, reader.fieldnames, list(additional_headers), planning_authority


def detect_encoding(file):
    detector = UniversalDetector()
    detector.reset()
    with open(file, 'rb') as f:
        for row in f:
            detector.feed(row)
            if detector.done:
                break
    detector.close()
    return detector.result
