# Main results

This sub-folder provides you with the main results of our simulations in Excel format.

Note that all estimates are provided in 2018 current USD (i.e., before the extrapolation to 2023 results applied in the *Global Tax Evasion Report* of October 2023).

## Scenarios covered

The following scenarios are included and determine the beginning of the Excel file name:

- Headquarter or full IIR scenario ("HQscenario_" prefix): tax deficits are entirely collected by the country of residence of the ultimate parent entity and only EU Member-States collect the domestic tax deficit of their multinationals;
- Full QDMTT scenario ("QDMTTscenario_" prefix): tax deficits are entirely collected by the jurisdictions where the under-taxed profits are booked and only EU Member-States collect the domestic tax deficit of their multinationals;
- Partial cooperation scenarios ("partialCoop_" prefix):

    - a set of implementing jurisdictions collect the tax deficits of their headquartered multinationals and share, based on the distribution of unrelated-party revenues, the tax deficits of multinationals headquartered in non-implementing jurisdictions;
    - there are two main variants for this scenario:

        - "EUOnly_" in the file name: only EU Member-States implement the agreement and collect the foreign and domestic tax deficits of their headquartered multinationals as well as foreign firms' foreign and domestic tax deficits;
        - "EUandOthers_" in the file name: (i) EU Member-States implement the agreement and collect the foreign and domestic tax deficits of their headquartered multinationals, (ii) a set of non-EU implementing jurisdictions collect the foreign tax deficits of their headquartered multinationals; (iii) EU and non-EU implementing jurisdictions share the foreign tax deficits of multinationals headquartered in a non-implementing country, (iv) only EU Member-States collect the domestic tax deficits of these firms.

- Unilateral implementation scenario (`unilateralScenario.xlsx`): each country is separately assumed to collect the tax deficits of its headquartered multinationals as well as a portion, still based on unrelated-party revenues, of foreign firms' tax deficits;
- Full sales apportionment scenario (`fullSalesApportionment.xlsx`): all tax deficits, including domestic ones, are allocated to a collecting jurisdiction according to the distribution of unrelated-party revenues.

## Headquarter and QDMTT scenarios

For the headquarter and QDMTT scenario, there are three distinct Excel files distinguished by a suffix:

- "noCO" suffix: no substance-based carve-outs are simulated;
- "firstYearCO" suffix: substance-based carve-outs are simulated with the rates of the first year of implementation (10% of payroll and 8% of tangible assets);
- "longTermCO" suffix: substance-based carve-outs are simulated with the rates of the tenth year of implementation ("long-term" rates, 5% of payroll and 5% of tangible assets).

In each file, a sheet corresponds to a given minimum effective tax rate. When the rate is not explicitly stated as part of the sheet name, it corresponds to a 15% rate. "15% with increment" as a sheet name means that a 15% minimum rate was used but all effective tax rates were raised by 2 percentage points to approximate the effect of the specific treatment of non-refundable tax credits.

In a given sheet, the country name and ISO alpha-3 codes are provided. The last column provides the total tax deficit allocated to the country considered. The other columns split this total across collection instruments:

- "collected_through_foreign_IIR": IIR applying to multinationals' foreign profits;
- "collected_through_domestic_IIR": IIR applying to multinationals' domestic profits;
- "collected_through_foreign_QDMTT": QDMTT applying to multinationals' foreign profits;
- "collected_through_domestic_QDMTT": QDMTT applying to multinationals' domestic profits;
- "collected_through_foreign_UTPR": UTPR applying to multinationals' foreign profits;
- "collected_through_domestic_UTPR": UTPR applying to multinationals' domestic profits.

For instance, in a headquarter scenario result file, only the first two of these columns contain non-zero values and values are all zeros for non-EU countries in the "collected_through_domestic_IIR" column, since they are assumed not to collect the domestic tax deficits of their multinationals.

## Partial cooperation scenarios

For each of the two partial cooperation scenarios described above, there are three distinct Excel files distinguished by a suffix. Rather than substance-based carve-outs, the suffix determines whether the collection of foreign multinationals' tax deficits is conditioned on a statutory corporate income tax rate threshold. More precisely:

- "noStatRateCond" suffix: this case corresponds to the base scenarios described above, in which implementing countries share the whole tax deficits of the multinationals headquartered in non-implementing jurisdictions;
- "20statRateCond" suffix: in this simulation, we replicate the transitional UTPR safe harbour introduced in the OECD's Administrative Guidance of July 2023 ([link](https://www.oecd.org/tax/beps/administrative-guidance-global-anti-base-erosion-rules-pillar-two-july-2023.pdf)) according to which the domestic tax deficits of the multinationals headquartered in non-implementing jurisdictions with a statutory rate above or equal to 20% cannot be collected by other countries;
- "20statRateCond_withForeign" suffix: eventually, we extend the condition above to foreign tax deficits such that none of the tax deficits (domestic and foreign) of the multinationals headquartered in non-implementing jurisdictions with a statutory rate above or equal to 20% can be collected by other countries.

In each file, a sheet corresponds to an assumption about substance-based carve-outs, while the minimum effective tax rate is always 15%. The three possibilities are the same as above:

- "noCO" suffix: no substance-based carve-outs are simulated;
- "firstYearCO" suffix: substance-based carve-outs are simulated with the rates of the first year of implementation (10% of payroll and 8% of tangible assets);
- "longTermCO" suffix: substance-based carve-outs are simulated with the rates of the tenth year of implementation ("long-term" rates, 5% of payroll and 5% of tangible assets).

The structure in a given sheet follows that of the headquarter and QDMTT scenarios. The country name and ISO alpha-3 codes are provided, the last column provides the total tax deficit allocated to the country considered, and the other columns split this total across collection instruments.

## Unilateral and full sales apportionment scenarios

For these scenarios, a unique variant is provided.

In the only sheet of both Excel files, long-term substance-based carve-outs (5% of payroll and 5% of tangible assets) apply and the minimum rate is 15%.

However, the structure within a sheet differs from the above. As before, the country name and ISO alpha-3 codes are provided and the last column ("total") provides the total tax deficit allocated to the country considered. This total is split into five items but before we describe them in details, it is necessary to give additional explanations. In both scenarios, a part of or all tax deficits are allocated to the relevant collecting country based on unrelated-party revenues (the code allowing for other options), which are observed in country-by-country report statistics. However, these data do not provide a sufficient mapping of sales for all headquarter countries in our sample. For the "problematic" parents, an extrapolation is required that is described in the technical note accompanying our October 2023 results (see `files/methodology/Data and code update (2023) - Methodological note.pdf` in this repository). The sub-totals in the Excel files essentially distinguish the revenue gains attributed based on an observed allocation key, from those that rely on extrapolations.

- "directly_allocated": tax deficits collected from multinationals headquartered in jurisdictions for which the allocation key is directly observed in country-by-country report statistics (including possibly the collecting country itself);
- "directly_allocated_dom": tax deficits collected from multinationals headquartered in the collecting country if its allocation key is directly observed in country-by-country report statistics, zero otherwise;
- "directly_allocated_for": tax deficits collected from multinationals headquartered in *foreign* jurisdictions for which the allocation key is directly observed in country-by-country report statistics (i.e., excluding the collecting country itself);
- "imputed_foreign": tax deficits collected from multinationals headquartered in *foreign* jurisdictions for which the allocation key is extrapolated;
- "imputed_domestic": tax deficits collected from multinationals headquartered in the collecting country if its allocation key is extrapolated, zero otheriwse.

As a consequence, the following equalities must hold:

```
directly_allocated" = directly_allocated_dom + directly_allocated_for
total = directly_allocated + imputed_foreign + imputed_domestic
```

Besides, we cannot have: `directly_allocated_dom > 0 & imputed_domestic > 0`.
-
