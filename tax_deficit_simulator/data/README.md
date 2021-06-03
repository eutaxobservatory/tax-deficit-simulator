# Quick description of the data

The four main macro-data sources that can be found in this folder are the following:

- the `oecd.csv` file was extracted from the OECD's aggregated and anonymized country-by-country reporting, considering only the positive profit sample. Figures are in 2016 USD;

- the `twz.csv` file was extracted from the Table C4 of the TWZ 2019 online appendix. It presents, for a number of countries, the amounts of profits shifted to tax havens that are re-allocated to them on an ultimate ownership basis. Figures are in 2016 USD million;

- the `twz_domestic.csv` file, taken from the outputs of benchmark computations run on Stata. It presents for each country the amount of corporate profits registered locally by domestic MNEs and the effective tax rate to which they are subject. Figures are in 2016 USD billion;

- the `twz_CIT.csv`, extracted from Table U1 of the TWZ 2019 online appendix. It presents the corporate income tax revenue of each country in 2016 USD billion.

As for micro-data, the 10 firm-level country-by-country reports that feed the "Case study with one multinational" page of the simulator are gathered in the `firm_level_cbcrs` folder.

Eventually, two `.csv` files in this folder (`listofeucountries_csv.csv` and `tax_haven_list.csv`) respectively provide the list of EU-28 alpha-3 country codes and the list of tax havens' alpha-3 codes.

# Where to access the raw data

The raw aggregated and anonymized country-by-country data of the OECD can be found on the statistics portal of the OECD, following [this link](https://stats.oecd.org/Index.aspx?DataSetCode=CBCR_TABLEI).

The data compiled by Tørsløv, Wier and Zucman (2020) is available on [their website](https://missingprofits.world).
