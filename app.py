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
    ]
)
template = "slate"
pd.options.display.max_columns = None


october = pd.concat([
    pd.read_csv("/Users/me/Google Drive/nytimes_api_analysis/nyt_october_2023.csv"),
    pd.read_csv("/Users/me/Google Drive/nytimes_api_analysis/nyt_november_2023.csv")
], ignore_index=True)

keywords_flat = []
for kw in october["keywords"]:
    keywords_flat.append([k["value"] for k in eval(kw)])

october["keywords_flat"] = keywords_flat
october["headline_flat"] = [eval(headline)["main"] for headline in october["headline"]]
october["pub_date"] = pd.to_datetime(october["pub_date"])
october["pub_day"] = october["pub_date"].dt.day

pub_day_df = october["pub_date"].dt.date.value_counts().sort_index().reset_index()


top_kwds = october["keywords_flat"].explode().value_counts().head(300).index

keywords = october[["pub_date", "pub_day", "keywords_flat"]].explode("keywords_flat")
keywords['date'] = keywords['pub_date'].dt.date

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE, dbc_css])


wordcount_hist = px.histogram(
    october,
    x="word_count",
    template=template,
    nbins=100,
    height=500,
    title="Word count per article NYTimes.com - October 2023",
    labels={"word_count": "word count"},
)


art_perday = px.bar(
    pub_day_df,
    x="pub_date",
    y="count",
    template=template,
    height=500,
    title="Articles per day NYTimes.com - October 2023",
    labels={"pub_day": "day"},
)
art_perday.update_layout(bargap=0.03)


keywords_perday = (
    keywords.groupby(["date", "keywords_flat"], as_index=False)
    .count()
    .sort_values(["date", "pub_date"], ascending=[True, False])
)
keywords_perday_fig = adviz.racing_chart(
    keywords_perday[["keywords_flat", "pub_date", "date"]].rename(
        columns={"pub_day": "Day"}
    ),
    n=15,
    theme=template,
    height=750,
    title="Top daily keywords - racing",
)
keywords_perday_fig.layout.margin.l = 200
keywords_perday_fig.layout.yaxis.title = None

app.layout = html.Div(
    [
        html.Br(),
        html.H1(
            [
                "NYTimes.com News Articles - October 2023",
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
                        dcc.Graph(figure=wordcount_hist),
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
                                    options=top_kwds,
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
        title="Articles per day per keyword - <b>nytimes.com</b><br>October, 2023",
        template=template,
        labels={
            "keywords_flat": "Keyword",
            "pub_day": "day",
            "date": "number of articles",
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


app.run(jupyter_mode="external")
