import os
import re
import ast
from datetime import datetime, date, time
import pymongo

#得到目录下所有文件
def get_files():
	file_list = os.listdir('logs')
	for x in file_list:
		if 'scrapy' not in x:
			file_list.remove(x)
	return file_list

def get_data(file_list):
	for index,x in enumerate(file_list):
		with open('./logs/' + x, 'r') as fr:
			content = fr.read()
			cons = content.split('\n')
			count = len(cons) - 50
			if count >= 0:
				string = ''
				for c in cons:
					if count < len(cons):
						string += cons[count]
					count+=1
				dicts = re.search('{.*}', string)
				if dicts is not None:
					dicts = dicts.group(0)
					times = re.findall('datetime.datetime.+?\)', dicts)
					if 2 == len(times):
						str_dict = str_convert_dict(times, dicts)
						save_data(str_dict ,x)

#string convert dict
def str_convert_dict(times, dicts):
	dicts_replace = re.sub('datetime.datetime.+?\)', '123', dicts)
	dicts_replace = dicts_replace.replace('.','_')

	time_list = convert_time(times)		

	str_dict = ast.literal_eval(dicts_replace)
	str_dict['finish_time'] = time_list[0]
	str_dict['start_time'] = time_list[1]

	now_date = date.today()
	now_time = time(0)
	noon_today = datetime.combine(now_date, now_time)
	#print(now_date, now_time, noon_today)
	str_dict['date'] = noon_today
	#print(str_dict['start_time'], str_dict['finish_time'], str_dict['date'])
	return str_dict


def save_data(str_dict, x):
	filenames = re.split(r'[\_\.]', x)
	dbname = filenames[1]
	logtime = filenames[2]
	str_dict['logtime'] = logtime
	connection = pymongo.MongoClient('localhost')
	with connection:
		db = connection['Exception']
		zillow = db[dbname]
		count = zillow.find({'logtime' : logtime}).count()
		if count == 0:
			zillow.insert(str_dict)


#time convert							
def convert_time(times):
	time_list = []
	for x in times:
		st = re.search('\d.+\d', x).group(0).split(',')
		time1 = datetime(int(st[0]), int(st[1]), int(st[2]), int(st[3]), int(st[4]), int(st[5]), int(st[6]))
		time_list.append(time1)
	return time_list

dir_list = get_files()
get_data(dir_list)