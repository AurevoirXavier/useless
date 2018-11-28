import re
from lxml import etree
from json import dumps
from requests import session

s = session()
s.post(
    'http://e-learning.kingenta.com/Services/CommonService.svc/UserLogin',
    headers={'Content-Type': 'text/json'},
    data=dumps({"userName": "qianhuanchao", "password": "123456", "isAutoLogin": "false", "validateCode": "", "fromUrl": ""})
)

i = 0
for page in range(1, 8):
    resp = s.get(f'http://e-learning.kingenta.com/knowledgecatalogsearch.htm?id=11a1e71b-fc71-4909-a52b-8bf84b0f605f&rn=009&h=menu&pi={page}').text
    html = etree.HTML(resp)
    for url in html.xpath('//img[@class="el-placehold-body hand"]'):
        url = f'http://e-learning.kingenta.com{url.attrib["onclick"][13:-2]}'
        print(i, url)

        if 'video' in url:
            ids = re.search(
                r'\(\'(.+)\);',
                etree.HTML(s.get(url).text).xpath('//*[@id="liFavorite"]/span')[0].attrib['onclick']
            ).group(1).replace('\'', '').split(',')

            s.post(
                'https://api-qidatestin.yunxuetang.cn/v1/study',
                headers={
                    'Content-Type': 'application/json',
                    'token': 'AAAAALBZ3nJ91_krNaHDxZtzYeA2ZQpztrVDhcqsyackONCBvJsjTOyPmECF04WnywL2I5YzlkGMGY-2mCiIlH6W5ZST177ckQAWRXwYv1Vp1yMM8mVBeoV2REZg5cT4uiVR4rEKtkrrTfzCsTECp9KIawE'
                },
                data=dumps({"OrgID": f"{ids[0]}", "UserID": "1e47421c-bd1a-4d60-8126-42b9e23276ac", "KnowledgeID": f"{ids[2]}",
                            "PackageID": f"{ids[3]}", "MasterID": "", "MasterType": "", "PageSize": 1, "StudyTime": -1, "studyChapterIDs": "",
                            "Type": 0, "IsOffLine": False, "DeviceId": "", "IsEnd": True, "ReqType": 0, "IsCare": True,
                            "viewSchedule": 1000000.260882815})
            )
            i += 1
            continue

        if 'package' not in  url:
            continue

        video = etree.HTML(
            s.get(url).text
        ).xpath('//*[@id="divcourselist"]/div[1]/div[2]/div/div[3]/a/@href')[0][31:-50]

        if 'video' not in video:
            continue

        ids = re.search(
            r'\(\'(.+)\);',
            etree.HTML(s.get(f'http://e-learning.kingenta.com{video}').text).xpath('//*[@id="liFavorite"]/span')[0].attrib['onclick']
        ).group(1).replace('\'', '').split(',')

        s.post(
            'https://api-qidatestin.yunxuetang.cn/v1/study',
            headers={
                'Content-Type': 'application/json',
                'token': 'AAAAALBZ3nJ91_krNaHDxZtzYeA2ZQpztrVDhcqsyackONCBvJsjTOyPmECF04WnywL2I5YzlkGMGY-2mCiIlH6W5ZST177ckQAWRXwYv1Vp1yMM8mVBeoV2REZg5cT4uiVR4rEKtkrrTfzCsTECp9KIawE'
            },
            data=dumps(
                {"OrgID": f"{ids[0]}", "UserID": "1e47421c-bd1a-4d60-8126-42b9e23276ac", "KnowledgeID": f"{ids[2]}", "PackageID": f"{ids[3]}",
                 "MasterID": "", "MasterType": "", "PageSize": 1, "StudyTime": -1, "studyChapterIDs": "", "Type": 0, "IsOffLine": False,
                 "DeviceId": "", "IsEnd": True, "ReqType": 0, "IsCare": True, "viewSchedule": 1000000000.260882815})
        )

        i += 1