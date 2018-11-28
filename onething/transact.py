# std
from datetime import datetime
from json import load, dumps
from os import listdir

# external
from requests import post
from web3.auto import w3

# custom
from setting import PASSWD, PROXIES, UTCS_PATH, WORKER

PREMIER_WALLET = next(filter(lambda f: f.startswith('0x'), listdir('.')))

UTCS = iter([])

NUM_OF_WALLETS = len(list(filter(lambda fn: fn.startswith('0x'), listdir(UTCS_PATH))))

WALLETS_AVAILABLE = True

UNAVAILABLE_WALLETS = set()


def get_utc() -> (str, str):
    global UTCS

    while True:
        try:
            utc = ''
            while not utc.startswith('0x'):
                utc = next(UTCS)
            return utc
        except StopIteration:
            UTCS = iter(listdir(UTCS_PATH))


def get_balance(address: str) -> int:
    return int(post(
        'https://walletapi.onethingpcs.com/getBalance',
        data=dumps({
            "jsonrpc": "2.0",
            "method": "eth_getTransactionCount",
            "params": [address, "latest"],
            "id": 1
        })
    ).json()['result'], 16)


def get_wallet(value: int) -> (str, str, int):
    global UNAVAILABLE_WALLETS

    from_ = get_utc()
    file = f'{UTCS_PATH}{from_}'
    balance = get_balance(from_)
    while balance < value:
        UNAVAILABLE_WALLETS.add(from_)
        print(f'[✗] [自动跳过] [<钱包: {from_}>, 剩余 <链克: {balance / 10**18}>, 需要 <链克: {value / 10**18}>] (来自支付线程的通知)')
        from_ = get_utc()
        while from_ in UNAVAILABLE_WALLETS:
            if len(UNAVAILABLE_WALLETS) == NUM_OF_WALLETS:
                raise ValueError
            from_ = get_utc()
        file = f'{UTCS_PATH}{from_}'
        balance = get_balance(from_)

    return from_, file


def all_not_enough_balance(account: str, kind: str):
    with open(f'余额不足无法购买.txt', 'a') as f:
        f.write(f'{account} {kind}\n')
    print('[✗] [所有钱包均处与余额警告状态退出支付] (来自支付线程的通知)')


def get_transaction_count(from_: str) -> str:
    return post(
        'https://walletapi.onethingpcs.com/getTransactionCount',
        data=dumps({
            'jsonrpc': '2.0',
            'method': 'eth_getTransactionCount',
            'params': [from_, 'latest'],
            'id': 1
        }),
        verify=False
    ).json()['result']


def contract_record(account: str, kind: str, utc: str, hash):
    with open(f'支付记录_{WORKER}.txt', 'a') as f:
        info = f'<钱包: {utc}>, 支付了 <账户: {account}>, 在 <时间: {str(datetime.now())[:-7]}>, 兑换的 <种类: {kind}>, 记录 <hash: {hash}>'
        f.write(f'{info}\n')
        print(f'[✓] [{info}] (来自支付线程的通知)')


def dispatch(value: int):
    private_key = w3.eth.account.decrypt(open(PREMIER_WALLET, 'r').read(), PASSWD)

    print('[✓] [开始分发]')
    with open(f'分发记录_{WORKER}.txt', 'a') as f:
        for to in listdir(UTCS_PATH):
            balance = get_balance(PREMIER_WALLET) / 10 ** 18
            if balance < value:
                print('[✗] [主钱包余额不足结束分发]')
                return

            if not to.startswith('0x'):
                continue

            signed_transaction = w3.eth.account.signTransaction({
                'from': w3.toChecksumAddress(PREMIER_WALLET),
                'to': w3.toChecksumAddress(to),
                'value': int(value * 10 ** 18),
                'gas': '0x186a0',
                'gasPrice': '0x174876e800',
                'nonce': get_transaction_count(PREMIER_WALLET)
            }, private_key).rawTransaction.hex()

            # print(signed_transaction)  # TODO Debug

            post_transaction(signed_transaction)

            info = f'[<钱包: {PREMIER_WALLET}>, 分发给 <钱包: {to}> <链克: {value}>, 后剩余 <链克: {get_balance(PREMIER_WALLET) / 10**18}>]'
            f.write(f'{info}\n')
            print(f'    -> {info}')
    print('[✓] [分发结束]')


def collect():
    with open(PREMIER_WALLET, 'r') as f:
        if PREMIER_WALLET[2:].lower() != load(f)['address']:
            print(PREMIER_WALLET)
            return

    print('[✓] [开始提取]')
    with open(f'提取记录_{WORKER}.txt', 'w') as f:
        for from_ in listdir(UTCS_PATH):
            if not from_.startswith('0x'):
                continue

            value =  get_balance(from_) - 0x186a0 * 0x174876e800
            if value < 0:
                print(f'    -> [<钱包: {from_}> 缴纳手续费后剩余 <链克: {value / 10**18}> 自动跳过]')
                continue

            signed_transaction = w3.eth.account.signTransaction({
                'from': w3.toChecksumAddress(from_),
                'to': w3.toChecksumAddress(PREMIER_WALLET),
                'value': value,
                'gas': '0x186a0',
                'gasPrice': '0x174876e800',
                'nonce': get_transaction_count(from_)
            }, w3.eth.account.decrypt(open(f'{UTCS_PATH}{from_}', 'r').read(), PASSWD)).rawTransaction.hex()

            # print(signed_transaction)  # TODO Debug

            post_transaction(signed_transaction)

            info = f'[<钱包: {PREMIER_WALLET}>, 从 <钱包: {from_}>, 收取 <链克: {value / 10**18}>, 余额 <链克: {get_balance(PREMIER_WALLET) / 10**18}>]'
            f.write(f'{info}\n')
            print(f'    -> {info}')
    print('[✓] [提取结束]')


def post_transaction(signed_transaction: int) -> str:
    resp = post(
        'https://walletapi.onethingpcs.com/sendRawTransaction',
        data=dumps({
            "jsonrpc": "2.0",
            "method": "eth_sendRawTransaction",
            "params": [signed_transaction],
            "id": 1
        }),
        headers={'content-type': 'application/json', "Nc": "IN"},
        proxies=PROXIES,
        verify=False
    ).json()

    print(resp)  # TODO Debug

    return resp['result']


def exec_contract(account: str, kind: str, to: str, data: str, value: str, gas_limit: int):
    global WALLETS_AVAILABLE
    if not WALLETS_AVAILABLE:
        all_not_enough_balance(account, kind)
        return

    value = int(value)
    try:
        from_, file = get_wallet(value)
    except ValueError:
        WALLETS_AVAILABLE = False
        all_not_enough_balance(account, kind)
        return

    signed_transaction = w3.eth.account.signTransaction({
        'from': w3.toChecksumAddress(from_),
        'to': w3.toChecksumAddress(to),
        'value': value,
        'gas': str(hex(gas_limit)),
        'gasPrice': '0x174876e800',
        'data': data,
        'nonce': get_transaction_count(from_)
    }, w3.eth.account.decrypt(open(file, 'r').read(), PASSWD)).rawTransaction.hex()

    # print(signed_transaction)  # TODO Debug

    contract_record(account, kind, from_, post_transaction(signed_transaction))
