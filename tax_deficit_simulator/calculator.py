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

path_to_oecd = os.path.join(path_to_dir, 'data', 'test.csv')

path_to_twz = os.path.join(path_to_dir, 'data', 'twz.csv')

path_to_twz_domestic = os.path.join(path_to_dir, 'data', 'twz_domestic.csv')


class TaxDeficitCalculator:

    def __init__(self):
        self.oecd = None
        self.twz = None

        self.assumed_non_haven_ETR_TWZ = 0.2
        self.assumed_haven_ETR_TWZ = 0.1

        self.USD_to_EUR_2016 = 1 / 1.1069031

        self.multiplier_EU = 1.13381004333496
        self.multiplier_world = 1.1330304145813

    def load_clean_data(
        self,
        path_to_oecd=path_to_oecd,
        path_to_twz=path_to_twz,
        path_to_twz_domestic=path_to_twz_domestic,
        inplace=True
    ):
        try:
            oecd = pd.read_csv(path_to_oecd, delimiter=';')
            twz = pd.read_csv(path_to_twz, delimiter=';')
            twz_domestic = pd.read_csv(path_to_twz_domestic, delimiter=';')

        except FileNotFoundError:
            raise Exception('Are you sure these are the right paths for the source files?')

        # --- Cleaning the OECD data

        numeric_columns = list(oecd.columns[5:])

        for column_name in numeric_columns:
            oecd[column_name] = oecd[column_name].map(lambda x: x.replace(',', '.'))
            oecd[column_name] = oecd[column_name].map(lambda x: 0 if x == '..' else x)
            oecd[column_name] = oecd[column_name].astype(float)

        oecd['Partner jurisdiction (whitespaces cleaned)'] = oecd.apply(rename_partner_jurisdictions, axis=1)

        oecd = oecd[
            ~oecd['Partner jurisdiction (whitespaces cleaned)'].isin(['Foreign Jurisdictions Total', 'Stateless'])
        ].copy()

        oecd['ETR'] = oecd['Income Tax Paid (on Cash Basis)'] / oecd['Profit (Loss) before Income Tax']
        oecd['ETR'] = oecd['ETR'].map(lambda x: 0 if x < 0 else x)

        oecd['Is domestic?'] = oecd.apply(
            lambda row: row['Parent jurisdiction (alpha-3 code)'] == row['Partner jurisdiction (alpha-3 code)'],
            axis=1
        ) * 1

        oecd['Is partner jurisdiction a non-haven?'] = 1 - oecd['Is partner jurisdiction a tax haven?']

        # oecd['Is partner jurisdiction a tax haven? - 2'] = oecd['Is partner jurisdiction a tax haven?'].copy()
        # oecd['Is partner jurisdiction a non-haven? - 2'] = oecd['Is partner jurisdiction a non-haven?'].copy()

        oecd['Is partner jurisdiction a tax haven?'] = oecd.apply(
            lambda row: manage_overlap_with_domestic(row, 'haven'),
            axis=1
        )

        oecd['Is partner jurisdiction a non-haven?'] = oecd.apply(
            lambda row: manage_overlap_with_domestic(row, 'non-haven'),
            axis=1
        )

        # --- Cleaning the TWZ tax haven profits data

        twz['Is parent in OECD data?'] = twz['Alpha-3 country code'].map(
            lambda x: x in oecd['Parent jurisdiction (alpha-3 code)'].unique() if x != 'SWE' else False
        ) * 1

        for column_name in ['Profits in all tax havens', 'Profits in all tax havens (positive only)']:
            twz[column_name] = twz[column_name].map(lambda x: x.replace(',', '.'))
            twz[column_name] = twz[column_name].astype(float) * 1000000

        twz = twz[twz['Profits in all tax havens (positive only)'] > 0].copy()

        # --- Cleaning the TWZ domestic profits data

        twz_domestic['Domestic profits'] = twz_domestic['Domestic profits']\
            .map(lambda x: x.replace(',', '.'))\
            .astype(float) * 1000000000

        twz_domestic['Domestic ETR'] = twz_domestic['Domestic ETR'].map(lambda x: x.replace(',', '.')).astype(float)

        if inplace:
            self.oecd = oecd.copy()
            self.twz = twz.copy()
            self.twz_domestic = twz_domestic.copy()

        else:
            return oecd.copy(), twz.copy()

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

        multiplier = (merged_df['is_eu'] * 1.133810043).map(lambda x: 1.133030415 if x == 0 else x)

        merged_df.drop(columns=['is_eu'], inplace=True)

        for column_name in merged_df.columns[2:]:
            merged_df[column_name] = merged_df[column_name] * self.USD_to_EUR_2016 * multiplier

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

    def output_all_tax_deficits_formatted(self, minimum_ETR=0.25):

        df = self.get_total_tax_deficits(minimum_ETR=minimum_ETR)

        df.drop(columns=['Parent jurisdiction (alpha-3 code)'], inplace=True)

        df['tax_deficit'] = df['tax_deficit'] / 10**6
        df['tax_deficit'] = df['tax_deficit'].map('{:,.0f}'.format)

        df.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Headquarter country',
                'tax_deficit': 'Collectible tax deficit (€m)'
            },
            inplace=True
        )

        return df.copy()

    def compute_second_scenario_gain(self, country, minimum_ETR=0.25):

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

        tax_deficits.reset_index(drop=True, inplace=True)

        dict_df = tax_deficits.to_dict()

        dict_df[tax_deficits.columns[0]][len(tax_deficits)] = 'Imputation'
        dict_df[tax_deficits.columns[1]][len(tax_deficits)] = imputation

        dict_df[tax_deficits.columns[0]][len(tax_deficits) + 1] = 'Total'
        dict_df[tax_deficits.columns[1]][len(tax_deficits) + 1] = tax_deficits[tax_deficits.columns[1]].sum()

        df = pd.DataFrame.from_dict(dict_df)

        return df.copy()

    def check_second_scenario_gain_computations(self, minimum_ETR=0.25):

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

            df = self.compute_second_scenario_gain(
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
                df[df['Parent jurisdiction (whitespaces cleaned)'] == 'Imputation'][column_name].iloc[0]
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

        return df.copy()

    def output_second_scenario_gain_formatted(self, country, minimum_ETR=0.25):

        df = self.compute_second_scenario_gain(
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
