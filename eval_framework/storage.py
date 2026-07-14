import sqlite3
from datetime import datetime
from eval_framework.config import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_label TEXT,
            test_case_name TEXT,
            metric_name TEXT,
            score REAL,
            passed INTEGER,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_run(run_label: str, case_results: list):
    conn = _connect()
    now = datetime.utcnow().isoformat()
    for case in case_results:
        for r in case.results:
            conn.execute(
                """INSERT INTO runs
                   (run_label, test_case_name, metric_name, score, passed, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (run_label, case.test_case_name, r.metric_name, r.score, int(r.passed), now),
            )
    conn.commit()
    conn.close()


def get_metric_history(metric_name: str) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT run_label, AVG(score) AS avg_score, MAX(created_at) AS created_at
        FROM runs
        WHERE metric_name = ?
        GROUP BY run_label
        ORDER BY created_at
        """,
        (metric_name,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def detect_regression(run_label: str, metric_name: str, threshold_drop: float = 0.1):
    """Compares this run's average score for a metric against the immediately
    preceding run's average. Returns a dict describing the regression if the
    score dropped by more than threshold_drop, otherwise None. This is the
    mechanism that turns evaluation from a one-off check into something that
    catches silent quality drops after a prompt change - the practice
    sometimes called 'eval driven development'."""
    history = get_metric_history(metric_name)
    if len(history) < 2:
        return None

    current = next((h for h in history if h["run_label"] == run_label), None)
    if current is None:
        return None

    current_index = history.index(current)
    if current_index == 0:
        return None
    previous = history[current_index - 1]

    drop = previous["avg_score"] - current["avg_score"]
    if drop > threshold_drop:
        return {
            "metric": metric_name,
            "previous_run": previous["run_label"],
            "previous_score": round(previous["avg_score"], 3),
            "current_score": round(current["avg_score"], 3),
            "drop": round(drop, 3),
        }
    return None
