from random import randint
from requests import session

s = session()
s.headers = {}

s.get('https://zhengzhou.xueanquan.com/login.html#')

resp = s.get(
    'https://henanlogin.xueanquan.com/LoginHandler.ashx',
    params={
        'jsoncallback': '',
        'userName': 'zhangquanyi2097',
        'password': 'a496358650',
        'checkcode': '',
        'type': 'login',
        'loginType': '1',
        'r': f'0.429381873551191{randint(0, 10)}',
    }
).text

print(resp)

resp = s.post(
    'https://zhengzhou.xueanquan.com/jiating/ajax/FamilyEduCenter.EscapeSkill.SeeVideo,FamilyEduCenter.ashx',
    data='''
workid=966893
fid=281
title=正视自我开心生活
require=
purpose=
contents=
testwanser=0|0|0
testinfo=已掌握技能
testMark=100
testReulst=1
SiteName=
siteAddrees=
watchTime=
CourseID=802
'''.encode('utf8'),
    params={
        '_method': 'TemplateIn2',
        '_session': 'rw',
    },
).text

print(resp)
