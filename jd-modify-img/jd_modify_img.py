# --- std ---
from os import makedirs, path
from shutil import rmtree
from time import sleep
# --- external ---
from lxml import etree
from requests import session
from selenium import webdriver

GOODS_API = 'https://ware.shop.jd.com/onSaleWare/onSaleWare_newDoSearch.action?page={}'


def dump_cookies(cookies, username):
    from pickle import dump
    with open(f'cookies/{username}', 'wb') as f:
        dump(cookies, f)


def load_cookies(username):
    from pickle import load
    with open(f'cookies/{username}', 'rb') as f:
        return load(f)


def build_session(cookies):
    s = session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])

    return s


def sign_in(username, password):
    with webdriver.Chrome() as browser:
        browser.get('https://passport.jd.com/common/loginPage?from=pop_vender')
        sleep(1)
        browser.find_element_by_id('loginname').send_keys(username)
        browser.find_element_by_id('nloginpwd').send_keys(password)
        browser.find_element_by_id('paipaiLoginSubmit').click()
        sleep(10)

        browser.get(GOODS_API.format(1))
        sleep(10)
        cookies = browser.get_cookies()

    dump_cookies(cookies, username)


def fetch_goods(s):
    goods_list = []
    page = 1
    while True:
        resp = s.get(GOODS_API.format(page))
        html = etree.HTML(resp.text)
        for good in html.xpath('//*[@id="tbl_type2"]/tbody/tr'):
            goods_list.append(good.xpath('./td[8]/div/div/div[2]/ul/li/a')[0].attrib['href'])

        if not goods_list or html.xpath('//*[@class="next-disabled"]'):
            break

        page += 1

    return goods_list


def modify_imgs(cookies, goods_list):
    with webdriver.Chrome() as browser:
        browser.get('https://passport.jd.com/common/loginPage?from=pop_vender')
        for cookie in cookies:
            browser.add_cookie(cookie)

        for good in goods_list:
            browser.get(f'https:{good}')
            sleep(1)
            browser.execute_script('''
                for (var imgs in globalAttr.ware.imageMap) { 
                    var tmp = globalAttr.ware.imageMap[imgs][4].imgUrl;
                    globalAttr.ware.imageMap[imgs][4].imgUrl = globalAttr.ware.imageMap[imgs][0].imgUrl;
                    globalAttr.ware.imageMap[imgs][0].imgUrl = tmp;
                }
            ''')
            sleep(1)
            browser.find_element_by_xpath('/html/body/div[2]/div[4]/div[4]/button[1]').click()
            sleep(3)


if __name__ == '__main__':
    if path.isdir('cookies'):
        rmtree('cookies')
    makedirs('cookies')

    with open('accounts.txt', 'r') as f:
        text = f.read()

    accounts = []
    for account in text.splitlines():
        account = account.split(' ')
        username = account[0]
        password = account[1]

        sign_in(username, password)
        accounts.append((username, password))

    for username, password in accounts:
        cookies = load_cookies(username)
        s = build_session(cookies)
        goods_list = fetch_goods(s)

        modify_imgs(cookies, goods_list)

    rmtree('cookies')
