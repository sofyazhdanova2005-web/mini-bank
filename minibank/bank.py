"""Бизнес-логика банка. Работает с SQLite, интерфейса не знает."""

import os
import random
import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


class BankError(Exception):
    """Ошибка, которую можно показать пользователю."""


def default_db_path() -> Path:
    """База лежит в папке пользователя, потому что Program Files только для чтения."""
    base = os.environ.get("APPDATA") or str(Path.home())
    folder = Path(base) / "MiniBank"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "minibank.db"


def rub_to_kop(text) -> int:
    """'1 250,50' -> 125050"""
    s = str(text).replace(" ", "").replace(",", ".")
    try:
        value = round(float(s) * 100)
    except ValueError:
        raise BankError("Сумма указана неверно")
    if value <= 0:
        raise BankError("Сумма должна быть больше нуля")
    return value


def kop_to_rub(kop: int) -> str:
    """125050 -> '1 250,50'"""
    rub, k = divmod(int(kop), 100)
    return f"{rub:,}".replace(",", " ") + f",{k:02d}"


class Bank:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.conn.commit()

    def close(self):
        self.conn.close()

    # ---------- клиенты ----------
    def add_client(self, full_name: str, passport: str, phone: str = "") -> int:
        full_name, passport = full_name.strip(), passport.strip()
        if not full_name:
            raise BankError("Укажите ФИО клиента")
        if not passport:
            raise BankError("Укажите паспорт клиента")
        try:
            cur = self.conn.execute(
                "INSERT INTO clients (full_name, passport, phone) VALUES (?, ?, ?)",
                (full_name, passport, phone.strip()),
            )
        except sqlite3.IntegrityError:
            raise BankError("Клиент с таким паспортом уже есть")
        self.conn.commit()
        return cur.lastrowid

    def clients(self):
        return self.conn.execute("SELECT * FROM clients ORDER BY full_name").fetchall()

    # ---------- счета ----------
    def account_types(self):
        return self.conn.execute("SELECT * FROM account_types ORDER BY id").fetchall()

    def _new_number(self) -> str:
        while True:
            number = "40817810" + "".join(random.choice("0123456789") for _ in range(12))
            exists = self.conn.execute(
                "SELECT 1 FROM accounts WHERE number = ?", (number,)
            ).fetchone()
            if not exists:
                return number

    def open_account(self, client_id: int, type_id: int = 1) -> int:
        try:
            cur = self.conn.execute(
                "INSERT INTO accounts (number, client_id, type_id) VALUES (?, ?, ?)",
                (self._new_number(), client_id, type_id),
            )
        except sqlite3.IntegrityError:
            raise BankError("Клиент или вид счёта не найден")
        self.conn.commit()
        return cur.lastrowid

    def accounts(self):
        return self.conn.execute(
            """SELECT a.id, a.number, a.balance, a.opened_at,
                      c.full_name, t.name AS type_name
               FROM accounts a
               JOIN clients c ON c.id = a.client_id
               JOIN account_types t ON t.id = a.type_id
               ORDER BY c.full_name, a.id"""
        ).fetchall()

    def balance(self, account_id: int) -> int:
        row = self.conn.execute(
            "SELECT balance FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        if row is None:
            raise BankError("Счёт не найден")
        return row["balance"]

    # ---------- операции ----------
    def deposit(self, account_id: int, amount: int, comment: str = "") -> None:
        if amount <= 0:
            raise BankError("Сумма должна быть больше нуля")
        self.balance(account_id)  # проверка, что счёт есть
        with self.conn:
            self.conn.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (amount, account_id),
            )
            self.conn.execute(
                "INSERT INTO transactions (kind, to_account_id, amount, comment) "
                "VALUES ('DEPOSIT', ?, ?, ?)",
                (account_id, amount, comment),
            )

    def withdraw(self, account_id: int, amount: int, comment: str = "") -> None:
        if amount <= 0:
            raise BankError("Сумма должна быть больше нуля")
        if self.balance(account_id) < amount:
            raise BankError("Недостаточно средств на счёте")
        with self.conn:
            self.conn.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (amount, account_id),
            )
            self.conn.execute(
                "INSERT INTO transactions (kind, from_account_id, amount, comment) "
                "VALUES ('WITHDRAW', ?, ?, ?)",
                (account_id, amount, comment),
            )

    def transfer(self, from_id: int, to_id: int, amount: int, comment: str = "") -> None:
        if from_id == to_id:
            raise BankError("Нельзя перевести деньги на тот же счёт")
        if amount <= 0:
            raise BankError("Сумма должна быть больше нуля")
        self.balance(to_id)
        if self.balance(from_id) < amount:
            raise BankError("Недостаточно средств на счёте")
        # with self.conn: обе записи проходят вместе или откатываются вместе
        with self.conn:
            self.conn.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, from_id)
            )
            self.conn.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, to_id)
            )
            self.conn.execute(
                "INSERT INTO transactions (kind, from_account_id, to_account_id, amount, comment) "
                "VALUES ('TRANSFER', ?, ?, ?, ?)",
                (from_id, to_id, amount, comment),
            )

    def history(self, limit: int = 200):
        return self.conn.execute(
            """SELECT t.id, t.created_at, t.kind, t.amount, t.comment,
                      fa.number AS from_number, ta.number AS to_number
               FROM transactions t
               LEFT JOIN accounts fa ON fa.id = t.from_account_id
               LEFT JOIN accounts ta ON ta.id = t.to_account_id
               ORDER BY t.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
