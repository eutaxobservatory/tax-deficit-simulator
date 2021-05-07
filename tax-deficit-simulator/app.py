# ----------------------------------------------------------------------------------------------------------------------
# --- Imports

# Streamlit import
import streamlit as st

# Various utils
import os
from lorem_text import lorem

# Imports from other Python files
from calculator import TaxDeficitCalculator
from utils import get_table_download_link

# ----------------------------------------------------------------------------------------------------------------------
# --- Instantiating the calculator and loading the data

calculator = TaxDeficitCalculator()

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'data', 'test.csv')

calculator.load_clean_data(path_to_file=path)

# ----------------------------------------------------------------------------------------------------------------------
# --- Instantiating the app

st.title('Tax Deficit Simulator')

st.header('Some explanations before you get started')

st.markdown(lorem.paragraph())

st.markdown('---')

st.header('Simulate potential tax revenue gains')

slider_value = st.slider(
    'Minimum ETR',
    min_value=10, max_value=50,
    value=25,
    step=1,
    format="%g percent",
    # help='Choose the minimum effective tax rate that headquarter countries should apply.'
)

output_df = calculator.compute_all_tax_deficits(
    minimum_ETR=slider_value / 100,
    verbose=0
)

st.write(output_df)

st.markdown('---')

st.header('Download the result')

st.markdown(get_table_download_link(output_df), unsafe_allow_html=True)






