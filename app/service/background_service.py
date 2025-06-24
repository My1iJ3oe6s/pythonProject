import threading
import time
from app.Order.order_dao import SelfStockOrderDAO
from app.Order.order_dao import SessionLocal
from app.rpa.request import PlaceOrderRequest
from app.service.order_service import OrderService


class BackgroundService:
    def __init__(self, interval=5, order_status=101, supplier_code="hubei-dianxin"):
        self.interval = interval
        self.is_running = False
        self.thread = None
        self.cached_orders = {}  # 缓存订单数据，格式为 {supplier_code: orders}
        self.default_order_status = order_status
        self.default_supplier_code = supplier_code

    def start(self):
        """Start the background service."""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True  # Daemonize thread
            self.thread.start()

    def stop(self):
        """Stop the background service."""
        self.is_running = False

    def _run(self):
        """The actual task to be executed periodically."""
        while self.is_running:
            try:
                self.execute_task()
            except Exception as e:
                print(f"Error in background task: {e}")
            time.sleep(self.interval)

    def execute_task(self):
        """Override this method with your custom logic."""
        print("#### 执行发送短信任务.")
        db = SessionLocal()
        try:
            dao = SelfStockOrderDAO(db)
            # 使用传入的状态和供应商代码查询订单
            orders = dao.get_orders_by_status_and_supplier(
                self.default_order_status, self.default_supplier_code
            )
            print(f"#### 执行订单数为: {len(orders)} ，供应商策略为: {self.default_supplier_code}.")
            # 缓存订单数据
            # self.cached_orders[self.default_supplier_code] = orders

            # 遍历订单并发送短信
            for order in orders:
                self.send_sms_for_order(order)

        finally:
            db.close()

    def send_sms_for_order(self, order):
        """调用 OrderService 发送短信，并在成功后更新订单状态"""
        print(f"###### 1、准备开发发送短信: {order.order_no}, {order.phone}")
        
        # 构造请求对象
        request = PlaceOrderRequest(
            open_url=order.supplier_order_url,
            order_id=order.order_no,
            phone=order.phone,
            product_code=order.goods_code,
            sms_code=order.sms_num,
            supplier_code=order.supplier_code
        )

        try:
            # 调用验证码接口
            response = OrderService.get_verification_code(request)
            db = SessionLocal()
            dao = SelfStockOrderDAO(db)
            # 验证码发送成功后更新订单状态为 102
            dao.update_order_status_by_id(order.order_id, 1 if response.get("code") == 200 else 4,  response.get("msg"))
        except Exception as e:
            print(f"###### 发送短信异常: {order.order_no}: {e}")
