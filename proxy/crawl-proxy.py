#!/usr/bin/python
# -*- coding: utf-8 -*-

# HOW TO RUN?
# python3 crawl-proxy.py (default --checkurl https://api.ipify.org/)
# python3 crawl-proxy.py --checkurl https://newyork.craigslist.org/


import argparse
import logging
import re
import requests
import copy
import time
import threading
from bs4 import BeautifulSoup
from lxml import etree
from parsel import Selector
from twisted.web import client
from scrapy.http import Request,FormRequest
from scrapy.core.downloader.handlers.http11 import HTTP11DownloadHandler
from scrapy.settings import Settings
from twisted.internet import reactor,defer,task
import pymongo
from queue import Queue

def log(args):
  logger = logging.getLogger("IPlogger")
  logger.setLevel(logging.INFO)
  filehandler = logging.FileHandler(map_checkurl_to_collection_name_and_logfile(args)[1],'w')
  formatter =  logging.Formatter('%(asctime)s  %(filename)s  %(levelname)s - %(message)s',datefmt='%a, %d %b %Y %H:%M:%S',)
  filehandler.setFormatter(formatter)
  logger.addHandler(filehandler)
  return logger


def map_checkurl_to_collection_name_and_logfile(args):
  if "api.ipify.org" in args.checkurl:
    return ("IPs","fetch_ip.log")
  elif "craigslist" in args.checkurl:
    return ("IPs_cg","fetch_ip_cg.log")
  elif "zillow" in args.checkurl:
    return ("IPs_zw","fetch_ip_zw.log")
  elif "airbnb" in args.checkurl:
    return ("IPs_air","fetch_ip_air.log")

def parse_args():
  parser = argparse.ArgumentParser(description="Get proxy from multiple sources'")
  group0=parser.add_argument_group('common')
  group0.add_argument("--conc",help="concurrent numbers",type=int,default=20)
  group0.add_argument("--timeout",type=int,default=15,help="timeout of request")
  group0.add_argument("-v", "--verbose", help="increase output verbosity",action="store_true")

  group1=parser.add_argument_group('Proxy get')
  group1.add_argument("--country",help="Get proxy from specified country")
  group1.add_argument("--reverse",action="store_true",help="Get proxy except specified country")
  group1.add_argument("--maxpage",type=int,default=25,help="max page number of 'http://gatherproxy.com'")

  group2 = parser.add_argument_group('Proxy check')
  group2.add_argument("--checkurl",type=str,default="https://api.ipify.org/",help="checking url")
  group2.add_argument("--checknum",type=int,default=1,help="checking times for every proxy")
  group2.add_argument("--checkthreshold",type=float,default=0.6,help="threshold for successful request percentage")
  args = parser.parse_args()
  if args.verbose:
    logger.setLevel(logging.DEBUG)
  return args

class find_http_proxy():
  """ find proxy from "http://gatherproxy.com/"(needs proxy to visit in China)
      
      Will only gather L1 (elite anonymity) proxies which should not 
      give out your IP or advertise that you are using a proxy at all.
      
      Attributes:
          proy_file: A txt which would save a list of valid proxy 
          country: find specified country proxy
          reverse:  filter opposite country proxy
          checknum: checking times for every proxy
          checkthreshold: threshold for successful request percentage
          proxy_list: A list consist of proxy and port 
          headers: A default user-agent setting
  """
  def __init__(self,args):
    self.concurrent = args.conc
    self.country = args.country     
    self.reverse = args.reverse if self.country else None
    self.maxpage = args.maxpage
    self.checknum = args.checknum
    self.checkthreshold = args.checkthreshold
    self.checkurl = args.checkurl
    self.timeout = args.timeout
    self.proxy_list = []
    self.passproxy = set()  # records proxy which conforms to the condition: successful rate above some level     
    self.headers = {'USER-AGENT':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36'}

  def getherproxy_req(self):
    """ Get proxy from gatherproxy.com"""
    proxys=[]
    url = 'http://www.gatherproxy.com/proxylist/anonymity/?t=Elite'
    for pagenum in range(1,self.maxpage+1):
      try:
        data = {'Type':'elite','PageIdx':str(pagenum),'Uptime':'0'}
        headers = copy.copy(self.headers)
        r = requests.post(url, headers=headers, data=data) 
        proxys = proxys + self._get_proxy(r.text,country=self.country)
      except Exception as e:
        logger.fatal(str(e))
        logger.fatal('[!] Failed: %s' % url)
    logger.info("Finished getherproxy(length:{})".format(len(proxys)))
    return proxys

  def _get_proxy(self,html,country):
    """ Parse the raw html into proxy list
    Args:
                html: web html string
                country: filter proxy by country name
    Return:
                A list consists of proxy-port and contry
                example:
                ['192.168.45.22:80,China',
                '92.28.45.22:80,HONG KONG',
                '52.40.56.35,United States'
                ...]
    """
    proxys1page = []
    sels = Selector(text=html)
    for index,sel in enumerate(sels.xpath("//div[contains(@class,'proxy-list')]/table/tr")):
      if index>=2:   # ignore table head and other stuff
        if country:
          proxy_temp = "{}:{},{}".format(
              sel.xpath('td[2]').re(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')[0],
              str(int(sel.xpath('td[3]').re(r"dep\('(.+)'\)")[0], 16)),
              sel.xpath('td[5]/text()').extract()[0]
              )
          if self.reverse:
            proxy_info = proxy_temp.split(',')[0] if proxy_temp.split(',')[1]!=country else None 
          else:
            proxy_info = proxy_temp.split(',')[0] if proxy_temp.split(',')[1]==country else None 
        else:
          proxy_info = "{}:{}".format(
                sel.xpath('td[2]').re(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')[0],
                str(int(sel.xpath('td[3]').re(r"dep\('(.+)'\)")[0], 16))
                )
        if proxy_info:
          proxys1page.append(proxy_info) 
    return proxys1page

  def get_html(self,url):
    try:
      r = requests.get(url,timeout=15)
      html = r.text
      return html
    except:
      pass

  def getproxy_multi_sources(self):
    ip0 = self.get_from_local()
    ip = self.getherproxy_req()
    ip1 = self.fetch_kxdaili()
    ip2 = self.fetch_yaoyaodaili()
    ip3 = self.fetch_66ip()
    ip4 = self.fetch_xici()
    ip5 = self.fetch_swei360()
    ip6 = self.fetch_mimiip()

    self.proxy_list = list(set(ip0+ip+ip1+ip2+ip3+ip4+ip5+ip6))

  def get_from_local(self):
    # didsoft proxy from local files
    proxys=[]
    try:
      with open("IPs.txt") as f:
        for line in f:
          if line.strip("\n"):
            proxys.append(line.split("#")[0])
    except:
      pass
    logger.info("Finish local")
    return proxys

  def fetch_kxdaili(self):
    #kxdaili,获取可用
    startUrl = 'http://www.kxdaili.com/ipList/'     #地址随时可能变动需要添加处理机制
    proxys = []
    for i in range(1,11):
      try:
        url = startUrl+str(i)+'.html'
        html = etree.HTML(self.get_html(url))
        trs = html.xpath('//*[@id="nav_btn01"]/div[5]/table/tbody/tr')
        for line in range(len(trs)):
          td_speed = trs[line].xpath('td[5]/text()')[0].split('.')[0]
          if int(td_speed)<3:
            td_ip = trs[line].xpath('td[1]/text()')[0]
            td_port = trs[line].xpath('td[2]/text()')[0]
            ip = td_ip+':'+str(td_port)
            proxys.append(ip)
      except:
        pass
    logger.info("Finished kxdaili(length:{})".format(len(proxys)))
    return proxys

  def fetch_yaoyaodaili(self):
    #这个瑶瑶代理可用的IP太少!!!  -全部高匿
    startUrl = 'http://www.httpsdaili.com/free.asp?page='
    proxys = []
    for i in range(1,8):
      url = startUrl+str(i)
      try:
        html = etree.HTML(self.get_html(url))
        trs = html.xpath('//*[@id="list"]/table/tbody/tr')
        for line in range(len(trs)):
          td_speed = trs[line].xpath('td[6]/text()')[0]
          td_ip = trs[line].xpath('td[1]/text()')[0]
          td_port = trs[line].xpath('td[2]/text()')[0]
          ip = td_ip+':'+td_port
          proxys.append(ip)
      except:
        pass
    logger.info("Finished yaoyaodaili(length:{})".format(len(proxys)))
    return proxys

  def fetch_xici(self):
    #获取西刺速度小于5秒的HTTPS代理 -get elite
    startUrl = 'http://www.xicidaili.com/wn/1'
    proxys = []
    try:
      html = etree.HTML(self.get_html(startUrl))
      tables = html.xpath('//table[@id="ip_list"]')
      if tables:
        trs = tables[0].xpath('tr')
        for line in trs[1:]:
          td_level = line.xpath('td[5]/text()')[0].strip()
          if "高匿" in td_level:
            td_speed = line.xpath('td[7]/div/@title')[0].strip()[:-1]
            if float(td_speed) < 5:
              td_ip = line.xpath('td[2]/text()')[0].strip()
              td_port = line.xpath('td[3]/text()')[0].strip()
              ip = td_ip +':'+td_port
              proxys.append(ip)
    except:
      pass
    logger.info("Finished xici daili(length:{})".format(len(proxys)))
    return proxys

  def fetch_nianshao(self):
    #年少代理 -全部高匿
    startUrl = 'http://www.nianshao.me/?stype=2&page='
    proxys = []
    for i in range(1,25):
      url = startUrl+str(i)
      try:
        html = etree.HTML(self.get_html(url))
        trs = html.xpath('//tr')
        for line in trs[1:]:
          td_speed = line.xpath('td[6]/div/div/@style')[0].strip()[6:8]
          if int(td_speed)>=70:  # above 70%
            td_ip = line.xpath('td[1]/text()')[0].strip()
            td_port = line.xpath('td[2]/text()')[0].strip()
            ip = td_ip +":"+td_port
            proxys.append(ip)
      except:
        pass
    logger.info("Finished nianshao(length:{})".format(len(proxys)))
    return proxys

  def fetch_swei360(self):
    #360代理IPHTTPS高匿部分
    startUrl = 'http://www.swei360.com/free/?page='
    proxys = []
    for i in range(1,8):
      url = startUrl+str(i)
      try:
        html = etree.HTML(self.get_html(url))
        trs = html.xpath('//tr')
        for line in trs[1:]:
          td_hide = line.xpath('td[3]/text()')[0].strip()
          if '高匿' in td_hide:
            td_speed = line.xpath('td[6]/text()')[0].strip()[:-1]
            if int(td_speed)<=5:
              td_ip = line.xpath('td[1]/text()')[0].strip()
              td_port = line.xpath('td[2]/text()')[0].strip()
              ip = td_ip +":"+td_port
              proxys.append(ip)
      except:
        pass
    logger.info("Finished swei360(length:{})".format(len(proxys)))
    return proxys


  def fetch_mimiip(self):
    #提取秘密代理IP前4页的代理
    startUrl = 'http://www.mimiip.com/gngao/'
    proxys = []
    for i in range(1,5):
      url = startUrl+str(i)
      try:
        html = etree.HTML(self.get_html(url))
        trs = html.xpath('//tr')
        for line in trs[1:]:
          td_speed = line.xpath('td[6]/div/@style')[0].strip()[6:-2]
          if int(td_speed)>=70:
              td_ip = line.xpath('td[1]/text()')[0].strip()
              td_port = line.xpath('td[2]/text()')[0].strip()
              ip = td_ip+":"+td_port
              proxys.append(ip)
      except:
        pass
    logger.info("Finnished mimiip(length:{})".format(len(proxys)))
    return proxys

  def fetch_66ip(self):
    #安小莫匿名IP提取api,提取最大800个
    startUrl = 'http://www.66ip.cn/nmtq.php?getnum=800&isp=0&anonymoustype=3&start=&ports=&export=&ipaddress=&area=1&proxytype=1&api=66ip'
    try:
      soup = BeautifulSoup(self.get_html(startUrl),"lxml")
      body = soup.body.find_all(text=re.compile('\d+\.\d+\.\d+\.\d+:\d+'))
      body = map(lambda x:x.strip(),body)
      logger.info("Finished 66ip")

      return list(body)
    except:
      logger.info("Finished 66ip(length:0)")
      return []

  def proxy_checker2(self, proxy):
    """ test using requests"""
    test_url = self.checkurl 
    #check_string = proxy.split(":")[0] 
    success = {}
    for times in range(self.checknum):
      try:
        logger.debug("Request :{} using proxy:{}".format(test_url,"http://"+proxy))
        r = requests.get(test_url, proxies = {'http': 'http://'+proxy,'https':'http://'+proxy}, timeout = self.timeout)
        if r.status_code == 200:      # and (check_string in r.text):
          success[proxy]=success.setdefault(proxy,0) + 1
          logger.debug("Successful(+{}/{}) ip:{}".format(success[proxy],self.checknum,proxy))
          if success[proxy]/self.checknum>= self.checkthreshold:
            self.passproxy.add(proxy) 
      except Exception as e:
        logger.debug("Bad proxy ip: {}".format(proxy))
        pass


if __name__ == '__main__':
    """ crawl proxy without stop, but rests certain seconds after every time
    """
    args = parse_args()
    logger = log(args)

    import yaml
    configuration_file = "proxypool_config.yml"
    with open(configuration_file) as f:
      DB_CFG = yaml.load(f)

    q = Queue()
    num_worker_threads = 100
    Threadpool = []
    while True:
      #logger.info("starting...")
      findProxy = find_http_proxy(parse_args())
      start = time.time()
      findProxy.getproxy_multi_sources()
      #print(len(findProxy.proxy_list))
      #findProxy.getherproxy_req()

      def saveproxy():
        try:
          if DB_CFG.get('mongo_db') and "hosts" in DB_CFG.get('mongo_db'):
            client = pymongo.MongoClient(DB_CFG['mongo_db']['hosts'])
        except:
          logger.error("Wrong configuration,Please check database config file")
          raise

        with client:
          db = client[DB_CFG['mongo_db']['proxy_database']]
          # remove old collections, create new
          db[map_checkurl_to_collection_name_and_logfile(args)[0]].drop()
          collection = db[map_checkurl_to_collection_name_and_logfile(args)[0]] 
          try:
            if findProxy.passproxy:
              templist = [{"_id":proxy} for proxy in findProxy.passproxy]
              collection.insert_many(templist)
              #logger.info("\n".join(findProxy.passproxy))
            else:
              templist = [{"_id":proxy} for proxy in findProxy.proxy_list]
              collection.insert_many(templist)
              #logger.info("\n".join(findProxy.passproxy))
          except:
            pass

      def worker():
        while True:     
          proxy = q.get()
          check_proxy(proxy)
          q.task_done()

      def check_proxy(proxy):
        findProxy.proxy_checker2(proxy)

      if not Threadpool:
        for i in range(num_worker_threads):
          t = threading.Thread(target = worker)
          t.daemon = True
          Threadpool.append(t)
          t.start() 

      for proxy in findProxy.proxy_list:
        q.put(proxy)

      q.join()
      saveproxy()

      logger.info("Length of successful proxy is %d" % len(findProxy.passproxy))
      logger.info("Entire job took: %s" % (time.time()-start))
      time.sleep(300)
