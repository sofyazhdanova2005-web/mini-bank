"""Окно программы на Tkinter."""

import tkinter as tk
from tkinter import messagebox, ttk

from . import __version__
from .bank import Bank, BankError, default_db_path, kop_to_rub, rub_to_kop

KIND_NAMES = {"DEPOSIT": "Пополнение", "WITHDRAW": "Снятие", "TRANSFER": "Перевод"}


class App(tk.Tk):
    def __init__(self, bank: Bank):
        super().__init__()
        self.bank = bank
        self.title(f"Мини-банк {__version__}")
        self.geometry("900x560")
        self.minsize(760, 480)

        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)
        tabs.add(self._clients_tab(tabs), text="Клиенты")
        tabs.add(self._accounts_tab(tabs), text="Счета")
        tabs.add(self._transfer_tab(tabs), text="Переводы")
        tabs.add(self._history_tab(tabs), text="История")
        tabs.bind("<<NotebookTabChanged>>", lambda e: self.refresh())
        tabs.enable_traversal()  # Ctrl+Tab переключает вкладки

        self.refresh()

    # ---------- общие помощники ----------
    @staticmethod
    def _table(parent, columns):
        frame = ttk.Frame(parent)
        tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings")
        for key, title, width in columns:
            tree.heading(key, text=title)
            tree.column(key, width=width, anchor="w")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return frame, tree

    def _run(self, action, ok_text):
        try:
            action()
        except BankError as e:
            messagebox.showwarning("Мини-банк", str(e))
            return False
        self.refresh()
        if ok_text:
            messagebox.showinfo("Мини-банк", ok_text)
        return True

    # ---------- вкладка «Клиенты» ----------
    def _clients_tab(self, parent):
        tab = ttk.Frame(parent, padding=10)
        form = ttk.LabelFrame(tab, text="Новый клиент", padding=10)
        form.pack(fill="x")

        self.e_name, self.e_passport, self.e_phone = (ttk.Entry(form, width=30) for _ in range(3))
        for i, (label, entry) in enumerate(
            [("ФИО", self.e_name), ("Паспорт", self.e_passport), ("Телефон", self.e_phone)]
        ):
            ttk.Label(form, text=label).grid(row=0, column=i * 2, padx=(0, 4), sticky="w")
            entry.grid(row=0, column=i * 2 + 1, padx=(0, 12))
        ttk.Button(form, text="Добавить", command=self._add_client).grid(row=0, column=6)

        frame, self.t_clients = self._table(
            tab,
            [("id", "№", 50), ("name", "ФИО", 300), ("passport", "Паспорт", 160),
             ("phone", "Телефон", 140), ("created", "Дата регистрации", 160)],
        )
        frame.pack(fill="both", expand=True, pady=(10, 0))
        return tab

    def _add_client(self):
        def action():
            self.bank.add_client(self.e_name.get(), self.e_passport.get(), self.e_phone.get())
        if self._run(action, None):
            for e in (self.e_name, self.e_passport, self.e_phone):
                e.delete(0, "end")

    # ---------- вкладка «Счета» ----------
    def _accounts_tab(self, parent):
        tab = ttk.Frame(parent, padding=10)

        form = ttk.LabelFrame(tab, text="Открыть счёт", padding=10)
        form.pack(fill="x")
        ttk.Label(form, text="Клиент").grid(row=0, column=0, padx=(0, 4))
        self.cb_client = ttk.Combobox(form, state="readonly", width=35)
        self.cb_client.grid(row=0, column=1, padx=(0, 12))
        ttk.Label(form, text="Вид счёта").grid(row=0, column=2, padx=(0, 4))
        self.cb_type = ttk.Combobox(form, state="readonly", width=18)
        self.cb_type.grid(row=0, column=3, padx=(0, 12))
        ttk.Button(form, text="Открыть", command=self._open_account).grid(row=0, column=4)

        cash = ttk.LabelFrame(tab, text="Касса (для выбранного в таблице счёта)", padding=10)
        cash.pack(fill="x", pady=(10, 0))
        ttk.Label(cash, text="Сумма, ₽").grid(row=0, column=0, padx=(0, 4))
        self.e_cash = ttk.Entry(cash, width=15)
        self.e_cash.grid(row=0, column=1, padx=(0, 12))
        ttk.Button(cash, text="Пополнить", command=lambda: self._cash(True)).grid(row=0, column=2, padx=4)
        ttk.Button(cash, text="Снять", command=lambda: self._cash(False)).grid(row=0, column=3, padx=4)

        frame, self.t_accounts = self._table(
            tab,
            [("id", "№", 50), ("number", "Номер счёта", 200), ("client", "Клиент", 240),
             ("type", "Вид", 130), ("balance", "Остаток, ₽", 130), ("opened", "Открыт", 150)],
        )
        frame.pack(fill="both", expand=True, pady=(10, 0))
        return tab

    def _open_account(self):
        ci, ti = self.cb_client.current(), self.cb_type.current()
        if ci < 0 or ti < 0:
            messagebox.showwarning("Мини-банк", "Выберите клиента и вид счёта")
            return
        self._run(lambda: self.bank.open_account(self._client_ids[ci], self._type_ids[ti]),
                  "Счёт открыт")

    def _cash(self, is_deposit):
        sel = self.t_accounts.selection()
        if not sel:
            messagebox.showwarning("Мини-банк", "Выберите счёт в таблице")
            return
        acc_id = int(sel[0])

        def action():
            amount = rub_to_kop(self.e_cash.get())
            if is_deposit:
                self.bank.deposit(acc_id, amount, "Касса")
            else:
                self.bank.withdraw(acc_id, amount, "Касса")
        if self._run(action, None):
            self.e_cash.delete(0, "end")

    # ---------- вкладка «Переводы» ----------
    def _transfer_tab(self, parent):
        tab = ttk.Frame(parent, padding=20)
        ttk.Label(tab, text="Перевод между счетами", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self.cb_from = ttk.Combobox(tab, state="readonly", width=60)
        self.cb_to = ttk.Combobox(tab, state="readonly", width=60)
        self.e_amount = ttk.Entry(tab, width=20)
        self.e_comment = ttk.Entry(tab, width=60)
        rows = [("Со счёта", self.cb_from), ("На счёт", self.cb_to),
                ("Сумма, ₽", self.e_amount), ("Комментарий", self.e_comment)]
        for i, (label, w) in enumerate(rows, start=1):
            ttk.Label(tab, text=label).grid(row=i, column=0, sticky="w", pady=4, padx=(0, 10))
            w.grid(row=i, column=1, sticky="w", pady=4)
        ttk.Button(tab, text="Перевести", command=self._transfer).grid(
            row=5, column=1, sticky="w", pady=(12, 0))
        return tab

    def _transfer(self):
        fi, ti = self.cb_from.current(), self.cb_to.current()
        if fi < 0 or ti < 0:
            messagebox.showwarning("Мини-банк", "Выберите оба счёта")
            return

        def action():
            self.bank.transfer(self._account_ids[fi], self._account_ids[ti],
                               rub_to_kop(self.e_amount.get()), self.e_comment.get().strip())
        if self._run(action, "Перевод выполнен"):
            self.e_amount.delete(0, "end")
            self.e_comment.delete(0, "end")

    # ---------- вкладка «История» ----------
    def _history_tab(self, parent):
        tab = ttk.Frame(parent, padding=10)
        frame, self.t_history = self._table(
            tab,
            [("date", "Дата", 150), ("kind", "Операция", 110), ("from", "Со счёта", 190),
             ("to", "На счёт", 190), ("amount", "Сумма, ₽", 110), ("comment", "Комментарий", 160)],
        )
        frame.pack(fill="both", expand=True)
        return tab

    # ---------- обновление всех данных ----------
    def refresh(self):
        clients = self.bank.clients()
        self.t_clients.delete(*self.t_clients.get_children())
        for c in clients:
            self.t_clients.insert("", "end", values=(c["id"], c["full_name"], c["passport"],
                                                     c["phone"], c["created_at"]))
        self._client_ids = [c["id"] for c in clients]
        self.cb_client["values"] = [f'{c["full_name"]} ({c["passport"]})' for c in clients]

        types = self.bank.account_types()
        self._type_ids = [t["id"] for t in types]
        self.cb_type["values"] = [t["name"] for t in types]
        if types and self.cb_type.current() < 0:
            self.cb_type.current(0)

        accounts = self.bank.accounts()
        self.t_accounts.delete(*self.t_accounts.get_children())
        for a in accounts:
            self.t_accounts.insert("", "end", iid=str(a["id"]), values=(
                a["id"], a["number"], a["full_name"], a["type_name"],
                kop_to_rub(a["balance"]), a["opened_at"]))
        self._account_ids = [a["id"] for a in accounts]
        labels = [f'{a["number"]} · {a["full_name"]} · {kop_to_rub(a["balance"])} ₽'
                  for a in accounts]
        self.cb_from["values"] = labels
        self.cb_to["values"] = labels

        self.t_history.delete(*self.t_history.get_children())
        for h in self.bank.history():
            self.t_history.insert("", "end", values=(
                h["created_at"], KIND_NAMES.get(h["kind"], h["kind"]),
                h["from_number"] or "—", h["to_number"] or "—",
                kop_to_rub(h["amount"]), h["comment"] or ""))


def main():
    bank = Bank(default_db_path())
    app = App(bank)
    app.mainloop()
    bank.close()


if __name__ == "__main__":
    main()
