from app import create_app

# 项目启动流程
# pip install -r requirements.txt
# python main.py
# 访问接口地址 http://localhost:5000/search?keyword=你好

# POST /order
# Content-Type: application/json
#
# {
#   "phone": "13800001111",
#   "step": "send_sms"
# }



app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
