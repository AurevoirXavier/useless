import requests
import xlwt
from json import loads
from re import sub
from selenium import webdriver, common
from time import sleep

URL = 'https://item.taobao.com/item.htm?spm=a1z10.3-c.w4002-10254921587.32.47525b76PsaapZ&id=546002101737'
PAGE_NUM = 10


class User:
    def __init__(self):
        self.__session = requests.session()
        self.__session.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15',
            'Connection': 'keep-alive',
        }

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
                return 'login' in self.__session.get('https://i.taobao.com/my_taobao.htm').request.url
            except requests.exceptions.Timeout:
                ()

    def sign_in(self, cookies_valid=True):
        from os.path import isfile

        print('[-] [尝试登陆]')

        if cookies_valid and isfile('cookies'):
            self.load_cookies()

            if self.check_online():
                self.sign_in(cookies_valid=False)
            else:
                return True

        with webdriver.Chrome() as browser:
            browser.get('https://login.taobao.com/member/login.jhtml')

            input('    [-] [请完成登陆]')

            cookies = browser.get_cookies()
            for cookie in cookies:
                self.__session.cookies.set(cookie['name'], cookie['value'])

            self.dump_cookies()

        return not self.check_online()

    def get_comments(self):
        TMALL = 'tmall' in URL

        print('[-] [获取地址]')
        with webdriver.Chrome() as browser:
            browser.get(URL)
            sleep(1)

            try:
                browser.find_element_by_id('sufei-dialog-close').click()
            except common.exceptions.NoSuchElementException:
                ()

            sleep(10)
            browser.find_element_by_xpath('//*[@id="J_TabBar"]/li[2]/a').click()

            if TMALL:
                xpath = '/html/head/script[3]'
                current_page = 'currentPage'
            else:
                xpath = '/html/head/script[1]'
                current_page = 'currentPageNum'

            sleep(5)
            list_detail_rate = sub(
                r'callback=.+',
                'callback=j',
                browser.find_element_by_xpath(xpath).get_attribute('src').replace(f'{current_page}=1', f'{current_page}={{}}')
            )
            print('[*] [获取地址成功]')

        # print(list_detail_rate)  # TODO Debug

        self.__session.headers['Host'] = 'rate.taobao.com'
        summary = {}
        prev = None
        for page_num in range(1, PAGE_NUM + 1):
            print(f'    [-] [正在处理第 {page_num} 页]')
            text = self.__session.get(list_detail_rate.format(page_num)).text.strip()
            if prev == text:
                break
            else:
                prev = text

            # print(text)  # TODO Debug

            if TMALL:
                for rate in loads(text[2:-1])['rateDetail']['rateList']:
                    kind = rate['auctionSku']
                    if kind in summary:
                        summary[kind] += 1
                    else:
                        summary[kind] = 1
            else:
                for comment in loads(text[2:-1])['comments']:
                    kind = comment['auction']['sku']
                    print(kind)
                    if kind in summary:
                        summary[kind] += 1
                    else:
                        summary[kind] = 1

            sleep(5)

        print('[-] [正在写入 Excel 文件]')
        f = xlwt.Workbook()
        sheet = f.add_sheet('1')
        sheet.write(0, 0, '款式')
        sheet.write(0, 1, '销量')

        summary = sorted(summary.items(), key=lambda d: d[1], reverse=True)
        for row, d in enumerate(summary, start=1):
            sheet.write(row, 0, d[0])
            sheet.write(row, 1, d[1])

        f.save('款式销量分析.xls')
        print('[*] [写入成功]')


if __name__ == '__main__':
    user = User()
    # if user.sign_in():
    #     print('[*] [登陆成功]')
    user.get_comments()
    # else:
    #     print('[x] [登陆失败]')
