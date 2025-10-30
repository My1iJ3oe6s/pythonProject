import os
from typing import Dict, Any, Optional
from DrissionPage import ChromiumPage, ChromiumOptions
import time
from urllib.parse import urlparse, parse_qs


# 将 PlaceOrderRequest 的导入移到类内部
from app.rpa.base import SupplierStrategy
from app.rpa.request import PlaceOrderRequest

class HuBeiPageStrategy(SupplierStrategy):
    """基于湖北的供应商策略实现基类"""

    def __init__(self):
        self._page = None
        self.sms_code = "123456"
        self.response_data = ""
        self.request_data = ""
        self.success = True
        self.tabs = {}
        self.supplier_ping_zheng = ""

    @property
    def page(self):
        if self._page is None:
            browser_path = ""
            if os.name == 'posix':  # Linux 系统
                browser_path = r"/opt/google/chrome/google-chrome"  # 或者 "/usr/bin/chromium-browser"
            elif os.name == 'nt':  # Windows 系统
                browser_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            # co = ChromiumOptions().set_browser_path(browser_path=r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            co = ChromiumOptions().set_paths(browser_path=browser_path)
            co.headless(False)
            co.incognito()  # 匿名模式
            co.set_argument('--ignore_https_errors')
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-dev-shm-usage')
            co.set_argument(f"--remote-debugging-port=9222")
            co.set_argument(f"--disable-web-security")
            co.set_argument(f"--allow-running-insecure-content")
            co.set_argument('--ignore-certificate-errors', True)
            co.set_argument('--disk-cache-dir=/path/to/cache')  # 指定磁盘缓存目录
            # 禁用图片资源  主要是为了加快页面加载
            co.set_argument('--blink-settings=imagesEnabled=false')
            co.ignore_certificate_errors()
            self._page = ChromiumPage(co, timeout=90)
        return self._page

    def open_order_page(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """导航到下单页面"""
        if not hasattr(self, 'tabs'):
            self.tabs = {}
        tab = self.page.new_tab(request.open_url)
        self.tabs[request.order_id] = tab
        print("###### 发送短信：2、打开站点成功：" + request.open_url)
        # 请求回调函数
        return {
            'status': 'success',
            'msg': '页面访问成功'
        }

    def get_order_tab(self, order_number):
        """
        获取已打开的订单 tab
        :param order_number: 订单编号
        :return: Tab 实例或 None
        """
        return self.tabs.get(order_number)

    def fill_phone_number(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        return {
            'status': 'success',
        }


    def get_verification_code(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """获取验证码（通过监听网络请求），基于订单号的tab"""
        self.success = True
        tab = self.get_order_tab(request.order_id)
        msg = ""
        if not tab:
            raise Exception(f"Tab not found for order: {request.order_id}")
        print("###### 发送验证码: 3、获取页面窗口成功")
        tab.listen.start('/smsCheck.action')  # 启动监听器
        # 点击获取验证码按钮
        verify_code_btn = tab.ele('#getRandomss')
        if verify_code_btn:
            verify_code_btn.click()
            print("###### 发送验证码: 3、点击发送短信按钮: " + request.order_id)
        else:
            print("###### 发送验证码: 异常-点击按钮失败，获取验证码按钮未找到")
            raise Exception("###### RPA发送验证码异常:获取验证码按钮未找到")
        # 等待并捕获短信请求的响应
        try:
            res = tab.listen.wait(timeout=30)  # 等待最多10秒
            if res and res.response:
                # 这里需要根据实际响应格式提取验证码
                # 假设响应中包含code字段
                self.request_data = f"{res.request.postData}"
                self.response_data = f"{res.response.body}"
                print("###### 发送验证码:4、执行发送短信操作：获取返回结果" + self.response_data)
                if  res.response.body != 0:
                    self.success = False
            else:
                print("###### 发送验证码异常:获取验证码接口返回失败")
                self.success = False
                self.sms_code = ""  # 默认验证码
            send_confire_but = tab.ele('#mb_btn_ok')
            if send_confire_but:
                msg = tab.ele('#mb_msg')
                print("###### 发送验证码: 关闭发送短信后的弹窗,提示信息为：" + msg.text)
                send_confire_but.click()
        except Exception as e:
            print(f"###### 发送验证码: Error capturing SMS code: {e}")
            tab.close()
            raise Exception(f"###### 发送短信异常: 无法获取发送验证码的响应{request.order_id}")
        return {
            'code': 200 if self.success else 500,
            'data':  f"{self.response_data}",
            'msg': msg,
            'resultLog':  f"{self.response_data}",
            'orderNo': request.order_id,
            'supplierOrderNo': '',
            'requestData':  f"{self.request_data}",
            'responseData': f"{self.response_data}"
        }

    def submit_order(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """提交订单，基于订单号的tab"""
        tab = self.get_order_tab(request.order_id)
        if not tab:
            raise Exception(f"###### 提交订单:未找到订单tab页面: {request.order_id}")

        print(f"提价订单: 订单数据为:  {request.order_id} - {request.sms_code}")
        tab.listen.start('/doSure.action')  # 启动监听器
        # 填写验证码
        code_input = tab.ele('#vcode')
        if code_input:
            code_input.clear()
            code_input.input(request.sms_code)
        else:
            raise Exception(f"###### 提交订单:输入验证码失败，验证码输入框未找到 {request.order_id} - {request.sms_code}")
        # 提交订单
        tab.run_js('orderQuery();')
        # https: // xyy.jxschot.com / mobile - template / index.html?p = D8043BE088B8A92B1BDFF97496EA1F007F5BA585D8E5AE6655FD4B2ED9731C9D
        # tab1 = page.new_tab(
        #     'https://xyy.jxschot.com/mobile-template/index.html?p=D8043BE088B8A92B1BDFF97496EA1F007F5BA585D8E5AE6655FD4B2ED9731C9D&a=1')
        #线程休息一秒钟
        time.sleep(1)
        supplier_ping_zheng_new = ""
        for tab in self.page.get_tabs():
            if "xyyOrderNo=" + request.order_id in str(tab.url):
                url = tab.url
                # parsed_url = urlparse(url)
                # # 获取查询参数
                # query_params = parse_qs(parsed_url.query)
                # 提取 p 的值
                # p_value = query_params.get('p', [None])[0]
                supplier_ping_zheng_new = url
                print(f"Submitting order with code: {request.sms_code}")
                self.sms_code = ""  # 默认验证码
                tab.close()
        time.sleep(1)
        if "p=" not in supplier_ping_zheng_new:
            self.success = False
            try:
                res = tab.listen.wait(timeout=10)  # 等待最多10秒
                if res and res.response and res.response.body:
                    # 这里需要根据实际响应格式提取验证码
                    # 假设响应中包含code字段
                    self.request_data = f"{res.request.postData}"
                    self.response_data = f"{res.response.body}"
                    if res.response.body.get("returnCode") != "200":
                        self.success = False
            except Exception as e:
                print(f"3、Error capturing SMS code: {e}")
                # 先检查是否存在该订单号的 tab
                if request.order_id in self.tabs:
                    del self.tabs[request.order_id]  # 删除指定 key
                    # 或者使用 pop 方法（推荐用于安全删除）
                    # self.tabs.pop(request.order_id, None)
                    raise Exception(f"GET Verify code Error：{request.order_id}")
            # tab.close()
            # 先检查是否存在该订单号的 tab
            if request.order_id in self.tabs:
                del self.tabs[request.order_id]  # 删除指定 key
                # 或者使用 pop 方法（推荐用于安全删除）
                # self.tabs.pop(request.order_id, None)
        return {
            'code': 200 if self.success else 500,
            'data':  f"{supplier_ping_zheng_new}" if self.success else f"{self.response_data}",
            'msg': f"{self.response_data}",
            'resultLog':  f"{self.response_data}",
            'orderNo': request.order_id,
            'supplierOrderNo': '',
            'requestData':  f"{self.request_data}",
            'responseData':  f"{self.response_data}"
        }
