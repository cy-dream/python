from flask import Flask, jsonify, request
import requests as req
import json
import yaml
import pymongo


app = Flask(__name__)

with open('wechat_msg.yml') as ya:
  param = yaml.load(ya)
  mongo = param['mongo']

user_information = (mongo['host'], mongo['database'])

class mongo_database():
  def __init__(self, config):
    self.client = None
    self.config = config
  def __enter__(self):
    host, dbName = self.config
    self.client = pymongo.MongoClient(
      host,
      27017
    )
    return self.client
  def __exit__(self, *args):
    self.client.close()


def get_userID(user_email):
  """
    Get the corresponding user_id by user_email
    return "id | id1 | id2", [email, email2, email3]
  """
  usersID = ''
  exist_user_email = set()  
  with mongo_database(config=user_information) as client:
    collection = client[user_information[1]][mongo['collection']]
    cursor = collection.find({'email':{'$in':user_email}})
    for x in cursor:
      usersID += x['userID'] + '|'
      exist_user_email.add(x['email'])
  return usersID, exist_user_email

def send_wechat(params):
  """ wechat invoke interface """
  url="https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token="+get_token()
  values ={
    "touser": params['touser'],
    "msgtype": "text",
    "agentid": param['wechat']['agentid'],
    "text": {
      "content": params['msg']
    },
    "safe":0
  }
  data = json.dumps(values, ensure_ascii=False)
  re = req.post(url, data.encode('utf-8'))
  return re.text


def get_token():
  """ get token """
  url='https://qyapi.weixin.qq.com/cgi-bin/gettoken'
  values = {'corpid' : 'wx5ca89ffbd7dae3cc',
      'corpsecret': param['wechat']['corpsecret'],
  }
  re = req.post(url, params=values)
  data = json.loads(re.text)
  return data["access_token"]


@app.route('/message', methods=['POST'])
def create_message_task():
  """ Service entrance 
      The parameter must contain msg field. else return {'errmsg':'Missing parameters'}
      return { "errcode": 0, "errmsg": "ok", "invaliduser": "user_email_list"}
   """
  params = request.get_json(force=True,silent=True)
  if not params or not 'msg' in params:
    return jsonify({'errmsg':'Missing parameters'}), 400
  user_email = params['touser']
  if user_email:
    usersID, exist_user_email = get_userID(user_email)
  else:
    usersID = '@all'
  not_exist_user_email = list(set(user_email).difference(exist_user_email))
  params['touser'] = usersID
  text = json.loads(send_wechat(params))
  if not_exist_user_email:
    text['invaliduser'] = not_exist_user_email
  return jsonify(text), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0')
