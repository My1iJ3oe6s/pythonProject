import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any

from app.rpa.request import PlaceOrderRequest


class SupplierStrategy(ABC):
    """供应商策略接口，每个供应商需要实现的具体操作"""

    @abstractmethod
    def open_order_page(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """导航到下单页面"""
        pass

    @abstractmethod
    def fill_phone_number(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """填写手机号"""
        pass

    @abstractmethod
    def get_verification_code(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """获取验证码"""
        pass

    @abstractmethod
    def submit_order(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """提交订单"""
        pass


class RPABaseService:
    """RPA基础类，提供通用功能"""
    
    def __init__(self, strategy: SupplierStrategy):
        self.strategy = strategy
        # self.page = Page()  # 示例初始化

    def get_verification_code(self, request: PlaceOrderRequest) -> Dict[str, Any]:
        """执行获取验证码流程"""
        try:
            self.strategy.open_order_page(request)
            print(f"123:")
            # 假设这里有一些通用操作
            self.strategy.fill_phone_number(request)
            print(f"1234:")
            # 等待验证码发送
            # 这里可以添加等待逻辑或监听网络请求
            sms_response = self.strategy.get_verification_code(request)
            return {
                'code': sms_response.get('code'),
                'data': sms_response.get('responseData'),
                'msg': sms_response.get('responseData'),
                'resultLog': sms_response.get('responseData'),
                'supplierOrderNo': sms_response.get('supplierOrderId'),  # 实际应该从页面获取
                'orderNo': request.order_id,  # 实际应该从页面获取
                'requestData': sms_response.get('requestData'),
                'responseData': sms_response.get('responseData')
            }
        except Exception as e:
            print("【异常堆栈】", traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'supplier_response': None
            }

    def execute_place_order(self, request :PlaceOrderRequest) -> Dict[str, Any]:
        """执行下单流程"""
        try:
            # self.strategy.open_order_page(request.checkout_url)
            # self.strategy.fill_phone_number(request.phone)
            result = self.strategy.submit_order(request)
            return result
        except Exception as e:
            return {
                'code': 500,
                'error': str(e),
                'supplier_response': ""
            }
