import time
from app.service.background_services.default_background_service import BackgroundService
from app.service.background_services.weidian_background_service import WeiDianBackgroundService


class ServiceManager:
    """服务管理器 - 统一管理所有后台服务的启动和停止"""
    
    def __init__(self):
        self.services = []
    
    def start_all_services(self):
        """启动所有后台服务"""
        print("开始启动所有后台服务...")
        
        # 启动原有服务
        default_service = BackgroundService(interval=5, order_status=101, supplier_code="hubei-dianxin")
        default_service.start()
        self.services.append(default_service)
        print("原有后台服务已启动")
        
        # 启动微店订单服务，使用较短的间隔以便更及时地处理订单
        weidian_service = WeiDianBackgroundService(interval=10, order_status=101, supplier_code="weidian")
        weidian_service.start()
        self.services.append(weidian_service)
        print("微店订单处理服务已启动")
        
        print("所有后台服务启动完成")
        return self.services
    
    def stop_all_services(self):
        """停止所有后台服务"""
        print("开始停止所有后台服务...")
        for service in self.services:
            service.stop()
        self.services.clear()
        print("所有后台服务已停止")
    
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