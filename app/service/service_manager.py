import time
from app.service.background_services.default_background_service import BackgroundService
from app.service.background_services.weidian_background_service import WeiDianBackgroundService
from app.rpa.strategies.weidian.browser_pool import BrowserPool


class ServiceManager:
    """服务管理器 - 统一管理所有后台服务的启动和停止"""
    
    def __init__(self, browser_pool_size=3):
        self.services = []
        self.browser_pool = None
        self.browser_pool_size = browser_pool_size
    
    def start_all_services(self):
        """启动所有后台服务"""
        print("开始启动所有后台服务...")
        
        # 初始化浏览器池
        print(f"正在初始化浏览器池，大小: {self.browser_pool_size}")
        try:
            self.browser_pool = BrowserPool(pool_size=self.browser_pool_size)
            print("浏览器池初始化成功")
        except Exception as e:
            print(f"浏览器池初始化失败: {e}")
        
        # 启动原有服务
        default_service = BackgroundService(interval=5, order_status=101, supplier_code="hubei-dianxin", browser_pool=self.browser_pool)
        default_service.start()
        self.services.append(default_service)
        print("原有后台服务已启动")
        
        # 启动微店订单服务，使用较短的间隔以便更及时地处理订单
        weidian_service = WeiDianBackgroundService(interval=10, order_status=101, supplier_code="weidian", browser_pool=self.browser_pool)
        weidian_service.start()
        self.services.append(weidian_service)
        print("微店订单处理服务已启动")
        
        print("所有后台服务启动完成")
        return self.services
    
    def stop_all_services(self):
        """停止所有后台服务"""
        print("开始停止所有后台服务...")
        
        # 先停止所有服务
        for service in self.services:
            service.stop()
        self.services.clear()
        
        # 然后关闭浏览器池
        if self.browser_pool:
            print("正在关闭浏览器池...")
            try:
                self.browser_pool.close_all()
                print("浏览器池已关闭")
            except Exception as e:
                print(f"关闭浏览器池时发生错误: {e}")
            finally:
                self.browser_pool = None
        
        print("所有后台服务已停止")
        
    def get_browser_instance(self):
        """获取一个可用的浏览器实例"""
        if not self.browser_pool:
            print("浏览器池尚未初始化")
            return None
        
        try:
            return self.browser_pool.get_browser_instance()
        except Exception as e:
            print(f"获取浏览器实例时发生错误: {e}")
            return None
    
    def get_service_count(self):
        """获取当前运行的服务数量"""
        return len(self.services)


# 服务管理的全局实例
service_manager = ServiceManager()


# 便捷函数
def start_services():
    """启动所有后台服务的便捷函数"""
    return service_manager.start_all_services()


def stop_services(services=None):
    """停止所有后台服务的便捷函数"""
    if services is None:
        service_manager.stop_all_services()
    else:
        # 兼容原有接口
        for service in services:
            service.stop()
        print("指定服务已停止")