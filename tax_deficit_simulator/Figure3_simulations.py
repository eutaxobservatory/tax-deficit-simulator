
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
            "/Users/Paul-Emmanuel/Desktop/EU Tax Observatory/4. Own Work/0. Tax Deficit/2018_update/outputs_Fig3"
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
    # --- Partial cooperation scenario ---------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    ####################################################################################################################

    print("###########################################################################################################")
    print('Partial cooperation scenario')
    print("###########################################################################################################")

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

        if safe_harbor_suffix == 'noStatRateCond':

            calculators = [
                calculator_noCO, calculator_noCO,
                calculator_firstyearCO, calculator_firstyearCO, calculator_firstyearCO
            ]
            CO_tabs = [
                'noCO', 'noCO',
                'firstYearCO', 'firstYearCO', 'firstYearCO'
            ]

            rates = [0.2, 0.15, 0.15, 0.15, 0.13]
            rate_tabs = ['20%', '15%', '15%', '15%', '13%']

            increments = [0, 0, 0, 0.02, 0]
            increment_tabs = ['+0ppt', '+0ppt', '+0ppt', '+2ppt', '+0ppt']

        elif safe_harbor_suffix == '20statRateCond':

            calculators = [calculator_firstyearCO, calculator_firstyearCO, calculator_firstyearCO]
            CO_tabs = ['firstYearCO', 'firstYearCO', 'firstYearCO']

            rates = [0.15, 0.15, 0.13]
            rate_tabs = ['15%', '15%', '13%']

            increments = [0, 0.02, 0]
            increment_tabs = ['+0ppt', '+2ppt', '+0ppt']

        else:

            calculators = [calculator_firstyearCO]
            CO_tabs = ['firstYearCO']

            rates = [0.15]
            rate_tabs = ['15%']

            increments = [0]
            increment_tabs = ['+0ppt']

        for i, (
            calculator, CO_tab, rate, rate_tab, increment, increment_tab
        ) in enumerate(zip(calculators, CO_tabs, rates, rate_tabs, increments, increment_tabs)):

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
                return_bilateral_details=True,
                ETR_increment=increment,
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
                return_bilateral_details=False,
                ETR_increment=increment,
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
            if i == 0:

                with pd.ExcelWriter(
                    path=os.path.join(TDResults.output_folder, f'partialCoop_EUandOthers_{safe_harbor_suffix}.xlsx'),
                    engine='openpyxl',
                    mode='w'
                ) as writer:
                    merged_df.to_excel(writer, index=False, sheet_name=f"{CO_tab} - {rate_tab} - {increment_tab}")

            else:

                with pd.ExcelWriter(
                    path=os.path.join(TDResults.output_folder, f'partialCoop_EUandOthers_{safe_harbor_suffix}.xlsx'),
                    engine='openpyxl',
                    mode='a'
                ) as writer:
                    merged_df.to_excel(writer, index=False, sheet_name=f"{CO_tab} - {rate_tab} - {increment_tab}")
