# Context

This repository accompanies the work of the [EU Tax Observatory](https://www.taxobservatory.eu) on the simulation of the revenue effects of a global minimum tax on corporate income.

- the first report, *Collecting the Tax Deficit of Multinational Companies: Simulations for the European Union*, was released in June 2021. The full-text version of the study can be read [here](https://www.taxobservatory.eu/wp-content/uploads/2021/06/EUTO2021.pdf#https-www-taxobservatory-eu-euto2021);


- it was followed by two notes, *Minimizing the Minimum Tax? The Critical Effect of Substance Carve-Outs* in July 2021 ([link](https://www.taxobservatory.eu/publication/minimizing-the-minimum-tax-the-critical-effect-of-substance-carve-outs/)) and *Revenue Effects of the Global Minimum Tax: Country-by-Country Estimates* in October 2021 ([link](https://www.taxobservatory.eu/publication/2938/));


- this work led to the publication of a peer-reviewed article in *Intertax*, under the title *Revenue Effects of the Global Minimum Tax Under Pillar Two*. The article can be accessed through this [link](https://kluwerlawonline.com/journalarticle/Intertax/50.10/TAXI2022074);


- eventually, the *Global Tax Evasion Report* of October 2023 (not yet released) presents an update of country-by-country revenue gain estimates.

# How to use the Python package

The code running the computations has been conceived as a Python package, making it easy to reproduce our results. The logic for macro-computations has been encapsulated in a Python class, `TaxDeficitCalculator`, defined in the `calculator.py` file. From there, several class methods allow to run the same computations as we do. Similarly, the computational logic for firm-level estimates (cf. first report of June 2021) is established in a dedicated class, `CompanyCalculator`, defined in the `firm_level.py` file.

## Installation

If you are using [pip](https://pip.pypa.io/en/stable/), you can run the following command to install the `tax_deficit_simulator` package:

```pip install --upgrade git+https://github.com/pechouc/tax_deficit_simulator.git```

## Example of usage

Once the package is installed, you can for instance reproduce our latest macro-computations of the paper with the `TaxDeficitCalculator` class. You can load the data locally or fetch them online as in:

```
from tax_deficit_simulator.calculator import TaxDeficitCalculator

calculator = TaxDeficitCalculator(year=2018, China_treatment_2018='2017_CbCR', fetch_data_online=True)
```

Before anything else, you will need to load and clean the data with the dedicated method. The command is the same regardless of whether you load the data from local files (`fetch_data_online` set to `False`) or online (`fetch_data_online` set to `True`).

```
calculator.load_clean_data()
```

You can then run any computation in which you are interested. For instance, to simulate a multilateral implementation of the Income Inclusion Rule (IIR) at a 15% minimum tax rate in which only EU Member-States collect their multinationals' domestic tax deficits:

```
calculator.compute_all_tax_deficits(0.15)
```

## Documentation

### Methodological resources

Documents describing our methodology and, in broad terms, how it translates in the code are available in the `files/methodology/` sub-folder of this repository ([link](https://github.com/eutaxobservatory/tax-deficit-simulator/tree/cleaning_repo/files/methodology)). You will find in there (i) the online appendix accompanying the *Intertax* article, which describes the methodology behind our computations from 2021 to 2022, and (ii) a technical note that presents the methodological updates introduced in 2023.

### Code specifications

The project documentation is available [here](https://eutaxobservatory.github.io/tax-deficit-simulator/) for detailed specifications. It will be complemented in the coming weeks with the latest additions to the code.

The documentation was built with [pdoc](https://pdoc3.github.io/pdoc/).

# How to use the simulator

The code in this repository also backs the online simulator, designed with the [Streamlit](https://streamlit.io) framework, that can be accessed via [this link](https://tax-deficit-simulator.herokuapp.com). This simulator was designed for policy makers, journalists, members of civil society, and all citizens in each EU country to assess the revenue potential from minimum taxation on both domestic and foreign firms.

This simulator estimates how much tax revenue the European Union could collect by imposing a minimum tax on the profits of multinational companies. It relies on the notion of tax deficit, defined as the difference between what multinationals currently pay in taxes, and what they would pay if they were subject to a minimum tax rate in each country. Three ways for EU countries to collect this tax deficit are considered:

- an international agreement on a minimum tax of the type currently discussed by the OECD ("Multinational agreement scenario" in the left-hand-side bar);


- an incomplete international agreement in which only EU countries apply a minimum tax. Additional revenues would then come from collecting a portion of the tax deficit of non-EU multinationals ("Partial cooperation scenario" in the left-hand-side bar);


- a "first-mover" scenario, in which one country alone decides to collect the tax deficit of multinational companies, entirely for its own firms and partially for the foreign ones ("Unilateral implementation scenario" in the left-hand-side bar).


In another tab, we also explain how the so-called "substance-based carve-outs" work and propose to investigate their impact on potential revenue gains ("Substance-based carve-outs" in the left-hand-side bar).

⚠️  Note that the results presented so far via the online simulator reflect our benchmark estimates as of August 2022, when the *Intertax* article was released, and the latest data used correspond to the 2017 income year. As such, **the simulator does not yet incorporate the methodological updates introduced in 2023**. The web application should be revamped in the coming weeks.

# Questions and contributions

Should you have any question about the code in this repository and its use, do not hesitate to write to [paul-emmanuel.chouc@ensae.fr](mailto:paul-emmanuel.chouc@ensae.fr) or open an issue in this repository.

In addition, so far, the code presented in this repository has not yet been optimized for performance. Feedback on how to improve computation times, the readability of the code, or anything else are very much welcome! Do not hesitate to open issues in the present repository should you have any question or remark.
