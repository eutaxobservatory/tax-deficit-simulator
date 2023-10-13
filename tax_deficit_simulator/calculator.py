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
import re
import warnings

from tax_deficit_simulator.utils import rename_partner_jurisdictions, manage_overlap_with_domestic, \
    impute_missing_carve_out_values, load_and_clean_twz_main_data, load_and_clean_twz_CIT, \
    load_and_clean_bilateral_twz_data, get_avg_of_available_years, find_closest_year_available, \
    apply_upgrade_factor, online_data_paths, get_growth_rates, country_name_corresp


# ----------------------------------------------------------------------------------------------------------------------
# --- Defining paths to data files and other utils

path_to_dir = os.path.dirname(os.path.abspath(__file__))

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')


# ----------------------------------------------------------------------------------------------------------------------
# --- Defining the TaxDeficitCalculator class

class TaxDeficitCalculator:

    # ------------------------------------------------------------------------------------------------------------------
    # --- INSTANTIATING METHOD -----------------------------------------------------------------------------------------

    def __init__(
        self,
        year=2017,
        alternative_imputation=True,
        non_haven_TD_imputation_selection='EU',
        sweden_treatment='adjust',
        belgium_treatment='replace',
        SGP_CYM_treatment='replace',
        China_treatment_2018='none',
        use_adjusted_profits=True,
        average_ETRs=True,
        years_for_avg_ETRs=[2016, 2017, 2018],
        carve_outs=False,
        carve_out_rate_assets=None, carve_out_rate_payroll=None,
        depreciation_only=None, exclude_inventories=None, payroll_premium=20,
        ex_post_ETRs=False,
        de_minimis_exclusion=True,
        add_AUT_AUT_row=True,
        extended_dividends_adjustment=False,
        use_TWZ_for_CbCR_newcomers=False,
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

        self.load_xchange_growth_rates()

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

        if average_ETRs and (years_for_avg_ETRs is None or len(years_for_avg_ETRs) == 0):
            raise Exception('To use mean ETRs, you must specify a set of year(s) over which ETRs should be averaged.')

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

        if year == 2018 and China_treatment_2018 == 'none':
            raise Exception(
                "To run the computations on 2018 data, you must specify the approach for China,"
                + " which does not provide aggregated country-by-country report statistics that year."
            )

        if (
            year == 2018 or (average_ETRs and 2018 in years_for_avg_ETRs)
        ) and China_treatment_2018 not in ['TWZ', '2017_CbCR']:
            raise Exception(
                "For 2018, two options are available to deal with the absence of Chinese CbCR data: either using TWZ"
                + " data only ('TWZ') or using 2017 CbCR data ('2017_CbCR'), to which we apply the appropriate exchange"
                + " rate and upgrade factor."
            )

        if use_TWZ_for_CbCR_newcomers and year == 2016:
            raise Exception(
                "The argument 'use_TWZ_for_CbCR_newcomers' can only be used as of 2017. If it is set to True, we do as"
                + " if countries reporting CbCR data in the year considered but not in the previous one were absent"
                + " from the OECD's data and required the use of TWZ data (except for tax havens). Purely"
                + " methodological detail to challenge our use of TWZ data."
            )

        self.fetch_data_online = fetch_data_online

        if self.fetch_data_online:
            # URL to the list of EU-28 and EU-27 country codes from a .csv file
            path_to_eu_countries = online_data_paths['path_to_eu_countries']

            # URL to the list of tax havens' alpha-3 country codes from a .csv file
            path_to_tax_haven_list = online_data_paths['path_to_tax_haven_list']

            # URL to country codes
            self.path_to_geographies = online_data_paths['path_to_geographies']

        else:
            # Local path to the list of EU-28 and EU-27 country codes from a .csv file in the data folder
            path_to_eu_countries = os.path.join(path_to_dir, 'data', 'listofeucountries_csv.csv')

            # Local path to list of tax havens' alpha-3 country codes from a .csv file in the data folder
            path_to_tax_haven_list = os.path.join(path_to_dir, 'data', 'tax_haven_list.csv')

            # Local path to country codes
            self.path_to_geographies = os.path.join(path_to_dir, 'data', 'geographies.csv')

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
        GDP_growth_rates = self.growth_rates.set_index('CountryGroupName')

        self.average_ETRs_bool = average_ETRs
        self.years_for_avg_ETRs = years_for_avg_ETRs
        self.deflator_2016_to_2018 = GDP_growth_rates.loc['World', 'uprusd1816']
        self.deflator_2017_to_2018 = GDP_growth_rates.loc['World', 'uprusd1817']

        self.de_minimis_exclusion = de_minimis_exclusion

        self.extended_dividends_adjustment = extended_dividends_adjustment

        self.use_TWZ_for_CbCR_newcomers = use_TWZ_for_CbCR_newcomers

        self.sweden_adj_ratio_2016 = (342 - 200) / 342
        self.sweden_adj_ratio_2017 = (512 - 266) / 512
        self.sweden_adj_ratio_2018 = (49.1 - 29.8) / 49.1

        # Average exchange rate over the relevant year, extracted from benchmark computations run on Stata
        # Source: European Central Bank
        xrates = self.xrates.set_index('year')
        self.USD_to_EUR = 1 / xrates.loc[self.year, 'usd']

        self.China_treatment_2018 = China_treatment_2018

        if year == 2016:

            # Gross growth rate of worldwide GDP in current EUR between 2016 and 2021
            # Extracted from the benchmark computations run on Stata
            self.multiplier_2021 = GDP_growth_rates.loc['World', 'upreur2116']

            self.COUNTRIES_WITH_MINIMUM_REPORTING = ['KOR', 'NLD', 'IRL', 'FIN']
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
                self.belgium_partners_for_adjustment = ['NLD']
                self.belgium_years_for_adjustment = [2017]

            elif self.belgium_treatment == 'replace':
                self.belgium_partners_for_replacement = ['NLD']
                self.belgium_years_for_replacement = [2017]

                self.belgium_GDP_growth_multipliers = [1 / GDP_growth_rates.loc['European Union', 'uprusd1716']]

            self.add_AUT_AUT_row = add_AUT_AUT_row

        elif year == 2017:

            # Gross growth rate of worldwide GDP in current EUR between 2017 and 2021
            # Extracted from the benchmark computations run on Stata
            self.multiplier_2021 = GDP_growth_rates.loc['World', 'upreur2117']

            self.COUNTRIES_WITH_MINIMUM_REPORTING = ['KOR', 'NLD', 'IRL', 'FIN']
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
                self.belgium_partners_for_adjustment = ['GBR']
                self.belgium_years_for_adjustment = [2016]

            elif self.belgium_treatment == 'replace':
                self.belgium_partners_for_replacement = ['GBR']
                self.belgium_years_for_replacement = [2016]

                self.belgium_GDP_growth_multipliers = [GDP_growth_rates.loc['European Union', 'uprusd1716']]

            if self.SGP_CYM_treatment == 'replace':
                self.SGP_CYM_GDP_growth_multiplier = GDP_growth_rates.loc['World', 'uprusd1716']

            self.add_AUT_AUT_row = add_AUT_AUT_row

        elif year == 2018:

            # Gross growth rate of worldwide GDP in current EUR between 2018 and 2021
            # Extracted from the benchmark computations run on Stata
            self.multiplier_2021 = GDP_growth_rates.loc['World', 'upreur2118']

            self.COUNTRIES_WITH_MINIMUM_REPORTING = ['KOR', 'NZL', 'IRL', 'FIN']
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

            if self.China_treatment_2018 == '2017_CbCR':
                self.USD_to_EUR_2017 = 1 / xrates.loc[2017, 'usd']
                self.multiplier_2017_2021 = GDP_growth_rates.loc['World', 'upreur2117']

            if self.belgium_treatment == 'adjust':
                self.belgium_partners_for_adjustment = ['GBR', 'NLD']
                self.belgium_years_for_adjustment = [2016, 2017]

            elif self.belgium_treatment == 'replace':
                self.belgium_partners_for_replacement = ['GBR', 'NLD']
                self.belgium_years_for_replacement = [2016, 2017]

                self.belgium_GDP_growth_multipliers = [
                    GDP_growth_rates.loc['European Union', 'uprusd1816'],
                    GDP_growth_rates.loc['European Union', 'uprusd1817']
                ]

            self.add_AUT_AUT_row = add_AUT_AUT_row

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

            if self.year == 2018 and self.China_treatment_2018 == '2017_CbCR':

                self.exclusion_threshold_revenues_China = 10 * 10**6 / self.USD_to_EUR_2017
                self.exclusion_threshold_profits_China = 1 * 10**6 / self.USD_to_EUR_2017

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

    # ------------------------------------------------------------------------------------------------------------------
    # --- DATA PREPARATION ---------------------------------------------------------------------------------------------

    def load_xchange_growth_rates(self):

        path_to_data = os.path.join(path_to_dir, "data")

        # --- Exchange rates

        raw_data = pd.read_csv(os.path.join(path_to_data, "eurofxref-hist.csv"))

        raw_data = raw_data[['Date', 'USD']].copy()
        raw_data['YEAR'] = raw_data['Date'].map(lambda date: date[:date.find('-')]).astype(int)
        raw_data = raw_data[np.logical_and(raw_data['YEAR'] >= 2012, raw_data['YEAR'] <= 2022)].copy()

        average_exchange_rates = raw_data.groupby('YEAR').agg({'USD': 'mean'}).reset_index()
        average_exchange_rates = average_exchange_rates.rename(columns={"YEAR": "year", "USD": "usd"})

        self.xrates = average_exchange_rates.copy()

        # --- Growth rates

        raw_data = pd.read_excel(
            os.path.join(path_to_data, "WEOOct2021group.xlsx"),
            engine="openpyxl"
        )

        raw_data = raw_data[raw_data["Country Group Name"].isin(["European Union", "World"])].copy()
        raw_data = raw_data[raw_data["Subject Descriptor"] == "Gross domestic product, current prices"].copy()
        raw_data = raw_data[raw_data["Units"] == "U.S. dollars"].copy()

        # Extracting relevant values for GDP in USD
        extract = raw_data[
            ["Country Group Name", "Units"] + [f"y{year}" for year in range(2012, 2023)]
        ].reset_index(drop=True).copy()

        # Deducing GDP in EUR by adding exchange rates
        exchange_rates_temp = average_exchange_rates.set_index("year")

        for year in range(2012, 2023):
            extract[f"eurgdp{year}"] = extract[f"y{year}"] / exchange_rates_temp.loc[year, "usd"]

        # One-year, two-year, and three-year growth rates for USD and EUR GDP
        for t in range(16, 23):
            # One-year growth rates
            t_1 = t - 1
            # GDP in USD
            extract[f"uprusd{t}{t_1}"] = extract[f"y20{t}"] / extract[f"y20{t_1}"]
            # GDP in EUR
            extract[f"upreur{t}{t_1}"] = extract[f"eurgdp20{t}"] / extract[f"eurgdp20{t_1}"]

            # Two-year growth rates
            t_2 = t - 2
            # GDP in USD
            extract[f"uprusd{t}{t_2}"] = extract[f"y20{t}"] / extract[f"y20{t_2}"]
            # GDP in EUR
            extract[f"upreur{t}{t_2}"] = extract[f"eurgdp20{t}"] / extract[f"eurgdp20{t_2}"]

            # Three-year growth rates
            t_3 = t - 3
            # GDP in USD
            extract[f"uprusd{t}{t_3}"] = extract[f"y20{t}"] / extract[f"y20{t_3}"]
            # GDP in EUR
            extract[f"upreur{t}{t_3}"] = extract[f"eurgdp20{t}"] / extract[f"eurgdp20{t_3}"]

        # Growth rates to 2021 in EUR and USD
        for t in [12] + list(range(16, 23)):
            # GDP in USD
            extract[f"uprusd21{t}"] = extract["y2021"] / extract[f"y20{t}"]
            # GDP in EUR
            extract[f"upreur21{t}"] = extract["eurgdp2021"] / extract[f"eurgdp20{t}"]

        # Growth rates to 2020 in EUR and USD
        for t in [16, 17]:
            # GDP in USD
            extract[f"uprusd20{t}"] = extract["y2020"] / extract[f"y20{t}"]
            # GDP in EUR
            extract[f"upreur20{t}"] = extract["eurgdp2020"] / extract[f"eurgdp20{t}"]

        columns = ["Country Group Name"] + list(
            extract.columns[extract.columns.map(lambda col: col.startswith("upr"))]
        )

        extract = extract[columns].copy()
        extract = extract.rename(columns={"Country Group Name": "CountryGroupName"})

        self.growth_rates = extract.copy()

    def load_clean_ILO_data(self):

        employee_population = self.employee_population.copy()
        earnings = self.earnings.copy()

        # --- Cleaning ILO data on employee population

        # Renaming columns
        employee_population = employee_population.rename(
            columns={
                'ref_area.label': 'countryname',
                'time': 'year'
            }
        )

        # Selecting relevant observations
        # All genders
        employee_population = employee_population[employee_population['sex.label'] == 'Sex: Total'].copy()
        employee_population = employee_population.drop(columns=['sex.label'])
        employee_population['sex'] = 'to'
        # Focusing on wage employees
        employee_population = employee_population[
            employee_population['classif1.label'] == 'Status in employment (Aggregate): Employees'
        ].copy()
        employee_population = employee_population.drop(columns=['classif1.label'])
        employee_population['status'] = 'wage'

        # Selecting relevant columns
        employee_population = employee_population[['year', 'countryname', 'obs_value', 'status']].copy()

        # Renaming the column with the values of interest
        employee_population = employee_population.rename(columns={'obs_value': 'emp'})

        # Focusing on the relevant year
        employee_population = employee_population[employee_population['year'] == self.year].copy()

        # --- Cleaning ILO data on mean earnings

        # Selecting relevant observations
        # All sectors
        earnings = earnings[earnings['classif1.label'].map(lambda label: 'Total' in label)].copy()
        # Focusing on current USD for the currency
        earnings = earnings[earnings['classif2.label'].map(lambda label: 'U.S. dollars' in label)].copy()
        # All genders
        earnings = earnings[earnings['sex.label'] == 'Sex: Total'].copy()
        # Recent years
        earnings = earnings[earnings['time'] >= 2014].copy()

        # Selecting columns of interest with relevant variable names
        earnings = earnings.drop(
            columns=[
                'source.label', 'sex.label', 'classif2.label', 'note_classif.label',
                'indicator.label', 'note_indicator.label', 'note_source.label'
            ]
        )
        earnings = earnings.rename(columns={'time': 'year', 'ref_area.label': 'country', 'classif1.label': 'type'})

        # Managing the different industry classifications
        # Simplifying the names of the different classifications
        earnings['type'] = earnings['type'].map(lambda string: re.findall('\((.+)\)', string)[0])
        earnings['type'] = earnings['type'].map(lambda string: string.replace('.', '').replace('-', ''))
        # Moving from long to wide format
        earnings = earnings.pivot(index=['country', 'year'], columns=['type'], values=['obs_value'])
        earnings.columns = earnings.columns.droplevel()
        earnings = earnings.reset_index()
        # Do we find different figures from a classification to another?
        earnings['check'] = earnings['Aggregate'] - earnings['ISICRev2']
        earnings['check'] = earnings.apply(
            lambda row: row['Aggregate'] - row['ISICRev31'] if np.isnan(row['check']) else row['check'],
            axis=1
        )
        earnings['check'] = earnings.apply(
            lambda row: row['Aggregate'] - row['ISICRev4'] if np.isnan(row['check']) else row['check'],
            axis=1
        )
        # Only issues: Canada in 2019 and Uganda in 2017
        # earnings[np.logical_and(earnings['check'] != 0, ~earnings['check'].isnull())]
        # We select values in that order: ISICRev4, ISICRev31, ISICRev2, Aggregate
        earnings['earn'] = earnings['ISICRev4']
        earnings['earn'] = earnings.apply(
            lambda row: row['ISICRev31'] if np.isnan(row['earn']) else row['earn'],
            axis=1
        )
        earnings['earn'] = earnings.apply(
            lambda row: row['ISICRev2'] if np.isnan(row['earn']) else row['earn'],
            axis=1
        )
        earnings['earn'] = earnings.apply(
            lambda row: row['Aggregate'] if np.isnan(row['earn']) else row['earn'],
            axis=1
        )

        # Correcting a small issue in the data
        earnings['earn'] = earnings.apply(
            lambda row: row['earn'] / 10 if row['country'] == 'Thailand' and row['year'] == 2017 else row['earn'],
            axis=1
        )

        # Distinction based on whether the year of interest is available
        earnings_directly_available = earnings[earnings['year'] == self.year].copy()
        earnings_not_available = earnings[
            ~earnings['country'].isin(
                earnings_directly_available['country'].unique()
            )
        ].copy()

        # Further distinction based on whether the interpolation is feasible
        earnings_not_available['help'] = earnings_not_available['year'] < self.year
        earnings_not_available['help2'] = earnings_not_available['year'] > self.year

        temp = earnings_not_available.groupby(by='country').sum()[['help', 'help2']].reset_index()
        countries_feasible_interpolation = temp[
            np.logical_and(temp['help'] > 0, temp['help2'] > 0)
        ]['country'].unique()

        earnings_not_available = earnings_not_available.drop(
            columns=['Aggregate', 'ISICRev2', 'ISICRev31', 'ISICRev4']
        )

        earnings_feasible_countries = earnings_not_available[
            earnings_not_available['country'].isin(countries_feasible_interpolation)
        ].copy()

        # Interpolation [CRITICAL STEP]
        # Sorting values from the oldest to the latest for each country
        earnings_feasible_countries = earnings_feasible_countries.sort_values(by=['country', 'year'])
        # Indexing by year in a datetime format
        earnings_feasible_countries['year'] = pd.to_datetime(earnings_feasible_countries['year'], format='%Y')
        earnings_feasible_countries = earnings_feasible_countries.set_index('year')
        # Computing the interpolation values
        df_interpol = earnings_feasible_countries.groupby(['country']).resample('A').mean()
        df_interpol['earn_ipo'] = df_interpol['earn'].interpolate()
        df_interpol = df_interpol.reset_index()
        df_interpol['year'] = df_interpol['year'].dt.year
        # Restricting to the year of interest
        df_interpol = df_interpol[df_interpol['year'] == self.year].copy()
        # Focusing on the columns of interest with some renaming
        df_interpol = df_interpol[['country', 'year', 'earn_ipo']].copy()
        df_interpol = df_interpol.rename(columns={'earn_ipo': 'earn'})
        # Dummy indicating whether the value was obtained via interpolation
        df_interpol['ipo'] = 1

        # Gathering earnings directly available and interpolated values
        earnings_interpolated = pd.concat(
            [earnings_directly_available, df_interpol],
            axis=0
        )[
            ['country', 'year', 'earn', 'ipo']
        ].reset_index(drop=True)
        # Completing the dummy variable
        earnings_interpolated['ipo'] = earnings_interpolated['ipo'].fillna(0)

        # Moving from monthly to annual earnings
        earnings_interpolated['earn'] *= 12

        # Renaming column showing the country
        earnings_interpolated = earnings_interpolated.rename(columns={'country': 'countryname'})

        # --- Finalising the preparation of ILO data

        # Merging earnings with population
        earnings_merged = earnings_interpolated.merge(
            employee_population,
            on=['countryname', 'year'],
            how='left'
        )

        # Adding country codes and continents
        # Manually editing one of the country names, otherwise not found in the file with correspondences
        earnings_merged['countryname'] = earnings_merged['countryname'].map(
            lambda country_name: {'Moldova, Republic of': 'Moldova'}.get(country_name, country_name)
        )
        # Merging with the file with correspondences
        earnings_merged = earnings_merged.merge(
            pd.read_csv(self.path_to_geographies),
            left_on='countryname', right_on='NAME',
            how='left'
        )
        # Renaming some columns, removing some others
        earnings_merged = earnings_merged.rename(
            columns={
                'CONTINENT_NAME': 'GEO',
                'CODE': 'partner'
            }
        ).drop(columns=['NAME', 'CONTINENT_CODE'])
        # Gathering South America and North America
        earnings_merged['GEO'] = earnings_merged['GEO'].map(
            lambda continent: {'South America': 'Americas', 'North America': 'Americas'}.get(continent, continent)
        )

        # Computing each country's population weight
        earnings_merged['wgt'] = earnings_merged['emp'] / earnings_merged['emp'].sum()

        # Row with the global mean earnings
        additional_rows = {
            'countryname': [''] * 2,
            'year': [self.year] * 2,
            'earn': [np.sum(earnings_merged['wgt'] * earnings_merged['earn'])] * 2,
            'ipo': [1] * 2,
            'emp': [np.nan] * 2,
            'status': ['wage'] * 2,
            'partner': ['FJT', 'GRPS'],
            'GEO': [''] * 2
        }
        additional_rows = pd.DataFrame(additional_rows)

        # Continent-level mean earnings
        regional_extract = earnings_merged.copy()
        regional_extract['numerator'] = regional_extract['earn'] * regional_extract['emp']
        # Correcting a few continents to match Stata outputs
        regional_extract['GEO'] = regional_extract.apply(
            lambda row: 'Europe' if row['countryname'] == 'Russian Federation' else row['GEO'],
            axis=1
        )
        regional_extract['GEO'] = regional_extract.apply(
            lambda row: 'Asia' if row['countryname'] == 'Cyprus' else row['GEO'],
            axis=1
        )
        regional_extract = regional_extract.groupby('GEO').sum()[['emp', 'numerator']]
        regional_extract['earn'] = regional_extract['numerator'] / regional_extract['emp']
        regional_extract = regional_extract.reset_index()

        # First auxiliary table used for countries with continental CbCRs
        # and to impute the missing values for countries that do not display data on earnings
        regional_extract1 = regional_extract.copy()
        regional_extract1['partner'] = regional_extract1['GEO'].map(
            {
                'Africa': 'AFRIC',
                'Europe': 'EUROP',
                'Asia': 'ASIAT',
                'Americas': 'AMER',
                'Oceania': 'OCEAN'
            }
        )
        regional_extract1['year'] = self.year
        regional_extract1['countryname'] = ''
        regional_extract1['ipo'] = 0
        regional_extract1['status'] = 'wage'
        regional_extract1['ipo'] = 0
        regional_extract1 = regional_extract1.drop(columns=['numerator'])

        # Second auxiliary table used to provide mean earnings for the regional aggregates in CbCR data
        regional_extract2 = regional_extract[regional_extract['GEO'] != 'Oceania'].copy()
        regional_extract2['partner'] = regional_extract2['GEO'].map(
            {
                'Africa': 'OAF',
                'Europe': 'OTE',
                'Asia': 'OAS',
                'Americas': 'OAM',
            }
        )
        regional_extract2['year'] = self.year
        regional_extract2['countryname'] = ''
        regional_extract2['status'] = 'wage'
        regional_extract2['ipo'] = 0
        regional_extract2 = regional_extract2.drop(columns=['numerator'])
        regional_extract2.head()

        # Gathering all the required data
        earnings_merged = earnings_merged.drop(columns=['wgt'])

        main_ILO_df = pd.concat([earnings_merged, additional_rows, regional_extract1, regional_extract2], axis=0)
        main_ILO_df = main_ILO_df.rename(columns={'partner': 'partner2'})
        main_ILO_df = main_ILO_df[['year', 'earn', 'partner2', 'GEO']].copy()

        continental_imputation_df = regional_extract1[['year', 'earn', 'partner', 'GEO']].copy()
        continental_imputation_df = continental_imputation_df.rename(
            columns={'GEO': 'CONTINENT_NAME', 'partner': 'CONTINENT_CODE'}
        )

        return main_ILO_df.copy(), continental_imputation_df.copy()

    def get_average_CbCR_ETRs(
        self, years
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
            lambda row: rename_partner_jurisdictions(
                row,
                COUNTRIES_WITH_MINIMUM_REPORTING=self.COUNTRIES_WITH_MINIMUM_REPORTING,
                use_case='specific'
            ),
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

            # For the years eventually considered in the average ETRs, we get the Sweden adjustment ratio and apply it

            # For the other years, we apply no adjustment (multiplying by 1)
            # This has no influence on the computation of average ETRs since these observations are removed later on

            sweden_adj_ratios = {
                year: TaxDeficitCalculator(
                    year=year,
                    sweden_treatment='adjust',
                    add_AUT_AUT_row=False,
                    average_ETRs=False,
                    fetch_data_online=self.fetch_data_online,
                    China_treatment_2018=self.China_treatment_2018
                ).sweden_adjustment_ratio
                for year in self.years_for_avg_ETRs
            }

            for year in [2016, 2017, 2018]:
                if year not in self.years_for_avg_ETRs:
                    sweden_adj_ratios[year] = 1

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
            2016: self.deflator_2016_to_2018,
            2017: self.deflator_2017_to_2018,
            2018: 1
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

        # IMPORTANT NEW STEP: Before summing, we restrict ourselves to the set of years considered for the average
        oecd_temp = oecd_temp[oecd_temp['YEA'].isin(years)].copy()

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
            # url_base = online_data_paths['url_base']
            # file_name = f'iloearn{self.year - 2000}.csv'
            # path_to_preprocessed_mean_wages = url_base + file_name

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
            self.path_to_statutory_rates = os.path.join(path_to_dir, 'data', 'KPMG_statutoryrates.xlsx')

            # Path to ILO data
            self.path_to_employee_pop = os.path.join(
                path_to_dir, 'data', 'EMP_2EMP_SEX_STE_NB_A-filtered-2021-07-20.csv'
            )
            self.path_to_mean_earnings = os.path.join(
                path_to_dir, 'data', 'EAR_4MTH_SEX_ECO_CUR_NB_A-filtered-2021-07-06.csv'
            )

            # Path to TWZ data on profits booked in tax havens
            self.path_to_excel_file = os.path.join(path_to_dir, 'data', 'TWZ', str(self.year), 'TWZ.xlsx')

            # Path to TWZ data on profits booked domestically (with ETRs)
            path_to_twz_domestic = os.path.join(path_to_dir, 'data', 'TWZ', 'TWZ2020AppendixTables.xlsx')

        try:
            # We try to read the files from the provided paths
            oecd = pd.read_csv(self.path_to_oecd)

            self.employee_population = pd.read_csv(self.path_to_employee_pop)
            self.earnings = pd.read_csv(self.path_to_mean_earnings)

            preprocessed_mean_wages = pd.read_csv(
                os.path.join(path_to_dir, 'data', f'iloearn{self.year - 2000}.csv'),
                delimiter=(';' if self.year == 2016 else ',')
            )
            self.preprocessed_mean_wages = preprocessed_mean_wages.copy()

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
                engine='openpyxl',
                sheet_name='TableA6',
                usecols='A,K:L',
                skiprows=9,
                header=None,
                names=['COUNTRY_NAME', 'Domestic profits', 'Domestic ETR']
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

            self.belgium_ratios_for_adjustment = []

            for partner, year in zip(self.belgium_partners_for_adjustment, self.belgium_years_for_adjustment):

                temp = oecd[
                    np.logical_and(
                        oecd['COU'] == 'BEL',
                        oecd['JUR'] == partner
                    )
                ].copy()

                temp = temp[temp['CBC'].isin(['TOT_REV', 'PROFIT'])].copy()
                temp = temp[temp['Year'] == year].copy()

                temp = temp[['CBC', 'Value']].set_index('CBC')

                self.belgium_ratios_for_adjustment.append((temp.loc['PROFIT'] / temp.loc['TOT_REV'])['Value'])

        elif self.belgium_treatment == 'replace':

            self.belgium_data_for_replacement = []

            for partner, year, multiplier in zip(
                self.belgium_partners_for_replacement,
                self.belgium_years_for_replacement,
                self.belgium_GDP_growth_multipliers
            ):
                belgium_data_for_replacement = oecd[
                    np.logical_and(
                        oecd['COU'] == 'BEL',
                        np.logical_and(
                            oecd['JUR'] == partner,
                            oecd['YEA'] == year
                        )
                    )
                ].copy()

                mask = ~(belgium_data_for_replacement['CBC'] == 'EMPLOYEES')
                belgium_data_for_replacement['Value'] *= (mask * (multiplier - 1) + 1)

                self.belgium_data_for_replacement.append(belgium_data_for_replacement.copy())

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

        # Dealing with the case of China in 2018 if relevant
        if self.year == 2018 and self.China_treatment_2018 == "2017_CbCR":

            oecd['Year'] = oecd.apply(
                lambda row: 2018 if row['COU'] == 'CHN' and row['Year'] == 2017 else row['Year'],
                axis=1
            )

        # Removing newcomers if relevant
        if self.use_TWZ_for_CbCR_newcomers:

            reporting_countries = oecd[oecd['Year'] == self.year]['COU'].unique()
            reporting_countries_previous_year = oecd[oecd['Year'] == self.year - 1]['COU'].unique()
            newcomers = reporting_countries[~reporting_countries.isin(reporting_countries_previous_year)].copy()
            newcomers = newcomers[~newcomers.isin(self.tax_haven_country_codes)].copy()

            oecd = oecd[~np.logical_and(oecd['Year'] == self.year, oecd['COU'].isin(newcomers))].copy()

        # Restricting the data to the relevant income year
        oecd = oecd[oecd['Year'] == self.year].copy()

        # Dealing with Belgian data depending on the value of "belgium_treatment" - Applying the adjustment
        if self.belgium_treatment == 'replace':

            for partner, data in zip(self.belgium_partners_for_replacement, self.belgium_data_for_replacement):

                oecd = oecd[~np.logical_and(oecd['COU'] == 'BEL', oecd['JUR'] == partner)].copy()

                oecd = pd.concat([oecd, data], axis=0)

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
        oecd['Partner jurisdiction (whitespaces cleaned)'] = oecd.apply(
            lambda row: rename_partner_jurisdictions(
                row,
                COUNTRIES_WITH_MINIMUM_REPORTING=self.COUNTRIES_WITH_MINIMUM_REPORTING,
                use_case="normal"
            ),
            axis=1
        )

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

        # --- We clean the statutory corporate income tax rates
        # Selecting the relevant year
        statutory_rates = statutory_rates[['CODE', 'Country', self.year]].copy()
        # Adding the country code for Bonaire
        statutory_rates['CODE'] = statutory_rates.apply(
            lambda row: 'BES' if row['Country'].startswith('Bonaire') else row['CODE'],
            axis=1
        )
        # Dealing with missing values
        statutory_rates[self.year] = statutory_rates[self.year].map(lambda x: np.nan if x == '-' else x).astype(float)
        # Managing duplicates (equivalently to the Stata code)
        # Removing the EU average
        statutory_rates = statutory_rates[statutory_rates['Country'] != 'EU average'].copy()
        # If two rows display the same country code and the same rate, we keep only the first
        statutory_rates = statutory_rates.drop_duplicates(subset=['CODE', self.year], keep='first').copy()
        # In practice, only effect is to keep one row for Sint-Maarten which is the only other duplicated country code
        # Adding a simple check for duplicates
        if statutory_rates.duplicated(subset='CODE').sum() > 0:
            raise Exception('At least one duplicated country code remains in the table of statutory rates.')
        # Replacing continent codes to match the OECD's
        code_mapping_1 = {'EUROPE': 'EUROP', 'AMERICA': 'AMER', 'AFRICA': 'AFRIC', 'ASIA': 'ASIAT', 'GLOBAL': 'FJT'}
        code_mapping_2 = {'EUROP': 'OTE', 'AMER': 'OAM', 'AFRIC': 'OAF', 'ASIAT': 'OAS', 'FJT': 'GRPS'}
        statutory_rates['CODE'] = statutory_rates['CODE'].map(
            lambda code: code_mapping_1.get(code, code)
        )
        # Adding codes for the "Other [CONTINENT]" partners
        extract = statutory_rates[statutory_rates['CODE'].isin(code_mapping_2.keys())].copy()
        extract['CODE'] = extract['CODE'].map(
            lambda code: code_mapping_2.get(code, code)
        )
        statutory_rates = pd.concat([statutory_rates, extract], axis=0)
        # Dropping the column with country names
        statutory_rates = statutory_rates.drop(columns='Country')
        # Dividing rates by 100 to move from percentages to values between 0 and 1
        statutory_rates[self.year] /= 100
        # Renaming columns
        statutory_rates.rename(
            columns={
                'CODE': 'partner',
                self.year: 'statrate'
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

            for partner, ratio in zip(self.belgium_partners_for_adjustment, self.belgium_ratios_for_adjustment):

                oecd['Profit (Loss) before Income Tax'] = oecd.apply(
                    (
                        lambda row: row['Total Revenues'] * ratio
                        if row['Parent jurisdiction (alpha-3 code)'] == 'BEL'
                        and row['Partner jurisdiction (alpha-3 code)'] == partner
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
            average_ETRs_df = self.get_average_CbCR_ETRs(years=self.years_for_avg_ETRs)

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
                    row['Parent jurisdiction (alpha-3 code)'] in self.COUNTRIES_WITH_MINIMUM_REPORTING
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

            if self.year == 2018 and self.China_treatment_2018 == '2017_CbCR':

                revenue_threshold = oecd['Parent jurisdiction (alpha-3 code)'].map(
                    lambda country_code: {
                        'CHN': self.exclusion_threshold_revenues_China
                    }.get(country_code, self.exclusion_threshold_revenues)
                )

                profit_threshold = oecd['Parent jurisdiction (alpha-3 code)'].map(
                    lambda country_code: {
                        'CHN': self.exclusion_threshold_profits_China
                    }.get(country_code, self.exclusion_threshold_profits)
                )

            else:

                revenue_threshold = self.exclusion_threshold_revenues
                profit_threshold = self.exclusion_threshold_profits

            mask_revenues = (oecd['Total Revenues'] >= revenue_threshold)
            mask_profits = (oecd['Profit (Loss) before Income Tax'] >= profit_threshold)

            mask_de_minimis_exclusion = np.logical_or(mask_revenues, mask_profits)

            oecd = oecd[mask_de_minimis_exclusion].copy()

        # We need some more work on the data if we want to simulate substance-based carve-outs
        if self.carve_outs or self.behavioral_responses:

            main_ILO_df, continental_imputation_df = self.load_clean_ILO_data()

            # We merge earnings data with country-by-country data on partner jurisdiction codes

            # - Countries for which earnings (possibly obtained via interpolations) are directly available
            oecd = oecd.merge(
                main_ILO_df[['earn', 'partner2']],
                how='left',
                left_on='Partner jurisdiction (alpha-3 code)', right_on='partner2'
            ).drop(columns=['partner2'])

            # - Countries for which they are imputed based on continental weighted averages

            # Adding continent codes for the imputation
            oecd = oecd.merge(
                pd.read_csv(self.path_to_geographies)[['CODE', 'CONTINENT_CODE']].drop_duplicates(),
                how='left',
                left_on='Partner jurisdiction (alpha-3 code)', right_on='CODE'
            ).drop(columns=['CODE'])

            # Adapting the set of continent codes to ensure the correspondence
            oecd['CONTINENT_CODE'] = oecd['CONTINENT_CODE'].map(
                lambda continent: {
                    'NAMR': 'AMER',
                    'SAMR': 'AMER',
                    'EUR': 'EUROP',
                    'AFR': 'AFRIC',
                    'ASIA': 'ASIAT',
                    'OCN': 'OCEAN',
                    'ATC': 'AFRIC'  # For the specific case of the Bouvet Island (in India's CbCR)
                }.get(continent, continent)
            )
            oecd['CONTINENT_CODE'] = oecd.apply(
                lambda row: 'EUROP' if row['Partner jurisdiction (alpha-3 code)'] == 'RUS' else row['CONTINENT_CODE'],
                axis=1
            )
            oecd['CONTINENT_CODE'] = oecd.apply(
                lambda row: 'ASIAT' if row['Partner jurisdiction (alpha-3 code)'] == 'CYP' else row['CONTINENT_CODE'],
                axis=1
            )

            # Merging based on continent codes
            oecd = oecd.merge(
                continental_imputation_df[['CONTINENT_CODE', 'earn']].rename(columns={'earn': 'earn_avg_continent'}),
                how='left',
                on='CONTINENT_CODE'
            )

            # - We gather earnings available at the country level and continental imputations
            oecd['earn'] = oecd.apply(
                lambda row: row['earn'] if not np.isnan(row['earn']) else row['earn_avg_continent'],
                axis=1
            )

            oecd = oecd.drop(columns=['CONTINENT_CODE', 'earn_avg_continent'])

            self.oecd_temp = oecd.copy()

            # We merge earnings data with country-by-country data on partner jurisdiction codes
            # oecd = oecd.merge(
            #     self.preprocessed_mean_wages[['partner2', 'earn']],
            #     how='left',
            #     left_on='Partner jurisdiction (alpha-3 code)', right_on='partner2'
            # )

            # oecd.drop(columns=['partner2'], inplace=True)

            oecd.rename(
                columns={
                    'earn': 'ANNUAL_VALUE'
                },
                inplace=True
            )

            # We clean the mean annual earnings column
            # oecd['ANNUAL_VALUE'] = oecd['ANNUAL_VALUE'].map(
            #     lambda x: x.replace(',', '.') if isinstance(x, str) else x
            # ).astype(float)

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

        # Dropping some rows at the bottom of the table without any data or country name
        twz_domestic = twz_domestic.dropna(subset=['Domestic profits', 'Domestic ETR'], how='all').copy()
        twz_domestic = twz_domestic.dropna(subset=['COUNTRY_NAME']).copy()

        # Removes intermediary totals ("Main developing countries", "Non-OECD tax havens", etc.)
        twz_domestic = twz_domestic[
            ~twz_domestic['COUNTRY_NAME'].map(
                lambda name: (
                    'countries' in name.lower() or 'havens' in name.lower() or 'world' in name.lower()
                )
            )
        ].copy()

        # "Correcting" some country names so that we can add alpha-3 codes
        twz_domestic['COUNTRY_NAME'] = twz_domestic['COUNTRY_NAME'].map(
            lambda name: country_name_corresp.get(name, name)
        )

        # Adding country codes
        geographies = pd.read_csv(self.path_to_geographies)

        twz_domestic = twz_domestic.merge(
            geographies[['NAME', 'CODE']].drop_duplicates(),
            how='left',
            left_on='COUNTRY_NAME', right_on='NAME'
        ).rename(
            columns={'CODE': 'Alpha-3 country code'}
        ).drop(
            columns=['NAME', 'COUNTRY_NAME']
        )

        # Simple check that we are not missing any country code
        if twz_domestic['Alpha-3 country code'].isnull().sum() > 0:
            raise Exception('We are missing some country codes when loading TWZ data on domestic activities.')

        # Upgrading profits from 2015 to the relevant year
        GDP_growth_rates = self.growth_rates.set_index('CountryGroupName')

        twz_domestic['IS_EU'] = twz_domestic['Alpha-3 country code'].isin(self.eu_27_country_codes) * 1
        twz_domestic['MULTIPLIER'] = twz_domestic['IS_EU'].map(
            {
                0: GDP_growth_rates.loc['World', f'uprusd{self.year - 2000}15'],
                1: GDP_growth_rates.loc['European Union', f'uprusd{self.year - 2000}15']
            }
        )
        twz_domestic['Domestic profits'] *= twz_domestic['MULTIPLIER']

        twz_domestic = twz_domestic.drop(columns=['IS_EU', 'MULTIPLIER'])

        # Replacing the ETR for Germany (taken from OECD's CBCR average ETR [--> TO BE UPDATED?])
        twz_domestic['Domestic ETR'] = twz_domestic.apply(
            lambda row: 0.2275 if row['Alpha-3 country code'] == 'DEU' else row['Domestic ETR'],
            axis=1
        )

        # After this line, figures are expressed in plain USD
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

    # ------------------------------------------------------------------------------------------------------------------
    # --- BASIC TAX DEFICIT COMPUTATIONS -------------------------------------------------------------------------------

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
                China_treatment_2018=self.China_treatment_2018,
                use_adjusted_profits=self.use_adjusted_profits,
                average_ETRs=self.average_ETRs_bool,
                years_for_avg_ETRs=self.years_for_avg_ETRs,
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
                use_TWZ_for_CbCR_newcomers=self.use_TWZ_for_CbCR_newcomers,
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
                self.COUNTRIES_WITH_MINIMUM_REPORTING + self.COUNTRIES_WITH_CONTINENTAL_REPORTING
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

    def get_alternative_non_haven_factor(self, minimum_ETR, ETR_increment=0):
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
                China_treatment_2018=self.China_treatment_2018,
                use_adjusted_profits=self.use_adjusted_profits,
                average_ETRs=self.average_ETRs_bool,
                years_for_avg_ETRs=self.years_for_avg_ETRs,
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
                use_TWZ_for_CbCR_newcomers=self.use_TWZ_for_CbCR_newcomers,
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
                minimum_ETR=self.reference_rate_for_alternative_imputation, ETR_increment=0
            )

        else:
            oecd_stratified = self.get_stratified_oecd_data(
                minimum_ETR=self.reference_rate_for_alternative_imputation, ETR_increment=0
            )

        # We exclude countries whose CbCR breakdown does not allow to distinguish tax-haven and non-haven profits
        df_restricted = oecd_stratified[
            ~oecd_stratified['Parent jurisdiction (alpha-3 code)'].isin(
                self.COUNTRIES_WITH_CONTINENTAL_REPORTING + self.COUNTRIES_WITH_MINIMUM_REPORTING
            )
        ].copy()

        # The denominator is the total non-haven tax deficit of relevant countries at the reference minimum ETR
        denominator = df_restricted['tax_deficit_x_non_haven'].sum()

        # We follow the same process, running computations at the minimum ETR this time
        if self.behavioral_responses:
            oecd_stratified = calculator_temp.get_stratified_oecd_data(
                minimum_ETR=minimum_ETR, ETR_increment=ETR_increment
            )

        else:
            oecd_stratified = self.get_stratified_oecd_data(
                minimum_ETR=minimum_ETR, ETR_increment=ETR_increment
            )

        # We exclude countries whose CbCR breakdown does not allow to distinguish tax-haven and non-haven profits
        df_restricted = oecd_stratified[
            ~oecd_stratified['Parent jurisdiction (alpha-3 code)'].isin(
                self.COUNTRIES_WITH_CONTINENTAL_REPORTING + self.COUNTRIES_WITH_MINIMUM_REPORTING
            )
        ].copy()

        # The numerator is the total non-haven tax deficit of relevant countries at the selected minimum ETR
        numerator = df_restricted['tax_deficit_x_non_haven'].sum()

        return numerator / denominator

    def get_stratified_oecd_data(self, minimum_ETR=0.25, exclude_non_EU_domestic_TDs=True, ETR_increment=0):
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
        # oecd = oecd[oecd['ETR'] < minimum_ETR].copy()

        # We compute the ETR differential for all low-taxed profits
        oecd['ETR'] += ETR_increment
        oecd['ETR_differential'] = oecd['ETR'].map(lambda x: max(minimum_ETR - x, 0))

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
        if exclude_non_EU_domestic_TDs:
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
        save_countries_replaced=True,
        exclude_non_EU_domestic_TDs=True,
        upgrade_to_2021=True
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
        oecd_stratified = self.get_stratified_oecd_data(
            minimum_ETR=minimum_ETR, exclude_non_EU_domestic_TDs=exclude_non_EU_domestic_TDs
        )

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
                years_for_avg_ETRs=self.years_for_avg_ETRs,
                fetch_data_online=self.fetch_data_online,
                sweden_treatment=self.sweden_treatment,
                belgium_treatment=self.belgium_treatment,
                SGP_CYM_treatment=self.SGP_CYM_treatment,
                China_treatment_2018=self.China_treatment_2018,
                use_TWZ_for_CbCR_newcomers=self.use_TWZ_for_CbCR_newcomers,
            )
            calculator.load_clean_data()
            _ = calculator.compute_all_tax_deficits(minimum_ETR=minimum_ETR, upgrade_to_2021=upgrade_to_2021)

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
        if exclude_non_EU_domestic_TDs:
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
        # twz_not_in_oecd = twz_not_in_oecd.merge(
        #     twz_domestic[['Alpha-3 country code', 'tax_deficit_x_domestic']],
        #     how='left',
        #     on='Alpha-3 country code'
        # )
        twz_domestic = twz_domestic[
            ~twz_domestic['Alpha-3 country code'].isin(self.oecd['Parent jurisdiction (alpha-3 code)'])
        ].copy()
        twz_not_in_oecd = twz_not_in_oecd.merge(
            twz_domestic[['Alpha-3 country code', 'tax_deficit_x_domestic']],
            how='outer',
            on='Alpha-3 country code'
        )

        # BES is in domestic TWZ data but not in tax haven TWZ data (at least for 2018)
        twz_not_in_oecd['Country'] = twz_not_in_oecd.apply(
            lambda row: 'Bonaire' if row['Alpha-3 country code'] == 'BES' else row['Country'],
            axis=1
        )
        twz_not_in_oecd['tax_deficit_x_tax_haven_TWZ'] = twz_not_in_oecd['tax_deficit_x_tax_haven_TWZ'].fillna(0)
        twz_not_in_oecd['tax_deficit_x_domestic'] = twz_not_in_oecd['tax_deficit_x_domestic'].fillna(0)
        twz_not_in_oecd['tax_deficit_x_non_haven'] = twz_not_in_oecd['tax_deficit_x_non_haven'].fillna(0)

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

            if upgrade_to_2021:

                if self.year == 2018 and self.China_treatment_2018 == "2017_CbCR":

                    multiplier = merged_df['Parent jurisdiction (alpha-3 code)'] == 'CHN'
                    multiplier *= self.USD_to_EUR_2017 * self.multiplier_2017_2021
                    multiplier = multiplier.map(
                        lambda x: self.USD_to_EUR * self.multiplier_2021 if x == 0 else x
                    )

                else:

                    multiplier = self.USD_to_EUR * self.multiplier_2021

            else:

                if self.year == 2018 and self.China_treatment_2018 == "2017_CbCR":

                    multiplier = merged_df['Parent jurisdiction (alpha-3 code)'] == 'CHN'

                    multiplier *= self.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                    multiplier = multiplier.map(lambda x: 1 if x == 0 else x)

                else:

                    multiplier = 1

            merged_df[column_name] = merged_df[column_name] * multiplier

        # --- Managing the case where the minimum ETR is 20% or below for TWZ countries

        # As mentioned above and detailed in Appendix A, the imputation of the non-haven tax deficit of TWZ countries
        # follows a specific process whenever the chosen minimum ETR is of or below 20%
        if minimum_ETR <= 0.2 and self.alternative_imputation:
            # We get the new multiplying factor from the method defined above
            multiplying_factor = self.get_alternative_non_haven_factor(minimum_ETR=minimum_ETR)

            # We compute all tax deficits at the reference rate (25% in the report)
            df = self.compute_all_tax_deficits(
                minimum_ETR=self.reference_rate_for_alternative_imputation,
                save_countries_replaced=False,
                upgrade_to_2021=upgrade_to_2021
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
            self.COUNTRIES_WITH_MINIMUM_REPORTING + self.COUNTRIES_WITH_CONTINENTAL_REPORTING
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

    # ------------------------------------------------------------------------------------------------------------------
    # --- QDMTT SCENARIO -----------------------------------------------------------------------------------------------

    def compute_qdmtt_revenue_gains(
        self, minimum_ETR=0.15, upgrade_non_havens=True, verbose=False
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

        self.full_sample_df = full_sample.copy()

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

        if verbose:

            print('Tax deficit already attributed bilaterally:', full_sample['TAX_DEFICIT'].sum() / 10**6, 'm USD')
            print('Tax deficit in rest of non-EU tax havens:', to_be_distributed / 10**6, 'm USD')
            print('___________________________________________________________________')

        full_sample['TEMP_DUMMY'] = np.logical_and(
            full_sample['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
            ~full_sample['PARTNER_COUNTRY_CODE'].isin(self.eu_27_country_codes + ['CHE'])
        ) * 1

        full_sample['TEMP_SHARE'] = (
            full_sample['TEMP_DUMMY'] * full_sample['TAX_DEFICIT']
            / full_sample[full_sample['TEMP_DUMMY'] == 1]['TAX_DEFICIT'].sum()
        )

        full_sample['IMPUTED_TAX_DEFICIT'] = full_sample['TEMP_SHARE'] * to_be_distributed

        imputation = full_sample.groupby('PARTNER_COUNTRY_CODE').agg(
            {
                'PARTNER_COUNTRY_NAME': 'first',
                'IMPUTED_TAX_DEFICIT': 'sum'
            }
        ).reset_index().rename(columns={'IMPUTED_TAX_DEFICIT': 'TAX_DEFICIT'})

        imputation['PARENT_COUNTRY_CODE'] = 'IMPT_REST'
        imputation['PARENT_COUNTRY_NAME'] = 'Imputation REST'

        full_sample = full_sample.drop(columns=['TEMP_DUMMY', 'TEMP_SHARE', 'IMPUTED_TAX_DEFICIT'])

        full_sample = pd.concat([full_sample, imputation])

        if verbose:

            print('Bilaterally attributed tax deficit after REST:', full_sample['TAX_DEFICIT'].sum() / 10**6, 'm USD')
            print('Worth a quick check here?')
            print('___________________________________________________________________')

        self.full_sample_before_TWZ_NH = full_sample.copy()

        # --- Upgrading non-haven tax deficits

        # - Theresa's method
        if upgrade_non_havens:

            if self.year == 2018 and self.China_treatment_2018 == "2017_CbCR":

                multiplier = headquarter_collects_scenario['Parent jurisdiction (alpha-3 code)'] == 'CHN'
                multiplier *= self.USD_to_EUR_2017 * self.multiplier_2017_2021
                multiplier = multiplier.map(
                    lambda x: self.USD_to_EUR * self.multiplier_2021 if x == 0 else x
                )

            else:

                multiplier = self.USD_to_EUR * self.multiplier_2021

            headquarter_collects_scenario['tax_deficit'] /= multiplier

            to_be_distributed = headquarter_collects_scenario['tax_deficit'].sum() - full_sample['TAX_DEFICIT'].sum()

            if verbose:

                print(
                    'Total tax deficit in the IIR scenario:',
                    headquarter_collects_scenario['tax_deficit'].sum() / 10**6,
                    'm USD'
                )
                print('Tax deficit currently bilaterally allocated:', full_sample['TAX_DEFICIT'].sum() / 10**6, 'm USD')
                print('Tax deficit to be distributed among non-havens:', to_be_distributed / 10**6, 'm USD')
                print('___________________________________________________________________')

            full_sample['TEMP_DUMMY'] = np.logical_and(
                ~full_sample['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
                np.logical_and(
                    full_sample['PARENT_COUNTRY_CODE'] != full_sample['PARTNER_COUNTRY_CODE'],
                    full_sample['PARENT_COUNTRY_CODE'] != 'IMPT_REST'
                )
            ) * 1

            full_sample['TEMP_SHARE'] = (
                full_sample['TEMP_DUMMY'] * full_sample['TAX_DEFICIT']
                / full_sample[full_sample['TEMP_DUMMY'] == 1]['TAX_DEFICIT'].sum()
            )

            self.full_sample_before_issue = full_sample.copy()

            full_sample['IMPUTED_TAX_DEFICIT'] = full_sample['TEMP_SHARE'] * to_be_distributed

            imputation = full_sample.groupby('PARTNER_COUNTRY_CODE').agg(
                {
                    'PARTNER_COUNTRY_NAME': 'first',
                    'IMPUTED_TAX_DEFICIT': 'sum'
                }
            ).reset_index().rename(columns={'IMPUTED_TAX_DEFICIT': 'TAX_DEFICIT'})

            imputation['PARENT_COUNTRY_CODE'] = 'IMPT_TWZ_NH'
            imputation['PARENT_COUNTRY_NAME'] = 'Imputation TWZ NH'

            full_sample = full_sample.drop(columns=['TEMP_DUMMY', 'TEMP_SHARE', 'IMPUTED_TAX_DEFICIT'])

            full_sample = pd.concat([full_sample, imputation])

            if verbose:

                print(
                    'Tax deficit bilaterally allocated after imputation for non-havens:',
                    full_sample['TAX_DEFICIT'].sum() / 10**6,
                    'm USD'
                )

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

        # Currency conversion and upgrade to 2021
        if self.year == 2018 and self.China_treatment_2018 == '2017_CbCR':

            multiplier = full_sample['PARENT_COUNTRY_CODE'] == 'CHN'
            multiplier *= self.multiplier_2017_2021 * self.USD_to_EUR_2017
            multiplier = multiplier.map(
                lambda x: self.multiplier_2021 * self.USD_to_EUR if x == 0 else x
            )

        else:

            multiplier = self.multiplier_2021 * self.USD_to_EUR

        full_sample['TAX_DEFICIT'] *= multiplier

        # Grouping by partner country in the full QDMTT scenario
        tax_deficits = full_sample.groupby(
            'PARTNER_COUNTRY_CODE'
        ).agg(
            {
                'PARTNER_COUNTRY_NAME': 'first',
                'TAX_DEFICIT': 'sum'
            }
        ).reset_index()

        self.final_full_sample = full_sample.copy()

        return tax_deficits.copy()

    # ------------------------------------------------------------------------------------------------------------------
    # --- PARTIAL COOPERATION AND UNILATERAL IMPLEMENTATION SCENARIOS --------------------------------------------------

    def get_tax_deficit_allocation_keys_intermediary(
        self,
        minimum_breakdown,
        weight_UPR, weight_employees, weight_assets,
        among_countries_implementing=False,
        countries_implementing=None
    ):

        share_UPR = weight_UPR / (weight_UPR + weight_employees + weight_assets)
        share_employees = weight_employees / (weight_UPR + weight_employees + weight_assets)
        share_assets = weight_assets / (weight_UPR + weight_employees + weight_assets)

        if among_countries_implementing and countries_implementing is None:
            raise Exception(
                'If you want to restrict the allocation to the set of countries implementing the deal (such that 100%'
                + 'of tax deficits end up being distributed), you must specify the list of implementing countries.'
            )

        oecd = pd.read_csv(self.path_to_oecd)

        # Focusing on the full sample (including loss-making entities)
        oecd = oecd[oecd['PAN'] == 'PANELA'].copy()

        if self.year == 2018 and self.China_treatment_2018 == '2017_CbCR':
            extract_China = oecd[np.logical_and(oecd['YEA'] == 2017, oecd['COU'] == 'CHN')].copy()
            extract_China['YEA'] += 1

            oecd = oecd[~np.logical_and(oecd['YEA'] == 2018, oecd['COU'] == 'CHN')].copy()
            oecd = pd.concat([oecd, extract_China], axis=0)

        oecd = oecd[oecd['YEA'] == self.year].copy()

        oecd.drop(
            columns=[
                'PAN', 'Grouping', 'Flag Codes', 'Flags', 'Year', 'YEA',
                'Ultimate Parent Jurisdiction'
            ],
            inplace=True
        )

        # Moving from a long to a wide dataset
        oecd = oecd.pivot(
            index=['COU', 'JUR', 'Partner Jurisdiction'],
            columns='CBC',
            values='Value'
        ).reset_index()

        # Focusing on columns of interest
        oecd = oecd[['COU', 'JUR', 'Partner Jurisdiction', 'UPR', 'EMPLOYEES', 'ASSETS']].copy()

        # Selecting parents with a sufficient breakdown of partners
        temp = oecd.groupby('COU').agg({'JUR': 'nunique'})
        relevant_parent_countries = temp[temp['JUR'] > minimum_breakdown].index
        oecd = oecd[oecd['COU'].isin(relevant_parent_countries)].copy()
        other_parent_countries = temp[temp['JUR'] <= minimum_breakdown].index

        # Removing foreign jurisdiction totals
        oecd = oecd[oecd['JUR'] != 'FJT'].copy()

        # Removing stateless entities
        oecd = oecd[oecd['JUR'] != 'STA'].copy()

        # Focusing on partners implementing the deal if relevant
        if among_countries_implementing:
            oecd = oecd[oecd['JUR'].isin(countries_implementing)].copy()

        if not oecd.empty:

            # Adding parent-level totals and deducing shares
            for col in ['UPR', 'EMPLOYEES', 'ASSETS']:
                # Missings are considered as 0s as a simplification
                oecd[col] = oecd[col].fillna(0)
                # Negative values (for unrelated-party revenues) are considered as 0s, again as a simplification
                oecd[col] = oecd[col].map(lambda x: max(x, 0))

                oecd[f'{col}_TOTAL'] = oecd.groupby('COU').transform('sum')[col]
                oecd[f'{col}_TOTAL'] = oecd[f'{col}_TOTAL'].astype(float)
                oecd[f'SHARE_{col}'] = oecd[col] / oecd[f'{col}_TOTAL']

            # oecd['KEY'] = (
            #     share_UPR * oecd['UPR'] + share_employees * oecd['EMPLOYEES'] + share_assets * oecd['ASSETS']
            # )
            # oecd['KEY_TOTAL'] = oecd.groupby('COU').transform('sum')['KEY']
            # oecd['KEY_TOTAL'] = oecd['KEY_TOTAL'].astype(float)
            oecd['SHARE_KEY'] = (
                share_UPR * oecd['SHARE_UPR']
                + share_employees * oecd['SHARE_EMPLOYEES']
                + share_assets * oecd['SHARE_ASSETS']
            )

        else:

            for col in ['UPR', 'EMPLOYEES', 'ASSETS']:

                oecd[f'{col}_TOTAL'] = None
                oecd[f'SHARE_{col}'] = None

            oecd['SHARE_KEY'] = None

        return other_parent_countries, oecd.copy()

    def get_tax_deficit_allocation_keys_unilateral(
        self,
        minimum_breakdown,
        full_own_tax_deficit,
        weight_UPR, weight_employees, weight_assets
    ):

        share_UPR = weight_UPR / (weight_UPR + weight_employees + weight_assets)
        share_employees = weight_employees / (weight_UPR + weight_employees + weight_assets)
        share_assets = weight_assets / (weight_UPR + weight_employees + weight_assets)

        oecd = pd.read_csv(self.path_to_oecd)

        # Focusing on the full sample (including loss-making entities)
        oecd = oecd[oecd['PAN'] == 'PANELA'].copy()

        if self.year == 2018 and self.China_treatment_2018 == '2017_CbCR':
            extract_China = oecd[np.logical_and(oecd['YEA'] == 2017, oecd['COU'] == 'CHN')].copy()
            extract_China['YEA'] += 1

            oecd = oecd[~np.logical_and(oecd['YEA'] == 2018, oecd['COU'] == 'CHN')].copy()
            oecd = pd.concat([oecd, extract_China], axis=0)

        oecd = oecd[oecd['YEA'] == self.year].copy()

        oecd.drop(
            columns=[
                'PAN', 'Grouping', 'Flag Codes', 'Flags', 'Year', 'YEA',
                'Ultimate Parent Jurisdiction', 'Partner Jurisdiction'
            ],
            inplace=True
        )

        # Moving from a long to a wide dataset
        oecd = oecd.pivot(
            index=['COU', 'JUR'],
            columns='CBC',
            values='Value'
        ).reset_index()

        # Focusing on columns of interest
        oecd = oecd[['COU', 'JUR', 'UPR', 'EMPLOYEES', 'ASSETS']].copy()

        # Selecting parents with a sufficient breakdown of partners
        temp = oecd.groupby('COU').agg({'JUR': 'nunique'})
        relevant_parent_countries = temp[temp['JUR'] > minimum_breakdown].index
        oecd = oecd[oecd['COU'].isin(relevant_parent_countries)].copy()
        other_parent_countries = temp[temp['JUR'] <= minimum_breakdown].index

        # Removing foreign jurisdiction totals
        oecd = oecd[oecd['JUR'] != 'FJT'].copy()

        # Removing stateless entities
        oecd = oecd[oecd['JUR'] != 'STA'].copy()

        # Adding parent-level totals and deducing shares
        for col in ['UPR', 'EMPLOYEES', 'ASSETS']:
            # Missings are considered as 0s as a simplification
            oecd[col] = oecd[col].fillna(0)
            # Negative values (for unrelated-party revenues) are considered as 0s, again as a simplification
            oecd[col] = oecd[col].map(lambda x: max(x, 0))

            oecd[f'{col}_TOTAL'] = oecd.groupby('COU').transform('sum')[col]
            oecd[f'{col}_TOTAL'] = oecd[f'{col}_TOTAL'].astype(float)
            oecd[f'SHARE_{col}'] = oecd[col] / oecd[f'{col}_TOTAL']

        # oecd['KEY'] = share_UPR * oecd['UPR'] + share_employees * oecd['EMPLOYEES'] + share_assets * oecd['ASSETS']
        # oecd['KEY_TOTAL'] = oecd.groupby('COU').transform('sum')['KEY']
        # oecd['KEY_TOTAL'] = oecd['KEY_TOTAL'].astype(float)
        oecd['SHARE_KEY'] = (
            share_UPR * oecd['SHARE_UPR']
            + share_employees * oecd['SHARE_EMPLOYEES']
            + share_assets * oecd['SHARE_ASSETS']
        )

        # Adjusting domestic observations depending on the "full_own_tax_deficit" argument
        if full_own_tax_deficit:
            for col in ['UPR', 'EMPLOYEES', 'ASSETS', 'KEY']:
                oecd[f'SHARE_{col}'] = oecd.apply(
                    lambda row: 1 if row['COU'] == row['JUR'] else row[f'SHARE_{col}'], axis=1
                )

        return other_parent_countries, oecd.copy()

    def compute_selected_intermediary_scenario_gain(
        self,
        countries_implementing,
        among_countries_implementing=False,
        minimum_ETR=0.15,
        minimum_breakdown=60,
        weight_UPR=1, weight_employees=0, weight_assets=0,
        exclude_non_implementing_domestic_TDs=True,
        upgrade_to_2021=True
    ):

        # We start by computing the total tax deficits of all in-sample countries (those of the multilateral scenario)
        tax_deficits = self.compute_all_tax_deficits(
            minimum_ETR=minimum_ETR,
            exclude_non_EU_domestic_TDs=exclude_non_implementing_domestic_TDs,
            upgrade_to_2021=upgrade_to_2021
        )

        tax_deficits = tax_deficits[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit',
                'tax_deficit_x_domestic',
            ]
        ].copy()

        # And we store in a separate DataFrame the tax deficits of selected countries implementing the deal
        selected_tax_deficits = tax_deficits[
            tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(countries_implementing)
        ].copy()

        # We focus on non-implementing countries, defined when the TaxDeficitCalculator object is instantiated
        temp = tax_deficits['Parent jurisdiction (alpha-3 code)'].unique()
        countries_not_implementing = temp[~np.isin(temp, countries_implementing)].copy()
        not_implementing_tax_deficits = tax_deficits[
            tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(countries_not_implementing)
        ].copy()

        # We remove non-implementing countries' domestic tax deficit from the sales-based allocation
        if exclude_non_implementing_domestic_TDs:
            not_implementing_tax_deficits['tax_deficit'] -= not_implementing_tax_deficits['tax_deficit_x_domestic']
            not_implementing_tax_deficits = not_implementing_tax_deficits.drop(columns=['tax_deficit_x_domestic'])

        # Let us get the relevant allocation keys
        parents_insufficient_brkdown, available_allocation_keys = self.get_tax_deficit_allocation_keys_intermediary(
            minimum_breakdown=minimum_breakdown,
            among_countries_implementing=False,
            countries_implementing=countries_implementing,
            weight_UPR=weight_UPR, weight_employees=weight_employees, weight_assets=weight_assets
        )

        share_UPR = weight_UPR / (weight_UPR + weight_employees + weight_assets)
        share_employees = weight_employees / (weight_UPR + weight_employees + weight_assets)
        share_assets = weight_assets / (weight_UPR + weight_employees + weight_assets)

        # Among non-implementing countries, we further focus on those for which we have allocation keys:
        # (i) TWZ countries are left aside
        # (ii) CbC-reporting countries with an insufficient partner country breakdown
        TWZ_countries = temp[~np.isin(temp, self.oecd['Parent jurisdiction (alpha-3 code)'].unique())].copy()
        allocable_non_implementing_TDs = not_implementing_tax_deficits[
            ~np.logical_or(
                not_implementing_tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(TWZ_countries),
                not_implementing_tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(parents_insufficient_brkdown)
            )
        ].copy()
        other_non_implementing_TDs = not_implementing_tax_deficits[
            np.logical_or(
                not_implementing_tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(TWZ_countries),
                not_implementing_tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(parents_insufficient_brkdown)
            )
        ].copy()

        # Allocating the directly allocable tax deficits
        allocable_non_implementing_TDs = allocable_non_implementing_TDs.merge(
            available_allocation_keys,
            how='left',
            left_on='Parent jurisdiction (alpha-3 code)', right_on='COU'
        )

        if among_countries_implementing:

            allocable_non_implementing_TDs = allocable_non_implementing_TDs[
                allocable_non_implementing_TDs['JUR'].isin(countries_implementing)
            ].copy()

            if allocable_non_implementing_TDs['SHARE_KEY'].sum() > 0:

                allocable_non_implementing_TDs['SHARE_KEY_TOTAL'] = allocable_non_implementing_TDs.groupby(
                    'Parent jurisdiction (alpha-3 code)'
                ).transform('sum')['SHARE_KEY']

                allocable_non_implementing_TDs['RESCALING_FACTOR'] = (
                    1 / allocable_non_implementing_TDs['SHARE_KEY_TOTAL']
                )

                allocable_non_implementing_TDs['SHARE_KEY'] *= allocable_non_implementing_TDs['RESCALING_FACTOR']

        allocable_non_implementing_TDs['directly_allocated'] = (
            allocable_non_implementing_TDs['tax_deficit'] * allocable_non_implementing_TDs['SHARE_KEY']
        ).astype(float)

        allocable_non_implementing_TDs = allocable_non_implementing_TDs[
            allocable_non_implementing_TDs['JUR'].isin(countries_implementing)
        ].copy()

        details_directly_allocated = allocable_non_implementing_TDs.copy()

        allocable_non_implementing_TDs = allocable_non_implementing_TDs.groupby(
            ['JUR', 'Partner Jurisdiction']
        ).agg(
            {'directly_allocated': 'sum'}
        ).reset_index().rename(columns={'JUR': 'Parent jurisdiction (alpha-3 code)'})

        # Allocating the tax deficits that are not directly allocable
        # Alternative approach?
        # sales_mapping = available_allocation_keys.copy()

        # if not among_countries_implementing:

        #     domestic_extract = sales_mapping[sales_mapping['COU'] == sales_mapping['JUR']].copy()

        #     avg_domestic_share = (
        #         share_UPR * domestic_extract['UPR'].sum() / sales_mapping['UPR'].sum()
        #         + share_employees * domestic_extract['EMPLOYEES'].sum() / sales_mapping['EMPLOYEES'].sum()
        #         + share_assets * domestic_extract['ASSETS'].sum() / sales_mapping['ASSETS'].sum()
        #     )

        # sales_mapping['IS_FOREIGN'] = sales_mapping['COU'] != sales_mapping['JUR']

        # sales_mapping['UPR_x_IS_FOREIGN'] = sales_mapping['UPR'] * sales_mapping['IS_FOREIGN']
        # sales_mapping['EMPLOYEES_x_IS_FOREIGN'] = sales_mapping['EMPLOYEES'] * sales_mapping['IS_FOREIGN']
        # sales_mapping['ASSETS_x_IS_FOREIGN'] = sales_mapping['ASSETS'] * sales_mapping['IS_FOREIGN']

        # if self.year == 2018 and self.China_treatment_2018 == "2017_CbCR":

        #     multiplier = sales_mapping['COU'] == 'CHN'
        #     multiplier *= self.growth_rates.set_index("CountryGroupName").loc['World', 'uprusd1817']
        #     multiplier = multiplier.map(lambda x: {0: 1}.get(x, x))

        # else:

        #     multiplier = 1

        # sales_mapping['UPR_x_IS_FOREIGN'] *= multiplier
        # sales_mapping['EMPLOYEES_x_IS_FOREIGN'] *= multiplier
        # sales_mapping['ASSETS_x_IS_FOREIGN'] *= multiplier

        # sales_mapping = sales_mapping.groupby(
        #     ['JUR', 'Partner Jurisdiction']
        # ).sum()[
        #     ['UPR_x_IS_FOREIGN', 'EMPLOYEES_x_IS_FOREIGN', 'ASSETS_x_IS_FOREIGN']
        # ].reset_index()

        # sales_mapping = sales_mapping.rename(
        #     columns={col: col.replace('_x_IS_FOREIGN', '') for col in sales_mapping.columns}
        # )

        # for col in ['UPR', 'EMPLOYEES', 'ASSETS']:

        #     sales_mapping[f'{col}_TOTAL'] = sales_mapping[col].sum()
        #     sales_mapping[f'SHARE_{col}'] = sales_mapping[col] / sales_mapping[f'{col}_TOTAL']

        # sales_mapping['SHARE_KEY'] = (
        #     share_UPR * sales_mapping['SHARE_UPR']
        #     + share_employees * sales_mapping['SHARE_EMPLOYEES']
        #     + share_assets * sales_mapping['SHARE_ASSETS']
        # )

        # avg_allocation_keys = sales_mapping[['JUR', 'Partner Jurisdiction', 'SHARE_KEY']].copy()

        # if not among_countries_implementing:

        #     avg_allocation_keys['SHARE_KEY'] *= (1 - avg_domestic_share)

        #     domestic_extract = other_non_implementing_TDs.copy()
        #     domestic_extract['JUR'] = domestic_extract['Parent jurisdiction (alpha-3 code)']
        #     domestic_extract['Partner Jurisdiction'] = domestic_extract['Parent jurisdiction (whitespaces cleaned)']
        #     domestic_extract['SHARE_KEY'] = avg_domestic_share

        # Allocating the tax deficits that are not directly allocable
        avg_allocation_keys = {'JUR': [], 'SHARE_KEY': []}

        sales_mapping = available_allocation_keys.drop(
            columns=[
                'UPR_TOTAL', 'ASSETS_TOTAL', 'EMPLOYEES_TOTAL',
                'SHARE_UPR', 'SHARE_ASSETS', 'SHARE_EMPLOYEES', 'SHARE_KEY'
            ]
        )

        # For the computation of average allocation keys, we consider all the partner jurisdictions included in the
        # OECD's country-by-country report statistics (not only in the sub-sample excluding loss-making entities but
        # in the whole dataset since allocation keys are sourced in the overall dataset)
        iteration = pd.read_csv(self.path_to_oecd, usecols=['JUR'])['JUR'].unique()
        iteration = iteration[~np.isin(iteration, ['STA', 'FJT'])].copy()

        # We extend this set to countries implementing the UTPR but never reported as partners in the data
        # They will get a share of allocation key of 0 and thus 0 revenue gains (except if we have them as parents)
        iteration = np.union1d(iteration, countries_implementing)

        # if among_countries_implementing:
        #     iteration = countries_implementing.copy()
        # else:
        #     iteration = np.union1d(
        #         np.union1d(
        #             tax_deficits['Parent jurisdiction (alpha-3 code)'].unique(),
        #             self.oecd['Partner jurisdiction (alpha-3 code)'].unique()
        #         ),
        #         self.oecd['Parent jurisdiction (alpha-3 code)'].unique()
        #     )

        for country in iteration:

            sales_mapping_foreign_MNEs = sales_mapping[sales_mapping['COU'] != country].copy()

            sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs[
                sales_mapping_foreign_MNEs['COU'] != sales_mapping_foreign_MNEs['JUR']
            ].copy()

            # if among_countries_implementing:
            #     sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs[
            #         sales_mapping_foreign_MNEs['JUR'].isin(countries_implementing)
            #     ].copy()

            country_extract = sales_mapping_foreign_MNEs[sales_mapping_foreign_MNEs['JUR'] == country].copy()

            avg_allocation_keys['JUR'].append(country)

            avg_allocation_keys['SHARE_KEY'].append(
                share_UPR * country_extract['UPR'].sum() / sales_mapping_foreign_MNEs['UPR'].sum()
                + share_employees * country_extract['EMPLOYEES'].sum() / sales_mapping_foreign_MNEs['EMPLOYEES'].sum()
                + share_assets * country_extract['ASSETS'].sum() / sales_mapping_foreign_MNEs['ASSETS'].sum()
            )

        avg_allocation_keys = pd.DataFrame(avg_allocation_keys)
        # avg_allocation_keys['SHARE_UPR'] = avg_allocation_keys['SHARE_UPR']

        # We re-scale the average allocation keys so that they sum to 1:
        #   - over the set of implementing countries if among_countries_implementing is True;
        #   - else over the set of all partner jurisdictions`.

        print(
            'Average allocation key for France:',
            avg_allocation_keys[avg_allocation_keys['JUR'] == 'FRA'].iloc[0, 1]
        )

        print(
            "Before the re-scaling of the average allocation keys, they sum to:",
            avg_allocation_keys['SHARE_KEY'].sum()
        )

        domestic_extract = sales_mapping[sales_mapping['COU'] == sales_mapping['JUR']].copy()
        avg_domestic_share = (
            share_UPR * domestic_extract['UPR'].sum() / sales_mapping['UPR'].sum()
            + share_employees * domestic_extract['EMPLOYEES'].sum() / sales_mapping['EMPLOYEES'].sum()
            + share_assets * domestic_extract['ASSETS'].sum() / sales_mapping['ASSETS'].sum()
        )
        print('Average domestic share:', avg_domestic_share)

        # print(
        #     "Before the re-scaling of the average allocation keys, they sum to:",
        #     avg_allocation_keys['SHARE_KEY'].sum()
        # )
        # if among_countries_implementing:
        #     rescaling_factor = 1 / avg_allocation_keys['SHARE_KEY'].sum()
        # else:
        #     rescaling_factor = (1 - avg_domestic_share) / avg_allocation_keys['SHARE_KEY'].sum()
        # avg_allocation_keys['SHARE_KEY'] *= rescaling_factor

        # avg_allocation_keys = avg_allocation_keys[avg_allocation_keys['JUR'].isin(countries_implementing)].copy()

        avg_allocation_keys['TEMP_KEY'] = 1
        other_non_implementing_TDs['TEMP_KEY'] = 1

        other_non_implementing_TDs = other_non_implementing_TDs.merge(
            avg_allocation_keys,
            how='left',
            on='TEMP_KEY'
        ).drop(columns=['TEMP_KEY'])

        other_non_implementing_TDs = other_non_implementing_TDs[
            other_non_implementing_TDs['Parent jurisdiction (alpha-3 code)'] != other_non_implementing_TDs['JUR']
        ].copy()

        if among_countries_implementing:
            other_non_implementing_TDs = other_non_implementing_TDs[
                other_non_implementing_TDs['JUR'].isin(countries_implementing)
            ].copy()

        other_non_implementing_TDs['SHARE_KEY_TOTAL'] = other_non_implementing_TDs.groupby(
            'Parent jurisdiction (alpha-3 code)'
        ).transform('sum')['SHARE_KEY']
        if not among_countries_implementing:
            other_non_implementing_TDs['RESCALING_FACTOR'] = (
                1 - avg_domestic_share
            ) / other_non_implementing_TDs['SHARE_KEY_TOTAL']
        else:
            other_non_implementing_TDs['RESCALING_FACTOR'] = 1 / other_non_implementing_TDs['SHARE_KEY_TOTAL']
        other_non_implementing_TDs['SHARE_KEY'] *= other_non_implementing_TDs['RESCALING_FACTOR']

        other_non_implementing_TDs = other_non_implementing_TDs[
            other_non_implementing_TDs['JUR'].isin(countries_implementing)
        ].copy()

        # if not among_countries_implementing:

        #     other_non_implementing_TDs = pd.concat([other_non_implementing_TDs, domestic_extract])

        other_non_implementing_TDs['imputed'] = (
            other_non_implementing_TDs['tax_deficit'] * other_non_implementing_TDs['SHARE_KEY']
        ).astype(float)

        other_non_implementing_TDs = other_non_implementing_TDs[
            other_non_implementing_TDs['JUR'].isin(countries_implementing)
        ].copy()

        details_imputed = other_non_implementing_TDs.copy()

        other_non_implementing_TDs = other_non_implementing_TDs.groupby('JUR').agg(
            {'imputed': 'sum'}
        ).reset_index().rename(columns={'JUR': 'Parent jurisdiction (alpha-3 code)'})

        selected_tax_deficits = selected_tax_deficits.merge(
            allocable_non_implementing_TDs, how='outer', on='Parent jurisdiction (alpha-3 code)'
        ).merge(
            other_non_implementing_TDs, how='outer', on='Parent jurisdiction (alpha-3 code)'
        )

        selected_tax_deficits['Parent jurisdiction (whitespaces cleaned)'] = selected_tax_deficits.apply(
            (
                lambda row: row['Parent jurisdiction (whitespaces cleaned)']
                if isinstance(row['Parent jurisdiction (whitespaces cleaned)'], str)
                else row['Partner Jurisdiction']
            ),
            axis=1
        )

        selected_tax_deficits = selected_tax_deficits.drop(columns=['Partner Jurisdiction'])

        selected_tax_deficits['tax_deficit'] = selected_tax_deficits['tax_deficit'].fillna(0)
        selected_tax_deficits['directly_allocated'] = selected_tax_deficits['directly_allocated'].fillna(0)
        selected_tax_deficits['imputed'] = selected_tax_deficits['imputed'].fillna(0)

        selected_tax_deficits['total'] = (
            selected_tax_deficits['tax_deficit']
            + selected_tax_deficits['directly_allocated']
            + selected_tax_deficits['imputed']
        )

        return selected_tax_deficits.copy(), details_directly_allocated.copy(), details_imputed.copy()

    def compute_unilateral_scenario_revenue_gains(
        self,
        full_own_tax_deficit,
        minimum_ETR=0.15,
        minimum_breakdown=60,
        weight_UPR=1, weight_employees=0, weight_assets=0,
        exclude_domestic_TDs=True,
        upgrade_to_2021=True
    ):

        # We start by computing the total tax deficits of all in-sample countries (those of the multilateral scenario)
        tax_deficits = self.compute_all_tax_deficits(
            minimum_ETR=minimum_ETR,
            exclude_non_EU_domestic_TDs=exclude_domestic_TDs,
            upgrade_to_2021=upgrade_to_2021
        )

        tax_deficits = tax_deficits[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit', 'tax_deficit_x_domestic'
            ]
        ].copy()

        # # if not full_own_tax_deficit:
        if exclude_domestic_TDs:
            tax_deficits['tax_deficit'] -= tax_deficits['tax_deficit_x_domestic']

        tax_deficits = tax_deficits.drop(columns=['tax_deficit_x_domestic'])

        # Let us get the relevant allocation keys
        parents_insufficient_brkdown, available_allocation_keys = self.get_tax_deficit_allocation_keys_unilateral(
            minimum_breakdown=minimum_breakdown, full_own_tax_deficit=full_own_tax_deficit,
            weight_UPR=weight_UPR, weight_employees=weight_employees, weight_assets=weight_assets
        )

        share_UPR = weight_UPR / (weight_UPR + weight_employees + weight_assets)
        share_employees = weight_employees / (weight_UPR + weight_employees + weight_assets)
        share_assets = weight_assets / (weight_UPR + weight_employees + weight_assets)

        # We focus on the tax deficits for which we have allocation keys:
        # (i) TWZ countries are left aside
        # (ii) CbC-reporting countries with an insufficient partner country breakdown
        temp = tax_deficits['Parent jurisdiction (alpha-3 code)'].unique()
        TWZ_countries = temp[~np.isin(temp, self.oecd['Parent jurisdiction (alpha-3 code)'].unique())].copy()
        allocable_TDs = tax_deficits[
            ~np.logical_or(
                tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(TWZ_countries),
                tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(parents_insufficient_brkdown)
            )
        ].copy()
        other_TDs = tax_deficits[
            np.logical_or(
                tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(TWZ_countries),
                tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(parents_insufficient_brkdown)
            )
        ].copy()

        # Allocating the directly allocable tax deficits
        allocable_TDs = allocable_TDs.merge(
            available_allocation_keys,
            how='left',
            left_on='Parent jurisdiction (alpha-3 code)', right_on='COU'
        )

        # if not full_own_tax_deficit:

        #     allocable_TDs['SHARE_KEY_TOTAL'] = allocable_TDs.groupby(
        #         'Parent jurisdiction (alpha-3 code)'
        #     ).transform('sum')['SHARE_KEY']
        #     allocable_TDs['RESCALING_FACTOR'] = 1 / allocable_TDs['SHARE_KEY_TOTAL']
        #     allocable_TDs['SHARE_KEY'] *= allocable_TDs['RESCALING_FACTOR']

        allocable_TDs['directly_allocated'] = (allocable_TDs['tax_deficit'] * allocable_TDs['SHARE_KEY']).astype(float)
        allocable_TDs['IS_DOMESTIC'] = allocable_TDs['COU'] == allocable_TDs['JUR']
        allocable_TDs['directly_allocated_dom'] = allocable_TDs['directly_allocated'] * allocable_TDs['IS_DOMESTIC']
        allocable_TDs['directly_allocated_for'] = allocable_TDs['directly_allocated'] * (~allocable_TDs['IS_DOMESTIC'])

        details_directly_allocated = allocable_TDs.copy()

        allocable_TDs = allocable_TDs.groupby('JUR').agg(
            {
                'directly_allocated': 'sum',
                'directly_allocated_dom': 'sum',
                'directly_allocated_for': 'sum'
            }
        ).reset_index()
        allocable_TDs = allocable_TDs.rename(columns={'JUR': 'Parent jurisdiction (alpha-3 code)'})

        # Allocating the tax deficits that are not directly allocable

        sales_mapping = available_allocation_keys.drop(
            columns=[
                'UPR_TOTAL', 'ASSETS_TOTAL', 'EMPLOYEES_TOTAL',
                'SHARE_UPR', 'SHARE_ASSETS', 'SHARE_EMPLOYEES', 'SHARE_KEY'
            ]
        )

        # (i) Allocating tax deficits collected from domestic multinationals

        other_TDs_domestic = other_TDs.copy()

        domestic_extract = sales_mapping[sales_mapping['COU'] == sales_mapping['JUR']].copy()

        # avg_domestic_share = domestic_extract['KEY'].sum() / sales_mapping['KEY'].sum()

        avg_domestic_share = (
            share_UPR * domestic_extract['UPR'].sum() / sales_mapping['UPR'].sum()
            + share_employees * domestic_extract['EMPLOYEES'].sum() / sales_mapping['EMPLOYEES'].sum()
            + share_assets * domestic_extract['ASSETS'].sum() / sales_mapping['ASSETS'].sum()
        )

        if full_own_tax_deficit:
            other_TDs_domestic['SHARE_KEY'] = 1

        else:

            other_TDs_domestic['SHARE_KEY'] = avg_domestic_share

        other_TDs_domestic['imputed_domestic'] = (
            other_TDs_domestic['tax_deficit'] * other_TDs_domestic['SHARE_KEY']
        ).astype(float)

        other_TDs_domestic = other_TDs_domestic.drop(
            columns=['tax_deficit', 'Parent jurisdiction (whitespaces cleaned)']
        )

        details_imputed_domestic = other_TDs_domestic.copy()

        # (ii) Allocating tax deficits to foreign countries / collected from foreign multinationals

        other_TDs_foreign = other_TDs.copy()

        avg_allocation_keys_foreign = {
            'JUR': [],
            'SHARE_KEY': []
        }

        # For the computation of average allocation keys, we consider all the partner jurisdictions included in the
        # OECD's country-by-country report statistics (not only in the sub-sample excluding loss-making entities but
        # in the whole dataset since allocation keys are sourced in the overall dataset)
        iteration = pd.read_csv(self.path_to_oecd, usecols=['JUR'])['JUR'].unique()
        iteration = iteration[~np.isin(iteration, ['STA', 'FJT'])].copy()

        # Among countries for which we have a tax deficit, we compute each country's average share of FOREIGN
        # multinationals' sales among countries with sufficiently detailed country-by-country report statistics
        for country in iteration:

            sales_mapping_foreign_MNEs = sales_mapping[sales_mapping['COU'] != country].copy()

            sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs[
                sales_mapping_foreign_MNEs['COU'] != sales_mapping_foreign_MNEs['JUR']
            ].copy()

            country_extract = sales_mapping_foreign_MNEs[sales_mapping_foreign_MNEs['JUR'] == country].copy()

            avg_allocation_keys_foreign['JUR'].append(country)

            avg_allocation_keys_foreign['SHARE_KEY'].append(
                share_UPR * country_extract['UPR'].sum() / sales_mapping_foreign_MNEs['UPR'].sum()
                + share_employees * country_extract['EMPLOYEES'].sum() / sales_mapping_foreign_MNEs['EMPLOYEES'].sum()
                + share_assets * country_extract['ASSETS'].sum() / sales_mapping_foreign_MNEs['ASSETS'].sum()
            )

        avg_allocation_keys_foreign = pd.DataFrame(avg_allocation_keys_foreign)

        print(
            'Average allocation key for France:',
            avg_allocation_keys_foreign[avg_allocation_keys_foreign['JUR'] == 'FRA'].iloc[0, 1]
        )

        print(
            "Before the re-scaling of the average allocation keys, they sum to:",
            avg_allocation_keys_foreign['SHARE_KEY'].sum()
        )
        # rescaling_factor = 1 / avg_allocation_keys_foreign['SHARE_KEY'].sum()
        # avg_allocation_keys_foreign['SHARE_KEY'] *= rescaling_factor

        # avg_allocation_keys_foreign = avg_allocation_keys_foreign[
        #     avg_allocation_keys_foreign['JUR'].isin(tax_deficits['Parent jurisdiction (alpha-3 code)'].unique())
        # ].copy()

        avg_allocation_keys_foreign['TEMP_KEY'] = 1
        other_TDs_foreign['TEMP_KEY'] = 1

        other_TDs_foreign = other_TDs_foreign.merge(
            avg_allocation_keys_foreign,
            how='left',
            on='TEMP_KEY'
        )

        other_TDs_foreign = other_TDs_foreign[
            other_TDs_foreign['Parent jurisdiction (alpha-3 code)'] != other_TDs_foreign['JUR']
        ].copy()

        other_TDs_foreign['SHARE_KEY_TOTAL'] = other_TDs_foreign.groupby(
            'Parent jurisdiction (alpha-3 code)'
        ).transform('sum')['SHARE_KEY']
        other_TDs_foreign['RESCALING_FACTOR'] = (
            1 - avg_domestic_share
        ) / other_TDs_foreign['SHARE_KEY_TOTAL']
        other_TDs_foreign['SHARE_KEY'] *= other_TDs_foreign['RESCALING_FACTOR']

        other_TDs_foreign['imputed_foreign'] = (
            other_TDs_foreign['tax_deficit'] * other_TDs_foreign['SHARE_KEY']
        ).astype(float)

        details_imputed_foreign = other_TDs_foreign.copy()

        other_TDs_foreign = other_TDs_foreign.groupby('JUR').agg(
            {'imputed_foreign': 'sum'}
        ).reset_index().rename(columns={'JUR': 'Parent jurisdiction (alpha-3 code)'})

        tax_deficits = tax_deficits.merge(
            allocable_TDs, how='outer', on='Parent jurisdiction (alpha-3 code)'
        ).merge(
            other_TDs_foreign, how='outer', on='Parent jurisdiction (alpha-3 code)'
        ).merge(
            other_TDs_domestic, how='outer', on='Parent jurisdiction (alpha-3 code)'
        )

        for col in [
            'directly_allocated', 'directly_allocated_dom', 'directly_allocated_for',
            'imputed_foreign', 'imputed_domestic'
        ]:
            tax_deficits[col] = tax_deficits[col].fillna(0)

        temp = tax_deficits.copy()
        temp['temp'] = temp['directly_allocated_dom'] + temp['directly_allocated_for']
        temp['diff'] = temp['directly_allocated'] - temp['temp']
        temp['diff_rel'] = temp['diff'] / temp['directly_allocated'] * 100

        if np.sum(temp['diff_rel'] > 0.001) > 0:
            raise Exception("We should have a perfect equality here.")

        tax_deficits['total'] = (
            tax_deficits['directly_allocated'] + tax_deficits['imputed_foreign'] + tax_deficits['imputed_domestic']
        )

        if full_own_tax_deficit and np.sum(tax_deficits['total'] < tax_deficits['tax_deficit']) > 0:
            raise Exception(
                'Since we attribute to each country the entire tax deficit of its own multinationals,'
                + ' the total revenue gains estimated here must be at least as high as the initial tax deficits.'
            )

        tax_deficits = tax_deficits.drop(columns=['tax_deficit', 'SHARE_KEY'])

        return (
            tax_deficits.copy(),
            details_directly_allocated.copy(),
            details_imputed_foreign.copy(),
            details_imputed_domestic.copy()
        )

    # ------------------------------------------------------------------------------------------------------------------
    # --- PURELY DOMESTIC FIRMS ----------------------------------------------------------------------------------------

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
            upgrade_factors = self.growth_rates.set_index('CountryGroupName')

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
        exchange_rates = self.xrates.copy()
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
        upgrade_factors = self.growth_rates.set_index('CountryGroupName')

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

    # ------------------------------------------------------------------------------------------------------------------
    # --- FULL BILATERAL DISAGGREGATION APPROACH -----------------------------------------------------------------------

    def build_bilateral_data(
        self,
        minimum_rate,
        QDMTT_incl_domestic,
        QDMTT_excl_domestic,
        ETR_increment=0,
        verbose=0,
        only_for_countries_replaced=False
    ):

        # We need to have previously loaded and cleaned the OECD and TWZ data
        if self.oecd is None or self.twz is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        # We fetch the list of OECD-reporting parent countries whose tax haven tax deficit is taken from TWZ data and
        # not from OECD data in the benchmark computations
        # _ = self.compute_all_tax_deficits(minimum_ETR=minimum_rate)
        # countries_replaced = self.countries_replaced.copy()

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
        # twz = twz[
        #     np.logical_or(
        #         ~twz['PARENT_COUNTRY_CODE'].isin(unique_parent_countries),
        #         twz['PARENT_COUNTRY_CODE'].isin(countries_replaced)
        #     )
        # ].copy()

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
        # twz_domestic = twz_domestic[twz_domestic['Alpha-3 country code'].isin(self.eu_27_country_codes)].copy()

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
        full_sample_df = pd.concat([oecd, twz, twz_domestic], axis=0)

        # --- Simplest case

        # For OECD-reporting countries whose tax haven tax deficit is taken in TWZ data, we must avoid double-counting
        full_sample_df['IS_DOMESTIC'] = full_sample_df['PARENT_COUNTRY_CODE'] == full_sample_df['PARTNER_COUNTRY_CODE']

        full_sample_df['ETR_inc'] = full_sample_df['ETR'] + ETR_increment
        full_sample_df['ETR_diff'] = full_sample_df['ETR_inc'].map(lambda x: max(minimum_rate - x, 0))
        full_sample_df['TAX_DEFICIT'] = full_sample_df['ETR_diff'] * full_sample_df['PROFITS_BEFORE_TAX_POST_CO']

        if not self.carve_outs:

            temp_df = full_sample_df.copy()
            temp_df['TAX_DEFICIT_oecd_th'] = temp_df['TAX_DEFICIT'] * np.logical_and(
                temp_df['SOURCE'] == 'oecd',
                temp_df['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes + ['REST'])
            )
            temp_df['TAX_DEFICIT_twz_th'] = temp_df['TAX_DEFICIT'] * np.logical_and(
                temp_df['SOURCE'] == 'twz_th',
                temp_df['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes + ['REST'])
            )
            temp_df = temp_df[
                ~np.logical_and(
                    temp_df['PARTNER_COUNTRY_CODE'] == temp_df['PARENT_COUNTRY_CODE'],
                    temp_df['SOURCE'] == 'oecd'
                )
            ].copy()
            temp_df['IS_OECD'] = temp_df['SOURCE'] == 'oecd'
            temp_df = temp_df.groupby(['PARENT_COUNTRY_CODE']).sum()[
                ['TAX_DEFICIT_oecd_th', 'TAX_DEFICIT_twz_th', 'IS_OECD']
            ].reset_index()
            temp_df = temp_df[temp_df['IS_OECD'] > 0].copy()
            temp_df = temp_df[temp_df['TAX_DEFICIT_twz_th'] > temp_df['TAX_DEFICIT_oecd_th']].copy()
            temp_df = temp_df.reset_index()
            temp_df = temp_df[
                ~temp_df['PARENT_COUNTRY_CODE'].isin(
                    self.COUNTRIES_WITH_MINIMUM_REPORTING + self.COUNTRIES_WITH_CONTINENTAL_REPORTING
                )
            ].copy()
            countries_replaced = sorted(list(temp_df['PARENT_COUNTRY_CODE'].unique()))
            print('Countries replaced:', countries_replaced)

        else:

            calculator_no_CO = TaxDeficitCalculator(
                year=self.year,
                alternative_imputation=self.alternative_imputation,
                non_haven_TD_imputation_selection=self.non_haven_TD_imputation_selection,
                sweden_treatment=self.sweden_treatment,
                belgium_treatment=self.belgium_treatment,
                SGP_CYM_treatment=self.SGP_CYM_treatment,
                China_treatment_2018=self.China_treatment_2018,
                use_adjusted_profits=self.use_adjusted_profits,
                average_ETRs=self.average_ETRs_bool,
                years_for_avg_ETRs=self.years_for_avg_ETRs,
                carve_outs=False,
                de_minimis_exclusion=self.de_minimis_exclusion,
                add_AUT_AUT_row=self.add_AUT_AUT_row,
                extended_dividends_adjustment=self.extended_dividends_adjustment,
                use_TWZ_for_CbCR_newcomers=self.use_TWZ_for_CbCR_newcomers,
                behavioral_responses=False,
                fetch_data_online=self.fetch_data_online
            )

            calculator_no_CO.load_clean_data()

            countries_replaced = calculator_no_CO.build_bilateral_data(
                minimum_rate=minimum_rate,
                QDMTT_incl_domestic=QDMTT_incl_domestic,
                QDMTT_excl_domestic=QDMTT_excl_domestic,
                ETR_increment=ETR_increment,
                verbose=0,
                only_for_countries_replaced=True
            )
            print('Countries replaced:', countries_replaced)

        if only_for_countries_replaced:
            return countries_replaced

        multiplier = np.logical_and(
            full_sample_df['PARENT_COUNTRY_CODE'] != full_sample_df['PARTNER_COUNTRY_CODE'],
            np.logical_and(
                full_sample_df['PARENT_COUNTRY_CODE'].isin(countries_replaced),
                np.logical_and(
                    full_sample_df['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
                    full_sample_df['SOURCE'] == 'oecd'
                )
            )
        )

        multiplier = 1 - multiplier

        full_sample_df['PROFITS_BEFORE_TAX_POST_CO'] *= multiplier
        full_sample_df['TAX_DEFICIT'] *= multiplier

        multiplier = np.logical_and(
            full_sample_df['PARENT_COUNTRY_CODE'].isin(self.oecd['Parent jurisdiction (alpha-3 code)']),
            np.logical_and(
                ~full_sample_df['PARENT_COUNTRY_CODE'].isin(countries_replaced),
                np.logical_and(
                    full_sample_df['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes + ['REST']),
                    full_sample_df['SOURCE'] == 'twz_th'
                )
            )
        )

        multiplier = 1 - multiplier

        full_sample_df['PROFITS_BEFORE_TAX_POST_CO'] *= multiplier
        full_sample_df['TAX_DEFICIT'] *= multiplier

        bilat_extract_df = full_sample_df[full_sample_df['PARTNER_COUNTRY_CODE'] != 'REST'].copy()

        rest_extract = full_sample_df[full_sample_df['PARTNER_COUNTRY_CODE'] == 'REST'].copy()

        if verbose:

            print(
                'Tax deficit already attributed bilaterally:',
                bilat_extract_df[
                    ~np.logical_and(
                        bilat_extract_df['PARTNER_COUNTRY_CODE'] == bilat_extract_df['PARENT_COUNTRY_CODE'],
                        bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(QDMTT_excl_domestic)
                    )
                ]['TAX_DEFICIT'].sum() / 10**6,
                'm USD'
            )
            print('Tax deficit in rest of non-EU tax havens:', rest_extract['TAX_DEFICIT'].sum() / 10**6, 'm USD')
            print('___________________________________________________________________')

        # --- Rest of non-EU tax havens

        bilat_extract_df['collected_through_foreign_QDMTT'] = np.logical_or(
            np.logical_and(
                bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(QDMTT_incl_domestic),
                ~bilat_extract_df['IS_DOMESTIC']
            ),
            np.logical_and(
                bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(QDMTT_excl_domestic),
                ~bilat_extract_df['IS_DOMESTIC']
            )
        )

        # variable_mask = bilat_extract_df['PARENT_COUNTRY_CODE'].isin(self.eu_27_country_codes)
        # variable_mask = bilat_extract_df['PARENT_COUNTRY_CODE'] != 'USA'

        # relevant_extract_df = bilat_extract_df[
        #     np.logical_and(
        #         # Selection of relevant parent countries
        #         np.logical_and(
        #             variable_mask,
        #             np.logical_and(
        #                 ~bilat_extract_df['PARENT_COUNTRY_CODE'].isin(
        #                     self.COUNTRIES_WITH_CONTINENTAL_REPORTING
        #                     + self.COUNTRIES_WITH_MINIMUM_REPORTING
        #                 ),
        #                 ~bilat_extract_df['PARENT_COUNTRY_CODE'].isin(self.tax_haven_country_codes)
        #             )
        #         ),
        #         # Selection of relevant partner countries
        #         np.logical_and(
        #             bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
        #             ~bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(
        #                 self.eu_27_country_codes + ['CHE']
        #             )
        #         )
        #     )
        # ].copy()

        relevant_extract_df = bilat_extract_df[
            np.logical_and(
                bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
                ~bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(
                    self.eu_27_country_codes + ['CHE']
                )
            )
        ].copy()

        relevant_extract_df['TAX_DEFICIT_foreign_QDMTT'] = (
            relevant_extract_df['TAX_DEFICIT'] * relevant_extract_df['collected_through_foreign_QDMTT']
        )

        total = relevant_extract_df[
            relevant_extract_df['PARENT_COUNTRY_CODE'] != relevant_extract_df['PARTNER_COUNTRY_CODE']
        ]['TAX_DEFICIT'].sum()

        shares = relevant_extract_df[
            relevant_extract_df['collected_through_foreign_QDMTT']
        ].groupby(
            ['PARTNER_COUNTRY_CODE', 'PARTNER_COUNTRY_NAME']
        ).sum()[['TAX_DEFICIT_foreign_QDMTT']].reset_index()

        shares = shares.rename(columns={'TAX_DEFICIT_foreign_QDMTT': 'KEY'})

        shares['collected_through_foreign_QDMTT'] = True

        idx = len(shares)

        shares.loc[idx, 'PARTNER_COUNTRY_CODE'] = 'REST'
        shares.loc[idx, 'PARTNER_COUNTRY_NAME'] = 'Rest'
        shares.loc[idx, 'KEY'] = total - shares['KEY'].sum()
        shares.loc[idx, 'collected_through_foreign_QDMTT'] = False

        if verbose:

            self.REST_shares_new = shares.copy()

        rest_extract = rest_extract[
            [
                'PARENT_COUNTRY_CODE', 'PARENT_COUNTRY_NAME',
                'SOURCE', 'IS_DOMESTIC', 'ETR', 'ETR_diff',
                'PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT'
            ]
        ].copy()

        rest_extract['MERGE_TEMP'] = 1

        shares['MERGE_TEMP'] = 1

        rest_extract = rest_extract.merge(shares, how='outer', on='MERGE_TEMP').drop(columns='MERGE_TEMP')

        if verbose:
            print(rest_extract.shape)

        # rest_extract = rest_extract[
        #     rest_extract['PARENT_COUNTRY_CODE'] != rest_extract['PARTNER_COUNTRY_CODE']
        # ].copy()

        if verbose:
            print(rest_extract.shape)

        rest_extract['KEY_TOTAL'] = rest_extract.groupby('PARENT_COUNTRY_CODE').transform('sum')['KEY']

        rest_extract['KEY_SHARE'] = rest_extract['KEY'] / rest_extract['KEY_TOTAL']

        rest_extract['PROFITS_BEFORE_TAX_POST_CO'] *= rest_extract['KEY_SHARE']
        rest_extract['TAX_DEFICIT'] *= rest_extract['KEY_SHARE']

        rest_extract = rest_extract.drop(columns=['KEY_TOTAL', 'KEY', 'KEY_SHARE'])

        rest_extract['EDGE_CASE'] = rest_extract['PARENT_COUNTRY_CODE'] == rest_extract['PARTNER_COUNTRY_CODE']
        bilat_extract_df['EDGE_CASE'] = False

        full_sample_df = pd.concat([bilat_extract_df, rest_extract], axis=0)

        if verbose:
            print(
                'Bilaterally attributed tax deficit after REST:',
                full_sample_df[
                    ~np.logical_and(
                        full_sample_df['PARTNER_COUNTRY_CODE'] == full_sample_df['PARENT_COUNTRY_CODE'],
                        full_sample_df['PARTNER_COUNTRY_CODE'].isin(QDMTT_excl_domestic)
                    )
                ]['TAX_DEFICIT'].sum() / 10**6,
                'm USD'
            )
            print('Worth a quick check here?')
            print('___________________________________________________________________')

        # --- TWZ countries' non-haven tax deficit

        TWZ_extract = full_sample_df[
            ~full_sample_df['PARENT_COUNTRY_CODE'].isin(
                self.oecd['Parent jurisdiction (alpha-3 code)'].unique()
            )
        ].copy()

        TWZ_extract = TWZ_extract[
            np.logical_or(
                TWZ_extract['PARENT_COUNTRY_CODE'] != TWZ_extract['PARTNER_COUNTRY_CODE'],
                TWZ_extract['collected_through_foreign_QDMTT']
            )
        ].copy()

        TWZ_extract = TWZ_extract[
            TWZ_extract['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes + ['REST'])
        ].copy()

        TWZ_extract['TAX_DEFICIT'] = TWZ_extract['TAX_DEFICIT'].astype(float)

        HQ_scenario_TWZ = TWZ_extract.groupby(
            ['PARENT_COUNTRY_CODE', 'PARENT_COUNTRY_NAME']
        ).sum()['TAX_DEFICIT'].reset_index()
        HQ_scenario_TWZ = HQ_scenario_TWZ.rename(
            columns={
                'PARENT_COUNTRY_CODE': 'Parent jurisdiction (alpha-3 code)',
                'PARENT_COUNTRY_NAME': 'Parent jurisdiction (whitespaces cleaned)',
                'TAX_DEFICIT': 'tax_deficit_x_non_haven'
            }
        )

        factor = self.get_non_haven_imputation_ratio(
            minimum_ETR=minimum_rate, selection=self.non_haven_TD_imputation_selection
        )
        HQ_scenario_TWZ['tax_deficit_x_non_haven'] *= factor

        if minimum_rate <= 0.2 and self.alternative_imputation:

            TWZ_extract = self.build_bilateral_data(
                self.reference_rate_for_alternative_imputation,
                QDMTT_incl_domestic,
                QDMTT_excl_domestic
            )

            TWZ_extract = TWZ_extract[TWZ_extract['SOURCE'] == 'imputation'].copy()

            TWZ_extract['TAX_DEFICIT'] = TWZ_extract['TAX_DEFICIT'].astype(float)

            HQ_scenario_TWZ = TWZ_extract.groupby(
                ['PARENT_COUNTRY_CODE', 'PARENT_COUNTRY_NAME']
            ).sum()['TAX_DEFICIT'].reset_index()

            HQ_scenario_TWZ = HQ_scenario_TWZ.rename(
                columns={
                    'PARENT_COUNTRY_CODE': 'Parent jurisdiction (alpha-3 code)',
                    'PARENT_COUNTRY_NAME': 'Parent jurisdiction (whitespaces cleaned)',
                    'TAX_DEFICIT': 'tax_deficit_x_non_haven'
                }
            )

            factor = self.get_alternative_non_haven_factor(minimum_ETR=minimum_rate, ETR_increment=ETR_increment)
            print("Alternative non-haven factor:", factor)

            HQ_scenario_TWZ['tax_deficit_x_non_haven'] *= factor

        HQ_scenario_TWZ = HQ_scenario_TWZ.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'PARENT_COUNTRY_NAME',
                'Parent jurisdiction (alpha-3 code)': 'PARENT_COUNTRY_CODE',
                'tax_deficit_x_non_haven': 'TAX_DEFICIT'
            }
        )

        # variable_mask = bilat_extract_df['PARENT_COUNTRY_CODE'].isin(self.eu_27_country_codes)
        # variable_mask = bilat_extract_df['PARENT_COUNTRY_CODE'] != 'USA'

        # relevant_extract_df = bilat_extract_df[
        #     np.logical_and(
        #         # Selection of relevant parent countries
        #         np.logical_and(
        #             variable_mask,
        #             np.logical_and(
        #                 ~bilat_extract_df['PARENT_COUNTRY_CODE'].isin(
        #                     self.COUNTRIES_WITH_CONTINENTAL_REPORTING
        #                     + self.COUNTRIES_WITH_MINIMUM_REPORTING
        #                 ),
        #                 ~bilat_extract_df['PARENT_COUNTRY_CODE'].isin(self.tax_haven_country_codes)
        #             )
        #         ),
        #         # Selection of relevant partner countries
        #         np.logical_and(
        #             ~bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
        #             bilat_extract_df['PARTNER_COUNTRY_CODE'] != bilat_extract_df['PARENT_COUNTRY_CODE']
        #         )
        #     )
        # ].copy()

        relevant_extract_df = bilat_extract_df[
            np.logical_and(
                ~bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
                bilat_extract_df['PARTNER_COUNTRY_CODE'] != bilat_extract_df['PARENT_COUNTRY_CODE']
            )
        ].copy()

        shares = relevant_extract_df.groupby(
            ['PARTNER_COUNTRY_CODE', 'PARTNER_COUNTRY_NAME']
        ).sum()[
            'TAX_DEFICIT'
        ].reset_index()

        shares = shares.rename(columns={'TAX_DEFICIT': 'KEY'})

        shares = shares[shares['KEY'] > 0].copy()

        shares['MERGE_TEMP'] = 1

        HQ_scenario_TWZ['MERGE_TEMP'] = 1

        TWZ_countries_non_havens = HQ_scenario_TWZ.merge(
            shares, how='outer', on='MERGE_TEMP').drop(
            columns=['MERGE_TEMP']
        )

        # TWZ_countries_non_havens = TWZ_countries_non_havens[
        #     TWZ_countries_non_havens['PARTNER_COUNTRY_CODE'] != TWZ_countries_non_havens['PARENT_COUNTRY_CODE']
        # ].copy()

        TWZ_countries_non_havens['KEY_TOTAL'] = TWZ_countries_non_havens.groupby(
            'PARENT_COUNTRY_CODE'
        ).transform('sum')['KEY']

        TWZ_countries_non_havens['SHARE_KEY'] = TWZ_countries_non_havens['KEY'] / TWZ_countries_non_havens['KEY_TOTAL']

        TWZ_countries_non_havens['TAX_DEFICIT'] *= TWZ_countries_non_havens['SHARE_KEY']

        TWZ_countries_non_havens = TWZ_countries_non_havens[
            [
                'PARENT_COUNTRY_CODE', 'PARENT_COUNTRY_NAME',
                'PARTNER_COUNTRY_CODE', 'PARTNER_COUNTRY_NAME',
                'TAX_DEFICIT'
            ]
        ].copy()

        TWZ_countries_non_havens['IS_DOMESTIC'] = False
        TWZ_countries_non_havens['SOURCE'] = 'imputation'
        TWZ_countries_non_havens['EDGE_CASE'] = (
            TWZ_countries_non_havens['PARENT_COUNTRY_CODE'] == TWZ_countries_non_havens['PARTNER_COUNTRY_CODE']
        )

        full_sample_df = full_sample_df.drop(columns=['collected_through_foreign_QDMTT'])

        full_sample_df = pd.concat([full_sample_df, TWZ_countries_non_havens], axis=0)

        return full_sample_df.copy()

    def allocate_bilateral_tax_deficits(
        self,
        minimum_rate,
        QDMTT_incl_domestic,
        IIR_incl_domestic,
        UTPR_incl_domestic,
        QDMTT_excl_domestic,
        IIR_excl_domestic,
        UTPR_excl_domestic,
        stat_rate_condition_for_UTPR=False,
        min_stat_rate_for_UTPR_safe_harbor=None,
        weight_UPR=1, weight_employees=0, weight_assets=0,
        minimum_breakdown=60,
        among_countries_implementing=True,
        return_bilateral_details=False,
        ETR_increment=0,
        verbose=1
    ):

        if stat_rate_condition_for_UTPR and min_stat_rate_for_UTPR_safe_harbor is None:
            raise Exception(
                'To condition the application of the UTPR on the statutory corporate income tax rate, '
                + 'you must provide the corresponding threshold rate.'
            )

        full_sample_df = self.build_bilateral_data(
            minimum_rate,
            QDMTT_incl_domestic, QDMTT_excl_domestic,
            ETR_increment=ETR_increment,
            verbose=verbose
        )

        # --- Generalities

        # Indicator variables for the QDMTT
        full_sample_df['collected_through_domestic_QDMTT'] = np.logical_and(
            full_sample_df['PARTNER_COUNTRY_CODE'].isin(QDMTT_incl_domestic),
            full_sample_df['PARENT_COUNTRY_CODE'] == full_sample_df['PARTNER_COUNTRY_CODE']
        )
        # full_sample_df['collected_through_foreign_QDMTT'] = np.logical_and(
        #     full_sample_df['PARTNER_COUNTRY_CODE'].isin(QDMTT_incl_domestic + QDMTT_excl_domestic),
        #     full_sample_df['PARENT_COUNTRY_CODE'] != full_sample_df['PARTNER_COUNTRY_CODE']
        # )
        full_sample_df['collected_through_foreign_QDMTT'] = np.logical_and(
            ~full_sample_df['collected_through_domestic_QDMTT'],
            np.logical_or(
                np.logical_and(
                    full_sample_df['PARTNER_COUNTRY_CODE'].isin(QDMTT_incl_domestic + QDMTT_excl_domestic),
                    full_sample_df['PARENT_COUNTRY_CODE'] != full_sample_df['PARTNER_COUNTRY_CODE']
                ),
                np.logical_and(
                    full_sample_df['PARTNER_COUNTRY_CODE'].isin(QDMTT_incl_domestic + QDMTT_excl_domestic),
                    full_sample_df['EDGE_CASE']
                )
            )
        )

        # Indicator variables for the IIR
        full_sample_df['collected_through_domestic_IIR'] = np.logical_and(
            ~full_sample_df['collected_through_domestic_QDMTT'],
            np.logical_and(
                full_sample_df['PARENT_COUNTRY_CODE'] == full_sample_df['PARTNER_COUNTRY_CODE'],
                full_sample_df['PARENT_COUNTRY_CODE'].isin(IIR_incl_domestic)
            )
        )
        full_sample_df['collected_through_foreign_IIR'] = np.logical_and(
            ~full_sample_df['collected_through_foreign_QDMTT'],
            np.logical_or(
                np.logical_and(
                    full_sample_df['PARENT_COUNTRY_CODE'] != full_sample_df['PARTNER_COUNTRY_CODE'],
                    full_sample_df['PARENT_COUNTRY_CODE'].isin(IIR_incl_domestic + IIR_excl_domestic)
                ),
                np.logical_and(
                    full_sample_df['EDGE_CASE'].astype(bool),
                    np.logical_and(
                        full_sample_df['PARENT_COUNTRY_CODE'].isin(IIR_incl_domestic + IIR_excl_domestic),
                        ~full_sample_df['collected_through_domestic_IIR']
                    )
                )
            )
        )

        # Indicator variables for the UTPR
        if stat_rate_condition_for_UTPR:

            # Reading Tax Foundation's corporate income tax rates for 2022
            if self.fetch_data_online:

                stat_rates_2022 = pd.read_csv(
                    (
                        "https://raw.githubusercontent.com/TaxFoundation/worldwide-corporate-tax-rates/"
                        + "master/final_outputs/all_rates_2022.csv"
                    )
                )

            else:

                stat_rates_2022 = pd.read_csv(os.path.join(path_to_dir, "data", "all_rates_2022.csv"))

            # Adding the tax rate for the Marshall Islands based on that of the Micronesia Federation
            new_idx = len(stat_rates_2022)

            stat_rates_2022.loc[new_idx, 'ISO3'] = 'MHL'

            stat_rates_2022.loc[new_idx, 'Corporate Tax Rate'] = stat_rates_2022[
                stat_rates_2022['ISO3'] == 'FSM'
            ]['Corporate Tax Rate'].unique()

            # Adding statutory tax rates to the main DataFrame
            full_sample_df = full_sample_df.merge(
                stat_rates_2022,
                how='left',
                left_on='PARENT_COUNTRY_CODE', right_on='ISO3'
            ).drop(columns='ISO3').rename(columns={'Corporate Tax Rate': 'STAT_RATE'})

            full_sample_df['collected_through_domestic_UTPR'] = np.logical_and(
                full_sample_df['PARENT_COUNTRY_CODE'] == full_sample_df['PARTNER_COUNTRY_CODE'],
                np.logical_and(
                    ~full_sample_df['collected_through_domestic_QDMTT'],
                    np.logical_and(
                        ~full_sample_df['collected_through_domestic_IIR'],
                        full_sample_df['STAT_RATE'] < min_stat_rate_for_UTPR_safe_harbor
                    )
                )
            )
            full_sample_df['collected_through_foreign_UTPR'] = np.logical_and(
                full_sample_df['PARENT_COUNTRY_CODE'] != full_sample_df['PARTNER_COUNTRY_CODE'],
                np.logical_and(
                    ~full_sample_df['collected_through_foreign_QDMTT'],
                    np.logical_and(
                        ~full_sample_df['collected_through_foreign_IIR'],
                        full_sample_df['STAT_RATE'] < min_stat_rate_for_UTPR_safe_harbor
                    )
                )
            )

            full_sample_df = full_sample_df.drop(columns=['STAT_RATE'])

        else:

            # full_sample_df['collected_through_domestic_UTPR'] = np.logical_and(
            #     full_sample_df['PARENT_COUNTRY_CODE'] == full_sample_df['PARTNER_COUNTRY_CODE'],
            #     np.logical_and(
            #         ~full_sample_df['collected_through_domestic_QDMTT'],
            #         ~full_sample_df['collected_through_domestic_IIR']
            #     )
            # )
            full_sample_df['collected_through_domestic_UTPR'] = np.logical_and(
                full_sample_df['PARENT_COUNTRY_CODE'] == full_sample_df['PARTNER_COUNTRY_CODE'],
                np.logical_and(
                    ~full_sample_df['EDGE_CASE'].astype(bool),
                    full_sample_df[
                        [
                            'collected_through_foreign_QDMTT',
                            'collected_through_domestic_QDMTT',
                            'collected_through_domestic_IIR'
                        ]
                    ].sum(axis=1) == 0
                )
            )
            full_sample_df['collected_through_foreign_UTPR'] = np.logical_and(
                np.logical_or(
                    full_sample_df['PARENT_COUNTRY_CODE'] != full_sample_df['PARTNER_COUNTRY_CODE'],
                    full_sample_df['EDGE_CASE'].astype(bool)
                ),
                full_sample_df[
                    [
                        'collected_through_foreign_QDMTT', 'collected_through_foreign_IIR',
                        'collected_through_domestic_QDMTT', 'collected_through_domestic_IIR'
                    ]
                ].sum(axis=1) == 0
            )

        print(full_sample_df[['collected_through_foreign_UTPR', 'collected_through_domestic_UTPR']].sum(axis=1).max())

        # --- Applying the UTPR

        domestic_UTPR_extract = full_sample_df[full_sample_df['collected_through_domestic_UTPR']].copy()
        foreign_UTPR_extract = full_sample_df[full_sample_df['collected_through_foreign_UTPR']].copy()

        share_UPR = weight_UPR / (weight_UPR + weight_employees + weight_assets)
        share_employees = weight_employees / (weight_UPR + weight_employees + weight_assets)
        share_assets = weight_assets / (weight_UPR + weight_employees + weight_assets)

        (
            parents_insufficient_brkdown, available_allocation_keys_domestic
        ) = self.get_tax_deficit_allocation_keys_intermediary(
            minimum_breakdown=minimum_breakdown,
            among_countries_implementing=False,
            countries_implementing=UTPR_incl_domestic,
            weight_UPR=weight_UPR, weight_employees=weight_employees, weight_assets=weight_assets
        )

        (_, available_allocation_keys_foreign) = self.get_tax_deficit_allocation_keys_intermediary(
            minimum_breakdown=minimum_breakdown,
            among_countries_implementing=False,
            countries_implementing=UTPR_incl_domestic + UTPR_excl_domestic,
            weight_UPR=weight_UPR, weight_employees=weight_employees, weight_assets=weight_assets
        )

        temp = full_sample_df['PARENT_COUNTRY_CODE'].unique()
        TWZ_countries = temp[
            ~np.isin(temp, self.oecd['Parent jurisdiction (alpha-3 code)'].unique())
        ].copy()

        allocable_domestic_UTPR_TDs = domestic_UTPR_extract[
            ~np.logical_or(
                domestic_UTPR_extract['PARENT_COUNTRY_CODE'].isin(TWZ_countries),
                domestic_UTPR_extract['PARENT_COUNTRY_CODE'].isin(parents_insufficient_brkdown)
            )
        ].copy()

        allocable_foreign_UTPR_TDs = foreign_UTPR_extract[
            ~np.logical_or(
                foreign_UTPR_extract['PARENT_COUNTRY_CODE'].isin(TWZ_countries),
                foreign_UTPR_extract['PARENT_COUNTRY_CODE'].isin(parents_insufficient_brkdown)
            )
        ].copy()

        other_domestic_UTPR_TDs = domestic_UTPR_extract[
            np.logical_or(
                domestic_UTPR_extract['PARENT_COUNTRY_CODE'].isin(TWZ_countries),
                domestic_UTPR_extract['PARENT_COUNTRY_CODE'].isin(parents_insufficient_brkdown)
            )
        ].copy()

        other_foreign_UTPR_TDs = foreign_UTPR_extract[
            np.logical_or(
                foreign_UTPR_extract['PARENT_COUNTRY_CODE'].isin(TWZ_countries),
                foreign_UTPR_extract['PARENT_COUNTRY_CODE'].isin(parents_insufficient_brkdown)
            )
        ].copy()

        allocable_domestic_UTPR_TDs = allocable_domestic_UTPR_TDs.merge(
            available_allocation_keys_domestic,
            how='left',
            left_on='PARENT_COUNTRY_CODE', right_on='COU'
        )

        if among_countries_implementing:

            allocable_domestic_UTPR_TDs = allocable_domestic_UTPR_TDs[
                allocable_domestic_UTPR_TDs['JUR'].isin(UTPR_incl_domestic)
            ].copy()

            if allocable_domestic_UTPR_TDs['SHARE_KEY'].sum() > 0:
                allocable_domestic_UTPR_TDs['SHARE_KEY_TOTAL'] = allocable_domestic_UTPR_TDs.groupby(
                    ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'SOURCE']
                ).transform('sum')['SHARE_KEY']
                allocable_domestic_UTPR_TDs['RESCALING_FACTOR'] = 1 / allocable_domestic_UTPR_TDs['SHARE_KEY_TOTAL']
                allocable_domestic_UTPR_TDs['SHARE_KEY'] *= allocable_domestic_UTPR_TDs['RESCALING_FACTOR']

        allocable_foreign_UTPR_TDs = allocable_foreign_UTPR_TDs.merge(
            available_allocation_keys_foreign,
            how='left',
            left_on='PARENT_COUNTRY_CODE', right_on='COU'
        )

        if among_countries_implementing:

            allocable_foreign_UTPR_TDs = allocable_foreign_UTPR_TDs[
                allocable_foreign_UTPR_TDs['JUR'].isin(UTPR_incl_domestic + UTPR_excl_domestic)
            ].copy()

            if allocable_foreign_UTPR_TDs['SHARE_KEY'].sum() > 0:
                allocable_foreign_UTPR_TDs['SHARE_KEY_TOTAL'] = allocable_foreign_UTPR_TDs.groupby(
                    ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'SOURCE']
                ).transform('sum')['SHARE_KEY']
                allocable_foreign_UTPR_TDs['RESCALING_FACTOR'] = 1 / allocable_foreign_UTPR_TDs['SHARE_KEY_TOTAL']
                allocable_foreign_UTPR_TDs['SHARE_KEY'] *= allocable_foreign_UTPR_TDs['RESCALING_FACTOR']

        allocable_domestic_UTPR_TDs = allocable_domestic_UTPR_TDs[
            [
                'PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE',
                'PARENT_COUNTRY_NAME', 'PARTNER_COUNTRY_NAME',
                'PROFITS_BEFORE_TAX_POST_CO', 'ETR', 'SOURCE',
                'IS_DOMESTIC', 'ETR_diff', 'TAX_DEFICIT',
                'collected_through_domestic_QDMTT', 'collected_through_foreign_QDMTT',
                'collected_through_domestic_IIR', 'collected_through_foreign_IIR',
                'collected_through_foreign_UTPR', 'collected_through_domestic_UTPR',
                'JUR', 'Partner Jurisdiction', 'SHARE_KEY',
            ]
        ].copy()

        allocable_domestic_UTPR_TDs = allocable_domestic_UTPR_TDs.rename(
            columns={
                'JUR': 'COLLECTING_COUNTRY_CODE',
                'Partner Jurisdiction': 'COLLECTING_COUNTRY_NAME',
                'SHARE_KEY': 'SHARE_COLLECTED'
            }
        )

        allocable_foreign_UTPR_TDs = allocable_foreign_UTPR_TDs[
            [
                'PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE',
                'PARENT_COUNTRY_NAME', 'PARTNER_COUNTRY_NAME',
                'PROFITS_BEFORE_TAX_POST_CO', 'ETR', 'SOURCE',
                'IS_DOMESTIC', 'ETR_diff', 'TAX_DEFICIT',
                'collected_through_domestic_QDMTT', 'collected_through_foreign_QDMTT',
                'collected_through_domestic_IIR', 'collected_through_foreign_IIR',
                'collected_through_foreign_UTPR', 'collected_through_domestic_UTPR',
                'JUR', 'Partner Jurisdiction', 'SHARE_KEY'
            ]
        ].copy()

        allocable_foreign_UTPR_TDs = allocable_foreign_UTPR_TDs.rename(
            columns={
                'JUR': 'COLLECTING_COUNTRY_CODE',
                'Partner Jurisdiction': 'COLLECTING_COUNTRY_NAME',
                'SHARE_KEY': 'SHARE_COLLECTED'
            }
        )

        allocable_domestic_UTPR_TDs['COLLECTING_COUNTRY_CODE'].unique()

        # Allocating the tax deficits that are not directly allocable
        avg_allocation_keys_domestic = {'JUR': [], 'SHARE_KEY': []}
        avg_allocation_keys_foreign = {'JUR': [], 'SHARE_KEY': []}

        sales_mapping = available_allocation_keys_domestic.drop(
            columns=[
                'UPR_TOTAL', 'ASSETS_TOTAL', 'EMPLOYEES_TOTAL',
                'SHARE_UPR', 'SHARE_ASSETS', 'SHARE_EMPLOYEES', 'SHARE_KEY'
            ]
        )

        if len(UTPR_incl_domestic) + len(UTPR_excl_domestic) > 0:

            domestic_extract = sales_mapping[sales_mapping['COU'] == sales_mapping['JUR']].copy()
            avg_domestic_share_domestic = (
                share_UPR * domestic_extract['UPR'].sum() / sales_mapping['UPR'].sum()
                + share_employees * domestic_extract['EMPLOYEES'].sum() / sales_mapping['EMPLOYEES'].sum()
                + share_assets * domestic_extract['ASSETS'].sum() / sales_mapping['ASSETS'].sum()
            )

            print(avg_domestic_share_domestic)

        else:

            avg_domestic_share_domestic = 0

        # Domestic UTPR

        # For the computation of average allocation keys, we consider all the partner jurisdictions included in the
        # OECD's country-by-country report statistics (not only in the sub-sample excluding loss-making entities but
        # in the whole dataset since allocation keys are sourced in the overall dataset)
        iteration = pd.read_csv(self.path_to_oecd, usecols=['JUR'])['JUR'].unique()

        # We extend this set to countries implementing the UTPR but never reported as partners in the data
        # They will get a share of allocation key of 0 and thus 0 revenue gains (except if we have them as parents)
        iteration = np.union1d(np.union1d(iteration, UTPR_incl_domestic), UTPR_excl_domestic)

        # if among_countries_implementing:
        #     iteration = UTPR_incl_domestic.copy()
        # else:
        #     iteration = np.union1d(
        #         UTPR_incl_domestic,
        #         np.union1d(
        #             self.oecd['Partner jurisdiction (alpha-3 code)'].unique(),
        #             np.union1d(
        #                 self.oecd['Parent jurisdiction (alpha-3 code)'].unique(),
        #                 full_sample_df['PARENT_COUNTRY_CODE'].unique()
        #             )
        #         )
        #     )

        for country in iteration:

            sales_mapping_foreign_MNEs = sales_mapping[sales_mapping['COU'] != country].copy()

            sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs[
                sales_mapping_foreign_MNEs['COU'] != sales_mapping_foreign_MNEs['JUR']
            ].copy()

            country_extract = sales_mapping_foreign_MNEs[sales_mapping_foreign_MNEs['JUR'] == country].copy()

            avg_allocation_keys_domestic['JUR'].append(country)

            avg_allocation_keys_domestic['SHARE_KEY'].append(
                share_UPR * country_extract['UPR'].sum() / sales_mapping_foreign_MNEs['UPR'].sum()
                + share_employees * country_extract['EMPLOYEES'].sum() / sales_mapping_foreign_MNEs['EMPLOYEES'].sum()
                + share_assets * country_extract['ASSETS'].sum() / sales_mapping_foreign_MNEs['ASSETS'].sum()
            )

        avg_allocation_keys_domestic = pd.DataFrame(avg_allocation_keys_domestic)

        print(
            "Average domestic allocation key for France:",
            avg_allocation_keys_domestic[avg_allocation_keys_domestic['JUR'] == 'FRA'].iloc[0, 1]
        )
        print(
            "Before the re-scaling of the domestic average allocation keys, they sum to:",
            avg_allocation_keys_domestic['SHARE_KEY'].sum()
        )
        # avg_allocation_keys['SHARE_UPR'] = avg_allocation_keys['SHARE_UPR']

        # We re-scale the average allocation keys so that they sum to 1:
        #   - over the set of implementing countries if among_countries_implementing is True;
        #   - else over the set of all partner jurisdictions.
        # if among_countries_implementing:
        #     print(
        #         "Before the re-scaling of the average allocation keys, they sum to:",
        #         avg_allocation_keys_domestic['SHARE_KEY'].sum()
        #     )
        #     if avg_allocation_keys_domestic['SHARE_KEY'].sum() > 0:
        #         rescaling_factor = 1 / avg_allocation_keys_domestic['SHARE_KEY'].sum()
        #     else:
        #         rescaling_factor = 1
        #     avg_allocation_keys_domestic['SHARE_KEY'] *= rescaling_factor

        #     avg_allocation_keys_domestic = avg_allocation_keys_domestic[
        #         avg_allocation_keys_domestic['JUR'].isin(UTPR_incl_domestic)
        #     ].copy()

        # Foreign UTPR
        sales_mapping = available_allocation_keys_foreign.drop(
            columns=[
                'UPR_TOTAL', 'ASSETS_TOTAL', 'EMPLOYEES_TOTAL',
                'SHARE_UPR', 'SHARE_ASSETS', 'SHARE_EMPLOYEES', 'SHARE_KEY'
            ]
        )

        if len(UTPR_incl_domestic) + len(UTPR_excl_domestic) > 0:

            domestic_extract = sales_mapping[sales_mapping['COU'] == sales_mapping['JUR']].copy()
            avg_domestic_share_foreign = (
                share_UPR * domestic_extract['UPR'].sum() / sales_mapping['UPR'].sum()
                + share_employees * domestic_extract['EMPLOYEES'].sum() / sales_mapping['EMPLOYEES'].sum()
                + share_assets * domestic_extract['ASSETS'].sum() / sales_mapping['ASSETS'].sum()
            )

            print(avg_domestic_share_foreign)

        else:

            avg_domestic_share_foreign = 0

        # For the computation of average allocation keys, we consider all the partner jurisdictions included in the
        # OECD's country-by-country report statistics (not only in the sub-sample excluding loss-making entities but
        # in the whole dataset since allocation keys are sourced in the overall dataset)
        iteration = pd.read_csv(self.path_to_oecd, usecols=['JUR'])['JUR'].unique()
        iteration = iteration[~np.isin(iteration, ['STA', 'FJT'])].copy()

        # We extend this set to countries implementing the UTPR but never reported as partners in the data
        # They will get a share of allocation key of 0 and thus 0 revenue gains (except if we have them as parents)
        iteration = np.union1d(np.union1d(iteration, UTPR_incl_domestic), UTPR_excl_domestic)

        # if among_countries_implementing:
        #     iteration = UTPR_incl_domestic + UTPR_excl_domestic
        # else:
        #     iteration = np.union1d(
        #         UTPR_incl_domestic + UTPR_excl_domestic,
        #         np.union1d(
        #             self.oecd['Partner jurisdiction (alpha-3 code)'].unique(),
        #             np.union1d(
        #                 self.oecd['Parent jurisdiction (alpha-3 code)'].unique(),
        #                 full_sample_df['PARENT_COUNTRY_CODE'].unique()
        #             )
        #         )
        #     )

        for country in iteration:

            sales_mapping_foreign_MNEs = sales_mapping[sales_mapping['COU'] != country].copy()

            sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs[
                sales_mapping_foreign_MNEs['COU'] != sales_mapping_foreign_MNEs['JUR']
            ].copy()

            country_extract = sales_mapping_foreign_MNEs[sales_mapping_foreign_MNEs['JUR'] == country].copy()

            avg_allocation_keys_foreign['JUR'].append(country)

            avg_allocation_keys_foreign['SHARE_KEY'].append(
                share_UPR * country_extract['UPR'].sum() / sales_mapping_foreign_MNEs['UPR'].sum()
                + share_employees * country_extract['EMPLOYEES'].sum() / sales_mapping_foreign_MNEs['EMPLOYEES'].sum()
                + share_assets * country_extract['ASSETS'].sum() / sales_mapping_foreign_MNEs['ASSETS'].sum()
            )

        avg_allocation_keys_foreign = pd.DataFrame(avg_allocation_keys_foreign)

        print(
            "Average foreign allocation key for France:",
            avg_allocation_keys_foreign[avg_allocation_keys_foreign['JUR'] == 'FRA'].iloc[0, 1]
        )
        print(
            "Before the re-scaling of the foreign average allocation keys, they sum to:",
            avg_allocation_keys_foreign['SHARE_KEY'].sum()
        )
        # avg_allocation_keys['SHARE_UPR'] = avg_allocation_keys['SHARE_UPR']

        # We re-scale the average allocation keys so that they sum to 1:
        #   - over the set of implementing countries if among_countries_implementing is True;
        #   - else over the set of all partner jurisdictions.
        # if among_countries_implementing:
        #     print(
        #         "Before the re-scaling of the average allocation keys, they sum to:",
        #         avg_allocation_keys_foreign['SHARE_KEY'].sum()
        #     )
        #     if avg_allocation_keys_foreign['SHARE_KEY'].sum() > 0:
        #         rescaling_factor = 1 / avg_allocation_keys_foreign['SHARE_KEY'].sum()
        #     else:
        #         rescaling_factor = 1
        #     avg_allocation_keys_foreign['SHARE_KEY'] *= rescaling_factor

        #     avg_allocation_keys_foreign = avg_allocation_keys_foreign[
        #         avg_allocation_keys_foreign['JUR'].isin(UTPR_incl_domestic + UTPR_excl_domestic)
        #     ].copy()

        # Alternative approach for determining average allocation keys?
        # if not among_countries_implementing:

        #     sales_mapping = available_allocation_keys_domestic.copy()

        #     domestic_extract = sales_mapping[sales_mapping['COU'] == sales_mapping['JUR']].copy()

        #     avg_domestic_share = (
        #         share_UPR * domestic_extract['UPR'].sum() / sales_mapping['UPR'].sum()
        #         + share_employees * domestic_extract['EMPLOYEES'].sum() / sales_mapping['EMPLOYEES'].sum()
        #         + share_assets * domestic_extract['ASSETS'].sum() / sales_mapping['ASSETS'].sum()
        #     )

        # avg_allocation_keys = {}

        # for UTPR_type, sales_mapping in zip(
        #     ['domestic', 'foreign'],
        #     [available_allocation_keys_domestic.copy(), available_allocation_keys_foreign.copy()]
        # ):

        #     sales_mapping['IS_FOREIGN'] = sales_mapping['COU'] != sales_mapping['JUR']

        #     sales_mapping['UPR_x_IS_FOREIGN'] = sales_mapping['UPR'] * sales_mapping['IS_FOREIGN']
        #     sales_mapping['EMPLOYEES_x_IS_FOREIGN'] = sales_mapping['EMPLOYEES'] * sales_mapping['IS_FOREIGN']
        #     sales_mapping['ASSETS_x_IS_FOREIGN'] = sales_mapping['ASSETS'] * sales_mapping['IS_FOREIGN']

        #     if self.year == 2018 and self.China_treatment_2018 == "2017_CbCR":

        #         multiplier = sales_mapping['COU'] == 'CHN'
        #         multiplier *= self.growth_rates.set_index("CountryGroupName").loc['World', 'uprusd1817']
        #         multiplier = multiplier.map(lambda x: {0: 1}.get(x, x))

        #     else:

        #         multiplier = 1

        #     sales_mapping['UPR_x_IS_FOREIGN'] *= multiplier
        #     sales_mapping['EMPLOYEES_x_IS_FOREIGN'] *= multiplier
        #     sales_mapping['ASSETS_x_IS_FOREIGN'] *= multiplier

        #     sales_mapping['UPR_x_IS_FOREIGN'] = sales_mapping['UPR_x_IS_FOREIGN'].astype(float)
        #     sales_mapping['EMPLOYEES_x_IS_FOREIGN'] = sales_mapping['EMPLOYEES_x_IS_FOREIGN'].astype(float)
        #     sales_mapping['ASSETS_x_IS_FOREIGN'] = sales_mapping['ASSETS_x_IS_FOREIGN'].astype(float)

        #     sales_mapping = sales_mapping.groupby(
        #         ['JUR', 'Partner Jurisdiction']
        #     ).sum()[
        #         ['UPR_x_IS_FOREIGN', 'EMPLOYEES_x_IS_FOREIGN', 'ASSETS_x_IS_FOREIGN']
        #     ].reset_index()

        #     sales_mapping = sales_mapping.rename(
        #         columns={col: col.replace('_x_IS_FOREIGN', '') for col in sales_mapping.columns}
        #     )

        #     for col in ['UPR', 'EMPLOYEES', 'ASSETS']:

        #         sales_mapping[f'{col}_TOTAL'] = sales_mapping[col].sum()
        #         sales_mapping[f'SHARE_{col}'] = sales_mapping[col] / sales_mapping[f'{col}_TOTAL']

        #     sales_mapping['SHARE_KEY'] = (
        #         share_UPR * sales_mapping['SHARE_UPR']
        #         + share_employees * sales_mapping['SHARE_EMPLOYEES']
        #         + share_assets * sales_mapping['SHARE_ASSETS']
        #     )

        #     avg_allocation_keys[UTPR_type] = sales_mapping[['JUR', 'Partner Jurisdiction', 'SHARE_KEY']].copy()

        # avg_allocation_keys_domestic = avg_allocation_keys['domestic'].copy()
        # avg_allocation_keys_foreign = avg_allocation_keys['foreign'].copy()

        # if not among_countries_implementing:

        #     avg_allocation_keys_domestic['SHARE_KEY'] *= (1 - avg_domestic_share)
        #     avg_allocation_keys_foreign['SHARE_KEY'] *= (1 - avg_domestic_share)

        #     domestic_UTPR_domestic_extract = other_domestic_UTPR_TDs.copy()
        #     foreign_UTPR_domestic_extract = other_foreign_UTPR_TDs.copy()

        #     domestic_UTPR_domestic_extract['JUR'] = domestic_UTPR_domestic_extract['PARENT_COUNTRY_CODE'].values
        #     domestic_UTPR_domestic_extract['Partner Jurisdiction'] = domestic_UTPR_domestic_extract[
        #         'PARENT_COUNTRY_NAME'
        #     ].values
        #     domestic_UTPR_domestic_extract['SHARE_KEY'] = avg_domestic_share

        #     foreign_UTPR_domestic_extract['JUR'] = foreign_UTPR_domestic_extract['PARENT_COUNTRY_CODE'].values
        #     foreign_UTPR_domestic_extract['Partner Jurisdiction'] = foreign_UTPR_domestic_extract[
        #         'PARENT_COUNTRY_NAME'
        #     ].values
        #     foreign_UTPR_domestic_extract['SHARE_KEY'] = avg_domestic_share

        avg_allocation_keys_domestic['TEMP_KEY'] = 1
        other_domestic_UTPR_TDs['TEMP_KEY'] = 1

        other_domestic_UTPR_TDs = other_domestic_UTPR_TDs.merge(
            avg_allocation_keys_domestic,
            how='left',
            on='TEMP_KEY'
        ).drop(columns=['TEMP_KEY'])

        print("Check 1")

        other_domestic_UTPR_TDs = other_domestic_UTPR_TDs[
            other_domestic_UTPR_TDs['PARENT_COUNTRY_CODE'] != other_domestic_UTPR_TDs['JUR']
        ].copy()

        if among_countries_implementing:
            other_domestic_UTPR_TDs = other_domestic_UTPR_TDs[
                other_domestic_UTPR_TDs['JUR'].isin(UTPR_incl_domestic)
            ].copy()

        if not other_domestic_UTPR_TDs.empty:
            other_domestic_UTPR_TDs['SHARE_KEY_TOTAL'] = other_domestic_UTPR_TDs.groupby(
                ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'SOURCE']
            ).transform('sum')['SHARE_KEY']

            if among_countries_implementing:
                other_domestic_UTPR_TDs['RESCALING_FACTOR'] = other_domestic_UTPR_TDs['PARENT_COUNTRY_CODE'].isin(
                    UTPR_incl_domestic
                )
                other_domestic_UTPR_TDs['RESCALING_FACTOR'] *= (
                    1 - avg_domestic_share_domestic
                ) / other_domestic_UTPR_TDs['SHARE_KEY_TOTAL']
                other_domestic_UTPR_TDs['RESCALING_FACTOR'] = other_domestic_UTPR_TDs.apply(
                    lambda row: {0: 1 / row['SHARE_KEY_TOTAL']}.get(
                        row['RESCALING_FACTOR'], row['RESCALING_FACTOR']
                    ),
                    axis=1
                )
            else:
                other_domestic_UTPR_TDs['RESCALING_FACTOR'] = (
                    1 - avg_domestic_share_domestic
                ) / other_domestic_UTPR_TDs['SHARE_KEY_TOTAL']

        else:

            other_domestic_UTPR_TDs['SHARE_KEY_TOTAL'] = other_domestic_UTPR_TDs['SHARE_KEY']
            other_domestic_UTPR_TDs['RESCALING_FACTOR'] = other_domestic_UTPR_TDs['SHARE_KEY']

        print("Check 2")

        other_domestic_UTPR_TDs['SHARE_KEY'] *= other_domestic_UTPR_TDs['RESCALING_FACTOR']

        self.other_domestic_UTPR_TDs = other_domestic_UTPR_TDs.copy()

        for parent_country in other_domestic_UTPR_TDs['PARENT_COUNTRY_CODE'].unique():
            if parent_country in UTPR_incl_domestic:
                ser = other_domestic_UTPR_TDs[other_domestic_UTPR_TDs['PARENT_COUNTRY_CODE'] == parent_country].copy()
                ser = ser.iloc[0].copy()

                ser.loc['JUR'] = parent_country
                ser.loc['SHARE_KEY'] = avg_domestic_share_domestic

                other_domestic_UTPR_TDs = pd.concat([other_domestic_UTPR_TDs, pd.DataFrame(ser).T], axis=0)

            else:
                continue

        # other_domestic_UTPR_TDs = other_domestic_UTPR_TDs.drop(columns=['SHARE_KEY_TOTAL', 'RESCALING_FACTOR'])

        # if not among_countries_implementing:

        #     other_domestic_UTPR_TDs = pd.concat([other_domestic_UTPR_TDs, domestic_UTPR_domestic_extract])

        other_domestic_UTPR_TDs = other_domestic_UTPR_TDs.rename(
            columns={
                'JUR': 'COLLECTING_COUNTRY_CODE',
                'Partner Jurisdiction': 'COLLECTING_COUNTRY_NAME',
                'SHARE_KEY': 'SHARE_COLLECTED'
            }
        )

        avg_allocation_keys_foreign['TEMP_KEY'] = 1
        other_foreign_UTPR_TDs['TEMP_KEY'] = 1

        other_foreign_UTPR_TDs = other_foreign_UTPR_TDs.merge(
            avg_allocation_keys_foreign,
            how='left',
            on='TEMP_KEY'
        ).drop(columns=['TEMP_KEY'])

        print("Check 3")

        other_foreign_UTPR_TDs = other_foreign_UTPR_TDs[
            other_foreign_UTPR_TDs['PARENT_COUNTRY_CODE'] != other_foreign_UTPR_TDs['JUR']
        ].copy()

        import time

        start_time = time.time()

        if among_countries_implementing:
            other_foreign_UTPR_TDs = other_foreign_UTPR_TDs[
                other_foreign_UTPR_TDs['JUR'].isin(np.union1d(UTPR_incl_domestic, UTPR_excl_domestic))
            ].copy()

        print('Check 3bis')

        end_time = time.time()

        print(end_time - start_time, 'seconds')

        if not other_foreign_UTPR_TDs.empty:

            start_time = time.time()

            other_foreign_UTPR_TDs['SHARE_KEY_TOTAL'] = other_foreign_UTPR_TDs.groupby(
                ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'SOURCE']
            ).transform('sum')['SHARE_KEY']

            print('Check 3c')

            end_time = time.time()

            print(end_time - start_time, 'seconds')

            start_time = time.time()
            if among_countries_implementing:
                other_foreign_UTPR_TDs['RESCALING_FACTOR'] = other_foreign_UTPR_TDs['PARENT_COUNTRY_CODE'].isin(
                    UTPR_incl_domestic + UTPR_excl_domestic
                )
                other_foreign_UTPR_TDs['RESCALING_FACTOR'] *= (
                    1 - avg_domestic_share_foreign
                ) / other_foreign_UTPR_TDs['SHARE_KEY_TOTAL']
                other_foreign_UTPR_TDs['RESCALING_FACTOR'] = other_foreign_UTPR_TDs.apply(
                    lambda row: {0: 1 / row['SHARE_KEY_TOTAL']}.get(
                        row['RESCALING_FACTOR'], row['RESCALING_FACTOR']
                    ),
                    axis=1
                )
            else:
                other_foreign_UTPR_TDs['RESCALING_FACTOR'] = (
                    1 - avg_domestic_share_foreign
                ) / other_foreign_UTPR_TDs['SHARE_KEY_TOTAL']

            print('Check 3d')

            end_time = time.time()

            print(end_time - start_time, 'seconds')

        else:

            other_foreign_UTPR_TDs['SHARE_KEY_TOTAL'] = other_foreign_UTPR_TDs['SHARE_KEY']
            other_foreign_UTPR_TDs['RESCALING_FACTOR'] = other_foreign_UTPR_TDs['SHARE_KEY']

        other_foreign_UTPR_TDs['SHARE_KEY'] *= other_foreign_UTPR_TDs['RESCALING_FACTOR']

        print("Check 4")

        for parent_country in other_foreign_UTPR_TDs['PARENT_COUNTRY_CODE'].unique():
            if parent_country in UTPR_incl_domestic + UTPR_excl_domestic:
                df = other_foreign_UTPR_TDs[other_foreign_UTPR_TDs['PARENT_COUNTRY_CODE'] == parent_country].copy()

                jur = df['JUR'].unique()
                jur = jur[0]

                df = df[df['JUR'] == jur].copy()

                df['JUR'] = parent_country
                df['SHARE_KEY'] = avg_domestic_share_domestic

                other_foreign_UTPR_TDs = pd.concat([other_foreign_UTPR_TDs, df], axis=0)

            else:
                continue

        # other_foreign_UTPR_TDs = other_foreign_UTPR_TDs.drop(columns=['SHARE_KEY_TOTAL', 'RESCALING_FACTOR'])

        # if not among_countries_implementing:

        #     other_foreign_UTPR_TDs = pd.concat([other_foreign_UTPR_TDs, foreign_UTPR_domestic_extract])

        other_foreign_UTPR_TDs = other_foreign_UTPR_TDs.rename(
            columns={
                'JUR': 'COLLECTING_COUNTRY_CODE',
                'Partner Jurisdiction': 'COLLECTING_COUNTRY_NAME',
                'SHARE_KEY': 'SHARE_COLLECTED'
            }
        )

        # --- Other than UTPR

        non_UTPR_extract = full_sample_df[
            np.logical_and(
                ~full_sample_df['collected_through_domestic_UTPR'],
                ~full_sample_df['collected_through_foreign_UTPR']
            )
        ].copy()

        print("Check 5")

        if not non_UTPR_extract.empty:

            non_UTPR_extract['SHARE_COLLECTED'] = 1

            non_UTPR_extract['COLLECTING_COUNTRY_CODE'] = non_UTPR_extract.apply(
                (
                    lambda row: row['PARENT_COUNTRY_CODE']
                    if row['collected_through_domestic_IIR'] or row['collected_through_foreign_IIR']
                    else row['PARTNER_COUNTRY_CODE']
                ),
                axis=1
            )

            non_UTPR_extract['COLLECTING_COUNTRY_NAME'] = non_UTPR_extract.apply(
                (
                    lambda row: row['PARENT_COUNTRY_NAME']
                    if row['collected_through_domestic_IIR'] or row['collected_through_foreign_IIR']
                    else row['PARTNER_COUNTRY_NAME']
                ),
                axis=1
            )

        full_sample_df = pd.concat(
            [
                non_UTPR_extract,
                allocable_domestic_UTPR_TDs, allocable_foreign_UTPR_TDs,
                other_foreign_UTPR_TDs, other_domestic_UTPR_TDs
            ],
            axis=0
        )

        full_sample_df['collected_through_domestic_UTPR'] *= full_sample_df['COLLECTING_COUNTRY_CODE'].isin(
            UTPR_incl_domestic
        )
        full_sample_df['collected_through_foreign_UTPR'] *= full_sample_df['COLLECTING_COUNTRY_CODE'].isin(
            UTPR_incl_domestic + UTPR_excl_domestic
        )

        collected_columns = list(
            np.unique(
                full_sample_df.columns[
                    full_sample_df.columns.map(lambda x: x.startswith("collected_through_"))
                ]
            )
        )

        full_sample_df['ALLOCATED_TAX_DEFICIT'] = (
            full_sample_df['TAX_DEFICIT']
            * full_sample_df['SHARE_COLLECTED']
            * full_sample_df[collected_columns].sum(axis=1)
        )
        full_sample_df['ALLOCATED_TAX_DEFICIT'] = full_sample_df['ALLOCATED_TAX_DEFICIT'].astype(float)

        if not return_bilateral_details:

            if self.year == 2018 and self.China_treatment_2018 == '2017_CbCR':

                multiplier = self.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                multiplier = full_sample_df['PARENT_COUNTRY_CODE'].map(
                    lambda x: {'CHN': multiplier}.get(x, 1)
                )

                for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                    full_sample_df[col] *= multiplier

            return full_sample_df.groupby(
                ['COLLECTING_COUNTRY_CODE']
            ).agg(
                {'COLLECTING_COUNTRY_NAME': 'first', 'ALLOCATED_TAX_DEFICIT': 'sum'}
            ).reset_index()

        else:

            return full_sample_df.copy()

    # ------------------------------------------------------------------------------------------------------------------
    # --- OLDER METHODS ------------------------------------------------------------------------------------------------

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
        if self.year == 2018 and self.China_treatment_2018 == '2017_CbCR':

            multiplier = merged_df['Parent jurisdiction (alpha-3 code)'] == 'CHN'
            multiplier *= self.multiplier_2017_2021 * self.USD_to_EUR_2017
            multiplier = multiplier.map(
                lambda x: self.multiplier_2021 * self.USD_to_EUR if x == 0 else x
            )

        else:

            multiplier = self.multiplier_2021 * self.USD_to_EUR

        merged_df['tax_deficit_15'] /= (merged_df['CIT revenue'] * multiplier / 100)

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
                merged_df['CIT revenue'] * multiplier / 100
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
            SGP_CYM_treatment=self.SGP_CYM_treatment,
            China_treatment_2018=self.China_treatment_2018,
            use_adjusted_profits=self.use_adjusted_profits,
            average_ETRs=self.average_ETRs_bool,
            years_for_avg_ETRs=self.years_for_avg_ETRs,
            carve_outs=True,
            carve_out_rate_assets=self.carve_out_rate_assets,
            carve_out_rate_payroll=self.carve_out_rate_payroll,
            depreciation_only=self.depreciation_only,
            exclude_inventories=self.exclude_inventories,
            ex_post_ETRs=self.ex_post_ETRs,
            add_AUT_AUT_row=self.add_AUT_AUT_row,
            extended_dividends_adjustment=self.extended_dividends_adjustment,
            use_TWZ_for_CbCR_newcomers=self.use_TWZ_for_CbCR_newcomers,
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
            SGP_CYM_treatment=self.SGP_CYM_treatment,
            China_treatment_2018=self.China_treatment_2018,
            use_adjusted_profits=self.use_adjusted_profits,
            average_ETRs=self.average_ETRs_bool,
            years_for_avg_ETRs=self.years_for_avg_ETRs,
            carve_outs=False,
            add_AUT_AUT_row=self.add_AUT_AUT_row,
            extended_dividends_adjustment=self.extended_dividends_adjustment,
            use_TWZ_for_CbCR_newcomers=self.use_TWZ_for_CbCR_newcomers,
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


if __name__ == '__main__':

    print("Command line use to be determined?")
