# std
from json import dumps
from time import time, sleep
from threading import Thread

# external
from requests import Session
from requests.exceptions import Timeout

# custom
from export import export
from setting import AVAILABLE, ACCOUNTS, EXPORT, PAY, PLAN, WORKER
from sign_in import sign_in
from transact import exec_contract
from util import gen_mall_headers, as_account, check_history, record_history, remove_history


def build_payload(kind: str) -> dict:
    payload = {
        'orders': [{
            'uid': '11111111-1111-1111-1111-111111111111',
            'businessid': 3,
            'num': 1
        }]
    }

    if kind == '年':
        payload['orders'][0].update({
            'exchange_price': 55,
            'goods_litimg': 'https://images1-mall.lianxiangcloud.com/static/upload/20180915182023_5b9cdce798f58.png',
            'goodsid': 101,
            'name': '爱奇艺黄金会员12个月',
            'price': 55,
        })
    elif kind == '半年':
        payload['orders'][0].update({
            'exchange_price': 30,
            'goods_litimg': 'https://images1-mall.lianxiangcloud.com/static/upload/20180915181801_5b9cdc59b414d.png',
            'goodsid': 100,
            'name': '爱奇艺黄金会员6个月',
            'price': 30,
        })
    elif kind == '钻年':
        payload['orders'][0].update({
            'exchange_price': 140,
            'goods_litimg': 'https://images1-mall.lianxiangcloud.com/static/upload/20180915182445_5b9cddedf3421.jpg',
            'goodsid': 103,
            'name': '爱奇艺VIP钻石会员年卡',
            'price': 140,
        })
    elif kind == '季':
        payload['orders'][0].update({
            'exchange_price': 15,
            'goods_litimg': 'http://red.xunlei.com/images/linktokenmall/mall/goods/iqiyi/goods_litmig/iqiyi_vip3.png',
            'goodsid': 13,
            'name': '爱奇艺会员季卡',
            'price': 15,
        })
    elif kind == '月':
        payload['orders'][0].update({
            'exchange_price': 6,
            'goods_litimg': 'https://images1-mall.lianxiangcloud.com/static/upload/20180831200326_5b892e8ec72e5.png',
            'goodsid': 12,
            'name': '爱奇艺会员月卡',
            'price': 6,
        })
    elif kind == '周':
        payload['orders'][0].update({
            'exchange_price': 2,
            'goods_litimg': 'https://images1-mall.lianxiangcloud.com/static/upload/20180915173350_5b9cd1fe77621.png',
            'goodsid': 99,
            'name': '爱奇艺黄金会员周卡',
            'price': 2,
        })
    elif kind == '钻':
        payload['orders'][0].update({
            'exchange_price': 15,
            'goods_litimg': 'https://images1-mall.lianxiangcloud.com/static/upload/20180814142827_5b72768b77d49.png',
            'goodsid': 49,
            'name': '爱奇艺钻石VIP会员',
            'price': 15,
        })

    return payload


def post_redeem(session: Session, account, kind: str) -> object:
    mall_headers = gen_mall_headers()
    while True:
        sleep(1)

        try:
            resp = session.post(
                f'https://api-mall.onethingpcs.com/order/submitorder?t={int(time() * 1000)}',
                data=dumps(build_payload(kind)),
                headers=mall_headers,
                timeout=(1, 1),
                verify=False
            )
        except Timeout:
            continue

        # print(resp.json())  # TODO Debug

        if resp.status_code == 200:
            resp = resp.json()
            break

    # print(resp)  # TODO Debug

    msg = resp['sMsg'].strip()

    print(f'        -> {kind}: {msg}')

    if '售空' in msg:
        if PLAN == 2:
            print('    [✗] [已售空跳过当前卡种]')
        AVAILABLE[kind] = False
        return 0
    elif msg == '成功':
        data = resp['data']
        if PAY == 1:
            Thread(target=exec_contract, args=[account, kind, data['to'], data['data'], data['value'], data['gas_limit']]).start()

        return f' {kind} '
    elif '频繁' in msg or '重试' in msg:
        return post_redeem(session, account, kind)
    elif '限兑' in msg:
        return 0
    elif msg == '违反商城用户协议，已加入黑名单':
        return -1
    else:
        with open('意外情况.txt', 'a') as f:
            f.write(f'{str(resp)}\n')
        return 0


def redeem_card(session: Session, account: str, kind: str, info: str) -> (int, str):
    result = post_redeem(session, account, kind)

    # print(result)  # TODO Debug

    if result == -1:
        print('    [✗] [违反商城用户协议，已加入黑名单]')
        with open(f'封禁账号_{WORKER}.txt', 'a') as f:
            f.write(f'{account}\n')
    elif result:
        info = f'{info} {result}'

    return result, info


def choose_plan(session: Session, account: str, kind: str):
    print('    [?] [兑换中]')

    info = ''
    if PLAN == 1:
        for kind, on_sale in AVAILABLE.items():
            if not on_sale:
                print(f'        -> {kind}: 已售空自动跳过')
                continue

            result, info = redeem_card(session, account, kind, info)
            if not result:
                return
    elif PLAN == 2:
        result, info = redeem_card(session, account, kind, info)

        # print(result)  # TODO Debug

        if not result:
            return
    else:
        return

    info = info.strip()
    if info != '':
        with open(f'兑换记录_{WORKER}.txt', 'a') as f:
            f.write(f'[用户 {account}] {info}\n')


def redeem():
    history = check_history('h_r')
    if PLAN == 1:
        kinds = [None]
    elif PLAN == 2:
        kinds = AVAILABLE.keys()
    else:
        return

    for kind in kinds:
        print('[✓] [执行兑换]')

        with open(ACCOUNTS, 'r') as f:
            for row, line in enumerate(f):
                if PLAN == 2 and not AVAILABLE[kind]:
                    continue

                if row < history:
                    if row + 1 == history:
                        print(f'        -> 跳过 {row} 行')
                    continue

                account, passwd = as_account(line)

                print(f'[用户 {account}]')
                flag, session = sign_in(account, passwd)

                # print(flag, session)  # TODO Debug

                if flag:
                    choose_plan(session, account, kind)

                record_history('h_r', row + 1)

                if not any(AVAILABLE.keys()):
                    print('    [✗] [全部售空]')
                    break

            print('[✓] [兑换线程结束]')
            remove_history('h_r')

    if PAY == 1 and EXPORT:
        print('[?] [导出前等待以确保支付写入区块]')
        for i in range(29, 0, -1):
            print(f'\r    -> 剩余 {i} 秒', end='')
            sleep(1)
        print()
        export()
