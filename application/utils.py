
class FileTypeException(Exception):

    def __init__(self, message):
        self.message = message


ordered_brownfield_register_fields = ['OrganisationURI',
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


temp_fields_seen_in_register = ['OrganisationURI',
                                'OrganisationLabel',
                                'SiteReference',
                                'name',
                                'notes',
                                'FirstaddedDate']

def to_boolean(value):
    if value is None:
        return False
    if str(value).lower() in ['1', 't', 'true', 'y', 'yes', 'on']:
        return True
    return False


def convert_to_csv_if_needed(filename):
    import subprocess
    try:
        if filename.endswith('.xls') or filename.endswith('.xlsx'):
            with open(f'{filename}.csv', 'w') as out:
                subprocess.check_call(['in2csv', filename], stdout=out)
            return f'{filename}.csv'
        elif filename.endswith('.xlsm'):
            with open(f'{filename}.csv', 'w') as out:
                subprocess.check_call(['xlsx2csv', filename], stdout=out)
            return f'{filename}.csv'
        else:
            return filename
    except Exception as e:
        msg = 'Could not convert %s into csv' % filename
        raise FileTypeException(msg)
