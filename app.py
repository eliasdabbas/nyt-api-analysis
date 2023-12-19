import json

import adviz
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests
from dash import Dash, Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate
from dash_bootstrap_templates import load_figure_template

load_figure_template(
    [
        "darkly",
        "flatly",
        "SPACELAB",
        "cosmo",
        "materia",
        "grid",
        "zephyr",
        "quartz",
        "morph",
        "SKETCHY",
        "vapor",
        "solar",
        "slate",
        "bootstrap"
    ]
)
template = "cosmo"
pd.options.display.max_columns = None

data = pd.read_csv('api_data.csv')

keywords_flat = []
for kw in data["keywords"]:
    keywords_flat.append([k["value"] for k in eval(kw)])

data["keywords_flat"] = keywords_flat
data["headline_flat"] = [eval(headline)["main"] for headline in data["headline"]]
data["pub_date"] = pd.to_datetime(data["pub_date"])
data["pub_day"] = data["pub_date"].dt.day

authors = []
for byline in data['byline']:
    try:
        d = eval(byline)
        persons = []
        if d.get('person'):
            for p in d['person']:
                tempname = ' '.join([p['firstname'], p['middlename'] or '', p['lastname']])
                persons.append(tempname.replace('  ', ' '))
        authors.append(', '.join(persons))
    except Exception as e:
        authors.append(None)
        continue
data['authors'] = authors

pub_day_df = data.groupby([data['pub_date'].dt.date, 'document_type'])['pub_day'].count().reset_index()

# pub_day_df = data["pub_date"].dt.date.value_counts().sort_index().reset_index()

art_perday = px.bar(
    pub_day_df,
    x="pub_date",
    y="pub_day",
    color='document_type',
    template=template,
    height=650,
    title=f"Articles per day NYTimes.com<br>{str(data['pub_date'].min())[:10]} - {str(data['pub_date'].max())[:10]}",
    labels={"pub_day": "count", "pub_date": ''},
)
art_perday.update_layout(bargap=0.03)
art_perday.layout.legend.title = 'Document type'
art_perday.layout.legend.orientation = 'h'

top_kwds = data["keywords_flat"].explode().value_counts().head(300).index

keywords = data[["pub_date", "pub_day", "keywords_flat"]].explode("keywords_flat")
keywords['date'] = keywords['pub_date'].dt.date



dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO, dbc_css])


wordcount_hist = px.histogram(
    data,
    x="word_count",
    template=template,
    nbins=100,
    height=500,
    title="Word count per article NYTimes.com - October 2023",
    labels={"word_count": "word count"},
)


keywords_perday = (
    keywords.groupby(["date", "keywords_flat"], as_index=False)
    .count()
    .sort_values(["date", "pub_date"], ascending=[True, False])
)
keywords_perday_fig = adviz.racing_chart(
    keywords_perday[["keywords_flat", "pub_date", "date"]].rename(
        columns={"pub_date": "count"}
    ),
    n=15,
    theme=template,
    # frame_duration=200,
    height=750,
    title="Top daily keywords - racing",
)
keywords_perday_fig.layout.margin.l = 200
keywords_perday_fig.layout.yaxis.title = None

top_keywords = data['keywords_flat'].explode().value_counts().head(20).reset_index()

top_keywords_fig = px.bar(
    top_keywords[::-1],
    title=f"Total articles per keyword (top 20)<br>{str(data['pub_date'].min())[:10]} - {str(data['pub_date'].max())[:10]}",
    labels={'keywords_flat': 'keyword'},
    template=template,
    height=650,
    x='count',
    y='keywords_flat')

app.layout = html.Div(
    [
        html.Br(),
        html.H1(
            [
                f"NYTimes.com News Articles - {str(data['pub_date'].min())[:10]} - {str(data['pub_date'].max())[:10]}",
                html.Div(
                    [
                        html.A(
                            [
                                html.Img(
                                    src="https://developer.nytimes.com/files/poweredby_nytimes_200c.png?v=1583354208354"
                                )
                            ],
                            href="https://developer.nytimes.com/",
                            target="_blank",
                        )
                    ]
                ),
            ]
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(figure=art_perday),
                        html.Br(),
                        html.Br(),
                    ],
                    lg=6,
                ),
                dbc.Col(
                    [
                        # dcc.Graph(figure=wordcount_hist),
                        dcc.Graph(figure=top_keywords_fig),
                        
                        html.Br(),
                        html.Br(),
                    ],
                    lg=6,
                ),
            ]
        ),
        html.Br(),
        html.Br(),
        dbc.Row(
            [
                dbc.Col([dcc.Graph(figure=keywords_perday_fig)], lg=6),
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(id="kw_chart"),
                                dbc.Label("Keyword(s):"),
                                dcc.Dropdown(
                                    id="kw_dropdown",
                                    multi=True,
                                    options=[{'label': f"{i}: {keyword}", 'value': keyword}
                                             for i, keyword in enumerate(top_kwds, start=1)],
                                    value=["Israel-Gaza War (2023- )"],
                                    maxHeight=400,
                                ),
                            ],
                        ),
                    ],
                    lg=6,
                ),
            ]
        ),
    ]
    + [html.Br() for i in range(15)],
    className="dbc",
    style={"marginLeft": "4%", "marginRight": "4%"},
)


@app.callback(Output("kw_chart", "children"), Input("kw_dropdown", "value"))
def make_kw_chart(kwds):
    if not kwds:
        raise PreventUpdate
    df = (
        keywords[keywords["keywords_flat"].isin(kwds)]
        .groupby(["date", "keywords_flat"], as_index=False)
        .count()
    )
    fig = px.line(
        df,
        x="date",
        y="pub_date",
        color="keywords_flat",
        title=f"Articles per day per keyword - <b>nytimes.com</b><br>{str(data['pub_date'].min())[:10]} - {str(data['pub_date'].max())[:10]}",
        template=template,
        labels={
            "keywords_flat": "Keyword",
            "pub_date": "count",
            # "date": "number of articles",
        },
    )
    fig.layout.hovermode = "x unified"
    fig.layout.xaxis.showgrid = False
    fig.layout.legend.font.size = 15
    fig.layout.margin.r = 5
    
    for i in range(len(fig.data)):
        fig.data[i].hovertemplate = (
            fig.data[i].hovertemplate.replace("Keyword=", "").replace("=", ": ")
        )
    fig.data[0].line.width = 3
    fig.update_layout(legend=dict(
        yanchor="top",
        y=-0.1,
        xanchor="left",
        x=0.01))
    return html.Div(
        [dcc.Graph(figure=fig, config={"displaylogo": False}, style={"height": 650})]
    )


app.run()
