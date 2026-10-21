import argparse
import logging
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, \
    f1_score, classification_report
import mlflow
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
    parser.add_argument("--training_data", dest="training_data", type=str, required=True)
    parser.add_argument("--validation_data", dest="validation_data", type=str, required=True)
    parser.add_argument("--n_estimators", dest="n_estimators", type=int, default=100)
    parser.add_argument("--max_depth", dest="max_depth", type=int, default=6)
    parser.add_argument("--learning_rate", dest="learning_rate", type=float, default=0.3)
    parser.add_argument("--model_output", dest="model_output", type=str, required=True)
    return parser.parse_args()


def read_folder(folder: str) -> pd.DataFrame:
    """Reads all csv files in a folder into a single dataframe."""
    files = sorted(Path(folder).glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No csv files found in {folder}")
    logger.info(f"Read {[f.name for f in files]} from {folder}")
    return pd.concat([pd.read_csv(f, header=0, sep=",") for f in files], ignore_index=True)


def split_features_target(df: pd.DataFrame):
    """Splits a dataframe into features and target."""
    return df.drop(columns=[TARGET]), df[TARGET]


if __name__ == "__main__":
    args = parse_args()

    X_train, y_train = split_features_target(read_folder(args.training_data))
    X_val, y_val = split_features_target(read_folder(args.validation_data))

    params = dict(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
    )

    logger.info(f"Train XGBoost model with params {params}")
    model = XGBClassifier(**params, eval_metric="logloss")
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    mlflow.log_params(params)

    preds = model.predict(X_val)

    metrics = dict(
        accuracy=accuracy_score(y_val, preds),
        precision=precision_score(y_val, preds),
        recall=recall_score(y_val, preds),
        f1_score=f1_score(y_val, preds)
    )
    logger.info(f"Validation metrics: {metrics}")
    mlflow.log_metrics(metrics)

    with open("classification_report.txt", "w") as f:
        f.write(classification_report(y_val, preds))
    mlflow.log_artifact("classification_report.txt")

    logger.info(f"Save model to {args.model_output}")
    mlflow.xgboost.save_model(model, args.model_output)
