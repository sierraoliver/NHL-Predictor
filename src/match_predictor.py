import pandas as pd
from xgboost import XGBClassifier
from datetime import datetime
from sklearn.metrics import accuracy_score, precision_score
from sklearn.model_selection import train_test_split

def rolling_averages(group, cols, new_cols):
    group = group.sort_values("date")
    rolling_stats = group[cols].rolling(5,closed='left').mean()
    group[new_cols] = rolling_stats
    today = pd.Timestamp.today().normalize()
    group = group[~((group["date"] < today) & group[new_cols].isna().any(axis=1))]
    return group

def make_predictions_prob (model, data, predictors, threshold):
    today = pd.Timestamp.today().normalize()
    train = data[data["date"]<today]
    future_games = data[data["date"]>= today].copy()
    future_games[predictors] = future_games[predictors].fillna(0)

    if (future_games.empty):
        print("No future games found")
        return pd.DataFrame()
    
    x_train = train[predictors]
    y_train = train["target"]

    model.fit(x_train, y_train)
    x_future = future_games[predictors]
    probs = model.predict_proba(x_future)[:, 1]
    preds = (probs > threshold).astype(int)
    combined = future_games.copy()
    combined["prediction"] = preds
    combined["home_win_probability"] = probs
    combined["away_win_probability"] = 1-probs
    combined["predicted_winner"] = combined.apply(lambda row: row["home_team"] if row["home_win_probability"] >= 0.5 else row["away_team"],axis=1)
    return combined

def build_matchups(matches):
    home_games = matches[matches["venue"] == "Home"].copy()
    away_games = matches[matches["venue"] == "Away"].copy()

    # Merge home rows with the corresponding away rows (same date + same opponent/team swap)
    merged = pd.merge(
        home_games, away_games,
        left_on=["date", "opponent"],
        right_on=["date", "team"],
        suffixes=("_home", "_away"),
        how="outer"
    )

    merged = merged.rename(columns={
        "team_home": "home_team",
        "team_away": "away_team",
        "opponent_away": "away_opponent",
        "opponent_home": "home_opponent"
    })

    # Sanity check: home_opponent should equal away_team
    #assert all(merged["home_opponent"] == merged["away_team"])
    merged["venue"] = merged["home_team"]
    merged = merged.drop(columns=["venue_home", "venue_away"])

    # Target: did the home team win?
    merged["target"] = (merged["result_home"] == "W").astype(int)

    # Create matchup-level features (home − away)
    merged["gf_diff"] = merged["gf_home"] - merged["gf_away"]
    merged["ga_diff"] = merged["ga_home"] - merged["ga_away"]
    merged["shot_diff"] = merged["sog_for_home"] - merged["sog_for_away"]
    merged["pim_diff"] = merged["pim_for_home"] - merged["pim_for_away"]
    merged["ppo_diff"] = merged["ppo_for_home"] - merged["ppo_for_away"]
    merged["ppg_diff"] = merged["ppg_for_home"] - merged["ppg_for_away"]

    # Encode categorical vars
    merged["venue_code"] = merged["venue"].astype("category").cat.codes
    merged["opp_code"] = merged["away_team"].astype("category").cat.codes
    merged["day_code"] = merged["date"].dt.dayofweek
    merged["overtime"] = merged["ot_home"].isin(["OT", "SO"]).astype(int)

    return merged

def calculate_team_stats(games):
    #calculate stats per team
    teams = games.groupby('team')
    win_percent = []
    for team_name, team_games in teams:
        wins = team_games[team_games['result'] == 'W']
        losses = team_games[team_games['result']=='L']
        win_avg = f"{len(wins) / len(team_games) if len(team_games) > 0 else 0:.3f}"
        ratio = f"{len(wins)}:{len(losses)}"
        shots = team_games['sog_for'].sum()
        shots_avg = f"{shots/len(team_games)if len(team_games) > 0 else 0:.3f}"
        goals = team_games['gf'].sum()
        shooting_acc = f"{goals/shots if shots >0 else 0:0.3f}"
        pim = team_games['pim_for'].sum()
        avg_pim = f"{pim/len(team_games) if len(team_games) > 0 else 0:.3f}"
        team_win = [team_name, win_avg, ratio, shots_avg, shooting_acc, avg_pim]
        win_percent.append(team_win)

    #create and print stats per team dataframe sorted by probability
    column_names = ['team', 'win rate', 'win/loss ratio', 'avg shots', 'shooting accuracy', 'avg penalty min']
    win_prob = pd.DataFrame(win_percent, columns=column_names)
    win_prob = win_prob.sort_values(by="win rate", ascending=False)
    print(win_prob.to_string(index=False))

def run_predictions():
    matches = pd.read_csv("matches.csv", index_col=0)
    matches["date"] = pd.to_datetime(matches["date"]).dt.normalize()

    today = datetime.today()

    matches["team"] = matches["team"].replace({
     "Utah Hockey Club": "Utah Mammoth"
    })
    matches["opponent"] = matches["opponent"].replace({
        "Utah Hockey Club": "Utah Mammoth"
    })

    past_games = matches[matches["date"] < today].copy()
    calculate_team_stats(past_games)

    cols = ["gf","ga","sog_for","sog_against","pim_for","pim_against"]
    new_cols = [f"{c}_rolling" for c in cols]

    matches_rolling = matches.groupby("team", group_keys=False).apply(lambda x: rolling_averages(x,cols,new_cols))
    matches_rolling.index = range(matches_rolling.shape[0])

    matchups = build_matchups(matches_rolling)

    predictors = [
        "venue_code","opp_code","day_code","shot_diff","pim_diff","ppo_diff","ppg_diff","overtime",
        "gf_rolling_home","ga_rolling_home","sog_for_rolling_home","sog_against_rolling_home",
        "pim_for_rolling_home","pim_against_rolling_home",
        "gf_rolling_away","ga_rolling_away","sog_for_rolling_away","sog_against_rolling_away",
        "pim_for_rolling_away","pim_against_rolling_away"
    ]

    model = XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=4)

    #include probabilities into results
    prob_pred_df = make_predictions_prob(model, matchups, predictors, threshold=0.6)
    prob_pred_df = prob_pred_df.sort_values(by="date", ascending=True)
    print("----- Probability Predictions -----")
    print(prob_pred_df[["date", "home_team","away_team", "home_win_probability", "away_win_probability","predicted_winner"]])
    prob_pred_df.to_csv("predictions.csv", index=False)

    #get the highest probability games
    high_conf = prob_pred_df[prob_pred_df["home_win_probability"] > 0.6].sort_values(by="home_win_probability", ascending=False)
    if (not high_conf.empty):
        high_conf.to_csv("high_confidence_predictions.csv", index=False)
        print(high_conf[["date", "prediction", "home_win_probability", "away_win_probability","predicted_winner"]].head())

        top10 = high_conf.head(10)
        print(top10)

    past_matchups = matchups[matchups["date"] < today].copy()
    X = past_matchups[predictors]
    y = past_matchups["target"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)

    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    print(f"Accuracy: {accuracy_score(y_test, preds):.2f}")
    print(f"Precision: {precision_score(y_test, preds):.2f}")

    eval_df = past_matchups.iloc[y_test.index].copy()
    eval_df["predicted"] = preds
    eval_df["probability"] = probs
    eval_df["correct"] = (eval_df["predicted"] == eval_df["target"]).astype(int)
    eval_df["correct_label"] = eval_df["correct"].map({1: "Correct", 0: "Incorrect"})

    print("----- Evaluation Predictions -----")
    print(eval_df[["date", "home_team", "away_team", "predicted", "probability", "target", "correct_label"]])

    return eval_df, prob_pred_df

run_predictions()