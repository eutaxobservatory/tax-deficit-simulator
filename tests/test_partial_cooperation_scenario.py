import numpy as np

import random

from tax_deficit_simulator.results import TaxDeficitResults
from tax_deficit_simulator.calculator import TaxDeficitCalculator


def test_partial_cooperation_scenario_1():

    # Scenario tested here:
    # Implementation of the deal solely by EU Member-States
    # They adopt an IIR including their domestic tax deficits
    # And a UTPR including foreign multinationals' domestic tax deficits

    TDResults = TaxDeficitResults(output_folder="~/Desktop", load_online_data=False)

    # for year in [2016, 2017, 2018]:
    for year in [2018]:

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

                alternative_computation, _, _ = calculator.compute_selected_intermediary_scenario_gain(
                    countries_implementing=calculator.eu_27_country_codes,
                    among_countries_implementing=True,
                    minimum_ETR=rate,
                    minimum_breakdown=60,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    exclude_non_implementing_domestic_TDs=False,
                    upgrade_to_2021=False
                )

                alternative_computation_tmp = alternative_computation[
                    ['Parent jurisdiction (alpha-3 code)', 'total']
                ].copy()

                output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=False,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=True,
                    return_bilateral_details=True
                )

                if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                    multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                    multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                        lambda x: {'CHN': multiplier}.get(x, 1)
                    )

                    for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                        output_df[col] *= multiplier

                relevant_columns = []
                aggregation = {'COLLECTING_COUNTRY_NAME': 'first'}

                for location in ['domestic', 'foreign']:
                    for instrument in ['IIR', 'UTPR', 'QDMTT']:

                        col = f'collected_through_{location}_{instrument}'

                        output_df['TAX_DEFICIT' + col] = (
                            output_df['ALLOCATED_TAX_DEFICIT'] * output_df[col]
                        )

                        output_df['TAX_DEFICIT' + col] = output_df['TAX_DEFICIT' + col].astype(float)

                        relevant_columns.append('TAX_DEFICIT' + col)
                        aggregation['TAX_DEFICIT' + col] = 'sum'

                decomposed_df = output_df.groupby('COLLECTING_COUNTRY_CODE').agg(aggregation).reset_index()
                decomposed_df['TAX_DEFICIT_total'] = decomposed_df[relevant_columns].sum(axis=1)

                agg_output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=False,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=True,
                    return_bilateral_details=False
                )

                merged_df = decomposed_df.merge(agg_output_df, how='outer', on='COLLECTING_COUNTRY_CODE')

                merged_df['DIFF'] = merged_df['TAX_DEFICIT_total'] - merged_df['ALLOCATED_TAX_DEFICIT']
                merged_df['RELATIVE_DIFF'] = merged_df['DIFF'] / merged_df['ALLOCATED_TAX_DEFICIT']

                assert merged_df[merged_df['TAX_DEFICIT_total'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
                assert merged_df[merged_df['ALLOCATED_TAX_DEFICIT'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
                assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert (np.abs(merged_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0

                merged_df = merged_df.drop(columns=['ALLOCATED_TAX_DEFICIT', 'COLLECTING_COUNTRY_NAME_y', 'DIFF'])

                temp_df = merged_df.merge(
                    alternative_computation_tmp,
                    how='outer',
                    left_on='COLLECTING_COUNTRY_CODE', right_on='Parent jurisdiction (alpha-3 code)'
                ).drop(columns=['Parent jurisdiction (alpha-3 code)'])

                temp_df['DIFF'] = temp_df['TAX_DEFICIT_total'] - temp_df['total']
                temp_df['RELATIVE_DIFF'] = temp_df['DIFF'] / temp_df['total']

                assert temp_df[temp_df['TAX_DEFICIT_total'].isnull()]['total'].sum() == 0
                assert temp_df[temp_df['total'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert temp_df[temp_df['RELATIVE_DIFF'].isnull()]['total'].sum() == 0
                assert temp_df[temp_df['RELATIVE_DIFF'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert (np.abs(temp_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0


def test_partial_cooperation_scenario_2():

    # Scenario tested here:
    # Implementation of the deal by EU Member-States and a list of adopting jurisdictions
    # They adopt an IIR including their domestic tax deficits
    # And a UTPR including foreign multinationals' domestic tax deficits

    non_EU_implementing_countries = [
        'AUS', 'CYM', 'GGY', 'HKG', 'IMN', 'JPN', 'JEY', 'KOR', 'LIE', 'MYS', 'NZL', 'QAT', 'SGP', 'CHE', 'GBR'
    ]

    TDResults = TaxDeficitResults(output_folder="~/Desktop", load_online_data=False)

    # for year in [2016, 2017, 2018]:
    for year in [2018]:

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

                alternative_computation, _, _ = calculator.compute_selected_intermediary_scenario_gain(
                    countries_implementing=calculator.eu_27_country_codes + non_EU_implementing_countries,
                    among_countries_implementing=True,
                    minimum_ETR=rate,
                    minimum_breakdown=60,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    exclude_non_implementing_domestic_TDs=False,
                    upgrade_to_2021=False
                )

                alternative_computation_tmp = alternative_computation[
                    ['Parent jurisdiction (alpha-3 code)', 'total']
                ].copy()

                output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes + non_EU_implementing_countries,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes + non_EU_implementing_countries,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=False,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=True,
                    return_bilateral_details=True
                )

                if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                    multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                    multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                        lambda x: {'CHN': multiplier}.get(x, 1)
                    )

                    for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                        output_df[col] *= multiplier

                relevant_columns = []
                aggregation = {'COLLECTING_COUNTRY_NAME': 'first'}

                for location in ['domestic', 'foreign']:
                    for instrument in ['IIR', 'UTPR', 'QDMTT']:

                        col = f'collected_through_{location}_{instrument}'

                        output_df['TAX_DEFICIT' + col] = (
                            output_df['ALLOCATED_TAX_DEFICIT'] * output_df[col]
                        )

                        output_df['TAX_DEFICIT' + col] = output_df['TAX_DEFICIT' + col].astype(float)

                        relevant_columns.append('TAX_DEFICIT' + col)
                        aggregation['TAX_DEFICIT' + col] = 'sum'

                decomposed_df = output_df.groupby('COLLECTING_COUNTRY_CODE').agg(aggregation).reset_index()
                decomposed_df['TAX_DEFICIT_total'] = decomposed_df[relevant_columns].sum(axis=1)

                agg_output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes + non_EU_implementing_countries,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes + non_EU_implementing_countries,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=False,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=True,
                    return_bilateral_details=False
                )

                merged_df = decomposed_df.merge(agg_output_df, how='outer', on='COLLECTING_COUNTRY_CODE')

                merged_df['DIFF'] = merged_df['TAX_DEFICIT_total'] - merged_df['ALLOCATED_TAX_DEFICIT']
                merged_df['RELATIVE_DIFF'] = merged_df['DIFF'] / merged_df['ALLOCATED_TAX_DEFICIT']

                assert merged_df[merged_df['TAX_DEFICIT_total'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
                assert merged_df[merged_df['ALLOCATED_TAX_DEFICIT'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
                assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert (np.abs(merged_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0

                merged_df = merged_df.drop(columns=['ALLOCATED_TAX_DEFICIT', 'COLLECTING_COUNTRY_NAME_y', 'DIFF'])

                temp_df = merged_df.merge(
                    alternative_computation_tmp,
                    how='outer',
                    left_on='COLLECTING_COUNTRY_CODE', right_on='Parent jurisdiction (alpha-3 code)'
                ).drop(columns=['Parent jurisdiction (alpha-3 code)'])

                temp_df['DIFF'] = temp_df['TAX_DEFICIT_total'] - temp_df['total']
                temp_df['RELATIVE_DIFF'] = temp_df['DIFF'] / temp_df['total']

                assert temp_df[temp_df['TAX_DEFICIT_total'].isnull()]['total'].sum() == 0
                assert temp_df[temp_df['total'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert temp_df[temp_df['RELATIVE_DIFF'].isnull()]['total'].sum() == 0
                assert temp_df[temp_df['RELATIVE_DIFF'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert (np.abs(temp_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0


def test_partial_cooperation_scenario_3():

    # Scenario tested here:
    # Implementation of the deal solely by EU Member-States
    # They adopt an IIR including their domestic tax deficits
    # And a UTPR including foreign multinationals' domestic tax deficits

    TDResults = TaxDeficitResults(output_folder="~/Desktop", load_online_data=False)

    # for year in [2016, 2017, 2018]:
    for year in [2018]:

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

                alternative_computation, _, _ = calculator.compute_selected_intermediary_scenario_gain(
                    countries_implementing=calculator.eu_27_country_codes,
                    among_countries_implementing=False,
                    minimum_ETR=rate,
                    minimum_breakdown=60,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    exclude_non_implementing_domestic_TDs=False,
                    upgrade_to_2021=False
                )

                alternative_computation_tmp = alternative_computation[
                    ['Parent jurisdiction (alpha-3 code)', 'total']
                ].copy()

                output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=False,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=False,
                    return_bilateral_details=True
                )

                if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                    multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                    multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                        lambda x: {'CHN': multiplier}.get(x, 1)
                    )

                    for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                        output_df[col] *= multiplier

                relevant_columns = []
                aggregation = {'COLLECTING_COUNTRY_NAME': 'first'}

                for location in ['domestic', 'foreign']:
                    for instrument in ['IIR', 'UTPR', 'QDMTT']:

                        col = f'collected_through_{location}_{instrument}'

                        output_df['TAX_DEFICIT' + col] = (
                            output_df['ALLOCATED_TAX_DEFICIT'] * output_df[col]
                        )

                        output_df['TAX_DEFICIT' + col] = output_df['TAX_DEFICIT' + col].astype(float)

                        relevant_columns.append('TAX_DEFICIT' + col)
                        aggregation['TAX_DEFICIT' + col] = 'sum'

                decomposed_df = output_df.groupby('COLLECTING_COUNTRY_CODE').agg(aggregation).reset_index()
                decomposed_df['TAX_DEFICIT_total'] = decomposed_df[relevant_columns].sum(axis=1)

                agg_output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=False,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=False,
                    return_bilateral_details=False
                )

                merged_df = decomposed_df.merge(agg_output_df, how='outer', on='COLLECTING_COUNTRY_CODE')

                merged_df['DIFF'] = merged_df['TAX_DEFICIT_total'] - merged_df['ALLOCATED_TAX_DEFICIT']
                merged_df['RELATIVE_DIFF'] = merged_df['DIFF'] / merged_df['ALLOCATED_TAX_DEFICIT']

                assert merged_df[merged_df['TAX_DEFICIT_total'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
                assert merged_df[merged_df['ALLOCATED_TAX_DEFICIT'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
                assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert (np.abs(merged_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0

                merged_df = merged_df.drop(columns=['ALLOCATED_TAX_DEFICIT', 'COLLECTING_COUNTRY_NAME_y', 'DIFF'])

                temp_df = merged_df.merge(
                    alternative_computation_tmp,
                    how='outer',
                    left_on='COLLECTING_COUNTRY_CODE', right_on='Parent jurisdiction (alpha-3 code)'
                ).drop(columns=['Parent jurisdiction (alpha-3 code)'])

                temp_df['DIFF'] = temp_df['TAX_DEFICIT_total'] - temp_df['total']
                temp_df['RELATIVE_DIFF'] = temp_df['DIFF'] / temp_df['total']

                assert temp_df[temp_df['TAX_DEFICIT_total'].isnull()]['total'].sum() == 0
                assert temp_df[temp_df['total'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert temp_df[temp_df['RELATIVE_DIFF'].isnull()]['total'].sum() == 0
                assert temp_df[temp_df['RELATIVE_DIFF'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert (np.abs(temp_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0


def test_partial_cooperation_scenario_4():

    # Scenario tested here:
    # Implementation of the deal by EU Member-States and a list of adopting jurisdictions
    # They adopt an IIR including their domestic tax deficits
    # And a UTPR including foreign multinationals' domestic tax deficits

    non_EU_implementing_countries = [
        'AUS', 'CYM', 'GGY', 'HKG', 'IMN', 'JPN', 'JEY', 'KOR', 'LIE', 'MYS', 'NZL', 'QAT', 'SGP', 'CHE', 'GBR'
    ]

    TDResults = TaxDeficitResults(output_folder="~/Desktop", load_online_data=False)

    # for year in [2016, 2017, 2018]:
    for year in [2018]:

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

                alternative_computation, _, _ = calculator.compute_selected_intermediary_scenario_gain(
                    countries_implementing=calculator.eu_27_country_codes + non_EU_implementing_countries,
                    among_countries_implementing=False,
                    minimum_ETR=rate,
                    minimum_breakdown=60,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    exclude_non_implementing_domestic_TDs=False,
                    upgrade_to_2021=False
                )

                alternative_computation_tmp = alternative_computation[
                    ['Parent jurisdiction (alpha-3 code)', 'total']
                ].copy()

                output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes + non_EU_implementing_countries,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes + non_EU_implementing_countries,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=False,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=False,
                    return_bilateral_details=True
                )

                if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                    multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                    multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                        lambda x: {'CHN': multiplier}.get(x, 1)
                    )

                    for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                        output_df[col] *= multiplier

                relevant_columns = []
                aggregation = {'COLLECTING_COUNTRY_NAME': 'first'}

                for location in ['domestic', 'foreign']:
                    for instrument in ['IIR', 'UTPR', 'QDMTT']:

                        col = f'collected_through_{location}_{instrument}'

                        output_df['TAX_DEFICIT' + col] = (
                            output_df['ALLOCATED_TAX_DEFICIT'] * output_df[col]
                        )

                        output_df['TAX_DEFICIT' + col] = output_df['TAX_DEFICIT' + col].astype(float)

                        relevant_columns.append('TAX_DEFICIT' + col)
                        aggregation['TAX_DEFICIT' + col] = 'sum'

                decomposed_df = output_df.groupby('COLLECTING_COUNTRY_CODE').agg(aggregation).reset_index()
                decomposed_df['TAX_DEFICIT_total'] = decomposed_df[relevant_columns].sum(axis=1)

                agg_output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes + non_EU_implementing_countries,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes + non_EU_implementing_countries,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=False,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=False,
                    return_bilateral_details=False
                )

                merged_df = decomposed_df.merge(agg_output_df, how='outer', on='COLLECTING_COUNTRY_CODE')

                merged_df['DIFF'] = merged_df['TAX_DEFICIT_total'] - merged_df['ALLOCATED_TAX_DEFICIT']
                merged_df['RELATIVE_DIFF'] = merged_df['DIFF'] / merged_df['ALLOCATED_TAX_DEFICIT']

                assert merged_df[merged_df['TAX_DEFICIT_total'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
                assert merged_df[merged_df['ALLOCATED_TAX_DEFICIT'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
                assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert (np.abs(merged_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0

                merged_df = merged_df.drop(columns=['ALLOCATED_TAX_DEFICIT', 'COLLECTING_COUNTRY_NAME_y', 'DIFF'])

                temp_df = merged_df.merge(
                    alternative_computation_tmp,
                    how='outer',
                    left_on='COLLECTING_COUNTRY_CODE', right_on='Parent jurisdiction (alpha-3 code)'
                ).drop(columns=['Parent jurisdiction (alpha-3 code)'])

                temp_df['DIFF'] = temp_df['TAX_DEFICIT_total'] - temp_df['total']
                temp_df['RELATIVE_DIFF'] = temp_df['DIFF'] / temp_df['total']

                assert temp_df[temp_df['TAX_DEFICIT_total'].isnull()]['total'].sum() == 0
                assert temp_df[temp_df['total'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert temp_df[temp_df['RELATIVE_DIFF'].isnull()]['total'].sum() == 0
                assert temp_df[temp_df['RELATIVE_DIFF'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert (np.abs(temp_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0


def test_partial_cooperation_scenario_stat_rate_cond():

    # Scenario tested here:
    # Implementation of the deal solely by EU Member-States
    # They adopt an IIR including their domestic tax deficits
    # And a UTPR including foreign multinationals' domestic tax deficits

    TDResults = TaxDeficitResults(output_folder="~/Desktop", load_online_data=False)

    # for year in [2016, 2017, 2018]:
    for year in [2018]:

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

                # Not sure why but starting with the new method without applying one of the old ones seems to raise
                # an error when running the tests
                _ = calculator.compute_all_tax_deficits(
                    minimum_ETR=rate, exclude_non_EU_domestic_TDs=True, upgrade_to_2021=False
                )

                output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=True,
                    min_stat_rate_for_UTPR_safe_harbor=0.2,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=True,
                    return_bilateral_details=True
                )

                if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                    multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                    multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                        lambda x: {'CHN': multiplier}.get(x, 1)
                    )

                    for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                        output_df[col] *= multiplier

                relevant_columns = []
                aggregation = {'COLLECTING_COUNTRY_NAME': 'first'}

                for location in ['domestic', 'foreign']:
                    for instrument in ['IIR', 'UTPR', 'QDMTT']:

                        col = f'collected_through_{location}_{instrument}'

                        output_df['TAX_DEFICIT' + col] = (
                            output_df['ALLOCATED_TAX_DEFICIT'] * output_df[col]
                        )

                        output_df['TAX_DEFICIT' + col] = output_df['TAX_DEFICIT' + col].astype(float)

                        relevant_columns.append('TAX_DEFICIT' + col)
                        aggregation['TAX_DEFICIT' + col] = 'sum'

                decomposed_df = output_df.groupby('COLLECTING_COUNTRY_CODE').agg(aggregation).reset_index()
                decomposed_df['TAX_DEFICIT_total'] = decomposed_df[relevant_columns].sum(axis=1)

                agg_output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=True,
                    min_stat_rate_for_UTPR_safe_harbor=0.2,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=True,
                    return_bilateral_details=False
                )

                merged_df = decomposed_df.merge(agg_output_df, how='outer', on='COLLECTING_COUNTRY_CODE')

                merged_df['DIFF'] = merged_df['TAX_DEFICIT_total'] - merged_df['ALLOCATED_TAX_DEFICIT']
                merged_df['RELATIVE_DIFF'] = merged_df['DIFF'] / merged_df['ALLOCATED_TAX_DEFICIT']

                assert merged_df[merged_df['TAX_DEFICIT_total'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
                assert merged_df[merged_df['ALLOCATED_TAX_DEFICIT'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['ALLOCATED_TAX_DEFICIT'].sum() == 0
                assert merged_df[merged_df['RELATIVE_DIFF'].isnull()]['TAX_DEFICIT_total'].sum() == 0
                assert (np.abs(merged_df['RELATIVE_DIFF']) > 0.0000001).sum() == 0

                merged_df = merged_df.drop(columns=['ALLOCATED_TAX_DEFICIT', 'COLLECTING_COUNTRY_NAME_y', 'DIFF'])

                output_df = calculator.allocate_bilateral_tax_deficits(
                    minimum_rate=rate,
                    QDMTT_incl_domestic=[],
                    QDMTT_excl_domestic=[],
                    IIR_incl_domestic=calculator.eu_27_country_codes,
                    IIR_excl_domestic=[],
                    UTPR_incl_domestic=calculator.eu_27_country_codes,
                    UTPR_excl_domestic=[],
                    stat_rate_condition_for_UTPR=False,
                    weight_UPR=weight_UPR,
                    weight_assets=weight_assets,
                    weight_employees=weight_employees,
                    minimum_breakdown=60,
                    among_countries_implementing=True,
                    return_bilateral_details=True
                )

                if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                    multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                    multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                        lambda x: {'CHN': multiplier}.get(x, 1)
                    )

                    for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                        output_df[col] *= multiplier

                relevant_columns = []
                aggregation = {'COLLECTING_COUNTRY_NAME': 'first'}

                for location in ['domestic', 'foreign']:
                    for instrument in ['IIR', 'UTPR', 'QDMTT']:

                        col = f'collected_through_{location}_{instrument}'

                        output_df['TAX_DEFICIT' + col] = (
                            output_df['ALLOCATED_TAX_DEFICIT'] * output_df[col]
                        )

                        output_df['TAX_DEFICIT' + col] = output_df['TAX_DEFICIT' + col].astype(float)

                        relevant_columns.append('TAX_DEFICIT' + col)
                        aggregation['TAX_DEFICIT' + col] = 'sum'

                decomposed_df_bis = output_df.groupby('COLLECTING_COUNTRY_CODE').agg(aggregation).reset_index()
                decomposed_df_bis['TAX_DEFICIT_total'] = decomposed_df[relevant_columns].sum(axis=1)

                merged_df = decomposed_df.merge(decomposed_df_bis, how='outer', on='COLLECTING_COUNTRY_CODE')

                assert merged_df[merged_df['COLLECTING_COUNTRY_NAME_x'].isnull()]['TAX_DEFICIT_total_y'].sum() == 0
                assert merged_df[merged_df['COLLECTING_COUNTRY_NAME_y'].isnull()]['TAX_DEFICIT_total_x'].sum() == 0

                merged_df = merged_df[
                    np.logical_and(
                        ~merged_df['COLLECTING_COUNTRY_NAME_x'].isnull(),
                        ~merged_df['COLLECTING_COUNTRY_NAME_y'].isnull()
                    )
                ].copy()

                for col in [
                    'TAX_DEFICITcollected_through_domestic_IIR', 'TAX_DEFICITcollected_through_domestic_QDMTT',
                    'TAX_DEFICITcollected_through_foreign_IIR', 'TAX_DEFICITcollected_through_foreign_QDMTT',
                ]:
                    assert (merged_df[col + '_x'] != merged_df[col + '_y']).sum() == 0
