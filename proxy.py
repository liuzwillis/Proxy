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
from multiprocessing import Pool
from multiprocessing import Manager
import random
import config
import time


class ProxyPool:

    def __init__(self):

        # 一些配置
        # headers
        self.user_agents = config.user_agents

        # 目标url 和 要爬取的页数
        self.url = 'http://www.xicidaili.com/nn/'
        self.page_num = 5

        # 测试用url 和 响应时间
        self.test_url = 'http://ip.chinaz.com/getip.aspx'
        self.timeout = 5

        # 暂存的ip、good ip、good ip 存储的文件路径
        self.ips = set()
        self.good_ips = set()
        self.good_ip_txt = 'good_ip.txt'

        # pool
        self.pool_num = 30

    def headers(self):
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',
        }
        return headers

    def _download_html(self, url):
        if not url:
            return None
        resp = requests.get(url=url, headers=self.headers())
        if resp.status_code == 200:
            resp.encoding = 'utf-8'
            return resp.text

    def get_ip(self):
        patt = r'<td>(\d{1,3}\.\d{1,3}.\d{1,3}.\d{1,3})</td>.*?<td>(\d{2,5})</td>'
        for i in range(self.page_num):
            url = self.url + str(i+1)
            text = self._download_html(url)
            ip_tuples = re.findall(patt, text, re.S)
            self.ips.update(':'.join(ip) for ip in ip_tuples)

    def _validate_task(self, ip, q):
        proxy = {'http': ip}
        try:
            res = requests.get(url=self.test_url, headers=self.headers(), proxies=proxy, timeout=self.timeout)
            if res.status_code == 200:
                q.put(ip)
                print(ip, 'good\t√')
        except Exception as e:
            print(ip, 'bad')
            pass

    def validate(self):
        manager = Manager()
        q = manager.Queue()
        p = Pool(self.pool_num)
        for ip in self.ips:
            p.apply_async(self._validate_task, (ip, q))
        p.close()
        p.join()
        while not q.empty():
            value = q.get()
            self.good_ips.add(value)

    def load(self):
        """
        从文件读取ip
        :return:
        """
        try:
            with open(self.good_ip_txt, 'r') as f:
                ips = json.load(f)
                self.ips.update(ips)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return

    def output(self):
        """
        存储good_ip
        :return:
        """
        with open(self.good_ip_txt, 'w') as f:
            json.dump(list(self.good_ips), f, ensure_ascii=False)

    def wash(self):
        print('get ip...')
        self.load()
        self.get_ip()
        print('start washing ip, please wait...')
        time0 = time.time()
        self.validate()
        print('time: {:.2f}'.format(time.time()-time0))
        self.output()
        print('washed:{}/{}'.format(len(self.good_ips), len(self.ips)))

if __name__ == '__main__':
    pool = ProxyPool()
    pool.wash()
