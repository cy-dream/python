import re
import time
import datetime
#from wxpy import *
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr
import smtplib
import pymongo
'''
获取上一次时间
'''

def fetch():
	with (open('../proxy/fetch_ip.log', 'r')) as fr:
		index = 0
		content = fr.read().split('\n')
		time_list = []
		for x in reversed(content):
			if index < 500:
				#print(x)
				if re.match('.+Entire job took', x):
					ti = re.search(r'(\d{1,2})\s\w+\s\d{4}\s\d{2}:\d{2}:\d{2}', x)
					#print(x)
					time_before = string_toTimestamp(ti.group(0))
					#print(time_before)
					time_list.append(time_before)
			index += 1
	return time_list


'''
当前时间与最后一次更新时间的比较
'''
def compare_time(time_before):
	time_now = time.time()
	time_difference = time_now - time_before

	if time_difference > 1200:
		#print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
		send_email()
		
	#else:
		#print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
		#print('出错了')
		#send_email()

'''
时间转换
'''
def string_toTimestamp(strTime):
	#把字符串转成时间戳形式
	localtime=time.strptime(strTime,'%d %b %Y %H:%M:%S')
	#从时间数据结构转换成时间戳
	time_cast = time.mktime(localtime)
	return time_cast

def send_email():
	today = datetime.datetime(year=datetime.date.today().year,month=datetime.date.today().month,day=datetime.date.today().day)
	one_day = datetime.timedelta(days=1)

	# Sender's Email Account
	smtp_server = 'smtp.gmail.com'
	from_addr = 'li18713823671@gmail.com'
	password = '******'

	# Receiver's Email Account
	to_addr = ['18713823671@163.com']
	#to_addr = ['jerry.an@wehome.io','wenhang@wehome.io','roc@wehome.io','cuiwei@wehome.io','lilychen@wehome.io','starry@wehome.io']

	# Email Msg Content
	client = pymongo.MongoClient("localhost")
	with client:
		msg = MIMEText("<h3 style='text-align:center'>Internal Server Error</h3> \n{}".format('hi,Administrator,please fix me'),'html', 'utf-8')
		msg['Subject'] = Header('Internal Server Error','utf-8').encode()
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


def _format_addr(s):
	name, addr = parseaddr(s)
	return formataddr((Header(name,'utf-8').encode(), addr))



#while True:
#		time_list = feach()
#		compare_time(time_list[0])
#		time.sleep(600)
time_list = fetch()
if len(time_list) != 0:
	compare_time(time_list[0])

