"""
This application was created for my middle school that way students can test themselves for the end-year exam known as
"Eksterna Matura". It utilises the Flask framework and in-memory SQlite database. All data stored is for analytical
purposes.

Copyright (c) 2022-2022 ammarsys
"""

# Standard library imports

import json
import itertools
import string
import sqlite3
import datetime
import threading

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlite3 import Cursor

# Related third party imports

from flask import Flask, request, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS


class Database:
    def __init__(self, db_type: str = ":memory:") -> None:
        self.con = sqlite3.connect(db_type, check_same_thread=False)
        self.lock = threading.Lock()
        self.db_type = db_type

        self.user_results: dict[str, int] = {}
        self.users_num = 1
        self.user_chars = itertools.cycle(string.ascii_uppercase)

    def execute_sql(self, sql: str, *args) -> "Cursor":
        """
        This function executes SQL.

        It solves the problem where a two different threads try to share a single connection. This method uses
        `threading.Lock`. In case for whatever reason, whoever, tries to scale this, I strongly suggest rewriting
        the entire codebase in FastAPI + aiosqlite "stack" as it's far more efficient. I would have already done
        this if my desired host supported ASGI which it doesn't.
        """

        with self.lock:
            return self.con.execute(sql, *args)

    def new_id(self) -> str:
        """Creates a new unique user ID"""

        self.users_num += 1
        id_ = next(self.user_chars) + str(self.users_num)

        self.execute_sql(
            """
            INSERT INTO users (id_, time_) VALUES (?, ?);
            """,
            (id_, datetime.datetime.now()),
        )
        return id_

    def set_data(self, id_: str, score: int) -> None:
        """Updates data for an ID"""

        time = self.execute_sql(
            "SELECT time_ FROM users WHERE id_ = ?;", (id_,)
        ).fetchone()[0]

        self.execute_sql(
            """
            UPDATE users SET time_ = ?, score = ?
            WHERE id_ = ?;
            """,
            (
                round(
                    (
                        datetime.datetime.now() - datetime.datetime.fromisoformat(time)
                    ).total_seconds()
                ),
                score,
                id_,
            ),
        )

    def get_data(self, id_: str) -> Any:
        """Fetches data from the database by ID"""

        db_data = self.execute_sql(
            "SELECT ROUND(score / 150 * 100, 1), CAST(score as INT), time_ FROM users WHERE id_ = ?;",
            (id_,),
        ).fetchone()

        return db_data


app = Flask(__name__)
limiter = Limiter(app, key_func=get_remote_address)

db = Database()
CORS(app)


with open("data/tehnika.json", "r", encoding="utf8") as questions_json:
    questions_json = json.load(questions_json)


@app.before_first_request
def create_table() -> None:
    """Ensure the table is created before anything"""

    db.execute_sql(
        """
        CREATE TABLE users (
            id_ varchar, 
            score float DEFAULT 0, 
            time_ varchar
        );
        """
    )


@app.route("/api/data", methods=["POST", "GET"])
@limiter.limit(limit_value="5/second")
def data() -> tuple[dict[str], int]:
    if request.method == "GET":
        id_ = db.new_id()

        return {"code": 200, "questions": questions_json, "id": id_}, 200

    if request.method == "POST":
        id_ = request.form.get("id_", default=0)
        score = request.form.get("score", default=0)
        db.set_data(id_, score)

        return {"code": 201, "message": "user successfully updates"}, 201


@app.route("/api/data/<user_identification>", methods=["GET"])
@limiter.limit(limit_value="10/second")
def data_by_id(user_identification: str) -> tuple[dict[str], int]:
    user_data = db.get_data(user_identification)

    if user_data:
        return {"code": 200, **user_data}, 200

    return {"code": 400, "message": "user ID was not found"}, 400


@app.route("/", methods=["GET"])
def index() -> str:
    return render_template("index.html")


@app.route("/quiz", methods=["GET"])
def quiz() -> str:
    return render_template("quiz.html")


@app.route("/privacypolicy", methods=["GET"])
def privacy() -> str:
    return render_template("privacypolicy.html")


if __name__ == "__main__":
    app.run(debug=True)
