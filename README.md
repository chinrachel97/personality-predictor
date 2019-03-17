# personality-predictor

This simple script does the following:
- Takes in a CSV of IDs, along with their corresponding personality scores
- Reads tweets in from gzip files for each user given the directory containing user json + gzip files (the output files from Habeeb's twitter crawler)
- Cleans the tweets: takes out unicode characters (assumed to be emojis) and non-alphabetical tokens
- Uses 25 tweet/user-based features to predict SDO and RWA score
- Runs regression on the features created and random real-numbered y-labels as personality scores (this will be replaced the ground truth when it is available)
- Returns real-valued predictions, correlation coefficients for each feature, mean squared error and variance score

Temporarily Unusable Functionalities:
- Performs feature selection by removing all but the highest scoring percentage of features (percentage defined by user)
- Performs topic modeling with LDA - included in the script in case it might produce some useful insights

To Do:
- Compare SelectPercentile(...) and SelectKBest(...)
- Add k-fold cross-validation
- Add option to save/load ML model
    - https://machinelearningmastery.com/save-load-machine-learning-models-python-scikit-learn/
- Use and compare the following regression models:
    - Linear Regression (current)
    - Ridge Regression
    - Least Angle Regression
    - Bayesian Regression
    - Logistic Regression
    - SVM Regression
    - Nearest Neighbors Regression
    - Decision Trees Regression
    - Gradient Tree Boosting Regression
    - NN Regression (Use code from research with Dr. Jiang)
- Compare results of using TF-IDF (use TfidfVectorizer(...) instead of CountVectorizer(...)) for regression instead (currently just TF)
- With either TfidfVectorizer(...) and CountVectorizer(...), add params like specifying n-grams 
- Write all results to a .log or .csv file
- Refine token filtering: don't just throw out anything that contains non-alphabetic characters
- Keep emojis
    - https://stackoverflow.com/questions/43146528/how-to-extract-all-the-emojis-from-text
- Write another script to run this automatically with different options (which models, what parameters, etc.)
- Display statistics/results graphically
- Use emojis as a feature