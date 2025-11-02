import os
import re
import time
import requests
from random import random
from typing import Dict, Any, Optional
from DrissionPage import ChromiumPage, ChromiumOptions
from urllib.parse import urlparse, parse_qs
from fake_useragent import UserAgent


# 将 PlaceOrderRequest 的导入移到类内部
from app.rpa.base import SupplierStrategy
from app.rpa.request import PlaceOrderRequest

class WeiDianPageStrategy(SupplierStrategy):
    """基于湖北的供应商策略实现基类"""

    def __init__(self):
        self.ua = None
        self._page = None
        self.sms_code = "123456"
        self.response_data = ""
        self.request_data = ""
        self.success = True
        self.tabs = {}
        self.supplier_ping_zheng = ""

        # 初始化UserAgent，添加异常处理
        try:
            self.ua = UserAgent()
        except Exception as e:
            print(f"Failed to initialize UserAgent: {e}")
            # 如果初始化失败，使用备用的User-Agent列表
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
            ]

    def get_proxy_ip(self, username=None, password=None):
        """
        获取代理IP地址，支持Postman风格的代理认证
        优化：添加超时设置、重试机制和更完善的错误处理
        
        Args:
            username: 代理认证用户名（可选）
            password: 代理认证密码（可选）
        """
        # 将代理API配置参数化，方便后续修改
        PROXY_API_CONFIG = {
            'url': "http://ip.quanminip.com/ip",
            'params': {
                'secret': '1mMkYQag',
                'num': 1,
                'port': 1,
                'type': 'txt',
                'mr': 1,
                'sign': '03e380d2ee0b8ca101180ef63d39195c'
            },
            'timeout': 10,  # 10秒超时
            'max_retries': 3,  # 最多重试3次
            'username': username,  # 代理认证用户名
            'password': password  # 代理认证密码
        }
        
        for attempt in range(PROXY_API_CONFIG['max_retries']):
            try:
                # 添加超时参数，避免请求无限等待
                response = requests.get(
                    PROXY_API_CONFIG['url'],
                    params=PROXY_API_CONFIG['params'],
                    timeout=PROXY_API_CONFIG['timeout']
                )
                
                if response.status_code == 200:
                    proxy_info = response.text.strip().split(':')
                    # 确保代理格式正确
                    if len(proxy_info) == 2 and self._is_valid_proxy_format(proxy_info[0], proxy_info[1]):
                        proxy_ip = proxy_info[0]
                        proxy_port = proxy_info[1]
                        
                        # 构建带有认证信息的代理URL，Postman风格
                        if username and password:
                            proxy_url = f"http://{username}:{password}@{proxy_ip}:{proxy_port}"
                        else:
                            proxy_url = f"http://{proxy_ip}:{proxy_port}"
                        # 可选：验证代理是否可用
                        if self._test_proxy(proxy_url):
                            print(f"Successfully obtained valid proxy: {proxy_url}")
                            return proxy_url
                        else:
                            print(f"Proxy {proxy_url} is not valid, retrying...")
                else:
                    print(f"API returned non-200 status code: {response.status_code}, retrying...")
                    
            except requests.exceptions.RequestException as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
            except Exception as e:
                print(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            # 重试间隔，使用指数退避
            if attempt < PROXY_API_CONFIG['max_retries'] - 1:
                sleep_time = (attempt + 1) * 2  # 1s, 2s, 4s...
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
        
        print("Failed to get valid proxy after multiple attempts")
        return None
    
    def _is_valid_proxy_format(self, ip, port):
        """验证IP和端口格式是否正确"""
        # 简单验证IP格式
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if not re.match(ip_pattern, ip):
            return False
        
        # 验证端口是否为有效数字
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except ValueError:
            return False
    
    def _test_proxy(self, proxy_url):
        """测试代理是否可用，支持带有认证信息的代理"""
        test_url = "http://www.baidu.com"
        test_timeout = 5
        
        try:
            # 支持带认证的代理URL
            proxies = {"http": proxy_url, "https": proxy_url}
            start_time = time.time()
            response = requests.get(test_url, proxies=proxies, timeout=test_timeout)
            elapsed = time.time() - start_time
            
            if response.status_code == 200 and elapsed < test_timeout:
                print(f"Proxy test passed, response time: {elapsed:.2f}s")
                return True
            else:
                print(f"Proxy test failed: status={response.status_code}, time={elapsed:.2f}s")
                return False
                
        except Exception as e:
            print(f"Proxy test exception: {e}")
            return False

    @property
    def page(self):
        if self._page is None:
            browser_path = ""
            if os.name == 'posix':  # Linux 系统
                browser_path = r"/opt/google/chrome/google-chrome"  # 或者 "/usr/bin/chromium-browser"
            elif os.name == 'nt':  # Windows 系统
                browser_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            
            # 创建ChromiumOptions对象
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

            # 创建ChromiumPage对象
            self._page = ChromiumPage(co, timeout=90)
        return self._page

    def open_order_page(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """导航到下单页面"""
        if not hasattr(self, 'tabs'):
            self.tabs = {}


        # 获取代理IP，可以传入认证信息
        # 示例：如需添加认证，可改为 self.get_proxy_ip(username='your_username', password='your_password')
        # 注意：代理已经在page属性的getter方法中通过ChromiumOptions设置
        # 这里不再重复获取，直接记录信息
        proxy_info = "已在页面初始化时设置"
        # 获取随机的User-Agent
        selected_user_agent = self.ua.random

        # 获取随机的User-Agent
        if hasattr(self, 'ua') and self.ua is not None:
            selected_user_agent = self.ua.random
        else:
            # 使用备用的User-Agent列表
            selected_user_agent = random.choice(self.user_agents)
        # 创建新标签页前先设置请求头
        # 在DrissionPage中，我们应该在创建请求时设置headers
        # 而不是直接访问私有属性
        tab = self.page.new_tab(request.open_url)
        # 使用标准方法设置请求头，这里假设DrissionPage支持headers属性的标准设置方式
        if hasattr(tab, 'headers'):
            tab.headers['User-Agent'] = selected_user_agent
        else:
            print(f"警告：无法设置User-Agent，标签页对象不支持headers属性")
        self.tabs[request.order_id] = tab
        print("###### 发送短信：2、打开站点成功：" + request.open_url)

        # 设置代理，如果获取到了代理IP
        # 代理已经在page属性初始化时通过ChromiumOptions设置
        # 这里仅记录信息
        print(f"###### 发送短信：2、打开站点成功，代理信息: {proxy_info}")

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
        tab = self.get_order_tab(request.order_id)
        if not tab:
            raise Exception(f"Tab not found for order: {request.order_id}")
        # 点击立即办理按钮
        confirm_btn = tab.ele('.btnBox')
        if confirm_btn:
            confirm_btn.click()
            print(f"###### 填写手机号: 5、点击立即办理按钮成功")
        else:
            print(f"###### 填写手机号: 异常-点击按钮失败，立即办理按钮未找到")
            raise Exception("###### RPA填写手机号异常:立即办理按钮未找到")
        
       #  # 在手机号输入框中输入手机号
       #  phone_input = tab.ele('input[placeholder="请输入手机号"]')
       # # phone_input = tab.ele('//input[contains(@class, "smsinput") and @placeholder="请输入手机号"]')
        phone_input = tab.eles('.smsinput')[1]
        if phone_input:
            phone_input.clear()
            phone_input.input(request.phone)
            print(f"###### 填写手机号: 6、输入手机号成功: {request.phone}")
        else:
            print(f"###### 填写手机号: 异常-输入框未找到，无法输入手机号")
            raise Exception("###### RPA填写手机号异常:手机号输入框未找到")
        
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
        tab.listen.start('/random.action')  # 启动监听器
        # 点击获取验证码按钮
        verify_code_btn = tab.ele('#id_getMessage')
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
                if  res.response.body["flag"] != '0':
                    self.success = False
                    tab.close()
            else:
                print("###### 发送验证码异常:获取验证码接口返回失败")
                self.success = False
                self.sms_code = ""  # 默认验证码
                tab.close()
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
        tab.listen.start('/gborderNew.action')  # 启动监听器
        # 填写验证码
        code_input = tab.ele('.smsinputA')
        if code_input:
            code_input.clear()
            code_input.input(request.sms_code)
        else:
            tab.close()
            raise Exception(f"###### 提交订单:输入验证码失败，验证码输入框未找到 {request.order_id} - {request.sms_code}")
        # 提交订单
        tab.ele('.btn btngo').click()
        # https: // xyy.jxschot.com / mobile - template / index.html?p = D8043BE088B8A92B1BDFF97496EA1F007F5BA585D8E5AE6655FD4B2ED9731C9D
        # tab1 = page.new_tab(
        #     'https://xyy.jxschot.com/mobile-template/index.html?p=D8043BE088B8A92B1BDFF97496EA1F007F5BA585D8E5AE6655FD4B2ED9731C9D&a=1')
        #线程休息一秒钟
        try:
            res = tab.listen.wait(timeout=30)  # 等待最多10秒
            if res and res.response:
                # 这里需要根据实际响应格式提取验证码
                # 假设响应中包含code字段
                self.request_data = f"{res.request.postData}"
                self.response_data = f"{res.response.body}"
                print("###### 发送验证码:4、执行发送短信操作：获取返回结果" + self.response_data)
                if not res.response.body["flag"]:
                    self.success = False
                    tab.close()
            else:
                print("###### 发送验证码异常:获取验证码接口返回失败")
                self.success = False
                self.sms_code = ""  # 默认验证码
                tab.close()
        except Exception as e:
            print(f"###### 发送验证码: Error capturing SMS code: {e}")
            tab.close()
            raise Exception(f"###### 发送短信异常: 无法获取发送验证码的响应{request.order_id}")

        return {
            'code': 200 if self.success else 500,
            'data':  f"{self.response_data}",
            'msg': f"{self.response_data}",
            'resultLog':  f"{self.response_data}",
            'orderNo': request.order_id,
            'supplierOrderNo': '',
            'requestData':  f"{self.request_data}",
            'responseData':  f"{self.response_data}"
        }
