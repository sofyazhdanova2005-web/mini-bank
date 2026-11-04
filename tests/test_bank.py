import pytest

from minibank.bank import Bank, BankError, kop_to_rub, rub_to_kop


@pytest.fixture
def bank():
    b = Bank(":memory:")  # база в памяти, файл на диске не создаётся
    yield b
    b.close()


def make_two_accounts(bank):
    anna = bank.add_client("Иванова Анна", "2510 123456")
    petr = bank.add_client("Петров Пётр", "2510 654321")
    return bank.open_account(anna), bank.open_account(petr)


def test_transfer_moves_money(bank):
    a, b = make_two_accounts(bank)
    bank.deposit(a, 100_000)          # 1000 ₽
    bank.transfer(a, b, 30_000)       # 300 ₽

    assert bank.balance(a) == 70_000
    assert bank.balance(b) == 30_000
    assert bank.history()[0]["kind"] == "TRANSFER"


def test_cannot_transfer_more_than_balance(bank):
    a, b = make_two_accounts(bank)
    bank.deposit(a, 5_000)

    with pytest.raises(BankError):
        bank.transfer(a, b, 10_000)

    # деньги никуда не ушли
    assert bank.balance(a) == 5_000
    assert bank.balance(b) == 0


def test_rubles_conversion():
    assert rub_to_kop("1 250,50") == 125_050
    assert kop_to_rub(125_050) == "1 250,50"
    with pytest.raises(BankError):
        rub_to_kop("-5")
