import requests
import re, json, sys, time, os
from bs4 import BeautifulSoup as bs
from urllib import parse

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Cookie
CSRFTOKEN = '1a1b02e976dcbe39fa83152c89daee5d9eb52f84s%3A88%3A%22N01GMWlINFN2dmlVMjlidGxTUUJ0M2Zzdmt1d3FoWHofm4htJfQtaGj6TjMR8QeKh9ZKM1H885iY8eGlyC8Pmg%3D%3D%22%3B'

# FB LOGIN
EMAIL = 'atm213001@gmail.com'
PASSWD = 'eva900507'

BUTTONNUM = 1
place = '搖滾F區'
# 0 is most expensive and -1 is cheapest
AREASELECT = 0

TICKETNUM = 1

ACTIVITY = '18_911'

# LOG
LOGFILE = False
STOREVC = False
ISDUG = False

# =======  config end  =======

DOMAIN = 'https://tixcraft.com'
GAMEPATH = '/activity/game/'
CAPTCHAPATH = '/ticket/captcha?v=5b666af4689f9'
CHECKPATH = '/ticket/check'
PAYMENTPATH = '/ticket/payment'
FACEBOOKPATH = '/login/facebook'
ORDERPAGE = '/ticket/order'

headers = {}

proxies = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080",
}


class MyRequests:
    def __init__(self, url, headers=None, data=None):
        self.url = url
        self.headers = headers
        self.data = data
        self.proxies = {
            "http": "http://127.0.0.1:8080",
            "https": "http://127.0.0.1:8080",
        }

    def get(self):
        if not ISDUG:
            return requests.get(url=self.url, headers=self.headers, allow_redirects=False)
        else:
            return requests.get(url=self.url, headers=self.headers, allow_redirects=False, proxies=self.proxies,
                                verify=True)

    def post(self):
        if not ISDUG:
            return requests.post(url=self.url, headers=self.headers, data=self.data, allow_redirects=False)
        else:
            return requests.post(url=self.url, headers=self.headers, data=self.data, allow_redirects=False,
                                 proxies=self.proxies, verify=True)


def getCaptcha():
    resp = MyRequests(url=DOMAIN + CAPTCHAPATH, headers=headers).get()
    with open('temp.png', 'wb') as f:
        f.write(resp.content)


def gamePage():
    buttons = []
    urls = []
    i = 0
    while len(buttons) == 0:
        i += 1
        time.sleep(0.00001)
        url = DOMAIN + GAMEPATH + ACTIVITY
        resp = MyRequests(url=url, headers=headers).get()
        soup = bs(resp.text, 'lxml')
        buttons = soup.find_all("input", type="button")
        if buttons:
            inputTag = soup.find_all('input', {'class': 'btn btn-info-filled btn-rounded'})
            if not inputTag:
                inputTag = buttons
            for tag in inputTag:
                urls.append(tag['data-href'])
        print(i)
    return urls


def selectArea(resp):
    try:
        areaUrlListstr = re.search(r'areaUrlList = {(.*?)};', resp.text).group(1)
        try:
            # print(re.findall(r'span>(.*?)<font', resp.text))
            seat = re.findall(r'id="([\d\_]*)"', resp.text)
            for i in seat:
                if place in re.search(i + r'"(.*?)span>(.*?)<font', resp.text).group(2):
                    areaUrlList = re.findall(i + r'":"(.*?)"', areaUrlListstr)[0].replace('\\', '')
                    return DOMAIN + areaUrlList
            raise IndexError

        except:
            areaUrlList = [i.replace('\\', '') for i in re.findall(r'"(.*?)"', areaUrlListstr) if 'ticket' in i]
            return DOMAIN + areaUrlList[AREASELECT]
    except:
        print("[!] Can't select areas!")
        sys.exit()


def areaPage(url):
    resp = MyRequests(url=url, headers=headers).get()
    if resp.status_code == 200:
        return selectArea(resp)
    else:
        locationUrl = resp.headers['Location']
        # pass verify page
        if 'verify' in locationUrl:
            head = headers
            resp = MyRequests(url=locationUrl, headers=head).get()
            soup = bs(resp.text, 'lxml')
            csrftoken = soup.find('input', attrs={'name': 'CSRFTOKEN'})['value']
            thing = soup.select('div.zone-verify')[0].get_text().strip() + '\nAnswer:'
            checkCode = input(thing)
            postdata = {
                "CSRFTOKEN": csrftoken,
                "checkCode": checkCode
            }
            checkCode_url = locationUrl.replace('verify', 'checkCode')
            resp = MyRequests(url=checkCode_url, headers=head, data=postdata).post()
            postdata['confirmed'] = True
            head['X-Requested-With'] = 'XMLHttpRequest'
            resp = MyRequests(url=checkCode_url, headers=head, data=postdata).post()
            return areaPage(url)
        else:
            return locationUrl


def ticketPage_get(ticketurl):
    resp = MyRequests(url=ticketurl, headers=headers).get()
    agreebs64 = re.search(r'agree\]\[(.*?)\]', resp.text).group(1)
    ticketPricebs64 = re.findall(r'TicketForm\[ticketPrice\]\[(.*?)\]', resp.text)[-1]
    soup = bs(resp.text, 'lxml')
    select = soup.find('select')['id']
    selectnum = select.split('_')[-1]
    csrftoken = soup.find('input', id='CSRFTOKEN')['value']
    return selectnum, csrftoken, agreebs64, ticketPricebs64


def ticketPage_post(url, captcha, num, csrftoken, agreebs64, ticketPricebs64):
    postdata = {
        "CSRFTOKEN": csrftoken,
        "TicketForm[ticketPrice][{}]".format(num): TICKETNUM,
        "TicketForm[ticketPrice][{}]".format(ticketPricebs64): TICKETNUM,
        "TicketForm[verifyCode]": captcha,
        "TicketForm[agree][{}]".format(agreebs64): "1",
        "ticketPriceSubmit": "確認張數"
    }
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    resp = MyRequests(url=url, headers=headers, data=parse.urlencode(postdata)).post()
    return True if resp.status_code == 302 else False


def orderPage():
    MyRequests(url=DOMAIN + ORDERPAGE, headers=headers).get()


def checkPage():
    headers['X-Requested-With'] = 'XMLHttpRequest'
    while 1:
        resp = MyRequests(url=DOMAIN + CHECKPATH, headers=headers).get()

        print(resp)

        print("Please waiting...")
        if json.loads(resp.text)['time'] == 0:
            print("Be going to check out...")
            break
        time.sleep(3)


def paymentPage():
    MyRequests(url=DOMAIN + PAYMENTPATH, headers=headers).get()


def printstr(string):
    print('[*] %s' % string)


# !not use
def login_facebook():
    global SID
    driver = webdriver.Firefox()
    driver.get(DOMAIN)
    elem = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "loginFacebook"))
    )
    driver.get(DOMAIN + FACEBOOKPATH)
    elem = driver.find_element_by_id("email")
    elem.send_keys(EMAIL)
    elem = driver.find_element_by_id("pass")
    elem.send_keys(PASSWD)
    elem.send_keys(Keys.RETURN)
    try:
        elem = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "logout"))
        )
        printstr('Login success')
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie['name'] == 'SID' and cookie['domain']:
                SID = cookie['value']
        with open('cookie', 'w') as f:
            f.write(SID)
        driver.quit()
    except:
        print("[!] Login failed")
        driver.quit()
        sys.exit()


def setHeader():
    global headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
        "Cookie": "_ga=GA1.2.978052635.1535849453; SID={}; CSRFTOKEN={}; _gid=GA1.2.934178753.1535849453; lang=1a73f0317e76f38c9adb36e69bdc73613602f560s%3A5%3A%22zh_tw%22%3B".format(
            SID, CSRFTOKEN)
    }


def isLogin():
    global SID
    try:
        f = open('cookie', 'r')
        SID = f.read().strip()
    except:
        return False
    setHeader()
    resp = MyRequests(url=DOMAIN + '/order', headers=headers).get()
    soup = bs(resp.text, 'lxml')
    logout = soup.find('a', {'id': 'logout'})
    return True if logout else False


def main():
    if not isLogin():
        printstr('FB logining...')
        login_facebook()
        setHeader()
    # setHeader()
    # printstr('Get verification code...')
    # getCaptcha()
    # time.sleep(2)
    # captcha = input('>>> verify code : ')
    printstr('Get button...')
    urls = gamePage()
    printstr('Choose area...')
    ticketurl = areaPage(DOMAIN + urls[BUTTONNUM - 1])
    printstr('Submit order...')
    num, csrftoken, agreebs64, ticketPricebs64 = ticketPage_get(ticketurl)
    # ticketSuccess = ticketPage_post(ticketurl, captcha, num, csrftoken, agreebs64, ticketPricebs64)
    ticketSuccess = False
    while not ticketSuccess:
        print('[!] Get verification code...')
        getCaptcha()
        captcha = input('>>> verify code : ')
        ticketSuccess = ticketPage_post(ticketurl, captcha, num, csrftoken, agreebs64, ticketPricebs64)
    orderPage()
    checkPage()
    paymentPage()
    printstr('Success! Please visit the main station for orders.')

    ticketPage_post(ticketurl, 'aaaa', num, csrftoken, agreebs64, ticketPricebs64)

    if not STOREVC:
        if os.path.exists("temp.png"):
            os.remove("temp.png")


if __name__ == '__main__':
    main()
