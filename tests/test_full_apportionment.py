import numpy as np

import random

from tax_deficit_simulator.results import TaxDeficitResults
from tax_deficit_simulator.calculator import TaxDeficitCalculator


def test_full_apportionment():

    TDResults = TaxDeficitResults(output_folder="~/Desktop", load_online_data=False)

    (
        calculator_noCO, calculator_firstyearCO, calculator_longtermCO
    ) = TDResults.load_benchmark_data_for_all_carve_outs()

    for calculator in [calculator_noCO, calculator_firstyearCO, calculator_longtermCO]:

        for i in (0, 1):

            if not i:

                weight_UPR = 1
                weight_assets = 0
                weight_employees = 0

            else:

                weight_UPR = random.uniform(0, 2)
                weight_assets = random.uniform(0, 2)
                weight_employees = random.uniform(0, 2)

                print("Weight for UPR:", weight_UPR)
                print("Weight for assets:", weight_assets)
                print("Weight for employees:", weight_employees)

            rate = random.uniform(0.15, 0.3)

            print("Minimum effective tax rate:", rate)

            (results_df, _, _, _) = calculator.compute_unilateral_scenario_revenue_gains(
                full_own_tax_deficit=False,
                minimum_ETR=rate,
                minimum_breakdown=60,
                weight_UPR=weight_UPR,
                weight_assets=weight_assets,
                weight_employees=weight_employees,
                exclude_domestic_TDs=False
            )

            total_revenue_gains = results_df[['total', 'YEAR']].groupby('YEAR').sum()

            hq_revenue_gains = calculator.compute_all_tax_deficits(
                minimum_ETR=rate, exclude_non_EU_domestic_TDs=False
            )
            total_hq_revenue_gains = hq_revenue_gains[['tax_deficit', 'YEAR']].groupby('YEAR').sum()
            total_hq_revenue_gains = total_hq_revenue_gains.rename(columns={'tax_deficit': 'total_hq'})

            diff1 = total_revenue_gains.merge(total_hq_revenue_gains, how='outer', on='YEAR')
            diff1['diff1'] = diff1['total'] - diff1['total_hq']
            diff1['relative_diff1'] = diff1['diff1'] / diff1['total_hq']
            assert (np.abs(diff1['relative_diff1']) > 0.0000001).sum() == 0

            agg_output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_incl_domestic=[],
                IIR_excl_domestic=[],
                UTPR_incl_domestic=TDResults.all_countries,
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=False,
                weight_UPR=weight_UPR,
                weight_assets=weight_assets,
                weight_employees=weight_employees,
                minimum_breakdown=60,
                among_countries_implementing=False,
                return_bilateral_details=False
            )
            total_revenue_gains_new_method1 = agg_output_df[['ALLOCATED_TAX_DEFICIT', 'YEAR']].groupby('YEAR').sum()

            diff2 = total_revenue_gains_new_method1.merge(total_revenue_gains, how='outer', on='YEAR')
            diff2['diff2'] = diff2['ALLOCATED_TAX_DEFICIT'] - diff2['total']
            diff2['relative_diff2'] = diff2['diff2'] / diff2['total']
            assert (np.abs(diff2['relative_diff2']) > 0.0000001).sum() == 0

            merged_df = agg_output_df.merge(
                results_df[['Parent jurisdiction (alpha-3 code)', 'total', 'YEAR']],
                how='outer',
                left_on=['COLLECTING_COUNTRY_CODE', 'YEAR'], right_on=['Parent jurisdiction (alpha-3 code)', 'YEAR']
            )

            merged_df['DIFF'] = merged_df['ALLOCATED_TAX_DEFICIT'] - merged_df['total']
            merged_df['RELATIVE_DIFF'] = merged_df['DIFF'] / merged_df['total']

            assert merged_df[merged_df['total'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
            assert merged_df[merged_df['ALLOCATED_TAX_DEFICIT'].isnull()]['total'].sum() == 0
            assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['total'].sum() == 0
            assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
            assert (np.abs(merged_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0

            agg_output_df2 = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_incl_domestic=[],
                IIR_excl_domestic=[],
                UTPR_incl_domestic=TDResults.all_countries,
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=False,
                weight_UPR=weight_UPR,
                weight_assets=weight_assets,
                weight_employees=weight_employees,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=False
            )
            total_revenue_gains_new_method2 = agg_output_df2[['ALLOCATED_TAX_DEFICIT', 'YEAR']].groupby('YEAR').sum()

            diff3 = total_revenue_gains_new_method2.merge(total_revenue_gains, how='outer', on='YEAR')
            diff3['diff3'] = diff3['ALLOCATED_TAX_DEFICIT'] - diff3['total']
            diff3['relative_diff3'] = diff3['diff3'] / diff3['total']
            assert (np.abs(diff3['relative_diff3']) > 0.0000001).sum() == 0

            merged_df = agg_output_df2.merge(
                results_df[['Parent jurisdiction (alpha-3 code)', 'total', 'YEAR']],
                how='outer',
                left_on=['COLLECTING_COUNTRY_CODE', 'YEAR'], right_on=['Parent jurisdiction (alpha-3 code)', 'YEAR']
            )

            merged_df['DIFF'] = merged_df['ALLOCATED_TAX_DEFICIT'] - merged_df['total']
            merged_df['RELATIVE_DIFF'] = merged_df['DIFF'] / merged_df['total']

            assert merged_df[merged_df['total'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
            assert merged_df[merged_df['ALLOCATED_TAX_DEFICIT'].isnull()]['total'].sum() == 0
            assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['total'].sum() == 0
            assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
            assert (np.abs(merged_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0
