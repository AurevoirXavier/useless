from requests import session


class Du:
    def __init__(self):
        self.__session = session()

    def sign_in(self):
        resp = self.__session.post(
            'https://m.poizon.com/users/unionLogin',
            data={
                '_timestamp': '1550048252414',
                'accessToken': '',
                'code': '',
                'countryCode': '86',
                'expire': '0',
                'mode': '0',
                'openId': '',
                'password': '127b128647b1a758b9d16675816530c2',
                'platform': 'iPhone',
                'refreshToken': '',
                'sign': '5b1058d22c399e76a03ddb2e2bd8f3a4',
                'sourcePage': '',
                'token': 'JLIjsdLjfsdII%3D%7CMTQxODg3MDczNA%3D%3D%7C07aaal32795abdeff41cc9633329932195',
                'type': 'pwd',
                'userName': '13672696485',
                'uuid': '415F29EA-2747-4A7E-87AF-124EB68A846D',
                'v': '3.5.5'
            }
        ).json()

        # print(resp)

        if resp['msg'] == '成功':
            return True
        else:
            return False

    def get_product(self, product_id):
        resp = self.__session.get(
            'https://m.poizon.com/product/detail',
            params={
                '_timestamp': '1550139390783',
                'isChest': '1',
                'lastId': '',
                'loginToken': '7fcbd841|41765824|3f534c7ad82d01ca',
                'mode': '0',
                'newSign': '3d062cf00d1560947dbe139251e406a1',
                'platform': 'iPhone',
                'productId': str(11172),
                'sign': '52cf486d5f3f9b72d3afbb80829c8a08',
                'token': 'JLIjsdLjfsdII%3D%7CMTQxODg3MDczNA%3D%3D%7C07aaal32795abdeff41cc9633329932195',
                'uuid': '415F29EA-2747-4A7E-87AF-124EB68A846D',
                'v': '3.5.5'
            }
        ).json()

        # print(resp)

        return resp

    def get_products(self, cat_id, union_id, page):
        resp = self.__session.get(
            'https://m.poizon.com/search/list',
            params={
                '_timestamp': '1550048604818',
                'catId': str(cat_id),
                'lastId': '',
                'limit': '20',
                'loginToken': '7fcbd841|41765824|3f534c7ad82d01ca',
                'mode': '0',
                'newSign': 'fffde6b35ea1f59bd55f1e13c91a2ae0',
                'page': str(page),
                'platform': 'iPhone',
                'sign': '16b7f6e1f102d4f3a48ebae2924b677b',
                'sortMode': '1',
                'sortType': '0',
                'token': 'JLIjsdLjfsdII%3D%7CMTQxODg3MDczNA%3D%3D%7C07aaal32795abdeff41cc9633329932195',
                'unionId': union_id,
                'uuid': '415F29EA-2747-4A7E-87AF-124EB68A846D',
                'v': '3.5.5'
            }
        ).json()

        # print(resp)

        return resp['data']['productList']

    def to_get_products(self, cat_id, union_id):
        page = 0
        while True:
            products = self.get_products(cat_id, union_id, page)

            if not products:
                break

            for product in products:
                # product = self.get_product(product['productId'])
                print(product)
                # print('\n\n\n')

            page += 1

    def get_category(self, params):
        resp = self.__session.get('https://m.poizon.com/search/categoryDetail', params=params).json()

        # print(resp)

        return resp['data']['list']

    def to_get_category(self, cat_id):
        for series in self.get_category(cat_id):
            for product in series['seriesList']:
                self.to_get_products(cat_id, product['redirect']['val'])

    def get_shoes(self):
        params = {
            'loginToken': '7fcbd841|41765824|3f534c7ad82d01ca',
            'mode': '0',
            'platform': 'iPhone',
            'token': 'JLIjsdLjfsdII%3D%7CMTQxODg3MDczNA%3D%3D%7C07aaal32795abdeff41cc9633329932195',
            'uuid': '415F29EA-2747-4A7E-87AF-124EB68A846D',
            'v': '3.5.5'
        }

        # sneakers
        params.update({
            '_timestamp': '1550139214323',
            'catId': '3',
            'newSign': 'f150ff482f420f9b6e5f3003acbf3e64',
            'sign': '39499701efb551aeed20a99c51f9014a',
        })
        self.to_get_category(params)
        # casual Shoes
        params.update({
            '_timestamp': '1550152434910',
            'catId': '4',
            'newSign': 'adf4064cfc9f9e3ee39e2928fdaf38df',
            'sign': '48cc82a7fde9f0269c58c430cf6a8434',
        })
        self.to_get_category(params)
        # running shoes
        params.update({
            '_timestamp': '1550152317000',
            'catId': '5',
            'newSign': '75ce7067905b8b8e7700f85c1b23982e',
            'sign': '4fbbd35d4b2aedf3c0df2c4b64af5dc2',
        })
        self.to_get_category(params)


if __name__ == '__main__':
    du = Du()
    if du.sign_in():
        du.get_shoes()
