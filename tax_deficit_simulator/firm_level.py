

# ----------------------------------------------------------------------------------------------------------------------
# --- Imports

import numpy as np
import pandas as pd

from scipy.stats.mstats import winsorize

import matplotlib.pyplot as plt

import os
import json

from utils import compute_ETRs


# ----------------------------------------------------------------------------------------------------------------------
# --- Loading the data file correspondences

path_to_correspondences = os.path.dirname(os.path.abspath(__file__))
path_to_correspondences = os.path.join(path_to_correspondences, 'data', 'firm_level_cbcrs_correspondence.json')

# path_to_correspondences = '../tax_deficit_simulator/data/firm_level_cbcrs_correspondence.json'

with open(path_to_correspondences) as file:
    correspondences = json.load(file)


# ----------------------------------------------------------------------------------------------------------------------
# --- Loading the EU country list

path_to_dir = os.path.dirname(os.path.abspath(__file__))

path_to_eu_countries = os.path.join(path_to_dir, 'data', 'listofeucountries_csv.csv')
eu_country_codes = list(pd.read_csv(path_to_eu_countries, delimiter=';')['Alpha-3 code'])


# ----------------------------------------------------------------------------------------------------------------------
# --- Defining the CompanyCalculator class

class CompanyCalculator:

    def __init__(self, company_name):

        self.multiplier_EU = 1.0184
        self.multiplier_world = 0.9991

        if company_name not in correspondences.keys():
            raise Exception('Company is not part of the 10 companies covered by the available data.')

        self.company_name = company_name
        self.file_name = correspondences[company_name]['file_name']
        # self.source = correspondences[company_name]['source']
        # self.url = correspondences[company_name]['url']

        path_to_data = os.path.dirname(os.path.abspath(__file__))
        path_to_data = os.path.join(path_to_data, 'data', 'firm_level_cbcrs', self.file_name)

        # path_to_data = f'../tax_deficit_simulator/data/firm_level_cbcrs/{self.file_name}'

        df = pd.read_csv(path_to_data, delimiter=';')

        columns = ['Revenue', 'Profit before tax', 'CIT paid', 'FTEs']

        if 'Average ETR over 6 years' in df.columns:
            self.kind = 'bank'
            self.exchange_rate = float(str(df['Exchange rate to EUR'].iloc[0]).replace(',', '.'))
            columns += ['Average ETR over 6 years']

        else:
            self.kind = 'mne'
            self.exchange_rate = 1
            columns += ['Statutory CIT rate']

        for column_name in columns:
            df[column_name] = df[column_name].astype(str)
            df[column_name] = df[column_name].map(lambda x: x.replace(',', '.'))
            df[column_name] = df[column_name].astype(float)

        self.data = df.copy()

        headquarter_country = self.data.loc[0, 'Headquarter country']

        if headquarter_country == 'Netherlands':
            headquarter_country = 'the Netherlands'

        self.headquarter_country = headquarter_country

        self.year = self.data.loc[0, 'Year']

    def compute_tax_deficits(self, minimum_ETR):
        df = self.data.copy()

        # We exclude jurisdictions with negative profits
        mask = ~(df['Profit before tax'] < 0)
        df = df[mask].copy()

        df['ETR'] = df.apply(
            lambda row: compute_ETRs(row, kind=self.kind),
            axis=1
        )

        df['ETR'] = winsorize(df['ETR'].values, limits=[0.05, 0.05])

        # We focus on profits taxed at a rate below the minimum one
        df = df[df['ETR'] <= minimum_ETR].copy()

        # We deduce the tax deficit for each partner jurisdiction with positive, low-taxed profits
        df['tax_deficit'] = (minimum_ETR - df['ETR']) * df['Profit before tax']

        multiplier = (
            df['Headquarter country code'].isin(eu_country_codes) * 1 * self.multiplier_EU
        ).map(lambda x: self.multiplier_world if x == 0 else x)

        df['tax_deficit'] = df['tax_deficit'] * self.exchange_rate * multiplier

        return df.copy()

    def compute_tax_revenue_gain(self, minimum_ETR):
        df = self.compute_tax_deficits(minimum_ETR=minimum_ETR)

        return df['tax_deficit'].sum()

    def check_firm_level_results(self):
        output = {
            'Company': list(correspondences.keys()),
        }

        for minimum_ETR in [0.15, 0.21, 0.25, 0.3]:

            output[f'{str(minimum_ETR * 100)}%'] = []

            for company in output['Company']:
                company_calculator = CompanyCalculator(company)

                output[f'{str(minimum_ETR * 100)}%'].append(
                    company_calculator.compute_tax_revenue_gain(minimum_ETR=minimum_ETR)
                )

        df = pd.DataFrame.from_dict(output)

        return df.copy()

    def plot_tax_revenue_gains(self, in_app=False):
        x = np.array([15, 21, 25, 30])
        x_cat = list(map(lambda val: str(val) + '%', x))

        y = np.array([self.compute_tax_revenue_gain(ETR) for ETR in x / 100])

        fig, ax = plt.subplots()

        ax.bar(x=x_cat, height=y, width=0.7, color='#4472C4')

        ax.set_title(
            f'Collectible tax deficit for {self.headquarter_country}'
            + ' depending on the minimum effective tax rate retained'
        )

        ax.set_xlabel('Minimum effective tax rate')
        ax.set_ylabel(f'Collectible tax deficit for {self.headquarter_country} (€m)')

        if not in_app:
            fig.show()

        else:
            return fig

    def get_tax_deficit_origins_table(self, minimum_ETR, formatted=False):
        df = self.compute_tax_deficits(minimum_ETR=minimum_ETR)

        df = df[['Partner jurisdiction', 'ETR', 'tax_deficit']].sort_values(
            by='tax_deficit',
            ascending=False
        ).copy()

        df['ETR'] = df['ETR'] * 100

        df.rename(
            columns={
                'tax_deficit': f'Collectible tax deficit for {self.headquarter_country} (€m)',
                'Partner jurisdiction': 'Jurisdiction where profit was registered',
                'ETR': 'Effective tax rate (%)'
            },
            inplace=True
        )

        df.reset_index(
            drop=True,
            inplace=True
        )

        dict_df = df.to_dict()

        dict_df[df.columns[0]][len(df)] = 'Total'
        dict_df[df.columns[1]][len(df)] = 0
        dict_df[df.columns[2]][len(df)] = df[f'Collectible tax deficit for {self.headquarter_country} (€m)'].sum()

        df = pd.DataFrame.from_dict(dict_df)

        if not formatted:
            df.iloc[-1, 1] = '..'

            return df.copy()

        else:

            df[f'Collectible tax deficit for {self.headquarter_country} (€m)'] = \
                df[f'Collectible tax deficit for {self.headquarter_country} (€m)'].map('{:,.2f}'.format)

            df['Effective tax rate (%)'] = df['Effective tax rate (%)'].map('{:.1f}'.format)

            df.iloc[-1, 1] = '..'

            return df.copy()

    def get_second_sentence(self):

        df = self.compute_tax_deficits(minimum_ETR=0.25)

        s = 'We now want to investigate where this tax deficit comes from, i.e. in what jurisdictions the profits taxed'

        s += f' at a lower rate than the minimum effective tax rate were booked by {self.company_name} in {self.year}. '

        s += f'The following table provides the details of the {len(df)} countries where {self.company_name} registered'

        s += ' profits that were taxed below a minimum effective tax rate of 25%.'

        return s
