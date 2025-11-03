import threading
import time
from app.Order.order_dao import SelfStockOrderDAO
from sqlalchemy.orm import Session
from app.Order.order_dao import SessionLocal
from app.service.order_service import OrderService
from app.rpa.request import PlaceOrderRequest


class OrderPushService:
    def __init__(self, interval=10, order_status="201", supplier_code="hubei-dianxin"):
        self.interval = interval
        self.is_running = False
        self.thread = None
        self.default_order_status = order_status
        self.default_supplier_code = supplier_code

    def start(self):
        """Start the order push service."""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        """Stop the order push service."""
        self.is_running = False

    def _run(self):
        """The actual task to be executed periodically."""
        while self.is_running:
            try:
                self.execute_task()
            except Exception as e:
                print(f"Error in order push task: {e}")
            time.sleep(self.interval)

    def execute_task(self):
        """Fetch and push orders."""
        print("Executing order push task...")
        db = SessionLocal()
        try:
            dao = SelfStockOrderDAO(db)
            orders = dao.get_orders_by_status(
                self.default_order_status
            )
            print(f"Pushing {len(orders)} orders for {self.default_supplier_code}.")

            # 遍历订单并推送
            for order in orders:
                self.push_order(order)

        finally:
            db.close()

    @staticmethod
    def push_order(order):
        """Push a single order using OrderService."""
        request = PlaceOrderRequest(
            open_url=order.distributor_url,
            order_id=order.order_no,
            phone=order.phone,
            product_code=order.goods_code,
            sms_code=order.sms_num,
            supplier_code=order.supplier_code
        )
        print(f"###### 推送订单获取订单凭证: {request.order_id}")
        try:
            # 调用验证码接口
            response = OrderService.execute_place_order(request)
            #https://xyy.jxschot.com/mobile-template/index.html?xyyOrderNo=XYY20250528132119001?p=D8043BE088B8A92B1BDFF97496EA1F006071AA22F4C599997986F3054A626DAA
            print(f"###### 推送订单获取订单凭证: {response}")
            db = SessionLocal()
            dao = SelfStockOrderDAO(db)
            # 验证码发送成功后更新订单状态为 102
            dao.update_order_status_by_id(order.order_id, 202 if response.get("code") == 200 else 5,  response.get("responseData") if  response.get("code") != 200 else response.get("data"))
        except Exception as e:
            print(f"Failed to send SMS for order {order.order_no}: {e}")