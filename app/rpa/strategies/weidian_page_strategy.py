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

    @property
    def page(self):
        return ''

    def open_order_page(self, request: PlaceOrderRequest, browser_pool=None) -> Dict[str, Any]:
        """导航到下单页面"""
        if not hasattr(self, 'tabs'):
            self.tabs = {}
        # 使用浏览器池或默认页面
        if browser_pool and hasattr(browser_pool, 'get_browser_instance'):
            browser_instance = browser_pool.get_browser_instance()
            if browser_instance and hasattr(browser_instance, 'page') and browser_instance.page:
                print(f"使用浏览器池中的实例 {browser_instance.instance_id} 打开订单页面")
                tab = browser_instance.page.new_tab(request.open_url)
                    
                # 保存实例引用以便后续操作
                self.tabs[request.order_id] = {'tab': tab, 'browser_instance': browser_instance}
                print("###### 发送短信：2、使用浏览器池打开站点成功：" + request.open_url)
                return {
                    'status': 'success',
                    'msg': '使用浏览器池页面访问成功',
                    'browser_instance_id': browser_instance.instance_id
                }
        
        # 回退到原有实现
        print("浏览器池不可用，使用默认页面")
            
        tab = self.page.new_tab(request.open_url)
            
        self.tabs[request.order_id] = {'tab': tab, 'browser_instance': None}
        print("###### 发送短信：2、打开站点成功：" + request.open_url)
        print(f"###### 发送短信：2、打开站点成功，代理信息: 已在页面初始化时设置")

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
        tab_data = self.tabs.get(order_number)
        if tab_data:
            return tab_data.get('tab')
        return None

    def fill_phone_number(self, request: PlaceOrderRequest, browser_pool=None) -> Dict[str, Any]:
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


    def get_verification_code(self, request: PlaceOrderRequest, browser_pool=None) -> Dict[str, Any]:
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

    def submit_order(self, request: PlaceOrderRequest, browser_pool=None) -> Dict[str, Any]:
        """提交订单，基于订单号的tab"""
        tab_data = self.tabs.get(request.order_id)
        if not tab_data or not tab_data.get('tab'):
            raise Exception(f"Tab not found for order: {request.order_id}")
            
        tab = tab_data['tab']
        browser_instance = tab_data.get('browser_instance')
        
        # 原有实现代码，保持不变
        self.success = True
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
