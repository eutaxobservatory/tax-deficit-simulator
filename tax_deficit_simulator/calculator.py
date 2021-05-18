import pandas as pd


class TaxDeficitCalculator:

    def __init__(self):
        self.data = None

    def load_clean_data(self, path_to_file='test.csv', inplace=True):
        try:
            df = pd.read_csv(path_to_file, delimiter=';')

        except FileNotFoundError:
            raise Exception('Are you sure this is the right path for the source file?')

        numeric_columns = list(df.columns[2:])

        for column_name in numeric_columns:
            df[column_name] = df[column_name].map(lambda x: x.replace(',', '.'))
            df[column_name] = df[column_name].map(lambda x: 0 if x == '..' else x)
            df[column_name] = df[column_name].astype(float)

        df = df[
            ~df['Partner jurisdiction (whitespaces cleaned)'].isin(['Foreign Jurisdictions Total', 'Stateless'])
        ].copy()

        df['ETR'] = df['Income Tax Paid (on Cash Basis)'] / df['Profit (Loss) before Income Tax']

        if inplace:
            self.data = df.copy()

        else:
            return df.copy()

    def compute_country_tax_deficit(self, country, minimum_ETR=0.25, use_domestic_ETR=False, verbose=1):
        if self.data is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        df = self.data.copy()

        if country not in df['Parent jurisdiction (whitespaces cleaned)'].unique():
            raise Exception(
                "You asked for the tax deficit of a country which is not covered by the OECD's 2016 CbCR data."
            )

        df_restricted = df[df['Parent jurisdiction (whitespaces cleaned)'] == country].copy()

        if use_domestic_ETR:
            if verbose:
                print('NB: Computations are run using the domestic ETRs of each headquarter country.')

            minimum_ETR = df_restricted[
                df_restricted['Partner jurisdiction (whitespaces cleaned)'] == country
            ]['ETR'].iloc[0]

        df_restricted = df_restricted[df_restricted['Partner jurisdiction (whitespaces cleaned)'] != country]

        df_restricted = df_restricted[df_restricted['ETR'] < minimum_ETR]

        df_restricted['ETR_differential'] = df_restricted['ETR'].map(lambda x: minimum_ETR - x)

        df_restricted['tax_deficit'] = df_restricted['ETR_differential']\
            * df_restricted['Profit (Loss) before Income Tax']

        return df_restricted['tax_deficit'].sum()

    def compute_all_tax_deficits(self, minimum_ETR=0.25, use_domestic_ETRs=False, verbose=1):
        if self.data is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        if use_domestic_ETRs:
            if verbose:
                print('NB: Computations are run using the domestic ETRs of each headquarter country.')

        parent_countries = list(self.data['Parent jurisdiction (whitespaces cleaned)'].unique())

        output = {
            'Headquarter country': parent_countries,
            'Collectible tax deficit': []
        }

        for parent_country in parent_countries:
            tax_deficit = self.compute_country_tax_deficit(
                country=parent_country,
                minimum_ETR=minimum_ETR,
                use_domestic_ETR=use_domestic_ETRs,
                verbose=0
            )

            output['Collectible tax deficit'].append(tax_deficit)

        df = pd.DataFrame.from_dict(output)

        df = df[df['Collectible tax deficit'] != 0]

        df.sort_values(by='Collectible tax deficit', ascending=False, inplace=True)

        df.reset_index(drop=True, inplace=True)

        dict_df = df.to_dict()

        dict_df[df.columns[0]][len(df)] = 'Total'
        dict_df[df.columns[1]][len(df)] = df[df.columns[1]].sum()

        df = pd.DataFrame.from_dict(dict_df)

        return df.copy()

    def compute_second_scenario_gain(self, country, minimum_ETR=0.25):
        if self.data is None:
            raise Exception('You first need to load clean data with the dedicated method and inplace=True.')

        df = self.data.copy()

        tax_deficits = self.compute_all_tax_deficits(minimum_ETR=minimum_ETR, verbose=0)

        taxing_country = country

        attribution_ratios = []

        for country in tax_deficits['Headquarter country'].values:

            if country == taxing_country:
                attribution_ratios.append(1)

            else:
                df_restricted = df[df['Parent jurisdiction (whitespaces cleaned)'] == country].copy()

                if taxing_country not in df_restricted['Partner jurisdiction (whitespaces cleaned)'].values:
                    attribution_ratios.append(0)

                else:
                    mask = (df_restricted['Partner jurisdiction (whitespaces cleaned)'] == taxing_country)
                    sales_in_country = df_restricted[mask]['Unrelated Party Revenues'].iloc[0]

                    mask = (df_restricted['Partner jurisdiction (whitespaces cleaned)'] != country)
                    total_foreign_sales = df_restricted[mask]['Unrelated Party Revenues'].sum()

                    attribution_ratios.append(sales_in_country / total_foreign_sales)

        tax_deficits['Attribution ratios'] = attribution_ratios

        tax_deficits[f'Collectible tax deficit for {taxing_country}'] = \
            tax_deficits['Collectible tax deficit'] * tax_deficits['Attribution ratios']

        tax_deficits.drop(columns=['Attribution ratios', 'Collectible tax deficit'], inplace=True)

        tax_deficits = tax_deficits[tax_deficits[f'Collectible tax deficit for {taxing_country}'] > 0].copy()

        tax_deficits.sort_values(
            by=f'Collectible tax deficit for {taxing_country}',
            ascending=False,
            inplace=True
        )

        tax_deficits.reset_index(drop=True, inplace=True)

        dict_df = tax_deficits.to_dict()

        dict_df[tax_deficits.columns[0]][len(tax_deficits)] = 'Total'
        dict_df[tax_deficits.columns[1]][len(tax_deficits)] = tax_deficits[tax_deficits.columns[1]].sum()

        df = pd.DataFrame.from_dict(dict_df)

        return df.copy()

    def output_all_tax_deficits_cleaned(self, minimum_ETR=0.25, use_domestic_ETRs=False, verbose=0):

        df = self.compute_all_tax_deficits(
            minimum_ETR=minimum_ETR,
            use_domestic_ETRs=use_domestic_ETRs,
            verbose=verbose
        )

        df['Collectible tax deficit'] = df['Collectible tax deficit'] / 1000000
        df['Collectible tax deficit'] = df['Collectible tax deficit'].map('{:,.2f}'.format)

        df.rename(
            columns={'Collectible tax deficit': 'Collectible tax deficit (€m)'},
            inplace=True
        )

        df.style.applymap('font-weight: bold', subset=pd.IndexSlice[df.index[df.index == 'Total'], :])

        return df.copy()

    def output_second_scenario_gain_cleaned(self, country, minimum_ETR=0.25):

        df = self.compute_second_scenario_gain(
            country=country,
            minimum_ETR=minimum_ETR
        )

        df[f'Collectible tax deficit for {country}'] = df[f'Collectible tax deficit for {country}'] / 1000000
        df[f'Collectible tax deficit for {country}'] = \
            df[f'Collectible tax deficit for {country}'].map('{:,.2f}'.format)

        df.rename(
            columns={f'Collectible tax deficit for {country}': f'Collectible tax deficit for {country} (€m)'},
            inplace=True
        )

        return df.copy()


