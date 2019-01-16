from json import loads
from re import search
from time import sleep

USERNAME = ''
PASSWORD = ''
PAGE = 'https://s.taobao.com/search?q={}&sort=sale-desc&s={}'


def load_keywords():
    with open('keywords.txt', 'r') as f:
        keywords = f.read().splitlines()

    return [keyword.split('@') if '@' in keyword else [keyword, '2'] for keyword in keywords]


def get_track(distance):
    from random import randint

    track = []
    current = 0
    mid = distance * 4 / 5
    t = 0.2
    v = 0

    while current < distance:
        if current < mid:
            a = randint(10, 30)
        else:
            a = -4
        v0 = v
        v = v0 + a * t
        move = v0 * t + 1 / 2 * a * t * t
        current += move
        track.append(round(move))
    return track


def move_to_gap(browser, slider, tracks):
    from selenium.webdriver.common.action_chains import ActionChains

    ActionChains(browser).click_and_hold(slider).perform()
    for x in tracks:
        ActionChains(browser).move_by_offset(xoffset=x, yoffset=0).perform()
    sleep(0.5)
    ActionChains(browser).release().perform()


def fuck_taobao(browser):
    from selenium.common.exceptions import UnexpectedAlertPresentException

    sleep(3)
    browser.execute_script('Object.defineProperty(navigator,"webdriver",{get:()=>false,});')
    try:
        while True:
            dragger = browser.find_element_by_id('nc_1_n1z')
            move_to_gap(browser, dragger, get_track(500))
            sleep(1)
            break
    except UnexpectedAlertPresentException:
        pass


def get(browser, url):
    from selenium.common.exceptions import TimeoutException

    while True:
        try:
            browser.get(url)
            break
        except TimeoutException:
            pass


def sign_in():
    from selenium import webdriver

    browser = webdriver.Chrome()
    browser.set_page_load_timeout(10)
    browser.set_script_timeout(10)
    browser.get('https://login.taobao.com?f=top')
    browser.find_element_by_id('J_Quick2Static').click()
    browser.find_element_by_id('TPL_username_1').send_keys(USERNAME)
    browser.find_element_by_id('TPL_password_1').send_keys(PASSWORD)
    fuck_taobao(browser)
    browser.find_element_by_id('J_SubmitStatic').click()

    return browser


def parse_page(browser, keyword, page):
    get(browser, PAGE.format(keyword, page * 44))

    while True:
        g_page_config = search(r'g_page_config = (.+?);\n', browser.page_source)
        if g_page_config is None:
            fuck_taobao(browser)
        else:
            break

    return loads(g_page_config.group(1))


def parse_auction(auction, browser):
    from selenium.common.exceptions import NoSuchElementException, TimeoutException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.wait import WebDriverWait

    title = auction['raw_title']
    url = f'https:{auction["detail_url"]}'
    price = auction['view_price']
    sales = auction['view_sales'][:-3] if 'view_sales' in auction else ''
    location = auction['item_loc']
    nick = auction['nick']

    get(browser, url)
    print(url)

    if 'taobao' in url:
        try:
            price_item = browser.find_element_by_id('J_PromoPriceNum').text
        except NoSuchElementException:
            price_item = browser.find_element_by_xpath('//*[@id="J_StrPrice"]/em[2]').text

        while True:
            month_sales = browser.find_element_by_id('J_SellCounter').text
            if month_sales != '-':
                break
    elif 'tmall' in url:
        while True:
            try:
                month_sales = browser.find_element_by_xpath('//*[@id="J_DetailMeta"]/div[1]/div[1]/div/ul/li[1]/div/span[2]').text
                break
            except NoSuchElementException:
                browser.switch_to.frame('sufei-dialog-content')
                fuck_taobao(browser)
                browser.switch_to.default_content()

        while True:
            try:
                WebDriverWait(browser, 10, 0.1).until(EC.presence_of_all_elements_located((By.XPATH, '//span[@class="tm-price"]')))
                break
            except TimeoutException:
                pass

        price_item = browser.find_element_by_xpath('//span[@class="tm-price"]').text
    else:
        print(url)
        raise ValueError

    price_item = price_item.split('-')
    lowest_price = price_item[0]
    if len(price_item) == 1:
        highest_price = price_item[0]
    else:
        highest_price = price_item[1]

    print(keyword, url, title, price, sales, location, nick, lowest_price, highest_price, month_sales)
    return [keyword, url, title, price, sales, location, nick, lowest_price, highest_price, month_sales]


def new_storage():
    import csv
    from datetime import datetime
    from os import path

    file_name = datetime.now().strftime("%Y_%m_%d")
    is_new_file = not path.isfile(file_name)

    if is_new_file:
        with open(f'{file_name}.csv', 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['关键词', '链接', '标题', '价格', '付款数', '发货地', '店铺名', '最低价', '最高价', '30天销量'])

    return file_name


def save_to_csv(file_name, items):
    import csv

    with open(f'{file_name}.csv', 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        for item in items:
            writer.writerow(item)


if __name__ == '__main__':
    browser = sign_in()
    csv = new_storage()

    for keyword, page in load_keywords():
        items = []
        for page in range(int(page)):
            g_page_config = parse_page(browser, keyword, page)
            if 'data' not in g_page_config['mods']['itemlist']:
                break

            auctions = g_page_config['mods']['itemlist']['data']['auctions']
            for auction in auctions:
                items.append(parse_auction(auction, browser))

            if len(auctions) < 44:
                break

        save_to_csv(csv, items)
        items.clear()
