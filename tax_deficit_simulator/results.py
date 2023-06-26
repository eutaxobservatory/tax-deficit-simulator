import numpy as np
import pandas as pd

import os

from tax_deficit_simulator.calculator import TaxDeficitCalculator


class TaxDeficitResults:

    def __init__(self, output_folder):

        self.output_folder = output_folder

    def benchmark_IIR_with_different_carve_outs(self, year):

        # --- Loading required data

        if year == 2016:

            calculator_noCO = TaxDeficitCalculator(
                year=2016,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
                carve_outs=False,
                de_minimis_exclusion=True,
                extended_dividends_adjustment=False,
                behavioral_responses=False,
                fetch_data_online=False
            )
            calculator_noCO.load_clean_data()

            calculator_firstyearCO = TaxDeficitCalculator(
                year=2016,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
                carve_outs=True,
                carve_out_rate_assets=0.08, carve_out_rate_payroll=0.1,
                depreciation_only=False, exclude_inventories=False, payroll_premium=20,
                ex_post_ETRs=False,
                de_minimis_exclusion=True,
                extended_dividends_adjustment=False,
                behavioral_responses=False,
                fetch_data_online=False
            )
            calculator_firstyearCO.load_clean_data()

            calculator_longtermCO = TaxDeficitCalculator(
                year=2016,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
                carve_outs=True,
                carve_out_rate_assets=0.05, carve_out_rate_payroll=0.05,
                depreciation_only=False, exclude_inventories=False, payroll_premium=20,
                ex_post_ETRs=False,
                de_minimis_exclusion=True,
                extended_dividends_adjustment=False,
                behavioral_responses=False,
                fetch_data_online=False
            )
            calculator_longtermCO.load_clean_data()

        elif year == 2017:

            calculator_noCO = TaxDeficitCalculator(
                year=2017,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
                carve_outs=False,
                de_minimis_exclusion=True,
                add_AUT_AUT_row=True,
                extended_dividends_adjustment=False,
                behavioral_responses=False,
                fetch_data_online=False
            )
            calculator_noCO.load_clean_data()

            calculator_firstyearCO = TaxDeficitCalculator(
                year=2017,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
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
                year=2017,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
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

        elif year == 2018:

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

        else:
            raise Exception("Three years are available for now: 2016, 2017, and 2018.")

        # --- Building the table

        CbC_Countries = list(calculator_2017_noCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits without carve-outs
        tds = calculator_noCO.compute_all_tax_deficits(minimum_ETR=0.15)

        extract1 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit'
            ]
        ].copy()

        extract1['tax_deficit'] /= 10**9
        extract1 = extract1.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Country',
                'tax_deficit': 'No Carve-Out',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with first-year carve-outs
        tds = calculator_firstyearCO.compute_all_tax_deficits(minimum_ETR=0.15)

        extract2 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit'
            ]
        ].copy()

        extract2['tax_deficit'] /= 10**9
        extract2 = extract2.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Country',
                'tax_deficit': 'Year 1',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        tds = calculator_longtermCO.compute_all_tax_deficits(minimum_ETR=0.15)

        extract3 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit'
            ]
        ].copy()

        extract3['tax_deficit'] /= 10**9
        extract3 = extract3.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Country',
                'tax_deficit': 'After Year 10',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the three tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Parent Country', 'CODE']
        ).merge(
            extract3, how='left', on=['Parent Country', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_2017_noCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_2017_noCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Parent Country"] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Parent Country"] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Parent Country"] = "Total for CbC reporting"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Parent Country"] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Parent Country"] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Parent Country"] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_sample_df])
        extract = extract.sort_values(by=["CATEGORY", 'Parent Country'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        # --- Saving the table hereby obtained
        print("Saving the table.")

        path = os.path.join(self.output_folder, f"{year}_benchmark_IIR_with_different_carve_outs.tex")

        extract.to_latex(
            buf=path,
            index=False,
            longtable=True,
            caption=f"Estimates of revenue gains from a global implementation of the IIR ({year})",
            label=f"tab:benchmarkIIR{year}carveouts"
        )

        print("Table saved as", f"{year}_benchmark_IIR_with_different_carve_outs.tex", "!")

    def benchmark_QDMTT_with_different_carve_outs(self, year):

        # --- Loading required data

        if year == 2016:

            calculator_noCO = TaxDeficitCalculator(
                year=2016,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
                carve_outs=False,
                de_minimis_exclusion=True,
                extended_dividends_adjustment=False,
                behavioral_responses=False,
                fetch_data_online=False
            )
            calculator_noCO.load_clean_data()

            calculator_firstyearCO = TaxDeficitCalculator(
                year=2016,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
                carve_outs=True,
                carve_out_rate_assets=0.08, carve_out_rate_payroll=0.1,
                depreciation_only=False, exclude_inventories=False, payroll_premium=20,
                ex_post_ETRs=False,
                de_minimis_exclusion=True,
                extended_dividends_adjustment=False,
                behavioral_responses=False,
                fetch_data_online=False
            )
            calculator_firstyearCO.load_clean_data()

            calculator_longtermCO = TaxDeficitCalculator(
                year=2016,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
                carve_outs=True,
                carve_out_rate_assets=0.05, carve_out_rate_payroll=0.05,
                depreciation_only=False, exclude_inventories=False, payroll_premium=20,
                ex_post_ETRs=False,
                de_minimis_exclusion=True,
                extended_dividends_adjustment=False,
                behavioral_responses=False,
                fetch_data_online=False
            )
            calculator_longtermCO.load_clean_data()

        elif year == 2017:

            calculator_noCO = TaxDeficitCalculator(
                year=2017,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
                carve_outs=False,
                de_minimis_exclusion=True,
                add_AUT_AUT_row=True,
                extended_dividends_adjustment=False,
                behavioral_responses=False,
                fetch_data_online=False
            )
            calculator_noCO.load_clean_data()

            calculator_firstyearCO = TaxDeficitCalculator(
                year=2017,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
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
                year=2017,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
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

        elif year == 2018:

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

        else:
            raise Exception("Three years are available for now: 2016, 2017, and 2018.")

        # --- Building the table

        CbC_Countries = list(calculator_2017_noCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits without carve-outs
        tds = calculator_noCO.compute_qdmtt_revenue_gains(minimum_ETR=0.15, upgrade_non_havens=True)

        extract1['TAX_DEFICIT'] /= 10**9
        extract1 = extract1.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'No Carve-Out',
                'PARTNER_COUNTRY_CODE': 'CODE',
            }
        )

        # Computing tax deficits with first-year carve-outs
        tds = calculator_firstyearCO.compute_qdmtt_revenue_gains(minimum_ETR=0.15, upgrade_non_havens=True)

        extract2['TAX_DEFICIT'] /= 10**9
        extract2 = extract2.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'Year 1',
                'PARTNER_COUNTRY_CODE': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        tds = calculator_longtermCO.compute_qdmtt_revenue_gains(minimum_ETR=0.15, upgrade_non_havens=True)

        extract3['TAX_DEFICIT'] /= 10**9
        extract3 = extract3.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'After Year 10',
                'PARTNER_COUNTRY_CODE': 'CODE',
            }
        )

        # Merging the three tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Source Country', 'CODE']
        ).merge(
            extract3, how='left', on=['Source Country', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_2017_noCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_2017_noCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 3 if row['IS_TH'] else 4, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else row['CATEGORY'], axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Source Country"] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Source Country"] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Source Country"] = "Total for CbC reporting"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Source Country"] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the tax haven sub-total
        TH_df = pd.DataFrame(extract[extract['IS_TH']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        TH_df.loc[0, "Source Country"] = "Total for tax havens"
        TH_df.loc[0, "CATEGORY"] = 3.4

        TH_df.loc[1, "Source Country"] = "Change in %"
        TH_df.iloc[1, 1] = ''
        TH_df.iloc[1, 2] = (TH_df.iloc[0, 2] - TH_df.iloc[0, 1]) / TH_df.iloc[0, 1] * 100
        TH_df.iloc[1, 3] = (TH_df.iloc[0, 3] - TH_df.iloc[0, 1]) / TH_df.iloc[0, 1] * 100
        TH_df.loc[1, "CATEGORY"] = 3.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Source Country"] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 3.8

        full_df.loc[1, "Source Country"] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 3.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC', 'IS_TH'])

        extract = pd.concat([extract, eu_df, cbc_df, full_sample_df])
        extract = extract.sort_values(by=["CATEGORY", 'Source Country'])
        extract = extract[extract['CATEGORY'] < 4].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        # --- Saving the table hereby obtained
        print("Saving the table.")

        path = os.path.join(self.output_folder, f"{year}_benchmark_QDMTT_with_different_carve_outs.tex")

        extract.to_latex(
            buf=path,
            index=False,
            longtable=True,
            caption=f"Estimates of revenue gains from a global implementation of the QDMTT ({year})",
            label=f"tab:benchmarkIIR{year}carveouts"
        )

        print("Table saved as", f"{year}_benchmark_QDMTT_with_different_carve_outs.tex", "!")

    def benchmark_IIR_with_different_minimum_rates(self, year):

        # --- Loading required data

        if year == 2016:

            calculator_longtermCO = TaxDeficitCalculator(
                year=2016,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
                carve_outs=True,
                carve_out_rate_assets=0.05, carve_out_rate_payroll=0.05,
                depreciation_only=False, exclude_inventories=False, payroll_premium=20,
                ex_post_ETRs=False,
                de_minimis_exclusion=True,
                extended_dividends_adjustment=False,
                behavioral_responses=False,
                fetch_data_online=False
            )
            calculator_longtermCO.load_clean_data()

        elif year == 2017:

            calculator_longtermCO = TaxDeficitCalculator(
                year=2017,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
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

        elif year == 2018:

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

        else:
            raise Exception("Three years are available for now: 2016, 2017, and 2018.")

        # --- Building the table

        CbC_Countries = list(calculator_2017_noCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits without carve-outs
        tds = calculator_longtermCO.compute_all_tax_deficits(minimum_ETR=0.15)

        extract1 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit'
            ]
        ].copy()

        extract1['tax_deficit'] /= 10**9
        extract1 = extract1.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Country',
                'tax_deficit': 'Minimum ETR: 15\%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with first-year carve-outs
        tds = calculator_longtermCO.compute_all_tax_deficits(minimum_ETR=0.2)

        extract2 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit'
            ]
        ].copy()

        extract2['tax_deficit'] /= 10**9
        extract2 = extract2.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Country',
                'tax_deficit': 'Minimum ETR: 20\%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        tds = calculator_longtermCO.compute_all_tax_deficits(minimum_ETR=0.25)

        extract3 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit'
            ]
        ].copy()

        extract3['tax_deficit'] /= 10**9
        extract3 = extract3.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Country',
                'tax_deficit': 'Minimum ETR: 25\%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        tds = calculator_longtermCO.compute_all_tax_deficits(minimum_ETR=0.3)

        extract4 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'tax_deficit'
            ]
        ].copy()

        extract4['tax_deficit'] /= 10**9
        extract4 = extract4.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract4 = extract4.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Country',
                'tax_deficit': 'Minimum ETR: 30\%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the three tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Parent Country', 'CODE']
        ).merge(
            extract3, how='left', on=['Parent Country', 'CODE']
        ).merge(
            extract4, how='left', on=['Parent Country', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_2017_noCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_2017_noCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Parent Country"] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Parent Country"] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = (eu_df.iloc[0, 4] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Parent Country"] = "Total for CbC reporting"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Parent Country"] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 4] = (cbc_df.iloc[0, 4] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Parent Country"] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Parent Country"] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 4] = (full_df.iloc[0, 4] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_sample_df])
        extract = extract.sort_values(by=["CATEGORY", 'Parent Country'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        # --- Saving the table hereby obtained
        print("Saving the table.")

        path = os.path.join(self.output_folder, f"{year}_benchmark_IIR_with_minimum_rates.tex")

        extract.to_latex(
            buf=path,
            index=False,
            longtable=True,
            caption=f"Estimates of revenue gains from the IIR for various minimum rates ({year})",
            label=f"tab:benchmarkIIR{year}minETR"
        )

        print("Table saved as", f"{year}_benchmark_IIR_with_minimum_rates.tex", "!")

    def benchmark_QDMTT_with_different_minimum_rates(self, year):

        # --- Loading required data

        if year == 2016:

            calculator_longtermCO = TaxDeficitCalculator(
                year=2016,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
                carve_outs=True,
                carve_out_rate_assets=0.05, carve_out_rate_payroll=0.05,
                depreciation_only=False, exclude_inventories=False, payroll_premium=20,
                ex_post_ETRs=False,
                de_minimis_exclusion=True,
                extended_dividends_adjustment=False,
                behavioral_responses=False,
                fetch_data_online=False
            )
            calculator_longtermCO.load_clean_data()

        elif year == 2017:

            calculator_longtermCO = TaxDeficitCalculator(
                year=2017,
                alternative_imputation=True,
                non_haven_TD_imputation_selection='EU',
                sweden_treatment='adjust', belgium_treatment='replace', SGP_CYM_treatment='replace',
                use_adjusted_profits=True,
                average_ETRs=True,
                years_for_avg_ETRs=[2016, 2017],
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

        elif year == 2018:

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

        else:
            raise Exception("Three years are available for now: 2016, 2017, and 2018.")

        # --- Building the table

        CbC_Countries = list(calculator_2017_noCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits without carve-outs
        tds = calculator_longtermCO.compute_qdmtt_revenue_gains(minimum_ETR=0.15)

        extract1['TAX_DEFICIT'] /= 10**9
        extract1 = extract1.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'Minimum ETR: 15\%',
                'PARTNER_COUNTRY_CODE': 'CODE',
            }
        )

        # Computing tax deficits with first-year carve-outs
        tds = calculator_longtermCO.compute_qdmtt_revenue_gains(minimum_ETR=0.2)

        extract2['TAX_DEFICIT'] /= 10**9
        extract2 = extract2.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'Minimum ETR: 20\%',
                'PARTNER_COUNTRY_CODE': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        tds = calculator_longtermCO.compute_qdmtt_revenue_gains(minimum_ETR=0.25)

        extract3['TAX_DEFICIT'] /= 10**9
        extract3 = extract3.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'Minimum ETR: 25\%',
                'PARTNER_COUNTRY_CODE': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        tds = calculator_longtermCO.compute_qdmtt_revenue_gains(minimum_ETR=0.3)

        extract4['TAX_DEFICIT'] /= 10**9
        extract4 = extract4.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract4 = extract4.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'Minimum ETR: 30\%',
                'PARTNER_COUNTRY_CODE': 'CODE',
            }
        )

        # Merging the three tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Source Country', 'CODE']
        ).merge(
            extract3, how='left', on=['Source Country', 'CODE']
        ).merge(
            extract4, how='left', on=['Source Country', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_2017_noCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_2017_noCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_TH'] else 4, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else row['CATEGORY'], axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Source Country"] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Source Country"] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = (eu_df.iloc[0, 4] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Source Country"] = "Total for CbC reporting"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Source Country"] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 4] = (cbc_df.iloc[0, 4] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the tax haven sub-total
        TH_df = pd.DataFrame(extract[extract['IS_TH']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T





        TH_df.loc[0, "Source Country"] = "Total for tax havens"
        TH_df.loc[0, "CATEGORY"] = 3.4

        TH_df.loc[1, "Source Country"] = "Change in %"
        TH_df.iloc[1, 1] = ''
        TH_df.iloc[1, 2] = (TH_df.iloc[0, 2] - TH_df.iloc[0, 1]) / TH_df.iloc[0, 1] * 100
        TH_df.iloc[1, 3] = (TH_df.iloc[0, 3] - TH_df.iloc[0, 1]) / TH_df.iloc[0, 1] * 100
        TH_df.loc[1, "CATEGORY"] = 3.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC', 'IS_TH']).sum()).T

        full_df.loc[0, "Source Country"] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 3.8

        full_df.loc[1, "Source Country"] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 4] = (full_df.iloc[0, 4] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 3.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_sample_df])
        extract = extract.sort_values(by=["CATEGORY", 'Source Country'])
        extract = extract[extract['CATEGORY'] < 4].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        # --- Saving the table hereby obtained
        print("Saving the table.")

        path = os.path.join(self.output_folder, f"{year}_benchmark_QDMTT_with_minimum_rates.tex")

        extract.to_latex(
            buf=path,
            index=False,
            longtable=True,
            caption=f"Estimates of revenue gains from the QDMTT for various minimum rates ({year})",
            label=f"tab:benchmarkQDMTT{year}minETR"
        )

        print("Table saved as", f"{year}_benchmark_QDMTT_with_minimum_rates.tex", "!")

