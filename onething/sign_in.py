# std
from time import sleep

# external
from requests import Session
from requests.exceptions import RequestException

# custom
from setting import PROXY, MANUAL_PROXY
from util import COMMON_HEADERS, gen_unknown_id, gen_uuid


def md5(string: str) -> str:
    import hashlib
    return hashlib.md5(string.encode('utf8')).hexdigest().lower()


def encrypt_passwd(passwd: str) -> str:
    cipher = md5(passwd)
    return md5(f'{cipher[0:2]}{cipher[8]}{cipher[3:8]}{cipher[2]}{cipher[9:17]}{cipher[27]}{cipher[18:27]}{cipher[17]}{cipher[28:]}')


def generate_sign(data: dict, k='') -> str:
    l = []
    while len(data) != 0:
        v = data.popitem()
        l.append(v[0] + '=' + v[1])
    l.sort()

    t = 0
    s = ''
    while t != len(l):
        s = s + l[t] + '&'
        t = t + 1
    s = s + 'key=' + k

    return md5(s)


def build_payload(account, passwd) -> dict:
    unknown_id = gen_unknown_id()
    payload = {
        'deviceid': unknown_id,
        'imeiid': unknown_id,
        'nc': 'GB',
        'ph_model': 'iPhone 6s',
        'ph_ver': 'iOS 12.0.1',
        'pwd': encrypt_passwd(passwd),
        'uuid': gen_uuid()
    }
    if '@' in account:
        payload.update({'account_type': '5', 'mail': account})
    else:
        payload.update({'account_type': '4', 'phone': account, 'phone_area': '86'})
    payload['sign'] = generate_sign(dict(payload))

    # print(payload)  # TODO Debug

    return payload


def sign_in(account: str, passwd: str) -> (bool, Session):
    print('[?] [尝试登入]')

    session = Session()

    if PROXY:
        while True:
            try:
                session.proxies = MANUAL_PROXY
                resp = session.post(
                    'https://api-accw.onethingpcs.com/user/login?appversion=2.0.1',
                    data=build_payload(account, passwd),
                    headers=COMMON_HEADERS,
                    timeout=(10, 10),
                    verify=False
                ).json()
                break
            except RequestException:
                continue
    else:
        resp = session.post(
            'https://api-accw.onethingpcs.com/user/login?appversion=2.0.1',
            data=build_payload(account, passwd),
            headers=COMMON_HEADERS,
            verify=False
        ).json()

    # print(resp)  # TODO Debug

    if resp['sMsg'] == '成功':
        print('    [✓] [登入成功]')
        sleep(1)
        return True, session
    return False, None
