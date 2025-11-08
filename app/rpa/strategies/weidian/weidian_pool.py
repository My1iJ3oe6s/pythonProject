# -*- coding: utf-8 -*-
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - [%(thread)d:%(threadName)s] - %(message)s')
logger = logging.getLogger(__name__)

# 从当前目录导入模块
from browser_pool import BrowserPool
from thread_pool_utils import ThreadPoolManager
from order_processor import OrderProcessor

def main():
    """多线程主函数"""
    
    browser_pool = None
    
    try:
        logger.info("[主程序] 开始执行多线程手机号处理任务")
        
        # 手机号列表
        phone_numbers = [
            "13800000000",
            "13900000000",
            "14000000000",
            "14100000000",
            "14200000000",
            "14800000000",
            "14900000000",
            "14700000000",
            "14600000000",
            "14500000000"
        ]
        
        logger.info(f"[主程序] 手机号列表加载完成，总计 {len(phone_numbers)} 个手机号")
        
        # 初始化浏览器实例池
        logger.info("[主程序] 开始初始化浏览器实例池")
        browser_pool = BrowserPool(pool_size=3)
        logger.info("[主程序] 浏览器实例池初始化完成")
        
        # 检查是否有可用的浏览器实例
        if not browser_pool.browser_instances:
            logger.error("[主程序] 错误：无法初始化浏览器实例池，无可用实例")
            return
        
        # 获取订单处理器实例
        order_processor = OrderProcessor.get_instance()
        
        # 创建线程池管理器
        max_workers = min(8, len(phone_numbers))  # 线程数不超过8
        logger.info(f"[主程序] 创建线程池管理器，最大线程数: {max_workers}")
        thread_pool = ThreadPoolManager(max_workers=max_workers)
        
        # 准备任务参数
        tasks = [(browser_pool, phone) for phone in phone_numbers]
        
        # 提交并执行任务
        logger.info(f"[主程序] 开始批量提交 {len(tasks)} 个任务")
        results = thread_pool.process_tasks_parallel(order_processor.process_phone_number, tasks)
        
        # 统计结果
        success_count = sum(1 for result in results if result)
        failure_count = len(results) - success_count
        
        # 任务全部完成，输出统计信息
        logger.info(f"[主程序] 所有任务执行完毕！总计: {len(results)}, 成功: {success_count}, 失败: {failure_count}")
    
    except KeyboardInterrupt:
        logger.warning("[主程序] 用户中断程序执行")
    except Exception as e:
        logger.error(f"[主程序] 发生异常: {str(e)}")
    finally:
        # 关闭浏览器实例池
        if browser_pool:
            logger.info("[主程序] 开始清理资源，关闭浏览器实例池")
            browser_pool.close_all()
            logger.info("[主程序] 浏览器实例池已关闭")
    
    logger.info("[主程序] 程序执行完毕，所有资源已释放")

if __name__ == '__main__':
    main()



