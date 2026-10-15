import argparse
import logging 
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from typing import List

logger = logging.getLogger(__name__)

logging.basicConfig(
        level="INFO",
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

parser = argparse.ArgumentParser()

parser.add_argument("--training_data", dest="training_data", type=str, required=True)

args = parser.parse_args()

def get_data(path) -> pd.DataFrame:
    """ Get the data from a specific location. Reads as csv. 

    Returns:
        The data as a dataframe.
    """
    logger.info(f"Gathering data into dataframe from location {args.training_data}")
    return pd.read_csv(path, header=0, sep=",")

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


def main():
    # Read data
    df = get_data(args.training_data)

    # split data
    X_train, X_test, y_train, y_test = split_data(df, test_size=0.3)

    # scale data
    scaler = get_scaler("standard")
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

if __name__ == "__main__":
    main()


