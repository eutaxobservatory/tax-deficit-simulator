# ----------------------------------------------------------------------------------------------------------------------
# --- Imports

# Streamlit import
import streamlit as st

# Various utils
import os
from lorem_text import lorem

# Imports from other Python files
from calculator import TaxDeficitCalculator
from firm_level import correspondences, CompanyCalculator
from utils import get_table_download_button, get_report_download_button, get_appendix_download_button

# ----------------------------------------------------------------------------------------------------------------------
# --- Setting the page configuration

path_to_dir = os.path.dirname(os.path.abspath(__file__))
path_to_logo = os.path.join(path_to_dir, 'assets', 'logo_color_RVB.jpg')

PAGE_CONFIG = {
    'page_title': 'Tax Deficit Simulator',
    'page_icon': path_to_logo
}

st.set_page_config(**PAGE_CONFIG)

# ----------------------------------------------------------------------------------------------------------------------
# --- Instantiating the calculator and loading the data

calculator = TaxDeficitCalculator()

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'data', 'test.csv')

calculator.load_clean_data(path_to_file=path)

# ----------------------------------------------------------------------------------------------------------------------
# --- Instantiating the app

st.title('Tax Deficit Simulator')

page = st.sidebar.selectbox(
    'Choose the page to view here:',
    [
        'Description of the research',
        'Case study with one multinational',
        'Multilateral implementation scenario',
        'Unilateral implementation scenario'
    ]
)

path_to_css = os.path.join(path_to_dir, 'assets', 'custom_styles.css')

st.markdown('<style>' + open(path_to_css).read() + '</style>', unsafe_allow_html=True)

if page == 'Description of the research':
    st.header('This is a page section')

    st.markdown(lorem.paragraph())

    st.markdown('---')

    st.header('This is another page section')

    st.markdown(lorem.paragraph())

    st.markdown('---')

    st.header('Download section')

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

    st.markdown(lorem.paragraph())

    st.markdown('---')

    st.header('Compute potential tax revenue gains')

    company_name = st.selectbox(
        'Select the company that you want to study:',
        ['...'] + list(correspondences.keys())
    )

    if company_name != '...':

        company = CompanyCalculator(company_name=company_name)

        # st.markdown(company.get_first_sentence())

        st.pyplot(company.plot_tax_revenue_gains(in_app=True))

        st.markdown('---')

        st.header('Where does this tax deficit come from?')

        df = company.get_tax_deficit_origins_table(minimum_ETR=0.25, formatted=True)

        st.markdown(company.get_second_sentence())

        st.write(df)

elif page == 'Multilateral implementation scenario':
    st.header('Some explanations before you get started')

    st.markdown(lorem.paragraph())

    st.markdown('---')

    st.header('Simulate potential tax revenue gains')

    slider_value = st.slider(
        'Select the minimum Effective Tax Rate (ETR):',
        min_value=10, max_value=50,
        value=25,
        step=1,
        format="%g percent",
        # help='Choose the minimum effective tax rate that headquarter countries should apply.'
    )

    output_df = calculator.output_all_tax_deficits_cleaned(
        minimum_ETR=slider_value / 100,
        verbose=0
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

else:
    tax_deficits = calculator.compute_all_tax_deficits(verbose=0)

    tax_deficits.sort_values(by='Headquarter country', inplace=True)

    st.header('Some explanations before you get started')

    st.markdown(lorem.paragraph())

    st.markdown('---')

    st.header('Simulate potential tax revenue gains')

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

    output_df = calculator.output_second_scenario_gain_cleaned(
        country=taxing_country,
        minimum_ETR=slider_value / 100
    )

    st.write(output_df)

    st.markdown(
        get_table_download_button(
            output_df,
            scenario=2,
            effective_tax_rate=slider_value,
            taxing_country=taxing_country
        ),
        unsafe_allow_html=True
    )
