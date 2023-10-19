
# General imports

import os

import numpy as np
import pandas as pd

# Project-specific imports

from calculator import TaxDeficitCalculator
from results import TaxDeficitResults

if __name__ == '__main__':

    ####################################################################################################################
    # ------------------------------------------------------------------------------------------------------------------
    # --- Preparing computations ---------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    ####################################################################################################################

    print("###########################################################################################################")
    print('Preparing calculators and data')
    print("###########################################################################################################")

    calculator_noCO = TaxDeficitCalculator(
        year=2018,
        alternative_imputation=True,
        non_haven_TD_imputation_selection='EU',
        sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
        China_treatment_2018="2017_CbCR",
        use_adjusted_profits=True,
        average_ETRs=True,
        years_for_avg_ETRs=[2016, 2017, 2018],
        carve_outs=False,
        de_minimis_exclusion=True,
        add_AUT_AUT_row=True,
        extended_dividends_adjustment=False,
        behavioral_responses=False,
        fetch_data_online=False
    )
    calculator_noCO.load_clean_data()

    calculator_firstyearCO = TaxDeficitCalculator(
        year=2018,
        alternative_imputation=True,
        non_haven_TD_imputation_selection='EU',
        sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
        China_treatment_2018="2017_CbCR",
        use_adjusted_profits=True,
        average_ETRs=True,
        years_for_avg_ETRs=[2016, 2017, 2018],
        carve_outs=True,
        carve_out_rate_assets=0.08, carve_out_rate_payroll=0.1,
        depreciation_only=False, exclude_inventories=False, payroll_premium=20,
        ex_post_ETRs=False,
        de_minimis_exclusion=True,
        add_AUT_AUT_row=True,
        extended_dividends_adjustment=False,
        behavioral_responses=False,
        fetch_data_online=False
    )
    calculator_firstyearCO.load_clean_data()

    calculator_longtermCO = TaxDeficitCalculator(
        year=2018,
        alternative_imputation=True,
        non_haven_TD_imputation_selection='EU',
        sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
        China_treatment_2018="2017_CbCR",
        use_adjusted_profits=True,
        average_ETRs=True,
        years_for_avg_ETRs=[2016, 2017, 2018],
        carve_outs=True,
        carve_out_rate_assets=0.05, carve_out_rate_payroll=0.05,
        depreciation_only=False, exclude_inventories=False, payroll_premium=20,
        ex_post_ETRs=False,
        de_minimis_exclusion=True,
        add_AUT_AUT_row=True,
        extended_dividends_adjustment=False,
        behavioral_responses=False,
        fetch_data_online=False
    )
    calculator_longtermCO.load_clean_data()

    # Locating the output folder, additional utils

    TDResults = TaxDeficitResults(
        output_folder=(
            "/Users/Paul-Emmanuel/Desktop/EU Tax Observatory/4. Own Work/0. Tax Deficit/2018_update/new_outputs"
        ),
        load_online_data=False
    )
    TDResults.output_folder

    # List of countries assumed to implement the deal in partial cooperation scenarios outside of the EU

    non_EU_implementing_countries = [
        'AUS', 'CYM', 'GGY', 'HKG', 'IMN', 'JPN', 'JEY',
        'KOR', 'LIE', 'MYS', 'NZL', 'QAT', 'SGP', 'CHE', 'GBR'
    ]

    ####################################################################################################################
    # ------------------------------------------------------------------------------------------------------------------
    # --- Headquarter scenario -----------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    ####################################################################################################################

    print("###########################################################################################################")
    print('Headquarter scenario')
    print("###########################################################################################################")

    for calculator, CO_suffix in zip(
        [calculator_noCO, calculator_firstyearCO, calculator_longtermCO],
        ['noCO', 'firstYearCO', 'longTermCO']
    ):

        if CO_suffix == 'longTermCO':
            rates = [0.15]

        elif CO_suffix == 'firstYearCO':
            rates = [0.15, 0.13]

        else:
            rates = [0.15, 0.2, 0.25, 0.3, 0.13]

        for rate in rates:

            output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_incl_domestic=list(TDResults.eu_27_country_codes),
                IIR_excl_domestic=list(TDResults.all_countries_but_EU),
                UTPR_incl_domestic=[],
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=False,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=True
            )

            # Upgrading observations with China as a parent country to 2018 USD
            if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                    lambda x: {'CHN': multiplier}.get(x, 1)
                )

                for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                    output_df[col] *= multiplier

            # Computing each country's total revenue gains
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

            # Computations doing the aggregation
            agg_output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_incl_domestic=list(TDResults.eu_27_country_codes),
                IIR_excl_domestic=list(TDResults.all_countries_but_EU),
                UTPR_incl_domestic=[],
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=False,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=False
            )

            # Checking compatibility
            merged_df = decomposed_df.merge(agg_output_df, how='outer', on='COLLECTING_COUNTRY_CODE')

            merged_df['DIFF'] = merged_df['TAX_DEFICIT_total'] - merged_df['ALLOCATED_TAX_DEFICIT']

            if len(merged_df[np.abs(merged_df['DIFF']) > 0.0001]) > 0:
                raise Exception(f"STOP - HQ scenario - {int(rate * 100)}% - {CO_suffix} - Match with agg. results.")

            merged_df = merged_df.drop(columns=['ALLOCATED_TAX_DEFICIT', 'COLLECTING_COUNTRY_NAME_y', 'DIFF'])

            # Alternative method ("old" one)
            alternative_computation = calculator.compute_all_tax_deficits(minimum_ETR=rate, upgrade_to_2021=False)

            # Checking compatibility
            alternative_computation_tmp = alternative_computation[
                ['Parent jurisdiction (alpha-3 code)', 'tax_deficit']
            ].copy()

            temp_df = merged_df.merge(
                alternative_computation_tmp,
                how='outer',
                left_on='COLLECTING_COUNTRY_CODE', right_on='Parent jurisdiction (alpha-3 code)'
            ).drop(columns=['Parent jurisdiction (alpha-3 code)'])

            temp_df['DIFF'] = temp_df['TAX_DEFICIT_total'] - temp_df['tax_deficit']

            temp_df[np.abs(temp_df['DIFF']) > 0.00001]

            if len(temp_df[np.abs(temp_df['DIFF']) > 0.0001]) > 0:
                raise Exception(f"STOP - HQ scenario - {int(rate * 100)}% - {CO_suffix} - Comparison with old method.")

            merged_df['TAX_DEFICIT_total'].sum()

            # Saving results
            if rate == 0.15:

                with pd.ExcelWriter(
                    path=os.path.join(TDResults.output_folder, f'HQscenario_{CO_suffix}.xlsx'),
                    engine='openpyxl',
                    mode='w'
                ) as writer:
                    merged_df.to_excel(writer, sheet_name='15%', index=False)

            else:

                with pd.ExcelWriter(
                    path=os.path.join(TDResults.output_folder, f'HQscenario_{CO_suffix}.xlsx'),
                    engine='openpyxl',
                    mode='a'
                ) as writer:
                    merged_df.to_excel(writer, sheet_name=f'{int(rate * 100)}%', index=False)

        # 15% with a 2% increment
        if CO_suffix != 'longTermCO':

            output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=0.15,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_incl_domestic=list(TDResults.eu_27_country_codes),
                IIR_excl_domestic=list(TDResults.all_countries_but_EU),
                UTPR_incl_domestic=[],
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=False,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=True,
                ETR_increment=0.02
            )

            # Upgrading observations with China as a parent country to 2018 USD.
            if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                    lambda x: {'CHN': multiplier}.get(x, 1)
                )

                for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                    output_df[col] *= multiplier

            # Computing each country's total revenue gains
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

            # Computations doing the aggregation
            agg_output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=0.15,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_incl_domestic=list(TDResults.eu_27_country_codes),
                IIR_excl_domestic=list(TDResults.all_countries_but_EU),
                UTPR_incl_domestic=[],
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=False,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=False,
                ETR_increment=0.02
            )

            # Checking compatibility
            merged_df = decomposed_df.merge(agg_output_df, how='outer', on='COLLECTING_COUNTRY_CODE')

            merged_df['DIFF'] = merged_df['TAX_DEFICIT_total'] - merged_df['ALLOCATED_TAX_DEFICIT']

            if len(merged_df[np.abs(merged_df['DIFF']) > 0.0001]) > 0:
                raise Exception(f"STOP - HQ scenario - 15% with 2% increment - {CO_suffix} - Match with agg. results.")

            merged_df = merged_df.drop(columns=['ALLOCATED_TAX_DEFICIT', 'COLLECTING_COUNTRY_NAME_y', 'DIFF'])

            merged_df['TAX_DEFICIT_total'].sum()

            # Saving results
            with pd.ExcelWriter(
                path=os.path.join(TDResults.output_folder, f'HQscenario_{CO_suffix}.xlsx'),
                engine='openpyxl',
                mode='a'
            ) as writer:
                merged_df.to_excel(writer, sheet_name='15% with increment', index=False)

    ####################################################################################################################
    # ------------------------------------------------------------------------------------------------------------------
    # --- QDMTT scenario -----------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    ####################################################################################################################

    print("###########################################################################################################")
    print('QDMTT scenario')
    print("###########################################################################################################")

    for calculator, CO_suffix in zip(
        [calculator_noCO, calculator_firstyearCO, calculator_longtermCO],
        ['noCO', 'firstYearCO', 'longTermCO']
    ):

        if CO_suffix == 'longTermCO':
            rates = [0.15]

        elif CO_suffix == 'firstYearCO':
            rates = [0.15]

        else:
            rates = [0.15, 0.2, 0.25, 0.3]

        for rate in rates:

            output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=list(TDResults.eu_27_country_codes),
                QDMTT_excl_domestic=list(TDResults.all_countries_but_EU),
                IIR_incl_domestic=[],
                IIR_excl_domestic=[],
                UTPR_incl_domestic=[],
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=False,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=True
            )

            output_df['ALLOCATED_TAX_DEFICIT'].sum()

            # Upgrading observations with China as a parent country to 2018 USD
            if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                    lambda x: {'CHN': multiplier}.get(x, 1)
                )

                for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                    output_df[col] *= multiplier

            # Computing each country's total revenue gains
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

            # Computations doing the aggregation
            agg_output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=list(TDResults.eu_27_country_codes),
                QDMTT_excl_domestic=list(TDResults.all_countries_but_EU),
                IIR_incl_domestic=[],
                IIR_excl_domestic=[],
                UTPR_incl_domestic=[],
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=False,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=False
            )

            # Checking compatibility
            merged_df = decomposed_df.merge(agg_output_df, how='outer', on='COLLECTING_COUNTRY_CODE')

            merged_df['DIFF'] = merged_df['TAX_DEFICIT_total'] - merged_df['ALLOCATED_TAX_DEFICIT']

            if len(merged_df[np.abs(merged_df['DIFF']) > 0.0001]) > 0:
                raise Exception("STOP.")

            merged_df = merged_df.drop(columns=['ALLOCATED_TAX_DEFICIT', 'COLLECTING_COUNTRY_NAME_y', 'DIFF'])

            # Controlling the new results vs. the "old" methodology

            # We load again the fully disaggregated computations
            output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=list(TDResults.eu_27_country_codes),
                QDMTT_excl_domestic=list(TDResults.all_countries_but_EU),
                IIR_incl_domestic=[],
                IIR_excl_domestic=[],
                UTPR_incl_domestic=[],
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=False,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=True
            )

            # Upgrading the observations with China as parent to 2018 (if relevant)
            if calculator.year == 2018 and calculator.China_treatment_2018 == "2017_CbCR":

                multiplier = output_df['PARENT_COUNTRY_CODE'] == 'CHN'
                multiplier *= calculator.USD_to_EUR_2017 * calculator.multiplier_2017_2021
                multiplier = multiplier.map(
                    lambda x: calculator.USD_to_EUR * calculator.multiplier_2021 if x == 0 else x
                )

            else:

                multiplier = calculator.USD_to_EUR * calculator.multiplier_2021

            output_df['ALLOCATED_TAX_DEFICIT'] *= multiplier

            new_df = output_df.groupby(
                ['COLLECTING_COUNTRY_CODE']
            ).sum()['ALLOCATED_TAX_DEFICIT'].reset_index()

            # Alternative computation using the "old" methodology
            alternative_computation = calculator.compute_qdmtt_revenue_gains(minimum_ETR=rate)

            # Comparison
            alternative_computation_tmp = alternative_computation[['PARTNER_COUNTRY_CODE', 'TAX_DEFICIT']].copy()

            temp_df = new_df.merge(
                alternative_computation_tmp,
                how='outer',
                left_on='COLLECTING_COUNTRY_CODE', right_on='PARTNER_COUNTRY_CODE'
            ).drop(columns=['PARTNER_COUNTRY_CODE'])

            temp_df['DIFF'] = temp_df['ALLOCATED_TAX_DEFICIT'] - temp_df['TAX_DEFICIT']

            if len(temp_df[np.abs(temp_df['DIFF']) > 0.0001]) > 0:
                raise Exception(f"STOP - QDMTT - {int(rate * 100)}% - {CO_suffix} - Comparison with previous method.")

            # Saving the results
            if rate == 0.15:

                with pd.ExcelWriter(
                    path=os.path.join(TDResults.output_folder, f'QDMTTscenario_{CO_suffix}.xlsx'),
                    engine='openpyxl',
                    mode='w'
                ) as writer:
                    merged_df.to_excel(writer, index=False, sheet_name="15%")

            else:

                with pd.ExcelWriter(
                    path=os.path.join(TDResults.output_folder, f'QDMTTscenario_{CO_suffix}.xlsx'),
                    engine='openpyxl',
                    mode='a'
                ) as writer:
                    merged_df.to_excel(writer, index=False, sheet_name=f"{int(rate * 100)}%")

    ####################################################################################################################
    # ------------------------------------------------------------------------------------------------------------------
    # --- Partial cooperation scenario ---------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    ####################################################################################################################

    print("###########################################################################################################")
    print('Partial cooperation scenario')
    print("###########################################################################################################")

    for calculator, CO_tab in zip(
        [calculator_noCO, calculator_firstyearCO, calculator_longtermCO],
        ['noCO', 'firstYearCO', 'longTermCO']
    ):

        rate = 0.15

        for (
            stat_rate_condition_for_UTPR,
            min_stat_rate_for_UTPR_safe_harbor,
            utpr_safe_harbor_incl_foreign_profits,
            safe_harbor_suffix
        ) in zip(
            [False, True, True, True],
            [0.2, 0.2, 0.2, 0.2 / 100],
            [False, False, True, True],
            ['noStatRateCond', '20statRateCond', '20statRateCond_withForeign', '20statRateCond_reproducing']
        ):

            # --- EU only ----------------------------------------------------------------------------------------------
            ############################################################################################################

            # Computations maintaining the trilateral split
            output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_incl_domestic=calculator.eu_27_country_codes,
                IIR_excl_domestic=[],
                UTPR_incl_domestic=calculator.eu_27_country_codes,
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=stat_rate_condition_for_UTPR,
                min_stat_rate_for_UTPR_safe_harbor=min_stat_rate_for_UTPR_safe_harbor,
                utpr_safe_harbor_incl_foreign_profits=utpr_safe_harbor_incl_foreign_profits,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=True
            )

            # Upgrading observations with China as a parent country to 2018 USD
            if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                    lambda x: {'CHN': multiplier}.get(x, 1)
                )

                for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                    output_df[col] *= multiplier

            # Computing each country's total revenue gains
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

            # Computations doing the aggregation
            agg_output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_incl_domestic=calculator.eu_27_country_codes,
                IIR_excl_domestic=[],
                UTPR_incl_domestic=calculator.eu_27_country_codes,
                UTPR_excl_domestic=[],
                stat_rate_condition_for_UTPR=stat_rate_condition_for_UTPR,
                min_stat_rate_for_UTPR_safe_harbor=min_stat_rate_for_UTPR_safe_harbor,
                utpr_safe_harbor_incl_foreign_profits=utpr_safe_harbor_incl_foreign_profits,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=False
            )

            # Checking compatibility
            merged_df = decomposed_df.merge(agg_output_df, how='outer', on='COLLECTING_COUNTRY_CODE')

            merged_df['DIFF'] = merged_df['TAX_DEFICIT_total'] - merged_df['ALLOCATED_TAX_DEFICIT']

            if len(merged_df[np.abs(merged_df['DIFF']) > 0.0001]) > 0:
                raise Exception(
                    f"STOP - EU partial cooperation - {CO_tab} - {safe_harbor_suffix} - Match with aggregated results."
                )

            merged_df = merged_df.drop(columns=['ALLOCATED_TAX_DEFICIT', 'COLLECTING_COUNTRY_NAME_y', 'DIFF'])

            # When we impose no condition on statutory tax rates, we can check with the extension of the "old" method
            if not stat_rate_condition_for_UTPR:

                (
                    alternative_computation, details_directly_allocated, details_imputed
                ) = calculator.compute_selected_intermediary_scenario_gain(
                    countries_implementing=calculator.eu_27_country_codes,
                    among_countries_implementing=True,
                    minimum_ETR=rate,
                    minimum_breakdown=60,
                    weight_UPR=1,
                    weight_employees=0,
                    weight_assets=0,
                    exclude_non_implementing_domestic_TDs=False,
                    upgrade_to_2021=False
                )

                alternative_computation_tmp = alternative_computation[
                    ['Parent jurisdiction (alpha-3 code)', 'total']
                ].copy()

                temp_df = merged_df.merge(
                    alternative_computation_tmp,
                    how='outer',
                    left_on='COLLECTING_COUNTRY_CODE', right_on='Parent jurisdiction (alpha-3 code)'
                ).drop(columns=['Parent jurisdiction (alpha-3 code)'])

                temp_df['DIFF'] = temp_df['TAX_DEFICIT_total'] - temp_df['total']

                temp_df[np.abs(temp_df['DIFF']) > 0.00001]

                if len(temp_df[np.abs(temp_df['DIFF']) > 0.0001]) > 0:
                    raise Exception(
                        f"STOP - EU partial cooperation - {CO_tab} - {safe_harbor_suffix} - Comparison with old method."
                    )

            # Saving results
            if CO_tab == 'noCO':

                with pd.ExcelWriter(
                    path=os.path.join(TDResults.output_folder, f'partialCoop_EUOnly_{safe_harbor_suffix}.xlsx'),
                    engine='openpyxl',
                    mode='w'
                ) as writer:
                    merged_df.to_excel(writer, index=False, sheet_name=CO_tab)

            else:

                with pd.ExcelWriter(
                    path=os.path.join(TDResults.output_folder, f'partialCoop_EUOnly_{safe_harbor_suffix}.xlsx'),
                    engine='openpyxl',
                    mode='a'
                ) as writer:
                    merged_df.to_excel(writer, index=False, sheet_name=CO_tab)

            # --- EU and other jurisdictions ---------------------------------------------------------------------------
            ############################################################################################################

            # Computations maintaining the trilateral split
            output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_incl_domestic=calculator.eu_27_country_codes,
                IIR_excl_domestic=non_EU_implementing_countries,
                UTPR_incl_domestic=calculator.eu_27_country_codes,
                UTPR_excl_domestic=non_EU_implementing_countries,
                stat_rate_condition_for_UTPR=stat_rate_condition_for_UTPR,
                min_stat_rate_for_UTPR_safe_harbor=min_stat_rate_for_UTPR_safe_harbor,
                utpr_safe_harbor_incl_foreign_profits=utpr_safe_harbor_incl_foreign_profits,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=True
            )

            # Upgrading observations with China as a parent country to 2018 USD
            if calculator.year == 2018 and calculator.China_treatment_2018 == '2017_CbCR':

                multiplier = calculator.growth_rates.set_index('CountryGroupName').loc['World', 'uprusd1817']

                multiplier = output_df['PARENT_COUNTRY_CODE'].map(
                    lambda x: {'CHN': multiplier}.get(x, 1)
                )

                for col in ['PROFITS_BEFORE_TAX_POST_CO', 'TAX_DEFICIT', 'ALLOCATED_TAX_DEFICIT']:
                    output_df[col] *= multiplier

            # Computing each country's total revenue gains
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

            # Computations doing the aggregation
            agg_output_df = calculator.allocate_bilateral_tax_deficits(
                minimum_rate=rate,
                QDMTT_incl_domestic=[],
                QDMTT_excl_domestic=[],
                IIR_incl_domestic=calculator.eu_27_country_codes,
                IIR_excl_domestic=non_EU_implementing_countries,
                UTPR_incl_domestic=calculator.eu_27_country_codes,
                UTPR_excl_domestic=non_EU_implementing_countries,
                stat_rate_condition_for_UTPR=stat_rate_condition_for_UTPR,
                min_stat_rate_for_UTPR_safe_harbor=min_stat_rate_for_UTPR_safe_harbor,
                utpr_safe_harbor_incl_foreign_profits=utpr_safe_harbor_incl_foreign_profits,
                weight_UPR=1,
                weight_assets=0,
                weight_employees=0,
                minimum_breakdown=60,
                among_countries_implementing=True,
                return_bilateral_details=False
            )

            # Checking compatibility
            merged_df = decomposed_df.merge(agg_output_df, how='outer', on='COLLECTING_COUNTRY_CODE')

            merged_df['DIFF'] = merged_df['TAX_DEFICIT_total'] - merged_df['ALLOCATED_TAX_DEFICIT']

            if len(merged_df[np.abs(merged_df['DIFF']) > 0.0001]) > 0:
                raise Exception(
                    f"STOP - EU and others partial coop. - {CO_tab} - {safe_harbor_suffix} - Match with agg/ results."
                )

            merged_df = merged_df.drop(columns=['ALLOCATED_TAX_DEFICIT', 'COLLECTING_COUNTRY_NAME_y', 'DIFF'])

            # Saving results
            if CO_tab == 'noCO':

                with pd.ExcelWriter(
                    path=os.path.join(TDResults.output_folder, f'partialCoop_EUandOthers_{safe_harbor_suffix}.xlsx'),
                    engine='openpyxl',
                    mode='w'
                ) as writer:
                    merged_df.to_excel(writer, index=False, sheet_name=CO_tab)

            else:

                with pd.ExcelWriter(
                    path=os.path.join(TDResults.output_folder, f'partialCoop_EUandOthers_{safe_harbor_suffix}.xlsx'),
                    engine='openpyxl',
                    mode='a'
                ) as writer:
                    merged_df.to_excel(writer, index=False, sheet_name=CO_tab)

    ####################################################################################################################
    # ------------------------------------------------------------------------------------------------------------------
    # --- Unilateral scenario ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    ####################################################################################################################

    print("###########################################################################################################")
    print('Unilateral scenario')
    print("###########################################################################################################")

    # Using the extension of the benchmark methodology for the unilateral implementation scenario
    results_df, _, _, _ = calculator_noCO.compute_unilateral_scenario_revenue_gains(
        full_own_tax_deficit=True,
        minimum_ETR=0.15,
        minimum_breakdown=60,
        weight_UPR=1,
        weight_assets=0,
        weight_employees=0,
        exclude_domestic_TDs=False,
        upgrade_to_2021=False
    )

    FRA_result_1 = results_df[
        results_df['Parent jurisdiction (alpha-3 code)'] == 'FRA'
    ].reset_index(drop=True).loc[0, 'total']

    # Using the new approach
    output_df = calculator_noCO.allocate_bilateral_tax_deficits(
        minimum_rate=0.15,
        QDMTT_incl_domestic=[],
        QDMTT_excl_domestic=[],
        IIR_incl_domestic=['FRA'],
        IIR_excl_domestic=[],
        UTPR_incl_domestic=['FRA'],
        UTPR_excl_domestic=[],
        stat_rate_condition_for_UTPR=False,
        weight_UPR=1,
        weight_assets=0,
        weight_employees=0,
        minimum_breakdown=60,
        among_countries_implementing=False,
        return_bilateral_details=False
    )

    FRA_results_2 = output_df[
        output_df['ALLOCATED_TAX_DEFICIT'] > 0
    ].reset_index(drop=True).loc[0, 'ALLOCATED_TAX_DEFICIT']

    # Using the extension of the benchmark methodology for partial cooperation scenarios
    (
        alternative_computation, details_directly_allocated, details_imputed
    ) = calculator_noCO.compute_selected_intermediary_scenario_gain(
        countries_implementing=['FRA'],
        among_countries_implementing=False,
        minimum_ETR=0.15,
        minimum_breakdown=60,
        weight_UPR=1,
        weight_employees=0,
        weight_assets=0,
        exclude_non_implementing_domestic_TDs=False,
        upgrade_to_2021=False
    )

    FRA_result_3 = alternative_computation[
        alternative_computation['Parent jurisdiction (alpha-3 code)'] == 'FRA'
    ].reset_index(drop=True).loc[0, 'total']

    # Checking compatibility of the different results
    diff_1 = np.abs(FRA_result_1 - FRA_results_2)
    diff_2 = np.abs(FRA_result_1 - FRA_results_3)
    diff_3 = np.abs(FRA_result_2 - FRA_results_3)

    if diff_1 > 0.0001 or diff_2 > 0.0001 or diff_3 > 0.0001:
        raise Exception(
            "STOP - Unilateral scenario - Comparison of the French revenue gains from various methods."
        )

    # Saving results
    with pd.ExcelWriter(
        path=os.path.join(TDResults.output_folder, 'unilateralScenario.xlsx'),
        engine='xlsxwriter'
    ) as writer:
        results_df.to_excel(writer, index=False)

    ####################################################################################################################
    # ------------------------------------------------------------------------------------------------------------------
    # --- Full sales apportionment -------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    ####################################################################################################################

    print("###########################################################################################################")
    print('Full sales apportionment scenario')
    print("###########################################################################################################")

    # Using the extension of the benchmark methodology for the unilateral implementation scenario
    (
        results_df,
        details_directly_allocated,
        details_imputed_foreign,
        details_imputed_domestic
    ) = calculator_noCO.compute_unilateral_scenario_revenue_gains(
        full_own_tax_deficit=False,
        minimum_ETR=0.15,
        minimum_breakdown=60,
        weight_UPR=1,
        weight_assets=0,
        weight_employees=0,
        exclude_domestic_TDs=False,
        upgrade_to_2021=False
    )

    agg_revenue_gains_1 = results_df['total'].sum() / 10**9

    # Simulating the headquarter scenario with full collection of the domestic tax deficits
    # (To compare aggregated revenue gains)
    tax_deficits = calculator_noCO.compute_all_tax_deficits(
        minimum_ETR=0.15, upgrade_to_2021=False, exclude_non_EU_domestic_TDs=False
    )

    agg_revenue_gains_2 = tax_deficits['tax_deficit'].sum() / 10**9

    # Simulating the full apportionment with the new methodology
    agg_output_df = calculator_noCO.allocate_bilateral_tax_deficits(
        minimum_rate=0.15,
        QDMTT_incl_domestic=[],
        QDMTT_excl_domestic=[],
        IIR_incl_domestic=[],
        IIR_excl_domestic=[],
        UTPR_incl_domestic=TDResults.all_countries,
        UTPR_excl_domestic=[],
        stat_rate_condition_for_UTPR=False,
        weight_UPR=1,
        weight_assets=0,
        weight_employees=0,
        minimum_breakdown=60,
        among_countries_implementing=False,
        return_bilateral_details=False
    )

    agg_revenue_gains_3 = agg_output_df['ALLOCATED_TAX_DEFICIT'].sum() / 10**9

    # Comparing aggregate revenue gains
    diff_1 = np.abs(agg_revenue_gains_1 - agg_revenue_gains_2)
    diff_2 = np.abs(agg_revenue_gains_1 - agg_revenue_gains_3)
    diff_3 = np.abs(agg_revenue_gains_2 - agg_revenue_gains_3)

    if diff_1 > 0.0001 or diff_2 > 0.0001 or diff_3 > 0.0001:
        raise Exception(
            "STOP - Full apportionment scenario - Comparison of aggregate revenue gains from various methods."
        )

    # Comparing the two exhaustive full apportionment simulations
    merged_df = agg_output_df.merge(
        results_df[['Parent jurisdiction (alpha-3 code)', 'total']],
        how='outer',
        left_on='COLLECTING_COUNTRY_CODE', right_on='Parent jurisdiction (alpha-3 code)'
    )

    merged_df['DIFF'] = merged_df['ALLOCATED_TAX_DEFICIT'] - merged_df['total']

    merged_df['DIFF_ABS'] = np.abs(merged_df['DIFF'])

    if len(merged_df[merged_df['DIFF_ABS'] > 0.0001]) > 0:
        raise Exception("STOP - Full apportionment scenario - Comparison of all revenue gain estimates.")

    # Saving results
    with pd.ExcelWriter(
        path=os.path.join(TDResults.output_folder, 'fullSalesApportionment.xlsx'),
        engine='xlsxwriter'
    ) as writer:
        results_df.to_excel(writer, index=False)
