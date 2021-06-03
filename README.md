# Context

This repository accompanies the report of the [EU Tax Observatory](https://www.taxobservatory.eu), *Collecting the tax deficit of multinational companies: Simulations for the European Union* (June 2021). The full-text version of the study can be read [here](https://www.taxobservatory.eu/wp-content/uploads/2021/06/EUTO2021.pdf#https-www-taxobservatory-eu-euto2021).

This study estimates how much tax revenue the European Union could collect by imposing a minimum tax on the profits of multinational companies. It relies on the notion of tax deficit, defined as the difference between what multinationals currently pay in taxes, and what they would pay if they were subject to a minimum tax rate in each country. Three ways for EU countries to collect this tax deficit are considered:

- an international agreement on a minimum tax of the type currently discussed by the OECD, in which scenario a minimum tax rate of 25% could increase corporate income tax revenues in the European Union by about €170 billion in 2021;


- an incomplete international agreement in which only EU countries apply a minimum tax. An additional €30 billion would then come from collecting a portion of the tax deficit of non-EU multinationals;


- a “first-mover” scenario, in which one country alone decides to collect the tax deficit of multinational companies. On average, a first mover in the European Union would increase its corporate tax revenues by close to 70% relative to its current corporate tax collection.

# How to use the simulator

The code in this repository backs the online simulator, designed with the [Streamlit](https://streamlit.io) framework, that can be accessed via [this link](https://tax-deficit-simulator.herokuapp.com). This simulator was designed for policy makers, journalists, members of civil society, and all citizens in each EU country to assess the revenue potential from minimum taxation on both domestic and foreign firms. Each of the aforementioned scenarios can be investigated on a specific page, accessible via the left-hand sidebar, that allows to simulate corporate tax revenue gains from any minimum effective tax rate between 10% and 50%.

# How to use the Python package

Besides the online simulator, the code running the computations has been conceived as a Python package, making it easy to reproduce our results. The logic for macro-computations has been encapsulated in a Python class, `TaxDeficitCalculator`, defined in the `calculator.py` file. From there, several class methods allow to run the same computations as we do for the three scenarios. Similarly, the computational logic for firm-level estimates is established in a dedicated class, `CompanyCalculator`, defined in the `firm_level.py` file.

## Installation

If you are using [pip](https://pip.pypa.io/en/stable/), you can run the following command to install the `tax_deficit_simulator` package:

```pip install --upgrade git+https://github.com/pechouc/tax_deficit_simulator.git```

## Example of usage

Once the package is installed, you can for instance reproduce the macro-computations of the paper with the `TaxDeficitCalculator` class:

```
from tax_deficit_simulator.calculator import TaxDeficitCalculator

calculator = TaxDeficitCalculator()
```

Before anything else, you will need to load and clean the data with the dedicated method. For now, you will need to pass the paths to the data as argumentsg:

```
calculator.load_clean_data(
    path_to_oecd=path_to_oecd,
    path_to_twz=path_to_twz,
    path_to_twz_domestic=path_to_twz_domestic,
    path_to_twz_CIT=path_to_twz_CIT,
    inplace=True
)
```

An option to directly fetch the data online should soon be available.

You can then run any computation in which you are interested. For instance, if you want to output the same table as the one presented in the "Multilateral implementation scenario" page of the simulator, you can use:

```
calculator.output_tax_deficits_formatted()
```

## Further documentation

The full project documentation is available [here](https://eutaxobservatory.github.io/tax-deficit-simulator/) for detailed specifications.

The documentation was built with [pdoc](https://pdoc3.github.io/pdoc/).

# Contributions

So far, the code presented in this repository has not yet been optimized for performance. Feedback on how to improve computation times, the readability of the code or anything else are very much welcome! Do not hesitate to open issues in the present repository should you have any question or remark.
