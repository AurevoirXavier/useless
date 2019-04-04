# --- std ---
import json
import pickle
from os.path import isfile
from random import randint, random
from requests import session
from sys import argv
from time import sleep, time
from uuid import uuid1
# --- custom ---
from rk import RClient
from secret import *


class JdAccount:
    rc = RClient(rk_id, rk_pwd, soft_id, soft_key)

    def __init__(self):
        self.session = session()
        self.session.headers.clear()

    def _get_qr_code(self):
        while True:
            resp = self.session.get(
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

                return

    def _check_qr_code_status(self):
        for _ in range(15):
            while True:
                resp = self.session.get(
                    'https://qr.m.jd.com/check',
                    params={
                        'callback': f'jQuery{randint(100000, 999999)}',
                        'appid': 123,
                        'token': self.session.cookies['wlfstk_smdl'],
                        '_': time() * 1000
                    }
                )

                if resp.status_code == 200:
                    break

            j = json.loads(resp.text[13:-1])

            if j['code'] == 200:
                print(j['code'], j['ticket'])

                return j['ticket']
            else:
                print(j['code'], j['msg'])
                sleep(3)

        raise EnvironmentError

    def _valid_qr_code(self, ticket):
        self.session.headers['Host'] = 'passport.jd.com'
        self.session.headers['Referer'] = 'https://passport.jd.com/uc/login?ltype=logout'

        while True:
            status_code = self.session.get('https://passport.jd.com/uc/qrCodeTicketValidation', params={'t': ticket}).status_code

            if status_code == 200:
                break

        return self.session.get('https://passport.jd.com/uc/qrCodeTicketValidation', params={'t': ticket})

    def _qr_code_sign_in(self):
        while True:
            if self.session.get('https://passport.jd.com/new/login.aspx').status_code == 200:
                break

        self._get_qr_code()

        self.session.headers['Host'] = 'qr.m.jd.com'
        self.session.headers['Referer'] = 'https://passport.jd.com/new/login.aspx'

        ticket = self._check_qr_code_status()

        if ticket is not None:
            resp = self._valid_qr_code(ticket)

            if resp.headers.get('P3P') is None:
                if 'url' in resp.json():
                    print('!!dangerous verify!!')
                else:
                    print('unknown error, contact Xavier')
                    print(resp)
                    raise EnvironmentError

            for k, v in resp.cookies.items():
                self.session.cookies[k] = v

            pickle.dump(self.session.cookies, open('cookie', 'wb'))

    def sign_in(self):
        if isfile('cookie'):
            self.session.cookies = pickle.loads(open('cookie', 'rb').read())
        else:
            self._qr_code_sign_in()

        print('sign in succeed')

        self.session.headers['Host'] = 'mygiftcard.jd.com'
        self.session.headers['Referer'] = 'https://mygiftcard.jd.com/giftcard/myGiftCardInit.action'

    def _get_captcha(self):
        while True:
            uuid = uuid1()
            resp = self.session.get(
                'https://mygiftcard.jd.com/giftcard/JDVerification.aspx',
                params={
                    'uid': uuid,
                    't': random()
                }
            )

            if resp.status_code == 200:
                with open('captcha.png', 'wb') as f:
                    f.write(resp.content)

                return uuid

    def _auth_captcha(self):
        uuid = self._get_captcha()
        rk_resp = self.rc.rk_create(open('captcha.png', 'rb').read(), 3040)

        while True:
            resp = self.session.get(
                'https://mygiftcard.jd.com/giftcard/checkAuthCode.action',
                params={
                    'action': 'CheckAuthcode',
                    'str': rk_resp['Result'],
                    'r': random(),
                    'uuid': uuid
                }
            )

            if resp.status_code == 200:
                print(resp.text)

                if resp.json()['code'] == 'success':
                    return uuid, rk_resp['Result']

                self.rc.rk_report_error(rk_resp['Id'])
                return self._auth_captcha()

    def bind(self, gift_card_pwd, do_bind=False):
        uuid, captcha = self._auth_captcha()
        data = {
            'actionType': 'bind',
            'uuid': uuid,
            'giftCardId': 'undefined',
            'giftCardPwd': gift_card_pwd,
            'verifyCode': captcha,
            'queryFlag': 0,
            'random': random()
        }

        while True:
            resp = self.session.post(
                'https://mygiftcard.jd.com/giftcard/queryBindGiftCardNew.action',
                data=data,
                params={'t': random()},
            )

            if resp.status_code == 200:
                print(resp.text)

                j = resp.json()

                if j['code'] == 'nobind' and do_bind:
                    data.update({
                        'doBindFlag': True,
                        'verifyCode': '',
                        'verifyCode2': j['data'][0]['pwdKey'],
                    })

                    while True:
                        resp = self.session.post(
                            'https://mygiftcard.jd.com/giftcard/queryBindGiftCardNew.action',
                            data=data,
                            params={'t': random()},
                        )

                        if resp.status_code == 200:
                            print(resp.text)

                            j = resp.json()

                            if j['code'] == 'frequently':
                                for i in range(60, -1, -1):
                                    print('\r{:>2}'.format(i), end='')
                                    sleep(1)

                                print()
                            else:
                                return j
                elif j['code'] in ['bindedself', 'bindedother']:
                    return j
                else:
                    if j['code'] == 'frequently':
                        for i in range(60, -1, -1):
                            print('\r{:>2}'.format(i), end='')
                            sleep(1)

                        print()

                    uuid, captcha = self._auth_captcha()
                    data.update({
                        'uuid': uuid,
                        'verifyCode': captcha
                    })


if __name__ == '__main__':
    jd_account = JdAccount()
    jd_account.sign_in()

    if argv[1] == 'query':
        for gift_card_pwd in open('keys.txt', 'r'):
            gift_card_pwd = gift_card_pwd.strip()
            j = jd_account.bind(gift_card_pwd)
            s = f'key: {gift_card_pwd}, 总值: {j["data"][0]["amountTotal"]}, 余额: {j["data"][0]["amount"]}, 有效期至: {j["data"][0]["timeEnd"]}\n'

            if j['code'] == 'nobind':
                with open('unbinded.txt', 'a') as f:
                    f.write(s)
            else:
                with open('binded.txt', 'a') as f:
                    f.write(s)
    elif argv[1] == 'bind':
        for gift_card_pwd in open('keys.txt', 'r'):
            jd_account.bind(gift_card_pwd.strip(), do_bind=True)
