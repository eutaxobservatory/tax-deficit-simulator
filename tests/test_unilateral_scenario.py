import numpy as np

import random

from tax_deficit_simulator.results import TaxDeficitResults
from tax_deficit_simulator.calculator import TaxDeficitCalculator


def test_unilateral_scenario():

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

            unilateral_revenue_gains, _, _, _ = calculator.compute_unilateral_scenario_revenue_gains(
                full_own_tax_deficit=True,
                minimum_ETR=rate,
                minimum_breakdown=60,
                weight_UPR=weight_UPR,
                weight_assets=weight_assets,
                weight_employees=weight_employees,
                exclude_domestic_TDs=False,
            )

            hq_revenue_gains = calculator.compute_all_tax_deficits(
                minimum_ETR=rate, exclude_non_EU_domestic_TDs=False
            )[['Parent jurisdiction (alpha-3 code)', 'tax_deficit', 'YEAR']].rename(
                columns={'tax_deficit': 'hq_gains'}
            )

            check_df = unilateral_revenue_gains.copy()
            check_df['hq_gains_repl'] = check_df['total'] - check_df[
                ['directly_allocated_for', 'imputed_foreign']
            ].sum(axis=1)
            check_df = check_df[['Parent jurisdiction (alpha-3 code)', 'hq_gains_repl', 'YEAR']].copy()
            check_df = check_df.merge(
                hq_revenue_gains,
                on=['Parent jurisdiction (alpha-3 code)', 'YEAR'],
                how='outer'
            )

            check_df['DIFF'] = check_df['hq_gains_repl'] - check_df['hq_gains']
            check_df['RELATIVE_DIFF'] = check_df['DIFF'] / check_df['hq_gains']

            assert check_df[check_df['hq_gains_repl'].isnull()]['hq_gains'].sum() == 0
            assert check_df[check_df['hq_gains'].isnull()]['hq_gains_repl'].sum() == 0
            assert check_df[check_df['RELATIVE_DIFF'].isnull()]['hq_gains'].sum() == 0
            assert check_df[check_df['RELATIVE_DIFF'].isnull()]['hq_gains_repl'].sum() == 0
            assert (np.abs(check_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0

            extract_countries = unilateral_revenue_gains[
                unilateral_revenue_gains['total'] > 0
            ]['Parent jurisdiction (alpha-3 code)'].sample(3)

            extract_df = unilateral_revenue_gains[
                unilateral_revenue_gains['Parent jurisdiction (alpha-3 code)'].isin(extract_countries)
            ].copy()

            for country_code in extract_countries:

                revenue_gains = extract_df[
                    extract_df['Parent jurisdiction (alpha-3 code)'] == country_code
                ][['total', 'YEAR']].copy()

                output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=[country_code],
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=[country_code],
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=False,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=False,
                    return_bilateral_details=False
                )

                check1 = output_df[output_df['ALLOCATED_TAX_DEFICIT'] > 0][['ALLOCATED_TAX_DEFICIT', 'YEAR']].copy()

                diff1 = revenue_gains.merge(check1, how='outer', on='YEAR')
                diff1['diff1'] = diff1['ALLOCATED_TAX_DEFICIT'] - diff1['total']
                diff1['relative_diff1'] = diff1['diff1'] / diff1['total']
                assert (np.abs(diff1['relative_diff1']) > 0.0000001).sum() == 0

                alternative_computation, _, _ = calculator.compute_selected_intermediary_scenario_gain(
                    countries_implementing=[country_code],
                    among_countries_implementing=False,
                    minimum_ETR=rate,
                    minimum_breakdown=60,
                    weight_UPR=weight_UPR,
                    weight_employees=weight_employees,
                    weight_assets=weight_assets,
                    exclude_non_implementing_domestic_TDs=False
                )

                check2 = alternative_computation[['total', 'YEAR']].copy()
                check2 = check2.rename(columns={'total': 'total_alternative'})

                diff2 = revenue_gains.merge(check2, how='outer', on='YEAR')
                diff2['diff2'] = diff2['total_alternative'] - diff2['total']
                diff2['relative_diff2'] = diff2['diff2'] / diff2['total']
                assert (np.abs(diff2['relative_diff2']) > 0.0000001).sum() == 0
