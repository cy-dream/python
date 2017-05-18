# /usr/bin/python3
# -*- coding:utf-8

from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr
import smtplib

import pymongo
import datetime


def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name,'utf-8').encode(), addr))

today = datetime.datetime(year=datetime.date.today().year,month=datetime.date.today().month,day=datetime.date.today().day)
one_day = datetime.timedelta(days=1)

# Sender's Email Account
smtp_server = 'smtp.gmail.com'
from_addr = 'yuechao.li@wehome.io'
password = '******'
# Receiver's Email Account
to_addr = ['jerry.an@wehome.io']
#to_addr = ['jerry.an@wehome.io','wenhang@wehome.io','roc@wehome.io','cuiwei@wehome.io','lilychen@wehome.io','starry@wehome.io']

# Email Msg Content
client = pymongo.MongoClient("localhost")
with client:
  
  
  msg = MIMEText("<h3 style='text-align:center'>Craigslist Daily Report </h3> \n{}".format(x),'html', 'utf-8')
  msg['Subject'] = Header('Scraper Daily Report-Craigslist','utf-8').encode()
  msg['From'] = _format_addr('Amazon Server <%s>' % from_addr)
  msg['To'] = _format_addr('Administrator <%s>' % to_addr)

  # Mail Transfer Protocol
  server =smtplib.SMTP(smtp_server,587)   # SMTP 协议默认端口
  server.ehlo()
  server.starttls()
  server.set_debuglevel(1)
  server.login(from_addr,password)
  server.sendmail(from_addr, to_addr, msg.as_string())
  server.quit()
