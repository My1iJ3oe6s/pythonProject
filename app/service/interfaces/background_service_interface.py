from abc import ABC, abstractmethod
from typing import List


class BackgroundServiceInterface(ABC):
    """后台服务接口定义"""
    
    @abstractmethod
    def start(self):
        """启动后台服务"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止后台服务"""
        pass
    
    @abstractmethod
    def execute_task(self):
        """执行具体任务"""
        pass


class OrderServiceInterface(ABC):
    """订单服务接口定义"""
    
    @abstractmethod
    def process_order(self, order):
        """处理订单"""
        pass