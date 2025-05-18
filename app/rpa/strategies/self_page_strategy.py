from typing import Dict, Any, Optional
from DrissionPage import ChromiumPage, ChromiumOptions
import time

# 将 PlaceOrderRequest 的导入移到类内部
from app.rpa.base import SupplierStrategy
from app.rpa.request import PlaceOrderRequest

class SelfPageStrategy(SupplierStrategy):
    """基于自营的供应商策略实现基类"""

    def __init__(self):
        self._page = None
        self.sms_code = "123456"
        self.response_data = None
        self.request_data = None

    @property
    def page(self):
        if self._page is None:
            co = ChromiumOptions().set_paths(browser_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
            co.headless(False)
            self._page = ChromiumPage(co)
        return self._page

    def open_order_page(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """导航到下单页面"""

        # co = ChromiumOptions().set_paths(browser_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        # # 1、设置无头模式：

        # # 2、设置无痕模式：co.incognito(True)
        # # 3、设置访客模式：co.set_argument('--guest')
        # # 4、设置请求头user-agent：co.set_user_agent()
        # # 5、设置指定端口号：co.set_local_port(7890)
        # # 6、设置代理：co.set_proxy('http://localhost:1080')
        # self.page = ChromiumPage(co)
        if not hasattr(self, 'tabs'):
            self.tabs = {}
        tab = self.page.new_tab('https://xyy.jxschot.com/mobile-template/index.html?goodsCode=WDDX205G')
        self.tabs[request.order_id] = tab
        # 请求回调函数
        return {
            'status': 'success',
            'msg': '登录成功'
        }

    def get_order_tab(self, order_number):
        """
        获取已打开的订单 tab
        :param order_number: 订单编号
        :return: Tab 实例或 None
        """
        return self.tabs.get(order_number)

    def fill_phone_number(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """填写手机号，基于订单号的tab"""
        print(f"Filling phone number: {request.phone}")
        tab = self.get_order_tab(request.order_id)
        if not tab:
            raise Exception(f"Tab not found for order: {request.order_id}")

        ele = tab.ele('#phone')
        if ele:
            ele.clear()  # 清空原有内容
            ele.input(request.phone)
            return {
                'status': 'success',
            }
        else:
            raise Exception("Phone element not found")

    def get_verification_code(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """获取验证码（通过监听网络请求），基于订单号的tab"""
        tab = self.get_order_tab(request.order_id)
        if not tab:
            raise Exception(f"Tab not found for order: {request.order_id}")

        tab.listen.start('/getSms')  # 启动监听器
        print("### 3、执行发送短信操作")
        # 点击获取验证码按钮
        verify_code_btn = tab.ele('#get_verify_code')
        if verify_code_btn:
            verify_code_btn.click()
        else:
            raise Exception("### 3、获取验证码按钮未找到")
        # 等待并捕获短信请求的响应
        try:
            res = tab.listen.wait(timeout=10)  # 等待最多10秒
            if res and res.response and res.response.body:
                # 这里需要根据实际响应格式提取验证码
                # 假设响应中包含code字段
                self.request_data = res.request.postData
                self.response_data = res.response.body
            else:
                print("### 3、获取验证码接口返回失败")
                self.sms_code = ""  # 默认验证码
        except Exception as e:
            print(f"3、Error capturing SMS code: {e}")
            raise Exception(f"GET Verify code Error：{request.order_id}")
        return {
            'code': 200,
            'msg': 'success',
            'supplierOrderNo': self.request_data.get("externalOrderNo"),
            'requestData': self.request_data,
            'responseData': self.response_data
        }

    def submit_order(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """提交订单，基于订单号的tab"""
        tab = self.get_order_tab(request.order_id)
        if not tab:
            raise Exception(f"Tab not found for order: {request.order_id}")

        print(f"Submitting order with code: {request.sms_code}")
        tab.listen.start('/submitOrder')  # 启动监听器
        # 填写验证码
        code_input = tab.ele('#smsNum')
        if code_input:
            code_input.clear()
            code_input.input(request.sms_code)
        else:
            raise Exception("Verify code input not found")

        # 提交订单
        # submit_btn = tab.ele('#submit-btn')
        #tab.run_js(''' var btn = document.querySelector("#page_container #submit"); var tapEvent = new Event('tap', {bubbles: true, cancelable: true}); btn.dispatchEvent(tapEvent); ''')
        tab.run_js('CT.formSubmit()')

        try:
            res = tab.listen.wait(timeout=10)  # 等待最多10秒
            if res and res.response and res.response.body:
                # 这里需要根据实际响应格式提取验证码
                # 假设响应中包含code字段
                self.request_data = res.request.postData
                self.response_data = res.response.body
            else:
                print("### 3、获取验证码接口返回失败")
                self.sms_code = ""  # 默认验证码
        except Exception as e:
            print(f"3、Error capturing SMS code: {e}")
            tab.close()
            # 先检查是否存在该订单号的 tab
            if request.order_id in self.tabs:
                del self.tabs[request.order_id]  # 删除指定 key
                # 或者使用 pop 方法（推荐用于安全删除）
                # self.tabs.pop(request.order_id, None)
            raise Exception(f"GET Verify code Error：{request.order_id}")
        tab.close()
        # 先检查是否存在该订单号的 tab
        if request.order_id in self.tabs:
            del self.tabs[request.order_id]  # 删除指定 key
            # 或者使用 pop 方法（推荐用于安全删除）
            # self.tabs.pop(request.order_id, None)

        return {
            'code': 200,
            'msg': 'success',
            'supplierOrderNo': self.request_data.get("externalOrderNo"),
            'requestData': self.request_data,
            'responseData': self.response_data
        }
