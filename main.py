from application.wechat_service import app
from flask_script import Manager

manager = Manager(app)

app = app

if __name__ == '__main__':
	#manager.run()
	app.run()
