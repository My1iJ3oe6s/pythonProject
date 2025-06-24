from app.rpa.request import PlaceOrderRequest
from app.rpa.strategies.self_page_strategy import SelfPageStrategy
from app.rpa.strategies.hubei_page_strategy import HuBeiPageStrategy
from app.rpa.base import RPABaseService
from fastapi import HTTPException
from typing import Optional

SUPPLIER_STRATEGIES = {
    "self": SelfPageStrategy(),  # 添加自营的策略
    "hubei-dianxin": HuBeiPageStrategy()
}

def get_supplier_strategy(supplier_code: str, order_id: Optional[str] = None) -> RPABaseService:
    """获取对应的供应商策略实例，优先复用已有会话"""
    strategy = SUPPLIER_STRATEGIES.get(supplier_code.lower())
    if not strategy:
        raise HTTPException(status_code=400, detail=f"Unsupported supplier: {supplier_code}")
    rpa_service = RPABaseService(strategy)
    return rpa_service

class OrderService:
    @staticmethod
    def get_verification_code(request: PlaceOrderRequest):
        """获取验证码接口"""
        rpa_service = get_supplier_strategy(request.supplier_code, request.order_id)
        print("###### 2、发送验证码：获取供应商策略实例：" + request.supplier_code)
        result = rpa_service.get_verification_code(request)
        print("###### RPA发送验证码：返回结果：" + str(result))
        return result

    @staticmethod
    def execute_place_order(request: PlaceOrderRequest):
        """下单接口"""
        rpa_service = get_supplier_strategy(request.supplier_code, request.order_id)
        result = rpa_service.execute_place_order(request)
        return result