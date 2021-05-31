# ----------------------------------------------------------------------------------------------------------------------
# --- Imports

# Streamlit import
import streamlit as st

# Various utils
import os
import json
from lorem_text import lorem

# Imports from other Python files
from calculator import TaxDeficitCalculator
from firm_level import correspondences, CompanyCalculator
from utils import get_table_download_button, get_report_download_button, get_appendix_download_button

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

calculator = TaxDeficitCalculator()

calculator.load_clean_data()

# ----------------------------------------------------------------------------------------------------------------------
# --- Loading the text content

path_to_text = os.path.join(path_to_dir, 'assets', 'text_content.json')

with open(path_to_text) as file:
    text_content = json.load(file)

# ----------------------------------------------------------------------------------------------------------------------
# --- Instantiating the app

st.title('Tax Deficit Simulator')

st.sidebar.image(path_to_logo, width=150)

page = st.sidebar.selectbox(
    'Choose the page to view here:',
    [
        'Description of the research',
        'Case study with one multinational',
        'Multilateral implementation scenario',
        'Partial cooperation scenario',
        'Unilateral implementation scenario'
    ]
)

path_to_css = os.path.join(path_to_dir, 'assets', 'custom_styles.css')

st.markdown('<style>' + open(path_to_css).read() + '</style>', unsafe_allow_html=True)

if page == 'Description of the research':
    st.header('Context')

    for i in range(1, 6):
        st.markdown(text_content[page][str(i)])

    st.markdown('---')

    st.header('How to use this simulator?')

    st.markdown(text_content[page]["6"])

    st.markdown('---')

    st.header('Download section')

    st.markdown(text_content[page]["7"])

    st.markdown(
        get_report_download_button(),
        unsafe_allow_html=True
    )

    st.markdown(
        get_appendix_download_button(),
        unsafe_allow_html=True
    )

elif page == 'Case study with one multinational':
    st.header('Some explanations before you get started')

    st.markdown(text_content[page]["1"])

    st.markdown('---')

    st.header('Compute potential tax revenue gains')

    st.markdown(text_content[page]["2"])

    company_name = st.selectbox(
        'Select the company that you want to study:',
        ['...'] + list(correspondences.keys())
    )

    if company_name != '...':

        company = CompanyCalculator(company_name=company_name)

        st.markdown(f'### What is the tax deficit of {company_name}?')

        st.markdown(company.get_first_sentence())

        st.markdown(text_content[page]["3"])

        st.pyplot(company.plot_tax_revenue_gains(in_app=True))

        st.markdown('---')

        st.markdown('### Where does this tax deficit come from?')

        df = company.get_tax_deficit_origins_table(minimum_ETR=0.25, formatted=True)

        st.markdown(company.get_second_sentence())

        st.write(df)

elif page == 'Multilateral implementation scenario':
    st.header('Some explanations before you get started')

    st.markdown(text_content[page]["1"])

    st.markdown(text_content[page]["2"])

    st.markdown('---')

    st.header('Simulate potential tax revenue gains')

    st.markdown(text_content[page]["3"])

    # st.markdown(text_content[page]["4"])

    slider_value = st.slider(
        'Select the minimum Effective Tax Rate (ETR):',
        min_value=10, max_value=50,
        value=25,
        step=1,
        format="%g percent",
        # help='Choose the minimum effective tax rate that headquarter countries should apply.'
    )

    output_df = calculator.output_tax_deficits_formatted(
        minimum_ETR=slider_value / 100
    )

    st.write(output_df)

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

    slider_value = st.slider(
        'Select the minimum Effective Tax Rate (ETR):',
        min_value=10, max_value=50,
        value=25,
        step=1,
        format="%g percent",
        # help='Choose the minimum effective tax rate that headquarter countries should apply.'
    )

    output_df = calculator.output_intermediary_scenario_gain_formatted_alternative(
        minimum_ETR=slider_value / 100
    )

    st.write(output_df)

    st.markdown(
        get_table_download_button(
            output_df,
            scenario=2,
            effective_tax_rate=slider_value
        ),
        unsafe_allow_html=True
    )

else:
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

    taxing_country = st.selectbox(
        'Select the country that would collect the tax deficit:',
        list(tax_deficits['Headquarter country'].values)
    )

    slider_value = st.slider(
        'Select the minimum Effective Tax Rate (ETR):',
        min_value=10, max_value=50,
        value=25,
        step=1,
        format="%g percent",
        # help=f'Choose the minimum effective tax rate that {taxing_country} should apply.'
    )

    output_df = calculator.output_unilateral_scenario_gain_formatted(
        country=taxing_country,
        minimum_ETR=slider_value / 100
    )

    st.write(output_df)

    st.markdown(
        get_table_download_button(
            output_df,
            scenario=3,
            effective_tax_rate=slider_value,
            taxing_country=taxing_country
        ),
        unsafe_allow_html=True
    )
