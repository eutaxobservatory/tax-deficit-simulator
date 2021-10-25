# ----------------------------------------------------------------------------------------------------------------------
# --- Imports

# Streamlit import
import streamlit as st

# Various utils
import os
import json

# Imports from other Python files
from calculator import TaxDeficitCalculator
from firm_level import correspondences, CompanyCalculator
from utils import get_table_download_button, get_report_download_button, get_carve_outs_note_download_button

# ----------------------------------------------------------------------------------------------------------------------
# --- Setting the page configuration

path_to_dir = os.path.dirname(os.path.abspath(__file__))
path_to_logo = os.path.join(path_to_dir, 'assets', 'logo_color_RVB.jpg')
path_to_small_logo = os.path.join(path_to_dir, 'assets', 'small_logo.jpg')

PAGE_CONFIG = {
    'page_title': 'Tax Deficit Simulator',
    'page_icon': path_to_small_logo
}

st.set_page_config(**PAGE_CONFIG)

# ----------------------------------------------------------------------------------------------------------------------
# --- Instantiating the calculator and loading the data

# We instantiate the calculator following the methodology for our benchmark estimates
calculator = TaxDeficitCalculator(
    year=2017,
    sweden_treatment='adjust', belgium_treatment='none', use_adjusted_profits=True,
    average_ETRs=True,
    de_minimis_exclusion=False,
    add_AUT_AUT_row=True,
)

calculator.load_clean_data()

# ----------------------------------------------------------------------------------------------------------------------
# --- Loading the text content

path_to_text = os.path.join(path_to_dir, 'assets', 'text_content.json')

with open(path_to_text) as file:
    text_content = json.load(file)

# ----------------------------------------------------------------------------------------------------------------------
# --- Instantiating the app

# Main title of the app
st.title('Tax Deficit Simulator')

# Sidebar logo and page selection dropdown
st.sidebar.image(path_to_logo, width=150)

page = st.sidebar.selectbox(
    'Choose the page to view here:',
    [
        'Description of the research',
        'Case study with one multinational',
        'Multilateral implementation scenario',
        'Partial cooperation scenario',
        'Unilateral implementation scenario',
        'Substance-based carve-outs'
    ]
)

# These few lines allow to add the custom .css styles to the app
path_to_css = os.path.join(path_to_dir, 'assets', 'custom_styles.css')

st.markdown('<style>' + open(path_to_css).read() + '</style>', unsafe_allow_html=True)

# Defining the content of the different pages one by one
if page == 'Description of the research':
    # We start with the description of the research
    st.header('Context')

    # Adding paragraphs from the pre-loaded text content
    for i in range(1, 6):
        st.markdown(text_content[page][str(i)])

    st.markdown('---')

    st.header('How to use this simulator?')

    st.markdown(text_content[page]["6"])

    st.markdown('---')

    st.header('Download section')

    # Download button for the PDF full-text version of the report
    st.markdown(
        get_report_download_button(),
        unsafe_allow_html=True
    )

    # Download button for the carve-outs note (PDF)
    st.markdown(
        get_carve_outs_note_download_button(),
        unsafe_allow_html=True
    )

    # Download button for the 2017 update note (PDF)
    # TO BE ADDED

elif page == 'Case study with one multinational':
    # We move to the case studies
    st.header('Some explanations before you get started')

    st.markdown(text_content[page]["1"])

    st.markdown('---')

    st.header('Compute potential tax revenue gains')

    st.markdown(text_content[page]["2"])

    # Company selection dropdown (initially set at the value '...')
    company_name = st.selectbox(
        'Select the company that you want to study:',
        ['...'] + list(correspondences.keys())
    )

    if company_name != '...':
        # Taking the company name from the dropdown, we instantiate the CompanyCalculator object
        company = CompanyCalculator(company_name=company_name)

        st.markdown(f'### What is the tax deficit of {company_name}?')

        # We use the get_first_sentence method of the CompanyCalculator object to fill-in the text content
        st.markdown(company.get_first_sentence())

        st.markdown(text_content[page]["3"])

        # We plot the bar chart with the company's tax deficit computed at various benchmark minimum ETRs
        st.pyplot(company.plot_tax_revenue_gains(in_app=True))

        st.markdown('---')

        st.markdown('### Where does this tax deficit come from?')

        # We display the table with all details on the 25% tax deficit of the company
        df = company.get_tax_deficit_origins_table(minimum_ETR=0.25, formatted=True)

        st.markdown(company.get_second_sentence())

        st.write(df)

        st.markdown('---')

        st.markdown('### How important is the minimum effective tax rate?')

        st.markdown(company.get_third_sentence())

        # Slider for the user to select a minimum effective tax rate between 10% and 50%
        slider_value = st.slider(
            'Select the minimum Effective Tax Rate (ETR):',
            min_value=10, max_value=50,
            value=15,
            step=1,
            format="%g percent",
        )

        # We use the CompanyCalculator object to compute the tax deficit of the company and get its breakdown
        output_df = company.get_tax_deficit_origins_table(
            minimum_ETR=slider_value / 100,
            formatted=True
        )

        # We display the table
        st.write(output_df)

        # Button to download the table in .csv format
        st.markdown(
            get_table_download_button(
                output_df,
                scenario=0,
                effective_tax_rate=slider_value,
                company=company_name
            ),
            unsafe_allow_html=True
        )

elif page == 'Multilateral implementation scenario':
    # We now move to the multilateral implementation scenario
    st.header('Some explanations before you get started')

    st.markdown(text_content[page]["1"])

    st.markdown(text_content[page]["2"])

    st.markdown('---')

    st.header('Simulate potential tax revenue gains')

    st.markdown(text_content[page]["3"])

    # Slider for the user to choose the minimum ETR applied multilaterally
    slider_value = st.slider(
        'Select the minimum Effective Tax Rate (ETR):',
        min_value=10, max_value=50,
        value=15,
        step=1,
        format="%g percent",
    )

    # We compute the corporate tax revenue gains of each headquarter country
    output_df = calculator.output_tax_deficits_formatted(
        minimum_ETR=slider_value / 100
    )

    # And output the resulting table
    st.write(output_df)

    # Button to download the table as a .csv file
    st.markdown(
        get_table_download_button(
            output_df,
            scenario=1,
            effective_tax_rate=slider_value
        ),
        unsafe_allow_html=True
    )

elif page == 'Partial cooperation scenario':
    st.header('Some explanations before you get started')

    st.markdown(text_content[page]["1"])

    st.markdown(text_content[page]["2"])

    st.markdown('---')

    st.header('Simulate potential tax revenue gains')

    st.markdown(text_content[page]["3"])

    # Slider for the user to choose the minimum effective tax rate applied by EU-27 countries
    slider_value = st.slider(
        'Select the minimum Effective Tax Rate (ETR):',
        min_value=10, max_value=50,
        value=15,
        step=1,
        format="%g percent",
    )

    # We compute the corporate tax revenue gains of EU-27 countries in this scenario, at the selected minimum ETR
    output_df = calculator.output_intermediary_scenario_gain_formatted(
        minimum_ETR=slider_value / 100
    )

    # And output the resulting table
    st.write(output_df)

    # Button to download the table as a .csv file
    st.markdown(
        get_table_download_button(
            output_df,
            scenario=2,
            effective_tax_rate=slider_value
        ),
        unsafe_allow_html=True
    )

elif page == 'Unilateral implementation scenario':
    # We first use the output_tax_deficits_formatted method to build the list of in-sample countries
    tax_deficits = calculator.output_tax_deficits_formatted()

    tax_deficits.sort_values(by='Headquarter country', inplace=True)

    tax_deficits = tax_deficits[
        ~tax_deficits['Headquarter country'].isin(['Total - EU27', 'Total - Whole sample'])
    ].copy()

    st.header('Some explanations before you get started')

    st.markdown(text_content[page]["1"])

    st.markdown(text_content[page]["2"])

    st.markdown('---')

    st.header('Simulate potential tax revenue gains')

    st.markdown(text_content[page]["3"])

    # Dropdown allowing the user to select which of the in-sample countries is the first mover
    taxing_country = st.selectbox(
        'Select the country that would collect the tax deficit:',
        list(tax_deficits['Headquarter country'].values)
    )

    # Slider for the user to choose the minimum effective tax rate applied by this first mover
    slider_value = st.slider(
        'Select the minimum Effective Tax Rate (ETR):',
        min_value=10, max_value=50,
        value=15,
        step=1,
        format="%g percent",
    )

    # We compute the corporate tax revenue gain for this country and determine from which multinationals it is collected
    output_df = calculator.output_unilateral_scenario_gain_formatted(
        country=taxing_country,
        minimum_ETR=slider_value / 100
    )

    # We output the resulting table
    st.write(output_df)

    # Button to download the table as a .csv file
    st.markdown(
        get_table_download_button(
            output_df,
            scenario=3,
            effective_tax_rate=slider_value,
            taxing_country=taxing_country
        ),
        unsafe_allow_html=True
    )

else:

    st.header(
        'Some explanations before you get started',
        anchor='carve_outs_page'
    )

    st.markdown(text_content[page]["1"])
    st.markdown(text_content[page]["2"])

    st.markdown('---')

    st.header('Let us take a simple example')

    for i in range(3, 10):
        st.markdown(text_content[page][str(i)])

    st.markdown('---')

    st.header('Simulate the impact of carve-outs on revenue gains')

    st.markdown(text_content[page]["10"])

    # Slider for the user to choose the minimum effective tax rate
    slider_value = st.slider(
        'Select the minimum Effective Tax Rate (ETR):',
        min_value=10, max_value=50,
        value=15,
        step=1,
        format="%g percent",
    )

    st.markdown(text_content[page]["11"])

    # Slider for the user to choose the carve-outs rate
    slider_value_co_assets_rate = st.slider(
        'Select the tangible assets carve-out rate:',
        min_value=0.0, max_value=10.0,
        value=8.0,
        step=0.2,
        format="%g percent",
    )

    slider_value_co_payroll_rate = st.slider(
        'Select the payroll carve-out rate:',
        min_value=0.0, max_value=10.0,
        value=10.0,
        step=0.2,
        format="%g percent",
    )

    calculator_carve_out = TaxDeficitCalculator(
        year=2017,
        sweden_treatment='adjust', belgium_treatment='none', use_adjusted_profits=True,
        average_ETRs=True,
        carve_outs=True,
        carve_out_rate_assets=slider_value_co_assets_rate / 100,
        carve_out_rate_payroll=slider_value_co_payroll_rate / 100,
        depreciation_only=False, exclude_inventories=False, ex_post_ETRs=False,
        de_minimis_exclusion=True,
        add_AUT_AUT_row=True,
    )

    st.markdown(text_content[page]["12"])

    st.markdown(text_content[page]["13"])

    calculator_carve_out.load_clean_data()

    # We compute corporate tax revenue gains with and without substance-based carve-out, as well as the % change
    output_df = calculator_carve_out.assess_carve_out_impact_formatted(
        minimum_ETR=slider_value / 100
    )

    # And output the resulting table
    st.write(output_df)

    # Button to download the table as a .csv file
    st.markdown(
        get_table_download_button(
            output_df,
            scenario=4,
            effective_tax_rate=slider_value,
            carve_out_rate_assets=slider_value_co_assets_rate,
            carve_out_rate_payroll=slider_value_co_payroll_rate
        ),
        unsafe_allow_html=True
    )
