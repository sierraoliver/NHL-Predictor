# NHL-Predictor
<h2>Description</h2>

This project is a machine learning-based NHL game outcome predictor that uses historical game data (2021–2025) to forecast match results. The model incorporates team stats, venue, opponent, shot differentials, penalties, and rolling averages to improve prediction accuracy.

------------------------------------------------------------------------------------
<h2>Features</h2>

- Data Collection: Web scraper extracts detailed NHL game data including scores, shots, penalties, and results.

- Feature Engineering: Converts categorical variables (venue, opponent) into numeric codes; computes shot and penalty differentials.

- Rolling Averages: Calculates 3-game rolling averages for key statistics to capture recent team momentum.

- Model: Uses XGBoost classifier to predict game outcomes.

- Evaluation: Reports accuracy (~63%) and precision (~66%) metrics

- Results: Displays high-confidence predictions with probabilities.

- Interactive Streamlit Application:
    - Update game data on demand
    - Retrain the prediction model
    - View upcoming game predictions with win probabilities
    - Highlight high-confidence matchups in tabular form

------------------------------------------------------------------------------------
<h2>Installation</h2>

1) Clone the repository:
    - git clone https://github.com/yourusername/NHL-Predictor.git

2) Install required Python packages:
    - pip install pandas xgboost scikit-learn streamlit beautifulsoup4 requests lxml
  
3) Run the application:
    - streamlit run app.py

-------------------------------------------------------------------------------------
<h2>Project Structure</h2>

├── read_stats.py          # Web scraping and data updates
├── match_predictor.py     # Feature engineering and prediction logic
├── app.py                 # Streamlit application
├── matches.csv            # Stored historical game data
├── predictions.csv        # Generated predictions
├── README.md

-------------------------------------------------------------------------------------
