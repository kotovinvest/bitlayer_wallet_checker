import requests
import pandas as pd
import time

# Bitlayer API URL для получения списка транзакций по адресу
BITLAYER_API_URL = "https://api.btrscan.com/scan/api"
BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

# Функция для получения курса BTC к USD с Binance
def get_btc_to_usd():
    try:
        response = requests.get(BINANCE_API_URL)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"Ошибка получения курса BTC к USD: {e}")
        return None

def get_balance(address):
    try:
        response = requests.get(BITLAYER_API_URL, params={
            'module': 'account',
            'action': 'balance',
            'address': address
        })
        balance_wei = int(response.json().get('result', 0))
        balance_btc = balance_wei / 1e18  # Переводим из Wei в BTC
        return round(balance_btc, 8)  # Округляем до 8 знаков после запятой для точности
    except Exception as e:
        print(f"Ошибка получения баланса для {address}: {e}")
        return None

def get_transaction_count(address):
    try:
        response = requests.get(BITLAYER_API_URL, params={
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'asc'
        })
        transactions = response.json().get('result', [])
        # Фильтруем только исходящие транзакции, где адрес отправителя равен нашему адресу
        outgoing_transactions = [tx for tx in transactions if tx['from'].lower() == address.lower()]
        return len(outgoing_transactions)
    except Exception as e:
        print(f"Ошибка получения количества транзакций для {address}: {e}")
        return None

def get_last_transaction_date(address):
    try:
        response = requests.get(BITLAYER_API_URL, params={
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'desc'
        })
        transactions = response.json().get('result', [])
        if transactions:
            # Ищем последнюю исходящую транзакцию
            outgoing_transactions = [tx for tx in transactions if tx['from'].lower() == address.lower()]
            if outgoing_transactions:
                last_tx = outgoing_transactions[0]
                last_tx_date = pd.to_datetime(int(last_tx['timeStamp']), unit='s')
                return last_tx_date.strftime('%d.%m.%Y')
        return None
    except Exception as e:
        print(f"Ошибка получения даты последней транзакции для {address}: {e}")
        return None

def get_first_transaction_date(address):
    try:
        response = requests.get(BITLAYER_API_URL, params={
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'asc'  # Сортируем по возрастанию, чтобы первая транзакция была первой в списке
        })
        transactions = response.json().get('result', [])
        if transactions:
            # Ищем первую исходящую транзакцию
            outgoing_transactions = [tx for tx in transactions if tx['from'].lower() == address.lower()]
            if outgoing_transactions:
                first_tx = outgoing_transactions[0]
                first_tx_date = pd.to_datetime(int(first_tx['timeStamp']), unit='s')
                return first_tx_date.strftime('%d.%m.%Y')
        return None
    except Exception as e:
        print(f"Ошибка получения даты первой транзакции для {address}: {e}")
        return None

# Получаем актуальный курс BTC к USD
btc_to_usd_rate = get_btc_to_usd()

# Читаем адреса кошельков из файла
with open('wallets.txt', 'r') as file:
    wallets = [line.strip() for line in file]

# Подготавливаем данные для записи в Excel
data = []
for idx, address in enumerate(wallets, 1):
    print(f"[{idx}/{len(wallets)}] Проверка кошелька: {address}")
    
    balance = get_balance(address)
    if balance is not None:
        usd_value = round(balance * btc_to_usd_rate, 2)  # Рассчитываем баланс в долларах
        # Форматируем баланс в BTC и USD с 5 знаками для BTC и 2 знаками для USD
        balance_formatted = f"{balance:.5f} BTC ({usd_value:.2f}$)"
    else:
        balance_formatted = None

    tx_count = get_transaction_count(address)
    first_tx_date = get_first_transaction_date(address)
    last_tx_date = get_last_transaction_date(address)
    
    print(f"  Баланс: {balance_formatted}, Кол-во транзакций: {tx_count}, Дата первой транзакции: {first_tx_date}, Дата последней транзакции: {last_tx_date}")
    
    data.append({
        'Address': address,
        'Balance': balance_formatted,
        'Transaction Count': tx_count,
        'First Transaction Date': first_tx_date,
        'Last Transaction Date': last_tx_date
    })
    
    time.sleep(0.5)  # Задержка 0.5 секунды

# Создаем DataFrame и записываем его в Excel
try:
    df = pd.DataFrame(data)
    df.to_excel('wallet_data.xlsx', index=False)
    print("Данные успешно записаны в wallet_data.xlsx")
except PermissionError as e:
    print(f"Ошибка записи в файл Excel: {e}")
