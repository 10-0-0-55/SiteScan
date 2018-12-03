#!/usr/bin/env python3

import aiohttp
import asyncio
import argparse
from bs4 import BeautifulSoup
import logging
import os
from itertools import product
import requests
from urllib.parse import urljoin

logging.basicConfig(level = logging.INFO, format="%(levelname)s %(asctime)s %(message)s")
class SiteScan(object):

    def __init__(self, target_url, dict_dir='', max_thread=4, mode = 'php'):
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
        self.mode = mode
        logging.info("Script init ok, target {}".format(target_url))
    
    def init_dict(self):
        dict_file = ['misc_file', 'back_file', 'general_file', 'package_ext', 'package_name', 'framework']
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
                    print("[ {code} ] {raw} -> {now}".format(code=resp.status, raw = url, now = urljoin(url,resp.headers["Location"])))
                    # add into queue
                    await queue.put(urljoin(url,resp.headers["Location"]))
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
        # first request
        r = requests.get(self.target_url, allow_redirects=False)
        if 'Server' in r.headers:
            logging.info('Remote Server: {}'.format(r.headers['Server']))
            if "Werkzeug" in r.headers["Server"]:
                print('It looks like the backend is flask')
                if self.mode != "php":
                    while True:
                        print("switch into framework mode? [Y/n]")
                        cmd = input()
                        if cmd == '' or cmd == 'y' or cmd == 'Y':
                            self.mode = 'framework'
                            break
                        if cmd == 'n' or cmd == 'N':
                            break

        if 'X-Powered-By' in r.headers:
            logging.info('The Backend: {}'.format(r.headers['X-Powered-By']))
            if "PHP" in r.headers['X-Powered-By']:
                print('It looks like the backend is PHP')
                if self.mode != "php":
                    while True:
                        print("switch into php mode? [Y/n]")
                        cmd = input()
                        if cmd == '' or cmd == 'y' or cmd == 'Y':
                            self.mode = 'php'
                            break
                        if cmd == 'n' or cmd == 'N':
                            break
            elif "Express" in r.headers['X-Powered-By']:
                print("It looks like the backend is nodejs")
                if self.mode != "framework":
                    while True:
                        print("switch into framework mode? [Y/n]")
                        cmd = input()
                        if cmd == '' or cmd == 'y' or cmd == 'Y':
                            self.mode = 'framework'
                            break
                        if cmd == 'n' or cmd == 'N':
                            break

            
        # load file to queue
        self.queue.put_nowait(self.target_url)
        if self.mode == 'framework':
            for i in self.dicts['framework']:
                self.queue.put_nowait(self.target_url + i)
        else:
            for i in self.dicts['misc_file']:
                self.queue.put_nowait(self.target_url + i)
            for i in self.dicts['general_file']:
                self.queue.put_nowait(self.target_url + i.replace('%EXT%', self.mode)) # to modify
            for pack_name, pack_ext in product(self.dicts['package_name'], self.dicts['package_ext']):
                self.queue.put_nowait(self.target_url + pack_name + pack_ext)
        loop = asyncio.get_event_loop()
        tasks = [self.handler(self.queue) for _ in range(self.max_thread)]
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

if __name__ == "__main__":
    print(r"""         _ __                                   
   _____(_) /____     ______________ _____      
  / ___/ / __/ _ \   / ___/ ___/ __ `/ __ \     
 (__  ) / /_/  __/  (__  ) /__/ /_/ / / / /     
/____/_/\__/\___/  /____/\___/\__,_/_/ /_/      
""")
    parser = argparse.ArgumentParser(description="This script uses the aiohttp library's head() method to determine the status word.")
    # 位置参数
    parser.add_argument("website", type=str, help="The website that needs to be scanned")
    # 可选参数
    parser.add_argument('-d', '--dict', dest="scanDictDir", help="Dictionary Directory for scanning", type=str, default="")
    parser.add_argument('-m', '--mode', dest="mode", help="Target site backend ", type=str, default='php')
    parser.add_argument('-t', '--thread', dest="threads", help="Number of coroutine running the program", type=int, default=50)
    parser.add_argument('-f', '--file', dest="file", action="store_true")
    args = parser.parse_args()
    if args.file:
        path_name = '/'.join(args.website.split('/')[:-1]) + '/'
        scaner = SiteScan(path_name, args.scanDictDir, args.threads, args.mode)
        scaner.queue.put_nowait(args.website)
    else:
        scaner = SiteScan(args.website, args.scanDictDir, args.threads, args.mode)
    scaner.start()
    logging.info("All down")