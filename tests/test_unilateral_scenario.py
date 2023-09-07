import numpy as np

import random

from tax_deficit_simulator.results import TaxDeficitResults
from tax_deficit_simulator.calculator import TaxDeficitCalculator


def test_unilateral_scenario():

    TDResults = TaxDeficitResults(output_folder="~/Desktop", load_online_data=False)

    for year in [2016, 2017, 2018]:

        (
            calculator_noCO, calculator_firstyearCO, calculator_longtermCO
        ) = TDResults.load_benchmark_data_for_all_carve_outs(year)

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
                    upgrade_to_2021=False
                )

                hq_revenue_gains = calculator.compute_all_tax_deficits(
                    minimum_ETR=rate, upgrade_to_2021=False, exclude_non_EU_domestic_TDs=False
                )[['Parent jurisdiction (alpha-3 code)', 'tax_deficit']].rename(
                    columns={'tax_deficit': 'hq_gains'}
                )

                check_df = unilateral_revenue_gains.copy()
                check_df['hq_gains_repl'] = check_df['total'] - check_df[
                    ['directly_allocated_for', 'imputed_foreign']
                ].sum(axis=1)
                check_df = check_df[['Parent jurisdiction (alpha-3 code)', 'hq_gains_repl']].copy()
                check_df = check_df.merge(hq_revenue_gains, on='Parent jurisdiction (alpha-3 code)', how='outer')

                check_df['DIFF'] = check_df['hq_gains_repl'] - check_df['hq_gains']
                check_df['RELATIVE_DIFF'] = check_df['DIFF'] / check_df['hq_gains']

                assert check_df[check_df['hq_gains_repl'].isnull()]['hq_gains'].sum() == 0
                assert check_df[check_df['hq_gains'].isnull()]['hq_gains_repl'].sum() == 0
                assert check_df[check_df['RELATIVE_DIFF'].isnull()]['hq_gains'].sum() == 0
                assert check_df[check_df['RELATIVE_DIFF'].isnull()]['hq_gains_repl'].sum() == 0
                assert (check_df['RELATIVE_DIFF'] > 0.0000001).sum() == 0

                extract_df = unilateral_revenue_gains[unilateral_revenue_gains['total'] > 0].sample(3)

                for (_, row) in extract_df.iterrows():

                    country_code = row['Parent jurisdiction (alpha-3 code)']
                    revenue_gains = row['total']

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

                    check1 = output_df[output_df['ALLOCATED_TAX_DEFICIT'] > 0].iloc[0, 2]

                    diff1 = check1 - revenue_gains
                    relative_diff1 = diff1 / revenue_gains
                    assert relative_diff1 <= 0.0000001

                    alternative_computation, _, _ = calculator.compute_selected_intermediary_scenario_gain(
                        countries_implementing=[country_code],
                        among_countries_implementing=False,
                        minimum_ETR=rate,
                        minimum_breakdown=60,
                        weight_UPR=weight_UPR,
                        weight_employees=weight_employees,
                        weight_assets=weight_assets,
                        exclude_non_implementing_domestic_TDs=False,
                        upgrade_to_2021=False
                    )

                    check2 = alternative_computation.loc[0, 'total']

                    diff2 = check2 - revenue_gains
                    relative_diff2 = diff2 / revenue_gains
                    assert relative_diff2 <= 0.0000001
