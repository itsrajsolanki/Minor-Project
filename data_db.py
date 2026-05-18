
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "predictions.db")


def init_data_db() -> None:
    """Create the predictions table if it does not exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                username     TEXT    NOT NULL,
                -- Inputs
                nitrogen     REAL    NOT NULL,
                phosphorus   REAL    NOT NULL,
                potassium    REAL    NOT NULL,
                ph           REAL    NOT NULL,
                location     TEXT    NOT NULL,
                -- Weather fetched
                temperature  REAL,
                humidity     REAL,
                rainfall     REAL,
                -- Outputs
                top_crop_1   TEXT,
                confidence_1 REAL,
                top_crop_2   TEXT,
                confidence_2 REAL,
                top_crop_3   TEXT,
                confidence_3 REAL,
                is_suitable  INTEGER,
                alert_message TEXT,
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def log_prediction(
    username: str,
    inputs: dict,
    weather: dict,
    top_crops: list,
    is_suitable: bool,
    alert_message: str,
) -> int:
    """
    Insert one prediction record and return the new row id.
    
    `inputs`  : {N, P, K, ph, location}
    `weather` : {temperature, humidity, rainfall}
    `top_crops`: [{"crop": str, "confidence": float}, ...]  (up to 3 items)
    """
    crops = (top_crops + [{}, {}, {}])[:3]           # ensure exactly 3 slots

    def _c(idx, key, default=None):
        return crops[idx].get(key, default)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO predictions
                (username, nitrogen, phosphorus, potassium, ph, location,
                 temperature, humidity, rainfall,
                 top_crop_1, confidence_1,
                 top_crop_2, confidence_2,
                 top_crop_3, confidence_3,
                 is_suitable, alert_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                inputs["N"], inputs["P"], inputs["K"], inputs["ph"], inputs["location"],
                weather.get("temperature"), weather.get("humidity"), weather.get("rainfall"),
                _c(0, "crop"), _c(0, "confidence"),
                _c(1, "crop"), _c(1, "confidence"),
                _c(2, "crop"), _c(2, "confidence"),
                int(is_suitable), alert_message,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_user_predictions(username: str) -> list:
    """Return all prediction rows for a given user (newest first)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM predictions WHERE username = ? ORDER BY created_at DESC",
            (username,),
        ).fetchall()
    return [dict(r) for r in rows]


# Auto-initialise on import
init_data_db()
