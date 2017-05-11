# coding:utf-8
__author__ = 'newpepsi'
import tornado.ioloop
import tornado.web
import requests

# 设置多个微信公众号
# 可以填写多个公众号的 appid appsecret
MPS = [('appid1', 'appkey1'), ('appid2', 'appkey2')]


class TokenCache(object):
    def __init__(self, appid, appsecret):
        self.appid = appid
        self.appsecret = appsecret
        self.access_token = ''
        self.expire_time = 0
        self.jsapi_ticket = ''
        self.wx_card_ticket = ''

    def get_ticket(self, access_token, type='jsapi'):
        '''
        
        :param access_token: update access token中生成的access_token
        :param type:  jsapi / wx_card 两个可选
        :return: 
        '''
        attr_name = '{}_ticket'.format(type)
        if hasattr(self, attr_name):
            url = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={}&type={}'.format(
                access_token, type)
            r = requests.get(url)
            data = r.json()
            if data.get('ticket'):
                ticket = data.get('ticket')
                setattr(self, attr_name, ticket)
                self.save()

    def update_access_token(self):
        import time
        if self.expire_time < int(time.time()):
            url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}'.format(
                self=self)
            r = requests.get(url)
            data = r.json()
            self.access_token = data.get('access_token')
            self.expire_time = time.time() + 7100
            self.save()
            self.get_ticket(self.access_token)
            self.get_ticket(self.access_token, 'wx_card')
        return self.access_token

    def get_access_token(self):
        return self.update_access_token()

    @property
    def data(self):
        return {'appid': self.appid, 'expire': self.expire_time, 'access_token': self.access_token,
                'js_ticket': self.jsapi_ticket, 'wx_card_ticket': self.wx_card_ticket}

    @property
    def json(self):
        import json
        return json.dumps(self.data)

    def save(self):
        '''dump to local'''
        pass


class MpDoesNotExists():
    pass


class TokenManager(object):
    tokens = {}

    @classmethod
    def create_mps(cls, mp_list):
        for pairs in mp_list:
            cls.create_mp(*pairs)

    @classmethod
    def create_mp(cls, appid, appsecret):
        cache = TokenCache(appid, appsecret)
        cache.update_access_token()
        cls.tokens[appid] = cache

    @classmethod
    def find_mp(cls, appid):
        return cls.tokens.get(appid, {})

    @classmethod
    def remove_mp(cls, appid):
        try:
            del cls.tokens[appid]
        except Exception as e:
            pass


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        appid = self.get_query_argument('appid')
        try:
            cache = TokenManager.find_mp(appid)
            self.set_header('content_type', 'application/json')
            self.write(cache.data)
        except Exception as e:
            pass


application = tornado.web.Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    TokenManager.create_mps(MPS)

    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
