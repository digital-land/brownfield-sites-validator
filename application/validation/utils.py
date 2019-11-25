import codecs
import collections
import csv
import json
from subprocess import CalledProcessError

from cchardet import UniversalDetector


class FileTypeException(Exception):

    def __init__(self, message):
        self.message = message


class BrownfieldStandard:

    @staticmethod
    def v1_standard_headers():
        return ['OrganisationURI',
                'OrganisationLabel',
                'SiteReference',
                'PreviouslyPartOf',
                'SiteNameAddress',
                'SiteplanURL',
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

    @staticmethod
    def v2_standard_schema():
        import os
        schema_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema', 'brownfield-land-v2.json')
        with open(schema_json) as f:
            schema = json.load(f)
        return schema

    @staticmethod
    def v2_standard_headers():
        schema = BrownfieldStandard.v2_standard_schema()
        return [item['name'] for item in schema['fields']]

    @staticmethod
    def headers_deprecated():
        return list(set(BrownfieldStandard.v1_standard_headers()) - set(BrownfieldStandard.v2_standard_headers()))


def try_convert_to_csv(filename):
    import subprocess
    try:
        try:
            with open(f'{filename}.csv', 'w') as out:
                subprocess.check_call(['in2csv', filename], stdout=out)
                return f'{filename}.csv', 'xls'
        except CalledProcessError as e:
            print(e)
            raise Exception
        try:
            with open(f'{filename}.csv', 'w') as out:
                subprocess.check_call(['xlsx2csv', filename], stdout=out)
            return f'{filename}.csv', 'xlsm'
        except CalledProcessError as e:
            print(e)
            raise Exception
    except Exception as e:  # noqa
        msg = f"We could not process {filename.split('/')[-1]} as a csv file"
        raise FileTypeException(msg)


def extract_data(file):
    original_file_type = 'csv'
    if not _looks_like_csv(file):
        file, original_file_type = try_convert_to_csv(file)
    return csv_to_dict(file, original_file_type)


def csv_to_dict(csv_file, original_file_type):
    rows = []
    data = []
    encoding = detect_encoding(csv_file)
    planning_authority = None
    with codecs.open(csv_file, encoding=encoding['encoding']) as f:
        reader = csv.DictReader(f)
        additional_headers = list(set(reader.fieldnames) - set(BrownfieldStandard.v2_standard_headers()))
        missing_headers = list(set(BrownfieldStandard.v2_standard_headers()) - set(reader.fieldnames))
        for row in reader:
            to_check = collections.OrderedDict()
            # TODO get planning authority name from opendatacommunities
            if planning_authority is None:
                planning_authority = row.get('OrganisationLabel', 'Unknown')
            for column in BrownfieldStandard.v2_standard_headers():
                value = row.get(column, None)
                if value is not None:
                    to_check[column] = row.get(column)
            rows.append(to_check)
            data.append(row)
    return {'rows': rows,
            'data': data,
            'meta_data': {
                'headers_found': reader.fieldnames,
                'additional_headers': additional_headers,
                'missing_headers': missing_headers,
                'planning_authority': planning_authority,
                'file_type': original_file_type}
            }


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


def _looks_like_csv(file):
    try:
        encoding = detect_encoding(file)
        with open(file, encoding=encoding['encoding']) as f:
            content = f.read()
            csv.Sniffer().sniff(content)
            return True
    except Exception as e:  # noqa
        print(e)
        return False
