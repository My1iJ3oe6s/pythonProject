from app.service.base_background_service import BaseBackgroundService
from app.Order.order_dao import SelfStockOrderDAO, SessionLocal


class BackgroundService(BaseBackgroundService):
    """原有的定时任务服务，处理普通订单"""
    
    def __init__(self, interval=5, order_status=101, supplier_code="hubei-dianxin"):
        super().__init__(interval, order_status, supplier_code)

    def execute_task(self):
        """执行发送短信任务"""
        print("#### 执行发送短信任务.")
        db = SessionLocal()
        try:
            dao = SelfStockOrderDAO(db)
            # 使用传入的状态和供应商代码查询订单
            orders = dao.get_orders_by_status_and_supplier(
                self.default_order_status, self.default_supplier_code
            )
            print(f"#### 执行订单数为: {len(orders)} ，供应商策略为: {self.default_supplier_code}.")

            # 遍历订单并发送短信
            for order in orders:
                self.send_sms_for_order(order)

        finally:
            db.close()