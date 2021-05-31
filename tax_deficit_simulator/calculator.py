import numpy as np
import pandas as pd

import os

from utils import rename_partner_jurisdictions, manage_overlap_with_domestic, combine_haven_tax_deficits, \
    COUNTRIES_WITH_MINIMUM_REPORTING, COUNTRIES_WITH_CONTINENTAL_REPORTING

path_to_dir = os.path.dirname(os.path.abspath(__file__))

path_to_eu_countries = os.path.join(path_to_dir, 'data', 'listofeucountries_csv.csv')
eu_country_codes = list(pd.read_csv(path_to_eu_countries, delimiter=';')['Alpha-3 code'])

eu_27_country_codes = eu_country_codes.copy()
eu_27_country_codes.remove('GBR')

path_to_tax_haven_list = os.path.join(path_to_dir, 'data', 'tax_haven_list.csv')
tax_haven_country_codes = list(pd.read_csv(path_to_tax_haven_list, delimiter=';')['Alpha-3 code'])

path_to_oecd = os.path.join(path_to_dir, 'data', 'oecd.csv')
path_to_twz = os.path.join(path_to_dir, 'data', 'twz.csv')
path_to_twz_domestic = os.path.join(path_to_dir, 'data', 'twz_domestic.csv')
path_to_twz_CIT = os.path.join(path_to_dir, 'data', 'twz_CIT.csv')


class TaxDeficitCalculator:

    def __init__(self, alternative_imputation=True):

        # These attributes will store the data loaded with the "load_clean_data" method
        self.oecd = None
        self.twz = None
        self.twz_domestic = None
        self.twz_CIT = None

        # For non-OECD reporting countries, data are taken from TWZ 2019 appendix tables
        # An effective tax rate of 20% is assumed to be applied on profits registered in non-havens
        self.assumed_non_haven_ETR_TWZ = 0.2

        # An effective tax rate of 10% is assumed to be applied on profits registered in tax havens
        self.assumed_haven_ETR_TWZ = 0.1

        # Average exchange rate over the year 2016, extracted from benchmark computations run on Stata
        # Source: European Central Bank
        self.USD_to_EUR_2016 = 1 / 1.1069031

        # self.multiplier_EU = 1.13381004333496
        # self.multiplier_world = 1.1330304145813

        # Gross growth rate of worldwide GDP in current EUR between 2016 and 2021
        # Extracted from benchmark computations run on Stata
        self.multiplier_2021 = 1.1330304145813

        # For rates of 0.2 or lower an alternative imputation is used to estimate the non-haven tax deficit of non-OECD
        # reporting countries; this argument allows to enable or disable this imputation
        self.alternative_imputation = alternative_imputation
        self.reference_rate_for_alternative_imputation = 0.25

        # The list of countries whose tax deficit is partly collected by EU countries in the intermediary scenario
        self.country_list_intermediary_scenario = [
            'USA',
            'AUS',
            'CAN',
            'CHL',
            'MEX',
            'NOR',
            'BMU',
            'BRA',
            'CHN',
            'IND',
            'SGP',
            'ZAF',
            'IDN',
            'JPN'
        ]

    def load_clean_data(
        self,
        path_to_oecd=path_to_oecd,
        path_to_twz=path_to_twz,
        path_to_twz_domestic=path_to_twz_domestic,
        path_to_twz_CIT=path_to_twz_CIT,
        inplace=True
    ):
        """
        This method allows to load and clean data from 4 different sources:

        - the "oecd.csv" file which was extracted from the OECD's aggregated and anonymized country-by-country repor-
        ting, considering only the positive profit sample. Figures are in 2016 USD;

        - the "twz.csv" file which was extracted from the Table C4 of the TWZ 2019 online appendix. It presents, for
        a number of countries, the amounts of profits shifted to tax havens that are re-allocated to them on an ultima-
        te ownership basis. Figures are in 2016 USD million;

        - the "twz_domestic.csv" file, taken from the outputs of benchmark computations run on Stata. It presents for
        each country the amount of corporate profits registered locally by domestic MNEs and the effective tax rate to
        which they are subject. Figures are in 2016 USD billion;

        - the "twz_CIT.file", extracted from Table U1 of the TWZ 2019 online appendix. It presents the corporate income
        tax revenue of each country in 2016 USD billion.

        Default paths are used to let the simulator run via the app.py file. If you wish to use the tax_deficit_calcula-
        tor package in another context, you can save the data locally and give the method paths to the data files. The
        possibility to load the files from an online host instead will soon be implemented.
        """
        try:

            # We try to read the files from the provided paths
            oecd = pd.read_csv(path_to_oecd, delimiter=';')
            twz = pd.read_csv(path_to_twz, delimiter=';')
            twz_domestic = pd.read_csv(path_to_twz_domestic, delimiter=';')
            twz_CIT = pd.read_csv(path_to_twz_CIT, delimiter=';')

        except FileNotFoundError:

            # If at least one of the files is not found
            raise Exception('Are you sure these are the right paths for the source files?')

        # --- Cleaning the OECD data

        numeric_columns = list(oecd.columns[5:])

        # We transform numeric columns so that they can be manipulated as such in Python
        for column_name in numeric_columns:
            # We replace the decimal separator
            oecd[column_name] = oecd[column_name].map(lambda x: x.replace(',', '.'))

            # We impute 0 for all missing values
            oecd[column_name] = oecd[column_name].map(lambda x: 0 if x == '..' else x)

            # We typecast the figures from strings into floats
            oecd[column_name] = oecd[column_name].astype(float)

        # Thanks to a function defined in utils.py, we rename the "Foreign Jurisdictions Total" field for all countries
        # that only report a domestic / foreign breakdown in their CbCR
        oecd['Partner jurisdiction (whitespaces cleaned)'] = oecd.apply(rename_partner_jurisdictions, axis=1)

        # We eliminate stateless entities and the "Foreign Jurisdictions Total" filds
        oecd = oecd[
            ~oecd['Partner jurisdiction (whitespaces cleaned)'].isin(['Foreign Jurisdictions Total', 'Stateless'])
        ].copy()

        # ETR computation (using tax paid as the numerator)
        oecd['ETR'] = oecd['Income Tax Paid (on Cash Basis)'] / oecd['Profit (Loss) before Income Tax']
        oecd['ETR'] = oecd['ETR'].map(lambda x: 0 if x < 0 else x)

        # Adding an indicator variable
        oecd['Is domestic?'] = oecd.apply(
            lambda row: row['Parent jurisdiction (alpha-3 code)'] == row['Partner jurisdiction (alpha-3 code)'],
            axis=1
        ) * 1

        # Adding an other indicator variable
        oecd['Is partner jurisdiction a non-haven?'] = 1 - oecd['Is partner jurisdiction a tax haven?']

        # Thanks to a small function imported from utils.py, we manage the slightly problematic overlap between the
        # various indicator variables ("Is domestic?" sort of gets the priority over the others)
        oecd['Is partner jurisdiction a tax haven?'] = oecd.apply(
            lambda row: manage_overlap_with_domestic(row, 'haven'),
            axis=1
        )

        oecd['Is partner jurisdiction a non-haven?'] = oecd.apply(
            lambda row: manage_overlap_with_domestic(row, 'non-haven'),
            axis=1
        )

        # --- Cleaning the TWZ tax haven profits data

        # Adding an indicator variable for OECD reporting - We do not consider the Swedish CbCR
        twz['Is parent in OECD data?'] = twz['Alpha-3 country code'].map(
            lambda x: x in oecd['Parent jurisdiction (alpha-3 code)'].unique() if x != 'SWE' else False
        ) * 1

        # We reformat numeric columns - Resulting figures are expressed in 2016 USD
        for column_name in ['Profits in all tax havens', 'Profits in all tax havens (positive only)']:
            twz[column_name] = twz[column_name].map(lambda x: x.replace(',', '.'))
            twz[column_name] = twz[column_name].astype(float) * 1000000

        # We filter out countries with 0 profits in tax havens
        twz = twz[twz['Profits in all tax havens (positive only)'] > 0].copy()

        # --- Cleaning the TWZ domestic profits data

        # Reformatting the profits column - Resulting figures are expressed in 2016 USD
        twz_domestic['Domestic profits'] = twz_domestic['Domestic profits']\
            .map(lambda x: x.replace(',', '.'))\
            .astype(float) * 1000000000

        # Reformatting the ETR column
        twz_domestic['Domestic ETR'] = twz_domestic['Domestic ETR'].map(lambda x: x.replace(',', '.')).astype(float)

        # --- Cleaning the TWZ CIT revenue data

        # Reformatting the CIT revenue column - Resulting figures are expressed in 2016 USD
        twz_CIT['CIT revenue'] = twz_CIT['CIT revenue']\
            .map(lambda x: x.replace(',', '.'))\
            .astype(float) * 1000000000

        if inplace:
            self.oecd = oecd.copy()
            self.twz = twz.copy()
            self.twz_domestic = twz_domestic.copy()
            self.twz_CIT = twz_CIT.copy()

        else:
            return oecd.copy(), twz.copy(), twz_domestic.copy(), twz_CIT.copy()

    def get_non_haven_imputation_ratio(self, minimum_ETR=0.25):
        if self.oecd is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        if minimum_ETR > 0.1:
            oecd = self.oecd.copy()

            mask_eu = oecd['Parent jurisdiction (alpha-3 code)'].isin(eu_country_codes)
            mask_non_haven = ~oecd['Parent jurisdiction (alpha-3 code)'].isin(tax_haven_country_codes)
            mask_minimum_reporting_countries = ~oecd['Parent jurisdiction (alpha-3 code)'].isin(
                COUNTRIES_WITH_MINIMUM_REPORTING + COUNTRIES_WITH_CONTINENTAL_REPORTING
            )

            mask = np.logical_and(mask_eu, mask_non_haven)
            mask = np.logical_and(mask, mask_minimum_reporting_countries)

            self.mask = mask.copy()

            mask = mask * 1

            foreign_non_haven_profits = (
                (
                    mask * oecd['Is partner jurisdiction a non-haven?']
                ) * oecd['Profit (Loss) before Income Tax']
            ).sum()
            foreign_haven_profits = (
                (
                    mask * oecd['Is partner jurisdiction a tax haven?']
                ) * oecd['Profit (Loss) before Income Tax']
            ).sum()

            imputation_ratio_non_haven = (
                (
                    max(minimum_ETR - self.assumed_non_haven_ETR_TWZ, 0) * foreign_non_haven_profits
                ) /
                ((minimum_ETR - self.assumed_haven_ETR_TWZ) * foreign_haven_profits)
            )

        elif minimum_ETR == 0.1:
            imputation_ratio_non_haven = 1

        else:
            raise Exception('Unexpected minimum ETR entered (strictly below 0.1).')

        return imputation_ratio_non_haven

    def get_alternative_non_haven_factor(self, minimum_ETR):
        if self.oecd is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        if minimum_ETR > 0.2:
            raise Exception('These computations are only used when the minimum ETR considered is 0.2 or less.')

        oecd_stratified = self.get_stratified_oecd_data(
            minimum_ETR=self.reference_rate_for_alternative_imputation
        )

        df_restricted = oecd_stratified[
            ~oecd_stratified['Parent jurisdiction (alpha-3 code)'].isin(
                COUNTRIES_WITH_CONTINENTAL_REPORTING + COUNTRIES_WITH_MINIMUM_REPORTING
            )
        ].copy()

        denominator = df_restricted['tax_deficit_x_non_haven'].sum()

        oecd_stratified = self.get_stratified_oecd_data(minimum_ETR=minimum_ETR)

        df_restricted = oecd_stratified[
            ~oecd_stratified['Parent jurisdiction (alpha-3 code)'].isin(
                COUNTRIES_WITH_CONTINENTAL_REPORTING + COUNTRIES_WITH_MINIMUM_REPORTING
            )
        ].copy()

        numerator = df_restricted['tax_deficit_x_non_haven'].sum()

        return numerator / denominator

    def get_stratified_oecd_data(self, minimum_ETR=0.25):
        if self.oecd is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        oecd = self.oecd.copy()

        oecd = oecd[oecd['ETR'] < minimum_ETR].copy()

        oecd['ETR_differential'] = oecd['ETR'].map(lambda x: minimum_ETR - x)

        oecd['tax_deficit'] = oecd['ETR_differential'] * oecd['Profit (Loss) before Income Tax']

        oecd['tax_deficit_x_domestic'] = oecd['tax_deficit'] * oecd['Is domestic?']
        oecd['tax_deficit_x_tax_haven'] = oecd['tax_deficit'] * oecd['Is partner jurisdiction a tax haven?']
        oecd['tax_deficit_x_non_haven'] = oecd['tax_deficit'] * oecd['Is partner jurisdiction a non-haven?']

        oecd_stratified = oecd[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit',
                'tax_deficit_x_domestic',
                'tax_deficit_x_tax_haven',
                'tax_deficit_x_non_haven'
            ]
        ].groupby(
            'Parent jurisdiction (whitespaces cleaned)'
        ).agg(
            {
                'Parent jurisdiction (alpha-3 code)': 'first',
                'tax_deficit': 'sum',
                'tax_deficit_x_domestic': 'sum',
                'tax_deficit_x_tax_haven': 'sum',
                'tax_deficit_x_non_haven': 'sum'
            }
        ).copy()

        oecd_stratified.reset_index(inplace=True)

        return oecd_stratified.copy()

    def compute_all_tax_deficits(self, minimum_ETR=0.25, inplace=True):
        if self.oecd is None or self.twz is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        oecd_stratified = self.get_stratified_oecd_data(minimum_ETR=minimum_ETR)

        twz = self.twz.copy()

        twz['tax_deficit_x_tax_haven_TWZ'] = twz['Profits in all tax havens (positive only)'] \
            * (minimum_ETR - self.assumed_haven_ETR_TWZ)

        # --- Managing countries in both OECD and TWZ data

        twz_in_oecd = twz[twz['Is parent in OECD data?'].astype(bool)].copy()

        merged_df = oecd_stratified.merge(
            twz_in_oecd[['Country', 'Alpha-3 country code', 'tax_deficit_x_tax_haven_TWZ']],
            how='left',
            left_on='Parent jurisdiction (alpha-3 code)',
            right_on='Alpha-3 country code'
        ).drop(columns=['Country', 'Alpha-3 country code'])

        merged_df['tax_deficit_x_tax_haven_TWZ'] = merged_df['tax_deficit_x_tax_haven_TWZ'].fillna(0)

        merged_df['tax_deficit_x_tax_haven_merged'] = merged_df.apply(
            combine_haven_tax_deficits,
            axis=1
        )

        merged_df.drop(columns=['tax_deficit_x_tax_haven', 'tax_deficit_x_tax_haven_TWZ'], inplace=True)

        merged_df.rename(
            columns={
                'tax_deficit_x_tax_haven_merged': 'tax_deficit_x_tax_haven'
            },
            inplace=True
        )

        merged_df['tax_deficit'] = merged_df['tax_deficit_x_tax_haven'] \
            + merged_df['tax_deficit_x_domestic'] \
            + merged_df['tax_deficit_x_non_haven']

        # --- Countries only in the TWZ data

        twz_not_in_oecd = twz[~twz['Is parent in OECD data?'].astype(bool)].copy()

        twz_not_in_oecd.drop(
            columns=['Profits in all tax havens', 'Profits in all tax havens (positive only)'],
            inplace=True
        )

        # Extrapolating the foreign non-haven tax deficit

        imputation_ratio_non_haven = self.get_non_haven_imputation_ratio(minimum_ETR=minimum_ETR)

        self.imputation_ratio_non_haven = imputation_ratio_non_haven

        twz_not_in_oecd['tax_deficit_x_non_haven'] = \
            twz_not_in_oecd['tax_deficit_x_tax_haven_TWZ'] * imputation_ratio_non_haven

        # Computing the domestic tax deficit

        twz_domestic = self.twz_domestic.copy()

        twz_domestic = twz_domestic[twz_domestic['Domestic ETR'] < minimum_ETR].copy()

        twz_domestic['ETR_differential'] = twz_domestic['Domestic ETR'].map(lambda x: minimum_ETR - x)

        twz_domestic['tax_deficit_x_domestic'] = twz_domestic['ETR_differential'] * twz_domestic['Domestic profits']

        twz_not_in_oecd = twz_not_in_oecd.merge(
            twz_domestic[['Alpha-3 country code', 'tax_deficit_x_domestic']],
            how='left',
            on='Alpha-3 country code'
        )

        twz_not_in_oecd['tax_deficit_x_domestic'] = twz_not_in_oecd['tax_deficit_x_domestic'].fillna(0)

        twz_not_in_oecd['tax_deficit'] = twz_not_in_oecd['tax_deficit_x_tax_haven_TWZ'] \
            + twz_not_in_oecd['tax_deficit_x_domestic'] \
            + twz_not_in_oecd['tax_deficit_x_non_haven']

        twz_not_in_oecd.rename(
            columns={
                'Country': 'Parent jurisdiction (whitespaces cleaned)',
                'Alpha-3 country code': 'Parent jurisdiction (alpha-3 code)',
                'tax_deficit_x_tax_haven_TWZ': 'tax_deficit_x_tax_haven'
            },
            inplace=True
        )

        twz_not_in_oecd.drop(columns=['Is parent in OECD data?'], inplace=True)

        merged_df = merged_df[merged_df['Parent jurisdiction (alpha-3 code)'] != 'SWE'].copy()

        merged_df = pd.concat(
            [merged_df, twz_not_in_oecd],
            axis=0
        )

        # --- Extrapolations to 2021 EUR

        merged_df['is_eu'] = merged_df['Parent jurisdiction (alpha-3 code)'].isin(eu_country_codes) * 1

        # multiplier = (merged_df['is_eu'] * self.multiplier_EU).map(lambda x: self.multiplier_world if x == 0 else x)
        multiplier = self.multiplier_2021

        merged_df.drop(columns=['is_eu'], inplace=True)

        for column_name in merged_df.columns[2:]:
            merged_df[column_name] = merged_df[column_name] * self.USD_to_EUR_2016 * multiplier

        # --- Managing the case where the minimum ETR is 20% or below for TWZ countries

        if minimum_ETR <= 0.2 and self.alternative_imputation:
            multiplying_factor = self.get_alternative_non_haven_factor(minimum_ETR=minimum_ETR)

            df = self.compute_all_tax_deficits(
                minimum_ETR=self.reference_rate_for_alternative_imputation
            )

            oecd_reporting_countries_but_SWE = self.oecd[
                self.oecd['Parent jurisdiction (alpha-3 code)'] != 'SWE'
            ]['Parent jurisdiction (alpha-3 code)'].unique()

            df = df[
                ~df['Parent jurisdiction (alpha-3 code)'].isin(oecd_reporting_countries_but_SWE)
            ].copy()

            df['tax_deficit_x_non_haven_imputation'] = df['tax_deficit_x_non_haven'] * multiplying_factor

            mapping = {}

            for _, row in df.iterrows():
                mapping[row['Parent jurisdiction (alpha-3 code)']] = row['tax_deficit_x_non_haven_imputation']

            merged_df['tax_deficit_x_non_haven_imputation'] = merged_df['Parent jurisdiction (alpha-3 code)'].map(
                lambda country_code: mapping.get(country_code, 0)
            )

            merged_df['tax_deficit_x_non_haven'] += merged_df['tax_deficit_x_non_haven_imputation']

            merged_df['tax_deficit'] += merged_df['tax_deficit_x_non_haven_imputation']

            merged_df.drop(
                columns=['tax_deficit_x_non_haven_imputation'],
                inplace=True
            )

        return merged_df.reset_index(drop=True).copy()

    def check_tax_deficit_computations(self, minimum_ETR=0.25):

        df = self.compute_all_tax_deficits(minimum_ETR=minimum_ETR)

        for column_name in df.columns[2:]:
            df[column_name] = df[column_name] / 10**9

        return df.copy()

    def get_total_tax_deficits(self, minimum_ETR=0.25):

        df = self.compute_all_tax_deficits(minimum_ETR=minimum_ETR)

        df = df[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'tax_deficit']
        ]

        df.sort_values(
            by='Parent jurisdiction (whitespaces cleaned)',
            inplace=True
        )

        total_eu = (df['Parent jurisdiction (alpha-3 code)'].isin(eu_27_country_codes) * 1 * df['tax_deficit']).sum()
        total_whole_sample = df['tax_deficit'].sum()

        dict_df = df.to_dict()

        dict_df[df.columns[0]][len(df)] = 'Total - EU27'
        dict_df[df.columns[1]][len(df)] = '..'
        dict_df[df.columns[2]][len(df)] = total_eu

        dict_df[df.columns[0]][len(df) + 1] = 'Total - Whole sample'
        dict_df[df.columns[1]][len(df) + 1] = '..'
        dict_df[df.columns[2]][len(df) + 1] = total_whole_sample

        df = pd.DataFrame.from_dict(dict_df)

        return df.reset_index(drop=True)

    def check_appendix_A2(self):
        if self.twz_CIT is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        df = self.get_total_tax_deficits(minimum_ETR=0.15)

        df.rename(columns={'tax_deficit': 'tax_deficit_15'}, inplace=True)

        merged_df = df.merge(
            self.twz_CIT,
            how='left',
            left_on='Parent jurisdiction (alpha-3 code)',
            right_on='Country (alpha-3 code)'
        ).drop(columns=['Country', 'Country (alpha-3 code)'])

        merged_df['tax_deficit_15'] /= (merged_df['CIT revenue'] * self.multiplier_2021 * self.USD_to_EUR_2016 / 100)

        for rate in [0.21, 0.25, 0.3]:
            df = self.get_total_tax_deficits(minimum_ETR=rate)

            merged_df = merged_df.merge(
                df,
                how='left',
                on='Parent jurisdiction (alpha-3 code)'
            )

            merged_df['tax_deficit'] = merged_df['tax_deficit'].fillna(0)

            merged_df.rename(
                columns={'tax_deficit': f'tax_deficit_{int(rate * 100)}'},
                inplace=True
            )

            merged_df[f'tax_deficit_{int(rate * 100)}'] /= (
                merged_df['CIT revenue'] * self.multiplier_2021 * self.USD_to_EUR_2016 / 100
            )

        eu_df = merged_df[merged_df['Parent jurisdiction (alpha-3 code)'].isin(eu_27_country_codes)].copy()

        self.check = [
            (
                eu_df[f'tax_deficit_{rate}'] * eu_df['CIT revenue'] / 100
            ).sum() / eu_df['CIT revenue'].sum() for rate in [15, 21, 25, 30]
        ]

        merged_df = merged_df[
            [
                'Parent jurisdiction (whitespaces cleaned)_x',
                'tax_deficit_15', 'tax_deficit_21', 'tax_deficit_25', 'tax_deficit_30'
            ]
        ].copy()

        return merged_df.copy()

    def output_tax_deficits_formatted(self, minimum_ETR=0.25):

        df = self.get_total_tax_deficits(minimum_ETR=minimum_ETR)

        oecd_reporting_countries = self.oecd['Parent jurisdiction (alpha-3 code)'].unique()
        oecd_reporting_countries = [
            country_code for country_code in oecd_reporting_countries if country_code not in ['SGP', 'BMU']
        ]

        mask = np.logical_or(
            df['Parent jurisdiction (alpha-3 code)'].isin(eu_27_country_codes),
            df['Parent jurisdiction (alpha-3 code)'].isin(oecd_reporting_countries)
        )

        df = df[mask].copy()

        df.sort_values(
            by='Parent jurisdiction (whitespaces cleaned)',
            inplace=True
        )

        df.reset_index(drop=True, inplace=True)

        df['tax_deficit'] = df['tax_deficit'] / 10**6

        dict_df = df.to_dict()

        dict_df[df.columns[0]][len(df)] = 'Total - EU27'
        dict_df[df.columns[1]][len(df)] = '..'
        dict_df[df.columns[2]][len(df)] = df[
            df['Parent jurisdiction (alpha-3 code)'].isin(eu_27_country_codes)
        ]['tax_deficit'].sum()

        dict_df[df.columns[0]][len(df) + 1] = 'Total - Whole sample'
        dict_df[df.columns[1]][len(df) + 1] = '..'
        dict_df[df.columns[2]][len(df) + 1] = df['tax_deficit'].sum()

        df = pd.DataFrame.from_dict(dict_df)

        df.drop(columns=['Parent jurisdiction (alpha-3 code)'], inplace=True)

        df['tax_deficit'] = df['tax_deficit'].map('{:,.0f}'.format)

        df.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Headquarter country',
                'tax_deficit': 'Collectible tax deficit (€m)'
            },
            inplace=True
        )

        return df.copy()

    def compute_unilateral_scenario_gain(self, country, minimum_ETR=0.25):

        if self.oecd is None or self.twz is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        oecd = self.oecd.copy()

        tax_deficits = self.get_total_tax_deficits(minimum_ETR=minimum_ETR)

        taxing_country = country
        taxing_country_code = tax_deficits[
            tax_deficits['Parent jurisdiction (whitespaces cleaned)'] == taxing_country
        ]['Parent jurisdiction (alpha-3 code)'].iloc[0]

        attribution_ratios = []

        for country_code in tax_deficits['Parent jurisdiction (alpha-3 code)'].values:

            if country_code == taxing_country_code:
                attribution_ratios.append(1)

            else:
                oecd_restricted = oecd[oecd['Parent jurisdiction (alpha-3 code)'] == country_code].copy()

                if taxing_country_code not in oecd_restricted['Partner jurisdiction (alpha-3 code)'].values:
                    attribution_ratios.append(0)

                else:
                    mask = (oecd_restricted['Partner jurisdiction (alpha-3 code)'] == taxing_country_code)
                    sales_in_taxing_country = oecd_restricted[mask]['Unrelated Party Revenues'].iloc[0]

                    # mask = (df_restricted['Partner jurisdiction (whitespaces cleaned)'] != country)
                    # total_foreign_sales = df_restricted[mask]['Unrelated Party Revenues'].sum()

                    total_sales = oecd_restricted['Unrelated Party Revenues'].sum()

                    attribution_ratios.append(sales_in_taxing_country / total_sales)

        tax_deficits['Attribution ratios'] = attribution_ratios

        tax_deficits[f'Collectible tax deficit for {taxing_country}'] = \
            tax_deficits['tax_deficit'] * tax_deficits['Attribution ratios']

        tax_deficits.drop(
            columns=[
                'Attribution ratios',
                'tax_deficit',
                'Parent jurisdiction (alpha-3 code)'
            ],
            inplace=True
        )

        tax_deficits = tax_deficits[tax_deficits[f'Collectible tax deficit for {taxing_country}'] > 0].copy()

        tax_deficits.sort_values(
            by=f'Collectible tax deficit for {taxing_country}',
            ascending=False,
            inplace=True
        )

        imputation = tax_deficits[
            ~tax_deficits['Parent jurisdiction (whitespaces cleaned)'].isin([taxing_country, 'United States'])
        ][f'Collectible tax deficit for {taxing_country}'].sum()

        if taxing_country_code == 'DEU':
            imputation /= 2

        tax_deficits.reset_index(drop=True, inplace=True)

        dict_df = tax_deficits.to_dict()

        dict_df[tax_deficits.columns[0]][len(tax_deficits)] = 'Others (imputation)'
        dict_df[tax_deficits.columns[1]][len(tax_deficits)] = imputation

        dict_df[tax_deficits.columns[0]][len(tax_deficits) + 1] = 'Total'
        dict_df[tax_deficits.columns[1]][len(tax_deficits) + 1] = (
            tax_deficits[tax_deficits.columns[1]].sum() + imputation
        )

        df = pd.DataFrame.from_dict(dict_df)

        return df.copy()

    def check_unilateral_scenario_gain_computations(self, minimum_ETR=0.25):

        country_list = self.get_total_tax_deficits()

        country_list = country_list[
            ~country_list['Parent jurisdiction (whitespaces cleaned)'].isin(['Total - EU27', 'Total - Whole sample'])
        ].copy()

        country_list = list(country_list['Parent jurisdiction (whitespaces cleaned)'].values)

        output = {
            'Country': country_list,
            'Own tax deficit': [],
            'Collection of US tax deficit': [],
            'Collection of non-US tax deficit': [],
            'Imputation': [],
            'Total': []
        }

        for country in country_list:

            df = self.compute_unilateral_scenario_gain(
                country=country,
                minimum_ETR=minimum_ETR
            )

            column_name = f'Collectible tax deficit for {country}'

            output['Own tax deficit'].append(
                df[df['Parent jurisdiction (whitespaces cleaned)'] == country][column_name].iloc[0]
            )

            if 'United States' in df['Parent jurisdiction (whitespaces cleaned)'].values:
                output['Collection of US tax deficit'].append(
                    df[df['Parent jurisdiction (whitespaces cleaned)'] == 'United States'][column_name].iloc[0]
                )
            else:
                output['Collection of US tax deficit'].append(0)

            output['Imputation'].append(
                df[df['Parent jurisdiction (whitespaces cleaned)'] == 'Others (imputation)'][column_name].iloc[0]
            )

            output['Total'].append(
                df[df['Parent jurisdiction (whitespaces cleaned)'] == 'Total'][column_name].iloc[0]
            )

            output['Collection of non-US tax deficit'].append(
                df[
                    ~df['Parent jurisdiction (whitespaces cleaned)'].isin(
                        [
                            country, 'United States', 'Total', 'Imputation'
                        ]
                    )
                ][column_name].sum()
            )

        df = pd.DataFrame.from_dict(output)

        df['Imputation'] = df['Collection of US tax deficit'] + df['Collection of non-US tax deficit']

        for column_name in df.columns[1:]:
            df[column_name] /= 10**9

        return df.copy()

    def output_unilateral_scenario_gain_formatted(self, country, minimum_ETR=0.25):

        df = self.compute_unilateral_scenario_gain(
            country=country,
            minimum_ETR=minimum_ETR
        )

        df[f'Collectible tax deficit for {country}'] = df[f'Collectible tax deficit for {country}'] / 10**6

        df[f'Collectible tax deficit for {country}'] = \
            df[f'Collectible tax deficit for {country}'].map('{:,.2f}'.format)

        df.rename(
            columns={
                f'Collectible tax deficit for {country}': f'Collectible tax deficit for {country} (€m)',
                'Parent jurisdiction (whitespaces cleaned)': 'Headquarter country'
            },
            inplace=True
        )

        return df.copy()

    def compute_intermediary_scenario_gain(self, minimum_ETR=0.25):

        tax_deficits = self.get_total_tax_deficits(minimum_ETR=minimum_ETR)

        oecd = self.oecd.copy()

        eu_27_tax_deficit = tax_deficits[
            tax_deficits['Parent jurisdiction (whitespaces cleaned)'] == 'Total - EU27'
        ]['tax_deficit'].iloc[0]

        attribution_ratios = {}

        europe_or_other_europe_ratios = {}

        for country in self.country_list_intermediary_scenario:

            oecd_restricted = oecd[oecd['Parent jurisdiction (alpha-3 code)'] == country]

            total_sales = oecd_restricted['Unrelated Party Revenues'].sum()

            mask_eu_27 = oecd_restricted['Partner jurisdiction (alpha-3 code)'].isin(eu_27_country_codes)

            if country != 'USA':
                mask_other_europe = (oecd_restricted['Partner jurisdiction (whitespaces cleaned)'] == 'Other Europe')
                mask_europe = (oecd_restricted['Partner jurisdiction (whitespaces cleaned)'] == 'Europe')

                mask_europe_or_other_europe = np.logical_or(mask_other_europe, mask_europe)

            else:
                mask_europe_or_other_europe = np.array([False] * len(oecd_restricted))

            mask = np.logical_or(mask_eu_27, mask_europe_or_other_europe)

            europe_or_other_europe_sales = oecd_restricted[
                mask_europe_or_other_europe
            ]['Unrelated Party Revenues'].sum()

            europe_or_other_europe_ratios[country] = europe_or_other_europe_sales / total_sales

            # if country in ['AUS', 'CAN', 'CHL', 'BRA', 'CHN', 'SGP', 'IDN', 'JPN']:
            #     mask_other_europe = (oecd_restricted['Partner jurisdiction (whitespaces cleaned)'] == 'Other Europe')

            #     mask = np.logical_or(mask_eu_27, mask_other_europe)

            #     other_europe_sales = oecd_restricted[mask_other_europe]['Unrelated Party Revenues'].sum()
            #     europe_or_other_europe_ratios[country] = other_europe_sales / total_sales

            # elif country == 'NOR':
            #     mask_europe = (oecd_restricted['Partner jurisdiction (whitespaces cleaned)'] == 'Europe')

            #     mask = np.logical_or(mask_eu_27, mask_europe)

            #     europe_sales = oecd_restricted[mask_europe]['Unrelated Party Revenues'].sum()
            #     europe_or_other_europe_ratios[country] = europe_sales / total_sales

            # else:
            #     mask = mask_eu_27.copy()

            #     europe_or_other_europe_ratios[country] = 0

            oecd_restricted = oecd_restricted[mask].copy()

            eu_sales = oecd_restricted['Unrelated Party Revenues'].sum()

            attribution_ratios[country] = eu_sales / total_sales

        tax_deficits = tax_deficits[
            tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(
                self.country_list_intermediary_scenario
            )
        ].copy()

        tax_deficits['EU attribution ratios'] = tax_deficits['Parent jurisdiction (alpha-3 code)'].map(
            attribution_ratios
        )

        tax_deficits['Europe or Other Europe ratios'] = tax_deficits['Parent jurisdiction (alpha-3 code)'].map(
            europe_or_other_europe_ratios
        )

        tax_deficits['Collectible tax deficit for the EU'] = \
            tax_deficits['tax_deficit'] * tax_deficits['EU attribution ratios']

        to_be_removed_from_imputation = (
            tax_deficits['tax_deficit'] * tax_deficits['Europe or Other Europe ratios']
        ).sum()

        self.to_be_removed_from_imputation = to_be_removed_from_imputation

        tax_deficits.drop(
            columns=[
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit',
                'EU attribution ratios',
                'Europe or Other Europe ratios'
            ],
            inplace=True
        )

        imputation = tax_deficits['Collectible tax deficit for the EU'].sum()

        tax_deficits.reset_index(drop=True, inplace=True)

        dict_df = tax_deficits.to_dict()

        dict_df[tax_deficits.columns[0]][len(tax_deficits)] = 'Others (imputation)'
        dict_df[tax_deficits.columns[1]][len(tax_deficits)] = imputation - to_be_removed_from_imputation

        dict_df[tax_deficits.columns[0]][len(tax_deficits) + 1] = 'EU27'
        dict_df[tax_deficits.columns[1]][len(tax_deficits) + 1] = eu_27_tax_deficit

        dict_df[tax_deficits.columns[0]][len(tax_deficits) + 2] = 'Total'
        dict_df[tax_deficits.columns[1]][len(tax_deficits) + 2] = (
            2 * imputation + eu_27_tax_deficit - to_be_removed_from_imputation
        )

        df = pd.DataFrame.from_dict(dict_df)

        return df.copy()

    def compute_intermediary_scenario_gain_alternative(self, minimum_ETR=0.25):

        tax_deficits = self.get_total_tax_deficits(minimum_ETR=minimum_ETR)

        oecd = self.oecd.copy()

        eu_27_tax_deficit = tax_deficits[
            tax_deficits['Parent jurisdiction (whitespaces cleaned)'] == 'Total - EU27'
        ]['tax_deficit'].iloc[0]

        eu_27_tax_deficits = tax_deficits[
            tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(
                eu_27_country_codes
            )
        ].copy()

        tax_deficits = tax_deficits[
            tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(
                self.country_list_intermediary_scenario
            )
        ].copy()

        additional_revenue_gains = {}

        for eu_country in eu_27_country_codes:

            td_df = tax_deficits.copy()

            attribution_ratios = {}

            for country in self.country_list_intermediary_scenario:

                oecd_restricted = oecd[oecd['Parent jurisdiction (alpha-3 code)'] == country].copy()

                sales_in_eu_country = oecd_restricted[
                    oecd_restricted['Partner jurisdiction (alpha-3 code)'] == eu_country
                ]['Unrelated Party Revenues'].sum()

                total_sales = oecd_restricted['Unrelated Party Revenues'].sum()

                attribution_ratios[country] = sales_in_eu_country / total_sales

            td_df['Attribution ratios'] = td_df['Parent jurisdiction (alpha-3 code)'].map(attribution_ratios)

            td_df['Collectible tax deficit'] = td_df['Attribution ratios'] * td_df['tax_deficit']

            additional_revenue_gains[eu_country] = td_df['Collectible tax deficit'].sum() * 2

        eu_27_tax_deficits['From foreign MNEs'] = eu_27_tax_deficits['Parent jurisdiction (alpha-3 code)'].map(
            additional_revenue_gains
        )

        eu_27_tax_deficits['Total'] = (
            eu_27_tax_deficits['tax_deficit'] + eu_27_tax_deficits['From foreign MNEs']
        )

        additional_revenue_gains = {}

        for aggregate in ['Europe', 'Other Europe']:

            td_df = tax_deficits.copy()

            attribution_ratios = {}

            for country in self.country_list_intermediary_scenario:

                if country == 'USA':
                    attribution_ratios[country] = 0

                    continue

                oecd_restricted = oecd[oecd['Parent jurisdiction (alpha-3 code)'] == country].copy()

                sales_in_europe_or_other_europe = oecd_restricted[
                    oecd_restricted['Partner jurisdiction (whitespaces cleaned)'] == aggregate
                ]['Unrelated Party Revenues'].sum()

                total_sales = oecd_restricted['Unrelated Party Revenues'].sum()

                attribution_ratios[country] = sales_in_europe_or_other_europe / total_sales

            td_df['Attribution ratios'] = td_df['Parent jurisdiction (alpha-3 code)'].map(attribution_ratios)

            td_df['Collectible tax deficit'] = td_df['Attribution ratios'] * td_df['tax_deficit']

            additional_revenue_gains[aggregate] = td_df['Collectible tax deficit'].sum()

        eu_27_tax_deficits.drop(
            columns=['Parent jurisdiction (alpha-3 code)'],
            inplace=True
        )

        eu_27_tax_deficits.reset_index(drop=True, inplace=True)

        dict_df = eu_27_tax_deficits.to_dict()

        dict_df[eu_27_tax_deficits.columns[0]][len(eu_27_tax_deficits)] = 'Other Europe'
        dict_df[eu_27_tax_deficits.columns[1]][len(eu_27_tax_deficits)] = 0
        dict_df[eu_27_tax_deficits.columns[2]][len(eu_27_tax_deficits)] = additional_revenue_gains['Other Europe']
        dict_df[eu_27_tax_deficits.columns[3]][len(eu_27_tax_deficits)] = additional_revenue_gains['Other Europe']

        dict_df[eu_27_tax_deficits.columns[0]][len(eu_27_tax_deficits) + 1] = 'Europe'
        dict_df[eu_27_tax_deficits.columns[1]][len(eu_27_tax_deficits) + 1] = 0
        dict_df[eu_27_tax_deficits.columns[2]][len(eu_27_tax_deficits) + 1] = additional_revenue_gains['Europe']
        dict_df[eu_27_tax_deficits.columns[3]][len(eu_27_tax_deficits) + 1] = additional_revenue_gains['Europe']

        total_additional_revenue_gain = eu_27_tax_deficits['From foreign MNEs'].sum() \
            + additional_revenue_gains['Europe'] \
            + additional_revenue_gains['Other Europe']

        dict_df[eu_27_tax_deficits.columns[0]][len(eu_27_tax_deficits) + 2] = 'Total'
        dict_df[eu_27_tax_deficits.columns[1]][len(eu_27_tax_deficits) + 2] = eu_27_tax_deficit
        dict_df[eu_27_tax_deficits.columns[2]][len(eu_27_tax_deficits) + 2] = total_additional_revenue_gain
        dict_df[eu_27_tax_deficits.columns[3]][len(eu_27_tax_deficits) + 2] = \
            eu_27_tax_deficit + total_additional_revenue_gain

        eu_27_tax_deficits = pd.DataFrame.from_dict(dict_df)

        for column_name in eu_27_tax_deficits.columns[1:]:
            eu_27_tax_deficits[column_name] /= 10**6

        return eu_27_tax_deficits.copy()

    def output_intermediary_scenario_gain_formatted(self, minimum_ETR=0.25):

        df = self.compute_intermediary_scenario_gain(minimum_ETR=minimum_ETR)

        df['Collectible tax deficit for the EU'] = df['Collectible tax deficit for the EU'] / 10 ** 6

        df['Collectible tax deficit for the EU'] = df['Collectible tax deficit for the EU'].map('{:,.0f}'.format)

        df.rename(
            columns={
                'Collectible tax deficit for the EU': 'Collectible tax deficit for the EU (€m)',
                'Parent jurisdiction (whitespaces cleaned)': 'Headquarter country or region'
            },
            inplace=True
        )

        return df.copy()

    def output_intermediary_scenario_gain_formatted_alternative(self, minimum_ETR=0.25):

        df = self.compute_intermediary_scenario_gain_alternative(minimum_ETR=minimum_ETR)

        df.drop(columns=['tax_deficit', 'From foreign MNEs'], inplace=True)

        df['Total'] = df['Total'].map('{:,.0f}'.format)

        df.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Taxing country',
                'Total': 'Collectible tax deficit (€m)'
            },
            inplace=True
        )

        df['Taxing country'] = df['Taxing country'].map(
            lambda x: x if x not in ['Europe', 'Other Europe'] else f'"{x}"'
        )

        return df.copy()
