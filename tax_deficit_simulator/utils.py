import base64
import os

def get_table_download_link(df, scenario, effective_tax_rate):

    csv = df.to_csv(index=False)

    b64 = base64.b64encode(csv.encode()).decode()

    href = f'<a href="data:file/csv;base64,{b64}"'

    if scenario == 1:
        href += f' download="first_scenario_{effective_tax_rate}_perc.csv">'

    elif scenario == 2:
        href += f' download="second_scenario_{effective_tax_rate}_perc.csv">'

    else:
        raise Exception('Value not accepted for the scenario argument.')

    href += '<input type="button" value="Click here to download the table" class="download-button-table"></a>'

    return href
