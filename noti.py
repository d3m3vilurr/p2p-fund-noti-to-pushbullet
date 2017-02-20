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
                yield dict(id=str(item['id']),
                           title=item['title'],
                           description=item['short_description'])
                curr += 1
                if self.max_item <= 0:
                    continue
                if curr >= self.max_item:
                    raise StopIteration


class TeraFundChannel(Channel):
    TERA_FUND_URL = 'https://www.terafunding.com'
    TERA_FUND_INVEST = 'https://www.terafunding.com/Invest'
    TERA_FUND_XPATHS = {
        'ITEMS': '//div[@id="contents_wraper"]//ul[@class="row grid-block-v2"]/li',
        'LINK': './/div[@class="caption_goods"][1]/h3[@class="mgoods2-tit"][1]//a'
    }

    def __iter__(self):
        session = requests.Session()
        curr = 0
        page = 0
        while True:
            page += 1
            params = dict(page_no=page)
            res = session.get(TeraFundChannel.TERA_FUND_INVEST, params=params)
            elem = lxml.html.fromstring(res.text)
            products = elem.xpath(TeraFundChannel.TERA_FUND_XPATHS['ITEMS'])
            for product in products:
                link = product.xpath(TeraFundChannel.TERA_FUND_XPATHS['LINK'])[0]
                title = link.text_content().strip()
                url = link.xpath('./@href')[0]
                yield dict(id=url.split('/')[-1],
                           title=title,
                           description=TeraFundChannel.TERA_FUND_URL + url)
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
    (u'테라펀드', TeraFundChannel),
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