import argparse
import logging 
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.model_selection import train_test_split
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)

logging.basicConfig(
        level="INFO",
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

TARGET = "Diabetic"


def parse_args() -> argparse.Namespace:
    """Parses the command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_data", dest="input_data", type=str, required=True)
    parser.add_argument("--valid_size", dest="valid_size", type=float, required=True)
    parser.add_argument("--scaler", dest="scaler", type=str, choices=["standard", "robust", "minmax"], default="standard")
    parser.add_argument("--training_data", dest="training_data", type=str, required=True)
    parser.add_argument("--validation_data", dest="validation_data", type=str, required=True)
    return parser.parse_args()


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

    X,y = df[features].values, df[TARGET].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=0)

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

def to_dataframe(X, y) -> pd.DataFrame:
    """Combines scaled features and target into a single dataframe."""
    df = pd.DataFrame(X, columns=get_features())
    df[TARGET] = y
    return df

if __name__ == "__main__":
    args = parse_args()

    logger.info(f"Read data from {args.input_data}")
    df = pd.read_csv(args.input_data, header=0, sep=",")

    logger.info(f"Split data into training and validation set (with value {args.valid_size})")
    X_train, X_val, y_train, y_val = split_data(df, test_size=args.valid_size)

    logger.info(f"Scale data with {args.scaler} scaler")
    scaler_alg = get_scaler(args.scaler)
    X_train_s = scaler_alg.fit_transform(X_train)
    X_val_s = scaler_alg.transform(X_val)

    logger.info(f"Write training data to {args.training_data}")
    Path(args.training_data).mkdir(parents=True, exist_ok=True)
    to_dataframe(X_train_s, y_train).to_csv(Path(args.training_data) / "train-data.csv", index=False)

    logger.info(f"Write validation data to {args.validation_data}")
    Path(args.validation_data).mkdir(parents=True, exist_ok=True)
    to_dataframe(X_val_s, y_val).to_csv(Path(args.validation_data) / "validation-data.csv", index=False)
