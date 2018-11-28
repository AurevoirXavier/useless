# std
from threading import Thread
from time import time, sleep

# external
from requests import Session
from requests.exceptions import Timeout

# custom
from setting import DATE, ACCOUNTS, WORKER
from sign_in import sign_in
from transact import exec_contract
from util import as_account, check_history, gen_mall_headers, record_history, remove_history


def pull_order(session: Session, account, order: iter, transaction: bool) -> int:
    for lists in order:
        name = lists['goods_list'][0]['name']
        order_id = lists['order_id']

        if order_id[1:9] != DATE:
            return 2

        resp = None
        while resp is None:
            try:
                resp = session.post(
                    f'https://api-mall.onethingpcs.com/order/info?t={int(time()) * 1000}',
                    data={'order_id': order_id},
                    timeout=(1, 1),
                    verify=False
                ).json().get('data')
            except Timeout:
                continue

            # sleep(1.5)

        # print(resp)  # TODO Debug

        if transaction:
            if resp['lists'][0]['pay_status'] == 1:
                data = session.post(
                    f'https://api-mall.onethingpcs.com/pay/exchange?t={int(time()) * 1000}',
                    data={'order_id': resp['lists'][0]['order_id']},
                ).json()['data']
                print(f'    -> 检测到未支付订单: {name}')
                Thread(target=exec_contract, args=[account, name, data['to'], data['data'], data['value'], data['gas_limit']]).start()
                continue
            continue

        code = resp['lists'][0]['code']
        if not code:
            continue

        with open(f'{name}_{DATE}.txt', 'a') as f:
            f.write(f'{code}\n')
        print(f'        -> {name} {code}')
    return 1


def pull_order_page(session: Session, account: str, page: int, transaction: bool) -> int:
    while True:
        try:
            resp = session.post(
                f'https://api-mall.onethingpcs.com/order/list?t={int(time()) * 1000}',
                data={'page': page, 'status': 0},
                timeout=(1, 1),
                verify=False
            )
        except Timeout:
            continue

        # sleep(1.5)

        if resp.status_code != 200:
            continue
        else:
            resp = resp.json()
        # print(resp)  # TODO Debug

        if 'sMsg' not in resp:
            continue

        msg = resp['sMsg']
        if '黑名单' in msg:
            with open(f'封禁账号_{WORKER}.txt', 'a') as f:
                f.write(f'{account}\n')
            print('    [✗] [违反商城用户协议，已加入黑名单}]')
            return 0
        elif '登录' in msg:
            return pull_order_page(session, account, page, transaction)

        if 'data' not in resp:
            print(f'        -> {resp["sMsg"]}')
            continue

        order = resp['data']['lists']

        print(f'    [✓] [拉取第 {page} 页]')
        return pull_order(session, account, order, transaction) if order else 3


def calc_page(session: Session, account: str, transaction: bool):
    page = 0
    while True:
        page += 1

        # status code
        # 1 -> normal
        # 0 -> baned
        # 2 -> out of date
        # 3 -> no history
        status = pull_order_page(session, account, page, transaction)
        if status in [0, 2, 3]:
            # print(f'退出状态码: {status}')  # TODO Debug
            return


def export(transaction: bool = False):
    print('[✓] [执行导出]')

    history = check_history('h_e')
    with open(ACCOUNTS, 'r') as f:
        for row, line in enumerate(f):
            if row < history:
                if row + 1 == history:
                    print(f'        -> 跳过 {row} 行')
                continue

            account, passwd = as_account(line)

            print(f'[用户 {account}]')
            flag, session = sign_in(account, passwd)

            # print(flag, session)  # TODO Debug

            if flag:
                print('    [?] [拉取订单页面]')
                session.headers.update(gen_mall_headers())
                calc_page(session, account, transaction)

            record_history('h_e', row + 1)

    print('[✓] [导出线程结束]')
    remove_history('h_e')
