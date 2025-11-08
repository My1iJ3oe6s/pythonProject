import os
import random  # 导入random模块
import time

from app.service import start_services
from app.service.background_service import BackgroundService, WeiDianBackgroundService  # 导入后台服务模块
from threading import Thread  # 导入线程模块

from DrissionPage import ChromiumPage, ChromiumOptions
from fastapi import FastAPI
from typing import Dict, Any
from app.rpa.request import PlaceOrderRequest
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.Order.order_dao import SelfStockOrderDAO, SessionLocal
from app.service.order_service import OrderService  # 导入订单服务
from app.service.order_push_service import OrderPushService  # 导入新的订单推送服务

app = FastAPI()

@app.post("/api/v1/get-code")
async def get_verification_code(request: PlaceOrderRequest) -> Dict[str, Any]:
    """获取验证码接口"""
    return OrderService.get_verification_code(request)

@app.post("/api/v1/place-order")
async def place_order(request: PlaceOrderRequest) -> Dict[str, Any]:
    """下单接口"""
    return OrderService.execute_place_order(request)

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
    co.headless(False)
    co.incognito()  # 匿名模式
    co.set_argument('--ignore_https_errors')
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument(f"--remote-debugging-port=9222")
    co.set_argument(f"--disable-web-security")
    co.set_argument(f"--allow-running-insecure-content")
    co.set_argument('--ignore-certificate-errors', True)
    # 禁用图片资源  主要是为了加快页面加载
    co.set_argument('--blink-settings=imagesEnabled=false')
    co.set_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    co.set_argument('--window-size=1920,1080')  # 设置窗口尺寸
    co.ignore_certificate_errors()
    page = None
    try:
        page = ChromiumPage(co)
        print("###### 打开浏览器页面成功")
        # tab = page.new_tab('https://hb.189.cn/xhy?o=7DD5AD758DC424463F616B4E9CD2BA2E&k=ECA48F85E135D9A9A3B81CAEA55AE70C&u=8EE7731A31A4E307C541F9702653BD045987B06DC5F424F1&s=45FB50B8E1D1EDBC9F3E7E44CEB587A4')
        tab = page.new_tab(
           'https://hls.it.10086.cn/v1/tfs/T1LtxTB7AT1RXx1p6K.html?shopId=MmrqURAm&goodsId=528243')
        # page.wait(1)
        print("###### 页面标题测试结果: " + tab.title)

        # element = page.ele('#handleButton')
        # element.click()
        element = tab.ele('.ui-btn ui-btn_primary')
        element.click()
        sj = tab.ele('#serviceNum')
        placeholder_text = sj.attrs.get("placeholder")
        print("###### 获取的弹框文字为:" + placeholder_text)
        return "###### 打开的页面为：" + tab.title
    except Exception as e:
        print(f"###### 错误: {e}")
    finally:
        # 确保页面和浏览器实例正确关闭
        if page:
            page.close()  # 关闭页面


@app.post("/api/v1/test-Wuhan")
async def test():
    """下单接口"""
    print("###### 测试开始")
    browser_path = ""
    if os.name == 'posix':  # Linux 系统
        browser_path = r"/opt/google/chrome/google-chrome"
    elif os.name == 'nt':  # Windows 系统
        browser_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

    co = ChromiumOptions().set_paths(browser_path=browser_path)

    # 基础配置
    co.headless(False)
    co.incognito()
    co.set_argument('--ignore_https_errors')
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument(f"--remote-debugging-port=9233")
    co.set_argument(f"--disable-web-security")
    co.set_argument(f"--allow-running-insecure-content")
    co.set_argument('--ignore-certificate-errors', True)
    co.set_argument('--blink-settings=imagesEnabled=false')
    co.set_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    co.set_argument('--window-size=1920,1080')
    co.ignore_certificate_errors()

    print("###### 测试开始1")
    page = None
    try:
        page = ChromiumPage(co, timeout=90)

        # 1. 设置更真实的浏览器特征
        page.set.load_mode.normal()

        # 2. 修改浏览器特征
        page.run_js("""
            // 修改 navigator 属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // 修改 Headers 原型
            if (Headers.prototype.append) {
                const originalAppend = Headers.prototype.append;
                Headers.prototype.append = function(name, value) {
                    if (name.toLowerCase() === 'function') {
                        return;
                    }
                    return originalAppend.call(this, name, value);
                };
            }

            // 禁用检测函数
            window._$_l = function() { return true; };
            window.$_ts = undefined;
        """)

        # 3. 设置请求头
        page.set.headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        })

        # 4. 模拟用户行为
        def simulate_user_behavior():
            time.sleep(random.uniform(1, 3))
            page.run_js("""
                var event = new MouseEvent('mousemove', {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true,
                    'clientX': %d,
                    'clientY': %d
                });
                document.dispatchEvent(event);
            """ % (random.randint(100, 700), random.randint(100, 500)))

        print("###### 打开浏览器页面成功")

        # 5. 访问页面前模拟用户行为
        simulate_user_behavior()

        # 6. 访问目标页面
        page.get(
            'https://hb.189.cn/xhy?o=7DD5AD758DC424463F616B4E9CD2BA2E&k=ECA48F85E135D9A9A3B81CAEA55AE70C&u=8EE7731A31A4E307C541F9702653BD045987B06DC5F424F1&s=45FB50B8E1D1EDBC9F3E7E44CEB587A4')

        # 7. 等待页面加载完成
       # page.wait.load_complete()

        # 8. 再次模拟用户行为
        simulate_user_behavior()

        print("###### 页面标题测试结果: " + page.title)

        # 9. 监听验证码请求
        page.listen.start('/smsCheck.action')

        # 10. 点击验证码按钮
        verify_code_btn = page.ele('#getRandomss')
        if verify_code_btn:
            # 模拟真实点击
            page.run_js("""
                var element = document.querySelector('#getRandomss');
                if(element) {
                    var rect = element.getBoundingClientRect();
                    var event = new MouseEvent('click', {
                        'view': window,
                        'bubbles': true,
                        'cancelable': true,
                        'clientX': rect.left + rect.width/2,
                        'clientY': rect.top + rect.height/2
                    });
                    element.dispatchEvent(event);
                }
            """)

        # 11. 等待验证码响应
        res = page.listen.wait(timeout=30)
        if res and res.response:
            print("###### RPA发送验证码:执行发送短信操作：获取返回结果" + str(res.response.body))

        return "###### 打开的页面为：" + page.title

    except Exception as e:
        print(f"###### 错误: {e}")
        return f"###### 发生错误: {str(e)}"

    finally:
        if page:
            page.close()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_background_service():
    """单独运行后台服务"""
    service = BackgroundService(interval=5)
    service.start()
    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        service.stop()
        print("Background service stopped.")

def run_weidian_background_service():
    """单独运行后台服务"""
    weidian_service = WeiDianBackgroundService(interval=10, order_status=101, supplier_code="weidian")
    weidian_service.start()
    print("微店订单处理服务已启动")
    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        weidian_service.stop()
        print("Background service stopped.")


def run_order_push_service():
    """单独运行订单推送服务"""
    push_service = OrderPushService(interval=10)
    push_service.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        push_service.stop()
        print("Order push service stopped.")


@app.post("/orders/status/supplier")
async def read_orders(params: dict, db: Session = Depends(get_db)):
    order_status = params.get('order_status')
    supplier_code = params.get('supplier_code')
    
    if order_status is None or supplier_code is None:
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    dao = SelfStockOrderDAO(db)
    orders = dao.get_orders_by_status_and_supplier(order_status, supplier_code)
    return {"count": len(orders), "orders": orders}


if __name__ == "__main__":
    # 启动后台服务线程
    background_thread = Thread(target=run_background_service, daemon=True)
    background_thread.start()
    #
    # background_thread = Thread(target=run_weidian_background_service, daemon=True)
    # background_thread.start()
    services = start_services()

    # 启动订单推送服务线程
    order_push_thread = Thread(target=run_order_push_service, daemon=True)
    order_push_thread.start()

    # 启动 FastAPI 服务
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
