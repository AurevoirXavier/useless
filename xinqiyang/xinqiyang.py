# --- std ---
from threading import Thread

# --- external ---
from requests import Session, session


class User(Thread):
    def __init__(self, username: str, password: str):
        super().__init__()
        self.s = session()
        self.username = username
        self.sign_in(password)

    def run(self):
        self.rush()

    def sign_in(self, password: str):
        # --- std ---
        from os import path, remove
        from tempfile import TemporaryFile
        # --- external ---
        from PIL import Image

        if path.isfile(f'{self.username}_cookie'):
            self.load_cookie()
        else:
            self.s.get('http://www.xinqiyang.cn')
            with TemporaryFile() as f:
                content = self.s.get('http://www.xinqiyang.cn/Home/login/verify').content
                f.write(content)
                Image.open(f).show()

            self.s.post(
                'http://www.xinqiyang.cn/Home/Login/logincl',
                data={
                    'ip': '8.8.8.8',
                    'account': self.username,
                    'password': password,
                    'verCode': input('验证码: ')
                }
            )

        if not self.check_sign_in():
            remove(f'{self.username}_cookie')
            self.sign_in(password)
        else:
            self.dump_cookie()

    def check_sign_in(self) -> bool:
        if self.s.get('http://www.xinqiyang.cn/Home/Index/me').url != 'http://www.xinqiyang.cn/Home/Index/me':
            print(f'[用户 {self.username} 登陆失败]')
            return False
        else:
            print(f'[用户 {self.username} 登陆成功]')
            return True

    def dump_cookie(self):
        # --- std ---
        from pickle import dump

        with open(f'{self.username}_cookie', 'wb') as f:
            dump(self.s.cookies, f)

    def load_cookie(self):
        # --- std ---
        from pickle import load

        with open(f'{self.username}_cookie', 'rb') as f:
            self.s.cookies.update(load(f))

    def rush(self):
        # --- external ---
        from re import compile

        regex = compile(r'alert\(\'(.+?)\'\)')

        # while True:
        #     resp = regex.search(self.s.get('http://www.xinqiyang.cn/Home/Myuser/qdc').text).group(1)
        #     print(resp)
        #     if resp != '抢单中心开放时间为19:00:00-19:30:00！':
        #         break

        for i in range(1, 41):
            text = self.s.get(f'http://www.xinqiyang.cn/Home/Myuser/grab/name/{i}').text
            # print(text)
            matched = regex.search(text)

            if matched is None:
                return

            resp = matched.group(1)
            print(f'用户 {self.username}, {i} 号 -> {resp}')

            if resp == '抢单时间已过！':
                print('[自动结束]')
                break


if __name__ == '__main__':
    users = []
    with open('accounts.txt', 'r') as f:
        for l in f:
            user = l.split('=')
            user = User(user[0], user[1])
            user.start()
            users.append(user)

    for user in users:
        user.join()
