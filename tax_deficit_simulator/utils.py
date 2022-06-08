"""
This module provides several functions useful to run the simulations defined in "calculator.py" or "firm_level.py".

It also provides various utils for the "app.py" file, especially to add file download buttons.
"""


# ----------------------------------------------------------------------------------------------------------------------
# --- Imports

import base64
import os
import json

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------------------------------------------------
# --- Paths to files that can be downloaded from the simulator

path_to_files = os.path.dirname(os.path.abspath(__file__))
path_to_files = os.path.join(path_to_files, 'files')

# ----------------------------------------------------------------------------------------------------------------------
# --- Utils for the calculator.py file

# This list is valid for both 2016 and 2017 dataset
COUNTRIES_WITH_MINIMUM_REPORTING = ['KOR', 'NLD', 'IRL', 'FIN']

# Correspondences between the country names used in TWZ data files and in our own set of country codes
country_name_corresp = {
    'BVI': 'British Virgin Islands',
    'Gribraltar': 'Gibraltar',
    'Isle of man': 'Isle of Man',
    'St. Kitts and Nevis': 'Saint Kitts and Nevis',
    'St. Lucia': 'Saint Lucia',
    'Turks and Caicos': 'Turks and Caicos Islands',
    'Bahamas, The': 'Bahamas'
}

# Opening the JSON file with the paths to the data files stored online
# path_to_data = os.path.dirname(os.path.abspath(__file__))
# path_to_data = os.path.join(path_to_data, 'data')

# with open(os.path.join(path_to_data, 'online_data_paths.json')) as file:
#     online_data_paths = json.load(file)

online_data_paths = {
    "path_to_eu_countries": "https://raw.githubusercontent.com/eutaxobservatory/tax-deficit-simulator/master/tax_deficit_simulator/data/listofeucountries_csv.csv",
    "path_to_tax_haven_list": "https://raw.githubusercontent.com/eutaxobservatory/tax-deficit-simulator/master/tax_deficit_simulator/data/tax_haven_list.csv",
    "path_to_geographies": "https://raw.githubusercontent.com/eutaxobservatory/tax-deficit-simulator/master/tax_deficit_simulator/data/geographies.csv",
    "path_to_twz_CIT": "https://raw.githubusercontent.com/eutaxobservatory/tax-deficit-simulator/master/tax_deficit_simulator/data/twz_CIT.csv",
    "path_to_statutory_rates": "https://github.com/eutaxobservatory/tax-deficit-simulator/raw/master/tax_deficit_simulator/data/statutory_rates.xlsx",
    "url_base": "https://raw.githubusercontent.com/eutaxobservatory/tax-deficit-simulator/master/tax_deficit_simulator/data/",
    "path_to_oecd": "https://raw.githubusercontent.com/eutaxobservatory/tax-deficit-simulator/master/tax_deficit_simulator/data/oecd.csv"
}



def load_and_clean_twz_main_data(
    path_to_excel_file,
    path_to_geographies
):
    """
    This function is used to load and preprocess the data compiled by TWZ on the profits booked by multinational compa-
    nies in tax havens. It simply takes as arguments the paths to the Excel file with TWZ data and to the CSV file with
    all the country codes. It returns a DataFrame that displays, for each headquarter country in TWZ' sample, the total
    amount of pre-tax profits booked in tax havens and the sum of positive profits only. Compared with the function
    "load_and_clean_bilateral_twz_data" defined below, it does not preserve the bilateral structure of the data source.
    """

    geographies = pd.read_csv(path_to_geographies)
    geographies = geographies[['NAME', 'CODE']].copy()

    twz = pd.read_excel(
        path_to_excel_file,
        sheet_name='TableC4',
        engine='openpyxl'
    )

    twz.drop(
        columns=['Unnamed: 0'] + list(twz.columns[-5:]),
        inplace=True
    )

    twz = twz.iloc[6:-3].copy()

    twz = twz[['Unnamed: 1', 'Unnamed: 2'] + list(twz.columns[-11:])].copy()

    column_names = list(twz.iloc[0, 1:]).copy()
    column_names[0] = 'All havens - Excessive high risk payments'

    twz.columns = ['Country'] + column_names

    twz = twz.iloc[2:].copy()

    twz.reset_index(drop=True, inplace=True)

    twz = twz[twz.isnull().sum(axis=1) != twz.isnull().sum(axis=1).max()].copy()

    twz.drop(
        columns=['All havens - Excessive high risk payments', 'All havens', 'EU havens', 'Non-EU tax havens'],
        inplace=True
    )

    for column in twz.columns[1:]:
        twz[column] = twz[column].fillna(0)

    twz = twz.dropna().reset_index(drop=True)

    twz = twz[
        ~twz['Country'].isin(
            [
                'OECD countries',
                'Main developing countries',
                'Non-OECD tax havens',
                'Rest of World',
                'Non-haven total',
                'Additional developing countries'
            ]
        )
    ].copy()

    twz['Country'] = twz['Country'].map(
        lambda country_name: country_name_corresp.get(country_name, country_name)
    )

    twz = twz.merge(
        geographies,
        how='left',
        left_on='Country', right_on='NAME'
    ).drop(columns='NAME')

    twz['Profits in all tax havens'] = twz[twz.columns[1:]].sum(axis=1)

    twz['Profits in all tax havens (positive only)'] = twz[twz.columns[1:]].apply(
        lambda row: row.iloc[:-2][row.iloc[:-2] >= 0].sum(),
        axis=1
    )

    for country_name in np.intersect1d(twz['Country'].unique(), twz.columns):

        twz[f'{country_name}_temp'] = (twz['Country'] == country_name)

        twz[f'{country_name}_temp'] = twz[country_name] * twz[f'{country_name}_temp']

        twz['Profits in all tax havens'] -= twz[f'{country_name}_temp']

        if (twz[f'{country_name}_temp'] > 0).sum() == 1:
            twz['Profits in all tax havens (positive only)'] -= twz[f'{country_name}_temp']

        twz.drop(columns=[f'{country_name}_temp'], inplace=True)

    twz = twz[['Country', 'CODE', 'Profits in all tax havens', 'Profits in all tax havens (positive only)']].copy()

    twz.rename(
        columns={
            'CODE': 'Alpha-3 country code'
        },
        inplace=True
    )

    if twz.isnull().sum().sum() > 0:
        raise Exception('Missing values remain in the TWZ data on tax haven profits.')

    return twz.reset_index(drop=True)


def load_and_clean_bilateral_twz_data(
    path_to_excel_file, path_to_geographies
):
    """
    This function is called when computing revenue gains under the QDMTT scenario, to preprocess the TWZ data on the
    profits booked in tax havens. Compared with the "load_and_clean_twz_main_data" function defined above, it preserves
    the bilateral structure of the data (to then attribute top-up taxes to the source / partner jurisdiction). It simply
    takes as arguments the paths to the Excel file with TWZ data and to the CSV file with all the country codes.
    """
    geographies = pd.read_csv(path_to_geographies)
    geographies = geographies[['NAME', 'CODE']].copy()

    twz = pd.read_excel(
        path_to_excel_file,
        sheet_name='TableC4',
        engine='openpyxl'
    )

    twz.drop(
        columns=['Unnamed: 0'] + list(twz.columns[-5:]),
        inplace=True
    )

    twz = twz.iloc[6:-3].copy()

    twz = twz[['Unnamed: 1', 'Unnamed: 2'] + list(twz.columns[-11:])].copy()

    column_names = list(twz.iloc[0, 1:]).copy()
    column_names[0] = 'All havens - Excessive high risk payments'

    twz.columns = ['Country'] + column_names

    twz = twz.iloc[2:].copy()

    twz.reset_index(drop=True, inplace=True)

    twz = twz[twz.isnull().sum(axis=1) != twz.isnull().sum(axis=1).max()].copy()

    twz.drop(
        columns=['All havens - Excessive high risk payments', 'All havens', 'EU havens', 'Non-EU tax havens'],
        inplace=True
    )

    for column in twz.columns[1:]:
        twz[column] = twz[column].fillna(0)

    twz = twz.dropna().reset_index(drop=True)

    twz = twz[
        ~twz['Country'].isin(
            [
                'OECD countries',
                'Main developing countries',
                'Non-OECD tax havens',
                'Rest of World',
                'Non-haven total',
                'Additional developing countries'
            ]
        )
    ].copy()

    twz['Country'] = twz['Country'].map(
        lambda country_name: country_name_corresp.get(country_name, country_name)
    )

    twz_reformatted = twz[['Country', 'Belgium']].copy()
    twz_reformatted['PARTNER_COUNTRY_NAME'] = 'Belgium'
    twz_reformatted = twz_reformatted.rename(columns={'Belgium': 'PROFITS'})

    for column in twz.columns[2:]:
        restricted_df = twz[['Country', column]].copy()
        restricted_df['PARTNER_COUNTRY_NAME'] = column
        restricted_df = restricted_df.rename(columns={column: 'PROFITS'})

        twz_reformatted = pd.concat([twz_reformatted, restricted_df], axis=0)

    twz_reformatted = twz_reformatted.merge(
        geographies,
        how='left',
        left_on='Country', right_on='NAME'
    ).drop(
        columns='NAME'
    ).rename(
        columns={
            'Country': 'PARENT_COUNTRY_NAME',
            'CODE': 'PARENT_COUNTRY_CODE'
        }
    )

    twz_reformatted = twz_reformatted.merge(
        geographies,
        how='left',
        left_on='PARTNER_COUNTRY_NAME', right_on='NAME'
    ).drop(
        columns='NAME'
    ).rename(
        columns={
            'CODE': 'PARTNER_COUNTRY_CODE'
        }
    )

    twz_reformatted['PARTNER_COUNTRY_CODE'] = twz_reformatted['PARTNER_COUNTRY_CODE'].fillna('REST')

    return twz_reformatted.copy()


def load_and_clean_twz_CIT(path_to_excel_file, path_to_geographies):
    """
    This function is used to load and clean the data compiled by Tørsløv et al. on countries' current corporate income
    tax revenues. It requires as arguments the paths to the TWZ Excel file and to the CSV file with country codes.
    """
    geographies = pd.read_csv(path_to_geographies)
    geographies = geographies[['NAME', 'CODE']].copy()

    twz = pd.read_excel(
        path_to_excel_file,
        sheet_name='Table U1',
        engine='openpyxl'
    )

    twz = twz.iloc[6:-13][['Unnamed: 1', 'Unnamed: 3']].copy()

    twz.columns = ['Country', 'CIT revenue']

    twz['Country'] = twz['Country'].map(
        lambda country_name: country_name_corresp.get(country_name, country_name)
    )

    twz = twz.merge(
        geographies,
        how='left',
        left_on='Country', right_on='NAME'
    ).drop(columns=['NAME'])

    twz = twz.dropna().reset_index(drop=True)

    if twz.isnull().sum().sum() > 0:
        raise Exception('Missing values remain in the TWZ data on CIT revenues.')

    return twz


def rename_partner_jurisdictions(row, use_case='normal'):
    """
    In the OECD data, each reporting country displays a line "Foreign Jurisdictions Total", which displays the sum of
    revenues, profits, corporate income taxes paid, etc. for the parent country across all foreign partner jurisdic-
    tions. In most cases, we want to eliminate this total to avoid any double-counting. But some countries (see list of
    alpha-3 codes above) only display a domestic vs. foreign breakdown and in these cases, it is important that we do
    not erase the "Foreign Jurisdictions Total" line. Therefore, we slightly rename it for these countries.
    """

    if use_case == 'normal':
        # Works for the main use case, to preprocess the OECD data

        if row['Parent jurisdiction (alpha-3 code)'] in COUNTRIES_WITH_MINIMUM_REPORTING:

            if row['Partner jurisdiction (whitespaces cleaned)'] == 'Foreign Jurisdictions Total':
                return 'Foreign Total'

            else:
                return row['Partner jurisdiction (whitespaces cleaned)']

        else:
            return row['Partner jurisdiction (whitespaces cleaned)']

    else:
        # Works for a secondary use case, when computing the average ETRs

        if row['COU'] in COUNTRIES_WITH_MINIMUM_REPORTING:

            if row['JUR'] == 'FJT':
                return 'FJTa'

            else:
                return row['JUR']

        else:
            return row['JUR']


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


def impute_missing_carve_out_values(
    row,
    avg_carve_out_impact_non_haven, avg_carve_out_impact_tax_haven,
    avg_carve_out_impact_domestic, avg_carve_out_impact_aggregate
):
    """
    This function allows to impute missing carve-out values based on two inputs: pre-tax profits and the average redu-
    ction in pre-tax profits due to carve-outs observed in OECD data. The factor used is determined by the partner ju-
    risdiction group in which profits are booked: tax havens, non-havens, domestic, aggregate partner jurisdictions.
    """

    if not np.isnan(row['CARVE_OUT']):
        return row['CARVE_OUT']

    elif row['Is domestic?'] == 1:
        return row['Profit (Loss) before Income Tax'] * avg_carve_out_impact_domestic

    elif row['Is partner jurisdiction a non-haven?'] == 1:
        return row['Profit (Loss) before Income Tax'] * avg_carve_out_impact_non_haven

    elif row['Is partner jurisdiction a tax haven?'] == 1:
        return row['Profit (Loss) before Income Tax'] * avg_carve_out_impact_tax_haven

    else:
        return row['Profit (Loss) before Income Tax'] * avg_carve_out_impact_aggregate


def get_avg_of_available_years(row, reference_year, variable):
    restricted_row = row[
        row.index[
            list(
                map(
                    lambda col: col.startswith(variable),
                    row.index
                )
            )
        ]
    ]

    available_values = restricted_row[~restricted_row.isnull()]

    if available_values.empty:
        return np.nan

    else:

        available_vars = restricted_row[~restricted_row.isnull()].index

        available_years = pd.Series(
            [
                int(available_var[-4:]) for available_var in available_vars
            ]
        )

        if reference_year in available_years:
            return row[variable + f'{str(reference_year)}']

        else:
            return available_values.mean()


def find_closest_year_available(row, reference_year, variable):
    restricted_row = row[
        row.index[
            list(
                map(
                    lambda col: col.startswith(variable),
                    row.index
                )
            )
        ]
    ]

    available_values = restricted_row[~restricted_row.isnull()].copy()

    if available_values.empty:
        return np.nan

    else:
        available_vars = available_values.index

        available_years = pd.Series(
            [
                int(available_var[-4:]) for available_var in available_vars
            ]
        )

        distance_to_reference_year = np.abs(available_years - reference_year)
        closest_available_year = available_years[
            distance_to_reference_year.idxmin()
        ]

        return closest_available_year


def apply_upgrade_factor(row, reference_year, variable, upgrade_factors):
    available_year_column = 'AVAILABLE_YEAR_' + variable
    available_year = row[available_year_column]

    if np.isnan(available_year):
        return np.nan

    else:
        available_year = int(available_year)

    if available_year > reference_year:
        column_name = f'uprusd{available_year - 2000}{reference_year - 2000}'
        try:
            factor = upgrade_factors.loc[
                'European Union', column_name
            ]
        except:
            print(column_name)
            factor = 1

        available_value = row[variable + str(available_year)]

        return available_value / factor

    elif available_year < reference_year:
        column_name = f'uprusd{reference_year - 2000}{available_year - 2000}'
        try:
            factor = upgrade_factors.loc[
                'European Union', column_name
            ]
        except:
            print(column_name)
            factor = 1

        available_value = row[variable + str(available_year)]

        return available_value * factor

    else:
        available_value = row[variable + str(available_year)]
        return available_value


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

def get_table_download_button(
    df,
    scenario,
    effective_tax_rate,
    company=None, taxing_country=None, carve_out_rate_assets=None, carve_out_rate_payroll=None
):
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

    elif scenario == 4:
        # Substance-based carve-outs page
        href += f' download="min_ETR_{effective_tax_rate}_perc_CO_'
        href += f'{str(carve_out_rate_assets)}_&_{str(carve_out_rate_payroll)}_perc.csv">'

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


def get_carve_outs_note_download_button():
    """
    Following the same principle, this function builds the HTML code that instantiates the download button allowing the
    user to obtain the note on substance-based carve-outs in PDF format.
    """

    # We fetch and read the .pdf file from the files folder
    path = os.path.join(path_to_files, 'carve_outs_note.pdf')

    with open(path, 'rb') as file:
        note_content = file.read()

    # We encode it to the right format
    b64 = base64.b64encode(note_content).decode()

    # And we build the HTML code
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(path)}">'

    href += '<input type="button" value="Click here to download the note on substance-based carve-outs (PDF)" '

    href += 'class="download-button pdf"></a>'

    return href


def get_2017_update_download_button():
    """
    Following the same principle, this function builds the HTML code that instantiates the download button allowing the
    user to obtain the October 2021 note in PDF format.
    """

    # We fetch and read the .pdf file from the files folder
    path = os.path.join(path_to_files, 'Note-2-November-2021.pdf')

    with open(path, 'rb') as file:
        note_content = file.read()

    # We encode it to the right format
    b64 = base64.b64encode(note_content).decode()

    # And we build the HTML code
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(path)}">'

    href += '<input type="button" value="Click here to download our latest country-by-country estimates '

    href += '(Oct. 2021, PDF)" class="download-button pdf"></a>'

    return href
