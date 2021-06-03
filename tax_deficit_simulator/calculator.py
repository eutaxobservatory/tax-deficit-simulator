"""
This module is dedicated to simulations based on macroeconomic data, namely the anonymized and aggregated country-by-
country data published by the OECD for the year 2016 and the data compiled by Tørløv, Wier and Zucman (2020).

Defining the TaxDeficitCalculator class, which encapsulates all computations for the multilaral, imperfect coordination
and unilateral scenarios presented in the report, this module pursues two main goals:

- providing the computational logic for simulations run on the tax deficit online simulator;

- allowing any Python user to reproduce the results presented in the report and to better understand the assumptions
that lie behind our estimates.

All explanations regarding the estimation methodology can be found in the body of the report or in its appendices. Com-
plementary information about how computations are run in Python can be found in the following docstrings and comments.

So far, the code presented here has not yet been optimized for performance. Feedback on how to improve computation ti-
mes, the readability of the code or anything else are very much welcome!
"""

# ----------------------------------------------------------------------------------------------------------------------
# --- Imports

import numpy as np
import pandas as pd

import os

from utils import rename_partner_jurisdictions, manage_overlap_with_domestic, combine_haven_tax_deficits, \
    COUNTRIES_WITH_MINIMUM_REPORTING, COUNTRIES_WITH_CONTINENTAL_REPORTING


# ----------------------------------------------------------------------------------------------------------------------
# --- Defining paths to data files and other utils

path_to_dir = os.path.dirname(os.path.abspath(__file__))

# We fetch the list of EU-28 and EU-27 country codes from a .csv file in the data folder
path_to_eu_countries = os.path.join(path_to_dir, 'data', 'listofeucountries_csv.csv')
eu_country_codes = list(pd.read_csv(path_to_eu_countries, delimiter=';')['Alpha-3 code'])

eu_27_country_codes = eu_country_codes.copy()
eu_27_country_codes.remove('GBR')

# We fetch the list of tax havens' alpha-3 country codes from a .csv file in the data folder
path_to_tax_haven_list = os.path.join(path_to_dir, 'data', 'tax_haven_list.csv')
tax_haven_country_codes = list(pd.read_csv(path_to_tax_haven_list, delimiter=';')['Alpha-3 code'])

# Absolute paths to data files, especially useful to run the app.py file
path_to_oecd = os.path.join(path_to_dir, 'data', 'oecd.csv')
path_to_twz = os.path.join(path_to_dir, 'data', 'twz.csv')
path_to_twz_domestic = os.path.join(path_to_dir, 'data', 'twz_domestic.csv')
path_to_twz_CIT = os.path.join(path_to_dir, 'data', 'twz_CIT.csv')


# ----------------------------------------------------------------------------------------------------------------------
# --- Defining the TaxDeficitCalculator class

class TaxDeficitCalculator:

    def __init__(self, alternative_imputation=True):
        """
        This is the instantiation method for the TaxDeficitCalculator class.

        It does not require any specific argument. By default, the boolean alternative_imputation is set to True, mea-
        ning that the imputation of the non-haven tax deficit of non-OECD reporting countries at minimum rates of 20% or
        below is operated. For more details on this methodological choice, you can refer to Appendix A of the report.

        The instantiation function is mainly used to define several object attributes that generally correspond to as-
        sumptions taken in the report.
        """

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

        - the "twz_CIT.csv" file, extracted from Table U1 of the TWZ 2019 online appendix. It presents the corporate in-
        come tax revenue of each country in 2016 USD billion.

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

    def get_non_haven_imputation_ratio(self, minimum_ETR):
        """
        For non-OECD reporting countries, we base our estimates on data compiled by Tørsløv, Wier and Zucman (2019).
        These allow to compute domestic and tax-haven-based tax deficit of these countries. We extrapolate the non-haven
        tax deficit of these countries from the tax-haven one.

        We impute the tax deficit in non-haven jurisdictions by estimating the ratio of tax deficits in non-tax havens
        to tax-havens for the EU non-tax haven parent countries in the CbCR data. We assume a 20% ETR in non-tax havens
        and a 10% ETR in tax havens (these rates are defined in two dedicated attributes in the instantiation function).

        This function allows to compute this ratio following the (A2) formula of Appendix A.

        The methodology is described in more details in the Appendix A of the report.
        """

        # We need to have previously loaded and cleaned the OECD data
        if self.oecd is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        # With a minimum ETR of 10%, the formula cannot be applied (division by 0), hence this case disjunction
        if minimum_ETR > 0.1:
            oecd = self.oecd.copy()

            # In the computation of the imputation ratio, we only focus on:
            # - EU-27 parent countries
            mask_eu = oecd['Parent jurisdiction (alpha-3 code)'].isin(eu_27_country_codes)
            # - That are not tax havens
            mask_non_haven = ~oecd['Parent jurisdiction (alpha-3 code)'].isin(tax_haven_country_codes)
            # - And report a detailed country by country breakdown in their CbCR
            mask_minimum_reporting_countries = ~oecd['Parent jurisdiction (alpha-3 code)'].isin(
                COUNTRIES_WITH_MINIMUM_REPORTING + COUNTRIES_WITH_CONTINENTAL_REPORTING
            )

            # We combine the boolean indexing masks
            mask = np.logical_and(mask_eu, mask_non_haven)
            mask = np.logical_and(mask, mask_minimum_reporting_countries)

            # And convert booleans into 0 / 1 integers
            mask = mask * 1

            # We compute the profits registered by retained countries in non-haven countries
            # (excluding domestic profits, cf. the earlier use of the manage_overlap_with_domestic function)
            foreign_non_haven_profits = (
                (
                    mask * oecd['Is partner jurisdiction a non-haven?']
                ) * oecd['Profit (Loss) before Income Tax']
            ).sum()

            # We compute the profits registered by retained countries in tax havens
            # (excluding domestic profits, cf. the earlier use of the manage_overlap_with_domestic function)
            foreign_haven_profits = (
                (
                    mask * oecd['Is partner jurisdiction a tax haven?']
                ) * oecd['Profit (Loss) before Income Tax']
            ).sum()

            # We apply the formula and compute the imputation ratio
            imputation_ratio_non_haven = (
                (
                    # If the minimum ETR is below the rate assumed to be applied on non-haven profits, there is no tax
                    # deficit to collect from these profits, which is why we have this max(..., 0)
                    max(minimum_ETR - self.assumed_non_haven_ETR_TWZ, 0) * foreign_non_haven_profits
                ) /
                ((minimum_ETR - self.assumed_haven_ETR_TWZ) * foreign_haven_profits)
            )

        # We manage the case where the minimum ETR is of 10% and the formula cannot be applied
        elif minimum_ETR == 0.1:

            # As long as tax haven profits are assumed to be taxed at a rate of 10%, the value that we set here has no
            # effect (it will be multiplied to 0 tax-haven-based tax deficits) but to remain consistent with higher
            # values of the minimum ETR, we impute 0

            imputation_ratio_non_haven = 0

        else:
            # We do not yet manage effective tax rates below 10%
            raise Exception('Unexpected minimum ETR entered (strictly below 0.1).')

        return imputation_ratio_non_haven

    def get_alternative_non_haven_factor(self, minimum_ETR):
        """
        Looking at the formula (A2) of Appendix A and at the previous method, we see that for a 15% tax rate, this impu-
        tation would result in no tax deficit to be collected from non-tax haven jurisdictions. Thus, we correct for
        this underestimation by computing the ratio of the tax deficit that can be collected in non-tax havens at a 15%
        and a 25% rate for OECD-reporting countries.

        This class method allows to compute this alternative imputation ratio.

        The methodology is described in more details in the Appendix A of the report.
        """

        # We need to have previously loaded and cleaned the OECD data
        if self.oecd is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        # This method is only useful if the previous one yields a ratio of 0, i.e. if the minimum ETR is of 20% or less
        if minimum_ETR > 0.2:
            raise Exception('These computations are only used when the minimum ETR considered is 0.2 or less.')

        # We use the get_stratified_oecd_data to compute the non-haven tax deficit of OECD-reporting countries
        oecd_stratified = self.get_stratified_oecd_data(
            minimum_ETR=self.reference_rate_for_alternative_imputation
        )

        # We exclude countries whose CbCR breakdown does not allow to distinguish tax-haven and non-haven profits
        df_restricted = oecd_stratified[
            ~oecd_stratified['Parent jurisdiction (alpha-3 code)'].isin(
                COUNTRIES_WITH_CONTINENTAL_REPORTING + COUNTRIES_WITH_MINIMUM_REPORTING
            )
        ].copy()

        # The denominator is the total non-haven tax deficit of relevant countries at the reference minimum ETR
        denominator = df_restricted['tax_deficit_x_non_haven'].sum()

        # We follow the same process, running computations at the minimum ETR this time
        oecd_stratified = self.get_stratified_oecd_data(minimum_ETR=minimum_ETR)

        # We exclude countries whose CbCR breakdown does not allow to distinguish tax-haven and non-haven profits
        df_restricted = oecd_stratified[
            ~oecd_stratified['Parent jurisdiction (alpha-3 code)'].isin(
                COUNTRIES_WITH_CONTINENTAL_REPORTING + COUNTRIES_WITH_MINIMUM_REPORTING
            )
        ].copy()

        # The numerator is the total non-haven tax deficit of relevant countries at the selected minimum ETR
        numerator = df_restricted['tax_deficit_x_non_haven'].sum()

        return numerator / denominator

    def get_stratified_oecd_data(self, minimum_ETR=0.25):
        """
        This method constitutes a first step in the computation of each country's collectible tax deficit in the multi-
        lateral agreement scenario.

        Taking the minimum effective tax rate as input and based on OECD data, this function outputs a DataFrame that
        displays, for each OECD-reporting parent country, the tax deficit that could be collected from the domestic,
        tax haven and non-haven profits of multinationals headquartered in this country.

        The output is in 2016 USD, like the raw OECD data.
        """

        # We need to have previously loaded and cleaned the OECD data
        if self.oecd is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        oecd = self.oecd.copy()

        # We only profits taxed at an effective tax rate above the minimum ETR
        oecd = oecd[oecd['ETR'] < minimum_ETR].copy()

        # We compute the ETR differential for all low-taxed profits
        oecd['ETR_differential'] = oecd['ETR'].map(lambda x: minimum_ETR - x)

        # And deduce the tax deficit generated by each Parent / Partner jurisidiction pair
        oecd['tax_deficit'] = oecd['ETR_differential'] * oecd['Profit (Loss) before Income Tax']

        # Using the aforementioned indicator variables allows to breakdown this tax deficit
        oecd['tax_deficit_x_domestic'] = oecd['tax_deficit'] * oecd['Is domestic?']
        oecd['tax_deficit_x_tax_haven'] = oecd['tax_deficit'] * oecd['Is partner jurisdiction a tax haven?']
        oecd['tax_deficit_x_non_haven'] = oecd['tax_deficit'] * oecd['Is partner jurisdiction a non-haven?']

        # We group the table by Parent jurisdiction such that for, say, France, the table displays the total domestic,
        # tax-haven and non-haven tax deficit generated by French multinationals
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

    def compute_all_tax_deficits(self, minimum_ETR=0.25):
        """
        This method encapsulates most of the computations for the multilateral agreement scenario.

        Taking as input the minimum effective tax rate to apply and based on OECD and TWZ data, it outputs a DataFrame
        which presents, for each country in our sample (countries in OECD and/or TWZ data) the total tax deficit, as
        well as its breakdown into domestic, tax-haven and non-haven tax deficits.

        The output is in 2021 EUR after a currency conversion and the extrapolation from 2016 to 2021 figures.
        """
        # We need to have previously loaded and cleaned the OECD and TWZ data
        if self.oecd is None or self.twz is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        # We use the method defined above and will use its output as a base for the following computations
        oecd_stratified = self.get_stratified_oecd_data(minimum_ETR=minimum_ETR)

        twz = self.twz.copy()

        # From TWZ data on profits registered in tax havens and assuming that these are taxed at a given minimum ETR
        # (10% in the report, see the instantiation function for the definition of this attribute), we deduce the tax-
        # haven-based tax deficit of TWZ countries
        twz['tax_deficit_x_tax_haven_TWZ'] = \
            twz['Profits in all tax havens (positive only)'] * (minimum_ETR - self.assumed_haven_ETR_TWZ)

        # --- Managing countries in both OECD and TWZ data

        # We focus on parent countries which are in both the OECD and TWZ data
        # NB: recall that we do not consider the Swedish CbCR
        twz_in_oecd = twz[twz['Is parent in OECD data?'].astype(bool)].copy()

        # We merge the two DataFrames on country codes
        merged_df = oecd_stratified.merge(
            twz_in_oecd[['Country', 'Alpha-3 country code', 'tax_deficit_x_tax_haven_TWZ']],
            how='left',
            left_on='Parent jurisdiction (alpha-3 code)',
            right_on='Alpha-3 country code'
        ).drop(columns=['Country', 'Alpha-3 country code'])

        # For countries that are in the OECD data but not in TWZ, we impute a tax-haven-based tax deficit from TWZ of 0
        merged_df['tax_deficit_x_tax_haven_TWZ'] = merged_df['tax_deficit_x_tax_haven_TWZ'].fillna(0)

        # Using a small function defined in utils.py, for each parent country, we retain the highest tax-haven tax defi-
        # cit found in the two data sources and store it in a new column of the merged DataFrame
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

        # Summing the tax-haven-based, non-haven and domestic tax deficits yields the total tax deficit of each country
        merged_df['tax_deficit'] = merged_df['tax_deficit_x_tax_haven'] \
            + merged_df['tax_deficit_x_domestic'] \
            + merged_df['tax_deficit_x_non_haven']

        # --- Countries only in the TWZ data

        # We now focus on countries that are absent from the OECD data
        # NB: recall that we do not consider the Swedish CbCR
        twz_not_in_oecd = twz[~twz['Is parent in OECD data?'].astype(bool)].copy()

        twz_not_in_oecd.drop(
            columns=['Profits in all tax havens', 'Profits in all tax havens (positive only)'],
            inplace=True
        )

        # - Extrapolating the foreign non-haven tax deficit

        # We compute the imputation ratio with the method defined above
        imputation_ratio_non_haven = self.get_non_haven_imputation_ratio(minimum_ETR=minimum_ETR)

        # And we deduce the non-haven tax deficit of countries that are only found in TWZ data
        twz_not_in_oecd['tax_deficit_x_non_haven'] = \
            twz_not_in_oecd['tax_deficit_x_tax_haven_TWZ'] * imputation_ratio_non_haven

        # - Computing the domestic tax deficit

        # For countries that are only in TWZ data, we still need to compute their domestic tax deficit
        twz_domestic = self.twz_domestic.copy()

        # We only consider countries whose domestic ETR is stricly below the minimum ETR
        # (otherwise, there is no tax deficit to collect from domestic profits)
        twz_domestic = twz_domestic[twz_domestic['Domestic ETR'] < minimum_ETR].copy()

        # We compute the ETR differential
        twz_domestic['ETR_differential'] = twz_domestic['Domestic ETR'].map(lambda x: minimum_ETR - x)

        # And deduce the domestic tax deficit of each country
        twz_domestic['tax_deficit_x_domestic'] = twz_domestic['ETR_differential'] * twz_domestic['Domestic profits']

        # - Combining the different forms of tax deficit

        # We merge the two DataFrames to complement twz_not_in_oecd with domestic tax deficit results
        twz_not_in_oecd = twz_not_in_oecd.merge(
            twz_domestic[['Alpha-3 country code', 'tax_deficit_x_domestic']],
            how='left',
            on='Alpha-3 country code'
        )

        # As we filtered out countries whose domestic ETR is stricly below the minimum ETR, some missing values
        # appear during the merge; we impute 0 for these as they do not have any domestic tax deficit to collect
        twz_not_in_oecd['tax_deficit_x_domestic'] = twz_not_in_oecd['tax_deficit_x_domestic'].fillna(0)

        # We deduce the total tax deficit for each country
        twz_not_in_oecd['tax_deficit'] = twz_not_in_oecd['tax_deficit_x_tax_haven_TWZ'] \
            + twz_not_in_oecd['tax_deficit_x_domestic'] \
            + twz_not_in_oecd['tax_deficit_x_non_haven']

        # --- Merging the results of the two data sources

        # We need columns to match for the concatenation to operate smoothly
        twz_not_in_oecd.rename(
            columns={
                'Country': 'Parent jurisdiction (whitespaces cleaned)',
                'Alpha-3 country code': 'Parent jurisdiction (alpha-3 code)',
                'tax_deficit_x_tax_haven_TWZ': 'tax_deficit_x_tax_haven'
            },
            inplace=True
        )

        twz_not_in_oecd.drop(columns=['Is parent in OECD data?'], inplace=True)

        # We exclude Sweden from the OECD-drawn results, as we do not consider its CbCR
        merged_df = merged_df[merged_df['Parent jurisdiction (alpha-3 code)'] != 'SWE'].copy()

        # We eventually concatenate the two DataFrames
        merged_df = pd.concat(
            [merged_df, twz_not_in_oecd],
            axis=0
        )

        # --- Extrapolations to 2021 EUR

        # We convert 2016 USD results in 2016 EUR and extraprolate them to 2021 EUR
        for column_name in merged_df.columns[2:]:
            merged_df[column_name] = merged_df[column_name] * self.USD_to_EUR_2016 * self.multiplier_2021

        # --- Managing the case where the minimum ETR is 20% or below for TWZ countries

        # As mentioned above and detailed in Appendix A, the imputation of the non-haven tax deficit of TWZ countries
        # follows a specific process whenever the chosen minimum ETR is of or below 20%
        if minimum_ETR <= 0.2 and self.alternative_imputation:
            # We get the new multiplying factor from the method defined above
            multiplying_factor = self.get_alternative_non_haven_factor(minimum_ETR=minimum_ETR)

            # We compute all tax deficits at the reference rate (25% in the report)
            df = self.compute_all_tax_deficits(
                minimum_ETR=self.reference_rate_for_alternative_imputation
            )

            # We only consider countries that are absent from the OECD data, except Sweden as usual
            oecd_reporting_countries_but_SWE = self.oecd[
                self.oecd['Parent jurisdiction (alpha-3 code)'] != 'SWE'
            ]['Parent jurisdiction (alpha-3 code)'].unique()

            df = df[
                ~df['Parent jurisdiction (alpha-3 code)'].isin(oecd_reporting_countries_but_SWE)
            ].copy()

            # For these countries, we multiply the non-haven tax deficit at the reference rate by the multiplying factor
            df['tax_deficit_x_non_haven_imputation'] = df['tax_deficit_x_non_haven'] * multiplying_factor

            # We save the results in a dictionary that will allow to map the DataFrame that we want to output in the end
            mapping = {}

            for _, row in df.iterrows():
                mapping[row['Parent jurisdiction (alpha-3 code)']] = row['tax_deficit_x_non_haven_imputation']

            # We create a new column in the to-be-output DataFrame which takes as value:
            # - the non-haven tax deficit estimated just above for TWZ countries
            # - 0 for OECD-reporting countries, which do not require this imputation
            merged_df['tax_deficit_x_non_haven_imputation'] = merged_df['Parent jurisdiction (alpha-3 code)'].map(
                lambda country_code: mapping.get(country_code, 0)
            )

            # We deduce the non-haven tax deficit of all countries
            merged_df['tax_deficit_x_non_haven'] += merged_df['tax_deficit_x_non_haven_imputation']

            # And add this imputation also to the column that presents the total tax deficit of each country
            merged_df['tax_deficit'] += merged_df['tax_deficit_x_non_haven_imputation']

            merged_df.drop(
                columns=['tax_deficit_x_non_haven_imputation'],
                inplace=True
            )

        return merged_df.reset_index(drop=True).copy()

    def check_tax_deficit_computations(self, minimum_ETR=0.25):
        """
        Taking the selected minimum ETR as input and relying on the compute_all_tax_deficits method defined above, this
        method outputs a DataFrame that can be compared with Table A1 of the report. For each country in OECD and/or TWZ
        data, it displays its total tax deficit and a breakdown into domestic, tax-haven-based and non-haven tax defi-
        cits. Figures are display in 2021 billion EUR.
        """

        # We start from the output of the previously defined method
        df = self.compute_all_tax_deficits(minimum_ETR=minimum_ETR)

        # And convert numeric columns from 2021 EUR to 2021 billion EUR
        for column_name in df.columns[2:]:
            df[column_name] = df[column_name] / 10**9

        return df.copy()

    def get_total_tax_deficits(self, minimum_ETR=0.25):
        """
        This method takes the selected minimum ETR as input and relies on the compute_all_tax_deficits, to output a Da-
        taFrame with (i) the total tax defict of each in-sample country in 2021 EUR and (ii) the sum of these tax defi-
        cits at the EU-27 and at the whole sample level. It can be considered as an intermediary step towards the fully
        formatted table displayed on the online simulator (section "Multilateral implementation scenario").
        """

        df = self.compute_all_tax_deficits(minimum_ETR=minimum_ETR)

        df = df[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'tax_deficit']
        ]

        df.sort_values(
            by='Parent jurisdiction (whitespaces cleaned)',
            inplace=True
        )

        # We compute the sum of total tax deficits at the EU-27 level and for the whole sample
        total_eu = (df['Parent jurisdiction (alpha-3 code)'].isin(eu_27_country_codes) * 1 * df['tax_deficit']).sum()
        total_whole_sample = df['tax_deficit'].sum()

        # Possibly suboptimal process to add "Total" lines at the end of the DataFrame
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
        """
        Relying on the get_total_tax_deficits method and on TWZ data on corporate income tax revenues, this method out-
        puts a DataFrame that can be compared with the first 4 columns of Table A2 in the report. For each in-sample
        country and at four different minimum ETRs (15%, 21%, 25% and 30% which are the four main cases considered in
        the report), the table presents estimated revenue gains as a percentage of currently corporate income taxes.
        """

        # We need to have previously loaded and cleaned the TWZ data on corporate income tax revenues
        # (figures in the pre-loaded DataFrame are provided in 2016 USD)
        if self.twz_CIT is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        # We compute total tax deficits, first at a 15% minimum ETR and in 2021 EUR
        df = self.get_total_tax_deficits(minimum_ETR=0.15)

        df.rename(columns={'tax_deficit': 'tax_deficit_15'}, inplace=True)

        # We merge the two DataFrames to combine information on collectible tax deficits and current CIT revenues
        merged_df = df.merge(
            self.twz_CIT,
            how='left',
            left_on='Parent jurisdiction (alpha-3 code)',
            right_on='Country (alpha-3 code)'
        ).drop(columns=['Country', 'Country (alpha-3 code)'])

        # We bring back the tax deficit estimated to 2016 USD (from 2021 EUR)
        merged_df['tax_deficit_15'] /= (merged_df['CIT revenue'] * self.multiplier_2021 * self.USD_to_EUR_2016 / 100)

        # For the 3 other rates considered in the output table
        for rate in [0.21, 0.25, 0.3]:
            # We compute total tax deficits at this rate
            df = self.get_total_tax_deficits(minimum_ETR=rate)

            # We add these results to the central DataFrame thanks to a merge operation
            merged_df = merged_df.merge(
                df,
                how='left',
                on='Parent jurisdiction (alpha-3 code)'
            )

            # We impute the missing values produced by the merge
            merged_df['tax_deficit'] = merged_df['tax_deficit'].fillna(0)

            # We rename the newly-added tax deficit column
            merged_df.rename(
                columns={'tax_deficit': f'tax_deficit_{int(rate * 100)}'},
                inplace=True
            )

            # And we bring it back to 2016 USD
            merged_df[f'tax_deficit_{int(rate * 100)}'] /= (
                merged_df['CIT revenue'] * self.multiplier_2021 * self.USD_to_EUR_2016 / 100
            )

        # We want to also verify the EU-27 average and restrict the DataFrame to these countries
        eu_df = merged_df[merged_df['Parent jurisdiction (alpha-3 code)'].isin(eu_27_country_codes)].copy()

        # This attribute stores the average EU-27 revenue gain estimate in % of current CIT revenues for each of the 4
        # minimum ETRs of interest (respectively 15.1%, 30.5%, 52.3% and 84.1% in the report)
        self.check = [
            (
                eu_df[f'tax_deficit_{rate}'] * eu_df['CIT revenue'] / 100
            ).sum() / eu_df['CIT revenue'].sum() for rate in [15, 21, 25, 30]
        ]

        # Coming back to the DataFrame with all in-sample countries, we only keep the relevant columns and output it
        merged_df = merged_df[
            [
                'Parent jurisdiction (whitespaces cleaned)_x',
                'tax_deficit_15', 'tax_deficit_21', 'tax_deficit_25', 'tax_deficit_30'
            ]
        ].copy()

        # NB: in the current version of this method, the successive merges have a poor effect on the "Total" rows that
        # are included in the output of the get_total_tax_deficits method; this could easily be improved

        return merged_df.copy()

    def output_tax_deficits_formatted(self, minimum_ETR=0.25):
        """
        This method is used in the "app.py" file, which underlies the Streamlit simulator. It is used to produce the
        table on the "Multilateral implementation scenario" page. It takes as input the selected minimum ETR and widely
        relies on the get_total_tax_deficits method defined above. It mostly consists in a series of formatting steps.
        """

        # We build the unformatted results table thanks to the get_total_tax_deficits method
        df = self.get_total_tax_deficits(minimum_ETR=minimum_ETR)

        # We only want to include certain countries in the output table:
        # - all the EU-27 countries that are included in our sample (4 unfortunately missing for now)
        # - most of the OECD-reporting countries, excluding only Singapore and Bermuda

        # We first build the list of OECD-reporting countries, excluding Singapore and Bermuda
        oecd_reporting_countries = self.oecd['Parent jurisdiction (alpha-3 code)'].unique()
        oecd_reporting_countries = [
            country_code for country_code in oecd_reporting_countries if country_code not in ['SGP', 'BMU']
        ]

        # From this list, we build the relevant boolean indexing mask that corresponds to our filtering choice
        mask = np.logical_or(
            df['Parent jurisdiction (alpha-3 code)'].isin(eu_27_country_codes),
            df['Parent jurisdiction (alpha-3 code)'].isin(oecd_reporting_countries)
        )

        df = df[mask].copy()

        # We sort values by the name of the parent jurisdiction, in the alphabetical order
        df.sort_values(
            by='Parent jurisdiction (whitespaces cleaned)',
            inplace=True
        )

        df.reset_index(drop=True, inplace=True)

        # We convert 2021 EUR figures into 2021 million EUR ones
        df['tax_deficit'] = df['tax_deficit'] / 10**6

        # Again, the same possibly sub-optimal process to add the "Total" lines
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

        # We drop country codes
        df.drop(columns=['Parent jurisdiction (alpha-3 code)'], inplace=True)

        # And we eventually reformat figures with a thousand separator and a 0-decimal rounding
        df['tax_deficit'] = df['tax_deficit'].map('{:,.0f}'.format)

        # We rename columns
        df.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Headquarter country',
                'tax_deficit': 'Collectible tax deficit (€m)'
            },
            inplace=True
        )

        return df.copy()

    def compute_unilateral_scenario_gain(self, country, minimum_ETR=0.25):
        """
        This method encapsulates most of the computations for the unilateral implementation scenario.

        It takes as input:

        - the name of the country assumed to unilaterally implement the tax deficit collection;

        - the minimum effective tax rate that it applies when collecting the full tax deficit of its multinationals and
        a part of the tax deficit of foreign multinationals, based on the location of their sales.

        The output of this method is a DataFrame organized as follows:

        - each row is a headquarter country whose tax deficit would be collected partly or entirely by the taxing coun-
        try (including the taxing country which collects 100% of the tax deficit of its multinationals);

        - there are two columns, with the name of the headquarter country considered and the tax deficit amount that
        could be collected from its multinationals by the taxing country.

        Figures are presented in 2021 EUR.

        Important disclaimer: for now, this method is not robust to variations in the country name, i.e. only country
        names as presented in the OECD CbCR data will generate a result. These are the country names that are proposed
        in the selectbox on the online simulator.

        The methogology behind these computations is described in much more details in Appendix B of the report.
        """

        # We start from the total tax deficits of all countries which can be partly re-allocated to the taxing country
        tax_deficits = self.get_total_tax_deficits(minimum_ETR=minimum_ETR)

        # The OECD data provides the information of extra-group sales, needed to allocate foreign tax deficits
        oecd = self.oecd.copy()

        # We simply convert the name of the taxing country to the corresponding alpha-3 code
        taxing_country = country
        try:
            taxing_country_code = self.oecd[
                self.oecd['Parent jurisdiction (whitespaces cleaned)'] == taxing_country
            ]['Parent jurisdiction (alpha-3 code)'].iloc[0]
        except:
            taxing_country_code = self.twz[
                self.twz['Country'] == taxing_country
            ]['Alpha-3 country code'].iloc[0]

        # This list will store the allocation ratios (for each headquarter country, the share of its tax deficit that
        # can be collected by the taxing country) computed based on the location of extra-group sales
        attribution_ratios = []

        # We iterate over parent countries in the OECD data
        for country_code in tax_deficits['Parent jurisdiction (alpha-3 code)'].values:

            # The taxing country collects 100% of the tax deficit of its own multinationals
            if country_code == taxing_country_code:
                attribution_ratios.append(1)

            # If the parent country is not the taxing country
            else:
                # We restrict the DataFrame to the CbCR of the considered parent country
                oecd_restricted = oecd[oecd['Parent jurisdiction (alpha-3 code)'] == country_code].copy()

                # If the taxing country is not part of its partner jurisdictions, the attribution ratio is of 0
                if taxing_country_code not in oecd_restricted['Partner jurisdiction (alpha-3 code)'].values:
                    attribution_ratios.append(0)

                else:
                    # We fetch extra-group sales registered in the taxing country
                    mask = (oecd_restricted['Partner jurisdiction (alpha-3 code)'] == taxing_country_code)
                    sales_in_taxing_country = oecd_restricted[mask]['Unrelated Party Revenues'].iloc[0]

                    # We compute total extra-group sales
                    total_sales = oecd_restricted['Unrelated Party Revenues'].sum()

                    # We append the resulting ratio to the list of attribution ratios
                    attribution_ratios.append(sales_in_taxing_country / total_sales)

        # We add this list to the DataFrame as a new column
        tax_deficits['Attribution ratios'] = attribution_ratios

        # We deduce, for each headquarter country, the tax deficit that could be collected by the taxing country
        tax_deficits[f'Collectible tax deficit for {taxing_country}'] = \
            tax_deficits['tax_deficit'] * tax_deficits['Attribution ratios']

        # We eliminate irrelevant columns
        tax_deficits.drop(
            columns=[
                'Attribution ratios',
                'tax_deficit',
                'Parent jurisdiction (alpha-3 code)'
            ],
            inplace=True
        )

        # We filter out rows for which the collectible tax deficit is 0
        tax_deficits = tax_deficits[tax_deficits[f'Collectible tax deficit for {taxing_country}'] > 0].copy()

        # We sort values based on the resulting tax deficit, in descending order
        tax_deficits.sort_values(
            by=f'Collectible tax deficit for {taxing_country}',
            ascending=False,
            inplace=True
        )

        # Because the OECD data only gather 26 headquarter countries, we need to make an assumption on the tax deficit
        # that could be collected from other parent countries, excluded from the 2016 version of the data

        # We therefore double the tax deficit collected from non-US foreign countries
        imputation = tax_deficits[
            ~tax_deficits['Parent jurisdiction (whitespaces cleaned)'].isin([taxing_country, 'United States'])
        ][f'Collectible tax deficit for {taxing_country}'].sum()

        # Except for Germany, for which we add back only half of the tax deficit collected from non-US foreign countries
        if taxing_country_code == 'DEU':
            imputation /= 2

        tax_deficits.reset_index(drop=True, inplace=True)

        # Again the same inelegant way of adding "Total" fields at the end of the DataFrame
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
        """
        Taking as input the selected minimum effective tax rate and relying on the compute_unilateral_scenario_gain,
        this method outputs a DataFrame that can be compared with the Table 3 of the report. For each country that is
        part of the EU-27 and/or included in the 2016 aggregated and anonymized CbCR data of the OECD, it shows the to-
        tal corporate tax revenue gain that could be drawn from the unilateral implementation of the tax deficit col-
        lection. It also provides a breakdown of this total between the tax deficit of the country's own multinationals,
        the amount that could be collected from US multinationals and revenues that could be collected from non-US ones.
        """

        # We build the list of countries that we want to include in the output table
        country_list = self.get_total_tax_deficits()

        country_list = country_list[
            ~country_list['Parent jurisdiction (whitespaces cleaned)'].isin(['Total - EU27', 'Total - Whole sample'])
        ].copy()

        country_list = list(country_list['Parent jurisdiction (whitespaces cleaned)'].values)

        # We prepare the structure of the output first as a dictionary
        output = {
            'Country': country_list,
            'Own tax deficit': [],
            'Collection of US tax deficit': [],
            'Collection of non-US tax deficit': [],
            'Imputation': [],
            'Total': []
        }

        # We iterate over the list of relevant countries
        for country in country_list:

            # Using the method defined above, we output the table presenting the tax deficit that could be collected
            # from a unilateral implementation of the tax deficit collection by the considered country and its origin
            df = self.compute_unilateral_scenario_gain(
                country=country,
                minimum_ETR=minimum_ETR
            )

            column_name = f'Collectible tax deficit for {country}'

            # We fetch the tax deficit that could be collected from the country's own multinationals
            output['Own tax deficit'].append(
                df[df['Parent jurisdiction (whitespaces cleaned)'] == country][column_name].iloc[0]
            )

            # We fetch the tax deficit that could be collected from US multinationals
            if 'United States' in df['Parent jurisdiction (whitespaces cleaned)'].values:
                output['Collection of US tax deficit'].append(
                    df[df['Parent jurisdiction (whitespaces cleaned)'] == 'United States'][column_name].iloc[0]
                )
            else:
                output['Collection of US tax deficit'].append(0)

            # We fetch the tax deficit that was imputed following our methodology
            output['Imputation'].append(
                df[df['Parent jurisdiction (whitespaces cleaned)'] == 'Others (imputation)'][column_name].iloc[0]
            )

            # We fetch the total tax deficit
            output['Total'].append(
                df[df['Parent jurisdiction (whitespaces cleaned)'] == 'Total'][column_name].iloc[0]
            )

            # And finally, we sum the tax deficits collected from foreign non-US multinationals
            output['Collection of non-US tax deficit'].append(
                df[
                    ~df['Parent jurisdiction (whitespaces cleaned)'].isin(
                        [
                            country, 'United States', 'Total', 'Others (imputation)'
                        ]
                    )
                ][column_name].sum()
            )

        # We convert the dictionary into a DataFrame
        df = pd.DataFrame.from_dict(output)

        # We sum the imputation and the tax deficit collected from foreign, non-US multinationals to obtain the uprated
        # figures that correspond to the "Other foreign firms" column of Table 3 in the report
        df['Collection of non-US tax deficit (uprated with imputation)'] = \
            df['Imputation'] + df['Collection of non-US tax deficit']

        # We convert the results from 2021 EUR into 2021 billion EUR
        for column_name in df.columns[1:]:
            df[column_name] /= 10**9

        return df.copy()

    def output_unilateral_scenario_gain_formatted(self, country, minimum_ETR=0.25):
        """
        This method is used in the "app.py" file, which lies behind the Streamlit simulator. It allows to produce the
        table presented on the "Unilateral implementation scenario" page. It takes as input the selected minimum ETR and
        the name of the country assumed to unilaterally implement the tax deficit collection. Then, it widely relies on
        the compute_unilateral_scenario_gain method defined above and mostly consists in a series of formatting steps to
        make the table more readable and understandable.
        """

        # We compute the gains from the unilateral implementation of the tax deficit collection for the taxing country
        df = self.compute_unilateral_scenario_gain(
            country=country,
            minimum_ETR=minimum_ETR
        )

        # We convert the numeric outputs into 2021 million EUR
        df[f'Collectible tax deficit for {country}'] = df[f'Collectible tax deficit for {country}'] / 10**6

        # We reformat figures with two decimals and a thousand separator
        df[f'Collectible tax deficit for {country}'] = \
            df[f'Collectible tax deficit for {country}'].map('{:,.2f}'.format)

        # We rename columns in accordance
        df.rename(
            columns={
                f'Collectible tax deficit for {country}': f'Collectible tax deficit for {country} (€m)',
                'Parent jurisdiction (whitespaces cleaned)': 'Headquarter country'
            },
            inplace=True
        )

        return df.copy()

    def compute_intermediary_scenario_gain(self, minimum_ETR=0.25):
        """
        This method encapsulates the computations used to estimate the corporate tax revenue gains of EU countries,
        should the European Union implement the tax deficit collection as a block. This corresponds therefore to the
        partial cooperation scenario described in the report.

        Taking as input the selected minimum effective tax rate, this method outputs a DataFrame that presents for each
        in-sample EU-27 country:

        - the corporate tax revenue gains that could be collected from its own multinationals ("tax_deficit" column);
        - the tax deficit that could be collected from foreign, non-EU multinationals ("From foreign MNEs" column);
        - and the resulting total corporate tax revenue gain.

        All figures are output in 2021 million EUR.

        The three lines at the end of the DataFrame are a bit specific. Some OECD-reporting contries do not provide a
        perfectly detailed country-by-country report and for these, the "Other Europe" and "Europe" fields are assumed
        to be related to EU countries and are included in the total collectible tax deficit. The final line presents
        this total.

        The methogology behind these computations is described in much more details in Appendix C of the report.
        """

        # We start by computing the total tax deficits of all in-sample countries (those of the multilateral scenario)
        tax_deficits = self.get_total_tax_deficits(minimum_ETR=minimum_ETR)

        oecd = self.oecd.copy()

        # We extract the total tax deficit for the EU-27
        eu_27_tax_deficit = tax_deficits[
            tax_deficits['Parent jurisdiction (whitespaces cleaned)'] == 'Total - EU27'
        ]['tax_deficit'].iloc[0]

        # And we store in a separate DataFrame the tax deficits of EU-27 countries
        eu_27_tax_deficits = tax_deficits[
            tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(
                eu_27_country_codes
            )
        ].copy()

        # We focus only on a few non-EU countries, defined when the TaxDeficitCalculator object is instantiated
        tax_deficits = tax_deficits[
            tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(
                self.country_list_intermediary_scenario
            )
        ].copy()

        # We store the results in a dictionary, which we will map upon the eu_27_tax_deficits DataFrame
        additional_revenue_gains = {}

        # We iterate over EU-27 countries and compute for eacht he tax deficit collected from non-EU multinationals
        for eu_country in eu_27_country_codes:

            td_df = tax_deficits.copy()

            # This dictionary will store the attribution ratios based on extra-group sales to be mapped upon td_df
            attribution_ratios = {}

            # We iterate over non-EU countries in our list
            for country in self.country_list_intermediary_scenario:

                oecd_restricted = oecd[oecd['Parent jurisdiction (alpha-3 code)'] == country].copy()

                # We fetch the extra-group sales registered by the non-EU country's multinationals in the EU-27 country
                # (defaults to 0 if the EU-27 country is not among the partners of the non-EU country)
                sales_in_eu_country = oecd_restricted[
                    oecd_restricted['Partner jurisdiction (alpha-3 code)'] == eu_country
                ]['Unrelated Party Revenues'].sum()

                # We compute the total extra-group sales registered by the non-EU country's multinationals worldwide
                total_sales = oecd_restricted['Unrelated Party Revenues'].sum()

                # We deduce the share of the non-EU country's tax deficit attributable to the EU-27 country
                attribution_ratios[country] = sales_in_eu_country / total_sales

            # We map the attribution_ratios dictionary upon the td_df DataFrame
            td_df['Attribution ratios'] = td_df['Parent jurisdiction (alpha-3 code)'].map(attribution_ratios)

            # We deduce, for each non-EU country, the amount of its tax deficit that is collected by the EU-27 country
            td_df['Collectible tax deficit'] = td_df['Attribution ratios'] * td_df['tax_deficit']

            # We sum all these and multiply the total by 2 to estimate the total tax deficit that the EU-27 country
            # could collect from non-EU multinationals
            additional_revenue_gains[eu_country] = td_df['Collectible tax deficit'].sum() * 2

            # NB: the multiplication by 2 corresponds to the imputation strategy defined in Appendix C of the report

        # We map the resulting dictionary upon the eu_27_tax_deficits DataFrame
        eu_27_tax_deficits['From foreign MNEs'] = eu_27_tax_deficits['Parent jurisdiction (alpha-3 code)'].map(
            additional_revenue_gains
        )

        # And deduce total corporate tax revenue gains from such a scenario for all EU-27 countries
        eu_27_tax_deficits['Total'] = (
            eu_27_tax_deficits['tax_deficit'] + eu_27_tax_deficits['From foreign MNEs']
        )

        # We operate a similar process for "Europe" and "Other Europe" field
        additional_revenue_gains = {}

        for aggregate in ['Europe', 'Other Europe']:

            td_df = tax_deficits.copy()

            attribution_ratios = {}

            for country in self.country_list_intermediary_scenario:

                # We do not consider the "Other Europe" field in the US CbCR as it probably does not correspond to
                # activities operated in EU-27 countries (sufficient country-by-country breakdown to exclude this)
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

        # We drop unnecessary columns
        eu_27_tax_deficits.drop(
            columns=['Parent jurisdiction (alpha-3 code)'],
            inplace=True
        )

        # And we operate very inelegant transformations of the DataFrame to add the "Other Europe", "Europe" and "Total"
        # fields at the bottom of the DataFrame
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

        # Here we compute total corporate tax revenue gains for EU-27 countries
        # NB: We have not multiplied the "Other Europe" and "Europe" fields by 2 (no imputation for these)
        total_additional_revenue_gain = eu_27_tax_deficits['From foreign MNEs'].sum() \
            + additional_revenue_gains['Europe'] \
            + additional_revenue_gains['Other Europe']

        dict_df[eu_27_tax_deficits.columns[0]][len(eu_27_tax_deficits) + 2] = 'Total'
        dict_df[eu_27_tax_deficits.columns[1]][len(eu_27_tax_deficits) + 2] = eu_27_tax_deficit
        dict_df[eu_27_tax_deficits.columns[2]][len(eu_27_tax_deficits) + 2] = total_additional_revenue_gain
        dict_df[eu_27_tax_deficits.columns[3]][len(eu_27_tax_deficits) + 2] = \
            eu_27_tax_deficit + total_additional_revenue_gain

        eu_27_tax_deficits = pd.DataFrame.from_dict(dict_df)

        # We convert 2021 EUR figures into 2021 billion EUR
        for column_name in eu_27_tax_deficits.columns[1:]:
            eu_27_tax_deficits[column_name] /= 10**6

        return eu_27_tax_deficits.copy()

    def output_intermediary_scenario_gain_formatted(self, minimum_ETR=0.25):
        """
        This method is used in the "app.py" file, which lies behind the Streamlit simulator. It allows to produce the
        table presented on the "Partial cooperation scenario" page. It takes as input the selected minimum ETR and then,
        widely relies on the compute_intermediary_scenario_gain method defined above. It mostly consists in a series of
        formatting steps to make the table more readable and understandable.
        """

        # We compute corporate tax revenue gains from the partial cooperation scenario
        df = self.compute_intermediary_scenario_gain(minimum_ETR=minimum_ETR)

        # We eliminate irrelevant columns
        df.drop(columns=['tax_deficit', 'From foreign MNEs'], inplace=True)

        # We reformat figures with a thousand separator and a 0-decimal rounding
        df['Total'] = df['Total'].map('{:,.0f}'.format)

        # We rename columns to make them more explicit
        df.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Taxing country',
                'Total': 'Collectible tax deficit (€m)'
            },
            inplace=True
        )

        # We add quotation marks to the "Europe" and "Other Europe" fields
        df['Taxing country'] = df['Taxing country'].map(
            lambda x: x if x not in ['Europe', 'Other Europe'] else f'"{x}"'
        )

        return df.copy()
