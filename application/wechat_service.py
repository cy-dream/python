from flask import Flask, jsonify, request
from .utils.util import *


app = Flask(__name__)

@app.route('/message', methods=['POST'])
def message():
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
    app.run(host='0.0.0.0', debug=True)
