import pandas as pd

class TaxDeficitCalculator:

    def __init__(self):
        self.data = None

    def load_clean_data(self, path_to_file='test.csv', inplace=True):
        try:
            df = pd.read_csv(path_to_file, delimiter=';')

        except:
            raise Exception('Are you sure this is the right path for the source file?')

        numeric_columns = list(df.columns[2:])

        for column_name in numeric_columns:
            df[column_name] = df[column_name].map(lambda x: x.replace(',', '.'))
            df[column_name] = df[column_name].map(lambda x: 0 if x == '..' else x)
            df[column_name] = df[column_name].astype(float)

        df = df[~df['Partner jurisdiction (whitespaces cleaned)'].isin(['Foreign Jurisdictions Total', 'Stateless'])].copy()

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
            raise Exception("You asked for the tax deficit of a country which is not covered by the OECD's 2016 CbCR data.")

        df_restricted = df[df['Parent jurisdiction (whitespaces cleaned)'] == country].copy()

        if use_domestic_ETR:
            if verbose:
                print('NB: Computations are run using the domestic ETRs of each headquarter country.')

            minimum_ETR = df_restricted[df_restricted['Partner jurisdiction (whitespaces cleaned)'] == country]['ETR'].iloc[0]

        df_restricted = df_restricted[df_restricted['Partner jurisdiction (whitespaces cleaned)'] != country]

        df_restricted = df_restricted[df_restricted['ETR'] < minimum_ETR]

        df_restricted['ETR_differential'] = df_restricted['ETR'].map(lambda x: minimum_ETR - x)

        df_restricted['tax_deficit'] = df_restricted['ETR_differential'] * df_restricted['Profit (Loss) before Income Tax']

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

        return df.reset_index(drop=True)