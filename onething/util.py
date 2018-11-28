# std
import os
from pickle import load, dump
from re import match
# from requests import get
from random import randint

# external
from web3.auto import w3

# custom
from setting import PASSWD, UTCS_PATH, WORKER
from transact import get_balance

COMMON_HEADERS = {
    'Host': 'api-accw.onethingpcs.com',
    'Connection': 'keep-alive',
    'User-Agent': 'MineCrafter3/2.0.1 (iPhone; iOS 12.0.1; Scale/2.00)',
    'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9'
}


# PROXIES = iter([])


def gen_device_ip() -> str:
    return f'{randint(1, 126)}.{randint(1, 255)}.{randint(1, 255)}.{randint(1, 254)}'


def gen_unknown_id() -> str:
    return f'{randint(100000, 999999)}b24fdf96f3c1ea236b849dbf{randint(100000, 999999)}ccef24b9fda1'


def gen_uuid() -> str:
    return f'62B4A12E-A211-4EFD-A{randint(100, 999)}-D80A29E{randint(1000, 9999)}C'


def gen_mall_headers() -> dict:
    return {
        'Host': 'api-mall.onethingpcs.com',
        'Origin': 'https://account.onethingpcs.com',
        'Connection': 'keep-alive',
        'User-Agent': f'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16A404 MineCrafter3/2.0.1 (iPhone; iOS 12.0.1; Scale/2.00) (origin=2&nc=GB&did={gen_uuid()}&area=CN&ver=2.0.1&deviceip={gen_device_ip()}&device_type=OneCloud&is_guest=0)',
        'Referer': 'https://account.onethingpcs.com/building/dist/mall/',
        'Accept-Language': 'zh-cn'
    }


def check_history(filename: str) -> int:
    history = 0
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            history = load(f)
            print(f'    [✓] [检测到历史, 将从第 {history} 行开始]')
    return history


def record_history(filename: str, history: int):
    with open(filename, 'wb') as f:
        dump(history + 1, f)


def remove_history(filename: str):
    os.remove(filename)
    print('    [✓] [历史删除成功]')


def as_account(text: str) -> (str, str):
    matched = match(r'(.+)=(.+)', text)
    return matched.group(1), matched.group(2)


# def get_proxies() -> str:
#     proxy = get('http://api3.xiguadaili.com/ip/?tid=556781886173125&num=1&category=2&protocol=https&filter=on&longlife=1').text.strip()
#     print(f'    -> 代理: {proxy}')
#     return proxy
#     global PROXIES
#
#     while True:
#         try:
#             proxy = next(PROXIES)
#             print(f'    -> 代理: {proxy}')
#             return proxy
#         except StopIteration:
#             PROXIES = iter(
#                 get('http://api3.xiguadaili.com/ip/?tid=556781886173125&num=5&category=2&protocol=https&filter=on&longlife=1').text.splitlines())


def gen_wallet(num: float):
    if not os.path.exists(f'生成钱包_{WORKER}'):
        os.mkdir(f'生成钱包_{WORKER}')

    print('[?] [生成钱包中]')
    for i in range(int(num)):
        account = w3.eth.account.create()
        address = account.address
        with open(f'生成钱包_{WORKER}/{address}', 'w') as f:
            f.write(str(w3.eth.account.encrypt(account.privateKey, PASSWD)).replace('\'', '\"'))
        print(f'    -> 第 {i + 1} 个钱包生成: {address}')
    print('[✓] [生成完毕]')


def get_all_balacnce():
    print('[?] [余额查询中]')
    for utc in os.listdir(UTCS_PATH):
        if utc.startswith('0x'):
            print(f'    -> [<钱包: {utc}> 剩余 <链克: {get_balance(utc) / 10**18}>]')
    print('[✓] [查询完毕]')