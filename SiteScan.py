#!/usr/bin/env python3

import aiohttp
import asyncio
import argparse
from bs4 import BeautifulSoup
import logging
import os
from itertools import product

logging.basicConfig(level = logging.INFO, format="%(levelname)s %(asctime)s %(message)s")
class SiteScan(object):

    def __init__(self, target_url, dict_dir='', max_thread=4):
        if "://" not in target_url:
            target_url = "http://" + target_url
        if not target_url.endswith('/'):
            target_url = target_url + '/'
        self.target_url = target_url
        self.dict_dir = dict_dir
        if self.dict_dir == '':
            self.dict_dir = os.path.split(os.path.realpath(__file__))[0] + '/dict'
        self.max_thread = max_thread
        self.queue = asyncio.Queue()
        self.dicts = {}
        self.init_dict()
        logging.info("Script init ok, target {}".format(target_url))
    
    def init_dict(self):
        dict_file = ['misc_file', 'back_file', 'general_file', 'package_ext', 'package_name']
        for file_name in dict_file:
            try:
                dic = self.load_dict(self.dict_dir + '/' + file_name + ".txt")
                logging.info("Loaded dict {}".format(file_name))
                self.dicts[file_name] = dic
            except:
                logging.warning("Load dict {} failed". format(file_name))


    def load_dict(self, path):
        with open(path, 'r') as f:
            raw_file = f.read()
        raw_file = raw_file.split('\n')
        dict_list = []
        for i in raw_file:
            if i and not i.startswith('#'):
                dict_list.append(i)
        return dict_list
    
    async def scan(self, url, queue):
        logging.debug("scan {}".format("url"))
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects = False) as resp:
                if resp.status == 301 or resp.status == 302:
                    print("[ {code} ] {raw} -> {now}".format(code=resp.status, raw = url, now = resp.headers["Location"]))
                    # add into queue
                    await queue.put(resp.headers["Location"])
                elif resp.status == 403 or resp.status == 200:
                    print("[ {code} ] {raw}".format(code=resp.status, raw = url))
                    if not url.endswith('/') and resp.status == 200:
                        # get file name
                        file_name = url.split('/')[-1]
                        path_name = '/'.join(url.split('/')[:-1]) + '/'
                        for back_file in self.dicts['back_file']:
                            await queue.put(path_name + back_file.replace("%FILE%", file_name))

    
    async def handler(self, queue):
        while not queue.empty():
            cur_url = await queue.get()
            try:
                await self.scan(cur_url, queue)
            except Exception as e:
                print(e)
    
    def start(self):
        # load file to queue
        for i in self.dicts['misc_file']:
            self.queue.put_nowait(self.target_url + i)
        for i in self.dicts['general_file']:
            self.queue.put_nowait(self.target_url + i.replace('%EXT%', 'php')) # to modify
        for pack_name, pack_ext in product(self.dicts['package_name'], self.dicts['package_ext']):
            self.queue.put_nowait(self.target_url + pack_name + pack_ext)
        loop = asyncio.get_event_loop()
        tasks = [self.handler(self.queue) for _ in range(self.max_thread)]
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

if __name__ == "__main__":
    print("""\
         _ __                                   
   _____(_) /____     ______________ _____      
  / ___/ / __/ _ \   / ___/ ___/ __ `/ __ \     
 (__  ) / /_/  __/  (__  ) /__/ /_/ / / / /     
/____/_/\__/\___/  /____/\___/\__,_/_/ /_/      
"""
    )
    scaner = SiteScan("http://localhost:8089")
    scaner.start()