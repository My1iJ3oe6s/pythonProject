import threading
import time
from collections import defaultdict
from app.service.base_background_service import BaseBackgroundService
from app.Order.order_dao import SelfStockOrderDAO, SessionLocal
from app.rpa.request import PlaceOrderRequest
from app.service.order_service import OrderService


class WeiDianBackgroundService(BaseBackgroundService):
    """微店订单处理服务 - 实现订单队列和商品级别限流"""
    
    def __init__(self, interval=5, order_status=101, supplier_code="weidian"):
        super().__init__(interval, order_status, supplier_code)
        # 按商品分组的订单队列
        self.order_queues = defaultdict(list)
        # 记录队列中已存在的订单号，避免重复添加
        self.queued_orders = set()
        # 记录当前正在处理的订单
        self.processing_orders = set()
        # 记录每个商品的上次处理时间
        self.product_last_process_time = defaultdict(float)
        # 限流时间间隔（秒）
        self.rate_limit_interval = 60
        # 用于控制订单处理线程
        self.processing_thread = None
        self.processing_is_running = False

    def start(self):
        """启动微店订单服务，包括查询服务和处理服务"""
        super().start()
        # 启动订单处理线程
        self.processing_is_running = True
        self.processing_thread = threading.Thread(target=self._process_orders_worker)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        print(f"微店订单处理服务已启动 - 查询间隔: {self.interval}秒")

    def stop(self):
        """停止微店订单服务"""
        super().stop()
        # 停止订单处理线程
        self.processing_is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
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
                    # 按商品分组加入队列
                    self.order_queues[order.goods_code + order.supplier_goods_code].append(order)
                    self.queued_orders.add(order.order_no)
                    added_count += 1
                    print(f"#### 订单 {order.order_no} (商品 {order.goods_code + order.supplier_goods_code}) 已加入队列")
                else:
                    print(f"#### 订单 {order.order_no} 已在队列或处理中，跳过添加")
            
            # 打印队列状态
            self._print_queue_status()
            print(f"#### 本次查询完成，新添加 {added_count} 个订单到队列")
            
        except Exception as e:
            print(f"#### 执行订单查询任务时发生异常: {e}")
        finally:
            db.close()
    
    def _process_orders_worker(self):
        """订单处理工作线程 - 持续监听队列并按限流规则处理订单"""
        print("微店订单处理工作线程已启动")
        
        while self.processing_is_running:
            try:
                current_time = time.time()
                
                # 对每个商品队列检查并处理订单
                for product_code in list(self.order_queues.keys()):
                    # 检查是否可以处理该商品的订单
                    if self._can_process_product(product_code, current_time) and self.order_queues[product_code]:
                        # 从队列中取出第一个订单
                        order = self.order_queues[product_code].pop(0)
                        
                        # 从队列记录中移除，但添加到处理中记录
                        self.queued_orders.remove(order.order_no)
                        self.processing_orders.add(order.order_no)
                        
                        print(f"#### 从队列取出商品 {product_code} 的订单 {order.order_no} 进行处理")
                        
                        try:
                            # 处理订单
                            self.process_weidian_order(order)
                            # 更新该商品的最后处理时间
                            self.product_last_process_time[product_code] = current_time
                            print(f"#### 商品 {product_code} 的订单 {order.order_no} 处理完成")
                        finally:
                            # 无论成功失败，都从处理中集合移除
                            self.product_last_process_time[product_code] = current_time
                            self.processing_orders.remove(order.order_no)
                
                # 打印队列状态
                self._print_queue_status()
                
                # 短暂休眠避免CPU占用过高
                time.sleep(1)
                
            except Exception as e:
                print(f"#### 订单处理工作线程异常: {e}")
                time.sleep(2)  # 异常后等待更长时间再重试
    
    def _can_process_product(self, product_code, current_time):
        """检查是否可以处理指定商品的订单"""
        last_process_time = self.product_last_process_time.get(product_code, 0)
        can_process = (current_time - last_process_time) >= self.rate_limit_interval
        if not can_process:
            remaining_time = self.rate_limit_interval - (current_time - last_process_time)
            print(f"#### 商品 {product_code} 还需等待 {remaining_time:.1f} 秒才能处理下一订单")
        return can_process
    
    def _print_queue_status(self):
        """打印队列状态信息"""
        total_orders = sum(len(queue) for queue in self.order_queues.values())
        product_count = len([code for code in self.order_queues.keys() if self.order_queues[code]])
        
        print(f"===== 队列状态 =====")
        print(f"总订单数: {total_orders}")
        print(f"有订单的商品数: {product_count}")
        
        for product_code, queue in self.order_queues.items():
            if queue:
                print(f"商品 {product_code}: {len(queue)} 个订单")
        print(f"处理中的订单数: {len(self.processing_orders)}")
        print(f"==================")
        
    def process_weidian_order(self, order):
        """处理单个微店订单"""
        print(f"###### 微店订单处理: 开始处理订单 {order.order_no}, 商品 {order.goods_code}")
        
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