r"""
Train a model that predicts whether a driver finishes ON THE PODIUM (top 3)
in a race, using only information known BEFORE the race starts:
  - grid        : starting position on the grid
  - year        : the season
  - constructor : the team

Because we only use pre-race info, the model isn't "cheating" by peeking at
the result. That's an important habit in ML — no data leakage.

Run:    .\.venv\Scripts\python.exe ml\train_model.py
Output: ml\podium_model.joblib   (this is what the dashboard loads)
"""
import sqlite3
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "f1.db"
MODEL_PATH = ROOT / "ml" / "podium_model.joblib"


def load_training_data() -> pd.DataFrame:
    """One row per race entry: the features, plus the answer (podium yes/no)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(
            """
            SELECT
                r.grid                                            AS grid,
                ra.year                                           AS year,
                c.name                                            AS constructor,
                CASE WHEN r.positionOrder <= 3 THEN 1 ELSE 0 END  AS podium
            FROM results r
            JOIN races ra       ON ra.raceId       = r.raceId
            JOIN constructors c ON c.constructorId = r.constructorId
            WHERE r.grid > 0     -- ignore pit-lane starts / missing grid data
            """,
            conn,
        )
    finally:
        conn.close()


def main() -> None:
    df = load_training_data()

    # Models need numbers, not words. "One-hot encoding" turns the constructor
    # column into one yes/no (1/0) column per team.
    X = pd.get_dummies(df[["grid", "year", "constructor"]], columns=["constructor"])
    y = df["podium"]

    # Hold back 20% of the data to TEST on, so we measure performance on races
    # the model has never seen (stratify keeps the podium ratio the same).
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200, max_depth=12, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate on the held-back test set.
    preds = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    print(f"Training rows : {len(df):,}")
    print(f"Podium rate   : {y.mean():.1%}  (how often a podium actually happens)")
    print(f"Accuracy      : {accuracy_score(y_test, preds):.3f}")
    print(f"ROC AUC       : {roc_auc_score(y_test, proba):.3f}  (0.5 = guessing, 1.0 = perfect)")

    # Save the model AND the exact column order, so the dashboard can build a
    # matching input row when it asks for a prediction.
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"model": model, "columns": X.columns.tolist()}, MODEL_PATH)
    print(f"\nSaved model -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
