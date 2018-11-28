#  std
import re
from base64 import b64encode
from json import loads
from os.path import isfile
# from tempfile import TemporaryFile
from time import sleep, time
from urllib import parse

#  external
from lxml import etree
# from PIL import Image
import requests
from selenium import webdriver

#  custom
from setting import *


class Tixcraft:
    def __init__(self):
        self.__session = requests.session()

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
                    'https://tixcraft.com/user',
                    timeout=TIMEOUT
                ).request.url == 'https://tixcraft.com/login'
            except requests.exceptions.Timeout:
                print('    [✗] Timeout\n        -> At check_online, continue...')

    def sign_in(self, cookies_valid=True):
        print('[Trying to sign in]')

        if cookies_valid and isfile('cookies'):
            self.load_cookies()

            if self.check_online():
                self.sign_in(cookies_valid=False)
            else:
                return True

        with webdriver.Chrome() as browser:
            browser.get('https://tixcraft.com/#login')
            browser.find_element_by_xpath('/html/body/div[1]/div[1]/div[2]/div[1]/div/div[2]/div/ul/li[3]/a').click()

            sleep(1)

            browser.find_element_by_id('loginFacebook').click()
            browser.find_element_by_id('email').send_keys(USERNAME)
            browser.find_element_by_id('pass').send_keys(PASSWORD)
            browser.find_element_by_id('loginbutton').click()

            cookies = browser.get_cookies()
            for cookie in cookies:
                self.__session.cookies.set(cookie['name'], cookie['value'])

            self.dump_cookies()

        return not self.check_online()

    @staticmethod
    def get_event_id():
        # TODO Try to get event id
        i = 0
        event_id = None
        while event_id is None:
            i += 1

            while True:
                try:
                    text = requests.get(f'https://tixcraft.com/activity/game/{ARTIST}', timeout=TIMEOUT).text
                    break
                except requests.exceptions.Timeout:
                    print('    [✗] Timeout\n        -> At get_event_id, continue...')

            event_id = etree.HTML(text).xpath(f'//*[@id="gameList"]/table/tbody/tr[{TYPE}]/td[4]/input')
            if event_id:
                event_id = event_id[0].attrib['data-href']
            else:
                print(f'\r    -> Searching {i} time(s)', end='')
                event_id = None
        return re.match(r'.+/(.+)', event_id).group(1)

    def verify_code(self, event_id, csrf_token, check_code=None):
        while True:
            try:
                resp = self.__session.post(
                    f'https://tixcraft.com/ticket/checkCode/{ARTIST}/{event_id}',
                    data={
                        'CSRFTOKEN': csrf_token,
                        'checkCode': check_code if check_code else input('        -> retry: '),
                        'confirmed': True
                    },
                    timeout=TIMEOUT
                ).json()
                break
            except requests.exceptions.Timeout:
                print('    [✗] Timeout\n        -> At verify_code, continue...')

        # print(resp)  # TODO Debug

        if resp['url'] is None:
            self.verify_code(event_id, csrf_token)

    def get_area(self, event_id):
        while True:
            try:
                resp = self.__session.get(f'https://tixcraft.com/ticket/area/{ARTIST}/{event_id}', timeout=TIMEOUT)
                break
            except requests.exceptions.Timeout:
                print('    [✗] Timeout\n        -> At get_area, continue...')

        if 'verify' in resp.request.url:
            form = etree.HTML(resp.text).xpath('//form')[0]
            question = ''.join([text.strip() for text in form.itertext()])
            csrf_token = form.xpath('./input')[0].attrib['value']
            check_code = CARD_NO if '信用卡' in question else input(f'        -> {question}: ')

            self.verify_code(event_id, csrf_token, check_code)

            while True:
                try:
                    text = self.__session.get(f'https://tixcraft.com/ticket/area/{ARTIST}/{event_id}', timeout=TIMEOUT).text
                    break
                except requests.exceptions.Timeout:
                    print('    [✗] Timeout\n        -> At get_area, continue...')
            return text
        return resp.text

    @staticmethod
    def get_seat(text):
        html = etree.HTML(text)
        matched = re.search(
            r'var areaUrlList = (.+);',
            html.xpath('/html/body/script[9]')[0].text
        ).group(1)

        if matched == '[]':
            return None

        available_seats_address = loads(matched)
        for id, name in zip(
                html.xpath('//ul[@class="area-list"]/li/a/@id'),
                html.xpath('//ul[@class="area-list"]/li/a/text()')
        ):
            if SEAT in name:
                return available_seats_address[id]
        return next(iter(available_seats_address.values()))

    def build_payload(self, url):
        while True:
            try:
                html = etree.HTML(self.__session.get(url, timeout=TIMEOUT).text)
                break
            except requests.exceptions.Timeout:
                print('    [✗] Timeout\n        -> At build_payload, continue...')

        csrf_token = html.xpath('//*[@id="CSRFTOKEN"]')[0].attrib['value']
        ticket_form_ticket_price = html.xpath('//*[@id="ticketPriceList"]/tbody/tr/td[2]/select')[0].attrib['name']
        captcha = html.xpath('//*[@id="TicketForm"]/div[2]/div[1]/img')[0].attrib['src']
        ticket_form_agree = re.search(
            r'\$\(this\).attr\("name", "(TicketForm\[agree\]\[.+\])"\);',
            html.xpath("/html/head/script[6]")[0].text
        ).group(1)

        return csrf_token, ticket_form_ticket_price, self.get_captcha(captcha), ticket_form_agree, captcha

    @staticmethod
    def auto_captcha():
        while True:
            try:
                resp = requests.post(
                    'http://api.ruokuai.com/create.json',
                    data={
                        'username': 'flora213001',
                        'password': 'super0430',
                        'typeid': '2040',
                        'timeout': '60',
                        'softid': '116611',
                        'softkey': '55edccd90b7b4c1eb88fba9e3fcfef1d',
                    },
                    files={'image': ('captcha.png', open('captcha.png', 'rb'))},
                    headers={
                        'Accept': '*/*',
                        'Accept-Language': 'zh-cn',
                        'Host': 'api.ruokuai.com'
                    },
                ).json()
                return resp['Result']
            except requests.RequestException:
                print('    [✗] Timeout\n        -> At auto_captcha, continue...')

    def get_captcha(self, url):
        print('    [?] [waiting for captcha]')

        # with TemporaryFile() as f:
        with open('captcha.png', 'wb') as f:
            while True:
                try:
                    content = self.__session.get(f'https://tixcraft.com{url}', timeout=TIMEOUT).content
                    break
                except requests.exceptions.Timeout:
                    print('    [✗] Timeout\n        -> At get_captcha, continue...')

            f.write(content)
        # Image.open(f).show()

        # captcha = Tixcraft.auto_captcha()
        # print(f'        -> Auto captcha: {captcha}')
        captcha = input('        -> Captcha: ')
        return captcha

    def check_order(self):
        while True:
            try:
                resp = self.__session.get('https://tixcraft.com/ticket/check', timeout=TIMEOUT).json()
                break
            except requests.exceptions.Timeout:
                print('    [✗] Timeout\n        -> At check_order, continue...')

        # print(resp)  # TODO Debug

        print('    [✓] [check succeed]') if resp['waiting'] else print('    [✗] [check failed]')

    def order_ticket(self):
        seat = Tixcraft.get_seat(self.get_area(Tixcraft.get_event_id()))

        # print(seat)  # TODO Debug

        if seat is None:
            print('    [✗] [sold out]')
            return

        url = f'https://tixcraft.com{seat}'
        csrf_token, ticket_form_ticket_price, captcha, ticket_form_agree, img = self.build_payload(url)

        while True:
            while True:
                try:
                    self.__session.post(
                        url,
                        data={
                            'CSRFTOKEN': csrf_token,
                            ticket_form_ticket_price: QUANTITY,  # TODO suggest setting to 4
                            'TicketForm[verifyCode]': captcha,
                            ticket_form_agree: '1',
                            'ticketPriceSubmit': None
                        },
                        timeout=TIMEOUT
                    )
                    break
                except requests.exceptions.Timeout:
                    print('    [✗] Timeout\n        -> At order_ticket, continue...')

            self.check_order()
            self.order_ticket()


if __name__ == '__main__':
    try:
        user = Tixcraft()

        if user.sign_in():
            print('    [✓] Sign in succeed\n[Working]')
            user.order_ticket()
        else:
            print('    [✗] Sign in failed')
    except KeyboardInterrupt:
        print('\n[Goodbye]')
