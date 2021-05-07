import base64

def get_table_download_link(df):

    csv = df.to_csv(index=False)

    b64 = base64.b64encode(csv.encode()).decode()

    href = f'<a href="data:file/csv;base64,{b64}" download="simulator_output.csv">'

    href += 'Click on this link to download the output (as a .csv file)</a>'

    return href
