import requests
from setting import *
from sys import stdout

COMMON_HEADERS = {
    'Origin': 'https://kktix.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15',
    'Connection': 'keep-alive',
}


class User:
    def __init__(self):
        self.__session = requests.session()

    def get_csrf(self, url, headers=None):
        from lxml import etree

        while True:
            try:
                return etree.HTML(
                    self.__session.get(url, headers=headers, timeout=TIMEOUT).text
                ).xpath('//*[@name="csrf-token"]')[0].attrib['content']
            except requests.exceptions.Timeout:
                print('    [✗] Timeout\n        -> At get_csrf, continue...')

    def dump_cookies(self):
        from pickle import dump
        with open('cookies', 'wb') as f:
            dump(self.__session.cookies, f)

    def load_cookies(self):
        from pickle import load
        with open('cookies', 'rb') as f:
            self.__session.cookies.update(load(f))

    def check_online(self):
        while True:
            try:
                return self.__session.get(
                    'https://kktix.com/account/orders',
                    headers=COMMON_HEADERS,
                    timeout=TIMEOUT
                ).request.url == 'https://kktix.com/users/sign_in'
            except requests.exceptions.Timeout:
                print('    [✗] Timeout\n        -> At check_online, continue...')

    def sign_in(self, cookies_valid=True):
        from os.path import isfile

        print('[Signing in]')

        if cookies_valid and isfile('cookies'):
            self.load_cookies()

            if self.check_online():
                self.sign_in(cookies_valid=False)
            else:
                return True

        while True:
            try:
                self.__session.post(
                    'https://kktix.com/users/sign_in',
                    data={
                        'utf8': '✓',
                        'authenticity_token': self.get_csrf('https://kktix.com/users/sign_in'),
                        'user[login]': USERNAME,
                        'user[password]': PASSWORD,
                        'user[remember_me]': 0,
                        'commit': 'Sign+In'
                    },
                    headers=COMMON_HEADERS,
                    timeout=TIMEOUT
                )
                self.dump_cookies()

                return not self.check_online()
            except requests.exceptions.Timeout:
                print('    [✗] Timeout\n        -> At sign_in, continue...')

    @staticmethod
    def get_register_info():
        return requests.get(
            f'https://kktix.com/g/events/{EVENT_ID}/register_info'
        ).json()

    def get_token(self, url, payload):
        while True:
            try:
                return self.__session.post(
                    url,
                    data=payload.encode(),
                    headers={
                        'Host': 'queue.kktix.com',
                        'Origin': 'https://kktix.com',
                        'Referer': BOOKING_PAGE,
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15',
                        'Connection': 'keep-alive'
                    },
                    timeout=TIMEOUT
                )
            except requests.exceptions.Timeout:
                print('    [✗] Timeout\n        -> At get_ticket_token, continue...')

    def check_token(self, question, ktx_captcha):
        from urllib import parse

        url = f'https://queue.kktix.com/queue/{EVENT_ID}?authenticity_token={parse.quote(self.get_csrf(BOOKING_PAGE, COMMON_HEADERS))}'
        payload = PAYLOAD_WITH_CAPTCHA.format(ktx_captcha) if ktx_captcha else PAYLOAD

        token = self.get_token(url, payload).json()
        # print(f'\n        -> {token}')  # TODO Debug

        if 'token' in token: return token['token']

        while token.get('result') == 'CAPTCHA_WRONG_ANSWER':
            token = self.get_token(
                url,
                PAYLOAD_WITH_CAPTCHA.format(
                    input(f'    [✗] Wrong answer\n        -> {question}: ').strip()
                )
            ).json()

        return token['token'] if 'token' in token else None

    @staticmethod
    def get_order_id(token):
        url = f'https://queue.kktix.com/queue/token/{token}'
        result = None
        while result is None:
            try:
                result = requests.get(url, timeout=TIMEOUT).json()
            except requests.exceptions.Timeout:
                print('    [✗] Timeout\n        -> At get_ticket_token, continue...')

        if 'result' in result:
            return User.get_order_id(token)
        else:
            # print(f'        -> {result}')  # TODO Debug
            return result

    def order_ticket(self):
        register_info = User.get_register_info()

        tickets = register_info['inventory']['ticketInventory']
        if tickets == {}:
            print('    [✗] All sold out')
            return

        ktx_captcha = register_info.get('ktx_captcha')
        question = ktx_captcha['question'] if ktx_captcha else None
        ktx_captcha = input(f'    [?] Question\n    -> {question}: ').strip() if question else None

        while True:
            token = None
            i = 1
            while token is None:
                stdout.write(f'\r    [?] Ordering ticket in {i} time(s)')
                stdout.flush()
                token = self.check_token(question, ktx_captcha)
                i += 1

            order_id = None
            while order_id is None:
                order_id = User.get_order_id(token)

            if 'message' in order_id:
                stdout.write(f'\r    [✗] Someone took your ticket')
                stdout.flush()
            else:
                print()
                order_id = order_id.get('to_param')
                break

        fucking_url = f'https://kktix.com/events/{EVENT_ID}/registrations/{order_id}#/'
        print(f'    [✓] Hurry up, get the ticket(s)! 10mins remain\n        -> {fucking_url}\n[Done]')

        with open('tickets.txt', 'a') as f:
            f.write(f'{EVENT_ID} -> {fucking_url}\n-----DIVIDE-LINE-----\n')


if __name__ == '__main__':
    try:
        user = User()

        if user.sign_in():
            print('    [✓] Sign in succeed\n[Working]')
            user.order_ticket()
        else:
            print('    [✗] Sign in failed')
    except KeyboardInterrupt:
        print('\n[Goodbye]')
