# NHL-Predictor
<h2>Description</h2>

This project is a machine learning-based NHL game outcome predictor that uses historical game data (2021–2025) to forecast match results. The model incorporates team stats, venue, opponent, shot differentials, penalties, and rolling averages to improve prediction accuracy.

------------------------------------------------------------------------------------
## Features

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
## Architecture
- Data ingestion: Web scraping using BeautifulSoup
- Processing: Pandas feature engineering and rolling averages
- Model: XGBoost classifier
- Interface: Streamlit app for retraining and visualization

------------------------------------------------------------------------------------
## Installation

1) Clone the repository:
    - git clone https://github.com/sierraoliver/NHL-Predictor.git
    - cd NHL-Predictor

2) Install required Python packages:
    - pip install pandas xgboost scikit-learn streamlit beautifulsoup4 requests lxml
  
3) Run the application:
    - streamlit run app.py

-------------------------------------------------------------------------------------
## Motivation
I built this project to explore how machine learning can be used to make probabilistic predictions on real-world sports data, and to practice building an end-to-end data pipeline from scraping to deployment.

-------------------------------------------------------------------------------------
