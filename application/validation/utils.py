import codecs
import collections
import csv
import os
import tempfile

from cchardet import UniversalDetector

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


current_standard_fields = [item['name'] for item in brownfield_site_schema['fields']]
columns_to_ignore = set(original_brownfield_register_fields) - set(current_standard_fields)


def brownfield_standard_fields():
    deprecated_fields = set(original_brownfield_register_fields) - set(current_standard_fields)
    return {
        "expected": sorted(current_standard_fields),
        "deprecated": deprecated_fields
    }


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
            return f'{filename}.csv', 'xlsm'
        else:
            return filename, 'csv'
    except Exception as e:
        msg = f"We could not convert {filename.split('/')[-1]} into csv"
        raise FileTypeException(msg)


def extract_data(upload_data, filename):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = f'{temp_dir}/data'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        file = os.path.join(output_dir, filename)
        upload_data.save(file)
        file, original_file_type = convert_to_csv_if_needed(file)
        data = csv_to_dict(file)
        data['file_type'] = original_file_type
        return data


def csv_to_dict(csv_file):
    # TODO fixup column names?
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
    return {'data': rows,
            'headers_found': reader.fieldnames,
            'additional_headers': list(additional_headers),
            'planning_authority': planning_authority}


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


def get_markdown_for_field(field_name):
    from pathlib import Path
    current_directory = Path(__file__).parent.resolve()
    markdown_file = Path(current_directory, 'markdown', f'{field_name}.md')
    with open(markdown_file) as f:
        content = f.read()
    return content