import argparse
import logging 
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, \
    confusion_matrix, f1_score, classification_report
import mlflow
from typing import List

logger = logging.getLogger(__name__)

logging.basicConfig(
        level="INFO",
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

parser = argparse.ArgumentParser()
parser.add_argument("--training_data", dest="training_data", type=str, required=True)
parser.add_argument("--regularization", dest="regularization", type=float, required=True)
parser.add_argument("--valid_size", dest="valid_size", type=float, required=True)
parser.add_argument("--scaler", dest="scaler", type=str, choices=["standard", "robust", "minmax"], default="standard",)
args = parser.parse_args()

def get_features() -> List[str]:
    """Returns a list of features which will be included."""
    return [
        'Pregnancies',
        'PlasmaGlucose',
        'DiastolicBloodPressure',
        'TricepsThickness',
        'SerumInsulin',
        'BMI',
        'DiabetesPedigree',
        'Age'
    ]

def split_data(df:pd.DataFrame, test_size=0.3):
    """Splits a dataframe into a train and test set.
    
    Args:
        df: The dataframe to split
        test_size: the test size porportionally to the dataframe

    Returns:
        List of numpy arrays
    """
    logger.info(f"Splitting dataframe with test_size={test_size}")

    features = get_features()
    target = "Diabetic"

    X,y = df[features].values, df[target].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)

    logger.info(f"{len(y_train)} records in training set and {len(y_test)} records in test set")

    return X_train, X_test, y_train, y_test

def get_scaler(scaler:str):
    """Function returns the desired scaler."""
    logger.info(f"Scaling with scaler type: {scaler}")

    if scaler.lower() == "minmax":
        return MinMaxScaler()
    elif scaler.lower() == "standard":
        return StandardScaler()
    elif scaler.lower() == "robust":
        return RobustScaler()
    else:
        raise ValueError("Unknown value for scaler. Pick from list: ['minmax', 'standard', 'robust']")


if __name__ == "__main__":

    logger.info(f"Read data from {args.training_data}")
    df = pd.read_csv(args.training_data, header=0, sep=",")

    logger.info(f"Split data into training and validation set (with value {args.valid_size})")
    X_train, X_val, y_train, y_val = split_data(df, test_size=args.valid_size)

    logger.info(f"Scale data with {args.scaler} scaler")
    scaler_alg = get_scaler(args.scaler)
    X_train_s = scaler_alg.fit_transform(X_train)
    X_val_s = scaler_alg.transform(X_val)

    logger.info("Train logistic regression model and log parameters")

    params = dict(
        C=1/args.regularization,
        solver="liblinear"
    )

    model = LogisticRegression(**params).fit(X_train, y_train)
    mlflow.log_params(params)

    preds = model.predict(X_val_s)

    metrics = dict(
        accuracy=accuracy_score(y_val, preds),
        precision=precision_score(y_val, preds),
        recall=recall_score(y_val, preds),
        f1_score=f1_score(y_val, preds)
    )
    mlflow.log_metrics(metrics)

    with open("classification_report.txt", "w") as f:
        report = classification_report(y_val, preds)
        f.write(report)
    mlflow.log_artifact("classification_report.txt")



