from json import loads
from re import search
from time import sleep

USERNAME = ''
PASSWORD = ''
PAGE = 'https://s.taobao.com/search?q={}&js=1&stats_click=search_radio_all%3A1&initiative_id=staobaoz_20190215&ie=utf8&sort=sale-desc'


class Taobao:
    @staticmethod
    def _get_track(distance):
        from random import randint

        track = []
        current = 0
        mid = distance * 4 / 5
        t = 0.2
        v = 0
        a = randint(50, 100)

        while current < distance:
            if current > mid:
                a *= -1

            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))

        return track

    def _move_to_gap(self, slider, tracks):
        from selenium.webdriver.common.action_chains import ActionChains

        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in tracks:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        sleep(0.5)
        ActionChains(self.browser).release().perform()

    def _fuck_taobao(self):
        sleep(0.5)
        self.browser.execute_script('Object.defineProperty(navigator,"webdriver",{get:()=>false,});')
        sleep(0.5)
        dragger = self.browser.find_element_by_id('nc_1_n1z')
        self._move_to_gap(dragger, Taobao._get_track(340))

    def __init__(self):
        from selenium import webdriver

        options = webdriver.ChromeOptions()
        options.add_experimental_option('prefs', {'profile.managed_default_content_settings.images': 2})
        self.browser = webdriver.Chrome(options=options)
        self.browser.set_page_load_timeout(10)
        self.browser.set_script_timeout(10)

        self.browser.get('https://login.taobao.com?f=top')
        self.browser.find_element_by_id('J_Quick2Static').click()
        self.browser.find_element_by_id('TPL_username_1').send_keys(USERNAME)
        self.browser.find_element_by_id('TPL_password_1').send_keys(PASSWORD)
        self._fuck_taobao()
        self.browser.find_element_by_id('J_SubmitStatic').click()

    def _get(self, url):
        from selenium.common.exceptions import TimeoutException

        while True:
            try:
                self.browser.get(url)
                break
            except TimeoutException:
                pass

    def _parse_page(self, keyword, page):
        self._get(PAGE.format(keyword, page * 44))
        while True:
            g_page_config = search(r'g_page_config = (.+?);\n', self.browser.page_source)
            if g_page_config is None:
                self._fuck_taobao()
                self.browser.refresh()
            else:
                return loads(g_page_config.group(1))['mods']['itemlist']['data']['auctions']

    def start(self, keyword, count):
        keywords = {}
        page = 1
        i = 0
        end = False
        while True:
            sleep(5)

            try:
                auctions = self._parse_page(keyword, page)
            except KeyError:
                break

            auctions_len = len(auctions)
            while True:
                sleep(5)

                keyword = auctions[i]['raw_title']
                title = self._parse_page(keyword, 1)[0]['title']
                i += 1

                for title in title.replace('<span class=H>', '').split('</span>')[:-1]:
                    if title in keywords:
                        keywords[title] += 1
                    else:
                        keywords[title] = 1

                if i == 44 and count > 44:
                    count -= 44
                    page += 1
                    i = 0
                    break
                if i == auctions_len or i == count:
                    end = True
                    break

            if end:
                return sorted(keywords.items(), key=lambda kv: kv[1], reverse=True)


if __name__ == '__main__':
    with open('keywords.txt', 'r') as f:
        keywords = f.readlines()

    # with open('result.txt', 'w') as f:
    #     taobao = Taobao()
    #     for keyword in keywords:
    #         keyword, count = keyword.split('@')
    #         count = int(count)
    #         if count != 0:
    #             keywords = taobao.start(keyword, count)
    #             result = keyword + ': {\n    '
    #             result += '\n    '.join([f'"{keyword}": {count},' for keyword, count in keywords])
    #             result += '\n}\n\n'
    #             f.write(result)
    #             f.flush()
    #
    #     taobao.browser.close()
