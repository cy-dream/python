import re
import json
from datetime import datetime, date
import ast
import pymongo
def get_data():
	with open('scrapy_Zillow_1490058302.log', 'r') as fr:
		content = fr.read()
		cons = content.split('\n')
		count = len(cons) - 50
		string = ''
		for x in cons:
			if count < len(cons):
				string += cons[count]
			count+=1
		
		dicts = re.search('{.*}', string).group(0)

		times = re.findall('datetime.datetime.+?\)', dicts)
		dicts_replace = re.sub('datetime.datetime.+?\)', '123', dicts)
		dicts_replace = dicts_replace.replace('.','_')
		time_list = convert_time(times)		
		
		str_dict = ast.literal_eval(dicts_replace)
		#print(str_dict)
		str_dict['finish_time'] = time_list[0]
		str_dict['start_time'] = time_list[1]
		str_dict['time'] = datetime.now()
		print(str_dict['finish_time'])
		print(str_dict['start_time'])
		print(str_dict['time'])
		save_data(str_dict)


def convert_time(times):
	time_list = []
	for x in times:
		st = re.search('\d.+\d', x).group(0).split(',')
		time1 = datetime(int(st[0]), int(st[1]), int(st[2]), int(st[3]), int(st[4]), int(st[5]), int(st[6]))
		time_list.append(time1)
	return time_list

def save_data(str_dict):
	connection = pymongo.MongoClient('localhost')
	with connection:
		db = connection['Expection']
		zillow = db['Zillow']
		zillow.insert(str_dict)

get_data()