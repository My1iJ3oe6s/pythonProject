from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class SelfStockOrder(Base):
    __tablename__ = 'self_stock_order'

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(128), nullable=False)
    distributor_code = Column(String(255))
    distributor_url = Column(Text)
    external_order_no = Column(String(218))
    phone = Column(String(100))
    province = Column(String(128))
    city_name = Column(String(128))
    city_code = Column(String(128))
    sms_num = Column(String(255))
    goods_code = Column(String(100))
    goods_name = Column(String(1024))
    supplier_code = Column(String(128))
    supplier_goods_code = Column(String(128))
    order_time = Column(DateTime)
    order_status = Column(SmallInteger)
    remark = Column(Text)
    sync_order_message = Column(Text)
    create_by = Column(String(64))
    create_time = Column(DateTime)
    update_by = Column(Text)
    update_time = Column(DateTime)
    is_deduct = Column(SmallInteger)
    url_params = Column(String(500))
    supplier_order_no = Column(String(64))
    is_unsubscribe = Column(SmallInteger)
    unsubscribe_time = Column(DateTime)
    is_blacklist = Column(SmallInteger)
    gong_hao = Column(String(126))
    goods_detail_id = Column(String(128))
    platform = Column(String(512))
    source_data = Column(Text)
    supplier_order_url = Column(String(256))


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 假设数据库URL为'your_database_url'
DATABASE_URL = 'mysql+pymysql://haoka:rNXmr4iK4SMAyTww@8.155.36.216:3306/haoka?charset=utf8mb4&use_unicode=1'

# 添加对 DATABASE_URL 的检查
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# 注意：如果遇到 "No module named 'pymysql'" 错误，请确保已安装 pymysql 模块
# 安装命令：pip install pymysql
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class SelfStockOrderDAO:
    def __init__(self, db_session):
        self.db_session = db_session

    def create_order(self, order_data):
        new_order = SelfStockOrder(**order_data)
        self.db_session.add(new_order)
        self.db_session.commit()
        self.db_session.refresh(new_order)
        return new_order

    def get_order_by_id(self, order_id):
        return self.db_session.query(SelfStockOrder).filter(SelfStockOrder.order_id == order_id).first()

    def get_orders_by_status_and_supplier(self, order_status, supplier_code):
        return self.db_session.query(SelfStockOrder).filter(
            SelfStockOrder.order_status == order_status,
            SelfStockOrder.supplier_code == supplier_code
        ).limit(10).all()

    def get_orders_by_status(self, order_status):
        return self.db_session.query(SelfStockOrder).filter(
            SelfStockOrder.order_status == order_status
        ).limit(10).all()

    def update_order_status_by_id(self, order_id, new_status, order_message):
        """
        根据订单ID更新订单状态
        :param order_message:
        :param order_id: 订单ID
        :param new_status: 新的状态值
        :return: 成功返回 True，失败返回 False
        """
        order = self.db_session.query(SelfStockOrder).get(order_id)
        if not order:
            print(f"Order with ID {order_id} not found.")
            return False

        order.order_status = new_status
        order.sync_order_message = order_message
        order.remark = f"订单发送短信提示信息为：{order_message}"
        try:
            self.db_session.add(order)
            self.db_session.commit()
            print(f"Order {order_id} status updated to {new_status}.")
            return True
        except Exception as e:
            self.db_session.rollback()
            print(f"Failed to update order status: {e}")
            return False

    # 可以根据需要添加更多CRUD操作...
