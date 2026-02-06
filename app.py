from dash import Dash, html, dcc, dash_table, Input, Output
import pandas as pd
import backend  # Assuming backend.py is in the same directory
import plotly.express as px

# Initialize the Dash app
app = Dash(__name__)
app.title = "Clinical Trial Data Dashboard"

# Load data using backend functions
backend.initialize_database()
backend.load_data(backend.csv_file)

# Grab DataFrames
frequency_df = backend.get_frequency()
subset_df, statistics_df = backend.get_statistics()
baseline_df = backend.get_specific_subset_data()

# Preparing table for part 2
frequency_display = frequency_df[['sample', 'total_count', 'population', 'count', 'percentage']]

# Preparing metrics for part 4
total_patients = len(baseline_df)
males = len(baseline_df[baseline_df['sex'] == 'M'])
females = len(baseline_df[baseline_df['sex'] == 'F'])
responders = len(baseline_df[baseline_df['response'] == 'yes'])
non_responders = len(baseline_df[baseline_df['response'] == 'no'])

# Layout of the app
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'}, children=[
    html.H1("Clinical Trial Data Dashboard", style={'textAlign': 'center', 'color': "#3A75AF"}),
    html.P("Analysis of Melanoma / Miraclib / PBMC Samples", style={'textAlign': 'center', 'fontSize': '18px', 'color': "#000000"}),

    html.Hr(),

    dcc.Tabs([
        # Tab for part 2: frequency
        dcc.Tab(label='Cell Populaion Frequencies', children=[
            html.H3("Relative Frequencies of Cell Populations"),
            html.P("This table shows the relative frequencies of different cell populations across samples."),

            dash_table.DataTable(
                data=frequency_display.to_dict('records'),
                columns=[{"name": i, "id": i} for i in frequency_display.columns],
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={'backgroundColor': '#3A75AF', 'color': 'white', 'fontWeight': 'bold'},
                export_format='csv'
            )
        ]),

        # Tab for part 3: statistics
        dcc.Tab(label='Statistical Analysis', children=[
            html.Div(style={'padding': '10px'}, children=[
                html.Div([
                    html.H3("Responder vs. Non-Responder Statistical Analysis"),
                    html.Label("Select Cell Population to View Statistics:"),
                    dcc.Dropdown(
                        id='population-dropdown',
                        options=sorted(subset_df['population'].unique()),
                        value='b_cell',
                        clearable=False,
                        style={'width': '300px'}
                    ),
                    dcc.Graph(id='box-plot')
                ]),

                html.Hr(),

                html.H3("Statistical Summary Table"),
                html.P("Comparision using Welch's t-test or Mann-Whitney U test based on normality."),

                dash_table.DataTable(
                    data=statistics_df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in statistics_df.columns],
                    style_cell={'textAlign': 'left', 'padding': '5px'},
                    style_header={'backgroundColor': '#3A75AF', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{significant} eq 1'},
                            'backgroundColor': '#d4edda',
                            'color': '#155724'
                        }
                    ]
                )
            ])
        ]),

        # Tab for part 4: baseline characteristics
        dcc.Tab(label='Baseline Characteristics', children=[
            html.Div(style={'padding': '10px'}, children=[
                html.H3("Baseline Demographics (Time = 0)"),

                html.Div(style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '20px'}, children=[
                    html.Div(style={'border': '1px solid #ccc', 'borderRadius': '5px', 'padding': '10px', 'width': '33%', 'textAlign': 'center'}, children=[
                        html.H2(total_patients, style={'margin': '0', 'color': '#3A75AF'}),
                        html.P("Total Patients", style={'margin': '0'})
                    ]),
                    html.Div(style={'border': '1px solid #ccc', 'borderRadius': '5px', 'padding': '10px', 'width': '33%', 'textAlign': 'center'}, children=[
                        html.H2(f"{males}M / {females}F", style={'margin': '0', 'color': '#3A75AF'}),
                        html.P("Gender Distribution", style={'margin': '0'})
                    ]),
                    html.Div(style={'border': '1px solid #ccc', 'borderRadius': '5px', 'padding': '10px', 'width': '33%', 'textAlign': 'center'}, children=[
                        html.H2(f"{responders} vs {non_responders}", style={'margin': '0', 'color': '#3A75AF'}),
                        html.P("Responders vs Non-Responders", style={'margin': '0'})
                    ]),
                ]),

                html.H4("Baseline Data Table"),
                dash_table.DataTable(
                    data=baseline_df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in baseline_df.columns],
                    page_size=10,
                    style_cell={'textAlign': 'left', 'padding': '5px'},
                    style_header={'backgroundColor': '#3A75AF', 'color': 'white', 'fontWeight': 'bold'},
                )
            ])
        ]),
    ])
])

# Callbacks
@app.callback(
    Output('box-plot', 'figure'),
    Input('population-dropdown', 'value')
)
def update_box_plot(selected_population):
    filtered_data = subset_df[subset_df['population'] == selected_population]

    fig = px.box(
        filtered_data,
        x='response',
        y='percentage',
        color='response',
        points='all',
        title=f'Percentage Distribution of {selected_population} by Response',
        color_discrete_map={'yes': "green", 'no': "red"}
    )
    return fig

# Run server
if __name__ == '__main__':
    app.run(debug=True)