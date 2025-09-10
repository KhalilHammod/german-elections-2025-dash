import pandas as pd
from pathlib import Path
from typing import Dict
import dash
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px

DATA_PATH = Path(__file__).parent / "elections_2025_state_party.csv"
try:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
except FileNotFoundError:
    print(f"Error: The file '{DATA_PATH}' was not found. Please ensure it is in the same directory.")
    df = pd.DataFrame() # Create an empty DataFrame to prevent errors

# ---- Party color map (real-life approximations) ----
PARTY_COLORS: Dict[str, str] = {
    "Christlich Demokratische Union Deutschlands": "#000000",
    "Christlich-Soziale Union in Bayern e.V.": "#008AC5",
    "Sozialdemokratische Partei Deutschlands": "#E3000F",
    "BÜNDNIS 90/DIE GRÜNEN": "#1AA037",
    "Freie Demokratische Partei": "#FFED00",
    "Alternative für Deutschland": "#009EE0",
    "Die Linke": "#BE3075",
    "Bündnis Sahra Wagenknecht": "#00B5AD",
    "Brandenb. Verein. Bürgerbewegungen/Freie Wähler": "#FF7F00",
    "Volt Deutschland": "#612095",
    "Die Partei": "#E20613",
    "Südschleswigscher Wählerverband": "#00A1DE",
}
DEFAULT_OTHER = "#CCCCCC"
def pcolor(name: str) -> str:
    return PARTY_COLORS.get(name, DEFAULT_OTHER)

ALL_STATES = sorted(df["state"].unique().tolist()) if not df.empty else []

# ---- National totals (computed from counts, not average of shares) ----
if not df.empty:
    nat_first = df.groupby("party", as_index=False)["first_votes"].sum()
    nat_second = df.groupby("party", as_index=False)["second_votes"].sum()
    nat_first["share"] = nat_first["first_votes"] / nat_first["first_votes"].sum() * 100
    nat_second["share"] = nat_second["second_votes"] / nat_second["second_votes"].sum() * 100
    nat_first = nat_first.sort_values("first_votes", ascending=False)
    nat_second = nat_second.sort_values("second_votes", ascending=False)
    winner_first = nat_first.iloc[0]["party"]
    winner_first_share = nat_first.iloc[0]["share"]
    winner_second = nat_second.iloc[0]["party"]
    winner_second_share = nat_second.iloc[0]["share"]
else:
    winner_first = "N/A"
    winner_first_share = 0
    winner_second = "N/A"
    winner_second_share = 0

# ---- Layout pieces ----
def kpi_card(title, value, sub="", icon_class="bi bi-person-fill"):
    """
    Creates a styled KPI card with an icon.
    """
    return dbc.Card(
        dbc.CardBody([
            dbc.Row(
                [
                    dbc.Col(html.I(className=f"{icon_class} me-2 fs-2 text-primary"), width="auto"),
                    dbc.Col(
                        [
                            html.Div(title, className="text-muted small text-uppercase fw-bold"),
                            html.H4(value, className="mb-0 fw-bold text-dark"),
                            html.Div(sub, className="text-muted small"),
                        ],
                        className="ms-2"
                    ),
                ],
                align="center",
                className="g-0"
            )
        ]),
        className="shadow-sm border-0 rounded-4",
        style={"backgroundColor": "#f8f9fa"}
    )

# --- Define external stylesheets ---
# We no longer need the custom_css variable in the Python file.
# The custom CSS is now in the separate 'assets/style.css' file.
external_stylesheets=[
    dbc.themes.CERULEAN,  # A cleaner, more professional blue theme
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css"
]
# Dash automatically looks for a file named 'style.css' in the 'assets' folder.
app = Dash(__name__, external_stylesheets=external_stylesheets, title="Germany 2025 — Overview & States")
server = app.server

app.layout = html.Div(
    [
        # The custom CSS is now automatically linked via the 'assets' folder.
        # No need for html.Style(custom_css) anymore.
        dbc.Navbar(
            dbc.Container(
                [
                    html.A(
                        dbc.Row(
                            [
                                dbc.Col(html.I(className="bi bi-bar-chart-line-fill me-2 fs-4 text-white")),
                                dbc.Col(dbc.NavbarBrand("Germany 2025 Election Dashboard", className="ms-2 fw-bold text-white fs-5")),
                            ],
                            align="center",
                            className="g-0",
                        ),
                        href="#", style={"textDecoration": "none"},
                    ),
                    dbc.NavbarToggler(id="navbar-toggler"),
                ]
            ),
            color="primary",
            dark=True,
            className="mb-4 shadow-lg rounded-bottom-4 border-0",
        ),
        dbc.Container([
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Dashboard Mode", className="form-label"),
                            dbc.RadioItems(
                                id="mode", inline=True, value="overall",
                                options=[
                                    {"label": "Overview", "value": "overall"},
                                    {"label": "States", "value": "state"}
                                ],
                                className="btn-group-toggle",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-primary rounded-pill",
                                labelCheckedClassName="active"
                            ),
                        ], md=6, lg=3),
                        dbc.Col([
                            dbc.Label("Overall Vote Type", className="form-label"),
                            dbc.RadioItems(
                                id="overall-vote-type", inline=True, value="second",
                                options=[
                                    {"label": "Second vote", "value": "second"},
                                    {"label": "First vote", "value": "first"}
                                ],
                                className="btn-group-toggle",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-primary rounded-pill",
                                labelCheckedClassName="active"
                            ),
                        ], md=6, lg=3, id="overall-opts"),
                        dbc.Col([
                            dbc.Label("Select State", className="form-label"),
                            dcc.Dropdown(
                                id="state-dd",
                                options=[{"label": s, "value": s} for s in ALL_STATES],
                                value=ALL_STATES[0] if ALL_STATES else None,
                                clearable=False,
                                className="rounded-pill"
                            )
                        ], md=6, lg=3, id="state-col", style={"display":"none"}),
                        dbc.Col([
                            #dbc.Label("Share Type", className="form-label"),
                            dbc.RadioItems(
                                id="share-type", inline=True, value="second_share",
                                options=[
                                    {"label": "Second", "value": "second_share"},
                                    {"label": "First", "value": "first_share"}
                                ],
                                className="btn-group-toggle",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-primary rounded-pill",
                                labelCheckedClassName="active"
                            ),
                        ], md=6, lg=2, id="share-col", style={"display":"none"}),
                        dbc.Col([
                            dbc.Label("Top N Parties", className="form-label"),
                            dcc.Slider(
                                id="top-n", min=2, max=6, step=1, value=6,
                                marks={i: {'label': str(i), 'style': {'color': '#777'}} for i in range(2,7)},
                                className="py-2"
                            )
                        ], md=12, lg=4, id="topn-col", style={"display":"none"}),
                    ], className="gy-3")
                ]),
                className="shadow-lg mb-4 rounded-4"
            ),
            html.Div(id="kpi-row", className="mb-4"),
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Loading(dcc.Graph(id="main-graph", style={"height": "60vh"}), type="default")
                        ),
                        className="shadow-lg rounded-4 border-0"
                    ),
                    width=12
                )
            ]),
        ], fluid=True)
    ]
)

# ---- Callbacks ----
@app.callback(
    Output("overall-opts","style"),
    Output("state-col","style"),
    Output("share-col","style"),
    Output("topn-col","style"),
    Input("mode","value")
)
def toggle_controls(mode):
    """
    Toggles the visibility of controls based on the selected dashboard mode.
    """
    if mode=="overall":
        return {}, {"display":"none"}, {"display":"none"}, {"display":"none"}
    return {"display":"none"}, {}, {}, {}

@app.callback(
    Output("kpi-row","children"),
    Output("main-graph","figure"),
    Input("mode","value"),
    Input("overall-vote-type","value"),
    Input("state-dd","value"),
    Input("share-type","value"),
    Input("top-n","value"),
)
def render(mode, overall_vote_type, state_value, share_type, topn):
    """
    Renders the KPI cards and the main graph based on user selections.
    """
    if df.empty:
        return html.Div(dbc.Alert("Data not found. Please check your CSV file path.", color="danger")), px.scatter(title="Error")

    if mode == "overall":
        # KPI row: overall winners for first & second votes (national)
        kpis = dbc.Row([
            dbc.Col(kpi_card("Second Vote Winner", winner_second, f"{winner_second_share:.1f}% nationally", icon_class="bi bi-trophy-fill"), md=4),
            dbc.Col(kpi_card("First Vote Winner", winner_first, f"{winner_first_share:.1f}% nationally", icon_class="bi bi-trophy-fill"), md=4),
            dbc.Col(kpi_card("States Covered", f"{len(ALL_STATES)}", "", icon_class="bi bi-map-fill"), md=4),
        ], className="g-4")
        
        # Chart: bar of chosen vote type
        if overall_vote_type == "second":
            nat = df.groupby("party", as_index=False)["second_votes"].sum().sort_values("second_votes", ascending=False)
            fig = px.bar(
                nat.head(15), 
                x="party", 
                y="second_votes",
                title="National Totals — Second Votes",
                color="party", 
                color_discrete_map={p:pcolor(p) for p in nat["party"]}
            )
            fig.update_layout(
                xaxis_title="", 
                yaxis_title="Second Votes", 
                margin=dict(l=10, r=10, t=50, b=10),
                plot_bgcolor='white', 
                paper_bgcolor='#f8f9fa',
                title_font_size=20,
                xaxis={'showgrid': False},
                yaxis={'showgrid': True}
            )
        else:
            nat = df.groupby("party", as_index=False)["first_votes"].sum().sort_values("first_votes", ascending=False)
            fig = px.bar(
                nat.head(15), 
                x="party", 
                y="first_votes",
                title="National Totals — First Votes",
                color="party", 
                color_discrete_map={p:pcolor(p) for p in nat["party"]}
            )
            fig.update_layout(
                xaxis_title="", 
                yaxis_title="First Votes", 
                margin=dict(l=10, r=10, t=50, b=10),
                plot_bgcolor='white', 
                paper_bgcolor='#f8f9fa',
                title_font_size=20,
                xaxis={'showgrid': False},
                yaxis={'showgrid': True}
            )
        return kpis, fig

    # State mode: one state pie of percentages
    if not state_value:
        return html.Div(), px.scatter(title="Pick a state")
    
    sdf = df[df["state"]==state_value].copy()
    sdf = sdf.sort_values(share_type, ascending=False)
    top = sdf.head(topn)
    others_share = max(0.0, 100.0 - float(top[share_type].sum()))
    if others_share > 0.05:
        top = pd.concat([top, pd.DataFrame([{"state": state_value, "party": "Others", share_type: others_share}])], ignore_index=True)
    
    cmap = {p: pcolor(p) for p in top["party"]}
    cmap["Others"] = "#CCCCCC"
    
    fig = px.pie(
        top, 
        names="party", 
        values=share_type, 
        title=f"{state_value} — {('Second' if share_type=='second_share' else 'First')} Vote Share (%)",
        color="party", 
        color_discrete_map=cmap, 
        hole=0.45
    )
    fig.update_traces(
        textposition="inside", 
        texttemplate="%{label}<br>%{value:.1f}%",
        marker=dict(line=dict(color='#000', width=1))
    )
    fig.update_layout(
        legend_title="", 
        margin=dict(l=10,r=10,t=50,b=10),
        plot_bgcolor='#f8f9fa', 
        paper_bgcolor='#f8f9fa',
        title_font_size=20
    )
    return html.Div(), fig

if __name__ == "__main__":
    app.run(debug=True)