from os import path, makedirs
from time import sleep
from lxml import etree
from requests import session
from selenium import webdriver

GOODS_API = 'https://ware.shop.jd.com/onSaleWare/onSaleWare_newDoSearch.action?page={}'


def init():
    if not path.isdir('cookies'):
        makedirs('cookies')


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
    if path.isfile(f'cookies/{username}'):
        cookies = load_cookies(username)
    else:
        with webdriver.Chrome() as browser:
            browser.get('https://passport.jd.com/common/loginPage?from=pop_vender')
            sleep(1)
            browser.find_element_by_id('loginname').send_keys(username)
            browser.find_element_by_id('nloginpwd').send_keys(password)
            browser.find_element_by_id('paipaiLoginSubmit').click()
            sleep(3)

            cookies = browser.get_cookies()
            dump_cookies(cookies, username)

    return cookies


def fetch_goods(s):
    goods_list = []
    page = 1
    while True:
        print(f'第 {page} 页')
        resp = s.get(GOODS_API.format(page))
        html = etree.HTML(resp.text)
        for good in html.xpath('//*[@id="tbl_type2"]/tbody/tr'):
            goods_list.append(good.xpath('./td[8]/div/div/div[2]/ul/li/a')[0].attrib['href'])

        if html.xpath('//*[@class="next-disabled"]'):
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
    init()

    with open('accounts.txt', 'r') as f:
        accounts = f.read()

    for account in accounts.splitlines():
        account = account.split(' ')
        username = account[0]
        password = account[1]

        cookies = sign_in(username, password)
        s = build_session(cookies)
        goods_list = fetch_goods(s)

        modify_imgs(cookies, goods_list)
