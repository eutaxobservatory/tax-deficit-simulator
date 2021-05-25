import base64
import os

path_to_files = os.path.dirname(os.path.abspath(__file__))
path_to_files = os.path.join(path_to_files, 'files')


# ----------------------------------------------------------------------------------------------------------------------
# --- Utils for the calculator.py file


COUNTRIES_WITH_MINIMUM_REPORTING = ['KOR', 'NLD', 'IRL', 'FIN']
COUNTRIES_WITH_CONTINENTAL_REPORTING = ['AUT', 'NOR', 'SVN', 'SWE']


def rename_partner_jurisdictions(row):

    if row['Parent jurisdiction (alpha-3 code)'] in COUNTRIES_WITH_MINIMUM_REPORTING:
        if row['Partner jurisdiction (whitespaces cleaned)'] == 'Foreign Jurisdictions Total':
            return 'Foreign Total'
        else:
            return row['Partner jurisdiction (whitespaces cleaned)']

    else:
        return row['Partner jurisdiction (whitespaces cleaned)']


def manage_overlap_with_domestic(row, kind):
    if row['Is domestic?']:
        return 0

    else:
        if kind == 'haven':
            return row['Is partner jurisdiction a tax haven?']
        elif kind == 'non-haven':
            return row['Is partner jurisdiction a non-haven?']


def combine_haven_tax_deficits(row):
    if row['Parent jurisdiction (alpha-3 code)'] not in (
        COUNTRIES_WITH_MINIMUM_REPORTING + COUNTRIES_WITH_CONTINENTAL_REPORTING
    ):
        return max(row['tax_deficit_x_tax_haven'], row['tax_deficit_x_tax_haven_TWZ'])

    else:
        return 0


# ----------------------------------------------------------------------------------------------------------------------
# --- Utils for the firm_level.py file

ADDITIONAL_ETRs = {
    'GEO': 0.15,
    'BLR': 0.18,
    'SOM': 0.05,
    'PNG': 0.3,
    'TLS': 0.1,
    'ABW': 0.25,
    'MOZ': 0.32,
    'GAB': 0.3,
    'CRI': 0.3
}


def compute_ETRs(row, kind):

    if kind == 'mne':
        if row['Partner jurisdiction code'] in ADDITIONAL_ETRs.keys():
            return ADDITIONAL_ETRs[row['Partner jurisdiction code']]

        else:
            try:
                effective_tax_rate = row['CIT paid'] / row['Profit before tax']

            except:
                effective_tax_rate = row['Statutory CIT rate']

            return effective_tax_rate

    elif kind == 'bank':
        try:
            effective_tax_rate = row['CIT paid'] / row['Profit before tax']

        except:
            effective_tax_rate = row['Average ETR over 6 years']

        if effective_tax_rate < 0:
            effective_tax_rate = row['Average ETR over 6 years']

        return effective_tax_rate


# ----------------------------------------------------------------------------------------------------------------------
# --- Utils for the app.py file

def get_table_download_button(df, scenario, effective_tax_rate, taxing_country=None):

    csv = df.to_csv(index=False)

    b64 = base64.b64encode(csv.encode()).decode()

    href = f'<a href="data:file/csv;base64,{b64}"'

    if scenario == 1:
        href += f' download="first_scenario_{effective_tax_rate}_perc.csv">'

    elif scenario == 2:
        taxing_country = taxing_country.lower().replace(' ', '_')

        if 'china' in taxing_country:
            taxing_country = 'china'

        href += f' download="second_scenario_{taxing_country}_{effective_tax_rate}_perc.csv">'

    else:
        raise Exception('Value not accepted for the scenario argument.')

    href += '<input type="button" value="Click here to download the table" class="download-button table"></a>'

    return href


def get_report_download_button():

    path = os.path.join(path_to_files, 'test.pdf')

    with open(path, 'rb') as file:
        report_content = file.read()

    b64 = base64.b64encode(report_content).decode()

    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(path)}">'

    href += '<input type="button" value="Click here to download the full-text report (PDF)" '

    href += 'class="download-button pdf"></a>'

    return href


def get_appendix_download_button():

    path = os.path.join(path_to_files, 'test.xlsx')

    with open(path, 'rb') as file:
        excel_content = file.read()

    b64 = base64.b64encode(excel_content).decode()

    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(path)}">'

    href += '<input type="button" value="Click here to download the appendix tables (Excel)" '

    href += 'class="download-button excel"></a>'

    return href
