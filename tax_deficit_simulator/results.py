import numpy as np
import pandas as pd

import os
import re

from tax_deficit_simulator.calculator import TaxDeficitCalculator


class TaxDeficitResults:

    def __init__(self, output_folder):

        self.output_folder = output_folder

    def load_benchmark_data_with_LT_carve_outs(self, year):

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

        return calculator_longtermCO

    def load_benchmark_data_for_all_carve_outs(self, year):

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

        return (calculator_noCO, calculator_firstyearCO, calculator_longtermCO)

    def show_partner_country_breakdowns_selected(self, year, minimum_breakdown):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Preprocessing OECD data

        oecd = pd.read_csv(calculator_longtermCO.path_to_oecd)

        # Focusing on the full sample (including loss-making entities)
        oecd = oecd[oecd['PAN'] == 'PANELA'].copy()

        if calculator_longtermCO.year == 2018 and calculator_longtermCO.China_treatment_2018 == '2017_CbCR':
            extract_China = oecd[np.logical_and(oecd['YEA'] == 2017, oecd['COU'] == 'CHN')].copy()
            extract_China['YEA'] += 1

            oecd = oecd[~np.logical_and(oecd['YEA'] == 2018, oecd['COU'] == 'CHN')].copy()
            oecd = pd.concat([oecd, extract_China], axis=0)

        oecd = oecd[oecd['YEA'] == calculator_longtermCO.year].copy()

        oecd.drop(
            columns=[
                'PAN', 'Grouping', 'Flag Codes', 'Flags', 'Year', 'YEA', 'Partner Jurisdiction'
            ],
            inplace=True
        )

        # Moving from a long to a wide dataset
        oecd = oecd.pivot(
            index=['COU', 'JUR', 'Ultimate Parent Jurisdiction'],
            columns='CBC',
            values='Value'
        ).reset_index()

        # Focusing on columns of interest
        oecd = oecd[['COU', 'JUR', 'Ultimate Parent Jurisdiction']].copy()

        # --- Building the table

        temp = oecd.groupby('Ultimate Parent Jurisdiction').agg({'JUR': 'nunique'}).reset_index()

        temp = temp[temp['JUR'] > minimum_breakdown].sort_values(by='JUR', ascending=False)

        temp = temp.rename(
            columns={
                'Ultimate Parent Jurisdiction': 'Parent jurisdiction',
                'JUR': 'Number of unique partners'
            }
        )

        temp = temp.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = temp.to_latex(
            column_format='lK{5cm}',
            index=False,
            longtable=True,
            caption=f"Parent countries with sufficiently granular CbCR statistics ({year})",
            label=f"tab:relevantparentcountries"
        )

        modified_string = str_table

        for col_name in temp.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        path = os.path.join(self.output_folder, f"{year}_relevant_parent_countries.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_relevant_parent_countries.tex", "!")

    def benchmark_IIR_with_different_carve_outs(self, year):

        # --- Loading required data

        (
            calculator_noCO, calculator_firstyearCO, calculator_longtermCO
        ) = self.load_benchmark_data_for_all_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

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
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
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
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
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
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
                'tax_deficit': 'After Year 10',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the three tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Parent Jur.', 'CODE']
        ).merge(
            extract3, how='left', on=['Parent Jur.', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Parent Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Parent Jur."] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Parent Jur."] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Parent Jur."] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Parent Jur."] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Parent Jur."] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Parent Jur.'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # return extract.to_latex(
        #     column_format='lK{2.5cm}K{2.5cm}K{2.5cm}',
        #     index=False,
        #     longtable=True,
        #     caption=f"Estimates of revenue gains from a global implementation of the IIR ({year})",
        #     label=f"tab:benchmarkIIR{year}carveouts"
        # )

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Estimates of revenue gains from a global implementation of the IIR ({year})",
            label=f"tab:benchmarkIIR{year}carveouts"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_IIR_with_different_carve_outs.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_IIR_with_different_carve_outs.tex", "!")

    def benchmark_QDMTT_with_different_carve_outs(self, year):

        # --- Loading required data

        (
            calculator_noCO, calculator_firstyearCO, calculator_longtermCO
        ) = self.load_benchmark_data_for_all_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits without carve-outs
        tds = calculator_noCO.compute_qdmtt_revenue_gains(minimum_ETR=0.15, upgrade_non_havens=True)

        extract1 = tds.copy()

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

        extract2 = tds.copy()

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

        extract3 = tds.copy()

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
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 3 if row['IS_TH'] else 4, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else row['CATEGORY'], axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC', 'IS_TH']).sum()).T

        eu_df.loc[0, "Source Country"] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Source Country"] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC', 'IS_TH']).sum()).T

        cbc_df.loc[0, "Source Country"] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Source Country"] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the tax haven sub-total
        TH_df = pd.DataFrame(extract[extract['IS_TH']].drop(columns=['IS_EU', 'IS_CBC', 'IS_TH']).sum()).T

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
        full_df.loc[1, "CATEGORY"] = 3.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC', 'IS_TH'])

        extract = pd.concat([extract, eu_df, cbc_df, TH_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Source Country'])
        extract = extract[extract['CATEGORY'] < 4].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Estimates of revenue gains from a global implementation of the QDMTT ({year})",
            label=f"tab:benchmarkQDMTT{year}carveouts"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [
            r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)',
            r'(Total for tax havens &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)'
        ]

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i <= 1:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i <= 1:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_QDMTT_with_different_carve_outs.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_QDMTT_with_different_carve_outs.tex", "!")

    def benchmark_IIR_with_different_minimum_rates(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits with a 15% minimum rate
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
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
                'tax_deficit': 'Min. ETR: 15%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 20% minimum rate
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
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
                'tax_deficit': 'Min. ETR: 20%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 25% minimum rate
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
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
                'tax_deficit': 'Min. ETR: 25%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 30% minimum rate
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
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
                'tax_deficit': 'Min. ETR: 30%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the four tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Parent Jur.', 'CODE']
        ).merge(
            extract3, how='left', on=['Parent Jur.', 'CODE']
        ).merge(
            extract4, how='left', on=['Parent Jur.', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Parent Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Parent Jur."] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = (eu_df.iloc[0, 4] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Parent Jur."] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Parent Jur."] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 4] = (cbc_df.iloc[0, 4] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Parent Jur."] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Parent Jur."] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 4] = (full_df.iloc[0, 4] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Parent Jur.'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Estimates of revenue gains from the IIR for various minimum rates ({year})",
            label=f"tab:benchmarkIIR{year}minETR"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_IIR_with_minimum_rates.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_IIR_with_minimum_rates.tex", "!")

    def benchmark_QDMTT_with_different_minimum_rates(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits without carve-outs
        tds = calculator_longtermCO.compute_qdmtt_revenue_gains(minimum_ETR=0.15)

        extract1 = tds.copy()

        extract1['TAX_DEFICIT'] /= 10**9
        extract1 = extract1.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'Min. ETR: 15%',
                'PARTNER_COUNTRY_CODE': 'CODE',
            }
        )

        # Computing tax deficits with first-year carve-outs
        tds = calculator_longtermCO.compute_qdmtt_revenue_gains(minimum_ETR=0.2)

        extract2 = tds.copy()

        extract2['TAX_DEFICIT'] /= 10**9
        extract2 = extract2.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'Min. ETR: 20%',
                'PARTNER_COUNTRY_CODE': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        tds = calculator_longtermCO.compute_qdmtt_revenue_gains(minimum_ETR=0.25)

        extract3 = tds.copy()

        extract3['TAX_DEFICIT'] /= 10**9
        extract3 = extract3.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'Min. ETR: 25%',
                'PARTNER_COUNTRY_CODE': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        tds = calculator_longtermCO.compute_qdmtt_revenue_gains(minimum_ETR=0.3)

        extract4 = tds.copy()

        extract4['TAX_DEFICIT'] /= 10**9
        extract4 = extract4.sort_values(by='PARTNER_COUNTRY_NAME').reset_index(drop=True)
        extract4 = extract4.rename(
            columns={
                'PARTNER_COUNTRY_NAME': 'Source Country',
                'TAX_DEFICIT': 'Min. ETR: 30%',
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
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 3 if row['IS_TH'] else 4, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else row['CATEGORY'], axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC', 'IS_TH']).sum()).T

        eu_df.loc[0, "Source Country"] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Source Country"] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = (eu_df.iloc[0, 4] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC', 'IS_TH']).sum()).T

        cbc_df.loc[0, "Source Country"] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Source Country"] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 4] = (cbc_df.iloc[0, 4] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the tax haven sub-total
        TH_df = pd.DataFrame(extract[extract['IS_TH']].drop(columns=['IS_EU', 'IS_CBC', 'IS_TH']).sum()).T

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
        extract = extract.drop(columns=['IS_EU', 'IS_CBC', 'IS_TH'])

        extract = pd.concat([extract, eu_df, cbc_df, TH_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Source Country'])
        extract = extract[extract['CATEGORY'] < 4].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Estimates of revenue gains from the QDMTT for various minimum rates ({year})",
            label=f"tab:benchmarkQDMTT{year}minETR"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [
            r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)',
            r'(Total for tax havens &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)'
        ]

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i <= 1:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i <= 1:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_QDMTT_with_minimum_rates.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_QDMTT_with_minimum_rates.tex", "!")

    def benchmark_IIR_with_origin_decomposed(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        extract = calculator_longtermCO.compute_all_tax_deficits(minimum_ETR=0.15)

        for col in ['tax_deficit', 'tax_deficit_x_domestic', 'tax_deficit_x_non_haven', 'tax_deficit_x_tax_haven']:
            extract[col] /= 10**9

        extract = extract.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
                'tax_deficit': 'Total tax deficit',
                'tax_deficit_x_domestic': 'From domestic profits',
                'tax_deficit_x_non_haven': 'From foreign non-havens',
                'tax_deficit_x_tax_haven': 'From foreign tax havens',
            }
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Parent Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Parent Jur."] = "Share of total (%)"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = eu_df.iloc[0, 2] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = eu_df.iloc[0, 3] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = eu_df.iloc[0, 4] / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Parent Jur."] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Parent Jur."] = "Share of total (%)"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = cbc_df.iloc[0, 2] / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = cbc_df.iloc[0, 3] / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 4] = cbc_df.iloc[0, 4] / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Parent Jur."] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Parent Jur."] = "Share of total (%)"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = full_df.iloc[0, 2] / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = full_df.iloc[0, 3] / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 4] = full_df.iloc[0, 4] / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Parent Jur.'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Origin of estimated revenue gains from the IIR ({year})",
            label=f"tab:benchmarkIIR{year}origin"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Share of total \(\\%\) &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_IIR_with_origin_decomposed.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_IIR_with_origin_decomposed.tex", "!")

    def benchmark_IIR_compare_years(self, year1, year2):

        if year1 == year2:
            raise Exception(
                'This function, designed for year-to-year comparisons, cannot run with twice the same year.'
            )

        year1_bis = min(year1, year2)
        year2_bis = max(year1, year2)

        year1 = year1_bis
        year2 = year2_bis

        # --- Loading required data

        calculator_longtermCO_year1 = self.load_benchmark_data_with_LT_carve_outs(year1)
        calculator_longtermCO_year2 = self.load_benchmark_data_with_LT_carve_outs(year2)

        # --- Building the table

        CbC_Countries_year1 = list(calculator_longtermCO_year1.oecd['Parent jurisdiction (alpha-3 code)'].unique())
        CbC_Countries_year2 = list(calculator_longtermCO_year2.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits with a 15% minimum rate
        tds = calculator_longtermCO_year1.compute_all_tax_deficits(minimum_ETR=0.15)

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
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
                'tax_deficit': f'{year1} tax deficit',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        extract1['temp'] = extract1['CODE'].isin(CbC_Countries_year1) * 1
        extract1[f'{year1} data source'] = extract1['temp'].map({0: 'TWZ', 1: 'CbCR'})
        extract1 = extract1.drop(columns=['temp'])

        # Computing tax deficits with a 20% minimum rate
        tds = calculator_longtermCO_year2.compute_all_tax_deficits(minimum_ETR=0.15)

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
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
                'tax_deficit': f'{year2} tax deficit',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        extract2['temp'] = extract2['CODE'].isin(CbC_Countries_year2) * 1
        extract2[f'{year2} data source'] = extract2['temp'].map({0: 'TWZ', 1: 'CbCR'})
        extract2 = extract2.drop(columns=['temp'])

        extract = extract1.merge(
            extract2,
            on=['CODE'],
            how='outer'
        )

        extract['Parent Jur.'] = extract.apply(
            lambda row: row['Parent Jur._x'] if isinstance(row['Parent Jur._x'], str) else row['Parent Jur._y'],
            axis=1
        )
        extract = extract.drop(columns=['Parent Jur._x', 'Parent Jur._y'])

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO_year1.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO_year1.tax_haven_country_codes)
        extract['IS_CBC'] = np.logical_or(
            extract['CODE'].isin(CbC_Countries_year1), extract['CODE'].isin(CbC_Countries_year2)
        )

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(
            columns=['IS_EU', 'IS_CBC', f'{year1} data source', f'{year2} data source']
        ).sum()).T

        eu_df.loc[0, "Parent Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Parent Jur."] = "Change in %"
        eu_df.loc[1, f'{year1} tax deficit'] = ''
        eu_df.loc[1, f'{year2} tax deficit'] = (
            eu_df.loc[0, f'{year2} tax deficit'] - eu_df.loc[0, f'{year1} tax deficit']
        ) / eu_df.loc[0, f'{year1} tax deficit'] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        eu_df[f'{year1} data source'] = ''
        eu_df[f'{year2} data source'] = ''

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(
            columns=['IS_EU', 'IS_CBC', f'{year1} data source', f'{year2} data source']
        ).sum()).T

        cbc_df.loc[0, "Parent Jur."] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Parent Jur."] = "Change in %"
        cbc_df.loc[1, f'{year1} tax deficit'] = ''
        cbc_df.loc[1, f'{year2} tax deficit'] = (
            cbc_df.loc[0, f'{year2} tax deficit'] - cbc_df.loc[0, f'{year1} tax deficit']
        ) / cbc_df.loc[0, f'{year1} tax deficit'] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        cbc_df[f'{year1} data source'] = ''
        cbc_df[f'{year2} data source'] = ''

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(
            columns=['IS_EU', 'IS_CBC', f'{year1} data source', f'{year2} data source']
        ).sum()).T

        full_df.loc[0, "Parent Jur."] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Parent Jur."] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.loc[1, f'{year1} tax deficit'] = ''
        full_df.loc[1, f'{year2} tax deficit'] = (
            full_df.loc[0, f'{year2} tax deficit'] - full_df.loc[0, f'{year1} tax deficit']
        ) / full_df.loc[0, f'{year1} tax deficit'] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        full_df[f'{year1} data source'] = ''
        full_df[f'{year2} data source'] = ''

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Parent Jur.'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract[
            ['Parent Jur.', f'{year1} data source', f'{year2} data source', f'{year1} tax deficit', f'{year2} tax deficit']
        ].copy()

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        for col in [f'{year1} data source', f'{year2} data source', f'{year1} tax deficit', f'{year2} tax deficit']:
            extract[col] = extract[col].fillna('NA')
            extract[col] = extract[col].map(lambda x: {'nan': 'NA'}.get(x, x))

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Estimates of revenue gains from the IIR ({year1} compared with {year2})",
            label=f"tab:benchmarkIIR{year1}comp{year2}"
        )

        modified_string = str_table

        modified_string = modified_string.replace(" NA ", " \\textit{NA} ")

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year1}comp{year2}_benchmark_IIR.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year1}comp{year2}_benchmark_IIR.tex", "!")

    def benchmark_EU_partial_cooperation_with_decomposition(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Building the table

        (
            selected_tax_deficits, details_directly_allocated, details_imputed
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=calculator_longtermCO.eu_27_country_codes,
            minimum_ETR=0.15,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract = selected_tax_deficits[
            ['Parent jurisdiction (whitespaces cleaned)', 'total', 'tax_deficit', 'directly_allocated', 'imputed']
        ].copy()

        for col in ['tax_deficit', 'total', 'directly_allocated', 'imputed']:
            extract[col] /= 10**9

        extract = extract.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Total revenue gains',
                'tax_deficit': 'Own tax deficit',
                'directly_allocated': 'From foreign firms, observed',
                'imputed': 'From foreign firms, imputed',
            }
        )

        extract['CATEGORY'] = 1

        # Adding the EU sub-total
        eu_df = pd.DataFrame(extract.sum()).T

        eu_df.loc[0, "Implementing Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.1

        eu_df.loc[1, "Implementing Jur."] = "Share of total (%)"
        eu_df.loc[1, "CATEGORY"] = 1.11
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = eu_df.iloc[0, 2] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = eu_df.iloc[0, 3] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = eu_df.iloc[0, 4] / eu_df.iloc[0, 1] * 100

        extract = pd.concat([extract, eu_df])

        # Re-ordering countries in alphabetical order
        extract = extract.sort_values(by=['CATEGORY', 'Implementing Jur.'])
        extract = extract.drop(columns=['CATEGORY'])

        # Rounding
        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the partial cooperation scenario restricted to the EU ({year})",
            label=f"tab:benchmarkpartialEU{year}decomposition"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Share of total \(\\%\) &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_EU_partial_cooperation_with_decomposition.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_EU_partial_cooperation_with_decomposition.tex", "!")

    def benchmark_EU_partial_cooperation_with_different_carve_outs(self, year):

        # --- Loading required data

        (
            calculator_noCO, calculator_firstyearCO, calculator_longtermCO
        ) = self.load_benchmark_data_for_all_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits without carve-outs
        (
            tds, _, _
        ) = calculator_noCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=calculator_noCO.eu_27_country_codes,
            minimum_ETR=0.15,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract1 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'total'
            ]
        ].copy()

        extract1['total'] /= 10**9
        extract1 = extract1.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'No Carve-Out',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with first-year carve-outs
        (
            tds, _, _
        ) = calculator_firstyearCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=calculator_firstyearCO.eu_27_country_codes,
            minimum_ETR=0.15,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract2 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'total'
            ]
        ].copy()

        extract2['total'] /= 10**9
        extract2 = extract2.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Year 1',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        (
            tds, _, _
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=calculator_longtermCO.eu_27_country_codes,
            minimum_ETR=0.15,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract3 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'total'
            ]
        ].copy()

        extract3['total'] /= 10**9
        extract3 = extract3.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'After Year 10',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the three tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Implementing Jur.', 'CODE']
        ).merge(
            extract3, how='left', on=['Implementing Jur.', 'CODE']
        )

        extract = extract.drop(columns=['CODE'])

        extract['CATEGORY'] = 1

        # Adding the EU sub-total
        eu_df = pd.DataFrame(extract.sum()).T

        eu_df.loc[0, "Implementing Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.1

        eu_df.loc[1, "Implementing Jur."] = "Change in %"
        eu_df.loc[1, "CATEGORY"] = 1.11
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100

        extract = pd.concat([extract, eu_df])

        # Re-ordering countries in alphabetical order
        extract = extract.sort_values(by=['CATEGORY', 'Implementing Jur.'])
        extract = extract.drop(columns=['CATEGORY'])

        # Rounding
        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the partial cooperation scenario restricted to the EU, for various minimum rates ({year})",
            label=f"tab:benchmarkpartialEU{year}carveouts"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_EU_partial_cooperation_with_different_carve_outs.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_EU_partial_cooperation_with_different_carve_outs.tex", "!")

    def benchmark_EU_partial_cooperation_with_different_min_rates(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Building the table

        # Computing tax deficits with a 15% minimum rate
        (
            tds, _, _
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=calculator_longtermCO.eu_27_country_codes,
            minimum_ETR=0.15,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract1 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'total'
            ]
        ].copy()

        extract1['total'] /= 10**9
        extract1 = extract1.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Min. ETR: 15%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 20% minimum rate
        (
            tds, _, _
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=calculator_longtermCO.eu_27_country_codes,
            minimum_ETR=0.2,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract2 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'total'
            ]
        ].copy()

        extract2['total'] /= 10**9
        extract2 = extract2.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Min. ETR: 20%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 25% minimum rate
        (
            tds, _, _
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=calculator_longtermCO.eu_27_country_codes,
            minimum_ETR=0.25,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract3 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'total'
            ]
        ].copy()

        extract3['total'] /= 10**9
        extract3 = extract3.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Min. ETR: 25%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 30% minimum rate
        (
            tds, _, _
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=calculator_longtermCO.eu_27_country_codes,
            minimum_ETR=0.3,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract4 = tds[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'total'
            ]
        ].copy()

        extract4['total'] /= 10**9
        extract4 = extract4.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract4 = extract4.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Min. ETR: 30%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the four tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Implementing Jur.', 'CODE']
        ).merge(
            extract3, how='left', on=['Implementing Jur.', 'CODE']
        ).merge(
            extract4, how='left', on=['Implementing Jur.', 'CODE']
        )

        extract = extract.drop(columns=['CODE'])

        extract['CATEGORY'] = 1

        # Adding the EU sub-total
        eu_df = pd.DataFrame(extract.sum()).T

        eu_df.loc[0, "Implementing Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.1

        eu_df.loc[1, "Implementing Jur."] = "Change in %"
        eu_df.loc[1, "CATEGORY"] = 1.11
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = (eu_df.iloc[0, 4] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100

        extract = pd.concat([extract, eu_df])

        # Re-ordering countries in alphabetical order
        extract = extract.sort_values(by=['CATEGORY', 'Implementing Jur.'])
        extract = extract.drop(columns=['CATEGORY'])

        # Rounding
        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the partial cooperation scenario restricted to the EU, for various minimum rates ({year})",
            label=f"tab:benchmarkpartialEU{year}minETR"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_EU_partial_cooperation_with_minimum_rates.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_EU_partial_cooperation_with_minimum_rates.tex", "!")

    def list_implementing_countries_TaxPolicyAssociates(self):

        # --- Listing countries implementing Pillar Two

        tax_data_TaxPolicyAssociates = pd.read_excel(
            "https://github.com/DanNeidle/tax_globe/raw/main/tax_globe_data.xlsx",
            engine="openpyxl"
        )

        tax_data_TaxPolicyAssociates['Pillar Two'] = tax_data_TaxPolicyAssociates.apply(
            lambda row: "implementing" if row['ISO'] == 'NOR' and row['Pillar Two'] == 'EU' else row['Pillar Two'],
            axis=1
        )

        extract = tax_data_TaxPolicyAssociates[
            tax_data_TaxPolicyAssociates['Pillar Two'].isin(['implementing', 'EU'])
        ].copy()

        extract = extract[['Jurisdiction', 'Pillar Two']].reset_index(drop=True)

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['Pillar Two'] == "EU"
        extract['IS_NON_EU'] = extract['Pillar Two'] != "EU"

        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else 2, axis=1)

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_NON_EU']).count()).T

        eu_df.loc[0, "Jurisdiction"] = "EU count"
        eu_df.loc[0, "CATEGORY"] = 1.5

        # Preparing the sub-total for non-EU countries
        non_eu_df = pd.DataFrame(extract[extract['IS_NON_EU']].drop(columns=['IS_EU', 'IS_NON_EU']).count()).T

        non_eu_df.loc[0, "Jurisdiction"] = "Non-EU count"
        non_eu_df.loc[0, "CATEGORY"] = 2.4

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_NON_EU']).count()).T

        full_df.loc[0, "Jurisdiction"] = "Full count"
        full_df.loc[0, "CATEGORY"] = 2.8

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_NON_EU'])

        extract = pd.concat([extract, eu_df, non_eu_df, full_df])

        extract = extract.sort_values(by=['CATEGORY', 'Jurisdiction'])

        extract = extract.rename(
            columns={
                'Pillar Two': 'Implementation status',
                'ISO': 'ISO alpha-3 code'
            }
        )

        extract = extract.drop(columns=['CATEGORY'])

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Jurisdictions implementing Pillar Two according to Tax Policy Associates",
            label=f"tab:implementingcountriesTaxPolicyAssociates"
        )

        modified_string = str_table

        for col_name in extract.columns:
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU count &(.+?)\\\\\n)', r'(Non-EU count &(.+?)\\\\\n)', r'(Full count &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        path = os.path.join(
            self.output_folder, f"implementing_countries_TaxPolicyAssociates.tex"
        )

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"implementing_countries_TaxPolicyAssociates.tex", "!")

    def benchmark_EUandothers_partial_cooperation_with_decomposition(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Listing countries implementing Pillar Two

        tax_data_TaxPolicyAssociates = pd.read_excel(
            "https://github.com/DanNeidle/tax_globe/raw/main/tax_globe_data.xlsx",
            engine="openpyxl"
        )

        tax_data_TaxPolicyAssociates['Pillar Two'] = tax_data_TaxPolicyAssociates.apply(
            lambda row: "implementing" if row['ISO'] == 'NOR' and row['Pillar Two'] == 'EU' else row['Pillar Two'],
            axis=1
        )

        countries_implementing = list(
            tax_data_TaxPolicyAssociates[
                tax_data_TaxPolicyAssociates['Pillar Two'].isin(['implementing', 'EU'])
            ]['ISO'].unique()
        )

        # --- Building the table

        (
            selected_tax_deficits, details_directly_allocated, details_imputed
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=countries_implementing,
            minimum_ETR=0.15,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract = selected_tax_deficits[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'Parent jurisdiction (alpha-3 code)',
                'total', 'tax_deficit', 'directly_allocated', 'imputed'
            ]
        ].copy()

        for col in ['tax_deficit', 'total', 'directly_allocated', 'imputed']:
            extract[col] /= 10**9

        extract = extract.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
                'total': 'Total revenue gains',
                'tax_deficit': 'Own tax deficit',
                'directly_allocated': 'From foreign firms, observed',
                'imputed': 'From foreign firms, imputed',
            }
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_NON_EU'] = ~extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)

        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else 2, axis=1)

        extract = extract.drop(columns=['CODE'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_NON_EU']).sum()).T

        eu_df.loc[0, "Implementing Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Implementing Jur."] = "Share of total (%)"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = eu_df.iloc[0, 2] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = eu_df.iloc[0, 3] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = eu_df.iloc[0, 4] / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for non-EU countries
        non_eu_df = pd.DataFrame(extract[extract['IS_NON_EU']].drop(columns=['IS_EU', 'IS_NON_EU']).sum()).T

        non_eu_df.loc[0, "Implementing Jur."] = "Non-EU total"
        non_eu_df.loc[0, "CATEGORY"] = 2.4

        non_eu_df.loc[1, "Implementing Jur."] = "Share of total (%)"
        non_eu_df.iloc[1, 1] = ''
        non_eu_df.iloc[1, 2] = non_eu_df.iloc[0, 2] / non_eu_df.iloc[0, 1] * 100
        non_eu_df.iloc[1, 3] = non_eu_df.iloc[0, 3] / non_eu_df.iloc[0, 1] * 100
        non_eu_df.iloc[1, 4] = non_eu_df.iloc[0, 4] / non_eu_df.iloc[0, 1] * 100
        non_eu_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_NON_EU']).sum()).T

        full_df.loc[0, "Implementing Jur."] = "All implementing"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Implementing Jur."] = "Share of total (%)"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = full_df.iloc[0, 2] / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = full_df.iloc[0, 3] / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 4] = full_df.iloc[0, 4] / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_NON_EU'])

        extract = pd.concat([extract, eu_df, non_eu_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Implementing Jur.'])

        extract = extract.drop(columns=['CATEGORY'])

        # Rounding
        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the partial cooperation scenario with EU and non-EU countries ({year})",
            label=f"tab:benchmarkpartialEUothers{year}decomposition"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(Non-EU total &(.+?)\\\\\n)', r'(All implementing &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Share of total \(\\%\) &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_EUandothers_partial_cooperation_with_decomposition.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_EUandothers_partial_cooperation_with_decomposition.tex", "!")

    def benchmark_EUandothers_partial_cooperation_with_different_carve_outs(self, year):

        # --- Loading required data

        (
            calculator_noCO, calculator_firstyearCO, calculator_longtermCO
        ) = self.load_benchmark_data_for_all_carve_outs(year)

        # --- Listing countries implementing Pillar Two

        tax_data_TaxPolicyAssociates = pd.read_excel(
            "https://github.com/DanNeidle/tax_globe/raw/main/tax_globe_data.xlsx",
            engine="openpyxl"
        )

        tax_data_TaxPolicyAssociates['Pillar Two'] = tax_data_TaxPolicyAssociates.apply(
            lambda row: "implementing" if row['ISO'] == 'NOR' and row['Pillar Two'] == 'EU' else row['Pillar Two'],
            axis=1
        )

        countries_implementing = list(
            tax_data_TaxPolicyAssociates[
                tax_data_TaxPolicyAssociates['Pillar Two'].isin(['implementing', 'EU'])
            ]['ISO'].unique()
        )

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits without carve-outs
        (
            selected_tax_deficits, _, _
        ) = calculator_noCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=countries_implementing,
            minimum_ETR=0.15,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract1 = selected_tax_deficits[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract1['total'] /= 10**9
        extract1 = extract1.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'No Carve-Out',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with first-year carve-outs
        (
            selected_tax_deficits, _, _
        ) = calculator_firstyearCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=countries_implementing,
            minimum_ETR=0.15,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract2 = selected_tax_deficits[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract2['total'] /= 10**9
        extract2 = extract2.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Year 1',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        (
            selected_tax_deficits, _, _
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=countries_implementing,
            minimum_ETR=0.15,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract3 = selected_tax_deficits[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract3['total'] /= 10**9
        extract3 = extract3.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'After Year 10',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the three tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Implementing Jur.', 'CODE']
        ).merge(
            extract3, how='left', on=['Implementing Jur.', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_NON_EU'] = ~extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)

        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else 2, axis=1)

        extract = extract.drop(columns=['CODE'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_NON_EU']).sum()).T

        eu_df.loc[0, "Implementing Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Implementing Jur."] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for non-EU countries
        non_eu_df = pd.DataFrame(extract[extract['IS_NON_EU']].drop(columns=['IS_EU', 'IS_NON_EU']).sum()).T

        non_eu_df.loc[0, "Implementing Jur."] = "Non-EU total"
        non_eu_df.loc[0, "CATEGORY"] = 2.4

        non_eu_df.loc[1, "Implementing Jur."] = "Change in %"
        non_eu_df.iloc[1, 1] = ''
        non_eu_df.iloc[1, 2] = (non_eu_df.iloc[0, 2] - non_eu_df.iloc[0, 1]) / non_eu_df.iloc[0, 1] * 100
        non_eu_df.iloc[1, 3] = (non_eu_df.iloc[0, 3] - non_eu_df.iloc[0, 1]) / non_eu_df.iloc[0, 1] * 100
        non_eu_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_NON_EU']).sum()).T

        full_df.loc[0, "Implementing Jur."] = "All implementing"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Implementing Jur."] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_NON_EU'])

        extract = pd.concat([extract, eu_df, non_eu_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Implementing Jur.'])

        extract = extract.drop(columns=['CATEGORY'])

        # Rounding
        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the partial cooperation scenario with EU and non-EU countries ({year})",
            label=f"tab:benchmarkpartialEUothers{year}carveouts"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(Non-EU total &(.+?)\\\\\n)', r'(All implementing &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_EUandothers_partial_cooperation_with_different_carve_outs.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_EUandothers_partial_cooperation_with_different_carve_outs.tex", "!")

    def benchmark_EUandothers_partial_cooperation_with_different_min_rates(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Listing countries implementing Pillar Two

        tax_data_TaxPolicyAssociates = pd.read_excel(
            "https://github.com/DanNeidle/tax_globe/raw/main/tax_globe_data.xlsx",
            engine="openpyxl"
        )

        tax_data_TaxPolicyAssociates['Pillar Two'] = tax_data_TaxPolicyAssociates.apply(
            lambda row: "implementing" if row['ISO'] == 'NOR' and row['Pillar Two'] == 'EU' else row['Pillar Two'],
            axis=1
        )

        countries_implementing = list(
            tax_data_TaxPolicyAssociates[
                tax_data_TaxPolicyAssociates['Pillar Two'].isin(['implementing', 'EU'])
            ]['ISO'].unique()
        )

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits with a 15% minimum rate
        (
            selected_tax_deficits, _, _
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=countries_implementing,
            minimum_ETR=0.15,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract1 = selected_tax_deficits[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract1['total'] /= 10**9
        extract1 = extract1.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Min. ETR: 15%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 20% minimum rate
        (
            selected_tax_deficits, _, _
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=countries_implementing,
            minimum_ETR=0.2,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract2 = selected_tax_deficits[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract2['total'] /= 10**9
        extract2 = extract2.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Min. ETR: 20%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 25% minimum rate
        (
            selected_tax_deficits, _, _
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=countries_implementing,
            minimum_ETR=0.25,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract3 = selected_tax_deficits[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract3['total'] /= 10**9
        extract3 = extract3.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Min. ETR: 25%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 30% minimum rate
        (
            selected_tax_deficits, _, _
        ) = calculator_longtermCO.compute_selected_intermediary_scenario_gain(
            countries_implementing=countries_implementing,
            minimum_ETR=0.3,
            among_countries_implementing=False,
            minimum_breakdown=60
        )

        extract4 = selected_tax_deficits[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract4['total'] /= 10**9
        extract4 = extract4.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract4 = extract4.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Implementing Jur.',
                'total': 'Min. ETR: 30%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the four tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Implementing Jur.', 'CODE']
        ).merge(
            extract3, how='left', on=['Implementing Jur.', 'CODE']
        ).merge(
            extract4, how='left', on=['Implementing Jur.', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_NON_EU'] = ~extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)

        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else 2, axis=1)

        extract = extract.drop(columns=['CODE'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_NON_EU']).sum()).T

        eu_df.loc[0, "Implementing Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Implementing Jur."] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = (eu_df.iloc[0, 4] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for non-EU countries
        non_eu_df = pd.DataFrame(extract[extract['IS_NON_EU']].drop(columns=['IS_EU', 'IS_NON_EU']).sum()).T

        non_eu_df.loc[0, "Implementing Jur."] = "Non-EU total"
        non_eu_df.loc[0, "CATEGORY"] = 2.4

        non_eu_df.loc[1, "Implementing Jur."] = "Change in %"
        non_eu_df.iloc[1, 1] = ''
        non_eu_df.iloc[1, 2] = (non_eu_df.iloc[0, 2] - non_eu_df.iloc[0, 1]) / non_eu_df.iloc[0, 1] * 100
        non_eu_df.iloc[1, 3] = (non_eu_df.iloc[0, 3] - non_eu_df.iloc[0, 1]) / non_eu_df.iloc[0, 1] * 100
        non_eu_df.iloc[1, 4] = (non_eu_df.iloc[0, 4] - non_eu_df.iloc[0, 1]) / non_eu_df.iloc[0, 1] * 100
        non_eu_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_NON_EU']).sum()).T

        full_df.loc[0, "Implementing Jur."] = "All implementing"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Implementing Jur."] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 4] = (full_df.iloc[0, 4] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_NON_EU'])

        extract = pd.concat([extract, eu_df, non_eu_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Implementing Jur.'])

        extract = extract.drop(columns=['CATEGORY'])

        # Rounding
        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the partial cooperation scenario with EU and non-EU countries ({year})",
            label=f"tab:benchmarkpartialEUothers{year}minETR"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(Non-EU total &(.+?)\\\\\n)', r'(All implementing &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_EUandothers_partial_cooperation_with_minimum_rates.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_EUandothers_partial_cooperation_with_minimum_rates.tex", "!")

    def benchmark_unilateral_with_decomposition(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        (
            extract, details_directly_allocated, details_imputed_foreign, details_imputed_domestic
        ) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=True,
            minimum_ETR=0.15,
            minimum_breakdown=60
        )

        extract = extract.drop(columns=['directly_allocated'])

        # Re-ordering columns
        extract = extract[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'total', 'directly_allocated_dom', 'directly_allocated_for', 'imputed_domestic', 'imputed_foreign',
                'Parent jurisdiction (alpha-3 code)'
            ]
        ].copy()

        for col in ['total', 'directly_allocated_dom', 'imputed_domestic', 'directly_allocated_for', 'imputed_foreign']:
            extract[col] /= 10**9

        extract = extract.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
                'total': 'Total revenue gains',
                'directly_allocated_dom': 'From own tax deficit, observed',
                'imputed_domestic': 'From own tax deficit, imputed',
                'directly_allocated_for': 'From foreign firms, observed',
                'imputed_foreign': 'From foreign firms, imputed',
            }
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Adopting Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Adopting Jur."] = "Share of total (%)"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = eu_df.iloc[0, 2] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = eu_df.iloc[0, 3] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = eu_df.iloc[0, 4] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 5] = eu_df.iloc[0, 5] / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Adopting Jur."] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Adopting Jur."] = "Share of total (%)"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = cbc_df.iloc[0, 2] / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = cbc_df.iloc[0, 3] / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 4] = cbc_df.iloc[0, 4] / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 5] = cbc_df.iloc[0, 5] / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Adopting Jur."] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Adopting Jur."] = "Share of total (%)"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = full_df.iloc[0, 2] / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = full_df.iloc[0, 3] / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 4] = full_df.iloc[0, 4] / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 5] = full_df.iloc[0, 5] / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Adopting Jur.'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the unilateral adoption scenario ({year})",
            label=f"tab:benchmarkunilateral{year}decomposition"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Share of total \(\\%\) &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_unilateral_with_decomposition.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_unilateral_with_decomposition.tex", "!")

    def benchmark_unilateral_with_different_carve_outs(self, year):

        # --- Loading required data

        (
            calculator_noCO, calculator_firstyearCO, calculator_longtermCO
        ) = self.load_benchmark_data_for_all_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits without carve-outs
        (tds, _, _, _) = calculator_noCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=True,
            minimum_ETR=0.15,
            minimum_breakdown=60
        )

        extract1 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract1['total'] /= 10**9
        extract1 = extract1.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'No Carve-Out',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with first-year carve-outs
        (tds, _, _, _) = calculator_firstyearCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=True,
            minimum_ETR=0.15,
            minimum_breakdown=60
        )

        extract2 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract2['total'] /= 10**9
        extract2 = extract2.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'Year 1',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        (tds, _, _, _) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=True,
            minimum_ETR=0.15,
            minimum_breakdown=60
        )

        extract3 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract3['total'] /= 10**9
        extract3 = extract3.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'After Year 10',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the three tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Adopting Jur.', 'CODE']
        ).merge(
            extract3, how='left', on=['Adopting Jur.', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Adopting Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Adopting Jur."] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Adopting Jur."] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Adopting Jur."] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Adopting Jur."] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Adopting Jur."] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Adopting Jur.'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the unilateral adoption scenario, for various carve-outs ({year})",
            label=f"tab:benchmarkunilateral{year}carveouts"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_unilateral_with_different_carve_outs.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_unilateral_with_different_carve_outs.tex", "!")

    def benchmark_unilateral_with_different_min_rates(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits with a 15% minimum rate
        (tds, _, _, _) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=True,
            minimum_ETR=0.15,
            minimum_breakdown=60
        )

        extract1 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract1['total'] /= 10**9
        extract1 = extract1.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'Min. ETR: 15%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 20% minimum rate
        (tds, _, _, _) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=True,
            minimum_ETR=0.2,
            minimum_breakdown=60
        )

        extract2 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract2['total'] /= 10**9
        extract2 = extract2.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'Min. ETR: 20%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 25% minimum rate
        (tds, _, _, _) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=True,
            minimum_ETR=0.25,
            minimum_breakdown=60
        )

        extract3 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract3['total'] /= 10**9
        extract3 = extract3.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'Min. ETR: 25%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 30% minimum rate
        (tds, _, _, _) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=True,
            minimum_ETR=0.3,
            minimum_breakdown=60
        )

        extract4 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract4['total'] /= 10**9
        extract4 = extract4.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract4 = extract4.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'Min. ETR: 30%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the four tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Adopting Jur.', 'CODE']
        ).merge(
            extract3, how='left', on=['Adopting Jur.', 'CODE']
        ).merge(
            extract4, how='left', on=['Adopting Jur.', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Adopting Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Adopting Jur."] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = (eu_df.iloc[0, 4] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Adopting Jur."] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Adopting Jur."] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 4] = (cbc_df.iloc[0, 4] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Adopting Jur."] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Adopting Jur."] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 4] = (full_df.iloc[0, 4] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Adopting Jur.'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the unilateral adoption scenario, for various minimum rates ({year})",
            label=f"tab:benchmarkunilateral{year}minETR"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_unilateral_with_minimum_rates.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_unilateral_with_minimum_rates.tex", "!")

    def benchmark_fullapportionment_with_decomposition(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        (
            extract, details_directly_allocated, details_imputed_foreign, details_imputed_domestic
        ) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=False,
            minimum_ETR=0.15,
            minimum_breakdown=60
        )

        extract = extract.drop(columns=['directly_allocated'])

        # Re-ordering columns
        extract = extract[
            [
                'Parent jurisdiction (whitespaces cleaned)',
                'total', 'directly_allocated_dom', 'directly_allocated_for', 'imputed_domestic', 'imputed_foreign',
                'Parent jurisdiction (alpha-3 code)'
            ]
        ].copy()

        for col in ['total', 'directly_allocated_dom', 'imputed_domestic', 'directly_allocated_for', 'imputed_foreign']:
            extract[col] /= 10**9

        extract = extract.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Parent Jur.',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
                'total': 'Total revenue gains',
                'directly_allocated_dom': 'From own tax deficit, observed',
                'imputed_domestic': 'From own tax deficit, imputed',
                'directly_allocated_for': 'From foreign firms, observed',
                'imputed_foreign': 'From foreign firms, imputed',
            }
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Parent Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Parent Jur."] = "Share of total (%)"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = eu_df.iloc[0, 2] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = eu_df.iloc[0, 3] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = eu_df.iloc[0, 4] / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 5] = eu_df.iloc[0, 5] / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Parent Jur."] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Parent Jur."] = "Share of total (%)"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = cbc_df.iloc[0, 2] / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = cbc_df.iloc[0, 3] / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 4] = cbc_df.iloc[0, 4] / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 5] = cbc_df.iloc[0, 5] / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Parent Jur."] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Parent Jur."] = "Share of total (%)"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = full_df.iloc[0, 2] / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = full_df.iloc[0, 3] / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 4] = full_df.iloc[0, 4] / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 5] = full_df.iloc[0, 5] / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Parent Jur.'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates with full sales apportionment ({year})",
            label=f"tab:benchmarkapportionment{year}decomposition"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Share of total \(\\%\) &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_fullapportionment_with_decomposition.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_fullapportionment_with_decomposition.tex", "!")

    def benchmark_fullapportionment_with_different_carve_outs(self, year):

        # --- Loading required data

        (
            calculator_noCO, calculator_firstyearCO, calculator_longtermCO
        ) = self.load_benchmark_data_for_all_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits without carve-outs
        (tds, _, _, _) = calculator_noCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=False,
            minimum_ETR=0.15,
            minimum_breakdown=60
        )

        extract1 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract1['total'] /= 10**9
        extract1 = extract1.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'No Carve-Out',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with first-year carve-outs
        (tds, _, _, _) = calculator_firstyearCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=False,
            minimum_ETR=0.15,
            minimum_breakdown=60
        )

        extract2 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract2['total'] /= 10**9
        extract2 = extract2.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'Year 1',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with long-term carve-outs
        (tds, _, _, _) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=False,
            minimum_ETR=0.15,
            minimum_breakdown=60
        )

        extract3 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract3['total'] /= 10**9
        extract3 = extract3.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'After Year 10',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the three tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Adopting Jur.', 'CODE']
        ).merge(
            extract3, how='left', on=['Adopting Jur.', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Adopting Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Adopting Jur."] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Adopting Jur."] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Adopting Jur."] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Adopting Jur."] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Adopting Jur."] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Adopting Jur.'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the full apportionment scenario, for various carve-outs ({year})",
            label=f"tab:benchmarkapportionment{year}carveouts"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_fullapportionment_with_different_carve_outs.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_fullapportionment_with_different_carve_outs.tex", "!")

    def benchmark_fullapportionment_with_different_min_rates(self, year):

        # --- Loading required data

        calculator_longtermCO = self.load_benchmark_data_with_LT_carve_outs(year)

        # --- Building the table

        CbC_Countries = list(calculator_longtermCO.oecd['Parent jurisdiction (alpha-3 code)'].unique())

        # Computing tax deficits with a 15% minimum rate
        (tds, _, _, _) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=False,
            minimum_ETR=0.15,
            minimum_breakdown=60
        )

        extract1 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract1['total'] /= 10**9
        extract1 = extract1.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract1 = extract1.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'Min. ETR: 15%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 20% minimum rate
        (tds, _, _, _) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=False,
            minimum_ETR=0.2,
            minimum_breakdown=60
        )

        extract2 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract2['total'] /= 10**9
        extract2 = extract2.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract2 = extract2.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'Min. ETR: 20%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 25% minimum rate
        (tds, _, _, _) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=False,
            minimum_ETR=0.25,
            minimum_breakdown=60
        )

        extract3 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract3['total'] /= 10**9
        extract3 = extract3.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract3 = extract3.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'Min. ETR: 25%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Computing tax deficits with a 30% minimum rate
        (tds, _, _, _) = calculator_longtermCO.compute_unilateral_scenario_revenue_gains(
            full_own_tax_deficit=False,
            minimum_ETR=0.3,
            minimum_breakdown=60
        )

        extract4 = tds[
            ['Parent jurisdiction (whitespaces cleaned)', 'Parent jurisdiction (alpha-3 code)', 'total']
        ].copy()

        extract4['total'] /= 10**9
        extract4 = extract4.sort_values(by='Parent jurisdiction (whitespaces cleaned)').reset_index(drop=True)
        extract4 = extract4.rename(
            columns={
                'Parent jurisdiction (whitespaces cleaned)': 'Adopting Jur.',
                'total': 'Min. ETR: 30%',
                'Parent jurisdiction (alpha-3 code)': 'CODE',
            }
        )

        # Merging the four tax deficit estimates
        extract = extract1.merge(
            extract2, how='left', on=['Adopting Jur.', 'CODE']
        ).merge(
            extract3, how='left', on=['Adopting Jur.', 'CODE']
        ).merge(
            extract4, how='left', on=['Adopting Jur.', 'CODE']
        )

        # Determining each country's category (and ultimately the position in the table)
        extract['IS_EU'] = extract['CODE'].isin(calculator_longtermCO.eu_27_country_codes)
        extract['IS_TH'] = extract['CODE'].isin(calculator_longtermCO.tax_haven_country_codes)
        extract['IS_CBC'] = extract['CODE'].isin(CbC_Countries)

        extract['CATEGORY'] = extract.apply(lambda row: 2 if row['IS_CBC'] else 3, axis=1)
        extract['CATEGORY'] = extract.apply(lambda row: 1 if row['IS_EU'] else row['CATEGORY'], axis=1)

        extract = extract.drop(columns=['CODE', 'IS_TH'])

        # Preparing the EU sub-total
        eu_df = pd.DataFrame(extract[extract['IS_EU']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        eu_df.loc[0, "Adopting Jur."] = "EU total"
        eu_df.loc[0, "CATEGORY"] = 1.5

        eu_df.loc[1, "Adopting Jur."] = "Change in %"
        eu_df.iloc[1, 1] = ''
        eu_df.iloc[1, 2] = (eu_df.iloc[0, 2] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 3] = (eu_df.iloc[0, 3] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.iloc[1, 4] = (eu_df.iloc[0, 4] - eu_df.iloc[0, 1]) / eu_df.iloc[0, 1] * 100
        eu_df.loc[1, "CATEGORY"] = 1.51

        # Preparing the sub-total for countries providing CbCR statistics
        cbc_df = pd.DataFrame(extract[extract['IS_CBC']].drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        cbc_df.loc[0, "Adopting Jur."] = "CbCR total"
        cbc_df.loc[0, "CATEGORY"] = 2.4

        cbc_df.loc[1, "Adopting Jur."] = "Change in %"
        cbc_df.iloc[1, 1] = ''
        cbc_df.iloc[1, 2] = (cbc_df.iloc[0, 2] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 3] = (cbc_df.iloc[0, 3] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.iloc[1, 4] = (cbc_df.iloc[0, 4] - cbc_df.iloc[0, 1]) / cbc_df.iloc[0, 1] * 100
        cbc_df.loc[1, "CATEGORY"] = 2.41

        # Preparing the full sample total
        full_df = pd.DataFrame(extract.drop(columns=['IS_EU', 'IS_CBC']).sum()).T

        full_df.loc[0, "Adopting Jur."] = "Full sample total"
        full_df.loc[0, "CATEGORY"] = 2.8

        full_df.loc[1, "Adopting Jur."] = "Change in %"
        full_df.iloc[1, 1] = ''
        full_df.iloc[1, 2] = (full_df.iloc[0, 2] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 3] = (full_df.iloc[0, 3] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.iloc[1, 4] = (full_df.iloc[0, 4] - full_df.iloc[0, 1]) / full_df.iloc[0, 1] * 100
        full_df.loc[1, "CATEGORY"] = 2.81

        # Adding sub-totals and ordering countries
        extract = extract.drop(columns=['IS_EU', 'IS_CBC'])

        extract = pd.concat([extract, eu_df, cbc_df, full_df])
        extract = extract.sort_values(by=["CATEGORY", 'Adopting Jur.'])
        extract = extract[extract['CATEGORY'] < 3].copy()
        extract = extract.drop(columns=['CATEGORY'])

        extract = extract.applymap(lambda x: str(round(x, 1)) if isinstance(x, float) else x).reset_index(drop=True)

        extract = extract.applymap(
            lambda x: {"China (People's Republic of)": "China", "Hong Kong, China": "Hong Kong"}.get(x, x)
        ).reset_index(drop=True)

        # --- Formatting and saving the table hereby obtained
        print("Formatting and saving the table.")

        str_table = extract.to_latex(
            column_format='lK{2.5cm}K{2.5cm}K{2.5cm}K{2.5cm}',
            index=False,
            longtable=True,
            caption=f"Revenue gain estimates in the full apportionment scenario, for various minimum rates ({year})",
            label=f"tab:benchmarkapportionment{year}minETR"
        )

        modified_string = str_table

        for col_name in extract.columns:
            col_name = col_name.replace('%', '\\%')
            modified_string = modified_string.replace(col_name + ' ', '\\textbf{' + col_name + '} ')

        patterns = [r'(EU total &(.+?)\\\\\n)', r'(CbCR total &(.+?)\\\\\n)', r'(Full sample total &(.+?)\\\\\n)']

        for i, pattern in enumerate(patterns):

            match = re.search(pattern, modified_string, re.DOTALL)

            if match:
                row = match.group(1)
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textbf{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + bold_row)

        pattern_perc = r'(Change in \\% &(.+?)\\\\\n)'
        matches = re.findall(pattern_perc, modified_string, re.DOTALL)

        if len(matches) > 0:
            for i, match in enumerate(matches):

                row = match[0]
                cells = [cell.strip() for cell in row.split('&')]
                cells[-1] = cells[-1].replace('\\', '')

                if i == 0:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n\\midrule\n'
                    modified_string = modified_string.replace(row, '\\hskip 10pt ' + bold_row)

                else:
                    bold_row = ' & '.join(['\\textit{' + cell + '}' for cell in cells]) + ' \\\\\n'
                    modified_string = modified_string.replace(row, '\\midrule\n' + '\\hskip 10pt ' + bold_row)

        path = os.path.join(self.output_folder, f"{year}_benchmark_fullapportionment_with_minimum_rates.tex")

        with open(path, 'w') as file:
            file.write(modified_string)

        print("Table saved as", f"{year}_benchmark_fullapportionment_with_minimum_rates.tex", "!")
