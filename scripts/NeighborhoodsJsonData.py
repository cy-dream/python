import os
import json
import zipfile
import pymongo
import requests
from parsel import Selector


'''
Usage:
  shell command:
    brew install gdal
    ogr2ogr -f "GeoJSON" output.json input.shp
  python run shell gdal:
    os.system('command')
'''

def download():
  # download shape data
  url = 'https://www.zillow.com/howto/api/neighborhood-boundaries.htm'
  response = requests.get(url)
  sel = Selector(text=response.text)
  urls = sel.xpath('//div[@class="zsg-content-component"]/ul/li/a/@href').extract()
  for ur in urls:
    print(ur)
    filename = ur.split('/')[5]
    r = requests.get(ur) 
    with open('./' + filename, "wb") as code:
      code.write(r.content)

def extract_zip():
  # Unpack the zip file
  file_list = os.listdir("./")
  for file in file_list:
    if os.path.splitext(file)[1] == '.zip':
      print(file)
      file_zip = zipfile.ZipFile(file, 'r')
      for file_name in file_zip.namelist():
        file_zip.extract(file_name, file.split('.')[0])
      file_zip.close()
      os.remove(file)

def shp_convert_json():
  # shp convert json
  dir_list = os.listdir('./')
  for di in dir_list:
    di_before = di.split('-')[0]
    if di_before == 'ZillowNeighborhoods':
      print(di)
      os.system('ogr2ogr -f "GeoJSON" ./'+'/'+di+'.json ./'+di+'/'+di+'.shp')
      os.system('rm -rf ' + di)

def save_database():
  # save json data database
  size = 1000
  counter = 0
  client = pymongo.MongoClient('localhost')
  with client:
    collection = client['map']['neighborhoods1']
    bulk = collection.initialize_unordered_bulk_op()
    dirs = os.listdir('./')
    for di in dirs:
      file_type = di.split('.')
      if len(file_type) == 2 and file_type[1] == 'json':
        with open('./' + di, 'r') as f:
          json_data = json.loads(f.read())
          for json_item in json_data['features']:
            counter += 1
            bulk.insert(json_item)
            if counter % size == 0:
              print(counter)
              bulk.execute()
              bulk = collection.initialize_unordered_bulk_op()
    if counter % size != 0:
      bulk.execute()

def delete_josn():
  # delete josn file
  dir_list = os.listdir('./')
  for di in dir_list:
    file_type = di.split('.')
    if len(file_type) == 2 and file_type[1] == 'json':
      os.remove(di)


if __name__ == '__main__':
  download()       # download shape data
  extract_zip()    # Unpack the zip file
  shp_convert_json() # shp convert json
  save_database()   # save json data
  delete_josn()     # delete file
