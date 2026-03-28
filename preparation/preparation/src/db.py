from __future__ import annotations

import os
from pathlib import Path
from sqlalchemy import create_engine
from dotenv import load_dotenv

# 项目根目录（src 的上一级），便于从任意工作目录运行脚本时都能找到 config/db.env
_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_engine(env_path: str = "config/db.env"):
    """
    MySQL SQLAlchemy engine.
    env variables:
      DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    """
    path = Path(env_path)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    load_dotenv(path)

    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "root")
    pwd = os.getenv("DB_PASSWORD", "")
    db = os.getenv("DB_NAME", "cocktail_graph")

    url = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset=utf8mb4"
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=3600,
        future=True,
    )

# ===== compatibility wrapper for Step2/Step3 =====
def get_conn():
    """
    Step2/Step3 expects get_conn() -> pymysql connection
    If your project already has another function (e.g. get_db / connect / get_connection),
    please map it here.
    """
    # 方案 A：如果你已经有现成的函数，比如叫 get_db()
    # return get_db()

    # 方案 B：如果你已经有现成的函数，比如叫 connect()
    # return connect()

    # 方案 C：如果你没有，就直接把下面这段连接逻辑写在这里（我给你完整可用版）
    from pathlib import Path
    import pymysql

    def _load_env(env_path: Path):
        data = {}
        for line in env_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            data[k.strip()] = v.strip()
        return data

    root = Path(__file__).resolve().parents[1]  # GRADUATION/
    env = _load_env(root / "config" / "db.env")

    return pymysql.connect(
        host=env.get("DB_HOST", "127.0.0.1"),
        port=int(env.get("DB_PORT", "3306")),
        user=env.get("DB_USER", "root"),
        password=env.get("DB_PASSWORD", ""),
        database=env.get("DB_NAME", "cocktail_graph"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

if __name__ == "__main__":
    c = get_conn()
    with c.cursor() as cur:
        cur.execute("SELECT 1")
        print(cur.fetchone())
    c.close()
