#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/1 001 16:07
# @Author  : willis
# @Site    : 
# @File    : proxy.py
# @Software: PyCharm
import requests
import re
import json


class ProxyPool:

    def __init__(self):

        # headers
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36' \
                     ' (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.3964.2 Safari/537.3'
        self.headers = {'User-Agent': user_agent}

        # 目标url 和 要爬取的页数
        self.url = 'http://www.xicidaili.com/nn/'
        self.page_num = 1

        # 测试用url 和 响应时间
        self.test_url = 'http://ip.chinaz.com/getip.aspx'
        self.timeout = 3

        # 暂存的ip、good ip、good ip 存储的文件路径
        self.ips = set()
        self.good_ips = set()
        self.good_ip_txt = 'good_ip.txt'

    def _download_html(self, url):
        if not url:
            return None
        resp = requests.get(url=url, headers=self.headers)
        if resp.status_code == 200:
            resp.encoding = 'utf-8'
            return resp.text

    def get_ip(self):
        patt = r'<td>(\d{1,3}\.\d{1,3}.\d{1,3}.\d{1,3})</td>.*?<td>(\d{2,5})</td>'
        for i in range(self.page_num):
            url = self.url + str(i+1)
            text = self._download_html(url)
            ips = re.findall(patt, text, re.S)
            self.ips.update(ips)

    def test_and_save_ip(self):
        for ip in self.ips:
            if isinstance(ip, tuple):
                ip = ':'.join(ip)
            print(ip, end='\t')
            proxy = {'http': ip}
            errors = (requests.exceptions.ReadTimeout,
                      requests.exceptions.ConnectTimeout,
                      requests.exceptions.ProxyError,
                      requests.exceptions.ChunkedEncodingError,
                      requests.exceptions.ConnectionError
                      )
            try:
                r = requests.get(url=self.test_url, headers=self.headers, proxies=proxy, timeout=self.timeout)
            except errors:
                print('bad')
            else:
                if r.status_code == 200:
                    print('good\t\t\t√')
                    self.good_ips.add(ip)
                else:
                    print(r.status_code)

    def load(self):
        try:
            with open(self.good_ip_txt, 'r') as f:
                ips = json.load(f)
                self.ips.update(ips)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return

    def output(self):
        """
        存储时，good_ips有可能为空，这时也可写入
        :return:
        """
        with open(self.good_ip_txt, 'w') as f:
            json.dump(list(self.good_ips), f, ensure_ascii=False)

    def wash(self):
        self.load()
        self.get_ip()
        self.test_and_save_ip()
        self.output()
        print('washed:{}/{}'.format(len(self.good_ips), len(self.ips)))

if __name__ == '__main__':
    pool = ProxyPool()
    pool.wash()
