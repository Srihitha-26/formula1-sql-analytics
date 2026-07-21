r"""
dashboard/app.py — interactive Formula 1 analytics dashboard (Streamlit + Plotly).

Streamlit turns this script into a web app (every st.* call draws something).
Plotly makes the charts interactive — hover for values, zoom, pan.
The dark + F1-red look comes from .streamlit/config.toml.

Run it (opens in your browser):
    .\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
"""
import sqlite3
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "f1.db"
MODEL_PATH = ROOT / "ml" / "podium_model.joblib"
F1_RED = "#E10600"

st.set_page_config(page_title="F1 Analytics", page_icon="🏎️", layout="wide")

# Every Plotly chart inherits this dark style + F1-red default colour.
px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = [F1_RED]

# A little CSS polish: hide Streamlit's default menu/footer, tighten spacing.
st.markdown(
    """
    <style>
      #MainMenu, footer {visibility: hidden;}
      .block-container {padding-top: 2.5rem; padding-bottom: 2rem;}
      h1, h2, h3 {letter-spacing: 0.3px;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def run_sql(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def style_fig(fig, height=340):
    """Shared chart styling: transparent background so it blends with the page."""
    fig.update_layout(
        height=height,
        margin=dict(t=45, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ---- Header --------------------------------------------------------------
st.markdown("# 🏎️ Formula 1 Analytics")
st.markdown(
    f"<span style='color:{F1_RED};font-weight:600'>75 seasons</span> of racing "
    "(1950–2024) &nbsp;·&nbsp; Python · SQL · Machine Learning",
    unsafe_allow_html=True,
)
st.divider()

tab_driver, tab_season, tab_predict = st.tabs(
    ["🏆 Driver performance", "📊 Season standings", "🔮 Podium predictor"]
)

# ---- TAB 1: Driver performance ------------------------------------------
with tab_driver:
    drivers = run_sql(
        "SELECT driverId, forename || ' ' || surname AS name FROM drivers ORDER BY name"
    )
    names = drivers["name"].tolist()
    default = names.index("Lewis Hamilton") if "Lewis Hamilton" in names else 0
    name = st.selectbox("Driver", names, index=default)
    did = int(drivers.loc[drivers["name"] == name, "driverId"].iloc[0])

    stats = run_sql(
        """
        SELECT COUNT(*)                                            AS entries,
               SUM(CASE WHEN positionOrder = 1  THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN positionOrder <= 3 THEN 1 ELSE 0 END) AS podiums,
               CAST(SUM(points) AS INT)                            AS points
        FROM results WHERE driverId = ?
        """,
        (did,),
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entries", int(stats["entries"][0]))
    c2.metric("Wins", int(stats["wins"][0]))
    c3.metric("Podiums", int(stats["podiums"][0]))
    c4.metric("Career points", f"{int(stats['points'][0]):,}")

    per_season = run_sql(
        """
        SELECT ra.year                                              AS season,
               SUM(CASE WHEN r.positionOrder = 1 THEN 1 ELSE 0 END) AS wins,
               SUM(r.points)                                        AS points
        FROM results r JOIN races ra ON ra.raceId = r.raceId
        WHERE r.driverId = ?
        GROUP BY ra.year ORDER BY ra.year
        """,
        (did,),
    )
    left, right = st.columns(2)
    with left:
        fig = px.bar(per_season, x="season", y="wins", title="Wins per season")
        fig.update_layout(bargap=0.15)
        st.plotly_chart(style_fig(fig), width="stretch")
    with right:
        fig = px.area(per_season, x="season", y="points", title="Points per season")
        fig.update_traces(line_color=F1_RED, fillcolor="rgba(225,6,0,0.25)")
        st.plotly_chart(style_fig(fig), width="stretch")

# ---- TAB 2: Season standings --------------------------------------------
with tab_season:
    years = run_sql("SELECT DISTINCT year FROM races ORDER BY year DESC")
    yr = int(st.selectbox("Season", years["year"]))
    standings = run_sql(
        """
        SELECT d.forename || ' ' || d.surname AS driver,
               CAST(SUM(r.points) AS INT)     AS points,
               SUM(CASE WHEN r.positionOrder = 1 THEN 1 ELSE 0 END) AS wins
        FROM results r
        JOIN races ra   ON ra.raceId  = r.raceId
        JOIN drivers d  ON d.driverId = r.driverId
        WHERE ra.year = ?
        GROUP BY r.driverId ORDER BY points DESC
        """,
        (yr,),
    )
    st.subheader(f"{yr} Drivers' Championship")
    chart_col, table_col = st.columns([3, 2])
    with chart_col:
        top = standings.head(10).iloc[::-1]  # reverse so the leader ends up on top
        fig = px.bar(
            top, x="points", y="driver", orientation="h", text="points",
            title="Top 10 by points",
            color="points", color_continuous_scale=["#5A0300", F1_RED],
        )
        fig.update_layout(yaxis_title=None, xaxis_title="Points", coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig, height=430), width="stretch")
    with table_col:
        st.dataframe(standings, width="stretch", hide_index=True, height=430)

# ---- TAB 3: Podium predictor --------------------------------------------
with tab_predict:
    st.write(
        "Predict the chance a driver finishes **on the podium** (top 3), "
        "from where they start and which team they drive for."
    )
    if not MODEL_PATH.exists():
        st.warning(r"Model not trained yet — run:  .\.venv\Scripts\python.exe ml\train_model.py")
    else:
        bundle = joblib.load(MODEL_PATH)
        model, columns = bundle["model"], bundle["columns"]
        constructors = run_sql("SELECT DISTINCT name FROM constructors ORDER BY name")

        a, b, c = st.columns(3)
        grid = a.number_input("Starting grid position", 1, 30, 3)
        year = b.number_input("Season year", 1950, 2024, 2024)
        team = c.selectbox("Constructor", constructors["name"])

        # Build one input row with the SAME columns the model trained on.
        row = pd.DataFrame([{col: 0 for col in columns}])
        row.at[0, "grid"] = grid
        row.at[0, "year"] = year
        team_col = f"constructor_{team}"
        if team_col in row.columns:
            row.at[0, team_col] = 1
        prob = float(model.predict_proba(row)[0, 1])

        # Show the probability as a gauge.
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(prob * 100, 1),
            number={"suffix": "%", "font": {"size": 44}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": F1_RED},
                "bgcolor": "rgba(0,0,0,0)",
                "steps": [
                    {"range": [0, 40], "color": "#20242E"},
                    {"range": [40, 70], "color": "#2C313D"},
                    {"range": [70, 100], "color": "#3A4150"},
                ],
            },
        ))
        gauge.update_layout(
            template="plotly_dark", height=340, margin=dict(t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(gauge, width="stretch")
        st.caption("Random forest · trained on 75 seasons · ROC AUC ≈ 0.89")
