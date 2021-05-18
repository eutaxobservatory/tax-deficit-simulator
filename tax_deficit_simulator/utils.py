import base64
import os

path_to_files = os.path.dirname(os.path.abspath(__file__))
path_to_files = os.path.join(path_to_files, 'files')


def get_table_download_button(df, scenario, effective_tax_rate, taxing_country=None):

    csv = df.to_csv(index=False)

    b64 = base64.b64encode(csv.encode()).decode()

    href = f'<a href="data:file/csv;base64,{b64}"'

    if scenario == 1:
        href += f' download="first_scenario_{effective_tax_rate}_perc.csv">'

    elif scenario == 2:
        taxing_country = taxing_country.lower().replace(' ', '_')

        if 'china' in taxing_country:
            taxing_country = 'china'

        href += f' download="second_scenario_{taxing_country}_{effective_tax_rate}_perc.csv">'

    else:
        raise Exception('Value not accepted for the scenario argument.')

    href += '<input type="button" value="Click here to download the table" class="download-button table"></a>'

    return href


def get_report_download_button():

    path = os.path.join(path_to_files, 'test.pdf')

    with open(path, 'rb') as file:
        report_content = file.read()

    b64 = base64.b64encode(report_content).decode()

    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(path)}">'

    href += '<input type="button" value="Click here to download the full-text report (PDF)" '

    href += 'class="download-button pdf"></a>'

    return href


def get_appendix_download_button():

    path = os.path.join(path_to_files, 'test.xlsx')

    with open(path, 'rb') as file:
        excel_content = file.read()

    b64 = base64.b64encode(excel_content).decode()

    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(path)}">'

    href += '<input type="button" value="Click here to download the appendix tables (Excel)" '

    href += 'class="download-button excel"></a>'

    return href
