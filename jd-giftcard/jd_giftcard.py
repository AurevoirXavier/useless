# --- std ---
import json
import pickle
from os.path import isfile
from random import randint, random
from requests import session
from time import sleep, time
from uuid import uuid1
# --- custom ---
from rk import RClient

rc = RClient('339472578', 'dj123456', 'soft_id', 'soft_key')
result = rc.rk_create(open('captcha.png', 'rb').read(), 3040)
print(result)

sleep(1000)

s = session()
s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15'

if isfile('cookie'):
    s.cookies = pickle.loads(open('cookie', 'rb'))
else:
    if s.get('https://passport.jd.com/new/login.aspx').status_code == 200:
        resp = s.get(
            'https://qr.m.jd.com/show',
            params={
                'appid': 123,
                'size': 147,
                't': time() * 1000
            }
        )

        if resp.status_code == 200:
            with open('captcha.png', 'wb') as f:
                f.write(resp.content)

        s.headers['Host'] = 'qr.m.jd.com'
        s.headers['Referer'] = 'https://passport.jd.com/new/login.aspx'
        ticket = None

        for _ in range(15):
            resp = s.get(
                'https://qr.m.jd.com/check',
                params={
                    'callback': f'jQuery{randint(100000, 999999)}',
                    'appid': 123,
                    'token': s.cookies['wlfstk_smdl'],
                    '_': time() * 1000
                }
            )

            if resp.status_code != 200:
                print(resp.text)
                sleep(0.5)
                continue

            j = json.loads(resp.text[13:-1])

            if j['code'] == 200:
                ticket = j['ticket']
                print(j['code'], ticket)
                break
            else:
                print(j['code'], j['msg'])
                sleep(3)

        if ticket is not None:
            s.headers['Host'] = 'passport.jd.com'
            s.headers['Referer'] = 'https://passport.jd.com/uc/login?ltype=logout'
            resp = s.get(
                'https://passport.jd.com/uc/qrCodeTicketValidation',
                params={'t': ticket}
            )

            if resp.status_code == 200:
                j = resp.json()
                if resp.headers.get('P3P') is None:
                    if 'url' in j:
                        print('!!dangerous verify!!')
                    else:
                        print('unknown error, contact Xavier')
                        print(resp)

            for k, v in resp.cookies.items():
                s.cookies[k] = v

            pickle.dump(s.cookies, open('cookie', 'wb'))

        print('login succeed')

        s.headers['Host'] = 'mygiftcard.jd.com'
        s.headers['Referer'] = 'https://mygiftcard.jd.com/giftcard/myGiftCardInit.action'
        uuid = uuid1()

        resp = s.get(
            'https://mygiftcard.jd.com/giftcard/JDVerification.aspx',
            params={
                'uid': uuid,
                't': random()
            }
        )

        if resp.status_code == 200:
            with open('captcha.png', 'wb') as f:
                f.write(resp.content)

            captcha = input('captcha: ')
            resp = s.get(
                'https://mygiftcard.jd.com/giftcard/checkAuthCode.action',
                params={
                    'action': 'CheckAuthcode',
                    'str': captcha,
                    'r': random(),
                    'uuid': uuid
                }
            )

            if resp.status_code == 200:
                if resp.json()['code'] == 'success':
                    resp = s.post(
                        'https://mygiftcard.jd.com/giftcard/queryBindGiftCardNew.action',
                        data={
                            'actionType': 'bind',
                            'uuid': uuid,
                            'giftCardId': 'undefined',
                            'giftCardPwd': input('gift card: '),
                            'verifyCode': captcha,
                            'queryFlag': 0,
                            'random': random()
                        },
                        params={'t': random()},
                    )

                    if resp.status_code == 200:
                        resp = s.post(
                            'https://mygiftcard.jd.com/giftcard/queryBindGiftCardNew.action',
                            data={
                                'actionType': 'bind',
                                'doBindFlag': True,
                                'uuid': uuid,
                                'giftCardId': 'undefined',
                                'giftCardPwd': input('gift card: '),
                                'verifyCode': '',
                                'verifyCode2': resp.json()['data'][0]['pwdKey'],
                                'queryFlag': 0,
                                'random': random()
                            },
                            params={'t': random()},
                        )
