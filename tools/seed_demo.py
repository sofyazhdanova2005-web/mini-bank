"""Заполняет базу демонстрационными данными (для скриншотов и показа)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from minibank.bank import Bank, default_db_path  # noqa: E402

bank = Bank(default_db_path())
if bank.clients():
    print("В базе уже есть данные, пропускаю")
    sys.exit(0)

anna = bank.add_client("Иванова Анна Сергеевна", "2510 123456", "+7 914 000-11-22")
petr = bank.add_client("Петров Пётр Алексеевич", "2511 654321", "+7 924 555-33-44")
olga = bank.add_client("Смирнова Ольга Викторовна", "2509 777888", "+7 902 123-45-67")

a1 = bank.open_account(anna, 1)
a2 = bank.open_account(anna, 2)
p1 = bank.open_account(petr, 1)
o1 = bank.open_account(olga, 1)

bank.deposit(a1, 15_000_000, "Зарплата")
bank.deposit(p1, 4_250_000, "Касса")
bank.deposit(o1, 980_000, "Касса")
bank.transfer(a1, a2, 5_000_000, "На накопления")
bank.transfer(a1, p1, 1_250_050, "Возврат долга")
bank.transfer(p1, o1, 300_000, "Подарок")
bank.withdraw(o1, 150_000, "Касса")
bank.close()
print("Демо-данные добавлены")
