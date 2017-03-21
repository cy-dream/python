import re
import time
import datetime
import itchat

'''
获取上一次时间
'''

def fetch():
	with (open('fetch_ip.log', 'r')) as fr:
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
		send_wechat()
		
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


def send_wechat():
	it = itchat.search_chatrooms('好好学习，玩你妹')
	username = it[0].get('UserName')
	itchat.send('Hello 孙小胖, 代理进程停止了, 赶紧去查看。', toUserName=username)


itchat.auto_login(enableCmdQR=2,hotReload=True)
while True:
		time_list = feach()
		compare_time(time_list[0])
		time.sleep(600)
#time_list = fetch()
#if len(time_list) != 0:
#	compare_time(time_list[0])

