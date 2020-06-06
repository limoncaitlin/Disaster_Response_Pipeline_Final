#imports
import numpy as np
import nltk
nltk.download(['punkt', 'wordnet'])
import re
import sys
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import pandas as pd
from sqlalchemy import create_engine
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier,AdaBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import make_scorer, accuracy_score, f1_score, fbeta_score, classification_report
from sklearn.datasets import make_multilabel_classification
from sklearn.model_selection import GridSearchCV
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import precision_recall_fscore_support
import joblib

def load_data(path_to_database):
    """
    Function to load data from a sql database and import it as a 
    pandas dataframe.
    Args:
        path_to_database: path to the sql database file
    Returns: 
        X: Message data (features for the model)
        y: Categories (target to predict)
        category_names: name of each category of y
    """
    engine = create_engine('sqlite:///'+path_to_database)
    df = pd.read_sql('disaster_data',engine)
    X = df['message']
    y = df.iloc[:,4:]
    category_names = y.columns
    return X, y, category_names

def tokenize(text):
    """
    Function to tokenize and lemmatize the text.
    Args:
        text (string): message to tokenize and lemmatize
    Returns: 
        list of tokens that have been tokenized, lemmatized, lower cased and
        cleaned
    """
    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()

    cleaned_tokens = []
    for i in tokens:
        clean_token = lemmatizer.lemmatize(i).lower().strip()
        cleaned_tokens.append(clean_token)

    return cleaned_tokens

def build_model():
    """
    Builds a model using MultiOutputClassifier implementing a Random Forest 
    Classifier with GridSearch to optimize some parameters.
    Args:
        None
    Returns:
        cv (model with parameters from GridSearch) 
    """
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('clf', MultiOutputClassifier(RandomForestClassifier()))])
    parameters = {
            'tfidf__use_idf': (True, False), 'tfidf__smooth_idf': (True, False),
            'tfidf__sublinear_tf': (True, False)}

    cv = GridSearchCV(pipeline, param_grid=parameters, verbose=10)
    return cv

def evaluate_model(model, X_test, y_test, category_names):
    """
    Use the model to predict on the test set. Then evaluate the accuracy
    Args:
        model
        X_test
        y_test
        category_names
    Returns: Print out of precision and recall for each category as well as overall 
    accuracy and F1 score for the model.
    """
    # predict test df
    y_pred = model.predict(X_test)
    total_accuracy = 0
    total_f1 = 0
    # print report 
    for i, category in enumerate(category_names):    
        class_report =  classification_report(y_test[y_test.columns[i]], y_pred[:,i])
        total_accuracy += accuracy_score(y_test[y_test.columns[i]], y_pred[:,i])
        total_f1 += precision_recall_fscore_support(y_test[y_test.columns[i]], y_pred[:,i], average = 'weighted')[2]
        print(category, 'accuracy: {:.5f}'.format(accuracy_score(y_test[y_test.columns[i]], y_pred[:,i])))
        print(class_report)
    print('total accuracy {:.5f}'.format(total_accuracy/len(category_names)))
    print('total f1 {:.5f}'.format(total_f1/len(category_names)))

def save_model(model, filepath):
    """
    Function to save the model as a pickle file.
    Args:
        model: the model generated by the build model function
        filepath: the path where the model should be saved
    Returns:
        A pickle file containing the model
    """
    joblib.dump(model, 'disaster_model.pkl')

def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()