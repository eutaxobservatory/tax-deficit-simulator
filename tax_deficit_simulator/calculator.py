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
    apply_upgrade_factor, online_data_paths, get_growth_rates, country_name_corresp, url_base


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
        alternative_imputation=True,
        non_haven_TD_imputation_selection='EU',
        sweden_treatment='adjust',
        belgium_treatment='replace',
        SGP_CYM_treatment='replace',
        use_adjusted_profits=True,
        average_ETRs=True,
        years_for_avg_ETRs=[2016, 2017, 2018, 2019, 2020],
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
        code disregards country-by-country data and uses TWZ data. Instead, if "adjust" is chosen, the code corrects for
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

        self.fetch_data_online = fetch_data_online

        self.load_xchange_growth_rates()

        # if year not in ['last', 2016, 2017, 2018, 2019, 2020]:
        #     # Due to the availability of country-by-country report statistics
        #     raise Exception(
        #         'Five years can be chosen for macro computations: 2016, 2017, 2018, 2019, or 2020.'
        #         + ' In addition, one can choose to retain the last year in which countries appear in CbCR data'
        #         + ' with a sufficiently detailed partner country breakdown (i.e., not continental nor minimal).'
        #     )

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
                + 'the latest valid year available (pass SGP_CYM_treatment="replace").'
            )

        if add_AUT_AUT_row is None:
            # AUT-AUT country pair missing in the 2017 sub-sample of profit-making entities
            raise Exception(
                'You need to indicate whether to add the 2017 AUT-AUT row from the full sample (including both negative'
                + ' and positive profits) or not, via the "add_AUT_AUT_row" argument.'
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

        if use_TWZ_for_CbCR_newcomers and year == 2016:
            raise Exception(
                "The argument 'use_TWZ_for_CbCR_newcomers' can only be used as of 2017. If it is set to True, we do as"
                + " if countries reporting CbCR data in the year considered but not in the previous one were absent"
                + " from the OECD's data and required the use of TWZ data (except for tax havens). Purely"
                + " methodological detail to challenge our use of TWZ data."
            )

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

        # # Storing the chosen year
        # self.year = year

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

        self.sweden_adj_ratios = {
            2016: (342 - 200) / 342,
            2017: (512 - 266) / 512,
            2018: (49.1 - 29.8) / 49.1,
            2019: 1,
            2020: 1,
        }

        # Average exchange rate over the relevant year, extracted from benchmark computations run on Stata
        # Source: European Central Bank
        xrates = self.xrates.set_index('year')
        self.USD_to_EUR_rates = {}
        # Gross growth rate of worldwide GDP in current EUR between 2016 and 2021
        # Extracted from the benchmark computations run on Stata
        self.multipliers_2021 = {}
        # Filling in the two dicts with a value for each year
        for y in (2016, 2017, 2018, 2019, 2020):
            self.USD_to_EUR_rates[y] = 1 / xrates.loc[y, 'usd']
            self.multipliers_2021[y] = GDP_growth_rates.loc['World', f'upreur21{y - 2000}']

        self.COUNTRIES_WITH_MINIMUM_REPORTING = {
            2016: ['FIN', 'IRL', 'KOR', 'NLD'],
            2017: ['FIN', 'IRL', 'KOR', 'NLD'],
            2018: ['FIN', 'IRL', 'KOR', 'NZL'],
            2019: ['IRL', 'NZL'],
            2020: ['IRL', 'NZL'],
        }

        self.COUNTRIES_WITH_CONTINENTAL_REPORTING = {
            2016: ['AUT', 'NOR', 'SVN', 'SWE'],                         # Slovenia is not really a continental split
            2017: ['AUT', 'GBR', 'GRC', 'IMN', 'NOR', 'SVN', 'SWE'],    # Romania?
            2018: ['AUT', 'GBR', 'GRC', 'IMN', 'LTU', 'SVN', 'SWE'],    # Lithuania?
            2019: ['AUT', 'FIN', 'GBR', 'KOR', 'MUS', 'SVN', 'SWE'],    # Lithuania?
            2020: ['AUT', 'BGR', 'FIN', 'GBR', 'KOR', 'SVN', 'SWE'],    # Lithuania? Tunisia? Bulgaria also unclear
        }

        self.belgium_partners_for_adjustment = {
            2016: ["NLD"],
            2017: ["GBR"],
            2018: ['GBR', 'NLD'],
            2019: ['GBR', 'NLD'],
            2020: [],
        }
        self.belgium_years_for_adjustment = {
            'NLD': [2017, 2020],
            'GBR': [2016, 2020],
        }

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
            self.exclusion_threshold_revenues = 10 * 10**6
            self.exclusion_threshold_profits = 1 * 10**6
            # self.exclusion_thresholds_revenues = {
            #     y: 10 * 10**6 / self.USD_to_EUR_rates[y] for y in (2016, 2017, 2018, 2019, 2020)
            # }
            # self.exclusion_thresholds_profits = {
            #     y: 1 * 10**6 / self.USD_to_EUR_rates[y] for y in (2016, 2017, 2018, 2019, 2020)
            # }

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

        if self.fetch_data_online:
            raw_data = pd.read_csv(online_data_paths['path_to_xrates'])

        else:
            raw_data = pd.read_csv(os.path.join(path_to_data, "eurofxref-hist.csv"))

        raw_data = raw_data[['Date', 'USD']].copy()
        raw_data['YEAR'] = raw_data['Date'].map(lambda date: date[:date.find('-')]).astype(int)
        raw_data = raw_data[np.logical_and(raw_data['YEAR'] >= 2012, raw_data['YEAR'] <= 2022)].copy()

        average_exchange_rates = raw_data.groupby('YEAR').agg({'USD': 'mean'}).reset_index()
        average_exchange_rates = average_exchange_rates.rename(columns={"YEAR": "year", "USD": "usd"})

        self.xrates = average_exchange_rates.copy()

        # --- Growth rates

        if self.fetch_data_online:
            raw_data = pd.read_excel(online_data_paths['path_to_WEO'], engine="openpyxl")

        else:
            raw_data = pd.read_excel(os.path.join(path_to_data, "WEOOct2021group.xlsx"), engine="openpyxl")

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

        # One-year, two-year, three-year, (four-year, and five-year) growth rates for USD and EUR GDP
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

            if t >= 19:

                # Four-year growth rates
                t_4 = t - 4
                # GDP in USD
                extract[f"uprusd{t}{t_4}"] = extract[f"y20{t}"] / extract[f"y20{t_4}"]
                # GDP in EUR
                extract[f"upreur{t}{t_4}"] = extract[f"eurgdp20{t}"] / extract[f"eurgdp20{t_4}"]

                # Five-year growth rates
                t_5 = t - 5
                # GDP in USD
                extract[f"uprusd{t}{t_5}"] = extract[f"y20{t}"] / extract[f"y20{t_5}"]
                # GDP in EUR
                extract[f"upreur{t}{t_5}"] = extract[f"eurgdp20{t}"] / extract[f"eurgdp20{t_5}"]

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
                'ref_area': 'country_code',
                'time': 'year'
            }
        )

        # Selecting relevant observations
        # All genders
        employee_population = employee_population[employee_population['sex'] == 'SEX_T'].copy()
        employee_population = employee_population.drop(columns=['sex'])
        employee_population['sex'] = 'to'
        # Focusing on a relatively close period
        employee_population = employee_population[employee_population['year'] >= 2014].reset_index(drop=True)
        # Focusing on wage employees
        employee_population = employee_population[
            employee_population['classif1'].isin(['STE_AGGREGATE_EES', 'STE_ICSE93_1'])
        ].copy()
        # Keeping the "Aggregate" status when it is available
        employee_population = employee_population.sort_values(
            by=['country_code', 'year', 'classif1']
        ).drop_duplicates(subset=['country_code', 'year'], keep='first')
        employee_population = employee_population.drop(columns=['classif1'])
        employee_population['status'] = 'wage'

        # Selecting relevant columns
        employee_population = employee_population[['year', 'country_code', 'obs_value', 'status']].copy()

        # Renaming the column with the values of interest
        employee_population = employee_population.rename(columns={'obs_value': 'emp'})

        # Indexing by year in a datetime format
        employee_population['year'] = pd.to_datetime(employee_population['year'], format='%Y')
        employee_population = employee_population.set_index('year')

        # Computing the interpolation values
        df_interpol = employee_population.groupby(['country_code']).resample('A').mean()
        df_interpol['emp_ipo'] = df_interpol['emp'].interpolate()
        df_interpol = df_interpol.reset_index()
        df_interpol['year'] = df_interpol['year'].dt.year

        # Employee population dataset with interpolated values
        employee_population = df_interpol[['country_code', 'year', 'emp_ipo']].rename(columns={'emp_ipo': 'emp'})

        # "Correcting" the country code for Kosovo so that we can merge with earnings later on
        employee_population['country_code'] = employee_population['country_code'].map(
            lambda country: {'KOS': 'XXK'}.get(country, country)
        )

        # --- Cleaning ILO data on mean earnings

        # Selecting relevant observations
        # All sectors
        earnings = earnings[earnings['classif1'].map(lambda classif: 'total' in classif.lower())].copy()
        # Focusing on current USD for the currency
        earnings = earnings[earnings['classif2'] == 'CUR_TYPE_USD'].copy()
        # All genders
        earnings = earnings[earnings['sex'] == 'SEX_T'].copy()
        # Recent years
        earnings = earnings[earnings['time'] >= 2014].copy()

        # Selecting columns of interest with relevant variable names
        # - Removing columns for which selection is done
        earnings = earnings.drop(columns=['sex', 'classif2'])
        # - Selecting only one type of aggregate sector
        earnings = earnings.sort_values(by=['time', 'ref_area', 'classif1'])
        earnings = earnings.drop_duplicates(subset=['ref_area', 'time'], keep='first')
        earnings = earnings.drop(columns=['classif1'])
        # - Renaming columns
        earnings = earnings.rename(columns={'time': 'year', 'ref_area': 'country_code', 'obs_value': 'earn'})
        # - Cleaning indices
        earnings = earnings.reset_index(drop=True)

        # Moving to annual earnings
        earnings['earn'] *= 12

        # "Correcting" the country code for Kosovo so that we can add the continent later on
        earnings['country_code'] = earnings['country_code'].map(
            lambda country: {'KOS': 'XXK'}.get(country, country)
        )

        # Indexing by year in a datetime format
        earnings_interpolated = earnings.copy()
        earnings_interpolated['year'] = pd.to_datetime(earnings_interpolated['year'], format='%Y')
        earnings_interpolated = earnings_interpolated.set_index('year')

        # Computing the interpolation values
        df_interpol = earnings_interpolated.groupby(['country_code']).resample('A').mean()
        df_interpol['earn_ipo'] = df_interpol['earn'].interpolate()
        df_interpol = df_interpol.reset_index()
        df_interpol['year'] = df_interpol['year'].dt.year

        # Employee population dataset with interpolated values
        earnings_interpolated = df_interpol[['country_code', 'year', 'earn_ipo']].rename(columns={'earn_ipo': 'earn'})

        # Adding continent codes
        geographies = pd.read_csv(os.path.join(path_to_dir, 'data', 'geographies.csv'))
        geographies['CONTINENT_CODE'] = geographies['CONTINENT_CODE'].map(
            lambda continent: {'NAMR': 'AMR', 'SAMR': 'AMR'}.get(continent, continent)
        )
        geographies = geographies[['CODE', 'CONTINENT_CODE']].drop_duplicates()

        earnings_merged = earnings.merge(
            geographies,
            how='left',
            left_on='country_code', right_on='CODE'
        ).drop(columns='CODE')

        # Correcting a few continents to match the previous methodology
        earnings_merged['CONTINENT_CODE'] = earnings_merged.apply(
            lambda row: 'EUR' if row['country_code'] == 'RUS' else row['CONTINENT_CODE'],
            axis=1
        )
        earnings_merged['CONTINENT_CODE'] = earnings_merged.apply(
            lambda row: 'ASIA' if row['country_code'] == 'CYP' else row['CONTINENT_CODE'],
            axis=1
        )

        # Adding employee count
        earnings_merged = earnings_merged.merge(
            employee_population,
            how='left',
            on=['country_code', 'year']
        )

        # Deducing yearly global mean earnings (for the FJT and GRPS observations)
        earnings_merged['numerator'] = earnings_merged['emp'] * earnings_merged['earn']

        global_averages = earnings_merged.groupby('year').sum()[['numerator', 'emp']]
        global_averages['earn'] = global_averages['numerator'] / global_averages['emp']
        global_averages = global_averages.reset_index()

        temp = global_averages.copy()
        temp['country_code'] = 'FJT'
        global_averages['country_code'] = 'GRPS'
        global_averages = pd.concat([global_averages, temp], axis=0)

        # Deducing yearly continental mean earnings (for continental observations and "Other [...]")
        continental_averages = earnings_merged.groupby(['year', 'CONTINENT_CODE']).sum()[['numerator', 'emp']]
        continental_averages['earn'] = continental_averages['numerator'] / continental_averages['emp']
        continental_averages = continental_averages.reset_index()

        temp = continental_averages.copy()
        temp['country_code'] = temp['CONTINENT_CODE'].map(
            {
                'AFR': 'AFRIC',
                'EUR': 'EUROP',
                'ASIA': 'ASIAT',
                'AMR': 'AMER',
                'OCN': 'OCEAN'
            }
        )
        continental_averages = continental_averages[continental_averages['CONTINENT_CODE'] != 'OCN'].copy()
        continental_averages['country_code'] = temp['CONTINENT_CODE'].map(
            {
                'AFR': 'OAF',
                'EUR': 'OTE',
                'ASIA': 'OAS',
                'AMR': 'OAM'
            }
        )
        continental_averages = pd.concat([continental_averages, temp], axis=0)
        continental_imputation_df = temp.copy()

        # Main DataFrame with annual earnings, to be merged with country-by-country report statistics
        main_ILO_df = pd.concat(
            [
                earnings_interpolated,
                global_averages[['country_code', 'year', 'earn']],
                continental_averages[['country_code', 'year', 'earn']]
            ],
            axis=0
        )

        # Additional DataFrame to impute the earnings that will remain missing based on continental averages
        continental_imputation_df = continental_imputation_df.rename(
            columns={
                'CONTINENT_CODE': 'CONTINENT_CODE_geographies',
                'country_code': 'CONTINENT_CODE_modified'
            }
        )[['CONTINENT_CODE_geographies', 'CONTINENT_CODE_modified', 'year', 'earn']]

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

            sweden_adj_ratios = self.sweden_adj_ratios.copy()

            for year in [2016, 2017, 2018, 2019, 2020]:
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
            oecd['PROBLEMATIC'] = oecd.apply(
                lambda row: row['COU'] == 'BEL' and row['JUR'] in self.belgium_partners_for_adjustment[row['YEA']],
                axis=1
            )

            oecd = oecd[~oecd['PROBLEMATIC']].copy()

            oecd = oecd.drop(columns=['PROBLEMATIC'])

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

        # Applying the extended adjustment for intra-group dividends if relevant
        if self.extended_dividends_adjustment:
            oecd['SELECTION'] = oecd.apply(
                (
                    lambda row: row['COU'] == row['JUR']
                    and not row['COU'] in (['SWE'] + list(self.adj_profits_countries[row['YEA']]))
                ),
                axis=1
            )

            oecd['MULTIPLIER'] = oecd.apply(
                lambda row: 1 if not row['SELECTION'] else self.extended_adjustment_ratios[row['YEA']],
                axis=1
            )

            oecd['Profit (Loss) before Income Tax'] *= oecd['MULTIPLIER']

            oecd = oecd.drop(columns=['SELECTION', 'MULTIPLIER'])

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
            left_on=['JUR', 'YEA'], right_on=['partner', 'YEAR']
        )

        oecd.drop(columns=['partner', 'YEAR'], inplace=True)

        # We deflate all profits and income taxes paid, bringing all values to 2021
        GDP_growth_rates = self.growth_rates.set_index('CountryGroupName')
        deflators = {y: GDP_growth_rates.loc['World', f'uprusd21{y - 2000}'] for y in (2016, 2017, 2018, 2019, 2020)}

        oecd['deflator'] = oecd['YEA'].map(deflators)

        oecd['Profit (Loss) before Income Tax'] *= oecd['deflator']
        oecd['Income Tax Paid (on Cash Basis)'] *= oecd['deflator']

        oecd.drop(columns=['deflator'], inplace=True)

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
            self.path_to_employee_pop = online_data_paths['path_to_employee_pop']
            self.path_to_mean_earnings = online_data_paths['path_to_mean_earnings']

            # Paths to TWZ data on profits booked in tax havens
            url_base_TWZ = url_base + 'TWZ/'
            self.paths_to_excel_files = {
                y: url_base_TWZ + f'{str(y)}/' + 'TWZ.xlsx' for y in (2016, 2017, 2018)
            }
            self.paths_to_excel_files[2019] = url_base_TWZ + f'{str(2019)}/' + 'WZ2022.xlsx'

            # Path to TWZ data on profits booked domestically (with ETRs)
            path_to_twz_domestic = url_base_TWZ + 'TWZ2020AppendixTables.xlsx'

        else:
            # Path to OECD data, TWZ data on corporate income tax revenues and data on statutory tax rates
            self.path_to_oecd = os.path.join(path_to_dir, 'data', 'oecd.csv')
            self.path_to_twz_CIT = os.path.join(path_to_dir, 'data', 'twz_CIT.csv')
            self.path_to_statutory_rates = os.path.join(path_to_dir, 'data', 'KPMG_statutoryrates.xlsx')

            # Path to ILO data
            self.path_to_employee_pop = os.path.join(
                path_to_dir, 'data', 'EMP_TEMP_SEX_STE_NB_A-full-2023-12-22.csv'
            )
            self.path_to_mean_earnings = os.path.join(
                path_to_dir, 'data', 'EAR_4MTH_SEX_ECO_CUR_NB_A.csv'
            )

            # Path to TWZ data on profits booked in tax havens
            self.paths_to_excel_files = {
                y: os.path.join(path_to_dir, 'data', 'TWZ', str(y), 'TWZ.xlsx') for y in (2016, 2017, 2018)
            }
            self.paths_to_excel_files[2019] = os.path.join(path_to_dir, 'data', 'TWZ', str(2019), 'WZ2022.xlsx')

            # Path to TWZ data on profits booked domestically (with ETRs)
            path_to_twz_domestic = os.path.join(path_to_dir, 'data', 'TWZ', 'TWZ2020AppendixTables.xlsx')

        try:
            # We try to read the files from the provided paths
            oecd = pd.read_csv(self.path_to_oecd)

            self.employee_population = pd.read_csv(self.path_to_employee_pop)
            self.earnings = pd.read_csv(
                self.path_to_mean_earnings,
                usecols=[
                    'ref_area', 'indicator', 'source', 'sex',
                    'classif1', 'classif2', 'time', 'obs_value'
                ],
                dtype={
                    'ref_area': 'str',
                    'indicator': 'str',
                    'source': 'str',
                    'sex': 'str',
                    'classif1': 'str',
                    'classif2': 'str',
                    'time': 'int',
                    'obs_value': 'float'
                }
            )

            statutory_rates = pd.read_excel(self.path_to_statutory_rates, engine='openpyxl')

            twz_data = []

            for y in (2016, 2017, 2018, 2019):
                twz = load_and_clean_twz_main_data(
                    path_to_excel_file=self.paths_to_excel_files[y],
                    path_to_geographies=self.path_to_geographies
                )

                twz['YEAR'] = y

                twz_data.append(twz)

            twz = pd.concat(twz_data, axis=0)
            del twz_data

            twz_CIT = load_and_clean_twz_CIT(
                path_to_excel_file=self.paths_to_excel_files[2016],
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

        if self.add_AUT_AUT_row:
            # Fetching the values for the AUT-AUT country pair from the full-sample 2017 data
            temp = oecd[
                np.logical_and(
                    oecd['PAN'] == 'PANELA',
                    oecd['YEA'] == 2017
                )
            ].copy()

            temp = temp[np.logical_and(temp['COU'] == 'AUT', temp['JUR'] == 'AUT')].copy()

            temp['PAN'] = 'PANELAI'

            oecd = pd.concat([oecd, temp], axis=0)

        # We restrict the OECD data to the sub-sample of interest
        oecd = oecd[oecd['PAN'] == 'PANELAI'].copy()

        # Dealing with Belgian data depending on the value of "belgium_treatment"
        if self.belgium_treatment == 'adjust':

            self.belgium_ratios_for_adjustment = {}

            # Computing the profitability ratios used in the correction
            for partner, relevant_years in self.belgium_years_for_adjustment.items():

                temp = oecd[
                    np.logical_and(
                        oecd['COU'] == 'BEL',
                        np.logical_and(
                            oecd['JUR'] == partner,
                            oecd['YEA'].isin(relevant_years)
                        )
                    )
                ].copy()

                temp = temp[temp['CBC'].isin(['TOT_REV', 'PROFIT'])].copy()

                temp['MULTIPLIER'] = temp['YEA'].map(
                    lambda y: self.growth_rates.set_index('CountryGroupName').loc[
                        'World', f'uprusd21{int(y - 2000)}'
                    ]
                )

                temp['Value_2021'] = temp['Value'] * temp['MULTIPLIER']

                temp = temp.groupby('CBC').sum()[['Value_2021']]

                ratio = temp.loc['PROFIT', 'Value_2021'] / temp.loc['TOT_REV', 'Value_2021']

                self.belgium_ratios_for_adjustment[partner] = ratio

            # Operating the correction
            for year, partners in self.belgium_partners_for_adjustment.items():

                mask_revenues = np.logical_and(
                    oecd['COU'] == 'BEL',
                    np.logical_and(
                        oecd['JUR'].isin(partners),
                        np.logical_and(
                            oecd['YEA'] == year,
                            oecd['CBC'] == 'TOT_REV'
                        )
                    )
                )

                revenues_extract = oecd[mask_revenues].copy()

                mask_selection = np.logical_and(
                    oecd['COU'] == 'BEL',
                    np.logical_and(
                        oecd['JUR'].isin(partners),
                        np.logical_and(
                            oecd['YEA'] == year,
                            oecd['CBC'] == 'PROFIT'
                        )
                    )
                )

                extract = oecd[mask_selection].copy()

                oecd = oecd[~mask_selection].copy()

                extract = extract.merge(
                    revenues_extract[['JUR', 'YEA', 'Value']].rename(columns={'Value': 'TOT_REV'}),
                    how='left',
                    on=['JUR', 'YEA']
                )

                if extract['TOT_REV'].isnull().sum() > 0:
                    raise Exception("Issue with the adjustment for Belgium.")

                extract['RATIO'] = extract['JUR'].map(self.belgium_ratios_for_adjustment)

                extract['Value'] = extract['RATIO'] * extract['TOT_REV']

                extract = extract.drop(columns=['RATIO', 'TOT_REV'])

                oecd = pd.concat([oecd, extract], axis=0)

        # Applying the extended adjustment for intra-group dividends if relevant
        if self.extended_dividends_adjustment:

            # - We focus on domestic observations
            temp = oecd[oecd['COU'] == oecd['JUR']].copy()

            # - We compute the sum of adjusted domestic profits in each year
            adj_profits = temp[temp['CBC'] == 'PROFIT_ADJ'].copy()
            adj_profits = adj_profits.groupby('YEA').sum()[['Value']].reset_index()
            adj_profits = adj_profits.rename(columns={'Value': 'PROFIT_ADJ'})

            # - For each year, we keep track of the countries that have provided adjusted domestic profits
            self.adj_profits_countries = {
                y: temp[
                    np.logical_and(
                        temp['CBC'] == 'PROFIT_ADJ',
                        temp['YEA'] == y
                    )
                ]['COU'].unique() for y in (2016, 2017, 2018, 2019, 2020)
            }

            # - We compute the sum of non-adjusted domestic profits in each year for these countries
            unadj_profits = temp.copy()
            unadj_profits['SELECTION_DUMMY'] = unadj_profits.apply(
                lambda row: row['COU'] in self.adj_profits_countries[row['YEA']] and row['CBC'] == 'PROFIT',
                axis=1
            )
            unadj_profits = unadj_profits[unadj_profits['SELECTION_DUMMY']].copy()
            unadj_profits = unadj_profits.groupby('YEA').sum()[['Value']].reset_index()
            unadj_profits = unadj_profits.rename(columns={'Value': 'PROFIT'})

            # - We compute the sum of non-adjusted and adjusted domestic profits for Sweden
            #   - Extracting the domestic profits of Swedish multinationals by year
            sweden_profits = temp[
                np.logical_and(
                    temp['COU'] == 'SWE',
                    temp['CBC'] == 'PROFIT'
                )
            ].groupby('YEA').sum()[['Value']].reset_index()
            sweden_profits = sweden_profits.rename(columns={'Value': 'PROFIT_SWE'})
            #   - Deducing adjusted profits thanks to the figures provided by the Swedish tax administration
            sweden_profits['PROFIT_ADJ_SWE'] = (
                sweden_profits['PROFIT_SWE'] * sweden_profits['YEA'].map(self.sweden_adj_ratios)
            )
            #   - We restrict to years for which the Swedish tax administration provides the relevant figures
            sweden_profits = sweden_profits[sweden_profits['YEA'].map(self.sweden_adj_ratios) != 1].copy()

            # - In a single DataFrame, we combine for each year:
            #       (i) the sum of domestic adjusted profits for countries providing an adjusted variable;
            #       (ii) the sum of domestic non-adjusted profits for countries providing an adjusted variable;
            #       (iii) the domestic adjusted and non-adjusted profits for Sweden.
            adj_profits = adj_profits.merge(sweden_profits, how='outer', on='YEA')
            adj_profits = adj_profits.merge(unadj_profits, how='outer', on='YEA')

            # - Imputing zeros when a value is missing (e.g., no adjustement for Sweden in 2020)
            for col in ['PROFIT', 'PROFIT_ADJ', 'PROFIT_SWE', 'PROFIT_ADJ_SWE']:
                adj_profits[col] = adj_profits[col].fillna(0)

            # - Summing the denominator and the numerator respectively
            adj_profits['PROFIT'] = adj_profits['PROFIT'] + adj_profits['PROFIT_SWE']
            adj_profits['PROFIT_ADJ'] = adj_profits['PROFIT_ADJ'] + adj_profits['PROFIT_ADJ_SWE']

            # - Deducing ratios
            adj_profits['RATIO'] = adj_profits['PROFIT_ADJ'] / adj_profits['PROFIT']

            # - Transforming into a dict
            self.extended_adjustment_ratios = adj_profits.set_index('YEA')['RATIO'].to_dict()

        # # Removing newcomers if relevant
        # if self.use_TWZ_for_CbCR_newcomers:

        #     reporting_countries = oecd[oecd['Year'] == self.year]['COU'].unique()
        #     reporting_countries_previous_year = oecd[oecd['Year'] == self.year - 1]['COU'].unique()
        #     newcomers = reporting_countries[~reporting_countries.isin(reporting_countries_previous_year)].copy()
        #     newcomers = newcomers[~newcomers.isin(self.tax_haven_country_codes)].copy()

        #     oecd = oecd[~np.logical_and(oecd['Year'] == self.year, oecd['COU'].isin(newcomers))].copy()

        # We drop a few irrelevant columns from country-by-country data
        oecd.drop(
            columns=['PAN', 'Grouping', 'Flag Codes', 'Flags'],
            inplace=True
        )

        # We reshape the DataFrame from a long to a wide dataset
        oecd = oecd.pivot(
            index=['COU', 'Ultimate Parent Jurisdiction', 'JUR', 'Partner Jurisdiction', 'YEA'],
            columns='Variable',
            values='Value'
        ).reset_index()

        # We rename some columns to match the code that has been written before modifying how OECD data are loaded
        oecd.rename(
            columns={
                'COU': 'Parent jurisdiction (alpha-3 code)',
                'Ultimate Parent Jurisdiction': 'Parent jurisdiction (whitespaces cleaned)',
                'JUR': 'Partner jurisdiction (alpha-3 code)',
                'Partner Jurisdiction': 'Partner jurisdiction (whitespaces cleaned)',
                'YEA': 'YEAR'
            },
            inplace=True
        )

        # Thanks to a function defined in utils.py, we rename the "Foreign Jurisdictions Total" field for all countries
        # that only report a domestic / foreign breakdown in their CbCR
        oecd['Partner jurisdiction (whitespaces cleaned)'] = oecd.apply(
            lambda row: rename_partner_jurisdictions(
                row,
                COUNTRIES_WITH_MINIMUM_REPORTING=self.COUNTRIES_WITH_MINIMUM_REPORTING[row['YEAR']],
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
        statutory_rates = statutory_rates.melt(id_vars=['CODE', 'Country'], var_name='YEAR', value_name='STAT_RATE')
        # Adding the country code for Bonaire
        statutory_rates['CODE'] = statutory_rates.apply(
            lambda row: 'BES' if row['Country'].startswith('Bonaire') else row['CODE'],
            axis=1
        )
        # Dealing with missing values
        statutory_rates['STAT_RATE'] = statutory_rates['STAT_RATE'].map(
            lambda x: np.nan if x == '-' else x
        ).astype(float)
        # Managing duplicates (equivalently to the Stata code)
        # Removing the EU average
        statutory_rates = statutory_rates[statutory_rates['Country'] != 'EU average'].copy()
        # If two rows display the same country code and year and the same rate, we keep only the first
        statutory_rates = statutory_rates.drop_duplicates(subset=['CODE', 'YEAR', 'STAT_RATE'], keep='first').copy()
        # In practice, only effect is to keep one row for Sint-Maarten which is the only other duplicated country code
        # Additional ad-hoc exclusion for Sint-Maarten
        statutory_rates = statutory_rates[
            ~np.logical_and(
                statutory_rates['CODE'] == 'SXM',
                statutory_rates['YEAR'] < 2016
            )
        ].copy()
        # Adding a simple check for duplicates
        if statutory_rates.duplicated(subset=['CODE', 'YEAR']).sum() > 0:
            raise Exception(
                'At least one duplicated pair of country code and year remains in the table of statutory rates.'
            )
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
        statutory_rates['STAT_RATE'] /= 100
        # Renaming columns
        statutory_rates.rename(
            columns={
                'CODE': 'partner',
                'STAT_RATE': 'statrate'
            },
            inplace=True
        )

        self.statutory_rates = statutory_rates.copy()

        # And we merge it with country-by-country data, on partner jurisdiction alpha-3 codes and year
        oecd = oecd.merge(
            statutory_rates,
            how='left',
            left_on=['Partner jurisdiction (alpha-3 code)', 'YEAR'], right_on=['partner', 'YEAR']
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
        # The adjustment ratio used here depends on the year selected for the Sweden-Sweden row
        oecd['Profit (Loss) before Income Tax'] = oecd.apply(
            (
                lambda row: row['Profit (Loss) before Income Tax'] * self.sweden_adj_ratios[row['YEAR']]
                if row['Parent jurisdiction (alpha-3 code)'] == 'SWE'
                and row['Partner jurisdiction (alpha-3 code)'] == 'SWE'
                else row['Profit (Loss) before Income Tax']
            ),
            axis=1
        )

        # If we prioritarily use adjusted pre-tax profits, we make the required adjustment
        if self.use_adjusted_profits:
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
            oecd['SELECTION'] = oecd.apply(
                (
                    lambda row: row['Parent jurisdiction (alpha-3 code)'] == row['Partner jurisdiction (alpha-3 code)']
                    and not row['Parent jurisdiction (alpha-3 code)'] in (
                        ['SWE'] + list(self.adj_profits_countries[row['YEAR']])
                    )
                ),
                axis=1
            )

            oecd['MULTIPLIER'] = oecd.apply(
                lambda row: 1 if not row['SELECTION'] else self.extended_adjustment_ratios[row['YEAR']],
                axis=1
            )

            oecd['Profit (Loss) before Income Tax'] *= oecd['MULTIPLIER']

            oecd = oecd.drop(columns=['SELECTION', 'MULTIPLIER'])

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

            revenue_threshold = self.exclusion_threshold_revenues
            profit_threshold = self.exclusion_threshold_profits

            mask_revenues = (oecd['Total Revenues'] >= revenue_threshold)
            mask_profits = (oecd['Profit (Loss) before Income Tax'] >= profit_threshold)

            mask_de_minimis_exclusion = np.logical_or(mask_revenues, mask_profits)

            oecd = oecd[mask_de_minimis_exclusion].copy()

        # We need some more work on the data if we want to simulate substance-based carve-outs
        if self.carve_outs or self.behavioral_responses:

            main_ILO_df, continental_imputation_df = self.load_clean_ILO_data()

            self.oecd_temp = oecd.copy()

            # We merge earnings data with country-by-country data on partner jurisdiction codes

            # - Countries for which earnings (possibly obtained via interpolations) are directly available
            oecd = oecd.merge(
                main_ILO_df,
                how='left',
                left_on=['Partner jurisdiction (alpha-3 code)', 'YEAR'],
                right_on=['country_code', 'year']
            ).drop(columns=['country_code', 'year'])

            self.oecd_temp_bis = oecd.copy()

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
                continental_imputation_df[
                    ['CONTINENT_CODE_modified', 'year', 'earn']
                ].rename(columns={'earn': 'earn_avg_continent'}),
                how='left',
                left_on=['CONTINENT_CODE', 'YEAR'], right_on=['CONTINENT_CODE_modified', 'year']
            ).drop(columns=['CONTINENT_CODE_modified', 'year'])

            # - We gather earnings available at the country level and continental imputations
            oecd['earn'] = oecd.apply(
                lambda row: row['earn'] if not np.isnan(row['earn']) else row['earn_avg_continent'],
                axis=1
            )

            oecd = oecd.drop(columns=['CONTINENT_CODE', 'earn_avg_continent'])

            # oecd.drop(columns=['partner2'], inplace=True)

            oecd.rename(
                columns={
                    'earn': 'ANNUAL_VALUE'
                },
                inplace=True
            )

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
            oecd_temp_agg = oecd_temp[oecd_temp['Is partner jurisdiction a non-haven? - CO'] == 1].copy()
            oecd_temp_agg = oecd_temp_agg.groupby('YEAR').sum()[['CARVE_OUT_TEMP', 'Profit (Loss) before Income Tax']]
            oecd_temp_agg['RATIO'] = oecd_temp_agg['CARVE_OUT_TEMP'] / oecd_temp_agg['Profit (Loss) before Income Tax']
            self.avg_carve_out_impact_non_haven = oecd_temp_agg['RATIO'].to_dict()

            # We do the same for pre-tax profits booked in tax havens, domestically and in aggregate partners
            oecd_temp_agg = oecd_temp[oecd_temp['Is partner jurisdiction a tax haven?'] == 1].copy()
            oecd_temp_agg = oecd_temp_agg.groupby('YEAR').sum()[['CARVE_OUT_TEMP', 'Profit (Loss) before Income Tax']]
            oecd_temp_agg['RATIO'] = oecd_temp_agg['CARVE_OUT_TEMP'] / oecd_temp_agg['Profit (Loss) before Income Tax']
            self.avg_carve_out_impact_tax_haven = oecd_temp_agg['RATIO'].to_dict()

            oecd_temp_agg = oecd_temp[oecd_temp['Is domestic?'] == 1].copy()
            oecd_temp_agg = oecd_temp_agg.groupby('YEAR').sum()[['CARVE_OUT_TEMP', 'Profit (Loss) before Income Tax']]
            oecd_temp_agg['RATIO'] = oecd_temp_agg['CARVE_OUT_TEMP'] / oecd_temp_agg['Profit (Loss) before Income Tax']
            self.avg_carve_out_impact_domestic = oecd_temp_agg['RATIO'].to_dict()

            oecd_temp_agg = oecd_temp[oecd_temp['Is partner jurisdiction an aggregate partner? - CO'] == 1].copy()
            oecd_temp_agg = oecd_temp_agg.groupby('YEAR').sum()[['CARVE_OUT_TEMP', 'Profit (Loss) before Income Tax']]
            oecd_temp_agg['RATIO'] = oecd_temp_agg['CARVE_OUT_TEMP'] / oecd_temp_agg['Profit (Loss) before Income Tax']
            self.avg_carve_out_impact_aggregate = oecd_temp_agg['RATIO'].to_dict()

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

        twz = twz.merge(
            oecd[['Parent jurisdiction (alpha-3 code)', 'YEAR']].drop_duplicates(),
            how='left',
            left_on=['Alpha-3 country code', 'YEAR'], right_on=['Parent jurisdiction (alpha-3 code)', 'YEAR']
        )
        twz['Is parent in OECD data?'] = ~twz['Parent jurisdiction (alpha-3 code)'].isnull()
        twz = twz.drop(columns='Parent jurisdiction (alpha-3 code)')

        if self.sweden_exclude:
            twz['Is parent in OECD data?'] = twz['Is parent in OECD data?'] * (twz['Alpha-3 country code'] != 'SWE')

        if self.belgium_treatment == 'exclude':
            problematic_years = [y for y in twz['YEAR'].unique() if len(self.belgium_partners_for_adjustment[y]) > 0]

            twz['Is parent in OECD data?'] = (
                twz['Is parent in OECD data?']
                * ~np.logical_and(twz['Alpha-3 country code'] == 'BEL', twz['YEAR'].isin(problematic_years))
            )

        # If we want to simulate carve-outs, we need to downgrade TWZ tax haven profits by the average reduction due to
        # carve-outs that is observed for tax haven profits in the OECD data
        if self.carve_outs:
            twz['MULTIPLIER'] = 1 - twz['YEAR'].map(self.avg_carve_out_impact_tax_haven)

        for column_name in ['Profits in all tax havens', 'Profits in all tax havens (positive only)']:
            twz[column_name] *= 10**6

            if self.carve_outs:
                twz[column_name] *= twz['MULTIPLIER']

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

        if self.carve_outs:
            twz = twz.drop(columns=['MULTIPLIER'])

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
        # GDP_growth_rates = self.growth_rates.set_index('CountryGroupName')

        # twz_domestic['IS_EU'] = twz_domestic['Alpha-3 country code'].isin(self.eu_27_country_codes) * 1
        # twz_domestic['MULTIPLIER'] = twz_domestic['IS_EU'].map(
        #     {
        #         0: GDP_growth_rates.loc['World', f'uprusd{self.year - 2000}15'],
        #         1: GDP_growth_rates.loc['European Union', f'uprusd{self.year - 2000}15']
        #     }
        # )
        # twz_domestic['Domestic profits'] *= twz_domestic['MULTIPLIER']

        # twz_domestic = twz_domestic.drop(columns=['IS_EU', 'MULTIPLIER'])

        # Replacing the ETR for Germany (taken from OECD's CBCR average ETR [--> TO BE UPDATED?])
        twz_domestic['Domestic ETR'] = twz_domestic.apply(
            lambda row: 0.2275 if row['Alpha-3 country code'] == 'DEU' else row['Domestic ETR'],
            axis=1
        )

        # After this line, figures are expressed in plain USD
        twz_domestic['Domestic profits'] *= 10**9

        # Adding a "YEAR" to keep track of the year associated with these data
        twz_domestic['YEAR'] = 2015

        if self.carve_outs:
            # If we want to simulate carve-outs, we need to downgrade TWZ domestic profits by the average reduction due
            # to carve-outs that is observed for domestic profits in the OECD data
            twz_domestic['Domestic profits'] *= (1 - np.mean(list(self.avg_carve_out_impact_domestic.values())))

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

        else:

            if self.carve_outs:
                return oecd.copy(), twz.copy(), twz_domestic.copy(), twz_CIT.copy()

            else:
                return oecd.copy(), twz.copy(), twz_domestic.copy(), twz_CIT.copy()

    # ------------------------------------------------------------------------------------------------------------------
    # --- BASIC TAX DEFICIT COMPUTATIONS -------------------------------------------------------------------------------

    def get_non_haven_imputation_ratios(self, minimum_ETR, selection):
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
            mask_minimum_reporting_countries = ~oecd.apply(
                (
                    lambda row: row['Parent jurisdiction (alpha-3 code)']
                    in self.COUNTRIES_WITH_MINIMUM_REPORTING[row['YEAR']]
                    + self.COUNTRIES_WITH_CONTINENTAL_REPORTING[row['YEAR']]
                ),
                axis=1
            )

            # We combine the boolean indexing masks
            mask = np.logical_and(mask_selection, mask_non_haven)
            mask = np.logical_and(mask, mask_minimum_reporting_countries)

            # And convert booleans into 0 / 1 integers
            mask = mask * 1

            # We compute the profits registered by retained countries in non-haven countries
            # (excluding domestic profits, cf. the earlier use of the manage_overlap_with_domestic function)
            oecd['FOREIGN_NON_HAVEN_PROFITS'] = (
                mask * oecd['Is partner jurisdiction a non-haven?'] * oecd['Profit (Loss) before Income Tax']
            )
            # foreign_non_haven_profits = (
            #     (
            #         mask * oecd['Is partner jurisdiction a non-haven?']
            #     ) * oecd['Profit (Loss) before Income Tax']
            # ).sum()

            # We compute the profits registered by retained countries in tax havens
            # (excluding domestic profits, cf. the earlier use of the manage_overlap_with_domestic function)
            oecd['FOREIGN_TAX_HAVEN_PROFITS'] = (
                mask * oecd['Is partner jurisdiction a tax haven?'] * oecd['Profit (Loss) before Income Tax']
            )
            # foreign_haven_profits = (
            #     (
            #         mask * oecd['Is partner jurisdiction a tax haven?']
            #     ) * oecd['Profit (Loss) before Income Tax']
            # ).sum()

            # We sum the two quantities by year
            oecd = oecd.groupby('YEAR').sum()[['FOREIGN_NON_HAVEN_PROFITS', 'FOREIGN_TAX_HAVEN_PROFITS']]

            # We apply the formula and compute the imputation ratio
            oecd['RATIOS'] = (
                (
                    # If the minimum ETR is below the rate assumed to be applied on non-haven profits, there is no tax
                    # deficit to collect from these profits, which is why we have this max(..., 0)
                    max(minimum_ETR - self.assumed_non_haven_ETR_TWZ, 0) * oecd['FOREIGN_NON_HAVEN_PROFITS']
                ) /
                ((minimum_ETR - self.assumed_haven_ETR_TWZ) * oecd['FOREIGN_TAX_HAVEN_PROFITS'])
            )
            imputation_ratios_non_haven = oecd['RATIOS'].to_dict()

        # We manage the case where the minimum ETR is of 10% and the formula cannot be applied
        elif minimum_ETR == 0.1:

            # As long as tax haven profits are assumed to be taxed at a rate of 10%, the value that we set here has no
            # effect (it will be multiplied to 0 tax-haven-based tax deficits) but to remain consistent with higher
            # values of the minimum ETR, we impute 0

            imputation_ratios_non_haven = {y: 0 for y in self.oecd['YEAR'].unique()}

        else:
            # We do not yet manage effective tax rates below 10%
            raise Exception('Unexpected minimum ETR entered (strictly below 0.1).')

        return imputation_ratios_non_haven

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
                'YEAR',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit',
                'tax_deficit_x_domestic',
                'tax_deficit_x_tax_haven',
                'tax_deficit_x_non_haven'
            ]
        ].groupby(
            ['Parent jurisdiction (whitespaces cleaned)', 'YEAR']
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

        mask_minimum_reporting_countries = oecd_stratified.apply(
            (
                lambda row: row['Parent jurisdiction (alpha-3 code)']
                in self.COUNTRIES_WITH_CONTINENTAL_REPORTING[row['YEAR']]
                + self.COUNTRIES_WITH_MINIMUM_REPORTING[row['YEAR']]
            ),
            axis=1
        )
        df_restricted = oecd_stratified[~mask_minimum_reporting_countries].copy()

        # The denominator is the total non-haven tax deficit of relevant countries at the reference minimum ETR
        denominator = df_restricted.groupby('YEAR').sum()[['tax_deficit_x_non_haven']].reset_index()
        denominator = denominator.rename(columns={'tax_deficit_x_non_haven': 'denominator'})

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
        mask_minimum_reporting_countries = oecd_stratified.apply(
            (
                lambda row: row['Parent jurisdiction (alpha-3 code)']
                in self.COUNTRIES_WITH_CONTINENTAL_REPORTING[row['YEAR']]
                + self.COUNTRIES_WITH_MINIMUM_REPORTING[row['YEAR']]
            ),
            axis=1
        )
        df_restricted = oecd_stratified[~mask_minimum_reporting_countries].copy()

        # The numerator is the total non-haven tax deficit of relevant countries at the selected minimum ETR
        numerator = df_restricted.groupby('YEAR').sum()[['tax_deficit_x_non_haven']].reset_index()
        numerator = numerator.rename(columns={'tax_deficit_x_non_haven': 'numerator'})

        # Merging the two tables
        merged_df = denominator.merge(numerator, how='outer', on='YEAR')

        # Deducing the relevant ratio for each year
        merged_df['RATIO'] = merged_df['numerator'] / merged_df['denominator']

        return merged_df.set_index('YEAR')['RATIO'].to_dict()

    def compute_all_tax_deficits(
        self,
        minimum_ETR=0.25,
        exclude_non_EU_domestic_TDs=True,
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

        if self.sweden_exclude:
            oecd_stratified = oecd_stratified[
                oecd_stratified['Parent jurisdiction (alpha-3 code)'] != 'SWE'
            ].copy()

        if self.belgium_treatment == 'exclude':
            problematic_years = [y for y in twz['YEAR'].unique() if len(self.belgium_partners_for_adjustment[y]) > 0]

            oecd_stratified = oecd_stratified[
                ~np.logical_and(
                    oecd_stratified['Parent jurisdiction (alpha-3 code)'] == 'BEL',
                    oecd_stratified['YEAR'].isin(problematic_years)
                )
            ].copy()

        twz = self.twz.copy()

        # From TWZ data on profits registered in tax havens and assuming that these are taxed at a given minimum ETR
        # (10% in the report, see the instantiation function for the definition of this attribute), we deduce the tax-
        # haven-based tax deficit of TWZ countries
        twz['tax_deficit_x_tax_haven_TWZ'] = \
            twz['Profits in all tax havens (positive only)'] * (minimum_ETR - self.assumed_haven_ETR_TWZ)

        # --- Countries only in TWZ data

        # We now focus on countries that are absent from the OECD data
        # NB: recall that we do not consider the Swedish CbCR if "exclude" was chosen
        # twz_not_in_oecd = twz[~twz['Is parent in OECD data?'].astype(bool)].copy()

        twz.drop(
            columns=['Profits in all tax havens', 'Profits in all tax havens (positive only)'],
            inplace=True
        )

        # - Extrapolating the foreign non-haven tax deficit

        # We compute the imputation ratio with the method defined above
        imputation_ratios_non_haven = self.get_non_haven_imputation_ratios(
            minimum_ETR=minimum_ETR, selection=self.non_haven_TD_imputation_selection
        )

        # And we deduce the non-haven tax deficit of countries that are only found in TWZ data
        twz['tax_deficit_x_non_haven'] = \
            twz['tax_deficit_x_tax_haven_TWZ'] * twz['YEAR'].map(imputation_ratios_non_haven)

        # - Computing the domestic tax deficit

        # For countries that are only in TWZ data, we still need to compute their domestic tax deficit
        twz_domestic = self.twz_domestic.copy()

        # However, if we assume that non-EU countries do not collect their domestic tax deficit,
        # We restrict the table of TWZ domestic profits and ETRs to EU countries
        if exclude_non_EU_domestic_TDs:
            twz_domestic = twz_domestic[twz_domestic['Alpha-3 country code'].isin(self.eu_27_country_codes)].copy()

        # We only consider countries whose domestic ETR is stricly below the minimum ETR
        # (otherwise, there is no tax deficit to collect from domestic profits)
        twz_domestic = twz_domestic[twz_domestic['Domestic ETR'] < minimum_ETR].copy()

        # We compute the ETR differential
        twz_domestic['ETR_differential'] = twz_domestic['Domestic ETR'].map(lambda x: minimum_ETR - x)

        # And deduce the domestic tax deficit of each country
        twz_domestic['tax_deficit_x_domestic'] = twz_domestic['ETR_differential'] * twz_domestic['Domestic profits']

        # We rename the new column to keep track of the fact that the TWZ data on domestic profits and ETRs are for the
        # year 2015 and have not yet been upgraded to any later income year
        twz_domestic = twz_domestic.rename(columns={'tax_deficit_x_domestic': 'tax_deficit_x_domestic_2015'})

        # - Combining the different forms of tax deficit

        # We merge the two DataFrames to complement twz with domestic tax deficit results
        twz = twz.merge(
            twz_domestic[['Alpha-3 country code', 'tax_deficit_x_domestic_2015']],
            how='outer',
            on='Alpha-3 country code'
        )

        # Adding the relevant years for countries that are in TWZ domestic data but not in TWZ tax haven data
        extract = twz[twz['YEAR'].isnull()].copy()
        twz = twz[~twz['YEAR'].isnull()].copy()
        for year in twz['YEAR'].unique():
            tmp = extract.copy()
            tmp['YEAR'] = year
            tmp['Is parent in OECD data?'] = (tmp['Alpha-3 country code'] + str(year)).isin(
                (oecd_stratified['Parent jurisdiction (alpha-3 code)'] + oecd_stratified['YEAR'].astype(str)).unique()
            )
            twz = pd.concat([twz, tmp], axis=0)

        twz_not_in_oecd = twz[~twz['Is parent in OECD data?'].astype(bool)].copy()

        # BES is in domestic TWZ data but not in tax haven TWZ data (at least for 2018)
        twz_not_in_oecd['Country'] = twz_not_in_oecd.apply(
            lambda row: 'Bonaire' if row['Alpha-3 country code'] == 'BES' else row['Country'],
            axis=1
        )
        twz_not_in_oecd['tax_deficit_x_tax_haven_TWZ'] = twz_not_in_oecd['tax_deficit_x_tax_haven_TWZ'].fillna(0)
        twz_not_in_oecd['tax_deficit_x_domestic_2015'] = twz_not_in_oecd['tax_deficit_x_domestic_2015'].fillna(0)
        twz_not_in_oecd['tax_deficit_x_non_haven'] = twz_not_in_oecd['tax_deficit_x_non_haven'].fillna(0)

        # As we filtered out countries whose domestic ETR is stricly below the minimum ETR, some missing values
        # appear during the merge; we impute 0 for these as they do not have any domestic tax deficit to collect
        twz_not_in_oecd['tax_deficit_x_domestic_2015'] = twz_not_in_oecd['tax_deficit_x_domestic_2015'].fillna(0)

        # We upgrade the domestic tax deficits to the relevant year
        GDP_growth_rates = self.growth_rates.set_index('CountryGroupName')
        twz_not_in_oecd['IS_EU'] = twz_not_in_oecd['Alpha-3 country code'].isin(self.eu_27_country_codes) * 1
        relevant_row = {0: 'World', 1: 'European Union'}

        twz_not_in_oecd['MULTIPLIER'] = twz_not_in_oecd.apply(
            lambda row: GDP_growth_rates.loc[relevant_row[row['IS_EU']], f'uprusd{row["YEAR"] - 2000}15'],
            axis=1
        )
        twz_not_in_oecd['tax_deficit_x_domestic'] = (
            twz_not_in_oecd['tax_deficit_x_domestic_2015'] * twz_not_in_oecd['MULTIPLIER']
        )
        twz_not_in_oecd = twz_not_in_oecd.drop(columns=['tax_deficit_x_domestic_2015', 'IS_EU', 'MULTIPLIER'])

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

        # We eventually concatenate the two DataFrames
        oecd_stratified['SOURCE'] = 'oecd'
        twz_not_in_oecd['SOURCE'] = 'twz'
        merged_df = pd.concat(
            [oecd_stratified, twz_not_in_oecd],
            axis=0
        )

        # --- Managing the case where the minimum ETR is 20% or below for TWZ countries

        # As mentioned above and detailed in Appendix A, the imputation of the non-haven tax deficit of TWZ countries
        # follows a specific process whenever the chosen minimum ETR is of or below 20%
        if minimum_ETR <= 0.2 and self.alternative_imputation:
            # We get the new multiplying factor from the method defined above
            multiplying_factors = self.get_alternative_non_haven_factor(minimum_ETR=minimum_ETR)

            # We compute all tax deficits at the reference rate (25% in the report)
            df = self.compute_all_tax_deficits(
                minimum_ETR=self.reference_rate_for_alternative_imputation
            )

            # What is the set of (country, year) pairs not concerned by this alternative imputation?
            tmp = self.oecd[['Parent jurisdiction (alpha-3 code)', 'YEAR']].copy()
            tmp['PAIR'] = tmp['Parent jurisdiction (alpha-3 code)'] + tmp['YEAR'].astype(str)
            country_year_pairs = pd.Series(tmp['PAIR'].unique())

            if self.sweden_exclude:
                country_year_pairs = country_year_pairs[
                    ~country_year_pairs.map(lambda pair: pair.startswith('SWE'))
                ].copy()

            if self.belgium_treatment == 'exclude':
                problematic_years = [
                    y for y in twz['YEAR'].unique() if len(self.belgium_partners_for_adjustment[y]) > 0
                ]

                problematic_country_years = ['BEL' + y for y in problematic_years]

                country_year_pairs = country_year_pairs[~country_year_pairs.isin(problematic_country_years)].copy()

            df['PAIR'] = df['Parent jurisdiction (alpha-3 code)'] + df['YEAR'].astype(str)

            df = df[~df['PAIR'].isin(country_year_pairs)].copy()

            # For these countries, we multiply the non-haven tax deficit at the reference rate by the multiplying factor
            df['tax_deficit_x_non_haven_imputation'] = (
                df['tax_deficit_x_non_haven'] * df['YEAR'].map(multiplying_factors)
            )

            # We save the results in a dictionary that will allow to map the DataFrame that we want to output in the end
            mapping = {}

            for _, row in df.iterrows():
                mapping[row['PAIR']] = row['tax_deficit_x_non_haven_imputation']

            # We create a new column in the to-be-output DataFrame which takes as value:
            # - the non-haven tax deficit estimated just above for TWZ countries
            # - 0 for OECD-reporting countries, which do not require this imputation
            merged_df['PAIR'] = merged_df['Parent jurisdiction (alpha-3 code)'] + merged_df['YEAR'].astype(str)
            merged_df['tax_deficit_x_non_haven_imputation'] = merged_df['PAIR'].map(lambda pair: mapping.get(pair, 0))

            # We deduce the non-haven tax deficit of all countries
            merged_df['tax_deficit_x_non_haven'] += merged_df['tax_deficit_x_non_haven_imputation']

            # And add this imputation also to the column that presents the total tax deficit of each country
            merged_df['tax_deficit'] += merged_df['tax_deficit_x_non_haven_imputation']

            merged_df.drop(
                columns=['tax_deficit_x_non_haven_imputation', 'PAIR'],
                inplace=True
            )

        return merged_df.reset_index(drop=True).copy()

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

        oecd = self.oecd.copy()

        # --- Step common to OECD and TWZ data

        # Depending on the chosen treatment of Belgian and Swedish CbCRs, we have to adapt the OECD data and therefore
        # the list of (parent country, year) pairs to consider in TWZ data
        tmp = oecd.copy()
        tmp['PAIR'] = tmp['Parent jurisdiction (alpha-3 code)'] + tmp['YEAR'].astype(str)
        unique_country_year_pairs = pd.Series(tmp['PAIR'].unique())
        del tmp

        if self.sweden_exclude:
            unique_country_year_pairs = unique_country_year_pairs[
                ~unique_country_year_pairs.map(lambda pair: pair.startswith('SWE'))
            ].copy()

        if self.belgium_treatment == 'exclude':
            problematic_years = [
                y for y in twz['YEAR'].unique() if len(self.belgium_partners_for_adjustment[y]) > 0
            ]

            problematic_country_years = ['BEL' + y for y in problematic_years]

            unique_country_year_pairs = unique_country_year_pairs[
                ~unique_country_year_pairs.isin(problematic_country_years)
            ].copy()

        self.unique_country_year_pairs_temp = unique_country_year_pairs.copy()

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
                'YEAR',
                'PROFITS_BEFORE_TAX_POST_CO', 'ETR'
            ]
        ].copy()

        oecd['SOURCE'] = 'oecd'

        # - TWZ tax haven data

        twz_data = []

        for y in (2016, 2017, 2018, 2019):
            twz = load_and_clean_bilateral_twz_data(
                path_to_excel_file=self.paths_to_excel_files[y],
                path_to_geographies=self.path_to_geographies
            )

            twz['YEAR'] = y

            twz_data.append(twz)

        twz = pd.concat(twz_data, axis=0)
        del twz_data

        # We exclude OECD-reporting countries, except for those that are excluded (possibly Sweden and / or Belgium)
        twz['PAIR'] = twz['PARENT_COUNTRY_CODE'] + twz['YEAR'].astype(str)
        twz = twz[~twz['PAIR'].isin(unique_country_year_pairs)].copy()
        twz = twz.drop(columns=['PAIR'])

        # We exclude the few observations for which parent and partner countries are the same (only for MLT and CYP)
        # This would otherwise induce double-counting with the domestic TWZ data
        twz = twz[twz['PARENT_COUNTRY_CODE'] != twz['PARTNER_COUNTRY_CODE']].copy()

        # Negative profits are brought to 0 (no tax deficit to collect)
        twz['PROFITS'] = twz['PROFITS'].map(lambda x: max(x, 0))

        # We move from millions of USD to USD
        twz['PROFITS'] = twz['PROFITS'] * 10**6

        # If carve-outs are applied, we need to apply the average reduction in tax haven profits implied by carve-outs
        if self.carve_outs:
            twz['PROFITS'] *= (1 - twz['YEAR'].map(self.avg_carve_out_impact_tax_haven))

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
                'YEAR',
                'PROFITS_BEFORE_TAX_POST_CO'
            ]
        ].copy()

        # Adding the variables that are still missing compared with the OECD sample
        twz['ETR'] = self.assumed_haven_ETR_TWZ
        twz['SOURCE'] = 'twz_th'

        # - TWZ domestic data

        twz_domestic_data = []

        for y in (2016, 2017, 2018, 2019):

            twz_domestic = self.twz_domestic.copy()

            twz_domestic['YEAR'] = y

            twz_domestic['IS_EU'] = twz_domestic['Alpha-3 country code'].isin(self.eu_27_country_codes) * 1

            GDP_growth_rates = self.growth_rates.set_index('CountryGroupName')
            relevant_row = {0: 'World', 1: 'European Union'}

            twz_domestic['MULTIPLIER'] = twz_domestic.apply(
                lambda row: GDP_growth_rates.loc[relevant_row[row['IS_EU']], f'uprusd{row["YEAR"] - 2000}15'],
                axis=1
            )

            twz_domestic['Domestic profits'] *= twz_domestic['MULTIPLIER']

            twz_domestic = twz_domestic.drop(columns=['IS_EU', 'MULTIPLIER'])

            twz_domestic_data.append(twz_domestic)

        twz_domestic = pd.concat(twz_domestic_data, axis=0)
        del twz_domestic_data

        # We filter out OECD-reporting countries to avoid double-counting their domestic tax deficit
        twz_domestic['PAIR'] = twz_domestic['Alpha-3 country code'] + twz_domestic['YEAR'].astype(str)
        twz_domestic = twz_domestic[~twz_domestic['PAIR'].isin(unique_country_year_pairs)].copy()
        twz_domestic = twz_domestic.drop(columns=['PAIR'])

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

        # Computation of tax deficits
        full_sample['ETR_DIFF'] = full_sample['ETR'].map(lambda x: max(minimum_ETR - x, 0))
        full_sample['TAX_DEFICIT'] = full_sample['ETR_DIFF'] * full_sample['PROFITS_BEFORE_TAX_POST_CO']

        # If we exclude these countries from the OECD's data, we must adjust Belgium's and Sweden's tax deficits
        if self.sweden_exclude:
            mask_sweden = np.logical_and(full_sample['PARENT_COUNTRY_CODE'] == 'SWE', full_sample['SOURCE'] == 'oecd')

            multiplier = 1 - mask_sweden

            full_sample['TAX_DEFICIT'] *= multiplier

        if self.belgium_treatment == "exclude":
            problematic_years = [
                y for y in twz['YEAR'].unique() if len(self.belgium_partners_for_adjustment[y]) > 0
            ]

            mask_belgium = np.logical_and(
                full_sample['PARENT_COUNTRY_CODE'] == 'SWE',
                np.logical_and(
                    full_sample['SOURCE'] == 'oecd',
                    full_sample['YEAR'].isin(problematic_years)
                )
            )

            multiplier = 1 - mask_belgium

            full_sample['TAX_DEFICIT'] *= multiplier

        # --- Attributing the tax deficits of the "Rest of non-EU tax havens" in TWZ data

        rest_extract = full_sample[full_sample['PARTNER_COUNTRY_CODE'] == 'REST'].copy()
        to_be_distributed = rest_extract.groupby('YEAR').sum()['TAX_DEFICIT'].to_dict()

        full_sample = full_sample[full_sample['PARTNER_COUNTRY_CODE'] != 'REST'].copy()

        if verbose:

            print('Tax deficit already attributed bilaterally:')
            print(full_sample.groupby('YEAR').sum()['TAX_DEFICIT'] / 10**6)
            print('m USD')
            print('-----')
            print('Tax deficit in rest of non-EU tax havens:')
            print(pd.Series(to_be_distributed) / 10**6)
            print('m USD')
            print('___________________________________________________________________')

        full_sample['TEMP_DUMMY'] = np.logical_and(
            full_sample['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
            ~full_sample['PARTNER_COUNTRY_CODE'].isin(self.eu_27_country_codes + ['CHE'])
        ) * 1

        full_sample['TEMP_DUMMY_x_TAX_DEFICIT'] = full_sample['TEMP_DUMMY'] * full_sample['TAX_DEFICIT']
        full_sample['TEMP_DUMMY_x_TAX_DEFICIT_sum_YEAR'] = full_sample.groupby('YEAR').transform('sum')[
            'TEMP_DUMMY_x_TAX_DEFICIT'
        ]
        full_sample['TEMP_SHARE'] = (
            full_sample['TEMP_DUMMY_x_TAX_DEFICIT'] / full_sample['TEMP_DUMMY_x_TAX_DEFICIT_sum_YEAR']
        )

        full_sample['TO_BE_DISTRIBUTED'] = full_sample['YEAR'].map(to_be_distributed)

        full_sample['IMPUTED_TAX_DEFICIT'] = full_sample['TEMP_SHARE'] * full_sample['TO_BE_DISTRIBUTED']

        imputation = full_sample.groupby(['PARTNER_COUNTRY_CODE', 'YEAR']).agg(
            {
                'PARTNER_COUNTRY_NAME': 'first',
                'IMPUTED_TAX_DEFICIT': 'sum'
            }
        ).reset_index().rename(columns={'IMPUTED_TAX_DEFICIT': 'TAX_DEFICIT'})

        imputation['PARENT_COUNTRY_CODE'] = 'IMPT_REST'
        imputation['PARENT_COUNTRY_NAME'] = 'Imputation REST'

        full_sample = full_sample.drop(
            columns=[
                'TEMP_DUMMY', 'TEMP_DUMMY_x_TAX_DEFICIT', 'TEMP_DUMMY_x_TAX_DEFICIT_sum_YEAR',
                'TEMP_SHARE',
                'TO_BE_DISTRIBUTED',
                'IMPUTED_TAX_DEFICIT'
            ]
        )

        full_sample = pd.concat([full_sample, imputation])

        if verbose:

            print('Bilaterally attributed tax deficit after REST:')
            print(full_sample.groupby('YEAR').sum()['TAX_DEFICIT'] / 10**6)
            print('m USD')
            print('Worth a quick check here?')
            print('___________________________________________________________________')

        # --- Upgrading non-haven tax deficits

        # - Theresa's method
        if upgrade_non_havens:

            hq_scenario_totals = headquarter_collects_scenario.groupby('YEAR').sum()[['tax_deficit']].rename(
                columns={'tax_deficit': 'HQ_TAX_DEFICIT'}
            )
            full_sample_totals = full_sample.groupby('YEAR').sum()[['TAX_DEFICIT']].rename(
                columns={'TAX_DEFICIT': 'FS_TAX_DEFICIT'}
            )

            to_be_distributed = hq_scenario_totals.join(full_sample_totals, how='outer')

            to_be_distributed['DIFF'] = to_be_distributed['HQ_TAX_DEFICIT'] - to_be_distributed['FS_TAX_DEFICIT']

            to_be_distributed = to_be_distributed['DIFF'].to_dict()

            if verbose:

                print('Total tax deficit in the IIR scenario:')
                print(headquarter_collects_scenario.groupby('YEAR').sum()['tax_deficit'] / 10**6)
                print('m USD')
                print('-----')
                print('Tax deficit currently bilaterally allocated:')
                print(full_sample.groupby('YEAR').sum()['TAX_DEFICIT'] / 10**6)
                print('m USD')
                print('-----')
                print('Tax deficit to be distributed among non-havens:')
                print(pd.Series(to_be_distributed) / 10**6)
                print('m USD')
                print('___________________________________________________________________')

            full_sample['TEMP_DUMMY'] = np.logical_and(
                ~full_sample['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
                np.logical_and(
                    full_sample['PARENT_COUNTRY_CODE'] != full_sample['PARTNER_COUNTRY_CODE'],
                    full_sample['PARENT_COUNTRY_CODE'] != 'IMPT_REST'
                )
            ) * 1

            full_sample['TEMP_DUMMY_x_TAX_DEFICIT'] = full_sample['TEMP_DUMMY'] * full_sample['TAX_DEFICIT']
            full_sample['TEMP_DUMMY_x_TAX_DEFICIT_sum_YEAR'] = full_sample[
                ['YEAR', 'TEMP_DUMMY_x_TAX_DEFICIT']
            ].groupby('YEAR').transform('sum')['TEMP_DUMMY_x_TAX_DEFICIT']

            full_sample['TEMP_SHARE'] = (
                full_sample['TEMP_DUMMY_x_TAX_DEFICIT'] / full_sample['TEMP_DUMMY_x_TAX_DEFICIT_sum_YEAR']
            )

            full_sample['TO_BE_DISTRIBUTED'] = full_sample['YEAR'].map(to_be_distributed)

            full_sample['IMPUTED_TAX_DEFICIT'] = full_sample['TEMP_SHARE'] * full_sample['TO_BE_DISTRIBUTED']

            imputation = full_sample.groupby(['PARTNER_COUNTRY_CODE', 'YEAR']).agg(
                {
                    'PARTNER_COUNTRY_NAME': 'first',
                    'IMPUTED_TAX_DEFICIT': 'sum'
                }
            ).reset_index().rename(columns={'IMPUTED_TAX_DEFICIT': 'TAX_DEFICIT'})

            imputation['PARENT_COUNTRY_CODE'] = 'IMPT_TWZ_NH'
            imputation['PARENT_COUNTRY_NAME'] = 'Imputation TWZ NH'

            full_sample = full_sample.drop(
                columns=[
                    'TEMP_DUMMY', 'TEMP_DUMMY_x_TAX_DEFICIT', 'TEMP_DUMMY_x_TAX_DEFICIT_sum_YEAR',
                    'TEMP_SHARE',
                    'TO_BE_DISTRIBUTED',
                    'IMPUTED_TAX_DEFICIT'
                ]
            )

            full_sample = pd.concat([full_sample, imputation])

            if verbose:

                print('Tax deficit bilaterally allocated after imputation for non-havens:')
                print(full_sample.groupby('YEAR').sum()['TAX_DEFICIT'] / 10**6)
                print('m USD')

        # --- Finalising the tax deficit computations

        # Grouping by partner country in the full QDMTT scenario
        tax_deficits = full_sample.groupby(
            ['PARTNER_COUNTRY_CODE', 'YEAR']
        ).agg(
            {
                'PARTNER_COUNTRY_NAME': 'first',
                'TAX_DEFICIT': 'sum'
            }
        ).reset_index()

        self.full_sample_QDMTT = full_sample.copy()

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

        # oecd = oecd[oecd['YEA'] == self.year].copy()

        oecd.drop(
            columns=[
                'PAN', 'Grouping', 'Flag Codes', 'Flags', 'Year',
                'Ultimate Parent Jurisdiction'
            ],
            inplace=True
        )

        # Moving from a long to a wide dataset
        oecd = oecd.pivot(
            index=['COU', 'JUR', 'Partner Jurisdiction', 'YEA'],
            columns='CBC',
            values='Value'
        ).reset_index()

        # Focusing on columns of interest
        oecd = oecd[['COU', 'JUR', 'Partner Jurisdiction', 'YEA', 'UPR', 'EMPLOYEES', 'ASSETS']].copy()

        # Selecting parents with a sufficient breakdown of partners
        temp = oecd.groupby(['COU', 'YEA']).agg({'JUR': 'nunique'}).reset_index()
        temp['PAIR'] = temp['COU'] + temp['YEA'].astype(str)
        relevant_parent_year_pairs = temp[temp['JUR'] > minimum_breakdown]['PAIR'].unique()
        oecd['PAIR'] = oecd['COU'] + oecd['YEA'].astype(str)
        oecd = oecd[oecd['PAIR'].isin(relevant_parent_year_pairs)].copy()
        oecd = oecd.drop(columns=['PAIR'])
        other_parent_year_pairs = temp[temp['JUR'] <= minimum_breakdown]['PAIR'].unique()

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

                oecd[f'{col}_TOTAL'] = oecd.groupby(['COU', 'YEA']).transform('sum')[col]
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

        return other_parent_year_pairs, oecd.copy()

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

        # oecd = oecd[oecd['YEA'] == self.year].copy()

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
            columns='CBC',
            values='Value'
        ).reset_index()

        # Focusing on columns of interest
        oecd = oecd[['COU', 'JUR', 'YEA', 'UPR', 'EMPLOYEES', 'ASSETS']].copy()

        # Selecting parents with a sufficient breakdown of partners
        temp = oecd.groupby(['COU', 'YEA']).agg({'JUR': 'nunique'}).reset_index()
        temp['PAIR'] = temp['COU'] + temp['YEA'].astype(str)
        relevant_parent_year_pairs = temp[temp['JUR'] > minimum_breakdown]['PAIR'].unique()
        oecd['PAIR'] = oecd['COU'] + oecd['YEA'].astype(str)
        oecd = oecd[oecd['PAIR'].isin(relevant_parent_year_pairs)].copy()
        oecd = oecd.drop(columns=['PAIR'])
        other_parent_year_pairs = temp[temp['JUR'] <= minimum_breakdown]['PAIR'].unique()

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

            oecd[f'{col}_TOTAL'] = oecd.groupby(['COU', 'YEA']).transform('sum')[col]
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

        return other_parent_year_pairs, oecd.copy()

    def compute_selected_intermediary_scenario_gain(
        self,
        countries_implementing,
        among_countries_implementing=False,
        minimum_ETR=0.15,
        minimum_breakdown=60,
        weight_UPR=1, weight_employees=0, weight_assets=0,
        exclude_non_implementing_domestic_TDs=True
    ):

        # We start by computing the total tax deficits of all in-sample countries (those of the multilateral scenario)
        tax_deficits = self.compute_all_tax_deficits(
            minimum_ETR=minimum_ETR,
            exclude_non_EU_domestic_TDs=exclude_non_implementing_domestic_TDs
        )

        tax_deficits = tax_deficits[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'YEAR',
                'tax_deficit',
                'tax_deficit_x_domestic',
            ]
        ].copy()

        # And we store in a separate DataFrame the tax deficits of selected countries implementing the deal
        selected_tax_deficits = tax_deficits[
            tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(countries_implementing)
        ].copy()

        # We focus on non-implementing countries, defined when the TaxDeficitCalculator object is instantiated
        temp = tax_deficits.copy()
        temp['PAIR'] = temp['Parent jurisdiction (alpha-3 code)'] + temp['YEAR'].astype(str)
        temp = temp[~temp['Parent jurisdiction (alpha-3 code)'].isin(countries_implementing)].copy()
        not_implementing_tax_deficits = tax_deficits[
            ~tax_deficits['Parent jurisdiction (alpha-3 code)'].isin(countries_implementing)
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

        # Among non-implementing countries, we further focus on those for which we have allocation keys
        available_pairs = (available_allocation_keys['COU'] + available_allocation_keys['YEA'].astype(str)).unique()
        not_implementing_tax_deficits['PAIR'] = (
            not_implementing_tax_deficits['Parent jurisdiction (alpha-3 code)']
            + not_implementing_tax_deficits['YEAR'].astype(str)
        )
        allocable_non_implementing_TDs = not_implementing_tax_deficits[
            not_implementing_tax_deficits['PAIR'].isin(available_pairs)
        ].copy()
        other_non_implementing_TDs = not_implementing_tax_deficits[
            ~not_implementing_tax_deficits['PAIR'].isin(available_pairs)
        ].copy()

        # Allocating the directly allocable tax deficits
        allocable_non_implementing_TDs = allocable_non_implementing_TDs.merge(
            available_allocation_keys,
            how='left',
            left_on=['Parent jurisdiction (alpha-3 code)', 'YEAR'], right_on=['COU', 'YEA']
        )

        if among_countries_implementing:

            allocable_non_implementing_TDs = allocable_non_implementing_TDs[
                allocable_non_implementing_TDs['JUR'].isin(countries_implementing)
            ].copy()

            if allocable_non_implementing_TDs['SHARE_KEY'].sum() > 0:

                allocable_non_implementing_TDs['SHARE_KEY_TOTAL'] = allocable_non_implementing_TDs.groupby(
                    ['Parent jurisdiction (alpha-3 code)', 'YEAR']
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
            ['JUR', 'Partner Jurisdiction', 'YEAR']
        ).agg(
            {'directly_allocated': 'sum'}
        ).reset_index().rename(columns={'JUR': 'Parent jurisdiction (alpha-3 code)'})

        # Allocating the tax deficits that are not directly allocable
        avg_allocation_keys = {'JUR': [], 'YEAR': [], 'SHARE_KEY': []}

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

            agg_country_extract = country_extract.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()
            agg_sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs.groupby('YEA').sum()[
                ['UPR', 'EMPLOYEES', 'ASSETS']
            ].reset_index()

            agg_dataset = agg_country_extract.merge(agg_sales_mapping_foreign_MNEs, how='outer', on='YEA')

            agg_dataset['SHARE_UPR'] = agg_dataset['UPR_x'] / agg_dataset['UPR_y']
            agg_dataset['SHARE_EMPLOYEES'] = agg_dataset['EMPLOYEES_x'] / agg_dataset['EMPLOYEES_y']
            agg_dataset['SHARE_ASSETS'] = agg_dataset['ASSETS_x'] / agg_dataset['ASSETS_y']

            agg_dataset['SHARE_KEY'] = (
                share_UPR * agg_dataset['SHARE_UPR']
                + share_employees * agg_dataset['SHARE_EMPLOYEES']
                + share_assets * agg_dataset['SHARE_ASSETS']
            )

            agg_dataset = agg_dataset.sort_values(by='YEA')

            avg_allocation_keys['YEAR'] += list(agg_dataset['YEA'].values)
            avg_allocation_keys['SHARE_KEY'] += list(agg_dataset['SHARE_KEY'].values)
            avg_allocation_keys['JUR'] += [country] * len(agg_dataset)

        avg_allocation_keys = pd.DataFrame(avg_allocation_keys)
        # avg_allocation_keys['SHARE_UPR'] = avg_allocation_keys['SHARE_UPR']

        # We re-scale the average allocation keys so that they sum to 1:
        #   - over the set of implementing countries if among_countries_implementing is True;
        #   - else over the set of all partner jurisdictions`.

        print('Average allocation keys for France:')
        print(avg_allocation_keys[avg_allocation_keys['JUR'] == 'FRA'])

        print("Before the re-scaling of the average allocation keys, they sum to:")
        print(avg_allocation_keys.groupby('YEAR').sum()['SHARE_KEY'])

        domestic_extract = sales_mapping[sales_mapping['COU'] == sales_mapping['JUR']].copy()

        agg_domestic_extract = domestic_extract.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()
        agg_sales_mapping = sales_mapping.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()

        agg_dataset = agg_domestic_extract.merge(agg_sales_mapping, how='outer', on='YEA')

        agg_dataset['SHARE_UPR'] = agg_dataset['UPR_x'] / agg_dataset['UPR_y']
        agg_dataset['SHARE_EMPLOYEES'] = agg_dataset['EMPLOYEES_x'] / agg_dataset['EMPLOYEES_y']
        agg_dataset['SHARE_ASSETS'] = agg_dataset['ASSETS_x'] / agg_dataset['ASSETS_y']

        agg_dataset['SHARE_KEY'] = (
            share_UPR * agg_dataset['SHARE_UPR']
            + share_employees * agg_dataset['SHARE_EMPLOYEES']
            + share_assets * agg_dataset['SHARE_ASSETS']
        )

        avg_domestic_shares = agg_dataset.set_index('YEA')['SHARE_KEY'].to_dict()

        print('Average domestic shares:')
        print(avg_domestic_shares)

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
            on=['YEAR', 'TEMP_KEY']
        ).drop(columns=['TEMP_KEY'])

        other_non_implementing_TDs = other_non_implementing_TDs[
            other_non_implementing_TDs['Parent jurisdiction (alpha-3 code)'] != other_non_implementing_TDs['JUR']
        ].copy()

        if among_countries_implementing:
            other_non_implementing_TDs = other_non_implementing_TDs[
                other_non_implementing_TDs['JUR'].isin(countries_implementing)
            ].copy()

        other_non_implementing_TDs['SHARE_KEY_TOTAL'] = other_non_implementing_TDs.groupby(
            ['Parent jurisdiction (alpha-3 code)', 'YEAR']
        ).transform('sum')['SHARE_KEY']
        if not among_countries_implementing:
            other_non_implementing_TDs['RESCALING_FACTOR'] = (
                1 - other_non_implementing_TDs['YEAR'].map(avg_domestic_shares)
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

        details_imputed = other_non_implementing_TDs.copy()

        other_non_implementing_TDs = other_non_implementing_TDs.groupby(['JUR', 'YEAR']).agg(
            {'imputed': 'sum'}
        ).reset_index().rename(columns={'JUR': 'Parent jurisdiction (alpha-3 code)'})

        selected_tax_deficits = selected_tax_deficits.merge(
            allocable_non_implementing_TDs, how='outer', on=['Parent jurisdiction (alpha-3 code)', 'YEAR']
        ).merge(
            other_non_implementing_TDs, how='outer', on=['Parent jurisdiction (alpha-3 code)', 'YEAR']
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
    ):

        # We start by computing the total tax deficits of all in-sample countries (those of the multilateral scenario)
        tax_deficits = self.compute_all_tax_deficits(
            minimum_ETR=minimum_ETR,
            exclude_non_EU_domestic_TDs=exclude_domestic_TDs,
        )

        tax_deficits = tax_deficits[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'YEAR',
                'tax_deficit', 'tax_deficit_x_domestic'
            ]
        ].copy()

        # # if not full_own_tax_deficit:
        if exclude_domestic_TDs:
            tax_deficits['tax_deficit'] -= tax_deficits['tax_deficit_x_domestic']

        tax_deficits = tax_deficits.drop(columns=['tax_deficit_x_domestic'])

        # Let us get the relevant allocation keys
        parents_insufficient_brkdown, available_allocation_keys = self.get_tax_deficit_allocation_keys_unilateral(
            minimum_breakdown=minimum_breakdown,
            full_own_tax_deficit=full_own_tax_deficit,
            weight_UPR=weight_UPR, weight_employees=weight_employees, weight_assets=weight_assets
        )

        share_UPR = weight_UPR / (weight_UPR + weight_employees + weight_assets)
        share_employees = weight_employees / (weight_UPR + weight_employees + weight_assets)
        share_assets = weight_assets / (weight_UPR + weight_employees + weight_assets)

        # We focus on the tax deficits for which we have allocation keys
        available_pairs = (available_allocation_keys['COU'] + available_allocation_keys['YEA'].astype(str)).unique()
        tax_deficits['PAIR'] = tax_deficits['Parent jurisdiction (alpha-3 code)'] + tax_deficits['YEAR'].astype(str)
        allocable_TDs = tax_deficits[tax_deficits['PAIR'].isin(available_pairs)].drop(columns=['PAIR'])
        other_TDs = tax_deficits[~tax_deficits['PAIR'].isin(available_pairs)].drop(columns=['PAIR'])

        # Allocating the directly allocable tax deficits
        allocable_TDs = allocable_TDs.merge(
            available_allocation_keys,
            how='left',
            left_on=['Parent jurisdiction (alpha-3 code)', 'YEAR'], right_on=['COU', 'YEA']
        ).drop(columns=['YEA'])

        allocable_TDs['directly_allocated'] = (allocable_TDs['tax_deficit'] * allocable_TDs['SHARE_KEY']).astype(float)
        allocable_TDs['IS_DOMESTIC'] = allocable_TDs['COU'] == allocable_TDs['JUR']
        allocable_TDs['directly_allocated_dom'] = allocable_TDs['directly_allocated'] * allocable_TDs['IS_DOMESTIC']
        allocable_TDs['directly_allocated_for'] = allocable_TDs['directly_allocated'] * (~allocable_TDs['IS_DOMESTIC'])

        details_directly_allocated = allocable_TDs.copy()

        allocable_TDs = allocable_TDs.groupby(['JUR', 'YEAR']).agg(
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

        agg_domestic_extract = domestic_extract.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()
        agg_sales_mapping = sales_mapping.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()

        agg_dataset = agg_domestic_extract.merge(agg_sales_mapping, how='outer', on='YEA')

        agg_dataset['SHARE_UPR'] = agg_dataset['UPR_x'] / agg_dataset['UPR_y']
        agg_dataset['SHARE_EMPLOYEES'] = agg_dataset['EMPLOYEES_x'] / agg_dataset['EMPLOYEES_y']
        agg_dataset['SHARE_ASSETS'] = agg_dataset['ASSETS_x'] / agg_dataset['ASSETS_y']

        agg_dataset['SHARE_KEY'] = (
            share_UPR * agg_dataset['SHARE_UPR']
            + share_employees * agg_dataset['SHARE_EMPLOYEES']
            + share_assets * agg_dataset['SHARE_ASSETS']
        )

        avg_domestic_shares = agg_dataset.set_index('YEA')['SHARE_KEY'].to_dict()

        print(avg_domestic_shares)

        if full_own_tax_deficit:
            other_TDs_domestic['SHARE_KEY'] = 1

        else:
            other_TDs_domestic['SHARE_KEY'] = other_TDs_domestic['YEAR'].map(avg_domestic_shares)

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
            'YEAR': [],
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

            agg_country_extract = country_extract.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()
            agg_sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs.groupby('YEA').sum()[
                ['UPR', 'EMPLOYEES', 'ASSETS']
            ].reset_index()

            agg_dataset = agg_country_extract.merge(agg_sales_mapping_foreign_MNEs, how='outer', on='YEA')

            agg_dataset['SHARE_UPR'] = agg_dataset['UPR_x'] / agg_dataset['UPR_y']
            agg_dataset['SHARE_EMPLOYEES'] = agg_dataset['EMPLOYEES_x'] / agg_dataset['EMPLOYEES_y']
            agg_dataset['SHARE_ASSETS'] = agg_dataset['ASSETS_x'] / agg_dataset['ASSETS_y']

            agg_dataset['SHARE_KEY'] = (
                share_UPR * agg_dataset['SHARE_UPR']
                + share_employees * agg_dataset['SHARE_EMPLOYEES']
                + share_assets * agg_dataset['SHARE_ASSETS']
            )

            agg_dataset = agg_dataset.sort_values(by='YEA')

            avg_allocation_keys_foreign['YEAR'] += list(agg_dataset['YEA'].values)
            avg_allocation_keys_foreign['SHARE_KEY'] += list(agg_dataset['SHARE_KEY'].values)
            avg_allocation_keys_foreign['JUR'] += [country] * len(agg_dataset)

        avg_allocation_keys_foreign = pd.DataFrame(avg_allocation_keys_foreign)

        print('Average allocation keys for France:')
        print(avg_allocation_keys_foreign[avg_allocation_keys_foreign['JUR'] == 'FRA'])

        print("Before the re-scaling of the average allocation keys, they sum to:")
        print(avg_allocation_keys_foreign.groupby('YEAR')['SHARE_KEY'].sum())

        avg_allocation_keys_foreign['TEMP_KEY'] = 1
        other_TDs_foreign['TEMP_KEY'] = 1

        other_TDs_foreign = other_TDs_foreign.merge(
            avg_allocation_keys_foreign,
            how='left',
            on=['YEAR', 'TEMP_KEY']
        )

        other_TDs_foreign = other_TDs_foreign[
            other_TDs_foreign['Parent jurisdiction (alpha-3 code)'] != other_TDs_foreign['JUR']
        ].copy()

        other_TDs_foreign['SHARE_KEY_TOTAL'] = other_TDs_foreign.groupby(
            ['Parent jurisdiction (alpha-3 code)', 'YEAR']
        ).transform('sum')['SHARE_KEY']
        other_TDs_foreign['RESCALING_FACTOR'] = (
            1 - other_TDs_foreign['YEAR'].map(avg_domestic_shares)
        ) / other_TDs_foreign['SHARE_KEY_TOTAL']
        other_TDs_foreign['SHARE_KEY'] *= other_TDs_foreign['RESCALING_FACTOR']

        other_TDs_foreign['imputed_foreign'] = (
            other_TDs_foreign['tax_deficit'] * other_TDs_foreign['SHARE_KEY']
        ).astype(float)

        details_imputed_foreign = other_TDs_foreign.copy()

        other_TDs_foreign = other_TDs_foreign.groupby(['JUR', 'YEAR']).agg(
            {'imputed_foreign': 'sum'}
        ).reset_index().rename(columns={'JUR': 'Parent jurisdiction (alpha-3 code)'})

        tax_deficits = tax_deficits.merge(
            allocable_TDs, how='outer', on=['Parent jurisdiction (alpha-3 code)', 'YEAR']
        ).merge(
            other_TDs_foreign, how='outer', on=['Parent jurisdiction (alpha-3 code)', 'YEAR']
        ).merge(
            other_TDs_domestic, how='outer', on=['Parent jurisdiction (alpha-3 code)', 'YEAR']
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
    # --- FULL BILATERAL DISAGGREGATION APPROACH -----------------------------------------------------------------------

    def build_bilateral_data(
        self,
        minimum_rate,
        QDMTT_incl_domestic,
        QDMTT_excl_domestic,
        ETR_increment=0,
        verbose=0,
    ):

        # We need to have previously loaded and cleaned the OECD and TWZ data
        if self.oecd is None or self.twz is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        # We fetch the list of OECD-reporting parent countries whose tax haven tax deficit is taken from TWZ data and
        # not from OECD data in the benchmark computations
        oecd = self.oecd.copy()

        # --- Step common to OECD and TWZ data

        # Depending on the chosen treatment of Belgian and Swedish CbCRs, we have to adapt the OECD data and therefore
        # the list of (parent country, year) pairs to consider in TWZ data
        tmp = oecd.copy()
        tmp['PAIR'] = tmp['Parent jurisdiction (alpha-3 code)'] + tmp['YEAR'].astype(str)
        unique_country_year_pairs = pd.Series(tmp['PAIR'].unique())
        del tmp

        if self.sweden_exclude:
            unique_country_year_pairs = unique_country_year_pairs[
                ~unique_country_year_pairs.map(lambda pair: pair.startswith('SWE'))
            ].copy()

        if self.belgium_treatment == 'exclude':
            problematic_years = [
                y for y in twz['YEAR'].unique() if len(self.belgium_partners_for_adjustment[y]) > 0
            ]

            problematic_country_years = ['BEL' + y for y in problematic_years]

            unique_country_year_pairs = unique_country_year_pairs[
                ~unique_country_year_pairs.isin(problematic_country_years)
            ].copy()

        self.unique_country_year_pairs_temp = unique_country_year_pairs.copy()

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
                'YEAR',
                'PROFITS_BEFORE_TAX_POST_CO', 'ETR'
            ]
        ].copy()

        oecd['SOURCE'] = 'oecd'

        # - TWZ tax haven data

        twz_data = []

        for y in (2016, 2017, 2018, 2019):
            twz = load_and_clean_bilateral_twz_data(
                path_to_excel_file=self.paths_to_excel_files[y],
                path_to_geographies=self.path_to_geographies
            )

            twz['YEAR'] = y

            twz_data.append(twz)

        twz = pd.concat(twz_data, axis=0)
        del twz_data

        # We exclude OECD-reporting countries, except for those that are excluded (possibly Sweden and / or Belgium)
        twz['PAIR'] = twz['PARENT_COUNTRY_CODE'] + twz['YEAR'].astype(str)
        twz = twz[~twz['PAIR'].isin(unique_country_year_pairs)].copy()
        twz = twz.drop(columns=['PAIR'])

        # We exclude the few observations for which parent and partner countries are the same (only for MLT and CYP)
        # This would otherwise induce double-counting with the domestic TWZ data
        twz = twz[twz['PARENT_COUNTRY_CODE'] != twz['PARTNER_COUNTRY_CODE']].copy()

        # Negative profits are brought to 0 (no tax deficit to collect)
        twz['PROFITS'] = twz['PROFITS'].map(lambda x: max(x, 0))

        # We move from millions of USD to USD
        twz['PROFITS'] = twz['PROFITS'] * 10**6

        # If carve-outs are applied, we need to apply the average reduction in tax haven profits implied by carve-outs
        if self.carve_outs:
            twz['PROFITS'] *= (1 - twz['YEAR'].map(self.avg_carve_out_impact_tax_haven))

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
                'YEAR',
                'PROFITS_BEFORE_TAX_POST_CO'
            ]
        ].copy()

        # Adding the variables that are still missing compared with the OECD sample
        twz['ETR'] = self.assumed_haven_ETR_TWZ
        twz['SOURCE'] = 'twz_th'

        # - TWZ domestic data

        twz_domestic_data = []

        for y in (2016, 2017, 2018, 2019):

            twz_domestic = self.twz_domestic.copy()

            twz_domestic['YEAR'] = y

            twz_domestic['IS_EU'] = twz_domestic['Alpha-3 country code'].isin(self.eu_27_country_codes) * 1

            GDP_growth_rates = self.growth_rates.set_index('CountryGroupName')
            relevant_row = {0: 'World', 1: 'European Union'}

            twz_domestic['MULTIPLIER'] = twz_domestic.apply(
                lambda row: GDP_growth_rates.loc[relevant_row[row['IS_EU']], f'uprusd{row["YEAR"] - 2000}15'],
                axis=1
            )

            twz_domestic['Domestic profits'] *= twz_domestic['MULTIPLIER']

            twz_domestic = twz_domestic.drop(columns=['IS_EU', 'MULTIPLIER'])

            twz_domestic_data.append(twz_domestic)

        twz_domestic = pd.concat(twz_domestic_data, axis=0)
        del twz_domestic_data

        # We filter out OECD-reporting countries to avoid double-counting their domestic tax deficit
        twz_domestic['PAIR'] = twz_domestic['Alpha-3 country code'] + twz_domestic['YEAR'].astype(str)
        twz_domestic = twz_domestic[~twz_domestic['PAIR'].isin(unique_country_year_pairs)].copy()
        twz_domestic = twz_domestic.drop(columns=['PAIR'])

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

        full_sample_df['IS_DOMESTIC'] = full_sample_df['PARENT_COUNTRY_CODE'] == full_sample_df['PARTNER_COUNTRY_CODE']

        full_sample_df['ETR_inc'] = full_sample_df['ETR'] + ETR_increment
        full_sample_df['ETR_diff'] = full_sample_df['ETR_inc'].map(lambda x: max(minimum_rate - x, 0))
        full_sample_df['TAX_DEFICIT'] = full_sample_df['ETR_diff'] * full_sample_df['PROFITS_BEFORE_TAX_POST_CO']

        # If we exclude these countries from the OECD's data, we must adjust Belgium's and Sweden's tax deficits
        if self.sweden_exclude:
            mask_sweden = np.logical_and(
                full_sample_df['PARENT_COUNTRY_CODE'] == 'SWE',
                full_sample_df['SOURCE'] == 'oecd'
            )

            multiplier = 1 - mask_sweden

            full_sample_df['TAX_DEFICIT'] *= multiplier

        if self.belgium_treatment == "exclude":
            problematic_years = [
                y for y in twz['YEAR'].unique() if len(self.belgium_partners_for_adjustment[y]) > 0
            ]

            mask_belgium = np.logical_and(
                full_sample_df['PARENT_COUNTRY_CODE'] == 'SWE',
                np.logical_and(
                    full_sample_df['SOURCE'] == 'oecd',
                    full_sample_df['YEAR'].isin(problematic_years)
                )
            )

            multiplier = 1 - mask_belgium

            full_sample_df['TAX_DEFICIT'] *= multiplier

        bilat_extract_df = full_sample_df[full_sample_df['PARTNER_COUNTRY_CODE'] != 'REST'].copy()

        rest_extract = full_sample_df[full_sample_df['PARTNER_COUNTRY_CODE'] == 'REST'].copy()

        if verbose:

            tmp = bilat_extract_df[
                ~np.logical_and(
                    bilat_extract_df['PARTNER_COUNTRY_CODE'] == bilat_extract_df['PARENT_COUNTRY_CODE'],
                    bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(QDMTT_excl_domestic)
                )
            ].copy()

            print('Tax deficit already attributed bilaterally:')
            print(tmp.groupby('YEAR').sum()['TAX_DEFICIT'] / 10**6)
            print('m USD')
            print('-----')
            print('Tax deficit in rest of non-EU tax havens:')
            print(rest_extract.groupby('YEAR').sum()['TAX_DEFICIT'] / 10**6)
            print('m USD')
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

        yearly_totals = relevant_extract_df[
            relevant_extract_df['PARENT_COUNTRY_CODE'] != relevant_extract_df['PARTNER_COUNTRY_CODE']
        ].groupby('YEAR').sum()['TAX_DEFICIT'].to_dict()

        shares = relevant_extract_df[
            relevant_extract_df['collected_through_foreign_QDMTT']
        ].groupby(
            ['PARTNER_COUNTRY_CODE', 'PARTNER_COUNTRY_NAME', 'YEAR']
        ).sum()[['TAX_DEFICIT_foreign_QDMTT']].reset_index()

        shares = shares.rename(columns={'TAX_DEFICIT_foreign_QDMTT': 'KEY'})

        shares['collected_through_foreign_QDMTT'] = True

        for year in rest_extract['YEAR'].unique():

            idx = len(shares)

            shares.loc[idx, 'PARTNER_COUNTRY_CODE'] = 'REST'
            shares.loc[idx, 'PARTNER_COUNTRY_NAME'] = 'Rest'
            shares.loc[idx, 'YEAR'] = year
            shares.loc[idx, 'KEY'] = yearly_totals[year] - shares[shares['YEAR'] == year]['KEY'].sum()
            shares.loc[idx, 'collected_through_foreign_QDMTT'] = False

        if verbose:

            self.REST_shares_new = shares.copy()

        rest_extract = rest_extract[
            [
                'PARENT_COUNTRY_CODE', 'PARENT_COUNTRY_NAME', 'YEAR',
                'SOURCE', 'IS_DOMESTIC', 'ETR', 'ETR_diff',
                'PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT'
            ]
        ].copy()

        rest_extract['MERGE_TEMP'] = 1

        shares['MERGE_TEMP'] = 1

        rest_extract = rest_extract.merge(shares, how='outer', on=['YEAR', 'MERGE_TEMP']).drop(columns='MERGE_TEMP')

        if verbose:
            print(rest_extract.shape)

        rest_extract['KEY_TOTAL'] = rest_extract.groupby(['PARENT_COUNTRY_CODE', 'YEAR']).transform('sum')['KEY']

        rest_extract['KEY_SHARE'] = rest_extract['KEY'] / rest_extract['KEY_TOTAL']

        rest_extract['PROFITS_BEFORE_TAX_POST_CO'] *= rest_extract['KEY_SHARE']
        rest_extract['TAX_DEFICIT'] *= rest_extract['KEY_SHARE']

        rest_extract = rest_extract.drop(columns=['KEY_TOTAL', 'KEY', 'KEY_SHARE'])

        rest_extract['EDGE_CASE'] = rest_extract['PARENT_COUNTRY_CODE'] == rest_extract['PARTNER_COUNTRY_CODE']
        bilat_extract_df['EDGE_CASE'] = False

        full_sample_df = pd.concat([bilat_extract_df, rest_extract], axis=0)

        if verbose:
            tmp = full_sample_df[
                ~np.logical_and(
                    full_sample_df['PARTNER_COUNTRY_CODE'] == full_sample_df['PARENT_COUNTRY_CODE'],
                    full_sample_df['PARTNER_COUNTRY_CODE'].isin(QDMTT_excl_domestic)
                )
            ].copy()
            tmp['TAX_DEFICIT'] = tmp['TAX_DEFICIT'].astype(float)

            print('Bilaterally attributed tax deficit after REST:')
            print(tmp.groupby('YEAR').sum()['TAX_DEFICIT'] / 10**6)
            print('m USD')
            print('Worth a quick check here?')
            print('___________________________________________________________________')

        # --- TWZ countries' non-haven tax deficit

        # TWZ_extract = full_sample_df[
        #     ~full_sample_df['PARENT_COUNTRY_CODE'].isin(
        #         self.oecd['Parent jurisdiction (alpha-3 code)'].unique()
        #     )
        # ].copy()

        TWZ_extract = full_sample_df[full_sample_df['SOURCE'] == 'twz_th'].copy()

        TWZ_extract = TWZ_extract[
            TWZ_extract['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes + ['REST'])
        ].copy()

        TWZ_extract = TWZ_extract[
            np.logical_or(
                TWZ_extract['PARENT_COUNTRY_CODE'] != TWZ_extract['PARTNER_COUNTRY_CODE'],
                TWZ_extract['collected_through_foreign_QDMTT']
            )
        ].copy()

        TWZ_extract['TAX_DEFICIT'] = TWZ_extract['TAX_DEFICIT'].astype(float)

        HQ_scenario_TWZ = TWZ_extract.groupby(
            ['PARENT_COUNTRY_CODE', 'PARENT_COUNTRY_NAME', 'YEAR']
        ).sum()['TAX_DEFICIT'].reset_index()
        HQ_scenario_TWZ = HQ_scenario_TWZ.rename(
            columns={
                'PARENT_COUNTRY_CODE': 'Parent jurisdiction (alpha-3 code)',
                'PARENT_COUNTRY_NAME': 'Parent jurisdiction (whitespaces cleaned)',
                'TAX_DEFICIT': 'tax_deficit_x_non_haven'
            }
        )

        factors = self.get_non_haven_imputation_ratios(
            minimum_ETR=minimum_rate, selection=self.non_haven_TD_imputation_selection
        )
        HQ_scenario_TWZ['FACTOR'] = HQ_scenario_TWZ['YEAR'].map(factors)
        HQ_scenario_TWZ['tax_deficit_x_non_haven'] *= HQ_scenario_TWZ['FACTOR']

        if minimum_rate <= 0.2 and self.alternative_imputation:

            TWZ_extract = self.build_bilateral_data(
                self.reference_rate_for_alternative_imputation,
                QDMTT_incl_domestic,
                QDMTT_excl_domestic
            )

            TWZ_extract = TWZ_extract[TWZ_extract['SOURCE'] == 'imputation'].copy()

            TWZ_extract['TAX_DEFICIT'] = TWZ_extract['TAX_DEFICIT'].astype(float)

            HQ_scenario_TWZ = TWZ_extract.groupby(
                ['PARENT_COUNTRY_CODE', 'PARENT_COUNTRY_NAME', 'YEAR']
            ).sum()['TAX_DEFICIT'].reset_index()

            HQ_scenario_TWZ = HQ_scenario_TWZ.rename(
                columns={
                    'PARENT_COUNTRY_CODE': 'Parent jurisdiction (alpha-3 code)',
                    'PARENT_COUNTRY_NAME': 'Parent jurisdiction (whitespaces cleaned)',
                    'TAX_DEFICIT': 'tax_deficit_x_non_haven'
                }
            )

            factors = self.get_alternative_non_haven_factor(minimum_ETR=minimum_rate, ETR_increment=ETR_increment)
            print("Alternative non-haven factors:")
            print(factors)

            HQ_scenario_TWZ['FACTOR'] = HQ_scenario_TWZ['YEAR'].map(factors)
            HQ_scenario_TWZ['tax_deficit_x_non_haven'] *= HQ_scenario_TWZ['FACTOR']

        HQ_scenario_TWZ.drop(columns=['FACTOR'])

        HQ_scenario_TWZ = HQ_scenario_TWZ.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'PARENT_COUNTRY_NAME',
                'Parent jurisdiction (alpha-3 code)': 'PARENT_COUNTRY_CODE',
                'tax_deficit_x_non_haven': 'TAX_DEFICIT'
            }
        )

        relevant_extract_df = bilat_extract_df[
            np.logical_and(
                ~bilat_extract_df['PARTNER_COUNTRY_CODE'].isin(self.tax_haven_country_codes),
                bilat_extract_df['PARTNER_COUNTRY_CODE'] != bilat_extract_df['PARENT_COUNTRY_CODE']
            )
        ].copy()

        shares = relevant_extract_df.groupby(
            ['PARTNER_COUNTRY_CODE', 'PARTNER_COUNTRY_NAME', 'YEAR']
        ).sum()[
            'TAX_DEFICIT'
        ].reset_index()

        shares = shares.rename(columns={'TAX_DEFICIT': 'KEY'})

        shares = shares[shares['KEY'] > 0].copy()

        shares['MERGE_TEMP'] = 1

        HQ_scenario_TWZ['MERGE_TEMP'] = 1

        TWZ_countries_non_havens = HQ_scenario_TWZ.merge(
            shares, how='outer', on=['YEAR', 'MERGE_TEMP']).drop(
            columns=['MERGE_TEMP']
        )

        TWZ_countries_non_havens['KEY_TOTAL'] = TWZ_countries_non_havens.groupby(
            ['PARENT_COUNTRY_CODE', 'YEAR']
        ).transform('sum')['KEY']

        TWZ_countries_non_havens['SHARE_KEY'] = TWZ_countries_non_havens['KEY'] / TWZ_countries_non_havens['KEY_TOTAL']

        TWZ_countries_non_havens['TAX_DEFICIT'] *= TWZ_countries_non_havens['SHARE_KEY']

        TWZ_countries_non_havens = TWZ_countries_non_havens[
            [
                'PARENT_COUNTRY_CODE', 'PARENT_COUNTRY_NAME',
                'PARTNER_COUNTRY_CODE', 'PARTNER_COUNTRY_NAME',
                'YEAR',
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
        utpr_safe_harbor_incl_foreign_profits=False,
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
                stat_rates_2022 = pd.read_csv(online_data_paths['path_to_2022_rates'])
                stat_rates_2023 = pd.read_csv(online_data_paths['path_to_2023_rates'])

            else:
                stat_rates_2022 = pd.read_csv(os.path.join(path_to_dir, "data", "all_rates_2022.csv"))
                stat_rates_2023 = pd.read_csv(os.path.join(path_to_dir, 'data', 'TABLE_II1_18102023223104057.csv'))

            # Adding the tax rate for the Marshall Islands based on that of the Micronesia Federation
            new_idx = len(stat_rates_2022)

            stat_rates_2022.loc[new_idx, 'ISO3'] = 'MHL'

            stat_rates_2022.loc[new_idx, 'Corporate Tax Rate'] = stat_rates_2022[
                stat_rates_2022['ISO3'] == 'FSM'
            ]['Corporate Tax Rate'].unique()

            stat_rates_2022['Corporate Tax Rate'] /= 100

            # Preparing OECD's statutory corporate income tax rates for 2023
            stat_rates_2023 = stat_rates_2023[stat_rates_2023['CORP_TAX'] == 'COMB_CIT_RATE'].copy()
            stat_rates_2023 = stat_rates_2023[stat_rates_2023['YEA'] == 2023].copy()
            stat_rates_2023 = stat_rates_2023[['COU', 'Value']].copy()

            stat_rates_2023['Value'] /= 100

            # Merging the 2022 and 2023 information
            stat_rates_2022_2023 = stat_rates_2022.merge(
                stat_rates_2023,
                how='outer',
                left_on='ISO3', right_on='COU',
            )

            stat_rates_2022_2023['ISO3'] = stat_rates_2022_2023['ISO3'].fillna(stat_rates_2022_2023['COU'])
            stat_rates_2022_2023['Corporate Tax Rate'] = stat_rates_2022_2023['Value'].fillna(
                stat_rates_2022_2023['Corporate Tax Rate']
            )

            stat_rates_2022_2023 = stat_rates_2022_2023.drop(columns=['COU', 'Value'])

            self.stat_rates_2022 = stat_rates_2022.copy()
            self.stat_rates_2023 = stat_rates_2023.copy()
            self.stat_rates_2022_2023 = stat_rates_2022_2023.copy()

            # Adding statutory tax rates to the main DataFrame
            full_sample_df = full_sample_df.merge(
                stat_rates_2022_2023,
                how='left',
                left_on='PARENT_COUNTRY_CODE', right_on='ISO3'
            ).drop(columns='ISO3').rename(columns={'Corporate Tax Rate': 'STAT_RATE'})

            full_sample_df['collected_through_domestic_UTPR'] = np.logical_and(
                full_sample_df['PARENT_COUNTRY_CODE'] == full_sample_df['PARTNER_COUNTRY_CODE'],
                np.logical_and(
                    ~full_sample_df['EDGE_CASE'].astype(bool),
                    np.logical_and(
                        full_sample_df[
                            [
                                'collected_through_foreign_QDMTT',
                                'collected_through_domestic_QDMTT',
                                'collected_through_domestic_IIR'
                            ]
                        ].sum(axis=1) == 0,
                        full_sample_df['STAT_RATE'] < min_stat_rate_for_UTPR_safe_harbor
                    )
                )
            )

            if utpr_safe_harbor_incl_foreign_profits:

                full_sample_df['collected_through_foreign_UTPR'] = np.logical_and(
                    np.logical_or(
                        full_sample_df['PARENT_COUNTRY_CODE'] != full_sample_df['PARTNER_COUNTRY_CODE'],
                        full_sample_df['EDGE_CASE'].astype(bool)
                    ),
                    np.logical_and(
                        full_sample_df[
                            [
                                'collected_through_foreign_QDMTT', 'collected_through_foreign_IIR',
                                'collected_through_domestic_QDMTT', 'collected_through_domestic_IIR'
                            ]
                        ].sum(axis=1) == 0,
                        full_sample_df['STAT_RATE'] < min_stat_rate_for_UTPR_safe_harbor
                    )
                )

            else:

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

        else:

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

        available_pairs_domestic = (
            available_allocation_keys_domestic['COU'] + available_allocation_keys_domestic['YEA'].astype(str)
        ).unique()
        available_pairs_foreign = (
            available_allocation_keys_foreign['COU'] + available_allocation_keys_foreign['YEA'].astype(str)
        ).unique()

        domestic_UTPR_extract['PAIR'] = (
            domestic_UTPR_extract['PARENT_COUNTRY_CODE'] + domestic_UTPR_extract['YEAR'].astype(str)
        )
        foreign_UTPR_extract['PAIR'] = (
            foreign_UTPR_extract['PARENT_COUNTRY_CODE'] + foreign_UTPR_extract['YEAR'].astype(str)
        )

        allocable_domestic_UTPR_TDs = domestic_UTPR_extract[
            domestic_UTPR_extract['PAIR'].isin(available_pairs_domestic)
        ].copy()
        allocable_foreign_UTPR_TDs = foreign_UTPR_extract[
            foreign_UTPR_extract['PAIR'].isin(available_pairs_foreign)
        ].copy()
        other_domestic_UTPR_TDs = domestic_UTPR_extract[
            ~domestic_UTPR_extract['PAIR'].isin(available_pairs_domestic)
        ].copy()
        other_foreign_UTPR_TDs = foreign_UTPR_extract[
            ~foreign_UTPR_extract['PAIR'].isin(available_pairs_foreign)
        ].copy()

        allocable_domestic_UTPR_TDs = allocable_domestic_UTPR_TDs.merge(
            available_allocation_keys_domestic,
            how='left',
            left_on=['PARENT_COUNTRY_CODE', 'YEAR'], right_on=['COU', 'YEA']
        ).drop(columns=['YEA'])

        if among_countries_implementing:

            allocable_domestic_UTPR_TDs = allocable_domestic_UTPR_TDs[
                allocable_domestic_UTPR_TDs['JUR'].isin(UTPR_incl_domestic)
            ].copy()

            if allocable_domestic_UTPR_TDs['SHARE_KEY'].sum() > 0:
                allocable_domestic_UTPR_TDs['SHARE_KEY_TOTAL'] = allocable_domestic_UTPR_TDs.groupby(
                    ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'YEAR', 'SOURCE']
                ).transform('sum')['SHARE_KEY']
                allocable_domestic_UTPR_TDs['RESCALING_FACTOR'] = 1 / allocable_domestic_UTPR_TDs['SHARE_KEY_TOTAL']
                allocable_domestic_UTPR_TDs['SHARE_KEY'] *= allocable_domestic_UTPR_TDs['RESCALING_FACTOR']

        allocable_foreign_UTPR_TDs = allocable_foreign_UTPR_TDs.merge(
            available_allocation_keys_foreign,
            how='left',
            left_on=['PARENT_COUNTRY_CODE', 'YEAR'], right_on=['COU', 'YEA']
        )

        if among_countries_implementing:

            allocable_foreign_UTPR_TDs = allocable_foreign_UTPR_TDs[
                allocable_foreign_UTPR_TDs['JUR'].isin(UTPR_incl_domestic + UTPR_excl_domestic)
            ].copy()

            if allocable_foreign_UTPR_TDs['SHARE_KEY'].sum() > 0:
                allocable_foreign_UTPR_TDs['SHARE_KEY_TOTAL'] = allocable_foreign_UTPR_TDs.groupby(
                    ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'YEAR', 'SOURCE']
                ).transform('sum')['SHARE_KEY']
                allocable_foreign_UTPR_TDs['RESCALING_FACTOR'] = 1 / allocable_foreign_UTPR_TDs['SHARE_KEY_TOTAL']
                allocable_foreign_UTPR_TDs['SHARE_KEY'] *= allocable_foreign_UTPR_TDs['RESCALING_FACTOR']

        col_list = [
            'PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE',
            'PARENT_COUNTRY_NAME', 'PARTNER_COUNTRY_NAME',
            'YEAR',
            'PROFITS_BEFORE_TAX_POST_CO', 'ETR', 'SOURCE',
            'IS_DOMESTIC', 'ETR_diff', 'TAX_DEFICIT',
            'collected_through_domestic_QDMTT', 'collected_through_foreign_QDMTT',
            'collected_through_domestic_IIR', 'collected_through_foreign_IIR',
            'collected_through_foreign_UTPR', 'collected_through_domestic_UTPR',
            'JUR', 'Partner Jurisdiction', 'SHARE_KEY', 'EDGE_CASE'
        ]

        if stat_rate_condition_for_UTPR:
            col_list.append('STAT_RATE')

        allocable_domestic_UTPR_TDs = allocable_domestic_UTPR_TDs[col_list].copy()

        allocable_domestic_UTPR_TDs = allocable_domestic_UTPR_TDs.rename(
            columns={
                'JUR': 'COLLECTING_COUNTRY_CODE',
                'Partner Jurisdiction': 'COLLECTING_COUNTRY_NAME',
                'SHARE_KEY': 'SHARE_COLLECTED'
            }
        )

        col_list = [
            'PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE',
            'PARENT_COUNTRY_NAME', 'PARTNER_COUNTRY_NAME',
            'YEAR',
            'PROFITS_BEFORE_TAX_POST_CO', 'ETR', 'SOURCE',
            'IS_DOMESTIC', 'ETR_diff', 'TAX_DEFICIT',
            'collected_through_domestic_QDMTT', 'collected_through_foreign_QDMTT',
            'collected_through_domestic_IIR', 'collected_through_foreign_IIR',
            'collected_through_foreign_UTPR', 'collected_through_domestic_UTPR',
            'JUR', 'Partner Jurisdiction', 'SHARE_KEY', 'EDGE_CASE'
        ]

        if stat_rate_condition_for_UTPR:
            col_list.append('STAT_RATE')

        allocable_foreign_UTPR_TDs = allocable_foreign_UTPR_TDs[col_list].copy()

        allocable_foreign_UTPR_TDs = allocable_foreign_UTPR_TDs.rename(
            columns={
                'JUR': 'COLLECTING_COUNTRY_CODE',
                'Partner Jurisdiction': 'COLLECTING_COUNTRY_NAME',
                'SHARE_KEY': 'SHARE_COLLECTED'
            }
        )

        allocable_domestic_UTPR_TDs['COLLECTING_COUNTRY_CODE'].unique()

        # Allocating the tax deficits that are not directly allocable
        avg_allocation_keys_domestic = {'JUR': [], 'YEAR': [], 'SHARE_KEY': []}
        avg_allocation_keys_foreign = {'JUR': [], 'YEAR': [], 'SHARE_KEY': []}

        sales_mapping = available_allocation_keys_domestic.drop(
            columns=[
                'UPR_TOTAL', 'ASSETS_TOTAL', 'EMPLOYEES_TOTAL',
                'SHARE_UPR', 'SHARE_ASSETS', 'SHARE_EMPLOYEES', 'SHARE_KEY'
            ]
        )

        if len(UTPR_incl_domestic) + len(UTPR_excl_domestic) > 0:

            domestic_extract = sales_mapping[sales_mapping['COU'] == sales_mapping['JUR']].copy()

            agg_domestic_extract = domestic_extract.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()
            agg_sales_mapping = sales_mapping.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()

            agg_dataset = agg_domestic_extract.merge(agg_sales_mapping, how='outer', on='YEA')

            agg_dataset['SHARE_UPR'] = agg_dataset['UPR_x'] / agg_dataset['UPR_y']
            agg_dataset['SHARE_EMPLOYEES'] = agg_dataset['EMPLOYEES_x'] / agg_dataset['EMPLOYEES_y']
            agg_dataset['SHARE_ASSETS'] = agg_dataset['ASSETS_x'] / agg_dataset['ASSETS_y']

            agg_dataset['SHARE_KEY'] = (
                share_UPR * agg_dataset['SHARE_UPR']
                + share_employees * agg_dataset['SHARE_EMPLOYEES']
                + share_assets * agg_dataset['SHARE_ASSETS']
            )

            avg_domestic_shares_domestic = agg_dataset.set_index('YEA')['SHARE_KEY'].to_dict()

            print("Average domestic shares:")
            print(avg_domestic_shares_domestic)

        else:

            avg_domestic_shares_domestic = {y: 0 for y in sales_mapping['YEA'].unique()}

        # Domestic UTPR

        # For the computation of average allocation keys, we consider all the partner jurisdictions included in the
        # OECD's country-by-country report statistics (not only in the sub-sample excluding loss-making entities but
        # in the whole dataset since allocation keys are sourced in the overall dataset)
        iteration = pd.read_csv(self.path_to_oecd, usecols=['JUR'])['JUR'].unique()

        # We extend this set to countries implementing the UTPR but never reported as partners in the data
        # They will get a share of allocation key of 0 and thus 0 revenue gains (except if we have them as parents)
        iteration = np.union1d(np.union1d(iteration, UTPR_incl_domestic), UTPR_excl_domestic)

        for country in iteration:

            sales_mapping_foreign_MNEs = sales_mapping[sales_mapping['COU'] != country].copy()

            sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs[
                sales_mapping_foreign_MNEs['COU'] != sales_mapping_foreign_MNEs['JUR']
            ].copy()

            country_extract = sales_mapping_foreign_MNEs[sales_mapping_foreign_MNEs['JUR'] == country].copy()

            agg_country_extract = country_extract.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()
            agg_sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs.groupby('YEA').sum()[
                ['UPR', 'EMPLOYEES', 'ASSETS']
            ].reset_index()

            agg_dataset = agg_country_extract.merge(agg_sales_mapping_foreign_MNEs, how='outer', on='YEA')

            agg_dataset['SHARE_UPR'] = agg_dataset['UPR_x'] / agg_dataset['UPR_y']
            agg_dataset['SHARE_EMPLOYEES'] = agg_dataset['EMPLOYEES_x'] / agg_dataset['EMPLOYEES_y']
            agg_dataset['SHARE_ASSETS'] = agg_dataset['ASSETS_x'] / agg_dataset['ASSETS_y']

            agg_dataset['SHARE_KEY'] = (
                share_UPR * agg_dataset['SHARE_UPR']
                + share_employees * agg_dataset['SHARE_EMPLOYEES']
                + share_assets * agg_dataset['SHARE_ASSETS']
            )

            agg_dataset = agg_dataset.sort_values(by='YEA')

            avg_allocation_keys_domestic['YEAR'] += list(agg_dataset['YEA'].values)
            avg_allocation_keys_domestic['SHARE_KEY'] += list(agg_dataset['SHARE_KEY'].values)
            avg_allocation_keys_domestic['JUR'] += [country] * len(agg_dataset)

        avg_allocation_keys_domestic = pd.DataFrame(avg_allocation_keys_domestic)

        print("Average domestic allocation key for France:")
        print(avg_allocation_keys_domestic[avg_allocation_keys_domestic['JUR'] == 'FRA'])
        print("Before the re-scaling of the domestic average allocation keys, they sum to:")
        print(avg_allocation_keys_domestic.groupby('YEAR').sum()['SHARE_KEY'])

        # Foreign UTPR
        sales_mapping = available_allocation_keys_foreign.drop(
            columns=[
                'UPR_TOTAL', 'ASSETS_TOTAL', 'EMPLOYEES_TOTAL',
                'SHARE_UPR', 'SHARE_ASSETS', 'SHARE_EMPLOYEES', 'SHARE_KEY'
            ]
        )

        if len(UTPR_incl_domestic) + len(UTPR_excl_domestic) > 0:

            domestic_extract = sales_mapping[sales_mapping['COU'] == sales_mapping['JUR']].copy()

            agg_domestic_extract = domestic_extract.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()
            agg_sales_mapping = sales_mapping.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()

            agg_dataset = agg_domestic_extract.merge(agg_sales_mapping, how='outer', on='YEA')

            agg_dataset['SHARE_UPR'] = agg_dataset['UPR_x'] / agg_dataset['UPR_y']
            agg_dataset['SHARE_EMPLOYEES'] = agg_dataset['EMPLOYEES_x'] / agg_dataset['EMPLOYEES_y']
            agg_dataset['SHARE_ASSETS'] = agg_dataset['ASSETS_x'] / agg_dataset['ASSETS_y']

            agg_dataset['SHARE_KEY'] = (
                share_UPR * agg_dataset['SHARE_UPR']
                + share_employees * agg_dataset['SHARE_EMPLOYEES']
                + share_assets * agg_dataset['SHARE_ASSETS']
            )

            avg_domestic_shares_foreign = agg_dataset.set_index('YEA')['SHARE_KEY'].to_dict()

            print("Average domestic shares:")
            print(avg_domestic_shares_foreign)

        else:

            avg_domestic_shares_foreign = {y: 0 for y in sales_mapping['YEA'].unique()}

        # For the computation of average allocation keys, we consider all the partner jurisdictions included in the
        # OECD's country-by-country report statistics (not only in the sub-sample excluding loss-making entities but
        # in the whole dataset since allocation keys are sourced in the overall dataset)
        iteration = pd.read_csv(self.path_to_oecd, usecols=['JUR'])['JUR'].unique()
        iteration = iteration[~np.isin(iteration, ['STA', 'FJT'])].copy()

        # We extend this set to countries implementing the UTPR but never reported as partners in the data
        # They will get a share of allocation key of 0 and thus 0 revenue gains (except if we have them as parents)
        iteration = np.union1d(np.union1d(iteration, UTPR_incl_domestic), UTPR_excl_domestic)

        for country in iteration:

            sales_mapping_foreign_MNEs = sales_mapping[sales_mapping['COU'] != country].copy()

            sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs[
                sales_mapping_foreign_MNEs['COU'] != sales_mapping_foreign_MNEs['JUR']
            ].copy()

            country_extract = sales_mapping_foreign_MNEs[sales_mapping_foreign_MNEs['JUR'] == country].copy()

            agg_country_extract = country_extract.groupby('YEA').sum()[['UPR', 'EMPLOYEES', 'ASSETS']].reset_index()
            agg_sales_mapping_foreign_MNEs = sales_mapping_foreign_MNEs.groupby('YEA').sum()[
                ['UPR', 'EMPLOYEES', 'ASSETS']
            ].reset_index()

            agg_dataset = agg_country_extract.merge(agg_sales_mapping_foreign_MNEs, how='outer', on='YEA')

            agg_dataset['SHARE_UPR'] = agg_dataset['UPR_x'] / agg_dataset['UPR_y']
            agg_dataset['SHARE_EMPLOYEES'] = agg_dataset['EMPLOYEES_x'] / agg_dataset['EMPLOYEES_y']
            agg_dataset['SHARE_ASSETS'] = agg_dataset['ASSETS_x'] / agg_dataset['ASSETS_y']

            agg_dataset['SHARE_KEY'] = (
                share_UPR * agg_dataset['SHARE_UPR']
                + share_employees * agg_dataset['SHARE_EMPLOYEES']
                + share_assets * agg_dataset['SHARE_ASSETS']
            )

            agg_dataset = agg_dataset.sort_values(by='YEA')

            avg_allocation_keys_foreign['YEAR'] += list(agg_dataset['YEA'].values)
            avg_allocation_keys_foreign['SHARE_KEY'] += list(agg_dataset['SHARE_KEY'].values)
            avg_allocation_keys_foreign['JUR'] += [country] * len(agg_dataset)

        avg_allocation_keys_foreign = pd.DataFrame(avg_allocation_keys_foreign)

        print("Average foreign allocation key for France:")
        print(avg_allocation_keys_foreign[avg_allocation_keys_foreign['JUR'] == 'FRA'])
        print("Before the re-scaling of the foreign average allocation keys, they sum to:")
        print(avg_allocation_keys_foreign.groupby('YEAR').sum()['SHARE_KEY'])

        # XX: To be removed
        import time
        time1 = time.time()
        print('checking time - start')

        avg_allocation_keys_domestic['TEMP_KEY'] = 1
        other_domestic_UTPR_TDs['TEMP_KEY'] = 1

        other_domestic_UTPR_TDs = other_domestic_UTPR_TDs.merge(
            avg_allocation_keys_domestic,
            how='left',
            on=['YEAR', 'TEMP_KEY']
        ).drop(columns=['TEMP_KEY'])

        # XX: To be removed
        time2 = time.time()
        print('checking time - intermediary 1', time2 - time1)

        other_domestic_UTPR_TDs = other_domestic_UTPR_TDs[
            other_domestic_UTPR_TDs['PARENT_COUNTRY_CODE'] != other_domestic_UTPR_TDs['JUR']
        ].copy()

        if among_countries_implementing:
            other_domestic_UTPR_TDs = other_domestic_UTPR_TDs[
                other_domestic_UTPR_TDs['JUR'].isin(UTPR_incl_domestic)
            ].copy()

        # XX: To be removed
        time3 = time.time()
        print('checking time - intermediary 2', time3 - time2)

        if not other_domestic_UTPR_TDs.empty:
            # # XX to be removed
            # return other_domestic_UTPR_TDs

            # other_domestic_UTPR_TDs['SHARE_KEY_TOTAL'] = other_domestic_UTPR_TDs.groupby(
            #     ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'YEAR', 'SOURCE']
            # ).transform('sum')['SHARE_KEY']

            tmp = other_domestic_UTPR_TDs[
                ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'YEAR', 'SOURCE', 'SHARE_KEY']
            ].groupby(
                ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'YEAR', 'SOURCE']
            ).sum().reset_index().rename(
                columns={'SHARE_KEY': 'SHARE_KEY_TOTAL'}
            )

            other_domestic_UTPR_TDs = other_domestic_UTPR_TDs.merge(
                tmp,
                how='left',
                on=['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'YEAR', 'SOURCE']
            )

            del tmp

            if among_countries_implementing:
                other_domestic_UTPR_TDs['RESCALING_FACTOR'] = other_domestic_UTPR_TDs['PARENT_COUNTRY_CODE'].isin(
                    UTPR_incl_domestic
                )
                other_domestic_UTPR_TDs['RESCALING_FACTOR'] *= (
                    1 - other_domestic_UTPR_TDs['YEAR'].map(avg_domestic_shares_domestic)
                ) / other_domestic_UTPR_TDs['SHARE_KEY_TOTAL']
                other_domestic_UTPR_TDs['RESCALING_FACTOR'] = other_domestic_UTPR_TDs.apply(
                    lambda row: {0: 1 / row['SHARE_KEY_TOTAL']}.get(
                        row['RESCALING_FACTOR'], row['RESCALING_FACTOR']
                    ),
                    axis=1
                )
            else:
                other_domestic_UTPR_TDs['RESCALING_FACTOR'] = (
                    1 - other_domestic_UTPR_TDs['YEAR'].map(avg_domestic_shares_domestic)
                ) / other_domestic_UTPR_TDs['SHARE_KEY_TOTAL']

        else:

            other_domestic_UTPR_TDs['SHARE_KEY_TOTAL'] = other_domestic_UTPR_TDs['SHARE_KEY']
            other_domestic_UTPR_TDs['RESCALING_FACTOR'] = other_domestic_UTPR_TDs['SHARE_KEY']

        # XX: To be removed
        time4 = time.time()
        print('checking time - intermediary 3', time4 - time3)

        other_domestic_UTPR_TDs['SHARE_KEY'] *= other_domestic_UTPR_TDs['RESCALING_FACTOR']

        extract = other_domestic_UTPR_TDs[
            other_domestic_UTPR_TDs['PARENT_COUNTRY_CODE'].isin(UTPR_incl_domestic)
        ].copy()

        extract = extract.groupby(
            ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'SOURCE', 'YEAR']
        ).first().reset_index()

        extract['JUR'] = extract['PARENT_COUNTRY_CODE']
        extract['SHARE_KEY'] = extract['YEAR'].map(avg_domestic_shares_foreign)

        other_domestic_UTPR_TDs = pd.concat([other_domestic_UTPR_TDs, extract], axis=0)

        # for parent_country in other_domestic_UTPR_TDs['PARENT_COUNTRY_CODE'].unique():
        #     if parent_country in UTPR_incl_domestic:
        #         extract = other_domestic_UTPR_TDs[
        #             other_domestic_UTPR_TDs['PARENT_COUNTRY_CODE'] == parent_country
        #         ].copy()

        #         extract['JUR'] = parent_country
        #         extract['SHARE_KEY'] = extract['YEAR'].map(avg_domestic_shares_domestic)

        #         other_domestic_UTPR_TDs = pd.concat([other_domestic_UTPR_TDs, extract], axis=0)

        #     else:
        #         continue

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
            on=['YEAR', 'TEMP_KEY']
        ).drop(columns=['TEMP_KEY'])

        other_foreign_UTPR_TDs = other_foreign_UTPR_TDs[
            other_foreign_UTPR_TDs['PARENT_COUNTRY_CODE'] != other_foreign_UTPR_TDs['JUR']
        ].copy()

        # XX: To be removed
        time5 = time.time()
        print('checking time - intermediary 4', time5 - time4)

        if among_countries_implementing:
            other_foreign_UTPR_TDs = other_foreign_UTPR_TDs[
                other_foreign_UTPR_TDs['JUR'].isin(np.union1d(UTPR_incl_domestic, UTPR_excl_domestic))
            ].copy()

        if not other_foreign_UTPR_TDs.empty:

            # other_foreign_UTPR_TDs['SHARE_KEY_TOTAL'] = other_foreign_UTPR_TDs.groupby(
            #     ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'YEAR', 'SOURCE']
            # ).transform('sum')['SHARE_KEY']

            tmp = other_foreign_UTPR_TDs[
                ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'YEAR', 'SOURCE', 'SHARE_KEY']
            ].groupby(
                ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'YEAR', 'SOURCE']
            ).sum().reset_index().rename(
                columns={'SHARE_KEY': 'SHARE_KEY_TOTAL'}
            )

            other_foreign_UTPR_TDs = other_foreign_UTPR_TDs.merge(
                tmp,
                how='left',
                on=['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'YEAR', 'SOURCE']
            )

            if among_countries_implementing:
                other_foreign_UTPR_TDs['RESCALING_FACTOR'] = other_foreign_UTPR_TDs['PARENT_COUNTRY_CODE'].isin(
                    UTPR_incl_domestic + UTPR_excl_domestic
                )
                other_foreign_UTPR_TDs['RESCALING_FACTOR'] *= (
                    1 - other_foreign_UTPR_TDs['YEAR'].map(avg_domestic_shares_foreign)
                ) / other_foreign_UTPR_TDs['SHARE_KEY_TOTAL']
                other_foreign_UTPR_TDs['RESCALING_FACTOR'] = other_foreign_UTPR_TDs.apply(
                    lambda row: {0: 1 / row['SHARE_KEY_TOTAL']}.get(
                        row['RESCALING_FACTOR'], row['RESCALING_FACTOR']
                    ),
                    axis=1
                )
            else:
                other_foreign_UTPR_TDs['RESCALING_FACTOR'] = (
                    1 - other_foreign_UTPR_TDs['YEAR'].map(avg_domestic_shares_foreign)
                ) / other_foreign_UTPR_TDs['SHARE_KEY_TOTAL']

        else:

            other_foreign_UTPR_TDs['SHARE_KEY_TOTAL'] = other_foreign_UTPR_TDs['SHARE_KEY']
            other_foreign_UTPR_TDs['RESCALING_FACTOR'] = other_foreign_UTPR_TDs['SHARE_KEY']

        # XX: To be removed
        time6 = time.time()
        print('checking time - intermediary 5', time6 - time5)

        other_foreign_UTPR_TDs['SHARE_KEY'] *= other_foreign_UTPR_TDs['RESCALING_FACTOR']

        extract = other_foreign_UTPR_TDs[
            other_foreign_UTPR_TDs['PARENT_COUNTRY_CODE'].isin(UTPR_incl_domestic + UTPR_excl_domestic)
        ].copy()

        extract = extract.groupby(
            ['PARENT_COUNTRY_CODE', 'PARTNER_COUNTRY_CODE', 'SOURCE', 'YEAR']
        ).first().reset_index()

        extract['JUR'] = extract['PARENT_COUNTRY_CODE']
        extract['SHARE_KEY'] = extract['YEAR'].map(avg_domestic_shares_foreign)

        other_foreign_UTPR_TDs = pd.concat([other_foreign_UTPR_TDs, extract], axis=0)

        # for parent_country in other_foreign_UTPR_TDs['PARENT_COUNTRY_CODE'].unique():
        #     if parent_country in UTPR_incl_domestic + UTPR_excl_domestic:
        #         df = other_foreign_UTPR_TDs[other_foreign_UTPR_TDs['PARENT_COUNTRY_CODE'] == parent_country].copy()

        #         jur = df['JUR'].unique()
        #         jur = jur[0]

        #         df = df[df['JUR'] == jur].copy()

        #         df['JUR'] = parent_country
        #         df['SHARE_KEY'] = df['YEAR'].map(avg_domestic_shares_foreign)

        #         other_foreign_UTPR_TDs = pd.concat([other_foreign_UTPR_TDs, df], axis=0)

        #     else:
        #         continue

        other_foreign_UTPR_TDs = other_foreign_UTPR_TDs.rename(
            columns={
                'JUR': 'COLLECTING_COUNTRY_CODE',
                'Partner Jurisdiction': 'COLLECTING_COUNTRY_NAME',
                'SHARE_KEY': 'SHARE_COLLECTED'
            }
        )

        # XX: To be removed
        time7 = time.time()
        print('checking time - intermediary 6', time7 - time6)

        # --- Other than UTPR

        non_UTPR_extract = full_sample_df[
            np.logical_and(
                ~full_sample_df['collected_through_domestic_UTPR'],
                ~full_sample_df['collected_through_foreign_UTPR']
            )
        ].copy()

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

        # XX: To be removed
        time8 = time.time()
        print('checking time - intermediary 8', time8 - time7)

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

            return full_sample_df.groupby(
                ['COLLECTING_COUNTRY_CODE', 'YEAR']
            ).agg(
                {'COLLECTING_COUNTRY_NAME': 'first', 'ALLOCATED_TAX_DEFICIT': 'sum'}
            ).reset_index()

        else:

            return full_sample_df.copy()


if __name__ == '__main__':

    print("Command line use to be determined?")
