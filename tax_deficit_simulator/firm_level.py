

# ----------------------------------------------------------------------------------------------------------------------
# --- Imports

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

import os
import json

# ----------------------------------------------------------------------------------------------------------------------
# --- Loading the data file correspondences

path_to_correspondences = os.path.dirname(os.path.abspath(__file__))
path_to_correspondences = os.path.join(path_to_correspondences, 'data', 'firm_level_cbcrs_correspondence.json')

# path_to_correspondences = '../tax_deficit_simulator/data/firm_level_cbcrs_correspondence.json'

with open(path_to_correspondences) as file:
    correspondences = json.load(file)

# ----------------------------------------------------------------------------------------------------------------------
# --- Defining the CompanyCalculator class

class CompanyCalculator:

    def __init__(self, company_name):

        if company_name not in correspondences.keys():
            raise Exception('Company is not part of the 10 companies covered by the available data.')

        self.company_name = company_name
        self.file_name = correspondences[company_name]['file_name']
        # self.source = correspondences[company_name]['source']
        # self.url = correspondences[company_name]['url']

        path_to_data = os.path.dirname(os.path.abspath(__file__))
        path_to_data = os.path.join(path_to_data, 'data', 'firm_level_cbcrs', self.file_name)

        # path_to_data = f'../tax_deficit_simulator/data/firm_level_cbcrs/{self.file_name}'

        self.data = pd.read_csv(path_to_data, delimiter=';')

        headquarter_country = self.data.loc[0, 'Headquarter country']

        if headquarter_country == 'Netherlands':
            headquarter_country = 'the Netherlands'

        self.headquarter_country = headquarter_country

        self.year = self.data.loc[0, 'Year']

    def compute_tax_deficits(self, minimum_ETR):
        df = self.data.copy()

        # We focus on jurisdictions with positive profits
        df = df[df['Profit before tax'] > 0].copy()

        # We compute the effective tax rate for each partner jurisdiction with positive profits
        df['ETR'] = df['CIT paid'] / df['Profit before tax']
        df['ETR'] = df['ETR'].map(lambda x: 0 if x < 0 else x)

        # We focus on profits taxed at a rate below the minimum one
        df = df[df['ETR'] < minimum_ETR].copy()

        # We deduce the tax deficit for each partner jurisdiction with positive, low-taxed profits
        df['tax_deficit'] = (minimum_ETR - df['ETR']) * df['Profit before tax']

        return df.copy()

    def compute_tax_revenue_gain(self, minimum_ETR):
        df = self.compute_tax_deficits(minimum_ETR=minimum_ETR)

        return df['tax_deficit'].sum()

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

        if not formatted:
            return df.copy()

        else:

            df[f'Collectible tax deficit for {self.headquarter_country} (€m)'] = \
                df[f'Collectible tax deficit for {self.headquarter_country} (€m)'].map('{:,.0f}'.format)

            df['Effective tax rate (%)'] = df['Effective tax rate (%)'].map('{:.1f}'.format)

            return df.copy()


    def get_second_sentence(self):

        df = self.compute_tax_deficits(minimum_ETR=0.25)

        s = 'We now want to investigate where this tax deficit comes from, i.e. in what jurisdictions the profits taxed'

        s += f' at a lower rate than the minimum effective tax rate were booked by {self.company_name} in {self.year}. '

        s += f'The following table provides the details of the {len(df)} countries where {self.company_name} registered'

        s += ' profits that were taxed below a minimum effective tax rate of 25%.'

        return s







