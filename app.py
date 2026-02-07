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
frequency_display['percentage'] = frequency_display['percentage'].map("{:.2f}%".format)

# Desired order for part 3
desired_order = [
    'population',
    'p-value',
    'adjusted p-value',
    'significant',
    'effect size',
    'responder mean',
    'responder median',
    'non-responder mean',
    'non-responder median',
    'test used',
    'test statistic'
]

# Preparing metrics for part 4
total_patients = len(baseline_df)
males = len(baseline_df[baseline_df['sex'] == 'M'])
females = len(baseline_df[baseline_df['sex'] == 'F'])
responders = len(baseline_df[baseline_df['response'] == 'yes'])
non_responders = len(baseline_df[baseline_df['response'] == 'no'])

# Layout of the app
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'}, children=[
    html.H1("Clinical Trial Data Dashboard", style={'textAlign': 'center', 'color': "#3A75AF"}),

    html.Hr(),

    dcc.Tabs([
        # Tab for part 2: frequency
        dcc.Tab(label='Cell Population Frequencies', children=[
            html.H3("Relative Frequencies of Cell Populations"),
            html.P("This table shows the relative frequencies of different cell populations across samples."),
        
            dash_table.DataTable(
                data=frequency_display.to_dict('records'),
                columns=[{"name": i, "id": i} for i in frequency_display.columns],
                page_size=20,
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
                        options=[{'label': 'All Populations', 'value': 'all'}] + 
                                [{'label': i, 'value': i} for i in sorted(subset_df['population'].unique())],
                        value='all',  # Default value in dropdown
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
                    columns=[{"name": i, "id": i} for i in desired_order if i in statistics_df.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '5px'},
                    style_header={'backgroundColor': '#3A75AF', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{significant} eq 1'},
                            'backgroundColor': '#d4edda',
                            'color': '#155724'
                        }
                    ]
                ),

                html.Div(style={'backgroundColor': '#f8d7da', 'color': '#721c24', 'padding': '10px', 'borderRadius': '5px', 'marginTop': '20px'}, children=[
                    html.H4("Statistical Interpretation:", style={'marginTop': '0'}),
                    dcc.Markdown('''
                    * **Overall Findings:** There are no statistically signficant differences in baseline PBMC cell frequencies between responders and non-responders in melanoma patients treated with Miraclib.
                    * **Specific Observations:** Although CD4 T-cells showed a potential trends with a raw p-value of 0.0134, it was not statistically significant after corrrecting for multiple testing (adjusted p-value of 0.067). The effect size of -0.0644 was negligible, indicating minimal practical difference between groups. Other cell populations did not show any statistically significant differences, with all adjusted p-values well above the 0.05 threshold and small effect sizes.
                    * **Methodoloy Note:** The Shapiro-Wilk test indicated that the data did not meet normality assumptions, leading to the use of the Mann-Whitney U test for non-parametric comparisons.
                    * **Conclusion:** These results suggest that baseline PBMC cell frequencies may not be reliable predictors of treatment response in this specific clinical context. Further research with larger sample sizes or additional biomarkers may be necessary to identify factors influencing treatment outcomes.
                    ''')
                ])
            ])
        ]),

        # Tab for part 4: baseline characteristics
        dcc.Tab(label='Baseline Characteristics', children=[
            html.Div(style={'padding': '10px'}, children=[
                html.H3("Baseline Demographics (Time = 0)"),
                html.P("Filter to explore specific subgroups."),

                html.Div(style={'display': 'flex', 'gap': '50px', 'marginBottom': '20px', 'padding': '10px'}, children=[
                    html.Div([
                        html.Label("Filter by Project:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='project-filter',
                            options=sorted(baseline_df['project'].unique()),
                            multi=True,
                            placeholder="All Projects"
                        )
                    ], style={'width': '30%', 'textAlign': 'center'}),

                    html.Div([
                        html.Label("Filter by Sex:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='sex-filter',
                            options=['M', 'F'],
                            multi=True,
                            placeholder="All Sexes"
                        )
                    ], style={'width': '30%', 'textAlign': 'center'}),

                    html.Div([
                        html.Label("Filter by Response:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='response-filter',
                            options=['yes', 'no'],
                            multi=True,
                            placeholder="All Responses"
                        )
                    ], style={'width': '30%', 'textAlign': 'center'})
                ]),

                html.Div(style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '20px'}, children=[
                    html.Div(style={'border': '1px solid #ccc', 'borderRadius': '10px', 'padding': '10px', 'width': '25%', 'textAlign': 'center'}, children=[
                        html.H2(id='metric-total', style={'margin': '0', 'color': '#3A75AF'}),
                        html.P('Samples Selected')
                    ]),
                    html.Div(style={'border': '1px solid #ccc', 'borderRadius': '10px', 'padding': '10px', 'width': '25%', 'textAlign': 'center'}, children=[
                        html.H2(id='metric-sex', style={'margin': '0', 'color': '#3A75AF'}),
                        html.P('Gender Split')
                    ]),
                    html.Div(style={'border': '1px solid #ccc', 'borderRadius': '10px', 'padding': '10px', 'width': '25%', 'textAlign': 'center'}, children=[
                        html.H2(id='metric-response', style={'margin': '0', 'color': '#3A75AF'}),
                        html.P('Responders vs Non-Responders')
                    ]),
                ]),

                html.H4("Baseline Data Table"),
                dash_table.DataTable(
                    id='baseline-table',
                    columns=[{"name": i, "id": i} for i in baseline_df.columns],
                    page_size=20,
                    style_cell={'textAlign': 'left', 'padding': '5px'},
                    style_header={'backgroundColor': '#3A75AF', 'color': 'white', 'fontWeight': 'bold'},
                    export_format='csv'
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
    if selected_population == 'all':
        fig = px.box(
            subset_df,
            x='response',
            y='percentage',
            color='response',
            points='all',
            facet_col='population',
            facet_col_wrap=5,
            title='Percentage Distribution of Cell Populations by Response',
            color_discrete_map={'yes': "green", 'no': "red"}
        )
        fig.update_yaxes(matches='y') 
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1].replace("_", " ").title()))
    else:
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

@app.callback(
    [Output('baseline-table', 'data'),
     Output('metric-total', 'children'),
     Output('metric-sex', 'children'),
     Output('metric-response', 'children')],
    [Input('project-filter', 'value'),
     Input('sex-filter', 'value'),
     Input('response-filter', 'value')]
)
def update_baseline_table(selected_projects, selected_sexes, selected_responses):
    full_dataset = baseline_df.copy()

    if selected_projects:
        full_dataset = full_dataset[full_dataset['project'].isin(selected_projects)]
    if selected_sexes:
        full_dataset = full_dataset[full_dataset['sex'].isin(selected_sexes)]
    if selected_responses:
        full_dataset = full_dataset[full_dataset['response'].isin(selected_responses)]

    total_samples = len(full_dataset)
    males = len(full_dataset[full_dataset['sex'] == 'M'])
    females = len(full_dataset[full_dataset['sex'] == 'F'])
    responders = len(full_dataset[full_dataset['response'] == 'yes'])
    non_responders = len(full_dataset[full_dataset['response'] == 'no'])

    gender_split = f"{males}M / {females}F"
    response_split = f"{responders} Responders / {non_responders} Non-Responders"

    return full_dataset.to_dict('records'), total_samples, gender_split, response_split

# Run server
if __name__ == '__main__':
    app.run(debug=True)