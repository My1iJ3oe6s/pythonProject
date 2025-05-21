import os
import random  # 导入random模块

from DrissionPage import ChromiumPage, ChromiumOptions
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
    print("###### RPA发送验证码：" + request.order_id + "," + request.phone)
    rpa_service = get_supplier_strategy(request.supplier_code, request.order_id)
    print("###### RPA发送验证码：获取供应商策略实例：" + request.supplier_code)
    result = rpa_service.get_verification_code(request)
    print("###### RPA发送验证码：返回结果：" + str(result))
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
    print("###### 测试开始")
    browser_path = ""
    if os.name == 'posix':  # Linux 系统
        browser_path = r"/opt/google/chrome/google-chrome"  # 或者 "/usr/bin/chromium-browser"
    elif os.name == 'nt':  # Windows 系统
        browser_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    # co = ChromiumOptions().set_browser_path(browser_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    co = ChromiumOptions().set_paths(browser_path=browser_path)
    # 2. 无头模式配置（根据系统情况选择）
    co.headless(True)  # 框架封装方法，自动添加 --headless=new 参数
    if os.name == 'posix':  # Linux 系统
        co.set_argument(f"--remote-debugging-port=9222")
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
    print("###### 连接浏览器成功")
    page = None
    try:
        page = ChromiumPage(co)
        print("###### 打开浏览器页面成功")
        tab = page.new_tab('https://www.baidu.com')
        print("###### 页面标题测试结果: " + tab.title)
        return "###### 打开的页面为：" + tab.title
    except Exception as e:
        print(f"###### 错误: {e}")
    finally:
        # 确保页面和浏览器实例正确关闭
        if page:
            page.close()  # 关闭页面


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)