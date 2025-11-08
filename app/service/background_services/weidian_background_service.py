import threading
import time
from collections import defaultdict
from app.service.base_background_service import BaseBackgroundService
from app.Order.order_dao import SelfStockOrderDAO, SessionLocal
from app.rpa.request import PlaceOrderRequest
from app.service.order_service import OrderService


class WeiDianBackgroundService(BaseBackgroundService):
    """微店订单处理服务 - 实现订单队列和商品级别限流"""
    
    def __init__(self, interval=5, order_status=101, supplier_code="weidian", browser_pool=None):
        super().__init__(interval, order_status, supplier_code)
        # 接收浏览器池实例
        self.browser_pool = browser_pool

    def start(self):
        """启动微店订单服务，包括查询服务和处理服务"""
        super().start()
        # 启动订单处理线程
        print(f"微店订单处理服务已启动 - 查询间隔: {self.interval}秒")

    def stop(self):
        """停止微店订单服务"""
        super().stop()
        # 停止订单处理线程
        print("微店订单处理服务已停止")

    def execute_task(self):
        """执行微店订单查询任务 - 查询最近100条订单并加入队列"""
        current_time = time.time()
        print(f"#### 执行微店订单查询任务，当前时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}")
        
        db = SessionLocal()
        try:
            dao = SelfStockOrderDAO(db)
            # 查询微店待处理订单
            orders = dao.get_orders_by_status_and_supplier(
                self.default_order_status,
                self.default_supplier_code
            )
            
            print(f"#### 查询到 {len(orders)} 个微店待处理订单")
            
            # 添加新订单到队列
            added_count = 0
            for order in orders:
                if order.order_no not in self.queued_orders and order.order_no not in self.processing_orders:
                    # 构造请求对象
                    request = PlaceOrderRequest(
                        open_url=order.supplier_order_url,
                        order_id=order.order_no,
                        phone=order.phone,
                        product_code=order.goods_code,
                        sms_code=order.sms_num,
                        supplier_code=order.supplier_code
                    )
                    response = OrderService.get_verification_code(request)
                    db = SessionLocal()
                    dao = SelfStockOrderDAO(db)
                    # 验证码发送成功后更新订单状态为 102
                    dao.update_order_status_by_id(order.order_id, 1 if response.get("code") == 200 else 4,  response.get("msg"))
                    print(f"#### 订单 {order.order_no} (商品 {order.goods_code + order.supplier_goods_code}) 已加入队列")
                else:
                    print(f"#### 订单 {order.order_no} 已在队列或处理中，跳过添加")
            
            
        except Exception as e:
            print(f"#### 执行订单查询任务时发生异常: {e}")
        finally:
            db.close()
