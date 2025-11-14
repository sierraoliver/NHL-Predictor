import streamlit as st

from match_predictor import run_predictions
from read_stats import read_stats

st.title("NHL Match Predictor")

# Button to update stats
if st.button("Update Stats"):
    with st.spinner("Updating stats..."):
        read_stats()  # Call the function when button is clicked
        st.success("Stats updated!")
    
    # Run predictions with updated data
    eval_df, prob_pred_df, high_conf = run_predictions()
    
    st.subheader("High Confidence Predictions")
    st.dataframe(high_conf)
    
    st.subheader("All Predictions")
    st.dataframe(prob_pred_df)

else:
    # Show predictions with existing data (no update)
    eval_df, prob_pred_df, high_conf = run_predictions()
    
    st.subheader("High Confidence Predictions")
    st.dataframe(high_conf[["date","season", "home_team", "away_team", "home_win_probability", "away_win_probability","predicted_winner"]])
    
    st.subheader("All Predictions")
    st.dataframe(prob_pred_df[["date","season", "home_team", "away_team", "home_win_probability", "away_win_probability","prediction", "predicted_winner"]])
