import os
import tempfile

from werkzeug.utils import secure_filename
from application.validation.schema import brownfield_site_schema

current_standard_fields = [item['name'] for item in brownfield_site_schema['fields']]

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
    "expected": current_standard_fields,
    "deprecated": deprecated_fields
  }


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
            data, additional_fields = process_csv_file(file)
            return data, additional_fields
        except Exception as e:
            print(e)
            return {'error': str(e)}, {}


def process_csv_file(csv_file):
    import pandas as pd
    df = pd.read_csv(csv_file, na_filter= False, encoding='ISO-8859-1')

    # TODO fixup column names

    columns_to_ignore = set(original_brownfield_register_fields) - set(current_standard_fields)
    additional_columns = set(df.columns) - set(current_standard_fields)
    df.drop(columns_to_ignore, axis=1, inplace=True)
    return df.to_dict(orient='records'), list(additional_columns)