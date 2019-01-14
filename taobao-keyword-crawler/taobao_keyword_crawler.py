import requests
from time import sleep
from selenium import webdriver
from os import path

page = 'https://s.taobao.com/search?q={}&sort=sale-desc'

s = requests.session()

s.headers = {
    'User-Agent': 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.2 Safari/605.1.15',
    'Cookie': 'isg=BA0NW-D9bdChqMnane_cFzcuHi-H6kG8rBGltk-WM6RORin4Fz9hjEOUtFIgnVl0; JSESSIONID=FDB4A4E17B54ADF167B0EA0546016356; mt=ci=0_1; uc1=cookie16=URm48syIJ1yk0MX2J7mAAEhTuw%3D%3D&cookie21=W5iHLLyFeYZ1WM9hVnmS&cookie15=W5iHLLyFOGW7aA%3D%3D&existShop=false&pas=0&cookie14=UoTYMbtSsuN2KA%3D%3D&tag=8&lng=zh_CN; lastalitrackid=login.taobao.com; _cc_=VT5L2FSpdA%3D%3D; _l_g_=Ug%3D%3D; _nk_=c_est_laviexavier; cookie1=WvSXAMmIcHV89bhJ52wQzQKcAG5tglJR2JNP7BUGPwg%3D; cookie17=UUtJZXMmPUavuQ%3D%3D; cookie2=18e1a89fa68a305df7567a35d1848318; csg=47d83d8f; dnk=c_est_laviexavier; existShop=MTU0NzQ3NTA1OA%3D%3D; lgc=c_est_laviexavier; sg=r50; skt=741c939e1f16cc25; t=1d60d70700ddc96c75f07f49c9e414ad; tg=0; tracknick=c_est_laviexavier; uc3=vt3=F8dByE%2BluQSu8DlJVaw%3D&id2=UUtJZXMmPUavuQ%3D%3D&nk2=AEX5p0zcb460L%2F7OOY2ms58%3D&lg2=UIHiLt3xD8xYTw%3D%3D; unb=2322140705; x5sec=7b227365617263686170703b32223a223032643430316161626364343639386465353266393136666530346335616466434c757538754546454f7969696f69486d5a3757756745614444497a4d6a49784e4441334d4455374d673d3d227d; l=aBClWJAYyF0iDzLKLMaiDXDCvxrxygBPugO3xMwzHiYGdP8ZuXKbBCWvP_wwN2Rttq7so0dj9cB2.; _uab_collina=154747116048853104969016; alitrackid=www.taobao.com; _tb_token_=5156377eeee5e; v=0; ali_ab=14.21.201.175.1545302324373.6; hng=CN%7Czh-CN%7CCNY%7C156; cna=pBdzFKD9mTwCAQ4Vyb+9V15k; thw=cn; enc=%2F18KiLG2VjlWIIslbuWqnKaDybUhIVjKSmWzeq5nkdmMrjmE2iuAT%2BflkwSzUqXm2bLnyRmiqK6C9%2FqWpEwOaw%3D%3D; miid=1052939520957951070'
}

keyword = '温度计'
resp = s.get(page.format(keyword)).text
print(resp)
