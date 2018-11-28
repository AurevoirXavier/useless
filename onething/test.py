# std
from json import dumps
from threading import Thread
from time import time

# external
from requests import Session

# custom
from setting import ACCOUNTS
from sign_in import sign_in
from transact import exec_contract
from util import *


def redeem(session: Session, account: str):
    mall_headers = gen_mall_headers()

    print('    [?] [兑换中]')

    session.post(f'https://api-mall.onethingpcs.com/bind/checkuser?t={int(time() * 1000)}', headers=mall_headers, verify=False)
    session.post(f'https://api-mall.onethingpcs.com/home/checknet?t={int(time() * 1000)}', headers=mall_headers, verify=False)

    # TODO Test Case
    payload = {
        "orders": [{
            "business_logo": "https://images1-mall.lianxiangcloud.com/merchant/20180906/227635b90d26304fe3929004.jpg",
            "business_name": "隅田川咖啡",
            "businessid": 74,
            "category": "生活服务",
            "content": "<p><strong>兑换步骤：</strong></p><p>1、微信搜索隅田川咖啡官方公众号【隅田川咖啡】；</p><p>&nbsp;</p><p>2、进入公众号后点击下方菜单【咖啡购】，选择喜欢的咖啡（优惠码全场通用），下单提交订单之前点击【优惠】；</p><p>&nbsp;</p><p>3、在下一个页面输入优惠码，点击【兑换】即可。</p><p><br/></p><p>4、兑换过程中遇到任何问题请微信联系：ytc-coffee</p><p><br/></p><p><strong>活动规则</strong></p><p>1、优惠码领取成功后有效期1年，新老用户都可使用。</p><p><br/></p><p>2、仅限于在有赞微商城使用。</p><p><br/></p><p>3、本优惠码不可兑换现金、不找零、不可叠加使用。</p><p><br/></p><p>4、客服电话18267158270</p><p><br/></p>",
            "exchange_num": 185,
            "exchange_price": 0.1,
            "goods_litimg": "https://images1-mall.lianxiangcloud.com/static/upload/20180915155911_5b9cbbcf4310f.jpg",
            "goods_pic": ["https://images1-mall.lianxiangcloud.com/static/upload/20180915155923_5b9cbbdb03c82.jpg",
                          "https://images1-mall.lianxiangcloud.com/static/upload/20180915155927_5b9cbbdf4d7f0.jpg"],
            "goodsid": 98,
            "is_soldout": 1,
            "name": "隅田川咖啡福利券",
            "price": 0.1,
            "num": 1
        }]
    }

    timestamp = int(time() * 1000)
    session.options(f'https://api-mall.onethingpcs.com/order/submitorder?t={timestamp}', headers=mall_headers)
    resp = session.post(
        f'https://api-mall.onethingpcs.com/order/submitorder?t={timestamp}',
        data=dumps(payload),
        headers=MALL_HEADERS,
        verify=False
    ).json()

    print(resp)  # TODO Debug

    data = resp['data']

    Thread(target=exec_contract, args=[account, '隅田川咖啡福利券', data['to'], data['data'], data['value'], data['gas_limit']]).start()


if __name__ == '__main__':
    print('[执行兑换]')
    with open(ACCOUNTS, 'r') as f:
        for line in f:
            account, passwd = as_account(line)
            flag, session = sign_in(account, passwd)
            if flag:
                redeem(session, account)
    print('[退出兑换线程]')
