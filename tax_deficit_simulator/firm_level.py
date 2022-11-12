"""
This module is dedicated to simulations based on microeconomic data, namely the country-by-country breakdowns mandatori-
ly reported by EU banks since 2014 and the voluntary country-by-country disclosures of some multinationals.

Through the CompanyCalculator class, this module provides the computational logic backing the simulations of the "Case
study with one multinational" page of the online tax deficit simulator.

All explanations regarding the estimation methodology can be found in the body of the report or in its appendices. Com-
plementary information about how computations are run in Python can be found in the following docstrings and comments.

So far, the code presented here has not yet been optimized for performance. Feedback on how to improve computation ti-
mes, the readability of the code or anything else are very much welcome!
"""

# ----------------------------------------------------------------------------------------------------------------------
# --- Imports

import numpy as np
import pandas as pd

from scipy.stats.mstats import winsorize

import matplotlib.pyplot as plt

import os
import json

from tax_deficit_simulator.utils import compute_ETRs


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
        """
        This is the instantiation function for the CompanyCalculator class.

        It takes as argument the name of the company under study. For now, there is not much flexibility in the way the
        company name can be specified. It has to match those of the firm_level_cbcrs_correspondence.json file.

        From there, the instantiation function is mainly used to:

        - define various attributes that either correspond to the assumptions lying behind the estimations presented in
        the report or that will prove useful in the "app.py" file;

        - read the CbCR data of the company from the data folder.
        """

        # Gross growth rate of EU-28 and worldwide GDP in current EUR between 2019 and 2021
        # Extracted from benchmark computations run on Stata
        self.multiplier_EU = 1.01842772960663  # 1.0184
        self.multiplier_world = 0.999141991138458  # 0.9991

        # Only a few companies are covered by the simulator and available in the data folder
        if company_name not in correspondences.keys():
            raise Exception('Company is not part of the 9 companies covered by the available data.')

        # We define some useful attributes
        self.company_name = company_name
        self.file_name = correspondences[company_name]['file_name']

        # We build the path to the corresponding data file
        path_to_data = os.path.dirname(os.path.abspath(__file__))
        path_to_data = os.path.join(path_to_data, 'data', 'firm_level_cbcrs', self.file_name)

        # We read the .csv file in a Pandas DataFrame
        df = pd.read_csv(path_to_data, delimiter=';')

        # Numeric columns to preprocess
        columns = ['Revenue', 'Profit before tax', 'CIT paid', 'FTEs']

        # If this condition is verified, then the company is a bank and we must also preprocess the "Average ETR over 6
        # years" column (which allows to correct for unplausible ETRs)
        if 'Average ETR over 6 years' in df.columns:
            self.kind = 'bank'
            self.exchange_rate = float(str(df['Exchange rate to EUR'].iloc[0]).replace(',', '.'))
            columns += ['Average ETR over 6 years']

        # If this condition is verified, then the company is a non-bank multinational and we must also preprocess the
        # "Statutory CIT rate" column (which will be used to replace unplausible ETRs)
        else:
            self.kind = 'mne'
            self.exchange_rate = 1
            columns += ['Statutory CIT rate']

        # We preprocess numeric columns
        for column_name in columns:
            df[column_name] = df[column_name].astype(str)
            df[column_name] = df[column_name].map(lambda x: x.replace(',', '.'))
            df[column_name] = df[column_name].astype(float)

        # And store the resulting DataFrame in an attribute of the CompanyCalculator object
        self.data = df.copy()

        # We define a few other useful attributes
        headquarter_country = self.data.loc[0, 'Headquarter country'].title()

        if headquarter_country in ['Netherlands', 'United Kingdom']:
            headquarter_country = 'the ' + headquarter_country

        self.headquarter_country = headquarter_country

        self.year = self.data.loc[0, 'Year']

    def compute_tax_deficits(self, minimum_ETR):
        """
        This method encapsulates the key computational logic of the simulation.

        Taking the selected minimum effective tax rate as input, it indeed allows to compute the tax deficit that the
        country where the multinational is headquartered could collect from imposing this minimum ETR on all its pro-
        fits, domestic or foreign.

        It outputs a DataFrame that mainly indicates, for each jurisdiction where the multinational is active:

        - the reported revenue;

        - the reported profit before tax;

        - the amount of corporate income tax paid;

        - the number of employees;

        - the average effective tax rate faced by the multinational over the 6 latest years in the partner jurisdiction
        (for a bank) or the statutory CIT rate of the partner jurisdiction (for a non-bank);

        - the effective tax rate retained based on the methodology detailed in the report;

        - and the resulting tax deficit that can be collected by the headquarter country.
        """
        df = self.data.copy()

        # We exclude jurisdictions with negative profits
        mask = ~(df['Profit before tax'] < 0)
        df = df[mask].copy()

        # We determine what ETR to retain based on the methodology detailed in the report (Appendix D)
        df['ETR'] = df.apply(
            lambda row: compute_ETRs(row, kind=self.kind),
            axis=1
        )

        # We winsorize ETRs to the 5% and 95% quantiles
        df['ETR'] = winsorize(df['ETR'].values, limits=[0.05, 0.05])

        # We focus on profits taxed at an effective rate below the minimum one
        df = df[df['ETR'] <= minimum_ETR].copy()

        # We deduce the tax deficit for each partner jurisdiction with positive, low-taxed profits
        df['tax_deficit'] = (minimum_ETR - df['ETR']) * df['Profit before tax']

        # The last lines are dedicated to the extrapolation of 2019 USD results into 2021 EUR
        multiplier = (
            df['Headquarter country code'].isin(eu_country_codes) * 1 * self.multiplier_EU
        ).map(lambda x: self.multiplier_world if x == 0 else x)

        df['tax_deficit'] = df['tax_deficit'] * self.exchange_rate * multiplier

        return df.copy()

    def compute_tax_revenue_gain(self, minimum_ETR):
        """
        Relying on the compute_tax_deficits method defined above, this method simply returns the total tax deficit that
        the headquarter country could collect from the multinational in 2021 EUR.
        """
        df = self.compute_tax_deficits(minimum_ETR=minimum_ETR)

        return df['tax_deficit'].sum()

    def check_firm_level_results(self):
        """
        This method is mainly used to compare the results of computations defined above with the Table 4 of the report.
        For each of the 9 in-sample companies, we compute their total tax deficits for various minimum effective tax
        rates (15%, 21%, 25%, 30%) and gather the results in a single DataFrame.
        """

        # We instantiate a dictionary that will store the results
        output = {
            'Company': list(correspondences.keys()),
        }

        # We iterate over the effective tax rates of interest
        for minimum_ETR in [0.15, 0.21, 0.25, 0.3]:

            # We create a dedicated key-value pair in the output dictionary
            output[f'{str(minimum_ETR * 100)}%'] = []

            # We iterate over the list of firms for which data is available in this repository
            for company in output['Company']:
                # We instantiate the CompanyCalculator object
                company_calculator = CompanyCalculator(company)

                # And compute the tax deficit for the minimum effective tax rate under consideration
                output[f'{str(minimum_ETR * 100)}%'].append(
                    company_calculator.compute_tax_revenue_gain(minimum_ETR=minimum_ETR)
                )

        # We convert the output dictionary into a Pandas DataFrame
        df = pd.DataFrame.from_dict(output)

        return df.copy()

    def plot_tax_revenue_gains(self, in_app=False):
        """
        This method is used in the "app.py" file, which lies behind the Streamlit simulator. It allows to create the bar
        chart that displays the multinational's tax deficit for the 4 benchmark minimum effective tax rates. The in_app
        argument indicates whether the method is called in or outside the simulator:

        - if the boolean argument is set to True, the method returns the figure object as required by Streamlit;

        - if it is set to False (for instance if the method is called in a notebook), the chart is directly displayed.
        """

        # We create the categorical values for the x axis
        x = np.array([15, 21, 25, 30])
        x_cat = list(map(lambda val: str(val) + '%', x))

        # For each minimum effective tax rate, we compute the corresponding tax deficit, which gives the y values
        y = np.array([self.compute_tax_revenue_gain(ETR) for ETR in x / 100])

        # We instantiate the figure and the axis object
        fig, ax = plt.subplots()

        # We create the bar chart
        ax.bar(x=x_cat, height=y, width=0.7, color='#4472C4')

        # And reformat it
        ax.set_title(
            f'Collectible tax deficit for {self.headquarter_country}'
            + ' depending on the minimum effective tax rate retained'
        )

        ax.set_xlabel('Minimum effective tax rate')
        ax.set_ylabel(f'Collectible tax deficit for {self.headquarter_country} (€m)')

        # Before returning it, depending on the in_app argument
        if not in_app:
            fig.show()

        else:
            return fig

    def get_tax_deficit_origins_table(self, minimum_ETR, formatted=False):
        """
        This method builds upon the compute_tax_deficits method to output a clean DataFrame that presents, for each ju-
        risdiction where the multinational is active and faces an effective tax rate below the selected minimum ETR, the
        effective tax rate retained and the resulting tax deficit in 2021 million EUR. It takes as arguments:

        - the selected minimum effective tax rate;

        - and "formatted", a boolean indicating whether or not to format the table as for the online simulator.
        """

        # We determine the tax deficit of the company and its breakdown by partner jurisdiction thanks to the compute_
        # tax_deficits method defined above
        df = self.compute_tax_deficits(minimum_ETR=minimum_ETR)

        # We sort values based on the tax deficit amount, in descending order
        df = df[['Partner jurisdiction', 'ETR', 'tax_deficit']].sort_values(
            by='tax_deficit',
            ascending=False
        ).copy()

        # ETRs are converted into percentages
        df['ETR'] = df['ETR'] * 100

        # We rename columns in a more appropriate way
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

        # We add the "Total" field at the bottom of the DataFrame
        dict_df = df.to_dict()

        dict_df[df.columns[0]][len(df)] = 'Total'
        dict_df[df.columns[1]][len(df)] = 0
        dict_df[df.columns[2]][len(df)] = df[f'Collectible tax deficit for {self.headquarter_country} (€m)'].sum()

        df = pd.DataFrame.from_dict(dict_df)

        # We either format numeric values as strings or not depending on the "formatted" boolean argument
        if not formatted:
            df.iloc[-1, 1] = '..'

            return df.copy()

        else:

            df[f'Collectible tax deficit for {self.headquarter_country} (€m)'] = \
                df[f'Collectible tax deficit for {self.headquarter_country} (€m)'].map('{:,.2f}'.format)

            df['Effective tax rate (%)'] = df['Effective tax rate (%)'].map('{:.1f}'.format)

            df.iloc[-1, 1] = '..'

            return df.copy()

    def get_first_sentence(self):
        """
        This method is used in the "app.py" file. Without requiring any specific argument, it outputs the first sentence
        displayed on the "Case study with one multinational" page.
        """
        amount = self.compute_tax_revenue_gain(minimum_ETR=0.15)

        s = f'Should {self.headquarter_country} impose a minimum tax rate of 15% on all the profits registered by '

        s += f'{self.company_name}, it could collect an additional tax revenue of about {"{:,.0f}".format(amount)} mil'

        s += 'lion EUR. This is the tax deficit of the company, which is fully attributed to its headquarter country.'

        return s

    def get_second_sentence(self):
        """
        This method is used in the "app.py" file. Without requiring any specific argument, it outputs the second senten-
        ce displayed on the "Case study with one multinational" page.
        """
        df = self.compute_tax_deficits(minimum_ETR=0.15)

        s = 'We now want to investigate where this tax deficit comes from, i.e. in what jurisdictions the profits taxed'

        s += f' at a lower rate than the minimum effective tax rate were booked by {self.company_name} in {self.year}. '

        s += f'The following table provides the details of the {len(df)} countries where {self.company_name} registered'

        s += ' profits that were taxed below a minimum effective tax rate of 15%.'

        return s

    def get_third_sentence(self):
        """
        This method is used in the "app.py" file. Without requiring any specific argument, it outputs the third sentence
        displayed on the "Case study with one multinational" page.
        """
        s = 'After investigating the effect of a 25% minimum rate, the following slider allows you to select what rate,'

        s += ' between 10% and 50%, would be imposed. The table presents the implied corporate tax revenue gain for '

        s += f'{self.headquarter_country} and its breakdown based on the location of low-taxed profits.'

        return s
