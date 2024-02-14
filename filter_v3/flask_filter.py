import pandas as pd
import json
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

df = pd.read_csv(r'C:\Users\PriyanshuGhosh\Documents\fashion_ads.csv')

def dynamic_filter(df, selected_filters, selected_date, selected_kpi):
    df_sel = df.copy()

    for filter_column, filter_values in selected_filters.items():
        if filter_values:
            df_sel = df_sel[df_sel[filter_column].isin(filter_values)]

    last = [key for key, val in selected_filters.items() if len(val) > 0]
    if last:
        result = list(selected_filters.keys())[list(selected_filters.keys()).index(last[-1]) + 1:-1]
    else:
        result = list(selected_filters.keys())

    df1 = df_sel[result].copy()
    df1['Year'] = pd.to_datetime(df_sel[selected_date['date_column']]).dt.year

    for i in selected_kpi:
        df1[i] = df_sel[i]

    return df1, result

def calculate_data(df1, result, selected_date, selected_kpi, selected_type):
    combined_data = {'KPI Overview': {}, 'Waterfall Data': {}, 'Pie Chart Data': {}}

    for kpi, selected_type in zip(selected_kpi, selected_type):

        if selected_type == "Average":
            total_1 = df1[df1['Year'] == selected_date['start']][kpi].mean()
            total_2 = df1[df1['Year'] == selected_date['end']][kpi].mean()
            total = df1[df1['Year'].between(selected_date['start'], selected_date['end'])][kpi].mean()

        else:
            total_1 = df1[df1['Year'] == selected_date['start']][kpi].sum()
            total_2 = df1[df1['Year'] == selected_date['end']][kpi].sum()
            total = df1[df1['Year'].between(selected_date['start'], selected_date['end'])][kpi].sum()

        change_percentage = ((total_2 - total_1) / total_1) * 100 if total_1 != 0 else 0

        combined_data['KPI Overview'][f'{selected_type} {kpi}'] = f"{total:.2f}"
        combined_data['KPI Overview'][f'{selected_type} {kpi} Change'] = f"{change_percentage:.2f}%"

        waterfall_data_kpi = {}

        for i in result:
            grouped_data_1 = df1[df1['Year'] == selected_date['start']].groupby(i)[kpi].sum()
            grouped_data_2 = df1[df1['Year'] == selected_date['end']].groupby(i)[kpi].sum()

            net_sum_1 = grouped_data_1.sum()
            net_sum_2 = -(grouped_data_2.sum())

            column_data = {
                f"Total {kpi} in {selected_date['start']}": float(net_sum_1),
            }

            for group, diff in zip(grouped_data_1.index, (grouped_data_2 - grouped_data_1)):
                column_data[group] = float(diff)

            column_data[f"Total {kpi} in {selected_date['end']}"] = float(net_sum_2)

            waterfall_data_kpi[i] = column_data

        combined_data['Waterfall Data'][f'Total {kpi}'] = waterfall_data_kpi

        pie_chart_data = {}
        for i in result:
            pie_data = df1.groupby(i)[kpi].sum()
            pie_chart_data[i] = {group: float(value) for group, value in pie_data.items()}

        combined_data['Pie Chart Data'][f'Total {kpi}'] = pie_chart_data

    json_data = json.dumps(combined_data, indent=2)
    print(json_data)
    return json_data

@app.route('/')
def index():
    return render_template('index1.html')

@app.route('/filter-data', methods=['POST'])
def filter_data():
    data = request.get_json()
    print(data)
    selected_filters = data.get('filters')
    selected_date = data.get('date')
    selected_kpi = data.get('kpi')
    selected_type = data.get('type')

    filtered_df, result = dynamic_filter(df, selected_filters, selected_date, selected_kpi)
    json_data = calculate_data(filtered_df, result, selected_date, selected_kpi, selected_type)

    # Save JSON data to a file
    file_name = 'filtered_data.json'
    file_path = os.path.join(app.root_path, file_name)
    with open(file_path, 'w') as file:
        file.write(json_data)

    return jsonify(json_data)

if __name__ == '__main__':
    app.run(debug=True)
    