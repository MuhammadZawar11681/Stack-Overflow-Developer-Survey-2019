from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import pandas as pd
from sqlalchemy import create_engine
from flask_cors import CORS
import plotly.express as px
from sklearn.cluster import KMeans
import numpy as np

app = Dash(__name__)
server = app.server
CORS(server)

# Connect to MySQL database and fetch data using SQLAlchemy
def fetch_data():
    engine = create_engine('mysql+mysqlconnector://root:@localhost/stackoverflow_survey_db')
    query = "SELECT * FROM survey_results_2019"
    df = pd.read_sql(query, engine)
    engine.dispose()
    return df

# Handle missing values and preprocess data
def preprocess_data(df):
    df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
    df['Age'] = df['Age'].fillna(df['Age'].median())
    df['ConvertedComp'] = pd.to_numeric(df['ConvertedComp'], errors='coerce')
    df['ConvertedComp'] = df['ConvertedComp'].fillna(df['ConvertedComp'].median())
    return df

# Preprocess data specifically for clustering
def preprocess_for_clustering(df):
    clustering_df = df[['Age', 'ConvertedComp']].copy()
    clustering_df['ConvertedComp'] = pd.to_numeric(clustering_df['ConvertedComp'], errors='coerce')
    clustering_df = clustering_df[clustering_df['ConvertedComp'] > 0]  # Remove zero or negative salaries
    clustering_df = clustering_df.dropna()
    return clustering_df

# Define the layout of the dashboard
def create_layout(df):
    return html.Div([
        html.H1('Stack Overflow Developer Survey 2019', style={'textAlign': 'center'}),

        html.Div([
            html.Label('Select Country'),
            dcc.Dropdown(
                id='country-filter',
                options=[{'label': country, 'value': country} for country in df['Country'].unique()],
                value='United States'
            )
        ], style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            html.Label('Cluster Legend:'),
            html.Div([
                html.Div('Low Salary', style={'display': 'inline-block', 'width': '20%', 'backgroundColor': 'rgb(255, 51, 51)', 'color': 'white', 'padding': '5px', 'textAlign': 'center'}),
                html.Div('Medium Salary', style={'display': 'inline-block', 'width': '20%', 'backgroundColor': 'rgb(255, 153, 51)', 'color': 'white', 'padding': '5px', 'textAlign': 'center'}),
                html.Div('High Salary', style={'display': 'inline-block', 'width': '20%', 'backgroundColor': 'rgb(255, 255, 51)', 'color': 'white', 'padding': '5px', 'textAlign': 'center'}),
            ])
        ], style={'width': '50%', 'display': 'inline-block', 'float': 'right', 'textAlign': 'right'}),
        
        dcc.Graph(id='country-graph'),

        html.Div([
            html.Label('Select Country for Line Chart'),
            dcc.Dropdown(
                id='line-chart-country-filter',
                options=[{'label': country, 'value': country} for country in df['Country'].unique()],
                value='United States'
            )
        ], style={'width': '50%', 'display': 'inline-block'}),

        dcc.Graph(id='line-chart'),

        html.Div([
            html.Label('Select Country for Box Plot'),
            dcc.Dropdown(
                id='boxplot-country-filter',
                options=[{'label': country, 'value': country} for country in df['Country'].unique()],
                value='United States'
            )
        ], style={'width': '50%', 'display': 'inline-block'}),

        dcc.Graph(id='box-plot'),

        html.Div([
            html.H2('Overview of the Entire Dataset'),
            dcc.Interval(
                id='interval-component',
                interval=60*60*1000,  # Update every hour
                n_intervals=0
            ),
            dcc.Graph(id='overview-graph')
        ])
    ])

# Define callback to update country graph
@app.callback(
    Output('country-graph', 'figure'),
    [Input('country-filter', 'value')]
)
def update_country_graph(selected_country):
    filtered_df = df[df['Country'] == selected_country]

    # Define salary ranges
    low_salary = filtered_df['ConvertedComp'].quantile(0.33)
    high_salary = filtered_df['ConvertedComp'].quantile(0.67)

    def categorize_salary(salary):
        if salary <= low_salary:
            return 'rgb(255, 51, 51)'
        elif salary <= high_salary:
            return 'rgb(255, 153, 51)'
        else:
            return 'rgb(255, 255, 51)'

    filtered_df['SalaryCategory'] = filtered_df['ConvertedComp'].apply(categorize_salary)

    language_counts = filtered_df['LanguageWorkedWith'].str.split(';').explode().value_counts()

    fig = {
        'data': [
            {
                'x': language_counts.index,
                'y': language_counts.values,
                'type': 'bar',
                'marker': {
                    'color': [categorize_salary(salary) for salary in filtered_df['ConvertedComp']],
                },
                'text': language_counts.values,
                'textposition': 'inside',
                'textfont': {'color': 'white'}
            }
        ],
        'layout': {
            'title': f'Languages used by developers in {selected_country}',
            'xaxis': {'title': {'text': 'Programming Languages', 'standoff': 15}, 'tickangle': -45, 'tickfont': {'size': 10}, 'automargin': True},
            'yaxis': {'title': 'Number of Developers'}
        }
    }
    return fig

# Define callback to update line chart
@app.callback(
    Output('line-chart', 'figure'),
    [Input('line-chart-country-filter', 'value')]
)
def update_line_chart(selected_country):
    filtered_df = df[df['Country'] == selected_country]
    age_salary = filtered_df.groupby('Age')['ConvertedComp'].median().reset_index()

    fig = px.line(
        age_salary,
        x='Age',
        y='ConvertedComp',
        title=f'Median Salary by Age in {selected_country}',
        labels={'Age': 'Age', 'ConvertedComp': 'Median Salary'}
    )

    fig.update_layout(
        xaxis_title='Age',
        yaxis_title='Median Salary',
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12
    )

    return fig

# Define callback to update box plot
@app.callback(
    Output('box-plot', 'figure'),
    [Input('boxplot-country-filter', 'value')]
)
def update_box_plot(selected_country):
    filtered_df = df[df['Country'] == selected_country]

    fig = px.box(
        filtered_df,
        x='Age',
        y='ConvertedComp',
        title=f'Salary Distribution by Age in {selected_country}',
        labels={'Age': 'Age', 'ConvertedComp': 'Salary'},
        points='all'
    )

    fig.update_traces(marker_color='rgb(7,40,89)', marker_line_color='rgb(7,40,89)',
                      marker_line_width=1.5, opacity=0.6)

    fig.update_layout(
        xaxis_title='Age',
        yaxis_title='Salary',
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12
    )

    return fig

# Define callback to update overview graph (treemap)
@app.callback(
    Output('overview-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_overview_graph(n_intervals):
    country_salary = df.groupby('Country')['ConvertedComp'].median().reset_index()
    country_salary = country_salary.sort_values(by='ConvertedComp', ascending=False)

    fig = px.treemap(
        country_salary,
        path=['Country'],
        values='ConvertedComp',
        title='Overview of Median Salaries by Country',
        labels={'ConvertedComp': 'Median Salary', 'Country': 'Country'}
    )

    fig.update_layout(
        treemapcolorway=['#636efa', '#ef553b', '#00cc96', '#ab63fa', '#19d3f3', '#e763fa', '#fecb52', '#ffa15a', '#ff6692', '#b6e880'],
        margin=dict(t=50, l=25, r=25, b=25)
    )

    return fig

if __name__ == '__main__':
    df = fetch_data()
    df = preprocess_data(df)
    app.layout = create_layout(df)
    app.run_server(debug=True)
