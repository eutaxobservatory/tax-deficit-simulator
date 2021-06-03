"""
This module provides several functions useful to run the simulations defined in "calculator.py" or "firm_level.py".

It also provides various utils for the "app.py" file, especially to add file download buttons.
"""


# ----------------------------------------------------------------------------------------------------------------------
# --- Imports

import base64
import os


# ----------------------------------------------------------------------------------------------------------------------
# --- Paths to files that can be downloaded from the simulator

path_to_files = os.path.dirname(os.path.abspath(__file__))
path_to_files = os.path.join(path_to_files, 'files')


# ----------------------------------------------------------------------------------------------------------------------
# --- Utils for the calculator.py file


COUNTRIES_WITH_MINIMUM_REPORTING = ['KOR', 'NLD', 'IRL', 'FIN']
COUNTRIES_WITH_CONTINENTAL_REPORTING = ['AUT', 'NOR', 'SVN', 'SWE']


def rename_partner_jurisdictions(row):
    """
    In the OECD data, each reporting country displays a line "Foreign Jurisdictions Total", which displays the sum of
    revenues, profits, corporate income taxes paid, etc. for the parent country across all foreign partner jurisdic-
    tions. In most cases, we want to eliminate this total to avoid any double-counting. But some countries (see list of
    alpha-3 codes above) only display a domestic vs. foreign breakdown and in these cases, it is important that we do
    not erase the "Foreign Jurisdictions Total" line. Therefore, we slightly rename it for these countries.
    """

    if row['Parent jurisdiction (alpha-3 code)'] in COUNTRIES_WITH_MINIMUM_REPORTING:

        if row['Partner jurisdiction (whitespaces cleaned)'] == 'Foreign Jurisdictions Total':
            return 'Foreign Total'

        else:
            return row['Partner jurisdiction (whitespaces cleaned)']

    else:
        return row['Partner jurisdiction (whitespaces cleaned)']


def manage_overlap_with_domestic(row, kind):
    """
    When cleaning and preprocessing the OECD data, we introduce several indicator variables:

    - one that takes value 1 if and only if the partner jurisdiction is a tax haven;
    - another that takes value 1 if and only if the partner jurisdiction is a non-haven country;
    - and a last one that indicates whether the parent and partner jurisdictions coincide.

    In the breakdown of the total tax deficit into domestic, tax-haven-based and non-haven tax deficits, we need to
    avoid any double-counting and two of these indicator variables cannot take the value 1 simultaneously.

    We therefore give the priority to the "Is domestic?" indicator variable: no matter whether the jurisdiction is a tax
    haven or not, this indicator variable takes the value 1 if the parent and partner are the same, while the other in-
    dicator variables are set to 0.
    """
    if row['Is domestic?']:
        return 0

    else:
        if kind == 'haven':
            return row['Is partner jurisdiction a tax haven?']
        elif kind == 'non-haven':
            return row['Is partner jurisdiction a non-haven?']


def combine_haven_tax_deficits(row):
    """
    This function is used to compute the tax deficit of all in-sample headquarter countries in the multilateral imple-
    mentation scenario.

    For parent countries that are in both the OECD and TWZ data, we have two different sources to compute their tax-
    haven-based tax deficit and we retain the highest of these two amounts.

    Besides, for parent countries in the OECD data that do not report a fully detailed country-by-country breakdown of
    the activity of their multinationals, we cannot distinguish their tax-haven and non-haven tax deficits. Quite arbi-
    trarily in the Python code, we attribute everything to the non-haven tax deficit. In the Table A1 of the report,
    these specific cases are described with the "Only foreign aggregate data" column.
    """
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
    """
    This function is used in the "firm_level.py" file to determine, for each partner jurisdiction where the multinatio-
    nal is active, what effective tax rate should be used. When we can, we compute the ETR on a cash basis as the ratio
    of the amount of corporate income taxes paid to profit before tax.

    If this computation yields an error (0 profit before tax or NaN value at the numerator or denominator):

    - for non-bank multinationals, we take the statutory corporate income tax rate of the partner jurisdiction;

    - for banks, we take the average ETR faced by the multinational in this jurisdiction over the last 6 years.

    Besides, for banks, if the computed ETR is negative, we replace it by the pre-computed average ETR.
    """

    if kind == 'mne':
        # In the case of a non-bank multinational
        if row['Partner jurisdiction code'] in ADDITIONAL_ETRs.keys():
            return ADDITIONAL_ETRs[row['Partner jurisdiction code']]

        else:
            try:
                effective_tax_rate = row['CIT paid'] / row['Profit before tax']

            except:
                # If the usual computation yields an error, we use the statutory corporate tax rate
                effective_tax_rate = row['Statutory CIT rate']

            return effective_tax_rate

    elif kind == 'bank':
        # In the case of a bank
        try:
            effective_tax_rate = row['CIT paid'] / row['Profit before tax']

        except:
            # If the usual computation yields an error, we use the average ETR computed over the last 6 years
            effective_tax_rate = row['Average ETR over 6 years']

        if effective_tax_rate < 0:
            # If the ETR computed on a cash basis is negative, we replace it with the average ETR
            effective_tax_rate = row['Average ETR over 6 years']

        return effective_tax_rate


# ----------------------------------------------------------------------------------------------------------------------
# --- Utils for the app.py file

def get_table_download_button(df, scenario, effective_tax_rate, company=None, taxing_country=None):
    """
    This function is used in the "app.py" file to generate the HTML code that instantiates the download button on the
    following pages: "Case study with one multinational" (scenario=0), "Multilateral implementation scenario" (scenario
    =1), "Partial cooperation scenario" (scenario=2) and "Unilateral implementation scenario" (scenario=3).

    The HTML code is then injected in a st.markdown() component, the "allow_unsafe_html" argument being set to True.

    This sort of hack was found on Streamlit user forums.
    """

    # We output the DataFrame to a csv format
    csv = df.to_csv(index=False)

    # We encode the csv file in the right format
    b64 = base64.b64encode(csv.encode()).decode()

    href = f'<a href="data:file/csv;base64,{b64}"'

    if scenario == 0:
        # "Case study with one multinational" page
        company_name = company.lower().replace(' ', '_')

        href += f' download="{company_name}_{effective_tax_rate}_perc.csv">'

    elif scenario == 1:
        # "Multilateral implementation scenario" page
        href += f' download="multilateral_scenario_{effective_tax_rate}_perc.csv">'

    elif scenario == 2:
        # "Partial cooperation scenario" page
        href += f' download="partial_cooperation_scenario_{effective_tax_rate}_perc.csv">'

    elif scenario == 3:
        # "Unilateral implementation scenario" page
        taxing_country = taxing_country.lower().replace(' ', '_')

        if 'china' in taxing_country:
            taxing_country = 'china'

        href += f' download="unilateral_scenario_{taxing_country}_{effective_tax_rate}_perc.csv">'

    else:
        raise Exception('Value not accepted for the scenario argument.')

    href += '<input type="button" value="Click here to download the table" class="download-button table"></a>'

    return href


def get_report_download_button():
    """
    Following the same principle, this function builds the HTML code that instantiates the download button allowing the
    user to obtain the full-text version of the study in PDF format.
    """

    # We fetch and read the .pdf file from the files folder
    path = os.path.join(path_to_files, 'EUTO2021.pdf')

    with open(path, 'rb') as file:
        report_content = file.read()

    # We encode it to the right format
    b64 = base64.b64encode(report_content).decode()

    # And we build the HTML code
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(path)}">'

    href += '<input type="button" value="Click here to download the full-text report (PDF)" '

    href += 'class="download-button pdf"></a>'

    return href


def get_appendix_download_button():
    """
    Not yet used but following the same principle, this function builds the HTML code that will ultimately instantiate
    the download button allowing the user to obtain the main and appendix tables of the study in Excel format.
    """

    # We fetch and read the .xlsx file from the files folder
    path = os.path.join(path_to_files, 'test.xlsx')

    with open(path, 'rb') as file:
        excel_content = file.read()

    # We encode it in the right format
    b64 = base64.b64encode(excel_content).decode()

    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(path)}">'

    href += '<input type="button" value="Click here to download the appendix tables (Excel)" '

    href += 'class="download-button excel"></a>'

    return href
