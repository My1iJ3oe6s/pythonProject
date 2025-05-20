from DrissionPage._configs.chromium_options import ChromiumOptions
from DrissionPage._pages.web_page import WebPage
from fastapi import FastAPI, HTTPException
from typing import Dict, Any, Optional
from app.rpa.base import RPABaseService
from app.rpa.request import PlaceOrderRequest
from app.rpa.strategies.hubei_page_strategy import HuBeiPageStrategy
from app.rpa.strategies.self_page_strategy import SelfPageStrategy

app = FastAPI()

# 定义下单请求的数据模型



# 供应商策略工厂
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

@app.post("/api/v1/get-code")
async def get_verification_code(request: PlaceOrderRequest) -> Dict[str, Any]:
    """获取验证码接口"""
    rpa_service = get_supplier_strategy(request.supplier_code, request.order_id)
    result = rpa_service.get_verification_code(request)
    return result

@app.post("/api/v1/place-order")
async def place_order(request: PlaceOrderRequest) -> Dict[str, Any]:
    """下单接口"""
    rpa_service = get_supplier_strategy(request.supplier_code, request.order_id)
    result = rpa_service.execute_place_order(request)
    return result

@app.post("/api/v1/test")
async def test():
    """下单接口"""
    co = ChromiumOptions().set_browser_path("/opt/google/chrome/google-chrome")
    co.headless(True)
    page = WebPage(chromium_options=co)
    page.get('https://www.google.com')
    print(page.title)
    page.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)