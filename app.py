import json
import pandas as pd
import requests
import plotly.express as px
from dash import Dash, Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
load_figure_template(['darkly', 'flatly', 'cosmo'])


october = pd.read_csv('nyt_october_2023.csv')

keywords_flat = []
for kw in october['keywords']:
    keywords_flat.append([k['value'] for k in eval(kw)])

october['keywords_flat'] = keywords_flat
october['headline_flat'] = [eval(headline)['main'] for headline in october['headline']]
october['pub_date'] = pd.to_datetime(october['pub_date'])
october['pub_day'] = october['pub_date'].dt.day

pub_day_df = october['pub_day'].value_counts().sort_index().reset_index()
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

top_kwds = october['keywords_flat'].explode().value_counts().head(300).index

keywords = october[['pub_date', 'pub_day', 'keywords_flat']].explode('keywords_flat')

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc_css])


wordcount_hist = px.histogram(
    october,
    x='word_count',
    template='darkly',
    nbins=100,
    height=500,
    title='Word count per article NYTimes.com - October 2023',
    labels={'word_count': 'word count'})


art_perday = px.bar(
    pub_day_df,
    x='pub_day',
    y='count',
    template='darkly',
    height=500,
    title='Articles per day NYTimes.com - October 2023',
    labels={'pub_day': 'day'})
art_perday.update_layout(bargap=0.03)


app.layout = html.Div([
    html.Br(),
    html.H1(["NYTimes.com News Articles - October 2023",
             html.Div([
                 html.A([
             html.Img(src='https://developer.nytimes.com/files/poweredby_nytimes_200c.png?v=1583354208354')
                 ], href='https://developer.nytimes.com/', target='_blank')
                 
             ])
             ]), html.Br(),
    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=art_perday), html.Br(), html.Br(),            
        ], lg=6),
        dbc.Col([
            dcc.Graph(figure=wordcount_hist), html.Br(), html.Br(),            
        ], lg=6),

    ]),

    html.Br(), html.Br(),
    
    html.Div([
        dbc.Label("Keyword(s):"),
        dcc.Dropdown(
            id='kw_dropdown',
            multi=True,
            options=top_kwds,
            maxHeight=400,
            style={'width': 600})
    ], style={'marginRight': '25%', 'marginLeft': '25%'}),
    html.Br(), html.Br(),
    html.Div(id='kw_chart')
] + [html.Br() for i in range(15)], className="dbc", style={'marginLeft': '4%', 'marginRight': '4%'})


@app.callback(
    Output('kw_chart', 'children'),
    Input('kw_dropdown', 'value'))
def make_kw_chart(kwds):
    if kwds is None:
        raise PreventUpdate
    df = keywords[keywords['keywords_flat'].isin(kwds)].groupby(['pub_day', 'keywords_flat'], as_index=False).count()
    fig = px.line(
        df,
        x='pub_day',
        y='pub_date',
        color='keywords_flat',
        title='Articles per day per keyword - <b>nytimes.com</b><br>October, 2023',
        template='darkly',
        labels={'keywords_flat': 'Keyword', 'pub_day': 'day', 'pub_date': 'number of articles'})
    fig.layout.hovermode="x unified"
    fig.data[0].line.width = 3
    fig.layout.xaxis.showgrid = False
    fig.layout.legend.font.size = 15
    for i in range(len(fig.data)):
        fig.data[i].hovertemplate = fig.data[i].hovertemplate.replace('Keyword=', '').replace('=', ': ')
    return html.Div([dcc.Graph(figure=fig, config={'displaylogo': False}, style={'height': 650})])

app.run(jupyter_mode='external')
