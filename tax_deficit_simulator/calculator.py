"""
This module is dedicated to simulations based on macroeconomic data, namely the anonymized and aggregated country-by-
country data published by the OECD for the years 2016 and 2017 and the data compiled by Tørløv, Wier and Zucman (2019).

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

from scipy.stats.mstats import winsorize
import pycountry

import os
import sys

from tax_deficit_simulator.utils import rename_partner_jurisdictions, manage_overlap_with_domestic, \
    COUNTRIES_WITH_MINIMUM_REPORTING, impute_missing_carve_out_values, load_and_clean_twz_main_data, \
    load_and_clean_twz_CIT, load_and_clean_bilateral_twz_data, get_avg_of_available_years, find_closest_year_available,\
    apply_upgrade_factor, online_data_paths, get_growth_rates


# ----------------------------------------------------------------------------------------------------------------------
# --- Defining paths to data files and other utils

path_to_dir = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------------------------------------------------------
# --- Defining the TaxDeficitCalculator class

class TaxDeficitCalculator:

    def __init__(
        self,
        year=2017,
        alternative_imputation=True,
        non_haven_TD_imputation_selection='EU',
        sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
        use_adjusted_profits=True,
        average_ETRs=True,
        carve_outs=False,
        carve_out_rate_assets=None, carve_out_rate_payroll=None,
        depreciation_only=None, exclude_inventories=None, payroll_premium=20,
        ex_post_ETRs=False,
        de_minimis_exclusion=True,
        add_AUT_AUT_row=True,
        extended_dividends_adjustment=False,
        behavioral_responses=False,
        behavioral_responses_method=None,
        behavioral_responses_TH_elasticity=None,
        behavioral_responses_non_TH_elasticity=None,
        behavioral_responses_attribution_formula=None,
        behavioral_responses_include_TWZ=None,
        behavioral_responses_include_problematic_parents=None,
        behavioral_responses_include_domestic=None,
        fetch_data_online=False
    ):
        """
        This is the instantiation method for the TaxDeficitCalculator class.

        All its arguments have a default value. They determine possible variations in the methodology. Please refer to
        the methodological sections of previous reports and notes for more information. Using the default arguments only
        will yield the current benchmark estimates without substance-based carve-outs.

        Required arguments are the following:

        - the income year on which computations should be based (integer, either 2016 or 2017). Set to 2016 by default;

        - the boolean "alternative_imputation" (set to True by default), determines whether the imputation of the non-
        haven tax deficit of non-OECD reporting countries at minimum rates of 20% or below is operated. For more details
        on this methodological choice, one can refer to Appendix A of the June 2021 report;

        - the "non_haven_TD_imputation_selection" argument is a character string that can take two values: either "EU"
        or "non-US". It determines the set of countries that are taken as comparables in country-by-country report sta-
        tistics to extrapolate TWZ countries' tax haven tax deficit. More details can be found in the documentation of
        the "get_non_haven_imputation_ratio" below;

        - the "sweden_treatment" argument is a character string. Because of the very low ETRs observed on domestic pro-
        fits in Swedish country-by-country data, this country can be treated specifically. If "exclude" is chosen, the
        code disregards country-by-country data and use TWZ data. Instead, if "adjust" is chosen, the code corrects for
        the intra-group dividends included in the domestic profits. See Appendix B of the October 2021 note for more in-
        formation about this adjustment. Argument set to "adjust" by default;

        - the "belgium_treatment" argument is a character string. As described in Appendix C of the October 2021 note,
        because of possible anomalies in the Belgian country-by-country data, this country can be treated specifically.
        If "none" is chosen, no adjustment is operated; if "exclude" is chosen, we use TWZ data and disregard CbCR data;
        if "adjust" is chosen, profits before tax are adjusted as described in the appendix; if "replace" is chosen, we
        replace the problematic observations with the corresponding values for the other income year. Argument is set to
        "replace" by default;

        - the "SGP_CYM_treatment" argument is a character string. Because of possible anomalies in the Singapore - Cay-
        man Islands observation of the 2017 country-by-country report statistics, we propose to treat this country pair
        specifically. If "none" is chosen, no adjustment is operated; if instead "replace" is chosen, we rather consider
        the 2016 values, uprated to 2017. Set to "replace" by default;

        - the boolean "use_adjusted_profits" indicates whether or not priority should be given to the adjusted profits
        before tax provided by some reporting countries (the Netherlands and the UK) over the usual profits before tax
        in country-by-country report statistics. This allows to limit the effect of intra-group dividends on estimates.
        It is set to True by default;

        - the boolean "average_ETRs" determines whether to average the ETRs over the two years of data (2016 and 2017)
        before running the tax deficit estimates. Set to True by default;

        - the boolean "carve_outs" (False by default) indicates whether to simulate substance-based carve-outs;

        - the boolean "de_minimis_exclusion" indicates whether to apply a proxy for the "de minimis exclusion" of small
        foreign affiliates. It is set to True by default;

        - the boolean "add_AUT_AUT_row" determines, when the selected income year is 2017, whether to add the AUT-AUT
        country pair observed in the 2017 full-sample country-by-country report statistics (including both profit- and
        loss-making entities). Indeed, otherwise, the country pair is missing from the sub-sample that we use in priori-
        ty. It is set to True by default;

        - the boolean "extended_dividends_adjustment" (set to False by default) indicates whether to apply the extended
        adjustment for intra-group dividends that is described in Appendix B of the October 2021 note;

        - the boolean "fetch_data_online" (False by default) determines whether to use data stored locally in the "data"
        folder (False) or online (True).

        If the "carve_outs" argument is set to True, additional arguments are required:

        - "carve_out_rate_assets" and "carve_out_rate_payroll" (floats between 0 and 1) respectively determine what sha-
        re of tangible assets and payroll should be deduced from the pre-tax profits of multinationals;

        - the boolean "depreciation_only" indicates whether to only account for depreciation expenses (instead of the
        full value of tangible assets) in the tangible assets component of the carve-outs. Following the methodology of
        the OECD Secretariat in its Economic Impact Assessment of Oct. 2020, is this argument is set to True, we appro-
        ximate depreciation expenses as 10% of the book value of tangible assets;

        - the boolean "exclude_inventories" indicates whether to downgrade the tangible assets values provided by the
        OECD's aggregated and anonymized country-by-country data. As a simplification of the OECD's methodology (Oct.
        2020), if the argument is set to True, we reduce all tangible assets by 24%;

        - "payroll_premium" (float between 0 and 100 (considered as a %)) determines what upgrade to apply to the pay-
        roll proxy. Indeed, the latter is based on ILO's data about per-country mean annual earnings. Considering that
        the employees of large multinationals generally earn above-average wages, we propose to apply a premium to our
        payroll proxy;

        - the boolean "ex_post_ETR" (set to False by default) indicates whether to re-compute the ETR of each country
        pair with the post-carve-out profits as denominator instead of the initial profits before tax.

        From there, the instantiation function is mainly used to define several object attributes that generally corres-
        pond to assumptions taken in the methodology.
        """

        if year not in [2016, 2017, 2018]:
            # Due to the availability of country-by-country report statistics
            raise Exception('Only three years can be chosen for macro computations: 2016, 2017, and 2018.')

        if sweden_treatment not in ['exclude', 'adjust']:
            # See Appendix B of the October 2021 note
            raise Exception(
                'The Swedish case can only be treated in two ways: considering it as excluded from OECD CbCR data'
                + ' ("exclude") or adjusting the domestic pre-tax profits ("adjust").'
            )

        if belgium_treatment not in ['none', 'exclude', 'adjust', 'replace']:
            # See Appendix C of the October 2021 note
            raise Exception(
                'The Belgian case can only be treated in three ways: using the OECD CbCR data as they are ("none"), '
                + 'using TWZ data instead ("exclude"), using the relevant financial year for problematic partner '
                + 'jurisdictions ("replace") or adjusting pre-tax profits ("adjust").'
            )

        if SGP_CYM_treatment not in ['none', 'replace'] and year == 2017:
            # Possible anomalies in the 2017 Singapore - Cayman Islands observation of CbCR data
            raise Exception(
                'The case of the 2017 Singapore - Cayman Islands observation can only be treated in two ways: '
                + 'either doing nothing (pass SGP_CYM_treatment="none") or replacing the observation with that for '
                + '2016 (pass SGP_CYM_treatment="replace").'
            )

        if year == 2017 and add_AUT_AUT_row is None:
            # AUT-AUT country pair missing in the 2017 sub-sample of profit-making entities
            raise Exception(
                'If you want to analyse 2017 data, you need to indicate whether to add the AUT-AUT row from the full'
                + ' sample (including both negative and positive profits) or not, via the "add_AUT_AUT_row" argument.'
            )

        if (sweden_treatment == 'exclude' or not use_adjusted_profits) and extended_dividends_adjustment:
            raise Exception(
                'The extended_dividends_adjustment is only valid if Sweden-Sweden profits before tax are adjusted and '
                + 'if adjusted profits are used whenever they are available (when use_adjusted_profits=True is passed.)'
            )

        if behavioral_responses and carve_outs:
            raise Exception(
                'Behavioral responses can only be used without the substance-based carve-outs.'
            )

        if behavioral_responses and (
            behavioral_responses_method is None or behavioral_responses_method not in [
                'linear_elasticity', 'bratta_et_al'
            ]
        ):
            raise Exception(
                "If you want to include firms's behavioral responses in the simulation, you must indicate which method"
                + ' should be used (either "linear_elasticity" or "bratta_et_al" for the cubic functional form).'
            )

        if behavioral_responses and behavioral_responses_method == 'linear_elasticity' and (
            behavioral_responses_TH_elasticity is None or behavioral_responses_non_TH_elasticity is None
        ):
            raise Exception(
                "If you want to include firms' behavioral responses in the simulation using the 'linear_elasticity'"
                + ", you must indicate the elasticity that should be used for tax havens and for non-havens."
            )

        if behavioral_responses and (
            behavioral_responses_attribution_formula is None or behavioral_responses_attribution_formula not in [
                'optimistic', 'pessimistic'
            ]
        ):
            raise Exception(
                "If you want to include firms' behavioral responses in the simulation, you must specify the attribution"
                + ' that should be used (either "optimistic" or "pessimistic"). These are detailed in the associated'
                + ' PDF file.'
            )

        if behavioral_responses and behavioral_responses_include_TWZ is None:
            raise Exception(
                "If you want to include firms' behavioral responses in the simulation, you must specify whether to "
                + "include tax haven profits of TWZ countries' multinationals in the behavioral adjustment."
            )

        if behavioral_responses and behavioral_responses_include_problematic_parents is None:
            raise Exception(
                "If you want to include firms' behavioral responses in the simulation, you must specify whether to "
                + "include problematic parents' multinationals in the behavioral adjustment."
            )

        if behavioral_responses and behavioral_responses_include_domestic is None:
            raise Exception(
                "If you want to include firms' behavioral responses in the simulation, you must specify whether to "
                + "include domestic observations (profits booked in the headquarter country) in the adjustment."
            )

        self.fetch_data_online = fetch_data_online

        if self.fetch_data_online:
            # URL to the list of EU-28 and EU-27 country codes from a .csv file
            path_to_eu_countries = online_data_paths['path_to_eu_countries']

            # URL to the list of tax havens' alpha-3 country codes from a .csv file
            path_to_tax_haven_list = online_data_paths['path_to_tax_haven_list']

            # URL to country codes
            self.path_to_geographies = online_data_paths['path_to_geographies']

            # Local path to the GDP growth rates
            self.path_to_GDP_growth_rates = (
                "https://github.com/eutaxobservatory/tax-deficit-simulator/blob/"
                + "master/tax_deficit_simulator/data/gdpgrowth.xlsx?raw=true"
            )

            # Local path to the USD-EUR exchange rates
            self.path_to_usdeur_xrate = (
                "https://github.com/eutaxobservatory/tax-deficit-simulator/blob/"
                + "master/tax_deficit_simulator/data/usdeur_xrate.xlsx?raw=true"
            )

        else:
            # Local path to the list of EU-28 and EU-27 country codes from a .csv file in the data folder
            path_to_eu_countries = os.path.join(path_to_dir, 'data', 'listofeucountries_csv.csv')

            # Local path to list of tax havens' alpha-3 country codes from a .csv file in the data folder
            path_to_tax_haven_list = os.path.join(path_to_dir, 'data', 'tax_haven_list.csv')

            # Local path to country codes
            self.path_to_geographies = os.path.join(path_to_dir, 'data', 'geographies.csv')

            # Local path to the GDP growth rates
            self.path_to_GDP_growth_rates = os.path.join(path_to_dir, 'data', 'gdpgrowth.xlsx')

            # Local path to the USD-EUR exchange rates
            self.path_to_usdeur_xrate = os.path.join(path_to_dir, 'data', 'usdeur_xrate.xlsx')

        # Storing EU Member-States' country codes
        eu_country_codes = list(pd.read_csv(path_to_eu_countries, delimiter=';')['Alpha-3 code'])

        eu_27_country_codes = eu_country_codes.copy()
        eu_27_country_codes.remove('GBR')
        self.eu_27_country_codes = eu_27_country_codes.copy()

        # Storing the country codes of tax havens
        tax_haven_country_codes = list(pd.read_csv(path_to_tax_haven_list, delimiter=';')['Alpha-3 code'])
        self.tax_haven_country_codes = tax_haven_country_codes.copy()

        # Storing the chosen year
        self.year = year

        # These attributes will store the data loaded with the "load_clean_data" method
        self.oecd = None
        self.twz = None
        self.twz_domestic = None
        self.twz_CIT = None
        self.mean_wages = None
        self.statutory_rates = None

        # For non-OECD reporting countries, data are taken from TWZ 2019 appendix tables
        # An effective tax rate of 20% is assumed to be applied on profits registered in non-havens
        self.assumed_non_haven_ETR_TWZ = 0.2

        # An effective tax rate of 10% is assumed to be applied on profits registered in tax havens
        self.assumed_haven_ETR_TWZ = 0.1

        # Specific treatment of some reporting jurisdictions or some observations
        self.sweden_treatment = sweden_treatment

        if sweden_treatment == 'exclude':
            self.sweden_exclude = True
            self.sweden_adjust = False

        else:
            self.sweden_exclude = False
            self.sweden_adjust = True

        self.belgium_treatment = belgium_treatment
        self.SGP_CYM_treatment = SGP_CYM_treatment
        self.use_adjusted_profits = use_adjusted_profits

        # Reading the Excel file with the growth rates of GDP
        GDP_growth_rates = pd.read_excel(
            self.path_to_GDP_growth_rates,
            engine='openpyxl'
        ).set_index(
            'CountryGroupName'
        )

        self.average_ETRs_bool = average_ETRs
        self.deflator_2016_to_2017 = GDP_growth_rates.loc['World', 'uprusd1716']

        self.de_minimis_exclusion = de_minimis_exclusion

        self.extended_dividends_adjustment = extended_dividends_adjustment

        self.sweden_adj_ratio_2016 = (342 - 200) / 342
        self.sweden_adj_ratio_2017 = (512 - 266) / 512
        self.sweden_adj_ratio_2018 = (49.1 - 29.8) / 49.1

        # Average exchange rate over the relevant year, extracted from benchmark computations run on Stata
        # Source: European Central Bank
        xrates = pd.read_excel(self.path_to_usdeur_xrate, engine='openpyxl').set_index('year')
        self.USD_to_EUR = 1 / xrates.loc[self.year, 'usd']

        if year == 2016:

            # Gross growth rate of worldwide GDP in current EUR between 2016 and 2021
            # Extracted from the benchmark computations run on Stata
            self.multiplier_2021 = GDP_growth_rates.loc['World', 'upreur2116']

            self.COUNTRIES_WITH_CONTINENTAL_REPORTING = ['AUT', 'NOR', 'SVN', 'SWE']

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
                'SGP',
                'ZAF',
                'IDN',
                'JPN'
            ]

            self.unilateral_scenario_non_US_imputation_ratio = 1
            self.unilateral_scenario_correction_for_DEU = 2
            self.intermediary_scenario_imputation_ratio = 2

            if self.sweden_adjust:
                self.sweden_adjustment_ratio = self.sweden_adj_ratio_2016

            else:
                self.sweden_adjustment_ratio = 1

            if self.belgium_treatment == 'adjust':
                self.belgium_partner_for_adjustment = 'NLD'

            elif self.belgium_treatment == 'replace':
                self.belgium_partner_for_replacement = 'NLD'
                self.belgium_year_for_replacement = 2017

                self.belgium_GDP_growth_multiplier = 1 / GDP_growth_rates.loc['European Union', 'uprusd1716']

        elif year == 2017:

            # Gross growth rate of worldwide GDP in current EUR between 2017 and 2021
            # Extracted from the benchmark computations run on Stata
            self.multiplier_2021 = GDP_growth_rates.loc['World', 'upreur2117']

            self.COUNTRIES_WITH_CONTINENTAL_REPORTING = ['AUT', 'GBR', 'GRC', 'IMN', 'NOR', 'SVN', 'SWE']

            # The list of countries whose tax deficit is partly collected by EU countries in the intermediary scenario
            self.country_list_intermediary_scenario = [
                'ARG', 'AUS', 'BMU', 'BRA', 'CAN', 'CHE', 'CHL', 'CHN', 'GBR', 'IDN',
                'IMN', 'IND', 'JPN', 'MEX', 'MYS', 'NOR', 'PER', 'SGP', 'USA', 'ZAF'
            ]

            self.unilateral_scenario_non_US_imputation_ratio = 0.25
            self.unilateral_scenario_correction_for_DEU = 1
            self.intermediary_scenario_imputation_ratio = 1 + 2 / 3

            if self.sweden_adjust:
                self.sweden_adjustment_ratio = self.sweden_adj_ratio_2017

            else:
                self.sweden_adjustment_ratio = 1

            if self.belgium_treatment == 'adjust':
                self.belgium_partner_for_adjustment = 'GBR'

            elif self.belgium_treatment == 'replace':
                self.belgium_partner_for_replacement = 'GBR'
                self.belgium_year_for_replacement = 2016

                self.belgium_GDP_growth_multiplier = GDP_growth_rates.loc['European Union', 'uprusd1716']

            if self.SGP_CYM_treatment == 'replace':
                self.SGP_CYM_GDP_growth_multiplier = GDP_growth_rates.loc['World', 'uprusd1716']

            self.add_AUT_AUT_row = add_AUT_AUT_row

        elif year == 2018:

            # Gross growth rate of worldwide GDP in current EUR between 2018 and 2021
            # Extracted from the benchmark computations run on Stata
            self.multiplier_2021 = GDP_growth_rates.loc['World', 'upreur2118']

            self.COUNTRIES_WITH_CONTINENTAL_REPORTING = ['AUT', 'GBR', 'GRC', 'IMN', 'LTU', 'SVN', 'SWE']

            # --- TO BE UPDATED? ---------------------------------------------------------------------------------------
            # The list of countries whose tax deficit is partly collected by EU countries in the intermediary scenario
            self.country_list_intermediary_scenario = [
                'ARG', 'AUS', 'BMU', 'BRA', 'CAN', 'CHE', 'CHL', 'CHN', 'GBR', 'IDN',
                'IMN', 'IND', 'JPN', 'MEX', 'MYS', 'NOR', 'PER', 'SGP', 'USA', 'ZAF'
            ]

            self.unilateral_scenario_non_US_imputation_ratio = 0.25
            self.unilateral_scenario_correction_for_DEU = 1
            self.intermediary_scenario_imputation_ratio = 1 + 2 / 3
            # --- TO BE UPDATED? ---------------------------------------------------------------------------------------

            if self.sweden_adjust:
                self.sweden_adjustment_ratio = self.sweden_adj_ratio_2018

            else:
                self.sweden_adjustment_ratio = 1

        # For rates of 0.2 or lower an alternative imputation is used to estimate the non-haven tax deficit of non-OECD
        # reporting countries; this argument allows to enable or disable this imputation
        self.alternative_imputation = alternative_imputation
        self.reference_rate_for_alternative_imputation = 0.25
        self.non_haven_TD_imputation_selection = non_haven_TD_imputation_selection

        # This boolean indicates whether or not to apply substance-based carve-outs
        self.carve_outs = carve_outs

        # In case we want to simulate substance-based carve-outs, a few additional steps are required
        if carve_outs:

            # We first check whether all the required parameters were provided
            if (
                carve_out_rate_assets is None or carve_out_rate_payroll is None
                or depreciation_only is None or exclude_inventories is None
                or ex_post_ETRs is None
            ):

                raise Exception(
                    'If you want to simulate substance-based carve-outs, you need to indicate all the parameters.'
                )

            if ex_post_ETRs and average_ETRs:
                raise Exception('Computing ETRs ex-post the carve-outs is not compatible with computing average ETRs.')

            # We now store the parameters retained
            self.carve_out_rate_assets = carve_out_rate_assets
            self.carve_out_rate_payroll = carve_out_rate_payroll
            self.depreciation_only = depreciation_only
            self.exclude_inventories = exclude_inventories
            self.payroll_premium = payroll_premium
            self.ex_post_ETRs = ex_post_ETRs

            # This corresponds to the OECD Secretariat's simulations in its Economic Impact Assessment (Oct. 2020):
            # inventories are excluded from tangible assets and only depreciation expenses can be partly deducted
            if depreciation_only and exclude_inventories:
                self.assets_multiplier = 0.1 * (1 - 0.24)

            # Here, we only account for depreciation expenses but do not exclude inventories
            elif depreciation_only and not exclude_inventories:
                self.assets_multiplier = 0.1

            # In this case, we take the full value of tangible assets to form the tangible assets component of substan-
            # ce-based carve-outs, while excluding inventories
            elif not depreciation_only and exclude_inventories:
                self.assets_multiplier = (1 - 0.24)

            # Benchmark case, where we take the full value of tangible assets without adjusting for inventories
            else:
                self.assets_multiplier = 1

        else:
            self.carve_out_rate_assets = None
            self.carve_out_rate_payroll = None
            self.depreciation_only = None
            self.exclude_inventories = None
            self.payroll_premium = None
            self.ex_post_ETRs = None

        if self.de_minimis_exclusion:
            self.exclusion_threshold_revenues = 10 * 10**6 / self.USD_to_EUR
            self.exclusion_threshold_profits = 1 * 10**6 / self.USD_to_EUR

        self.behavioral_responses = behavioral_responses

        if self.behavioral_responses:
            self.behavioral_responses_method = behavioral_responses_method

            self.carve_out_rate_assets = 0.05
            self.carve_out_rate_payroll = 0.05
            self.depreciation_only = False
            self.exclude_inventories = False
            self.payroll_premium = 20
            self.ex_post_ETRs = False
            self.assets_multiplier = 1

            if self.behavioral_responses_method == 'linear_elasticity':
                self.behavioral_responses_TH_elasticity = behavioral_responses_TH_elasticity
                self.behavioral_responses_non_TH_elasticity = behavioral_responses_non_TH_elasticity

            else:
                self.behavioral_responses_beta_1 = -3.916
                self.behavioral_responses_beta_2 = 11.11
                self.behavioral_responses_beta_3 = -11.58

            self.behavioral_responses_attribution_formula = behavioral_responses_attribution_formula
            self.behavioral_responses_problematic_parents = []
            self.behavioral_responses_include_TWZ = behavioral_responses_include_TWZ
            self.behavioral_responses_include_problematic_parents = behavioral_responses_include_problematic_parents
            self.behavioral_responses_include_domestic = behavioral_responses_include_domestic

    def load_clean_data(
        self,
        path_to_dir=path_to_dir,
        inplace=True
    ):
        """
        This method allows to load and clean data from various data sources, either online or stored locally.

        Default paths are used to let the simulator run via the app.py file. If you wish to use the tax_deficit_calcula-
        tor package in another context, you can save the data locally and give the method paths to the data files. The
        possibility to load the files from an online host instead will soon be implemented.
        """

        # If data are loaded from files stored online
        if self.fetch_data_online:

            # We construct the URL from which we can load the CSV country-by-country dataset
            # url_base = 'http://stats.oecd.org/SDMX-JSON/data/'
            # dataset_identifier = 'CBCR_TABLEI/'
            # dimensions = 'ALL/'
            # agency_name = 'OECD'

            # self.path_to_oecd = (
            #     url_base + dataset_identifier + dimensions + agency_name + '?contenttype=csv'
            # )

            self.path_to_oecd = online_data_paths['path_to_oecd']

            # Path to TWZ data on corporate income tax revenues and to data on statutory tax rates
            self.path_to_twz_CIT = online_data_paths['path_to_twz_CIT']
            self.path_to_statutory_rates = online_data_paths['path_to_statutory_rates']

            # Path to ILO data
            url_base = online_data_paths['url_base']
            file_name = f'iloearn{self.year - 2000}.csv'
            path_to_preprocessed_mean_wages = url_base + file_name

            # Path to TWZ data on profits booked in tax havens
            url_base += 'TWZ/'
            url_base += f'{str(self.year)}/'
            self.path_to_excel_file = url_base + 'TWZ.xlsx'

            # Path to TWZ data on profits booked domestically (with ETRs)
            path_to_twz_domestic = url_base + 'twz_domestic.xlsx'

        else:
            # Path to OECD data, TWZ data on corporate income tax revenues and data on statutory tax rates
            self.path_to_oecd = os.path.join(path_to_dir, 'data', 'oecd.csv')
            self.path_to_twz_CIT = os.path.join(path_to_dir, 'data', 'twz_CIT.csv')
            self.path_to_statutory_rates = os.path.join(path_to_dir, 'data', 'statutory_rates.xlsx')

            # Path to ILO data
            path_to_preprocessed_mean_wages = os.path.join(path_to_dir, 'data', f'iloearn{self.year - 2000}.csv')

            # Path to TWZ data on profits booked in tax havens
            self.path_to_excel_file = os.path.join(path_to_dir, 'data', 'TWZ', str(self.year), 'TWZ.xlsx')

            # Path to TWZ data on profits booked domestically (with ETRs)
            path_to_twz_domestic = os.path.join(path_to_dir, 'data', 'TWZ', str(self.year), 'twz_domestic.xlsx')

        try:
            # We try to read the files from the provided paths
            oecd = pd.read_csv(self.path_to_oecd)

            if self.year == 2016:
                delimiter = ';'
            else:
                delimiter = ','

            preprocessed_mean_wages = pd.read_csv(path_to_preprocessed_mean_wages, delimiter=delimiter)

            statutory_rates = pd.read_excel(self.path_to_statutory_rates, engine='openpyxl')

            twz = load_and_clean_twz_main_data(
                path_to_excel_file=self.path_to_excel_file,
                path_to_geographies=self.path_to_geographies
            )

            twz_CIT = load_and_clean_twz_CIT(
                path_to_excel_file=self.path_to_excel_file,
                path_to_geographies=self.path_to_geographies
            )

            twz_domestic = pd.read_excel(
                path_to_twz_domestic,
                engine='openpyxl'
            )

        except FileNotFoundError:

            # If at least one of the files is not found
            raise Exception('Are you sure these are the right paths for the source files?')

        # --- Cleaning the OECD data

        if self.year == 2017 and self.add_AUT_AUT_row:
            # Fetching the values for the AUT-AUT country pair from the full-sample 2017 data
            temp = oecd[
                np.logical_and(
                    oecd['PAN'] == 'PANELA',
                    oecd['YEA'] == 2017
                )
            ].copy()

            temp.drop(
                columns=['PAN', 'Grouping', 'Flag Codes', 'Flags', 'YEA', 'Year'],
                inplace=True
            )

            temp = temp.pivot(
                index=['COU', 'Ultimate Parent Jurisdiction', 'JUR', 'Partner Jurisdiction'],
                columns='Variable',
                values='Value'
            ).reset_index()

            temp = temp[
                np.logical_and(
                    temp['COU'] == 'AUT',
                    temp['JUR'] == 'AUT'
                )
            ].copy()

            self.temp_AUT = temp.copy()

        # We restrict the OECD data to the sub-sample of interest
        oecd = oecd[oecd['PAN'] == 'PANELAI'].copy()

        # Dealing with Belgian data depending on the value of "belgium_treatment" - First fetching the relevant values
        if self.belgium_treatment == 'adjust':
            temp = oecd[
                np.logical_and(
                    oecd['COU'] == 'BEL',
                    oecd['JUR'] == self.belgium_partner_for_adjustment
                )
            ].copy()

            temp = temp[temp['CBC'].isin(['TOT_REV', 'PROFIT'])].copy()
            temp = temp[temp['Year'] == (2017 if self.year == 2016 else 2016)].copy()

            temp = temp[['CBC', 'Value']].set_index('CBC')

            self.belgium_ratio_for_adjustment = (temp.loc['PROFIT'] / temp.loc['TOT_REV'])['Value']

        elif self.belgium_treatment == 'replace':
            belgium_data_for_replacement = oecd[
                np.logical_and(
                    oecd['COU'] == 'BEL',
                    np.logical_and(
                        oecd['JUR'] == self.belgium_partner_for_replacement,
                        oecd['YEA'] == self.belgium_year_for_replacement
                    )
                )
            ].copy()

            mask = ~(belgium_data_for_replacement['CBC'] == 'EMPLOYEES')
            belgium_data_for_replacement['Value'] *= (mask * (self.belgium_GDP_growth_multiplier - 1) + 1)

            self.belgium_data_for_replacement = belgium_data_for_replacement.copy()

        # Dealing with the problematic Singapore-Cayman Islands observation - First fetching the relevant values
        if self.SGP_CYM_treatment == 'replace' and self.year == 2017:
            SGP_CYM_data_for_replacement = oecd[
                np.logical_and(
                    oecd['COU'] == 'SGP',
                    np.logical_and(
                        oecd['JUR'] == 'CYM',
                        oecd['YEA'] == 2016
                    )
                )
            ].copy()

            mask = ~(SGP_CYM_data_for_replacement['CBC'] == 'EMPLOYEES')
            SGP_CYM_data_for_replacement['Value'] *= (mask * (self.SGP_CYM_GDP_growth_multiplier - 1) + 1)

            self.SGP_CYM_data_for_replacement = SGP_CYM_data_for_replacement.copy()

        # Applying the extended adjustment for intra-group dividends if relevant
        if self.extended_dividends_adjustment:
            temp = oecd[
                np.logical_and(
                    oecd['COU'] == oecd['JUR'],
                    oecd['Year'] == 2017
                )
            ].copy()

            sweden_profits = temp[
                np.logical_and(
                    temp['COU'] == 'SWE',
                    temp['CBC'] == 'PROFIT'
                )
            ]['Value'].iloc[0]
            adj_sweden_profits = sweden_profits * self.sweden_adj_ratio_2017

            adj_profits = temp[temp['CBC'] == 'PROFIT_ADJ']['Value'].sum()
            self.adj_profits_countries = temp[temp['CBC'] == 'PROFIT_ADJ']['COU'].unique()
            profits = temp[
                np.logical_and(
                    temp['COU'].isin(self.adj_profits_countries),
                    temp['CBC'] == 'PROFIT'
                )
            ]['Value'].sum()

            self.extended_adjustment_ratio = (adj_sweden_profits + adj_profits) / (sweden_profits + profits)

        # Restricting the data to the relevant income year
        oecd = oecd[oecd['Year'] == self.year].copy()

        # Dealing with Belgian data depending on the value of "belgium_treatment" - Applying the adjustment
        if self.belgium_treatment == 'replace':
            oecd = oecd[
                ~np.logical_and(
                    oecd['COU'] == 'BEL',
                    oecd['JUR'] == self.belgium_partner_for_replacement
                )
            ].copy()

            oecd = pd.concat([oecd, self.belgium_data_for_replacement], axis=0)

        # Dealing with the problematic Singapore-Cayman Islands observation - Applying the adjustment
        if self.SGP_CYM_treatment == 'replace' and self.year == 2017:
            oecd = oecd[
                ~np.logical_and(
                    oecd['COU'] == 'SGP',
                    oecd['JUR'] == 'CYM'
                )
            ].copy()

            oecd = pd.concat([oecd, self.SGP_CYM_data_for_replacement], axis=0)

        # We drop a few irrelevant columns from country-by-country data
        oecd.drop(
            columns=['PAN', 'Grouping', 'Flag Codes', 'Flags', 'YEA', 'Year'],
            inplace=True
        )

        # We reshape the DataFrame from a long to a wide dataset
        oecd = oecd.pivot(
            index=['COU', 'Ultimate Parent Jurisdiction', 'JUR', 'Partner Jurisdiction'],
            columns='Variable',
            values='Value'
        ).reset_index()

        # Adding the AUT-AUT values from the full sample if relevant
        if self.year == 2017 and self.add_AUT_AUT_row:
            oecd = pd.concat(
                [oecd, self.temp_AUT],
                axis=0
            ).reset_index(drop=True)

        # We rename some columns to match the code that has been written before modifying how OECD data are loaded
        oecd.rename(
            columns={
                'COU': 'Parent jurisdiction (alpha-3 code)',
                'Ultimate Parent Jurisdiction': 'Parent jurisdiction (whitespaces cleaned)',
                'JUR': 'Partner jurisdiction (alpha-3 code)',
                'Partner Jurisdiction': 'Partner jurisdiction (whitespaces cleaned)'
            },
            inplace=True
        )

        # Thanks to a function defined in utils.py, we rename the "Foreign Jurisdictions Total" field for all countries
        # that only report a domestic / foreign breakdown in their CbCR
        oecd['Partner jurisdiction (whitespaces cleaned)'] = oecd.apply(rename_partner_jurisdictions, axis=1)

        # We eliminate stateless entities and the "Foreign Jurisdictions Total" fields
        oecd = oecd[
            ~oecd['Partner jurisdiction (whitespaces cleaned)'].isin(['Foreign Jurisdictions Total', 'Stateless'])
        ].copy()

        # We replace missing "Income Tax Paid" values by the corresponding "Income Tax Accrued" values
        # (Some missing values remain even after this edit)
        oecd['Income Tax Paid (on Cash Basis)'] = oecd.apply(
            (
                lambda row: row['Income Tax Paid (on Cash Basis)']
                if not np.isnan(row['Income Tax Paid (on Cash Basis)'])
                else row['Income Tax Accrued - Current Year']
            ),
            axis=1
        )

        # We clean the statutory corporate income tax rates
        column_of_interest = f'statrate{self.year - 2000}'
        statutory_rates = statutory_rates[['Country code', column_of_interest]].copy()

        statutory_rates.rename(
            columns={
                'Country code': 'partner',
                column_of_interest: 'statrate'
            },
            inplace=True
        )

        self.statutory_rates = statutory_rates.copy()

        # And we merge it with country-by-country data, on partner jurisdiction alpha-3 codes
        oecd = oecd.merge(
            statutory_rates,
            how='left',
            left_on='Partner jurisdiction (alpha-3 code)', right_on='partner'
        )

        oecd.drop(columns=['partner'], inplace=True)

        # We impute missing "Income Tax Paid" values assuming that pre-tax profits are taxed at the local statutory rate
        oecd['Income Tax Paid (on Cash Basis)'] = oecd.apply(
            (
                lambda row: row['Income Tax Paid (on Cash Basis)']
                if not np.isnan(row['Income Tax Paid (on Cash Basis)'])
                else row['Profit (Loss) before Income Tax'] * row['statrate']
            ),
            axis=1
        )

        oecd.drop(columns=['statrate'], inplace=True)

        # We adjust the domestic pre-tax profits for Sweden (with a neutral factor if "exclude" was chosen)
        oecd['Profit (Loss) before Income Tax'] = oecd.apply(
            (
                lambda row: row['Profit (Loss) before Income Tax'] * self.sweden_adjustment_ratio
                if row['Parent jurisdiction (alpha-3 code)'] == 'SWE'
                and row['Partner jurisdiction (alpha-3 code)'] == 'SWE'
                else row['Profit (Loss) before Income Tax']
            ),
            axis=1
        )

        # We adjust the pre-tax profits of Belgian multinationals if the "adjust" option has been chosen
        if self.belgium_treatment == 'adjust':
            oecd['Profit (Loss) before Income Tax'] = oecd.apply(
                (
                    lambda row: row['Total Revenues'] * self.belgium_ratio_for_adjustment
                    if row['Parent jurisdiction (alpha-3 code)'] == 'BEL'
                    and row['Partner jurisdiction (alpha-3 code)'] == self.belgium_partner_for_adjustment
                    else row['Profit (Loss) before Income Tax']
                ),
                axis=1
            )

        # If we prioritarily use adjusted pre-tax profits, we make the required adjustment
        if self.use_adjusted_profits and self.year == 2017:
            oecd['Profit (Loss) before Income Tax'] = oecd.apply(
                (
                    lambda row: row['Adjusted Profit (Loss) before Income Tax']
                    if not np.isnan(row['Adjusted Profit (Loss) before Income Tax'])
                    else row['Profit (Loss) before Income Tax']
                ),
                axis=1
            )

        # Applying the extended adjustment for intra-group dividends if relevant
        if self.extended_dividends_adjustment:
            multiplier = np.logical_and(
                oecd['Parent jurisdiction (alpha-3 code)'] == oecd['Partner jurisdiction (alpha-3 code)'],
                ~oecd['Parent jurisdiction (alpha-3 code)'].isin(['SWE'] + list(self.adj_profits_countries))
            ) * 1

            multiplier = multiplier.map(
                {0: 1, 1: self.extended_adjustment_ratio}
            )

            oecd['Profit (Loss) before Income Tax'] *= multiplier

        if not self.average_ETRs_bool:

            # ETR computation (using tax paid as the numerator)
            oecd['ETR'] = oecd['Income Tax Paid (on Cash Basis)'] / oecd['Profit (Loss) before Income Tax']
            oecd['ETR'] = oecd['ETR'].map(lambda x: 0 if x < 0 else x)
            oecd['ETR'] = oecd['ETR'].fillna(0)

        else:
            # We compute ETRs over both 2016 and 2017 fiscal years
            average_ETRs_df = self.get_average_CbCR_ETRs()

            # We input these average ETRs into our dataset
            oecd = oecd.merge(
                average_ETRs_df,
                how='left',
                on=['Parent jurisdiction (alpha-3 code)', 'Partner jurisdiction (alpha-3 code)']
            )

        # Adding an indicator variable for domestic profits (rows with the same parent and partner jurisdiction)
        oecd['Is domestic?'] = oecd.apply(
            lambda row: row['Parent jurisdiction (alpha-3 code)'] == row['Partner jurisdiction (alpha-3 code)'],
            axis=1
        ) * 1

        # We add an indicator variable that takes value 1 if and only if the partner is a tax haven
        oecd['Is partner jurisdiction a tax haven?'] = oecd['Partner jurisdiction (alpha-3 code)'].isin(
            self.tax_haven_country_codes
        ) * 1

        # Adding another indicator variable that takes value 1 if and only if the partner is not a tax haven
        oecd['Is partner jurisdiction a non-haven?'] = 1 - oecd['Is partner jurisdiction a tax haven?']

        # This indicator variable is used specifically for the simulation of carve-outs; it takes value 1 if and only if
        # the partner jurisdiction is not the parent jurisdiction, not a tax haven and not a regional aggregate
        oecd['Is partner jurisdiction a non-haven? - CO'] = oecd.apply(
            (
                lambda row: 0
                if (
                    row['Parent jurisdiction (alpha-3 code)'] in COUNTRIES_WITH_MINIMUM_REPORTING
                    and row['Partner jurisdiction (alpha-3 code)'] == 'FJT'
                ) or (
                    row['Parent jurisdiction (alpha-3 code)'] in self.COUNTRIES_WITH_CONTINENTAL_REPORTING
                    and row['Partner jurisdiction (alpha-3 code)'] in [
                        'GRPS', 'AFRIC', 'AMER', 'ASIAT', 'EUROP', 'OAM', 'OTE', 'OAS', 'OAF'
                    ]
                ) or (
                    row['Is domestic?'] == 1
                )
                else row['Is partner jurisdiction a non-haven?']
            ),
            axis=1
        )

        # This indicator variable, used specifically for the simulation of carve-outs, takes value 1 if and only if the
        # partner is a regional aggregate
        oecd['Is partner jurisdiction an aggregate partner? - CO'] = np.logical_and(
            oecd['Is domestic?'] == 0,
            np.logical_and(
                oecd['Is partner jurisdiction a non-haven? - CO'] == 0,
                oecd['Is partner jurisdiction a tax haven?'] == 0
            )
        ) * 1

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

        # We apply - if relevant - the de minimis exclusion based on revenue and profit thresholds
        if self.de_minimis_exclusion:
            mask_revenues = (oecd['Total Revenues'] >= self.exclusion_threshold_revenues)
            mask_profits = (oecd['Profit (Loss) before Income Tax'] >= self.exclusion_threshold_profits)

            mask_de_minimis_exclusion = np.logical_or(mask_revenues, mask_profits)

            oecd = oecd[mask_de_minimis_exclusion].copy()

        # We need some more work on the data if we want to simulate substance-based carve-outs
        if self.carve_outs or self.behavioral_responses:

            # We merge earnings data with country-by-country data on partner jurisdiction codes
            oecd = oecd.merge(
                preprocessed_mean_wages[['partner2', 'earn']],
                how='left',
                left_on='Partner jurisdiction (alpha-3 code)', right_on='partner2'
            )

            oecd.drop(columns=['partner2'], inplace=True)

            oecd.rename(
                columns={
                    'earn': 'ANNUAL_VALUE'
                },
                inplace=True
            )

            # We clean the mean annual earnings column
            oecd['ANNUAL_VALUE'] = oecd['ANNUAL_VALUE'].map(
                lambda x: x.replace(',', '.') if isinstance(x, str) else x
            ).astype(float)

            # We deduce the payroll proxy from the number of employees and from mean annual earnings
            oecd['PAYROLL'] = oecd['Number of Employees'] * oecd['ANNUAL_VALUE'] * (1 + self.payroll_premium / 100)

            # We compute substance-based carve-outs from both payroll and tangible assets
            oecd['CARVE_OUT'] = (
                self.carve_out_rate_payroll * oecd['PAYROLL']
                + (
                    self.carve_out_rate_assets *
                    oecd['Tangible Assets other than Cash and Cash Equivalents'] * self.assets_multiplier
                )
            )

            # This column will contain slightly modified carve-outs, carve-outs being replaced by pre-tax profits
            # wherever the former exceeds the latter
            oecd['CARVE_OUT_TEMP'] = oecd.apply(
                (
                    lambda row: row['CARVE_OUT'] if row['Profit (Loss) before Income Tax'] > row['CARVE_OUT']
                    or np.isnan(row['CARVE_OUT'])
                    else row['Profit (Loss) before Income Tax']
                ),
                axis=1
            )

            # We exclude rows with missing carve-out values in a temporary DataFrame
            oecd_temp = oecd[
                ~np.logical_or(
                    oecd['PAYROLL'].isnull(),
                    oecd['Tangible Assets other than Cash and Cash Equivalents'].isnull()
                )
            ].copy()

            # We compute the average reduction in non-haven pre-tax profits due to carve-outs
            self.avg_carve_out_impact_non_haven = (
                oecd_temp[
                    oecd_temp['Is partner jurisdiction a non-haven? - CO'] == 1
                ]['CARVE_OUT_TEMP'].sum() /
                oecd_temp[
                    oecd_temp['Is partner jurisdiction a non-haven? - CO'] == 1
                ]['Profit (Loss) before Income Tax'].sum()
            )

            # We do the same for pre-tax profits booked in tax havens, domestically and in aggregate partners
            self.avg_carve_out_impact_tax_haven = (
                oecd_temp[oecd_temp['Is partner jurisdiction a tax haven?'] == 1]['CARVE_OUT_TEMP'].sum() /
                oecd_temp[
                    oecd_temp['Is partner jurisdiction a tax haven?'] == 1
                ]['Profit (Loss) before Income Tax'].sum()
            )
            self.avg_carve_out_impact_domestic = (
                oecd_temp[oecd_temp['Is domestic?'] == 1]['CARVE_OUT_TEMP'].sum() /
                oecd_temp[oecd_temp['Is domestic?'] == 1]['Profit (Loss) before Income Tax'].sum()
            )
            self.avg_carve_out_impact_aggregate = (
                oecd_temp[
                    oecd_temp['Is partner jurisdiction an aggregate partner? - CO'] == 1
                ]['CARVE_OUT_TEMP'].sum() /
                oecd_temp[
                    oecd_temp['Is partner jurisdiction an aggregate partner? - CO'] == 1
                ]['Profit (Loss) before Income Tax'].sum()
            )

            # We impute missing carve-out values based on these average reductions in pre-tax profits
            oecd['CARVE_OUT'] = oecd.apply(
                lambda row: impute_missing_carve_out_values(
                    row,
                    avg_carve_out_impact_domestic=self.avg_carve_out_impact_domestic,
                    avg_carve_out_impact_tax_haven=self.avg_carve_out_impact_tax_haven,
                    avg_carve_out_impact_non_haven=self.avg_carve_out_impact_non_haven,
                    avg_carve_out_impact_aggregate=self.avg_carve_out_impact_aggregate
                ),
                axis=1
            )

            # Some missing values remain whenever profits before tax are missing
            oecd = oecd[~oecd['CARVE_OUT'].isnull()].copy()

            oecd['UNCARVED_PROFITS'] = oecd['Profit (Loss) before Income Tax'].values

            # We remove substance-based carve-outs from pre-tax profits
            oecd['Profit (Loss) before Income Tax'] = oecd.apply(
                (
                    lambda row: row['Profit (Loss) before Income Tax'] - row['CARVE_OUT']
                    if row['Profit (Loss) before Income Tax'] - row['CARVE_OUT'] >= 0
                    else 0
                ),
                axis=1
            )

            if self.ex_post_ETRs:
                oecd['ETR'] = oecd['Income Tax Paid (on Cash Basis)'] / oecd['Profit (Loss) before Income Tax']
                oecd['ETR'] = oecd['ETR'].map(lambda x: 0 if x < 0 else x)
                oecd['ETR'] = oecd['ETR'].fillna(0)

        if self.behavioral_responses:
            # Determining the unshifting rate for each observation
            # Note that it is systematically 0 when the ETR is at least 15% and for domestic observations
            if self.behavioral_responses_method == 'linear_elasticity':
                oecd['ELASTICITY'] = (
                    # Foreign non-havens and regional aggregates
                    oecd['Is partner jurisdiction a non-haven?'] * self.behavioral_responses_non_TH_elasticity

                    # Foreign tax havens
                    + oecd['Is partner jurisdiction a tax haven?'] * self.behavioral_responses_TH_elasticity
                )

                if self.behavioral_responses_include_domestic:
                    oecd['ELASTICITY'] += (
                        # If the parent jurisdiction is a tax haven
                        oecd['Parent jurisdiction (alpha-3 code)'].isin(
                            self.tax_haven_country_codes
                        ) * self.behavioral_responses_TH_elasticity

                        # If the parent jurisdiction is not a tax haven
                        + ~oecd['Parent jurisdiction (alpha-3 code)'].isin(
                            self.tax_haven_country_codes
                        ) * self.behavioral_responses_non_TH_elasticity

                        # Focusing on domestic observations
                    ) * (oecd['Parent jurisdiction (alpha-3 code)'] == oecd['Partner jurisdiction (alpha-3 code)']) * 1

                oecd['UNSHIFTING_RATE'] = oecd['ELASTICITY'] * oecd['ETR'].map(lambda x: max(15 - x * 100, 0))
                # Before computing 15 - ETR, I multiply the ETR by 100 as it is otherwise comprised between 0 and 1

            else:
                if self.behavioral_responses_include_domestic:
                    multiplier = (oecd['ETR'] < 0.15) * 1

                else:
                    multiplier = np.logical_and(
                        oecd['ETR'] < 0.15,
                        oecd['Parent jurisdiction (alpha-3 code)'] != oecd['Partner jurisdiction (alpha-3 code)']
                    ) * 1

                # We apply the formula obtained in "behavioral_responses.pdf"
                oecd['UNSHIFTING_RATE'] = (
                    1 - np.exp(
                        self.behavioral_responses_beta_1 * 0.15
                        + self.behavioral_responses_beta_2 * 0.15**2
                        + self.behavioral_responses_beta_3 * 0.15**3
                        - self.behavioral_responses_beta_1 * oecd['ETR']
                        - self.behavioral_responses_beta_2 * oecd['ETR']**2
                        - self.behavioral_responses_beta_3 * oecd['ETR']**3
                    )
                ) * multiplier

            # We deduce the unshifted profits
            oecd['UNSHIFTED_PROFITS'] = oecd['UNCARVED_PROFITS'] * oecd['UNSHIFTING_RATE']
            oecd['NEW_PROFITS'] = oecd['UNCARVED_PROFITS'] - oecd['UNSHIFTED_PROFITS']

            # We isolate the profits that must be distributed with the relevant country codes
            to_be_distributed = oecd[
                [
                    'Parent jurisdiction (alpha-3 code)',
                    'Partner jurisdiction (alpha-3 code)',
                    'UNSHIFTED_PROFITS']
            ].copy()
            to_be_distributed = to_be_distributed[to_be_distributed['UNSHIFTED_PROFITS'] > 0].copy()

            # We iterate over the country pairs for which there is a positive amount of unshifted profits to allocate
            for _, row in to_be_distributed.iterrows():

                parent_country = row['Parent jurisdiction (alpha-3 code)']   # Country i in the formula
                low_tax_country = row['Partner jurisdiction (alpha-3 code)']   # Country k in the formula
                unshifted_profits = row['UNSHIFTED_PROFITS']   # U_{i,k} in the LaTeX file

                # We get the corresponding ETR (ETR_{i,k}) in the preprocessed OECD data
                etr_ik = oecd[
                    np.logical_and(
                        oecd['Parent jurisdiction (alpha-3 code)'] == parent_country,
                        oecd['Partner jurisdiction (alpha-3 code)'] == low_tax_country
                    )
                ]['ETR'].iloc[0]

                # multiplier will contain a dummy indicating whether or not a country pair is eligible
                # to get some of the unshifted profits

                # Eligibility first requires to have country i as parent country
                is_parent_country = (oecd['Parent jurisdiction (alpha-3 code)'] == parent_country) * 1

                # And the ETR must be at least 15% (1_{\{ETR_{i, j} \geq 15\%\} in the LaTeX file)
                is_ETR_above_15 = (oecd['ETR'] >= 0.15) * 1

                # We interact the two conditions
                multiplier = is_parent_country * is_ETR_above_15

                # This condition is satisfied if we find at least one eligible destination for the unshifted profits
                if multiplier.sum() > 0:

                    # We compute the ETR differential (oecd['ETR'] stands for ETR_{i,j})
                    # Multiplying by the multiplier dummy ensures that we have 0 for all the ineligible country pairs
                    oecd['ETR_differential_ijk'] = (oecd['ETR'] - etr_ik) * multiplier

                    # There should be no negative ETR differentials since eligibility requires ETR_{i,j} to be above 15%
                    # and profits are unshifted only from country pairs with an ETR below 15%, but we can still check
                    if (oecd['ETR_differential_ijk'] < 0).sum() > 0:
                        raise Exception('Weird stuff with negative ETR differentials.')

                    # We deduce the numerator depending on the attribution formula retained
                    if self.behavioral_responses_attribution_formula == 'optimistic':
                        oecd['numerator_ijk'] = (
                            oecd['PAYROLL'].fillna(0)
                            + oecd['Tangible Assets other than Cash and Cash Equivalents'].fillna(0)
                        ) * oecd['ETR_differential_ijk']   # Multiplying by the ETR differential

                    else:
                        temp_columns = []
                        for column in ['PAYROLL', 'Tangible Assets other than Cash and Cash Equivalents']:
                            oecd[column + '_TEMP'] = oecd[column].fillna(0)
                            temp_columns.append(column + '_TEMP')

                        oecd['numerator_ijk'] = oecd.apply(
                            (
                                lambda row: (
                                    row['PAYROLL_TEMP']
                                    + row['Tangible Assets other than Cash and Cash Equivalents_TEMP']
                                ) / row['ETR_differential_ijk'] if row['ETR_differential_ijk'] > 0 else 0
                            ),
                            axis=1
                        )

                        oecd = oecd.drop(columns=temp_columns)

                    # In both cases, denominator is obtained by summing the numerator
                    denominator = oecd['numerator_ijk'].sum()

                    # And we eventually deduce the share of unshifted profits attributable to country j
                    oecd['varphi_ijk'] = oecd['numerator_ijk'] / denominator

                # If there is no eligible obs, we re-attribute profits to the pair from which they were unshifted
                else:
                    is_partner_country = (oecd['Partner jurisdiction (alpha-3 code)'] == low_tax_country) * 1
                    multiplier = is_parent_country * is_partner_country

                    oecd['varphi_ijk'] = multiplier

                    self.behavioral_responses_problematic_parents.append(parent_country)

                # In these last steps, we actually attribute the unshifted profits
                oecd['attributed_ijk'] = unshifted_profits * oecd['varphi_ijk']
                oecd['NEW_PROFITS'] += oecd['attributed_ijk']

            # Dropping the variables that are not relevant anymore
            oecd = oecd.drop(columns=['ETR_differential_ijk', 'numerator_ijk', 'varphi_ijk', 'attributed_ijk'])

            # We deduce the change in CIT revenues involved by the recomposition of profits
            oecd['DELTA_CIT_j'] = (oecd['NEW_PROFITS'] - oecd['UNCARVED_PROFITS']) * oecd['ETR']

            # We can sum these changes by partner jurisdictions and save them as an attribute of the calculator
            self.behavioral_responses_Delta_CIT_j = oecd.groupby(
                ['Partner jurisdiction (whitespaces cleaned)', 'Partner jurisdiction (alpha-3 code)']
            ).sum(
            )[
                'DELTA_CIT_j'
            ].reset_index()

            # Eventually, we replace the pre-tax profits by the recomposed profits
            # Note that although we went through the carve-out computations, we end up with pre-carve-out profits
            oecd['Profit (Loss) before Income Tax'] = oecd['NEW_PROFITS'].values

            if self.behavioral_responses_include_problematic_parents:
                multiplier = oecd['Parent jurisdiction (alpha-3 code)'].isin(
                    self.behavioral_responses_problematic_parents
                )

                oecd['Profit (Loss) before Income Tax'] -= (oecd['UNSHIFTED_PROFITS'] * multiplier)

        # --- Cleaning the TWZ tax haven profits data

        # Adding an indicator variable for OECD reporting - We do not consider the Swedish CbCR if "exclude" was chosen
        if self.sweden_exclude and self.belgium_treatment == 'exclude':
            twz['Is parent in OECD data?'] = twz['Alpha-3 country code'].map(
                lambda x: x in oecd['Parent jurisdiction (alpha-3 code)'].unique() if x in ['SWE', 'BEL'] else False
            ) * 1

        elif self.sweden_exclude and self.belgium_treatment != 'exclude':
            twz['Is parent in OECD data?'] = twz['Alpha-3 country code'].map(
                lambda x: x in oecd['Parent jurisdiction (alpha-3 code)'].unique() if x != 'SWE' else False
            ) * 1

        elif not self.sweden_exclude and self.belgium_treatment == 'exclude':
            twz['Is parent in OECD data?'] = twz['Alpha-3 country code'].map(
                lambda x: x in oecd['Parent jurisdiction (alpha-3 code)'].unique() if x != 'BEL' else False
            ) * 1

        else:
            twz['Is parent in OECD data?'] = twz['Alpha-3 country code'].map(
                lambda x: x in oecd['Parent jurisdiction (alpha-3 code)'].unique()
            ) * 1

        # If we want to simulate carve-outs, we need to downgrade TWZ tax haven profits by the average reduction due to
        # carve-outs that is observed for tax haven profits in the OECD data
        for column_name in ['Profits in all tax havens', 'Profits in all tax havens (positive only)']:
            twz[column_name] *= 10**6

            if self.carve_outs:
                twz[column_name] *= (1 - self.avg_carve_out_impact_tax_haven)

            elif self.behavioral_responses and self.behavioral_responses_include_TWZ:

                if self.behavioral_responses_method == 'linear_elasticity':
                    twz[column_name] *= (
                        1 - self.behavioral_responses_TH_elasticity * max(
                            15 - self.assumed_haven_ETR_TWZ * 100, 0
                        )
                    )

                else:
                    multiplier = 1 if self.assumed_haven_ETR_TWZ >= 0.15 else np.exp(
                        self.behavioral_responses_beta_1 * 0.15
                        + self.behavioral_responses_beta_2 * 0.15**2
                        + self.behavioral_responses_beta_3 * 0.15**3
                        - self.behavioral_responses_beta_1 * self.assumed_haven_ETR_TWZ
                        - self.behavioral_responses_beta_2 * self.assumed_haven_ETR_TWZ**2
                        - self.behavioral_responses_beta_3 * self.assumed_haven_ETR_TWZ**3
                    )

                    twz[column_name] *= multiplier

            else:
                continue

        # We filter out countries with 0 profits in tax havens
        twz = twz[twz['Profits in all tax havens (positive only)'] > 0].copy()

        # --- Cleaning the TWZ domestic profits data

        # Resulting figures are expressed in 2016 USD
        twz_domestic['Domestic profits'] *= 10**9

        if self.carve_outs:
            # If we want to simulate carve-outs, we need to downgrade TWZ domestic profits by the average reduction due
            # to carve-outs that is observed for domestic profits in the OECD data
            twz_domestic['Domestic profits'] *= (1 - self.avg_carve_out_impact_domestic)

        if self.behavioral_responses and self.behavioral_responses_include_domestic:
            if self.behavioral_responses_method == 'linear_elasticity':
                elasticities = (
                    # If the parent jurisdiction is a tax haven
                    twz_domestic['Alpha-3 country code'].isin(
                        self.tax_haven_country_codes
                    ) * self.behavioral_responses_TH_elasticity

                    # If the parent jurisdiction is not a tax haven
                    + ~twz_domestic['Alpha-3 country code'].isin(
                        self.tax_haven_country_codes
                    ) * self.behavioral_responses_non_TH_elasticity
                )

                unshifting_rates = elasticities * twz_domestic['Domestic ETR'].map(lambda x: max(15 - x * 100, 0))

            else:
                multiplier = (twz_domestic['Domestic ETR'] < 0.15) * 1

                # We apply the formula obtained in "behavioral_responses.pdf"
                unshifting_rates = (
                    1 - np.exp(
                        self.behavioral_responses_beta_1 * 0.15
                        + self.behavioral_responses_beta_2 * 0.15**2
                        + self.behavioral_responses_beta_3 * 0.15**3
                        - self.behavioral_responses_beta_1 * twz_domestic['Domestic ETR']
                        - self.behavioral_responses_beta_2 * twz_domestic['Domestic ETR']**2
                        - self.behavioral_responses_beta_3 * twz_domestic['Domestic ETR']**3
                    )
                ) * multiplier

            unshifted_profits = twz_domestic['Domestic profits'] * unshifting_rates
            self.unshifted_profits = unshifted_profits.copy()
            self.unshifting_rates = unshifting_rates.copy()
            twz_domestic['Domestic profits'] -= unshifted_profits

        # --- Cleaning the TWZ CIT revenue data

        # Reformatting the CIT revenue column - Resulting figures are expressed in 2016 USD
        twz_CIT['CIT revenue'] = twz_CIT['CIT revenue'] * 10**9

        if inplace:
            self.oecd = oecd.copy()
            self.twz = twz.copy()
            self.twz_domestic = twz_domestic.copy()
            self.twz_CIT = twz_CIT.copy()
            self.mean_wages = preprocessed_mean_wages.copy()

        else:

            if self.carve_outs:
                return oecd.copy(), twz.copy(), twz_domestic.copy(), twz_CIT.copy(), preprocessed_mean_wages.copy()

            else:
                return oecd.copy(), twz.copy(), twz_domestic.copy(), twz_CIT.copy()

    def get_non_haven_imputation_ratio(self, minimum_ETR, selection):
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

        # The selection argument can only take a few values
        if selection not in ['EU', 'non-US']:
            raise Exception(
                'When computing the non-haven tax deficit imputation ratio for TWZ countries, the "selection" argument '
                + 'can only take two values: either "EU" if we focus on EU-27 parent countries or "non-US" if we accept'
                + ' any non-US parent countries. In both cases, tax havens and countries without a sufficient bilateral'
                + ' breakdown are excluded.'
            )

        if self.behavioral_responses:

            calculator_temp = TaxDeficitCalculator(
                year=self.year,
                alternative_imputation=self.alternative_imputation,
                non_haven_TD_imputation_selection=self.non_haven_TD_imputation_selection,
                sweden_treatment=self.sweden_treatment,
                belgium_treatment=self.belgium_treatment,
                SGP_CYM_treatment=self.SGP_CYM_treatment,
                use_adjusted_profits=self.use_adjusted_profits,
                average_ETRs=self.average_ETRs_bool,
                carve_outs=self.carve_outs,
                carve_out_rate_assets=self.carve_out_rate_assets,
                carve_out_rate_payroll=self.carve_out_rate_payroll,
                depreciation_only=self.depreciation_only,
                exclude_inventories=self.exclude_inventories,
                payroll_premium=self.payroll_premium,
                ex_post_ETRs=self.ex_post_ETRs,
                add_AUT_AUT_row=self.add_AUT_AUT_row,
                de_minimis_exclusion=self.de_minimis_exclusion,
                extended_dividends_adjustment=self.extended_dividends_adjustment,
                fetch_data_online=self.fetch_data_online,
                behavioral_responses=False,
            )

            calculator_temp.load_clean_data()

        # With a minimum ETR of 10%, the formula cannot be applied (division by 0), hence this case disjunction
        if minimum_ETR > 0.1:
            if self.behavioral_responses:
                oecd = calculator_temp.oecd.copy()
            else:
                oecd = self.oecd.copy()

            # In the computation of the imputation ratio, we only focus on:
            # - EU-27 parent countries or non-US parent countries depending on what is chosen
            if selection == 'EU':
                mask_selection = oecd['Parent jurisdiction (alpha-3 code)'].isin(self.eu_27_country_codes)
            else:
                mask_selection = (oecd['Parent jurisdiction (alpha-3 code)'] != 'USA')
            # - That are not tax havens
            mask_non_haven = ~oecd['Parent jurisdiction (alpha-3 code)'].isin(self.tax_haven_country_codes)
            # - And report a detailed country by country breakdown in their CbCR
            mask_minimum_reporting_countries = ~oecd['Parent jurisdiction (alpha-3 code)'].isin(
                COUNTRIES_WITH_MINIMUM_REPORTING + self.COUNTRIES_WITH_CONTINENTAL_REPORTING
            )

            # We combine the boolean indexing masks
            mask = np.logical_and(mask_selection, mask_non_haven)
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

        if self.behavioral_responses:

            calculator_temp = TaxDeficitCalculator(
                year=self.year,
                alternative_imputation=self.alternative_imputation,
                non_haven_TD_imputation_selection=self.non_haven_TD_imputation_selection,
                sweden_treatment=self.sweden_treatment,
                belgium_treatment=self.belgium_treatment,
                SGP_CYM_treatment=self.SGP_CYM_treatment,
                use_adjusted_profits=self.use_adjusted_profits,
                average_ETRs=self.average_ETRs_bool,
                carve_outs=self.carve_outs,
                carve_out_rate_assets=self.carve_out_rate_assets,
                carve_out_rate_payroll=self.carve_out_rate_payroll,
                depreciation_only=self.depreciation_only,
                exclude_inventories=self.exclude_inventories,
                payroll_premium=self.payroll_premium,
                ex_post_ETRs=self.ex_post_ETRs,
                add_AUT_AUT_row=self.add_AUT_AUT_row,
                de_minimis_exclusion=self.de_minimis_exclusion,
                extended_dividends_adjustment=self.extended_dividends_adjustment,
                fetch_data_online=self.fetch_data_online,
                behavioral_responses=False,
            )

            calculator_temp.load_clean_data()

        # This method is only useful if the previous one yields a ratio of 0, i.e. if the minimum ETR is of 20% or less
        if minimum_ETR > 0.2:
            raise Exception('These computations are only used when the minimum ETR considered is 0.2 or less.')

        # We use the get_stratified_oecd_data to compute the non-haven tax deficit of OECD-reporting countries
        if self.behavioral_responses:
            oecd_stratified = calculator_temp.get_stratified_oecd_data(
                minimum_ETR=self.reference_rate_for_alternative_imputation
            )

        else:
            oecd_stratified = self.get_stratified_oecd_data(
                minimum_ETR=self.reference_rate_for_alternative_imputation
            )

        # We exclude countries whose CbCR breakdown does not allow to distinguish tax-haven and non-haven profits
        df_restricted = oecd_stratified[
            ~oecd_stratified['Parent jurisdiction (alpha-3 code)'].isin(
                self.COUNTRIES_WITH_CONTINENTAL_REPORTING + COUNTRIES_WITH_MINIMUM_REPORTING
            )
        ].copy()

        # The denominator is the total non-haven tax deficit of relevant countries at the reference minimum ETR
        denominator = df_restricted['tax_deficit_x_non_haven'].sum()

        # We follow the same process, running computations at the minimum ETR this time
        if self.behavioral_responses:
            oecd_stratified = calculator_temp.get_stratified_oecd_data(
                minimum_ETR=minimum_ETR
            )

        else:
            oecd_stratified = self.get_stratified_oecd_data(
                minimum_ETR=minimum_ETR
            )

        # We exclude countries whose CbCR breakdown does not allow to distinguish tax-haven and non-haven profits
        df_restricted = oecd_stratified[
            ~oecd_stratified['Parent jurisdiction (alpha-3 code)'].isin(
                self.COUNTRIES_WITH_CONTINENTAL_REPORTING + COUNTRIES_WITH_MINIMUM_REPORTING
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

        # We only consider profits taxed at an effective tax rate above the minimum ETR
        oecd = oecd[oecd['ETR'] < minimum_ETR].copy()

        # We compute the ETR differential for all low-taxed profits
        oecd['ETR_differential'] = oecd['ETR'].map(lambda x: minimum_ETR - x)

        # And deduce the tax deficit generated by each Parent / Partner jurisdiction pair
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

        # As a last step, since we now (Feb. 2022) assume that non-EU countries do not collect their domestic tax defi-
        # cit, we bring the "tax_deficit_x_domestic" down to 0 for non-EU countries and recompute the total tax deficit
        oecd_stratified['IS_EU'] = oecd_stratified[
            'Parent jurisdiction (alpha-3 code)'
        ].isin(self.eu_27_country_codes) * 1
        oecd_stratified['tax_deficit_x_domestic'] *= oecd_stratified['IS_EU']

        oecd_stratified['tax_deficit'] = oecd_stratified[
            ['tax_deficit_x_domestic', 'tax_deficit_x_tax_haven', 'tax_deficit_x_non_haven']
        ].sum(
            axis=1
        )

        oecd_stratified = oecd_stratified.drop(columns=['IS_EU'])

        return oecd_stratified.copy()

    def compute_all_tax_deficits(
        self,
        minimum_ETR=0.25,
        CbCR_reporting_countries_only=False,
        save_countries_replaced=True
    ):
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
        # NB: recall that we do not consider the Swedish CbCR if "exclude" was chosen
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

        if save_countries_replaced:
            self.countries_replaced = []

        if self.carve_outs:

            calculator = TaxDeficitCalculator(
                year=self.year,
                add_AUT_AUT_row=True,
                average_ETRs=self.average_ETRs_bool,
                fetch_data_online=self.fetch_data_online
            )
            calculator.load_clean_data()
            _ = calculator.compute_all_tax_deficits(minimum_ETR=minimum_ETR)

            countries_replaced = calculator.countries_replaced.copy()

            merged_df['tax_deficit_x_tax_haven_merged'] = merged_df.apply(
                lambda row: self.combine_haven_tax_deficits(
                    row,
                    carve_outs=self.carve_outs,
                    countries_replaced=countries_replaced,
                    save_countries_replaced=save_countries_replaced
                ),
                axis=1
            )

        else:
            merged_df['tax_deficit_x_tax_haven_merged'] = merged_df.apply(
                lambda row: self.combine_haven_tax_deficits(
                    row,
                    carve_outs=self.carve_outs,
                    save_countries_replaced=save_countries_replaced
                ),
                axis=1
            )

        # self.countries_replaced = merged_df[
        #     merged_df['tax_deficit_x_tax_haven_merged'] > merged_df['tax_deficit_x_tax_haven']
        # ]['Parent jurisdiction (alpha-3 code)'].unique()

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
        # NB: recall that we do not consider the Swedish CbCR if "exclude" was chosen
        twz_not_in_oecd = twz[~twz['Is parent in OECD data?'].astype(bool)].copy()

        twz_not_in_oecd.drop(
            columns=['Profits in all tax havens', 'Profits in all tax havens (positive only)'],
            inplace=True
        )

        # - Extrapolating the foreign non-haven tax deficit

        # We compute the imputation ratio with the method defined above
        imputation_ratio_non_haven = self.get_non_haven_imputation_ratio(
            minimum_ETR=minimum_ETR, selection=self.non_haven_TD_imputation_selection
        )

        # And we deduce the non-haven tax deficit of countries that are only found in TWZ data
        twz_not_in_oecd['tax_deficit_x_non_haven'] = \
            twz_not_in_oecd['tax_deficit_x_tax_haven_TWZ'] * imputation_ratio_non_haven

        # - Computing the domestic tax deficit

        # For countries that are only in TWZ data, we still need to compute their domestic tax deficit
        twz_domestic = self.twz_domestic.copy()

        # However, we assume that non-EU countries do not collect their domestic tax deficit
        # We therefore restrict the table of TWZ domestic profits and ETRs to EU countries
        twz_domestic = twz_domestic[twz_domestic['Alpha-3 country code'].isin(self.eu_27_country_codes)].copy()

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

        if self.sweden_exclude and self.belgium_treatment == 'exclude':
            # We exclude Sweden and Belgium from the OECD-drawn results, as we do not consider their CbCR
            merged_df = merged_df[~merged_df['Parent jurisdiction (alpha-3 code)'].isin(['SWE', 'BEL'])].copy()

        elif self.sweden_exclude and self.belgium_treatment != 'exclude':
            # We exclude Sweden from the OECD-drawn results, as we do not consider its CbCR
            merged_df = merged_df[merged_df['Parent jurisdiction (alpha-3 code)'] != 'SWE'].copy()

        elif not self.sweden_exclude and self.belgium_treatment == 'exclude':
            # We exclude Belgium from the OECD-drawn results, as we do not consider its CbCR
            merged_df = merged_df[merged_df['Parent jurisdiction (alpha-3 code)'] != 'BEL'].copy()

        else:
            pass

        # We eventually concatenate the two DataFrames
        merged_df = pd.concat(
            [merged_df, twz_not_in_oecd],
            axis=0
        )

        # --- Extrapolations to 2021 EUR

        # We convert 2016 USD results in 2016 EUR and extrapolate them to 2021 EUR
        for column_name in merged_df.columns[2:]:
            merged_df[column_name] = merged_df[column_name] * self.USD_to_EUR * self.multiplier_2021

        # --- Managing the case where the minimum ETR is 20% or below for TWZ countries

        # As mentioned above and detailed in Appendix A, the imputation of the non-haven tax deficit of TWZ countries
        # follows a specific process whenever the chosen minimum ETR is of or below 20%
        if minimum_ETR <= 0.2 and self.alternative_imputation:
            # We get the new multiplying factor from the method defined above
            multiplying_factor = self.get_alternative_non_haven_factor(minimum_ETR=minimum_ETR)

            # We compute all tax deficits at the reference rate (25% in the report)
            df = self.compute_all_tax_deficits(
                minimum_ETR=self.reference_rate_for_alternative_imputation,
                save_countries_replaced=False
            )

            # What is the set of countries not concerned by this alternative imputation?
            if self.sweden_exclude and self.belgium_treatment == 'exclude':
                set_of_countries = self.oecd[
                    ~self.oecd['Parent jurisdiction (alpha-3 code)'].isin(['SWE', 'BEL'])
                ]['Parent jurisdiction (alpha-3 code)'].unique()

            elif self.sweden_exclude and self.belgium_treatment != 'exclude':
                set_of_countries = self.oecd[
                    self.oecd['Parent jurisdiction (alpha-3 code)'] != 'SWE'
                ]['Parent jurisdiction (alpha-3 code)'].unique()

            elif not self.sweden_exclude and self.belgium_treatment == 'exclude':
                set_of_countries = self.oecd[
                    self.oecd['Parent jurisdiction (alpha-3 code)'] != 'BEL'
                ]['Parent jurisdiction (alpha-3 code)'].unique()

            else:
                set_of_countries = self.oecd['Parent jurisdiction (alpha-3 code)'].unique()

            df = df[
                ~df['Parent jurisdiction (alpha-3 code)'].isin(set_of_countries)
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

        if CbCR_reporting_countries_only:
            merged_df = merged_df[
                merged_df['Parent jurisdiction (whitespaces cleaned)'].isin(
                    self.oecd['Parent jurisdiction (whitespaces cleaned)'].unique()
                )
            ].copy()

        return merged_df.reset_index(drop=True).copy()

    def combine_haven_tax_deficits(
        self,
        row,
        save_countries_replaced,
        carve_outs=False,
        countries_replaced=None,
    ):
        """
        This function is used to compute the tax deficit of all in-sample headquarter countries in the multilateral im-
        plementation scenario.

        For parent countries that are in both the OECD and TWZ data, we have two different sources to compute their tax-
        haven-based tax deficit and we retain the highest of these two amounts.

        Besides, for parent countries in the OECD data that do not report a fully detailed country-by-country breakdown
        of the activity of their multinationals, we cannot distinguish their tax-haven and non-haven tax deficits. Quite
        arbitrarily in the Python code, we attribute everything to the non-haven tax deficit. In the Table A1 of the re-
        port, these specific cases are described with the "Only foreign aggregate data" column.
        """
        if carve_outs and countries_replaced is None:
            raise Exception(
                'Using this function under carve-outs requires to indicate a list of countries to replace.'
            )

        if row['Parent jurisdiction (alpha-3 code)'] not in (
            COUNTRIES_WITH_MINIMUM_REPORTING + self.COUNTRIES_WITH_CONTINENTAL_REPORTING
        ):
            if countries_replaced is None:

                if row['tax_deficit_x_tax_haven_TWZ'] > row['tax_deficit_x_tax_haven']:
                    if save_countries_replaced:
                        self.countries_replaced.append(row['Parent jurisdiction (alpha-3 code)'])
                    return row['tax_deficit_x_tax_haven_TWZ']

                else:
                    return row['tax_deficit_x_tax_haven']

            else:
                if (
                    row['tax_deficit_x_tax_haven_TWZ'] > row['tax_deficit_x_tax_haven']
                    and row['Parent jurisdiction (alpha-3 code)'] in countries_replaced
                ):
                    if save_countries_replaced:
                        self.countries_replaced.append(row['Parent jurisdiction (alpha-3 code)'])
                    return row['tax_deficit_x_tax_haven_TWZ']

                else:
                    return row['tax_deficit_x_tax_haven']

        else:
            return 0

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
        total_eu = (
            df['Parent jurisdiction (alpha-3 code)'].isin(self.eu_27_country_codes) * 1 * df['tax_deficit']
        ).sum()
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
        merged_df['tax_deficit_15'] /= (merged_df['CIT revenue'] * self.multiplier_2021 * self.USD_to_EUR / 100)

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
                merged_df['CIT revenue'] * self.multiplier_2021 * self.USD_to_EUR / 100
            )

        # We want to also verify the EU-27 average and restrict the DataFrame to these countries
        eu_df = merged_df[merged_df['Parent jurisdiction (alpha-3 code)'].isin(self.eu_27_country_codes)].copy()

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
            df['Parent jurisdiction (alpha-3 code)'].isin(self.eu_27_country_codes),
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
            df['Parent jurisdiction (alpha-3 code)'].isin(self.eu_27_country_codes)
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
        ][f'Collectible tax deficit for {taxing_country}'].sum() * self.unilateral_scenario_non_US_imputation_ratio

        # Except for Germany, for which we add back only half of the tax deficit collected from non-US foreign countries
        if taxing_country_code == 'DEU':
            imputation /= self.unilateral_scenario_correction_for_DEU

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

            if country in df['Parent jurisdiction (whitespaces cleaned)'].unique():
                # We fetch the tax deficit that could be collected from the country's own multinationals
                output['Own tax deficit'].append(
                    df[df['Parent jurisdiction (whitespaces cleaned)'] == country][column_name].iloc[0]
                )

            else:
                output['Own tax deficit'].append(0)

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
                self.eu_27_country_codes
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
        for eu_country in self.eu_27_country_codes:

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
            additional_revenue_gains[eu_country] = (
                td_df['Collectible tax deficit'].sum() * self.intermediary_scenario_imputation_ratio
            )

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
                if country in ['USA', 'IMN']:
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

            if aggregate == 'Other Europe':
                self.intermediary_scenario_temp = td_df.copy()

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

    def assess_carve_out_impact(self, minimum_ETR=0.25):
        """
        This function takes as input a minimum effective tax rate (which defaults to 25%) and outputs a DataFrame
        showing, for each in-sample country (EU and/or CbCR-reporting countries):

        - the tax deficit that it could collect by imposing this minimum ETR on the profits of its multinationals;
        - the split between domestic, tax haven and non-haven tax deficits;
        - and the same amounts with carve-outs being applied.

        Carve-outs are applied with the parameters (carve-out rates, use of the full value of tangible assets or of de-
        preciation expenses only and exclusion of inventories or not) that are defined when instantiating the TaxDefi-
        citCalculator object.
        """

        # If carve-out parameters have not been indicated, we cannot run the computations
        if (
            self.carve_out_rate_assets is None or self.carve_out_rate_payroll is None
            or self.depreciation_only is None or self.exclude_inventories is None
            or self.ex_post_ETRs is None
        ):
            raise Exception(
                'If you want to simulate substance-based carve-outs, you need to indicate all the parameters.'
            )

        # We instantiate a TaxDeficitCalculator object with carve-outs
        calculator = TaxDeficitCalculator(
            year=self.year,
            sweden_treatment=self.sweden_treatment,
            belgium_treatment=self.belgium_treatment,
            use_adjusted_profits=self.use_adjusted_profits,
            average_ETRs=self.average_ETRs_bool,
            carve_outs=True,
            carve_out_rate_assets=self.carve_out_rate_assets,
            carve_out_rate_payroll=self.carve_out_rate_payroll,
            depreciation_only=self.depreciation_only,
            exclude_inventories=self.exclude_inventories,
            ex_post_ETRs=self.ex_post_ETRs,
            add_AUT_AUT_row=self.add_AUT_AUT_row,
            extended_dividends_adjustment=self.extended_dividends_adjustment,
            fetch_data_online=self.fetch_data_online
        )

        # We load the data
        calculator.load_clean_data()

        # And deduce total tax deficits and their split, with carve-outs being applied
        carve_outs = calculator.compute_all_tax_deficits(
            CbCR_reporting_countries_only=False,
            minimum_ETR=minimum_ETR
        )

        # We instantiate a TaxDeficitCalculator object without carve-outs
        calculator_no_carve_out = TaxDeficitCalculator(
            year=self.year,
            sweden_treatment=self.sweden_treatment,
            belgium_treatment=self.belgium_treatment,
            use_adjusted_profits=self.use_adjusted_profits,
            average_ETRs=self.average_ETRs_bool,
            carve_outs=False,
            add_AUT_AUT_row=self.add_AUT_AUT_row,
            extended_dividends_adjustment=self.extended_dividends_adjustment,
            fetch_data_online=self.fetch_data_online
        )

        # We load the data
        calculator_no_carve_out.load_clean_data()

        # And deduce total tax deficits and their split, without any carve-out being applied
        no_carve_outs = calculator_no_carve_out.compute_all_tax_deficits(
            CbCR_reporting_countries_only=False,
            minimum_ETR=minimum_ETR
        )

        # We merge the two DataFrames
        carve_outs_impact = carve_outs.merge(
            no_carve_outs,
            how='inner',
            on=[
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)'
            ]
        ).rename(
            columns={
                'tax_deficit_x': 'TD_with_carve_outs',
                'tax_deficit_y': 'TD_no_carve_outs',
                'tax_deficit_x_domestic_x': 'domestic_TD_with_carve_outs',
                'tax_deficit_x_domestic_y': 'domestic_TD_no_carve_outs',
                'tax_deficit_x_non_haven_x': 'non_haven_TD_with_carve_outs',
                'tax_deficit_x_non_haven_y': 'non_haven_TD_no_carve_outs',
                'tax_deficit_x_tax_haven_x': 'tax_haven_TD_with_carve_outs',
                'tax_deficit_x_tax_haven_y': 'tax_haven_TD_no_carve_outs'
            }
        )

        # We only show EU and/or CbCR-reporting countries
        cbcr_reporting_countries = list(self.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        mask_eu = carve_outs_impact['Parent jurisdiction (alpha-3 code)'].isin(self.eu_27_country_codes)
        mask_cbcr = carve_outs_impact['Parent jurisdiction (alpha-3 code)'].isin(cbcr_reporting_countries)

        # This condition is encapsulated in this boolean indexing mask
        mask = np.logical_or(mask_eu, mask_cbcr)

        # We add two useful indicator variables
        carve_outs_impact['IS_EU'] = mask_eu * 1
        carve_outs_impact['REPORTS_CbCR'] = mask_cbcr * 1

        # And restrict the DataFrame to relevant countries
        restricted_df = carve_outs_impact[mask].copy()

        # We finalise the formatting of the table
        restricted_df.sort_values(
            by=['IS_EU', 'Parent jurisdiction (alpha-3 code)'],
            ascending=[False, True],
            inplace=True
        )

        columns = [
            'Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)',
            'TD_with_carve_outs', 'TD_no_carve_outs', 'domestic_TD_with_carve_outs', 'domestic_TD_no_carve_outs',
            'non_haven_TD_with_carve_outs', 'non_haven_TD_no_carve_outs', 'tax_haven_TD_with_carve_outs',
            'tax_haven_TD_no_carve_outs', 'IS_EU', 'REPORTS_CbCR'
        ]

        return restricted_df[columns].copy()

    def assess_carve_out_impact_formatted(self, minimum_ETR=0.25):
        """
        This method is used in the "app.py" file, which underlies the Streamlit simulator. It is used to produce the
        table on the "Substance-based carve-outs" page. It takes as input the selected minimum ETR and widely relies on
        the assess_carve_out_impact method defined above. It mostly consists in a series of formatting steps.
        """
        df = self.assess_carve_out_impact(minimum_ETR=minimum_ETR)

        df.sort_values(
            by='Parent jurisdiction (whitespaces cleaned)',
            inplace=True
        )

        mask_eu = df['Parent jurisdiction (alpha-3 code)'].isin(self.eu_27_country_codes)

        df = df[['Parent jurisdiction (whitespaces cleaned)', 'TD_no_carve_outs', 'TD_with_carve_outs']].copy()

        dict_df = df.to_dict()

        dict_df[df.columns[0]][len(df) + 1] = 'Total - EU27'
        dict_df[df.columns[1]][len(df) + 1] = df[mask_eu]['TD_no_carve_outs'].sum()
        dict_df[df.columns[2]][len(df) + 1] = df[mask_eu]['TD_with_carve_outs'].sum()

        dict_df[df.columns[0]][len(df) + 2] = 'Total - Whole sample'
        dict_df[df.columns[1]][len(df) + 2] = df['TD_no_carve_outs'].sum()
        dict_df[df.columns[2]][len(df) + 2] = df['TD_with_carve_outs'].sum()

        df = pd.DataFrame.from_dict(dict_df)

        df['Change in % of revenue gains without carve-outs'] = (
            (df['TD_with_carve_outs'] - df['TD_no_carve_outs']) / df['TD_no_carve_outs']
        ) * 100

        df.rename(
            columns={
                'TD_no_carve_outs': 'Collectible tax deficit without carve-outs (€m)',
                'TD_with_carve_outs': 'Collectible tax deficit with carve-outs (€m)'
            },
            inplace=True
        )

        for column_name in df.columns[1:-1]:
            df[column_name] /= 10**6
            df[column_name] = df[column_name].map('{:,.0f}'.format)

        df[df.columns[-1]] = df[df.columns[-1]].map('{:.1f}'.format)

        return df.copy()

    def get_carve_outs_table(
        self,
        TWZ_countries_methodology,
        depreciation_only, exclude_inventories,
        carve_out_rate_assets=0.05,
        carve_out_rate_payroll=0.05
    ):
        """
        This function takes as input:

        - the methodology to use to estimate the post-carve-out revenue gains of TWZ countries;

        - a boolean, "depreciation_only", indicating whether to restrict the tangible assets component of substance-
        based carve-outs to a share of depreciation expenses;

        - a boolean, "exlude_inventories", indicating whether to exlude inventories from tangible assets or not;

        - the carve-out rates to use (which both default to 5%).

        It returns a DataFrame that shows, for the 15% and 25% minimum rates and for each in-sample country, the estima-
        ted revenue gains from a global minimum tax without and with carve-outs being applied.
        """

        # We need to have previously loaded and cleaned the OECD data
        if self.oecd is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        # The "TWZ_countries_methodology" argument can only take a few string values
        if TWZ_countries_methodology not in ['initial', 'new']:
            raise Exception('The "TWZ_countries_methodology" argument only accepts two values: "initial" or "new".')

        # Computing tax deficits without substance-based carve-outs
        calculator = TaxDeficitCalculator(fetch_data_online=self.fetch_data_online)

        calculator.load_clean_data()

        td_25 = calculator.get_total_tax_deficits(minimum_ETR=0.25).iloc[:-2, :]
        td_15 = calculator.get_total_tax_deficits(minimum_ETR=0.15).iloc[:-2, :]

        # We merge the resulting DataFrames for the 15% and 25% minimum rates
        merged_df = td_25.merge(
            td_15[['Parent jurisdiction (alpha-3 code)', 'tax_deficit']],
            how='left',
            on='Parent jurisdiction (alpha-3 code)'
        )

        merged_df['tax_deficit_y'] = merged_df['tax_deficit_y'].fillna(0)

        merged_df.rename(
            columns={
                'tax_deficit_x': 'tax_deficit_25_no_carve_out',
                'tax_deficit_y': 'tax_deficit_15_no_carve_out'
            },
            inplace=True
        )

        # Computing corresponding tax deficits with substance-based carve-outs
        calculator = TaxDeficitCalculator(
            carve_outs=True,
            carve_out_rate_assets=carve_out_rate_assets, carve_out_rate_payroll=carve_out_rate_payroll,
            depreciation_only=depreciation_only,
            exclude_inventories=exclude_inventories,
            fetch_data_online=self.fetch_data_online
        )

        calculator.load_clean_data()

        td_25 = calculator.get_total_tax_deficits(minimum_ETR=0.25).iloc[:-2]
        td_15 = calculator.get_total_tax_deficits(minimum_ETR=0.15).iloc[:-2]

        # We merge the DataFrame obtained for the 25% minimum rate
        merged_df = merged_df.merge(
            td_25[['Parent jurisdiction (alpha-3 code)', 'tax_deficit']],
            how='left',
            on='Parent jurisdiction (alpha-3 code)'
        )

        merged_df.rename(
            columns={
                'tax_deficit': 'tax_deficit_25_with_carve_out'
            },
            inplace=True
        )

        # We merge the DataFrame obtained for the 15% minimum rate
        merged_df = merged_df.merge(
            td_15[['Parent jurisdiction (alpha-3 code)', 'tax_deficit']],
            how='left',
            on='Parent jurisdiction (alpha-3 code)'
        )

        merged_df['tax_deficit'] = merged_df['tax_deficit'].fillna(0)

        merged_df.rename(
            columns={
                'tax_deficit': 'tax_deficit_15_with_carve_out'
            },
            inplace=True
        )

        # We only show EU and/or CbCR-reporting countries
        cbcr_reporting_countries = list(self.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        mask_eu = merged_df['Parent jurisdiction (alpha-3 code)'].isin(self.eu_27_country_codes)
        mask_cbcr = merged_df['Parent jurisdiction (alpha-3 code)'].isin(cbcr_reporting_countries)

        # This condition is encapsulated in this boolean indexing mask
        mask = np.logical_or(mask_eu, mask_cbcr)

        # We add two useful indicator variables
        merged_df['IS_EU'] = mask_eu * 1
        merged_df['REPORTS_CbCR'] = mask_cbcr * 1

        # And we restrict the DataFrame to relevant countries
        restricted_df = merged_df[mask].copy()

        # We finalise the reformatting of the DataFrame
        restricted_df.sort_values(
            by=['IS_EU', 'Parent jurisdiction (alpha-3 code)'],
            ascending=[False, True],
            inplace=True
        )

        if TWZ_countries_methodology == 'initial':
            # If we have opted for the "initial" methodology for TWZ countries, we can simply return the DataFrame as is
            return restricted_df.copy()

        else:
            # If we have chosen the "new" methodology, we have a bit more work!

            # We create a temporary copy of the DataFrame, restricted to CbCR-reporting countries
            temp = restricted_df[restricted_df['REPORTS_CbCR'] == 1].copy()

            if self.sweden_exclude and self.belgium_treatment == 'exclude':
                temp = temp[~temp['Parent jurisdiction (alpha-3 code)'].isin(['SWE', 'BEL'])].copy()

            elif self.sweden_exclude and self.belgium_treatment != 'exclude':
                temp = temp[temp['Parent jurisdiction (alpha-3 code)'] != 'SWE'].copy()

            elif not self.sweden_exclude and self.belgium_treatment == 'exclude':
                temp = temp[temp['Parent jurisdiction (alpha-3 code)'] != 'BEL'].copy()

            else:
                pass

            # We deduce the average reduction factors to apply to the collectible tax deficits of TWZ countries
            self.imputation_15 = temp['tax_deficit_15_with_carve_out'].sum() / temp['tax_deficit_15_no_carve_out'].sum()
            self.imputation_25 = temp['tax_deficit_25_with_carve_out'].sum() / temp['tax_deficit_25_no_carve_out'].sum()

            if self.sweden_exclude and self.belgium_treatment == 'exclude':
                restricted_df['REPORTS_CbCR'] = restricted_df.apply(
                    (
                        lambda row: 0 if row['Parent jurisdiction (alpha-3 code)'] in ['SWE', 'BEL']
                        else row['REPORTS_CbCR']
                    ),
                    axis=1
                )

            elif self.sweden_exclude and self.belgium_treatment != 'exclude':
                restricted_df['REPORTS_CbCR'] = restricted_df.apply(
                    lambda row: 0 if row['Parent jurisdiction (alpha-3 code)'] == 'SWE' else row['REPORTS_CbCR'],
                    axis=1
                )

            elif not self.sweden_exclude and self.belgium_treatment == 'exclude':
                restricted_df['REPORTS_CbCR'] = restricted_df.apply(
                    lambda row: 0 if row['Parent jurisdiction (alpha-3 code)'] == 'BEL' else row['REPORTS_CbCR'],
                    axis=1
                )

            else:
                pass

            # We apply the two downgrade factors to tax deficits without carve-outs
            restricted_df['tax_deficit_15_with_carve_out'] = restricted_df.apply(
                (
                    lambda row: row['tax_deficit_15_no_carve_out'] * self.imputation_15
                    if row['REPORTS_CbCR'] == 0 else row['tax_deficit_15_with_carve_out']
                ),
                axis=1
            )

            restricted_df['tax_deficit_25_with_carve_out'] = restricted_df.apply(
                (
                    lambda row: row['tax_deficit_25_no_carve_out'] * self.imputation_25
                    if row['REPORTS_CbCR'] == 0 else row['tax_deficit_25_with_carve_out']
                ),
                axis=1
            )

            # And we return the adjusted DataFrame
            return restricted_df.copy()

    def get_carve_outs_table_2(
        self,
        exclude_inventories, depreciation_only,
        carve_out_rate_assets=0.05,
        carve_out_rate_payroll=0.05,
        output_Excel=False
    ):
        """
        This function takes as input:

        - a boolean, "depreciation_only", indicating whether to restrict the tangible assets component of substance-
        based carve-outs to a share of depreciation expenses;

        - a boolean, "exlude_inventories", indicating whether to exlude inventories from tangible assets or not;

        - the carve-out rates to use (which both default to 5%).

        It returns a DataFrame that shows, for the different minimum effective tax rates and for each in-sample country,
        the estimated impact of substance-based carve-outs. The change is expressed as a percentage of revenue gain es-
        timates without substance-based carve-outs.
        """

        # The "get_carve_outs_table" method provides the required information for two minimum ETRs, 15% and 25%
        # This will serve as a central DataFrame to which we will add the 21% and 30% columns
        df = self.get_carve_outs_table(
            TWZ_countries_methodology='initial',
            exclude_inventories=exclude_inventories, depreciation_only=depreciation_only,
            carve_out_rate_assets=carve_out_rate_assets,
            carve_out_rate_payroll=carve_out_rate_payroll
        )

        # Computing tax deficits without substance-based carve-outs
        calculator = TaxDeficitCalculator(fetch_data_online=self.fetch_data_online)

        calculator.load_clean_data()

        td_21 = calculator.get_total_tax_deficits(minimum_ETR=0.21).iloc[:-2, :]
        td_30 = calculator.get_total_tax_deficits(minimum_ETR=0.3).iloc[:-2, :]

        # We add the 21% tax deficit to the central DataFrame
        merged_df = df.merge(
            td_21[['Parent jurisdiction (alpha-3 code)', 'tax_deficit']],
            how='left',
            on='Parent jurisdiction (alpha-3 code)'
        )

        merged_df['tax_deficit'] = merged_df['tax_deficit'].fillna(0)

        # We add the 30% tax deficit to the central DataFrame
        merged_df = merged_df.merge(
            td_30[['Parent jurisdiction (alpha-3 code)', 'tax_deficit']],
            how='left',
            on='Parent jurisdiction (alpha-3 code)'
        )

        merged_df['tax_deficit_y'] = merged_df['tax_deficit_y'].fillna(0)

        merged_df.rename(
            columns={
                'tax_deficit_x': 'tax_deficit_21_no_carve_out',
                'tax_deficit_y': 'tax_deficit_30_no_carve_out'
            },
            inplace=True
        )

        # Computing corresponding tax deficits with substance-based carve-outs
        calculator = TaxDeficitCalculator(
            carve_outs=True,
            carve_out_rate_assets=carve_out_rate_assets,
            carve_out_rate_payroll=carve_out_rate_payroll,
            depreciation_only=depreciation_only,
            exclude_inventories=exclude_inventories,
            fetch_data_online=self.fetch_data_online
        )

        calculator.load_clean_data()

        td_21 = calculator.get_total_tax_deficits(minimum_ETR=0.21).iloc[:-2]
        td_30 = calculator.get_total_tax_deficits(minimum_ETR=0.3).iloc[:-2]

        # We add the 21% tax deficit with carve-outs to the central DataFrame
        merged_df = merged_df.merge(
            td_21[['Parent jurisdiction (alpha-3 code)', 'tax_deficit']],
            how='left',
            on='Parent jurisdiction (alpha-3 code)'
        )

        merged_df['tax_deficit'] = merged_df['tax_deficit'].fillna(0)

        merged_df.rename(
            columns={
                'tax_deficit': 'tax_deficit_21_with_carve_out'
            },
            inplace=True
        )

        # We add the 30% tax deficit with carve-outs to the central DataFrame
        merged_df = merged_df.merge(
            td_30[['Parent jurisdiction (alpha-3 code)', 'tax_deficit']],
            how='left',
            on='Parent jurisdiction (alpha-3 code)'
        )

        merged_df['tax_deficit'] = merged_df['tax_deficit'].fillna(0)

        merged_df.rename(
            columns={
                'tax_deficit': 'tax_deficit_30_with_carve_out'
            },
            inplace=True
        )

        # We have the tax deficit absolute amounts with and without carve-outs at 15%, 21%, 25% and 30% minimum rates
        # But we want to display the changes due to carve-outs, as a % of the no-carve-out tax deficit

        # We store the names of the 4 columns that we are going to add to the central DataFrame
        new_columns = []

        # We iterate over the 4 minimum rates
        for minimum_rate in [15, 21, 25, 30]:
            column_name_no_carve_out = f'tax_deficit_{minimum_rate}_no_carve_out'
            column_name_with_carve_out = f'tax_deficit_{minimum_rate}_with_carve_out'

            # We are going to add a new column that provides the % reduction due to carve-outs at the rate considered
            new_column_name = f'reduction_at_{minimum_rate}_minimum_rate'

            # We make the corresponding computation
            merged_df[new_column_name] = (
                (merged_df[column_name_with_carve_out] - merged_df[column_name_no_carve_out]) /
                merged_df[column_name_no_carve_out]
            ) * 100

            new_columns.append(new_column_name)

        if output_Excel:
            with pd.ExcelWriter('/Users/Paul-Emmanuel/Desktop/carve_outs_table_2.xlsx', engine='xlsxwriter') as writer:
                merged_df.to_excel(writer, sheet_name='table_2', index=False)

        # We output the resulting DataFrame with country codes and names, as well as the 4 columns of interest
        merged_df = merged_df[
            ['Parent jurisdiction (alpha-3 code)', 'Parent jurisdiction (whitespaces cleaned)'] + new_columns
        ].copy()

        return merged_df.copy()

    def get_carve_outs_rate_table(
        self,
        minimum_ETR,
        depreciation_only, exclude_inventories,
    ):
        """
        This function takes as inputs:

        - the minimum effective tax rate to apply to multinationals' profits;

        - a boolean, "depreciation_only", indicating whether to restrict the tangible assets component of substance-
        based carve-outs to a share of depreciation expenses;

        - a boolean, "exlude_inventories", indicating whether to exlude inventories from tangible assets or not.

        It returns a DataFrame that shows, for each in-sample country, the estimated revenues that could be collected
        from a global minimum tax without any carve-outs and with carve-outs of 5%, 7.5% and 10% of tangible assets and
        payroll combined.
        """

        # We instantiate a TaxDeficitCalculator object without carve-outs
        calculator = TaxDeficitCalculator(fetch_data_online=self.fetch_data_online)

        calculator.load_clean_data()

        # We use it to compute revenue gains without any carve-out
        td_no_carve_out = calculator.get_total_tax_deficits(minimum_ETR=minimum_ETR).iloc[:-2]

        td_no_carve_out.rename(
            columns={
                'tax_deficit': 'tax_deficit_no_carve_out'
            },
            inplace=True
        )

        # A copy of the resulting DataFrame will be used as a central table to which we add the relevant columns
        merged_df = td_no_carve_out.copy()

        # We iterate over carve-out rates
        for carve_out_rate in [5, 7.5, 10]:
            actual_rate = carve_out_rate / 100

            # We instantiate a TaxDeficitCalculator object with carve-outs at the rate considered
            # NB: we assume that the actual_rate is applied to both payroll and tangible assets similarly
            calculator = TaxDeficitCalculator(
                carve_outs=True,
                carve_out_rate_assets=actual_rate, carve_out_rate_payroll=actual_rate,
                depreciation_only=False,
                exclude_inventories=exclude_inventories,
                fetch_data_online=self.fetch_data_online
            )
            calculator.load_clean_data()

            # We use it to compute revenue gains with substance-based carve-outs being applied
            td_carve_out = calculator.get_total_tax_deficits(minimum_ETR=minimum_ETR).iloc[:-2]

            # We add the tax deficits thereby computed to the central table
            merged_df = merged_df.merge(
                td_carve_out[['Parent jurisdiction (alpha-3 code)', 'tax_deficit']],
                how='left',
                on='Parent jurisdiction (alpha-3 code)'
            )

            merged_df['tax_deficit'] = merged_df['tax_deficit'].fillna(0)

            merged_df.rename(
                columns={
                    'tax_deficit': f'tax_deficit_{carve_out_rate}_carve_out'
                },
                inplace=True
            )

        # We only display EU or CbCR-reporting countries
        cbcr_reporting_countries = list(self.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        mask_eu = merged_df['Parent jurisdiction (alpha-3 code)'].isin(self.eu_27_country_codes)
        mask_cbcr = merged_df['Parent jurisdiction (alpha-3 code)'].isin(cbcr_reporting_countries)

        # This condition is encapsulated in the following boolean indexing mask
        mask = np.logical_or(mask_eu, mask_cbcr)

        # We add two useful indicator variables
        merged_df['IS_EU'] = mask_eu * 1
        merged_df['REPORTS_CbCR'] = mask_cbcr * 1

        # And we restrict the DataFrame to relevant countries
        restricted_df = merged_df[mask].copy()

        # We finalise the formatting of the table
        restricted_df.sort_values(
            by=['IS_EU', 'Parent jurisdiction (alpha-3 code)'],
            ascending=[False, True],
            inplace=True
        )

        # And eventually return the DataFrame
        return restricted_df.copy()

    def get_average_CbCR_ETRs(
        self
    ):
        """
        Based on the country-by-country report statistics, this method allows to compute effective tax rates (ETRs)
        averaged over the two available income years at the level of each parent / partner country pair. Averaged ETRs
        are less sensitive to temporary adjustments and should provide a more accurate view of the actual tax rates.
        """
        if self.statutory_rates is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        oecd = pd.read_csv(self.path_to_oecd)

        statutory_rates = self.statutory_rates.copy()

        # Focusing on the positive profits sub-sample
        oecd = oecd[oecd['PAN'] == 'PANELAI'].copy()

        oecd.drop(
            columns=[
                'PAN', 'Grouping', 'Flag Codes', 'Flags', 'Year',
                'Ultimate Parent Jurisdiction', 'Partner Jurisdiction'
            ],
            inplace=True
        )

        # Moving from a long to a wide dataset
        oecd = oecd.pivot(
            index=['COU', 'JUR', 'YEA'],
            columns='Variable',
            values='Value'
        ).reset_index()

        # Keeping only columns of interest
        oecd = oecd[
            [
                'COU', 'JUR', 'YEA', 'Profit (Loss) before Income Tax',
                'Income Tax Paid (on Cash Basis)', 'Income Tax Accrued - Current Year',
                'Adjusted Profit (Loss) before Income Tax'
            ]
        ].copy()

        # Eliminating Foreign Jurisdictions Totals and Stateless Entities when they are not needed
        oecd['JUR'] = oecd.apply(
            lambda row: rename_partner_jurisdictions(row, use_case='specific'),
            axis=1
        )

        # We eliminate stateless entities and the "Foreign Jurisdictions Total" fields
        oecd = oecd[
            ~oecd['JUR'].isin(['FJT', 'STA'])
        ].copy()

        oecd['JUR'] = oecd['JUR'].map(lambda x: 'FJT' if x == 'FJTa' else x)

        # Replacing, if relevant, unadjusted profits by the adjusted ones
        if self.use_adjusted_profits:
            oecd['Profit (Loss) before Income Tax'] = oecd.apply(
                (
                    lambda row: row['Adjusted Profit (Loss) before Income Tax']
                    if not np.isnan(row['Adjusted Profit (Loss) before Income Tax'])
                    else row['Profit (Loss) before Income Tax']
                ),
                axis=1
            )

        if self.sweden_adjust:
            sweden_adj_ratios = {
                year: TaxDeficitCalculator(
                    year=year,
                    sweden_treatment='adjust',
                    add_AUT_AUT_row=False,
                    fetch_data_online=self.fetch_data_online
                ).sweden_adjustment_ratio
                for year in [2016, 2017, 2018]
            }

            oecd['Profit (Loss) before Income Tax'] = oecd.apply(
                (
                    lambda row: row['Profit (Loss) before Income Tax'] * sweden_adj_ratios[row['YEA']]
                    if row['COU'] == 'SWE' and row['JUR'] == 'SWE' else row['Profit (Loss) before Income Tax']
                ),
                axis=1
            )

        if self.belgium_treatment in ['adjust', 'replace']:

            # We remove the problematic country pairs from the computation of average ETRs
            oecd = oecd[
                ~np.logical_or(
                    np.logical_and(
                        oecd['COU'] == 'BEL',
                        np.logical_and(
                            oecd['JUR'] == 'NLD',
                            oecd['YEA'] == 2016
                        )
                    ),
                    np.logical_and(
                        oecd['COU'] == 'BEL',
                        np.logical_and(
                            oecd['JUR'] == 'GBR',
                            oecd['YEA'] == 2017
                        )
                    )
                )
            ].copy()

        if self.SGP_CYM_treatment == 'replace':

            # We remove the problematic observation from the computation of average ETRs
            oecd = oecd[
                ~np.logical_and(
                    oecd['COU'] == 'SGP',
                    np.logical_and(
                        oecd['JUR'] == 'CYM',
                        oecd['YEA'] == 2017
                    )
                )
            ].copy()

        if self.extended_dividends_adjustment:
            multiplier = np.logical_and(
                oecd['COU'] == oecd['JUR'],
                ~oecd['COU'].isin(['SWE'] + list(self.adj_profits_countries))
            ) * 1

            multiplier = multiplier.map(
                {0: 1, 1: self.extended_adjustment_ratio}
            )

            oecd['Profit (Loss) before Income Tax'] *= multiplier

        oecd.drop(columns=['Adjusted Profit (Loss) before Income Tax'], inplace=True)

        # Replacing missing income tax paid values by income tax accrued and adding statutory rates
        oecd['Income Tax Paid (on Cash Basis)'] = oecd.apply(
            (
                lambda row: row['Income Tax Paid (on Cash Basis)']
                if row['Income Tax Paid (on Cash Basis)'] >= 0
                and not np.isnan(row['Income Tax Paid (on Cash Basis)'])
                else row['Income Tax Accrued - Current Year']
            ),
            axis=1
        )

        oecd.drop(columns=['Income Tax Accrued - Current Year'], inplace=True)

        oecd = oecd.merge(
            statutory_rates,
            how='left',
            left_on='JUR', right_on='partner'
        )

        oecd.drop(columns=['partner'], inplace=True)

        # We apply the deflation of profits and income taxes paid
        deflators = {
            2016: self.deflator_2016_to_2017,
            2017: 1
        }

        oecd['deflators'] = oecd['YEA'].map(deflators)

        oecd['Profit (Loss) before Income Tax'] *= oecd['deflators']
        oecd['Income Tax Paid (on Cash Basis)'] *= oecd['deflators']

        oecd.drop(columns=['deflators'], inplace=True)

        # We eliminate the rows that lack both profits and income taxes paid
        oecd = oecd[
            ~np.logical_and(
                oecd['Profit (Loss) before Income Tax'].isnull(),
                oecd['Income Tax Paid (on Cash Basis)'].isnull()
            )
        ].copy()

        # After these preprocessing steps, moving to the computation of average ETRs

        # We exclude from the computation rows for which either profits or income taxes paid are missing
        oecd_temp = oecd[
            ~np.logical_or(
                oecd['Profit (Loss) before Income Tax'].isnull(),
                oecd['Income Tax Paid (on Cash Basis)'].isnull()
            )
        ].copy()

        oecd_temp = oecd_temp[
            ~np.logical_and(
                oecd_temp['Profit (Loss) before Income Tax'] == 0,
                oecd_temp['Income Tax Paid (on Cash Basis)'] == 0
            )
        ].copy()

        # Theresa excludes from the computation the rows for which income taxes paid are negative
        oecd_temp = oecd_temp[
            oecd_temp['Income Tax Paid (on Cash Basis)'] >= 0
        ].copy()

        average_ETRs = oecd_temp.groupby(['COU', 'JUR']).sum()[
            ['Profit (Loss) before Income Tax', 'Income Tax Paid (on Cash Basis)']
        ].reset_index()

        average_ETRs['ETR'] = (
            average_ETRs['Income Tax Paid (on Cash Basis)'] / average_ETRs['Profit (Loss) before Income Tax']
        )

        average_ETRs['ETR'] = average_ETRs.apply(
            (
                lambda row: 0 if row['Income Tax Paid (on Cash Basis)'] == 0
                and row['Profit (Loss) before Income Tax'] == 0 else row['ETR']
            ),
            axis=1
        )

        average_ETRs = average_ETRs[['COU', 'JUR', 'ETR']].copy()

        oecd = oecd.merge(
            average_ETRs,
            on=['COU', 'JUR'],
            how='left'
        )

        oecd['ETR'] = oecd.apply(
            lambda row: row['statrate'] if np.isnan(row['ETR']) else row['ETR'],
            axis=1
        )

        self.temp = oecd.copy()

        # oecd['ETR'] = winsorize(oecd['ETR'].values, limits=[0.04, 0.04], nan_policy='omit')

        quantile = oecd['ETR'].quantile(q=0.96, interpolation='nearest')
        oecd['ETR'] = oecd['ETR'].map(lambda x: quantile if not np.isnan(x) and x > quantile else x)

        average_ETRs = oecd.groupby(['COU', 'JUR']).mean()['ETR'].reset_index()

        average_ETRs.rename(
            columns={
                'COU': 'Parent jurisdiction (alpha-3 code)',
                'JUR': 'Partner jurisdiction (alpha-3 code)'
            },
            inplace=True
        )

        self.average_ETRs = average_ETRs.copy()

        return average_ETRs.copy()

    def output_dividends_appendix_table(self):
        """
        This method allows to produce the Table A5 in Appendix B of the October 2021 note.

        For the three countries that have shared relevant information (the Netherlands, the UK and Sweden), it provides
        an overview of the (potential) weight of intra-group dividends in the profits recorded domestically in country-
        by-country report statistics.
        """

        # Loading the raw OECD data
        oecd = pd.read_csv(self.path_to_oecd)

        oecd = oecd[oecd['PAN'] == 'PANELAI'].copy()

        # Instantiating the dictionary which will be transformed into a DataFrame
        output = {
            'Parent country': [],
            'Year': [],
            'Unadjusted profits before tax ($bn)': [],
            'Adjusted profits before tax ($bn)': [],
            'Adjustment factor (%)': []
        }

        # Sweden case
        temp = oecd[
            np.logical_and(
                oecd['COU'] == 'SWE',
                np.logical_and(
                    oecd['JUR'] == 'SWE',
                    oecd['CBC'] == 'PROFIT'
                )
            )
        ].copy()

        for year in [2016, 2017, 2018]:
            output['Parent country'].append('Sweden')
            output['Year'].append(year)

            output['Unadjusted profits before tax ($bn)'].append(
                temp[temp['YEA'] == year]['Value'].iloc[0] / 10**9
            )

            multiplier = self.sweden_adj_ratio_2016 if year == 2016 else self.sweden_adj_ratio_2017

            output['Adjusted profits before tax ($bn)'].append(
                temp[temp['YEA'] == year]['Value'].iloc[0] / 10**9 * multiplier
            )

            output['Adjustment factor (%)'].append(multiplier * 100)

        # Countries providing adjusted profits
        temp = oecd[oecd['CBC'] == 'PROFIT_ADJ'].copy()

        for parent_country in temp['Ultimate Parent Jurisdiction'].unique():
            output['Parent country'].append(parent_country)

            temp_bis = temp[temp['Ultimate Parent Jurisdiction'] == parent_country].copy()

            for year in temp_bis['YEA'].unique():
                output['Year'].append(year)

                adjusted_profits = temp_bis[temp_bis['Year'] == year]['Value'].iloc[0]

                unadjusted_profits = oecd[
                    np.logical_and(
                        oecd['Ultimate Parent Jurisdiction'] == parent_country,
                        np.logical_and(
                            oecd['Partner Jurisdiction'] == parent_country,
                            np.logical_and(
                                oecd['YEA'] == year,
                                oecd['CBC'] == 'PROFIT'
                            )
                        )
                    )
                ]['Value'].iloc[0]

                output['Adjusted profits before tax ($bn)'].append(adjusted_profits / 10**9)
                output['Unadjusted profits before tax ($bn)'].append(unadjusted_profits / 10**9)
                output['Adjustment factor (%)'].append(adjusted_profits / unadjusted_profits * 100)

        return pd.DataFrame(output)

    def compute_qdmtt_revenue_gains(
        self, minimum_ETR=0.15, upgrade_non_havens=True
    ):
        """
        This method is used to produce the revenue gain estimates under the "QDMTT scenario". In this simulation, all
        source countries - i.e., countries where profits are booked - are assumed to implement a Qualified Domestic Top-
        up Tax (QDMTT) and thereby collect the relevant top-up taxes. Methodology is described in the dedicated section
        of the latest paper and in the associated Online Appendix.

        The following arguments are required:

        - "minimum_ETR", that defaults to 0.15, simply corresponds to the minimum ETR that should be applied;

        - the boolean "upgrade_non_havens" indicates whether to upgrade non-havens' estimated revenue gains. Indeed, in
        the "headquarter scenario", we impute the non-haven tax deficit of TWZ countries. Because this amount is not di-
        rectly observed in the bilateral data sources that we use, it would be absent from QDMTT revenue gains simply
        based on the attribution of top-up taxes to source jurisdictions. To ensure consistent aggregate revenue gains
        between the two scenarios, we distribute this amount among non-havens proportionally to their QDMTT revenues.
        """

        # We need to have previously loaded and cleaned the OECD and TWZ data
        if self.oecd is None or self.twz is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        # We fetch the list of OECD-reporting parent countries whose tax haven tax deficit is taken from TWZ data and
        # not from OECD data in the benchmark computations
        headquarter_collects_scenario = self.compute_all_tax_deficits(minimum_ETR=minimum_ETR)
        countries_replaced = self.countries_replaced.copy()

        oecd = self.oecd.copy()

        # --- Step common to OECD and TWZ data

        # Depending on the chosen treatment of Belgian and Swedish CbCRs, we have to adapt the OECD data and therefore
        # the list of parent countries to consider in TWZ data
        unique_parent_countries = oecd['Parent jurisdiction (alpha-3 code)'].unique()

        if self.sweden_exclude and self.belgium_treatment == 'exclude':
            oecd = oecd[~oecd['Parent jurisdiction (alpha-3 code)'].isin(['BEL', 'SWE'])].copy()

            unique_parent_countries = list(
                unique_parent_countries[
                    ~unique_parent_countries.isin(['BEL', 'SWE'])
                ]
            )

        elif self.sweden_exclude and self.belgium_treatment != 'exclude':
            oecd = oecd[oecd['Parent jurisdiction (alpha-3 code)'] != 'SWE'].copy()

            unique_parent_countries = list(
                unique_parent_countries[unique_parent_countries != 'SWE'].copy()
            )

        elif not self.sweden_exclude and self.belgium_treatment == 'exclude':
            oecd = oecd[oecd['Parent jurisdiction (alpha-3 code)'] != 'BEL'].copy()

            unique_parent_countries = list(
                unique_parent_countries[unique_parent_countries != 'BEL'].copy()
            )

        else:
            unique_parent_countries = list(unique_parent_countries)

        self.unique_parent_countries_temp = unique_parent_countries.copy()

        # --- Building the full sample table

        # - OECD data

        oecd = oecd.rename(
            columns={
                'Parent jurisdiction (alpha-3 code)': 'PARENT_COUNTRY_CODE',
                'Partner jurisdiction (alpha-3 code)': 'PARTNER_COUNTRY_CODE',
                'Parent jurisdiction (whitespaces cleaned)': 'PARENT_COUNTRY_NAME',
                'Partner jurisdiction (whitespaces cleaned)': 'PARTNER_COUNTRY_NAME',
                'Profit (Loss) before Income Tax': 'PROFITS_BEFORE_TAX_POST_CO'
            }
        )

        oecd = oecd[
            [
                'PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE',
                'PARENT_COUNTRY_NAME', 'PARTNER_COUNTRY_NAME',
                'PROFITS_BEFORE_TAX_POST_CO', 'ETR'
            ]
        ].copy()

        oecd['SOURCE'] = 'oecd'

        # - TWZ tax haven data

        twz = load_and_clean_bilateral_twz_data(
            path_to_excel_file=self.path_to_excel_file,
            path_to_geographies=self.path_to_geographies
        )

        # We exclude OECD-reporting countries, except for those whose tax haven tax deficit is taken from TWZ data
        twz = twz[
            np.logical_or(
                ~twz['PARENT_COUNTRY_CODE'].isin(unique_parent_countries),
                twz['PARENT_COUNTRY_CODE'].isin(countries_replaced)
            )
        ].copy()

        # We exclude the few observations for wich parent and partner countries are the same (only for MLT and CYP)
        # This would otherwise induce double-counting with the domestic TWZ data
        twz = twz[twz['PARENT_COUNTRY_CODE'] != twz['PARTNER_COUNTRY_CODE']].copy()

        # Negative profits are brought to 0 (no tax deficit to collect)
        twz['PROFITS'] = twz['PROFITS'].map(lambda x: max(x, 0))

        # We move from millions of USD to USD
        twz['PROFITS'] = twz['PROFITS'] * 10**6

        # If carve-outs are applied, we need to apply the average reduction in tax haven profits implied by carve-outs
        if self.carve_outs:
            twz['PROFITS'] *= (1 - self.avg_carve_out_impact_tax_haven)

        if self.behavioral_responses and self.behavioral_responses_include_TWZ:
            if self.behavioral_responses_method == 'linear_elasticity':
                twz['PROFITS'] *= (
                    1 - self.behavioral_responses_TH_elasticity * max(
                        15 - self.assumed_haven_ETR_TWZ * 100, 0
                    )
                )

            else:
                multiplier = 1 if self.assumed_haven_ETR_TWZ >= 0.15 else np.exp(
                    self.behavioral_responses_beta_1 * 0.15
                    + self.behavioral_responses_beta_2 * 0.15**2
                    + self.behavioral_responses_beta_3 * 0.15**3
                    - self.behavioral_responses_beta_1 * self.assumed_haven_ETR_TWZ
                    - self.behavioral_responses_beta_2 * self.assumed_haven_ETR_TWZ**2
                    - self.behavioral_responses_beta_3 * self.assumed_haven_ETR_TWZ**3
                )

                twz['PROFITS'] *= multiplier

        twz = twz.rename(columns={'PROFITS': 'PROFITS_BEFORE_TAX_POST_CO'})

        # Focusing on columns of interest
        twz = twz[
            [
                'PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE',
                'PARENT_COUNTRY_NAME', 'PARTNER_COUNTRY_NAME',
                'PROFITS_BEFORE_TAX_POST_CO'
            ]
        ].copy()

        # Adding the variables that are still missing compared with the OECD sample
        twz['ETR'] = self.assumed_haven_ETR_TWZ
        twz['SOURCE'] = 'twz_th'

        # - TWZ domestic data

        twz_domestic = self.twz_domestic.copy()

        # We filter out OECD-reporting countries to avoid double-counting their domestic tax deficit
        twz_domestic = twz_domestic[~twz_domestic['Alpha-3 country code'].isin(unique_parent_countries)].copy()

        # We filter non-EU countries as they are not assumed to collect their domestic tax deficit
        twz_domestic = twz_domestic[twz_domestic['Alpha-3 country code'].isin(self.eu_27_country_codes)].copy()

        # We add country names to TWZ data on domestic profits and ETRs
        geographies = pd.read_csv(self.path_to_geographies)
        geographies = geographies.groupby('CODE').first().reset_index()   # To have only one name per country code

        twz_domestic = twz_domestic.merge(
            geographies[['CODE', 'NAME']],
            how='left',
            left_on='Alpha-3 country code', right_on='CODE'
        )

        if twz_domestic['CODE'].isnull().sum() > 0:
            raise Exception('Some country codes in the TWZ domestic data could not be identified.')

        twz_domestic = twz_domestic.drop(columns=['CODE'])

        # Renaming columns in the standardized way
        twz_domestic = twz_domestic.rename(
            columns={
                'Domestic profits': 'PROFITS_BEFORE_TAX_POST_CO',
                'Domestic ETR': 'ETR',
                'Alpha-3 country code': 'PARENT_COUNTRY_CODE',
                'NAME': 'PARENT_COUNTRY_NAME'
            }
        )

        # Adding the columns that are still missing for the concatenation into the full sample table
        twz_domestic['PARTNER_COUNTRY_CODE'] = twz_domestic['PARENT_COUNTRY_CODE'].values
        twz_domestic['PARTNER_COUNTRY_NAME'] = twz_domestic['PARENT_COUNTRY_NAME'].values

        twz_domestic['SOURCE'] = 'twz_dom'

        # --- Deducing the full sample table

        # Concatenating the three data sources
        full_sample = pd.concat([oecd, twz, twz_domestic], axis=0)

        # Non-EU countries are not assumed to collect their domestic tax deficit
        multiplier = np.logical_and(
            ~full_sample['PARENT_COUNTRY_CODE'].isin(self.eu_27_country_codes),
            full_sample['PARENT_COUNTRY_CODE'] == full_sample['PARTNER_COUNTRY_CODE']
        ) * 1

        multiplier = 1 - multiplier

        full_sample['PROFITS_BEFORE_TAX_POST_CO'] *= multiplier

        # For OECD-reporting countries whose tax haven tax deficit is taken in TWZ data, we must avoid double-counting
        multiplier = np.logical_and(
            full_sample['PARENT_COUNTRY_CODE'].isin(countries_replaced),
            np.logical_and(
                full_sample['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
                full_sample['SOURCE'] == 'oecd'
            )
        )

        multiplier = 1 - multiplier

        full_sample['PROFITS_BEFORE_TAX_POST_CO'] *= multiplier

        # Computation of tax deficits
        full_sample['ETR_DIFF'] = full_sample['ETR'].map(lambda x: max(minimum_ETR - x, 0))
        full_sample['TAX_DEFICIT'] = full_sample['ETR_DIFF'] * full_sample['PROFITS_BEFORE_TAX_POST_CO']

        # --- Attributing the tax deficits of the "Rest of non-EU tax havens" in TWZ data

        rest_extract = full_sample[full_sample['PARTNER_COUNTRY_CODE'] == 'REST'].copy()
        to_be_distributed = rest_extract['TAX_DEFICIT'].sum()

        full_sample = full_sample[full_sample['PARTNER_COUNTRY_CODE'] != 'REST'].copy()

        full_sample['TEMP_DUMMY'] = np.logical_and(
            full_sample['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
            ~full_sample['PARTNER_COUNTRY_CODE'].isin(self.eu_27_country_codes + ['CHE'])
        ) * 1

        full_sample['TEMP_SHARE'] = (
            full_sample['TEMP_DUMMY'] * full_sample['TAX_DEFICIT']
            / full_sample[full_sample['TEMP_DUMMY'] == 1]['TAX_DEFICIT'].sum()
        )

        full_sample['TAX_DEFICIT'] += full_sample['TEMP_SHARE'] * to_be_distributed

        full_sample = full_sample.drop(columns=['TEMP_SHARE', 'TEMP_DUMMY'])

        # --- Upgrading non-haven tax deficits

        # - Theresa's method
        if upgrade_non_havens:
            to_be_distributed = (
                headquarter_collects_scenario['tax_deficit'].sum() / (self.USD_to_EUR * self.multiplier_2021)
                - full_sample['TAX_DEFICIT'].sum()
            )

            full_sample['TEMP_DUMMY'] = np.logical_and(
                ~full_sample['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
                full_sample['PARENT_COUNTRY_CODE'] != full_sample['PARTNER_COUNTRY_CODE']
            ) * 1

            full_sample['TEMP_SHARE'] = (
                full_sample['TEMP_DUMMY'] * full_sample['TAX_DEFICIT']
                / full_sample[full_sample['TEMP_DUMMY'] == 1]['TAX_DEFICIT'].sum()
            )

            full_sample['TAX_DEFICIT'] += full_sample['TEMP_SHARE'] * to_be_distributed

            full_sample = full_sample.drop(columns=['TEMP_SHARE', 'TEMP_DUMMY'])

        # Alternative method that avoids attributing revenues to the headquarter country itself
        # if upgrade_non_havens:

        #     # What we miss is the non-haven tax deficit of TWZ countries in the headquarter country scenario
        #     # We can find it in the "headquarter_collects_scenario" table
        #     temp = headquarter_collects_scenario[
        #         ~headquarter_collects_scenario['Parent jurisdiction (alpha-3 code)'].isin(unique_parent_countries)
        #     ].copy()

        #     # We iterate over each row / taxing country in this DataFrame
        #     for _, row in temp.iterrows():

        #         # We fetch the code of the TWZ country considered and the associated, imputed non-haven tax deficit
        #         twz_country = row['Parent jurisdiction (alpha-3 code)']
        #         tax_deficit_to_distribute = row['tax_deficit_x_non_haven'] / (self.USD_to_EUR * self.multiplier_2021)

        #         full_sample['TEMP_DUMMY'] = np.logical_and(
        #             ~full_sample['PARTNER_COUNTRY_CODE'].isin(tax_haven_country_codes),
        #             np.logical_and(
        #                 full_sample['PARENT_COUNTRY_CODE'] != full_sample['PARTNER_COUNTRY_CODE'],
        #                 full_sample['PARTNER_COUNTRY_CODE'] != twz_country
        #             )
        #         ) * 1

        #         full_sample['TEMP_SHARE'] = (
        #             full_sample['TEMP_DUMMY'] * full_sample['TAX_DEFICIT']
        #             / full_sample[full_sample['TEMP_DUMMY'] == 1]['TAX_DEFICIT'].sum()
        #         )

        #         full_sample['TAX_DEFICIT'] += full_sample['TEMP_SHARE'] * tax_deficit_to_distribute

        #         full_sample = full_sample.drop(columns=['TEMP_SHARE', 'TEMP_DUMMY'])

        # --- Finalising the tax deficit computations

        # Grouping by partner country in the full QDMTT scenario
        tax_deficits = full_sample.groupby(
            'PARTNER_COUNTRY_CODE'
        ).agg(
            {
                'PARTNER_COUNTRY_NAME': 'first',
                'TAX_DEFICIT': 'sum'
            }
        ).reset_index()

        # Currency conversion and upgrade to 2021
        tax_deficits['TAX_DEFICIT'] *= self.multiplier_2021 * self.USD_to_EUR

        return tax_deficits.copy()

    def compute_tds_from_purely_domestic_firms(
        self,
        imputation,
        average_ETRs,
        minimum_ETR=0.15,
        output_Excel=False,
        output_sample=False,
        verbose=False,
        exclude_COVID_years=False,
        exclude_unconsolidated=False,
    ):
        """
        This method is used to preprocess the ORBIS data on EU large-scale purely domestic groups and deduce estimates
        for the revenue gains that could be drawn from their inclusion in the scope of the European Commission's di-
        rective. The methodology is described in details in the Online Appendix associated with the latest paper.

        Several arguments are required:

        - "imputation" is a character string (either "average" or "closest_year") that indicates the methodology to use
        to deal with missing values. In both cases, 2021 is taken as reference. If "average" is chosen, 2021 missing va-
        lues are imputed based on the average of the corresponding variable in the other income years. If "closest_year"
        is chosen, we impute missing values by looking for the latest value available and uprating it to 2021;

        - "average_ETRs" is a boolean indicating whether to average each firm's ETR over all the income years for which
        positive profits and taxes paid are recorded, similarly to what can be done with macro-data;

        - "minimum_ETR", that defaults to 0.15, simply indicates the minimum ETR to consider;

        - the boolean "output_Excel" indicates whether to save the estimates in a dedicated Excel file. Make sure to
        change the destination path defined below if you want to use this option. Set to False by default;

        - the boolean "output_sample" indicates whether to output the preprocessed data alongside the revenue gain esti-
        mates. If it is set to True, 3 different DataFrames are returned. If it is set to False, only one table that
        displays the revenue gain estimates is returned. Set to False by default;

        - the boolean "verbose" indicates whether to print some intermediary statements that help follow the computa-
        tions. It is set to False by default and was mainly used to write the methodological complement to this code.

        This method relies on the "get_firm_level_average_ETRs" method defined below and mobilizes different functions
        defined in "utils.py" ("get_avg_of_available_years", "find_closest_year_available", "apply_upgrade_factor").
        """

        if imputation not in ['average', 'closest_year']:
            raise Exception(
                'Two methodologies can be used for missing values: either average the variable over available years '
                + '("average") or use the closest year available and upgrade it to the reference year ("closest_year").'
            )

        input_file_name = 'large_scale_purely_domestic_groups_final_sample.xlsx'
        output_file_suffix = 'final_extract'

        file_name = input_file_name
        path_to_data = os.path.join(path_to_dir, 'data', file_name)

        self.path_to_purely_dom_firms = path_to_data

        # Opening the Excel file
        df = pd.read_excel(path_to_data, engine='openpyxl', sheet_name='Results')

        self.temp_extract1 = df.copy()

        # Excluding COVID years if relevant
        if exclude_COVID_years:
            columns_to_drop = list(df.columns[df.columns.map(lambda x: x.endswith('2020') or x.endswith('2021'))])
            df = df.drop(columns=columns_to_drop)

        # We exclude the first row, only made of the Orbis codes of the variables, and the first column with indices
        df = df.iloc[1:, 1:].copy()

        # We execute the additional filtering steps required by the final extract if relevant
        df['Company name Latin alphabet'] = df['Company name Latin alphabet'].ffill()

        # Excluding unconsolidated financials if relevant
        df['Consolidation code'] = df['Consolidation code'].ffill()

        if exclude_unconsolidated:
            df = df[df['Consolidation code'].isin(['C1', 'C2'])].copy()

        if verbose:
            print('Number of unique firms in the unfiltered sample:', df['Company name Latin alphabet'].nunique())

        extract = df[
            [
                'Company name Latin alphabet', 'Country ISO code',
                'Subsidiary - Country ISO code', 'CSH - Type'
            ]
        ].copy()

        # Filtering based on the types of controlling shareholders
        to_be_excluded_CSH = extract[
            extract['CSH - Type'].isin(
                [
                    'Public authority, state, government', 'Bank', 'Corporate',
                    'Foundation, research Institute', 'Financial company'
                ]
            )
        ]['Company name Latin alphabet'].unique()

        extract = extract[
            ~extract['Company name Latin alphabet'].isin(to_be_excluded_CSH)
        ].copy()
        extract = extract.drop(columns=['CSH - Type'])
        extract = extract.dropna(subset=['Subsidiary - Country ISO code']).copy()

        # Filtering based on the location of direct and indirect subsidiaries
        extract['Country ISO code'] = extract['Country ISO code'].ffill()

        to_be_excluded_subsidiaries = extract[
            np.logical_and(
                extract['Country ISO code'] != extract['Subsidiary - Country ISO code'],
                extract['Subsidiary - Country ISO code'] != 'No data fulfill your filter criteria'
            )
        ]['Company name Latin alphabet'].unique()

        # Gathering the two filters
        to_be_excluded = list(to_be_excluded_CSH) + list(to_be_excluded_subsidiaries)

        if verbose:
            print('----------------')
            print('Number of firms excluded because of controlling shareholders:', len(to_be_excluded_CSH))
            print('Number of firms excluded because of foreign subsidiaries:', len(to_be_excluded_subsidiaries))
            print('Firms excluded for either of these two reasons:', len(np.unique(to_be_excluded)))
            print('----------------')

        excluded_manually = [
            'JOHN DEERE MEXICO S.A R.L.',
            'SEAGATE TECHNOLOGY HOLDINGS PUBLIC LIMITED COMPANY'
        ]
        to_be_excluded += excluded_manually

        # Excluding some firms manually
        if verbose:
            print(
                'Number of firms excluded manually:',
                len(
                    np.intersect1d(
                        excluded_manually,
                        df['Company name Latin alphabet'].unique()
                    )
                )
            )
            print('----------------')

        df = df[~df['Company name Latin alphabet'].isin(to_be_excluded)].copy()
        df = df.dropna(subset=['Country ISO code']).copy()

        # Eventually, removing duplicates
        df = df.drop_duplicates(subset=['Company name Latin alphabet']).copy()

        df = df.drop(
            columns=[
                'Inactive', 'Quoted', 'Branch', 'OwnData', 'Woco', 'Type of entity', 'Consolidation code',
                'NACE Rev. 2, core code (4 digits)', 'BvD ID number', 'European VAT number',
                'Subsidiary - Name', 'Subsidiary - BvD ID number', 'Subsidiary - Country ISO code',
                'CSH - Name', 'CSH - BvD ID number', 'CSH - Type', 'CSH - Level', 'CSH - Direct %',
                'CSH - Total %', 'Headquarters\nName', 'Headquarters\nBvD ID number', 'Headquarters\nType'
            ]
        )

        self.temp_extract = df.copy()

        # Missing values are designated as character strings "n.a."
        # We replace all of these by the usual object for missing values in Python
        df = df.applymap(
            lambda x: np.nan if x == 'n.a.' else x
        )

        # We constitute a list of the relevant financial variables
        financial_variables = df.columns[5:].copy()

        # And we convert them in a numeric format
        for column in financial_variables:
            df[column] = df[column].astype(float)

        # We also convert the column with the last year of data available
        df['Last avail. year'] = df['Last avail. year'].astype(int)

        # Adding ISO alpha-3 country codes
        df['Country ISO code - Alpha-3'] = df['Country ISO code'].map(
            lambda code: pycountry.countries.get(alpha_2=code).alpha_3
        )

        # --- Computation of average ETRs

        if average_ETRs:

            self.purely_dom_firms_df = df.copy()
            firm_level_average_ETRs = self.get_firm_level_average_ETRs(exclude_COVID_years=exclude_COVID_years)

        # --- Computing the average growth rates of turnover for each firm

        df['GROWTH_RATE'] = df.apply(get_growth_rates, axis=1)

        if verbose:
            print('Number of firms for which we lack a proper growth rate:', df['GROWTH_RATE'].isnull().sum())
            print('----------------')

        annual_growth_rates = df[
            ['Company name Latin alphabet', 'GROWTH_RATE']
        ].set_index(
            'Company name Latin alphabet'
        ).to_dict()['GROWTH_RATE']

        # --- Imputation of missing values

        if imputation == 'average':
            # We impute missing values by the average of the variable over the years for which it is available

            data = df.copy()
            # reference_year = self.year
            reference_year = 2021

            relevant_columns = []

            variables = [
                'Operating revenue (Turnover)\nm USD ', 'P/L before tax\nm USD ',
                'Taxation\nm USD ', 'Number of employees\n', 'Tangible fixed assets\nm USD '
            ]

            variables += ['Costs of employees\nm USD ']

            for variable in variables:

                # If we average ETRs over the whole sample period, we do not care about selecting a relevant value for
                # taxes paid (only used to obtain the ETR in the tax deficit computation)
                if average_ETRs and variable == 'Taxation\nm USD ':
                    continue

                column_name = 'RELEVANT_' + variable

                data[column_name] = data.apply(
                    lambda row: get_avg_of_available_years(row, reference_year, variable),
                    axis=1
                )

                relevant_columns.append(column_name)

        elif imputation == 'closest_year':
            # We first look for the year closest to the reference year for which the missing variable is available

            data = df.copy()
            # reference_year = self.year
            reference_year = 2021

            available_year_columns = []

            variables = [
                'Operating revenue (Turnover)\nm USD ', 'P/L before tax\nm USD ',
                'Taxation\nm USD ', 'Number of employees\n', 'Tangible fixed assets\nm USD '
            ]

            variables += ['Costs of employees\nm USD ']

            for variable in variables:

                # If we average ETRs over the whole sample period, we do not care about selecting a relevant value for
                # taxes paid (only used to obtain the ETR in the tax deficit computation)
                if average_ETRs and variable == 'Taxation\nm USD ':
                    continue

                column_name = 'AVAILABLE_YEAR_' + variable

                data[column_name] = data.apply(
                    lambda row: find_closest_year_available(row, reference_year, variable),
                    axis=1
                )

                available_year_columns.append(column_name)

            for column in available_year_columns:
                data[column] = data[column].astype(float)

            # We read the Excel file that contains the upgrade factor
            upgrade_factors = pd.read_excel(
                os.path.join(path_to_dir, 'data', 'gdpgrowth.xlsx'),
                engine='openpyxl'
            ).set_index(
                'CountryGroupName'
            )

            relevant_columns = []

            for variable in variables:

                # If we average ETRs over the whole sample period, we do not care about selecting a relevant value for
                # taxes paid (only used to obtain the ETR in the tax deficit computation)
                if average_ETRs and variable == 'Taxation\nm USD ':
                    continue

                column_name = 'RELEVANT_' + variable

                data[column_name] = data.apply(
                    lambda row: apply_upgrade_factor(
                        row,
                        reference_year,
                        variable,
                        upgrade_factors,
                        annual_growth_rates
                    ),
                    axis=1
                )

                relevant_columns.append(column_name)

        restricted_df = data[
            [
                'Company name Latin alphabet', 'Country ISO code - Alpha-3', 'Country ISO code',
            ] + list(relevant_columns)
        ].copy()

        # Conversion from million USD to plain USD
        for column in relevant_columns:
            if column != 'RELEVANT_Number of employees\n':
                restricted_df[column] *= 10**6

        # Applying the turnover threshold
        exchange_rates = pd.read_excel(os.path.join(path_to_dir, 'data', 'usdeur_xrate.xlsx'), engine='openpyxl')
        exchange_rate = exchange_rates.set_index('year').loc[reference_year, 'usd']

        threshold = 750 * 10**6 * exchange_rate
        self.threshold = threshold

        if verbose:
            print(
                'Number of firms excluded because of the turnover threshold:',
                (restricted_df['RELEVANT_Operating revenue (Turnover)\nm USD '] < threshold).sum()
            )

        restricted_df = restricted_df[
            restricted_df['RELEVANT_Operating revenue (Turnover)\nm USD '] >= threshold
        ].copy()

        subset = [
            'RELEVANT_Operating revenue (Turnover)\nm USD ',
            'RELEVANT_P/L before tax\nm USD ',
            'RELEVANT_Tangible fixed assets\nm USD '
        ]

        sample_before_dropna = restricted_df.copy()

        if not average_ETRs:
            subset += ['RELEVANT_Taxation\nm USD ']

        restricted_df = restricted_df.dropna(subset=subset).copy()

        restricted_df = restricted_df[
            ~np.logical_and(
                restricted_df['RELEVANT_Number of employees\n'].isnull(),
                restricted_df['RELEVANT_Costs of employees\nm USD '].isnull()
            )
        ].copy()

        # --- Applying carve-outs if relevant

        if self.carve_outs:

            mean_wages = self.mean_wages.copy()
            mean_wages = mean_wages[['partner2', 'earn']].copy()

            restricted_df = restricted_df.merge(
                mean_wages,
                how='left',
                left_on='Country ISO code - Alpha-3', right_on='partner2'
            ).drop(
                columns='partner2'
            )

            restricted_df['PAYROLL_PROXY'] = (
                restricted_df['earn'] * restricted_df['RELEVANT_Number of employees\n']
                * (1 + self.payroll_premium / 100)
            )

            restricted_df['PAYROLL'] = restricted_df[
                ['PAYROLL_PROXY', 'RELEVANT_Costs of employees\nm USD ']
            ].apply(
                (
                    lambda row: row['PAYROLL_PROXY']
                    if np.isnan(row['RELEVANT_Costs of employees\nm USD '])
                    else row['RELEVANT_Costs of employees\nm USD ']
                ),
                axis=1
            )

            restricted_df['CARVE_OUT'] = (
                self.carve_out_rate_payroll * restricted_df['PAYROLL']
                + (
                    self.carve_out_rate_assets * restricted_df['RELEVANT_Tangible fixed assets\nm USD ']
                    * self.assets_multiplier
                )
            )

            restricted_df['POST_CARVE_OUT_PROFITS'] = (
                restricted_df['RELEVANT_P/L before tax\nm USD '] - restricted_df['CARVE_OUT']
            ).map(lambda x: 0 if x < 0 else x)

        # --- Computation of tax deficits

        # We compute ETRs
        if not average_ETRs:

            # We bring negative taxes to 0 for the computation of ETRs
            restricted_df['ETR_numerator'] = restricted_df['RELEVANT_Taxation\nm USD '].map(
                lambda x: max(x, 0)
            )

            restricted_df['ETR'] = restricted_df['ETR_numerator'] / restricted_df['RELEVANT_P/L before tax\nm USD ']

        else:
            restricted_df = restricted_df.merge(
                firm_level_average_ETRs,
                how='left',
                on='Company name Latin alphabet'
            )

            if verbose:
                print('----------------')
                print('Number of firms for which we lack an average ETR:', restricted_df['ETR'].isnull().sum())

            stat_rates = self.statutory_rates.set_index(
                'partner'
            ).to_dict(
            )['statrate']

            restricted_df['ETR'] = restricted_df.apply(
                (
                    lambda row: row['ETR'] if not np.isnan(row['ETR'])
                    else stat_rates.get(row['Country ISO code - Alpha-3'], np.nan)
                ),
                axis=1
            )

            restricted_df = restricted_df.dropna(subset=['ETR']).copy()

        sample_with_CO_and_ETR = restricted_df.copy()

        # We focus on observations with positive profits
        if not self.carve_outs:
            restricted_df = restricted_df[restricted_df['RELEVANT_P/L before tax\nm USD '] > 0].copy()

        else:
            restricted_df = restricted_df[restricted_df['POST_CARVE_OUT_PROFITS'] > 0].copy()

        # We restrict to observations with an ETR below the minimum rate
        restricted_df = restricted_df[restricted_df['ETR'] < minimum_ETR].copy()

        # We deduce the ETR differential compared with the minimum rate
        restricted_df['ETR_differential'] = minimum_ETR - restricted_df['ETR']

        # Which eventually gives the tax deficit
        if not self.carve_outs:
            restricted_df['tax_deficit'] = (
                restricted_df['ETR_differential'] * restricted_df['RELEVANT_P/L before tax\nm USD ']
            )

        else:
            restricted_df['tax_deficit'] = (
                restricted_df['ETR_differential'] * restricted_df['POST_CARVE_OUT_PROFITS']
            )

        # We sum by parent country
        tax_deficits = restricted_df.groupby(['Country ISO code - Alpha-3', 'Country ISO code']).agg(
            {'tax_deficit': 'sum'}
        ).reset_index()

        # Currency conversion based on the exchange rate loaded previously
        tax_deficits['tax_deficit'] /= exchange_rate

        if output_Excel:
            path_base = '/Users/Paul-Emmanuel/Dropbox/EUTO/03. Research/2_tax_deficit/4_analysis/'
            path_base += 'Purely domestic firms/Python outputs'

            if not self.carve_outs:
                file_name = f'purely_dom_firms_{imputation}_imputation_no_CO_{output_file_suffix[file]}.xlsx'

            else:
                file_name = f'purely_dom_firms_{imputation}_imputation_'
                file_name += f'with_CO_{self.carve_out_rate_assets}%_{self.carve_out_rate_payroll}%_'
                file_name += f'{output_file_suffix[file]}.xlsx'

            path = os.path.join(path_base, file_name)

            with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
                tax_deficits.to_excel(writer, index=False)

        if output_sample:
            return sample_before_dropna.copy(), sample_with_CO_and_ETR.copy(), tax_deficits.copy()

        else:
            return tax_deficits.copy()

    def get_firm_level_average_ETRs(self, exclude_COVID_years, verbose=False):
        """
        This method, mobilized in the "compute_tds_from_purely_domestic_firms" method defined above, allows to estimate
        each large-scale purely domestic group's average ETR, considering all the income years for which it has recor-
        ded positive profits and positive income taxes. Setting the "verbose" boolean argument to True, we print the
        number of companies for which such an average ETR could not be computed (in which case we will impute the statu-
        tory corporate income tax rate in the method above).
        """

        df = self.purely_dom_firms_df.copy()

        ETR_dummy_columns = {}
        pos_profits_dummy_columns = {}
        valid_ETR_columns = {}
        pos_taxes_dummy_columns = {}

        range_temp = range(2016, 2022) if not exclude_COVID_years else range(2016, 2020)
        for year in range_temp:
            # Variables indicating whether the ETR can be computed
            ETR_dummy_column = f'IS_ETR_{year}_COMPLETE'

            bool_array1 = df[f'P/L before tax\nm USD {year}'].isnull()
            bool_array2 = df[f'Taxation\nm USD {year}'].isnull()

            df[ETR_dummy_column] = ((bool_array1 * 1 + bool_array2 * 1) == 0) * 1

            ETR_dummy_columns[year] = ETR_dummy_column

            # Variables indicating positive profits
            pos_profits_dummy_column = f'ARE_{year}_PROFITS_POSITIVE'

            df[pos_profits_dummy_column] = np.logical_and(
                ~df[f'P/L before tax\nm USD {year}'].isnull(),
                df[f'P/L before tax\nm USD {year}'] > 0
            ) * 1

            pos_profits_dummy_columns[year] = pos_profits_dummy_column

            # Variables indicating positive taxes
            pos_taxes_dummy_column = f'ARE_{year}_TAXES_POSITIVE'

            df[pos_taxes_dummy_column] = np.logical_and(
                ~df[f'Taxation\nm USD {year}'].isnull(),
                df[f'Taxation\nm USD {year}'] > 0
            ) * 1

            pos_taxes_dummy_columns[year] = pos_taxes_dummy_column

            # Variables indicating whether the ETR will be fully valid
            valid_ETR_column = f'IS_ETR_{year}_VALID'

            df[valid_ETR_column] = (
                df[f'IS_ETR_{year}_COMPLETE'] * df[f'ARE_{year}_PROFITS_POSITIVE'] * df[f'ARE_{year}_TAXES_POSITIVE']
            )

            valid_ETR_columns[year] = valid_ETR_column

        # We eliminate companies for which we never have a year with a valid ETR to compute
        if verbose:
            print(
                (
                    df[valid_ETR_columns.values()].sum(axis=1) == 0
                ).sum()
            )

            self.temp_extract = df[df[valid_ETR_columns.values()].sum(axis=1) == 0].copy()

        restricted_df = df[df[valid_ETR_columns.values()].sum(axis=1) != 0].copy()

        # We construct the numerator and the denominator for the computation of average ETRs
        # Obtained by summing valid pre-tax profits and valid taxes paid
        # These are valid if they are both available at the same time and if profits are positive

        # When summing, we upgrade all values to 2021 for comparability purposes thanks to the usual upgrade factors
        upgrade_factors = pd.read_excel(
            os.path.join(path_to_dir, 'data', 'gdpgrowth.xlsx'),
            engine='openpyxl'
        ).set_index(
            'CountryGroupName'
        )

        restricted_df['DENOMINATOR'] = (
            restricted_df['P/L before tax\nm USD 2016'].fillna(0)
            * upgrade_factors.loc['European Union', 'uprusd2116'] * restricted_df['IS_ETR_2016_VALID']
        )

        restricted_df['NUMERATOR'] = (
            restricted_df['Taxation\nm USD 2016'].fillna(0)
            * upgrade_factors.loc['European Union', 'uprusd2116'] * restricted_df['IS_ETR_2016_VALID']
        )

        range_temp = range(2017, 2022) if not exclude_COVID_years else range(2017, 2020)
        for year in range_temp:
            upgrade_factor = upgrade_factors.loc['European Union', f'uprusd21{year - 2000}']

            restricted_df['DENOMINATOR'] += (
                restricted_df[f'P/L before tax\nm USD {year}'].fillna(0)
                * restricted_df[f'IS_ETR_{year}_VALID']
                * upgrade_factor  # Applying the upgrade factor
            )

            restricted_df['NUMERATOR'] += (
                restricted_df[f'Taxation\nm USD {year}'].fillna(0)
                * restricted_df[f'IS_ETR_{year}_VALID']
                * upgrade_factor  # Applying the upgrade factor
            )

        # We deduce ETRs
        restricted_df['ETR'] = restricted_df['NUMERATOR'] / restricted_df['DENOMINATOR']

        # In a few cases, negative total taxes paid yield a negative ETR, which we bring to 0
        # restricted_df['ETR'] = restricted_df['ETR'].map(lambda x: max(x, 0))
        # Not useful now that we require positive taxes for the ETR to be deemed valid

        if restricted_df['ETR'].isnull().sum() > 0:
            print('Missing values remain when computing average ETRs.')

        # We restrict the table to the relevant fields
        restricted_df = restricted_df[['Company name Latin alphabet', 'ETR']].copy()

        return restricted_df.copy()


if __name__ == '__main__':

    path_to_output_file = sys.argv[1]

    final_output = {}

    for year in [2016, 2017, 2018]:
        calculator = TaxDeficitCalculator(year=year, fetch_data_online=self.fetch_data_online)
        calculator.load_clean_data()

        for rate in [15, 21, 25, 30]:
            key = f'total_TD_{rate}%_{year}'
            value = calculator.get_total_tax_deficits(minimum_ETR=rate / 100)

            final_output[key] = value.copy()

        for rate in [15, 21, 25, 30]:
            key = f'decomposed_{rate}%_{year}'
            value = calculator.compute_all_tax_deficits(minimum_ETR=rate / 100)

            final_output[key] = value.copy()

        final_output[f'unilateral_25%_{year}'] = calculator.check_unilateral_scenario_gain_computations()
        final_output[f'partial_25%_{year}'] = calculator.compute_intermediary_scenario_gain()

    with pd.ExcelWriter(path_to_output_file, engine='xlsxwriter') as writer:
        for key, value in final_output.items():
            value.to_excel(writer, sheet_name=key, index=False)
