import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score
from sklearn.model_selection import train_test_split

def rolling_averages(group, cols, new_cols):
    group = group.sort_values("date")
    rolling_stats = group[cols].rolling(3,closed='left').mean()
    group[new_cols] = rolling_stats
    group = group.dropna(subset=new_cols)
    return group

def make_predictions (model, data,predictors):
    train = data[data["date"]<'2024-01-01']
    test = data[data["date"]>'2024-01-01']
    x_train = train[predictors]
    y_train = train["target"]
    x_test = test[predictors]
    y_test = test["target"]
    model.fit(x_train, y_train)
    preds = model.predict(x_test)
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds)
    combined = pd.DataFrame(dict(actual=y_test,predicted=preds),index=test.index)
    return combined, acc, prec

def make_predictions_prob (model, data, predictors, threshold):
    train = data[data["date"] < '2024-01-01']
    test = data[data["date"] > '2024-01-01']
    x_train = train[predictors]
    y_train = train["target"]
    x_test = test[predictors]
    y_test = test["target"]
    model.fit(x_train, y_train)
    probs = model.predict_proba(x_test)[:, 1]
    preds = (probs > threshold).astype(int)
    combined = pd.DataFrame({
        "actual": y_test,
        "predicted": preds,
        "probability": probs
    }, index=test.index)
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds)
    return combined, acc, prec

def main():
    #10250 rows + 1 for titles
    matches = pd.read_csv("matches.csv", index_col=0)

    #covert columns to useable data types
    matches["date"] = pd.to_datetime(matches["date"])

    #get values to use for model
    matches["venue_code"] = matches["venue"].astype("category").cat.codes
    matches["opp_code"] = matches["opponent"].astype("category").cat.codes
    matches["day_code"] = matches["date"].dt.dayofweek
    matches["target"] = (matches['result']=='W').astype("int")
    matches["shot_diff"] = (matches["sog_for"]-matches["sog_against"])
    matches["pim_diff"] = (matches["pim_for"]-matches["pim_against"])
    matches["ppo_diff"] = (matches["ppo_for"]-matches["ppo_against"])
    matches["ppg_diff"] = (matches["ppg_for"]-matches["ppg_against"])
    matches["overtime"] = matches["ot"].isin(["OT","SO"]).astype(int)

    #initialize model
    train = matches[matches["date"]<'2024-01-01']
    test = matches[matches["date"]>'2024-01-01']
    predictors = ["venue_code","opp_code","day_code","shot_diff","pim_diff","ppo_diff","ppg_diff","overtime"]

    cols = ["gf","ga","sog_for","sog_against","pim_for","pim_against"]
    new_cols = [f"{c}_rolling" for c in cols]

    matches_rolling = matches.groupby("team").apply(lambda x: rolling_averages(x,cols,new_cols))
    matches_rolling = matches_rolling.droplevel('team')
    matches_rolling.index = range(matches_rolling.shape[0])

    x_train = train[predictors]
    y_train = train["target"]
    x_test = test[predictors]
    y_test = test["target"]

    model = XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=4)
    model.fit(x_train, y_train)

    #predict and evaluate
    preds = model.predict(x_test)
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds)

    print(f"Basic Prediction")
    print(f"Accuracy: {acc:.3f}, Precision: {prec:.3f}")
    print(f"Prediction vs. Actual Results")

    #combine test data with prediction and print table results
    combined = pd.DataFrame(dict(actual=y_test,prediction=preds))
    table = pd.crosstab(index=combined["actual"],columns=combined["prediction"])
    print(table,"\n")


    #add rolling calculations to model and print results
    combined, accuracy, precision = make_predictions (model, matches_rolling, predictors+new_cols)
    table = pd.crosstab(index=combined["actual"],columns=combined["predicted"])
    combined = combined.merge(matches_rolling[['date','team','opponent','result']],left_index=True,right_index=True)
    merged = combined.merge(combined, left_on=["date","team"], right_on=["date","opponent"])
    print("Prediction With Rolling Statistics")
    print(f"Accuracy: {accuracy:.3f}, Precision: {precision:.3f}")
    print(f"Prediction vs. Actual Results")
    print(table, "\n")
    print(merged)

    #include probabilities into results
    combined, accuracy, precision = make_predictions_prob (model, matches_rolling, predictors + new_cols, 0.6)
    combined = combined.merge(matches_rolling[['date','team','opponent','result']],left_index=True,right_index=True)
    merged = combined.merge(combined, left_on=["date","team"], right_on=["date","opponent"])
    print(f"Accuracy: {accuracy:.3f}, Precision: {precision:.3f}")
    print(merged)
    merged.to_csv("predictions.csv", index=False)

    #get the highest probability games
    high_conf = combined[combined["probability"] > 0.7]
    print(high_conf[["actual", "predicted", "probability","date","team","opponent","result"]].head())
    high_conf_sorted = high_conf.sort_values(by="probability", ascending=False)
    high_conf_sorted.to_csv("high_confidence_predictions.csv", index=False)

main()