import numpy as np

import random

from tax_deficit_simulator.results import TaxDeficitResults
from tax_deficit_simulator.calculator import TaxDeficitCalculator


def test_headquarter_scenario():

    TDResults = TaxDeficitResults(output_folder="~/Desktop", load_online_data=False)

    (
        calculator_noCO, calculator_firstyearCO, calculator_longtermCO
    ) = TDResults.load_benchmark_data_for_all_carve_outs()

    for calculator in [calculator_noCO, calculator_firstyearCO, calculator_longtermCO]:

        for rate in [random.uniform(0.1, 0.2), random.uniform(0.2, 0.3)]:

            print("Rate considered for the test:", rate)

            old_df = calculator.compute_all_tax_deficits(
                minimum_ETR=rate, exclude_non_EU_domestic_TDs=True
            )

            full_sample_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_excl_domestic=TDResults.all_countries_but_EU,
                IIR_incl_domestic=TDResults.eu_27_country_codes,
                UTPR_excl_domestic=[],
                UTPR_incl_domestic=[],
                return_bilateral_details=True
            )

            new_df = full_sample_df.groupby(
                ['COLLECTING_COUNTRY_CODE', 'YEAR']
            ).sum()['ALLOCATED_TAX_DEFICIT'].reset_index()

            new_df = new_df[['COLLECTING_COUNTRY_CODE', 'ALLOCATED_TAX_DEFICIT', 'YEAR']].copy()
            old_df = old_df[['Parent jurisdiction (alpha-3 code)', 'tax_deficit', 'YEAR']].copy()

            merged_df = new_df.merge(
                old_df,
                how='outer',
                left_on=['COLLECTING_COUNTRY_CODE', 'YEAR'], right_on=['Parent jurisdiction (alpha-3 code)', 'YEAR']
            ).drop(columns=['Parent jurisdiction (alpha-3 code)'])

            # Checking that, with the new method, we cover all countries with revenue gains in the old method
            assert merged_df[merged_df['ALLOCATED_TAX_DEFICIT'].isnull()].empty

            # Checking that, with the old method, we only lack tax deficits for countries that have 0 revenue gains
            assert merged_df[merged_df['tax_deficit'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0

            merged_df['DIFF'] = merged_df['ALLOCATED_TAX_DEFICIT'] - merged_df['tax_deficit']
            merged_df['RELATIVE_DIFF'] = merged_df['DIFF'] / merged_df['tax_deficit'] * 100

            # Checking that the relative difference between both estimates is never larger than 10**(-6)
            assert merged_df[np.abs(merged_df['RELATIVE_DIFF']) > 10**(-6)].empty


def test_headquarter_scenario_with_all_domestic():

    TDResults = TaxDeficitResults(output_folder="~/Desktop", load_online_data=False)

    (
        calculator_noCO, calculator_firstyearCO, calculator_longtermCO
    ) = TDResults.load_benchmark_data_for_all_carve_outs()

    for calculator in [calculator_noCO, calculator_firstyearCO, calculator_longtermCO]:

        for rate in [random.uniform(0.1, 0.2), random.uniform(0.2, 0.3)]:

            print("Rate considered for the test:", rate)

            old_df = calculator.compute_all_tax_deficits(
                minimum_ETR=rate, exclude_non_EU_domestic_TDs=False
            )

            full_sample_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_excl_domestic=[],
                IIR_incl_domestic=TDResults.all_countries,
                UTPR_excl_domestic=[],
                UTPR_incl_domestic=[],
                return_bilateral_details=True
            )

            new_df = full_sample_df.groupby(
                ['COLLECTING_COUNTRY_CODE', 'YEAR']
            ).sum()['ALLOCATED_TAX_DEFICIT'].reset_index()

            new_df = new_df[['COLLECTING_COUNTRY_CODE', 'ALLOCATED_TAX_DEFICIT', 'YEAR']].copy()
            old_df = old_df[['Parent jurisdiction (alpha-3 code)', 'tax_deficit', 'YEAR']].copy()

            merged_df = new_df.merge(
                old_df,
                how='outer',
                left_on=['COLLECTING_COUNTRY_CODE', 'YEAR'], right_on=['Parent jurisdiction (alpha-3 code)', 'YEAR']
            ).drop(columns=['Parent jurisdiction (alpha-3 code)'])

            # Checking that, with the new method, we cover all countries with revenue gains in the old method
            assert merged_df[merged_df['ALLOCATED_TAX_DEFICIT'].isnull()].empty

            # Checking that, with the old method, we only lack tax deficits for countries that have 0 revenue gains
            assert merged_df[merged_df['tax_deficit'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0

            merged_df['DIFF'] = merged_df['ALLOCATED_TAX_DEFICIT'] - merged_df['tax_deficit']
            merged_df['RELATIVE_DIFF'] = merged_df['DIFF'] / merged_df['tax_deficit'] * 100

            # Checking that the relative difference between both estimates is never larger than 10**(-6)
            assert merged_df[np.abs(merged_df['RELATIVE_DIFF']) > 10**(-6)].empty
