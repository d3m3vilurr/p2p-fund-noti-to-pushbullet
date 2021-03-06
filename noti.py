# -*- coding: utf-8 -*-
import os
import requests
import json
import lxml.html
from pushbullet import PushBullet
import config as CONFIG


class Channel(object):
    def __init__(self, max_item=-1):
        self.max_item = max_item

    def __iter__(self):
        raise StopIteration


class TankerFundChannel(Channel):
    TANKER_FUND_ITEM_LIST = 'https://api.tanker.fund/product/list/'
    TANKER_FUND_ITEM_DETAIL = 'https://tanker.fund/#/product/detail/%s'
    STATUS = dict(RESERVE=(1,),
                  OPEN=(2, 3),
                  CLOSE=(4, 5, 6, 7, 8))

    def __iter__(self):
        session = requests.Session()
        curr = 0
        while True:
            params = dict(count=9,
                          offset=curr,
                          filter_status=TankerFundChannel.STATUS['OPEN'])
            res = session.get(TankerFundChannel.TANKER_FUND_ITEM_LIST, params=params)
            datas = json.loads(res.text)
            if not datas.get('products'):
                raise StopIteration
            for item in datas.get('products'):
                url = TankerFundChannel.TANKER_FUND_ITEM_DETAIL % item['id']
                yield dict(id=str(item['id']),
                           title=item['title'],
                           description=item['short_description'] + ' ' + url)
                curr += 1
                if self.max_item <= 0:
                    continue
                if curr >= self.max_item:
                    raise StopIteration


class TeraFundChannel(Channel):
    TERA_FUND_URL = 'https://www.terafunding.com'
    TERA_FUND_INVEST = 'https://www.terafunding.com/Invest'
    TERA_FUND_DETAIL = TERA_FUND_INVEST + '/Detail/'

    def __iter__(self):
        session = requests.Session()
        curr = 0
        page = 0
        while True:
            page += 1
            params = dict(page_no=page, returnType='json')
            res = session.get(TeraFundChannel.TERA_FUND_INVEST, params=params)
            result = json.loads(res.text)
            # TODO check result Status
            products = json.loads(result['Message'])
            for product in products:
                title = product['Title']
                yield dict(id=product['FundsID'],
                           title=title,
                           description=TeraFundChannel.TERA_FUND_DETAIL + product['FundsID'])
                curr += 1
                if self.max_item <= 0:
                    continue
                if curr >= self.max_item:
                    raise StopIteration


class RoofFundChannel(Channel):
    ROOF_FUND_ITEM_LIST = 'https://www.rooffunding.com/v1/projects/page/%d'
    ROOF_FUND_ITEM_DETAIL = 'https://www.rooffunding.com/offers#/detail/%s'

    def __iter__(self):
        session = requests.Session()
        curr = 0
        page = 0
        while True:
            page += 1
            res = session.get(RoofFundChannel.ROOF_FUND_ITEM_LIST % page)
            datas = json.loads(res.text)
            if not datas.get('projects'):
                raise StopIteration
            for item in datas.get('projects'):
                url = RoofFundChannel.ROOF_FUND_ITEM_DETAIL % item['_id']
                yield dict(id=str(item['_id']),
                           title=item['title'],
                           description=item['address'] + ' ' + url)
                curr += 1
                if self.max_item <= 0:
                    continue
                if curr >= self.max_item:
                    raise StopIteration


class VillyChannel(Channel):
    VILLY_FUND_URL = 'https://www.villy.co.kr'
    VILLY_FUND_ITEM_LIST = 'https://www.villy.co.kr/product/fundList/total/realestate'
    VILLY_FUND_XPATHS = {
        'ITEMS': '//div[@class="row total-deal-row"]/div[@class="col-sm-6 col-md-4"]/a',
        'TITLE': './/div[@class="deal-card-detail"]/div[1]/h3',
        'DESC': './/div[@class="deal-card-detail"]/div[1]/div/p',
    }

    def __iter__(self):
        session = requests.Session()
        curr = 0
        page = 0
        while True:
            page += 1
            params = dict(page=page)
            res = session.get(VillyChannel.VILLY_FUND_ITEM_LIST, params=params)
            elem = lxml.html.fromstring(res.text)
            products = elem.xpath(VillyChannel.VILLY_FUND_XPATHS['ITEMS'])
            for product in products:
                title = product.xpath(VillyChannel.VILLY_FUND_XPATHS['TITLE'])[0] \
                        .text_content().strip()
                url = product.xpath('./@href')[0]
                desc =product.xpath(VillyChannel.VILLY_FUND_XPATHS['DESC'])[0] \
                        .text_content().strip()
                yield dict(id=url.split('/')[-1],
                           title=title,
                           description=desc + ' ' + VillyChannel.VILLY_FUND_URL + url)
                curr += 1
                if self.max_item <= 0:
                    continue
                if curr >= self.max_item:
                    raise StopIteration


class SoditChannel(Channel):
    SODIT_FUND_URL = 'https://www.sodit.co.kr'
    SODIT_FUND_ITEM_LIST = 'https://www.sodit.co.kr/investment/list.php'
    SODIT_FUND_XPATHS = {
        'ITEMS': '//section//div[@class="card"]',
        'TITLE': './/h4',
        'URL': './a/@href',
    }

    def __iter__(self):
        session = requests.Session()
        curr = 0
        page = 0
        checked = []
        while True:
            page += 1
            params = dict(page=page)
            res = session.get(SoditChannel.SODIT_FUND_ITEM_LIST, params=params)
            elem = lxml.html.fromstring(res.text)
            products = elem.xpath(SoditChannel.SODIT_FUND_XPATHS['ITEMS'])
            for product in products:
                title = product.xpath(SoditChannel.SODIT_FUND_XPATHS['TITLE'])[0] \
                        .text_content().strip()
                url = product.xpath(SoditChannel.SODIT_FUND_XPATHS['URL'])[0]
                uid = url.split('id=')[-1]
                if uid in checked:
                    continue
                checked.append(uid)
                yield dict(id=uid,
                           title=title,
                           description=SoditChannel.SODIT_FUND_URL + url)
                curr += 1
                if self.max_item <= 0:
                    continue
                if curr >= self.max_item:
                    raise StopIteration


bullet = PushBullet(CONFIG.PUSHBULLET_API)
if CONFIG.PUSHBULLET_CHANNEL:
    bullet = bullet.get_channel(CONFIG.PUSHBULLET_CHANNEL)

def push(title, message):
    bullet.push_note(title, message)


channels = [
    (u'탱커펀드', TankerFundChannel),
    (u'테라펀딩', TeraFundChannel),
    (u'루프펀딩', RoofFundChannel),
    (u'빌리', VillyChannel),
    (u'소딧', SoditChannel),
]

def main():
    for chan_name, ChannelCls in channels:
        pushed_fn = '.%s_pushed' % ChannelCls.__name__.lower()
        if not os.path.exists(pushed_fn):
            pushed = []
        else:
            with open(pushed_fn, 'r') as r:
                pushed = map(lambda x: x.strip(), r.readlines())
        for idx, item in enumerate(ChannelCls(20)):
            if item['id'] in pushed:
                continue
            push(chan_name + ': ' + item['title'], item['description'])
            pushed.append(item['id'])
        with open(pushed_fn, 'w') as w:
            w.write('\n'.join(pushed[-100:]))

if __name__ == '__main__':
    main()
