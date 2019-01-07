from time import sleep
from lxml import etree
from requests import session
from selenium import webdriver

GOODS_LIST = 'https://ware.shop.jd.com/onSaleWare/onSaleWare_newDoSearch.action?page={}'


def dump_cookies(cookies):
    from pickle import dump
    with open('cookies', 'wb') as f:
        dump(cookies, f)


def load_cookies():
    from pickle import load
    with open('cookies', 'rb') as f:
        return load(f)


with webdriver.Chrome() as browser:
    with open('accounts.txt', 'r') as f:
        accounts = f.read()

    for account in accounts.splitlines():
        account = account.split(' ')

        username = account[0]
        password = account[1]
        page = 1

        browser.get('https://passport.jd.com/common/loginPage?from=pop_vender')
        sleep(1)
        browser.find_element_by_id('loginname').send_keys(username)
        browser.find_element_by_id('nloginpwd').send_keys(password)
        browser.find_element_by_id('paipaiLoginSubmit').click()
        sleep(3)

        cookies = browser.get_cookies()

        s = session()
        for cookie in cookies:
            s.cookies.set(cookie['name'], cookie['value'])

        resp = s.get(GOODS_LIST.format(page))
        html = etree.HTML(resp.text)
        for good in html.xpath('//*[@id="tbl_type2"]/tbody/tr'):
            print(good.xpath('./td[8]/div/div/div[2]/ul/li/a')[0].attrib['href'])
