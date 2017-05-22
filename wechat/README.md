# wechat
请求说明
>Http请求说明：POST
>http://172.31.2.118:80/message

参数说明


```
{
   "touser": [email, email2, email3],
   "msg": "text",
}

```


 参数 | 必须 | 说明
---|--- |---
touser  | 否  |成员email，参数为list，特殊情况：指定为空，则向关注该企业应用的全部成员发送
msg     | 是  |发送消息内容

- Note：如果touser为空，默认给关注企业应用的全部成员发送

使用方式

```
url = ‘http://172.31.2.118:80/message’
values = {'touser' : [‘email’, ‘email2’],
          'msg' : 'Mongodb'
  }

headers = {'content-type': 'application/json'}

r = requests.post(url, data=json.dumps(values), headers=headers)

```

返回结果

```
{
   "errcode": 0,
   "errmsg": "ok",
   "invaliduser": [‘email’, ‘email2’] //不存在的成员列表
}

```






