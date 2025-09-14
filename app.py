import duckdb
import plotly.express as px
import streamlit as st
from streamlit_searchbox import st_searchbox

atp_duck = duckdb.connect("atp.duckdb", read_only=True)


def search_players(search_term):
    query = """
    SELECT DISTINCT winner_name AS player
      FROM matches
      WHERE player ilike '%' || $search_term || '%'
    UNION
      SELECT DISTINCT loser_name AS player
      FROM matches
      WHERE player ilike '%' || $search_term || '%'
    """
    values = atp_duck.execute(query, {"search_term": search_term}).fetchall()
    return [value[0] for value in values]


st.set_page_config(layout="wide")
st.title("ATP Head to Head")

left, right = st.columns(2)

with left:
    player1 = st_searchbox(
        search_players,
        label="Player 1",
        key="player1_search",
        default="Roger Federer",
        placeholder="Roger Federer",
    )
with right:
    player2 = st_searchbox(
        search_players,
        label="Player 2",
        key="player2_search",
        default="Rafael Nadal",
        placeholder="Rafael Nadal",
    )


matches_for_players = atp_duck.execute(
    """
SELECT
  tourney_date, 
  tourney_name, 
  surface, 
  round,
  rounds.order AS roundOrder,
  levels.name AS level, 
  levels.rank AS levelRank,
  winner_name, score
FROM matches
  JOIN levels ON levels.short_name = matches.tourney_level 
  JOIN rounds ON rounds.name = matches.round 
WHERE (loser_name = $player1 AND winner_name = $player2) OR
  (loser_name = $player2 AND winner_name = $player1)
ORDER BY tourney_date DESC
""",
    {"player1": player1, "player2": player2},
).fetchdf()


left, middle, right = st.columns(3)  # ①
with left:  # ②
    st.markdown(
        f"<h2 style='text-align: left; '>{player1}</h2>", unsafe_allow_html=True
    )
with right:  # ③
    st.markdown(
        f"<h2 style='text-align: right; '>{player2}</h2>", unsafe_allow_html=True
    )

p1_wins = matches_for_players[  # ④
    matches_for_players.winner_name == player1
].shape[0]
p2_wins = matches_for_players[  # ⑤
    matches_for_players.winner_name == player2
].shape[0]
with middle:
    st.markdown(  # ⑥
        f"<h2 style='text-align: center; '>{p1_wins} vs {p2_wins}</h2>",
        unsafe_allow_html=True,
    )


st.markdown("### Matches")
st.dataframe(matches_for_players.drop(["roundOrder", "level", "levelRank"], axis=1))


sorted_matches_for_players = atp_duck.sql("""
FROM matches_for_players
ORDER BY strftime(tourney_date, '%m-%d')
""").fetchdf()


fig = px.scatter(
    sorted_matches_for_players,
    x="tourney_date",
    y="tourney_name",
    color="winner_name",
    size="roundOrder",
    # ①ポイントに指定される色調。デフォルトでは2つの淡い色で表示され、印刷物では区別が難しい。他の
    # 選択肢については、 https://plotly.com/python/discrete-color を参照
    color_discrete_sequence=px.colors.qualitative.Plotly,  # ①
    # ②plot.lyがトーナメント名の順序を再度並べ替えてしまわないようにする
    category_orders={
        "tourney_name": (  # ②
            sorted_matches_for_players["tourney_name"].drop_duplicates().tolist()
        )
    },
)


min_year = sorted_matches_for_players["tourney_date"].dt.year.min()  # ①
max_year = sorted_matches_for_players["tourney_date"].dt.year.max()  # ②
unique_years = list(range(min_year, max_year + 2))  # ③
for year in unique_years:  # ④
    fig.add_shape(  # ⑤
        type="line",
        x0=f"{year}-01-01",
        x1=f"{year}-01-01",
        y0=0,
        y1=1,
        yref="paper",
        layer="below",
        line=dict(color="#efefef", width=2),
    )

st.plotly_chart(fig, use_container_width=True)

# how to run
# uv run streamlit app.py
