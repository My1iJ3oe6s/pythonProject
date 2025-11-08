# -*- coding: utf-8 -*-
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - [%(thread)d:%(threadName)s] - %(message)s')
logger = logging.getLogger(__name__)

class ThreadPoolManager:
    """线程池管理器，提供线程池的创建和任务管理功能"""
    
    def __init__(self, max_workers=8, thread_name_prefix='Worker'):
        """
        初始化线程池管理器
        
        Args:
            max_workers: 最大线程数，默认为8
            thread_name_prefix: 线程名称前缀，默认为'Worker'
        """
        self.max_workers = max_workers
        self.thread_name_prefix = thread_name_prefix
        self.executor = None
        logger.info(f"[线程池-初始化] 创建线程池管理器，最大线程数: {max_workers}，线程名称前缀: {thread_name_prefix}")
    
    def create_executor(self):
        """创建线程池执行器"""
        if self.executor is None or self.executor._shutdown:
            logger.info(f"[线程池-创建] 创建ThreadPoolExecutor，最大线程数: {self.max_workers}")
            self.executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix=self.thread_name_prefix
            )
        return self.executor
    
    def submit_task(self, func, *args, **kwargs):
        """
        提交单个任务到线程池
        
        Args:
            func: 要执行的函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数
            
        Returns:
            Future对象
        """
        if self.executor is None or self.executor._shutdown:
            self.create_executor()
        
        task_name = func.__name__
        logger.debug(f"[线程池-提交] 提交任务: {task_name}")
        return self.executor.submit(func, *args, **kwargs)
    
    def submit_tasks(self, func, tasks_params):
        """
        批量提交任务到线程池
        
        Args:
            func: 要执行的函数
            tasks_params: 任务参数列表，每个元素是一个元组(位置参数列表, 关键字参数字典)
            
        Returns:
            字典，键为Future对象，值为任务标识（这里使用参数的字符串表示）
        """
        if self.executor is None or self.executor._shutdown:
            self.create_executor()
        
        task_name = func.__name__
        future_to_task = {}
        
        logger.info(f"[线程池-提交批量] 开始批量提交任务: {task_name}，任务数量: {len(tasks_params)}")
        
        for i, (args, kwargs) in enumerate(tasks_params):
            # 为每个任务创建一个标识
            task_id = f"{task_name}_task_{i}"
            logger.debug(f"[线程池-提交批量] 提交任务 {i+1}/{len(tasks_params)}: {task_id}")
            future = self.executor.submit(func, *args, **kwargs)
            future_to_task[future] = task_id
        
        logger.info(f"[线程池-提交批量] 所有任务提交完成，总计: {len(future_to_task)}个任务")
        return future_to_task
    
    def submit_tasks_with_identifiers(self, func, tasks_identifiers):
        """
        提交带标识符的任务到线程池
        
        Args:
            func: 要执行的函数
            tasks_identifiers: 列表，每个元素为(标识符, *args, **kwargs)格式
            
        Returns:
            字典，键为Future对象，值为任务标识符
        """
        if self.executor is None or self.executor._shutdown:
            self.create_executor()
        
        task_name = func.__name__
        future_to_identifier = {}
        
        logger.info(f"[线程池-提交带标识] 开始提交带标识符的任务: {task_name}，任务数量: {len(tasks_identifiers)}")
        
        for i, (identifier, *args_kwargs) in enumerate(tasks_identifiers):
            # 处理参数，分离位置参数和关键字参数
            args = args_kwargs[:-1] if args_kwargs and isinstance(args_kwargs[-1], dict) else args_kwargs
            kwargs = args_kwargs[-1] if args_kwargs and isinstance(args_kwargs[-1], dict) else {}
            
            logger.debug(f"[线程池-提交带标识] 提交任务 {i+1}/{len(tasks_identifiers)}: {identifier}")
            future = self.executor.submit(func, *args, **kwargs)
            future_to_identifier[future] = identifier
        
        logger.info(f"[线程池-提交带标识] 所有任务提交完成，总计: {len(future_to_identifier)}个任务")
        return future_to_identifier
    
    def wait_for_results(self, future_dict, callback=None):
        """
        等待所有任务完成并获取结果
        
        Args:
            future_dict: 包含Future对象和任务标识的字典
            callback: 可选的回调函数，接收(task_identifier, result)作为参数
            
        Returns:
            字典，键为任务标识，值为任务结果
        """
        results = {}
        completed_count = 0
        success_count = 0
        failure_count = 0
        total_tasks = len(future_dict)
        
        logger.info(f"[线程池-结果] 开始等待任务执行结果，总计: {total_tasks}个任务")
        
        for future in as_completed(future_dict):
            task_identifier = future_dict[future]
            completed_count += 1
            
            try:
                result = future.result()
                results[task_identifier] = result
                success_count += 1
                logger.info(f"[线程池-结果] [完成 {completed_count}/{total_tasks}] 任务 {task_identifier} 执行成功")
                
                # 如果提供了回调函数，调用它
                if callback:
                    try:
                        callback(task_identifier, result)
                    except Exception as cb_e:
                        logger.error(f"[线程池-结果] 任务 {task_identifier} 回调函数执行异常: {str(cb_e)}")
                        
            except Exception as e:
                results[task_identifier] = None
                failure_count += 1
                logger.error(f"[线程池-结果] [完成 {completed_count}/{total_tasks}] 任务 {task_identifier} 执行异常: {str(e)}")
        
        logger.info(f"[线程池-结果] 所有任务执行完毕！总计: {total_tasks}, 成功: {success_count}, 失败: {failure_count}")
        return results
    
    def shutdown(self, wait=True):
        """
        关闭线程池
        
        Args:
            wait: 是否等待所有任务完成，默认为True
        """
        if self.executor and not self.executor._shutdown:
            logger.info(f"[线程池-关闭] 关闭线程池，等待任务完成: {wait}")
            self.executor.shutdown(wait=wait)
            logger.info(f"[线程池-关闭] 线程池已关闭")
    
    def close(self):
        """关闭线程池（shutdown方法的别名）"""
        self.shutdown(wait=True)
    

    
    def process_tasks_parallel(self, func, tasks):
        """并行处理多个任务"""
        logger.info(f"[线程池-处理] 开始并行处理 {len(tasks)} 个任务")
        results = []
        futures = []
        
        # 确保executor已创建
        if self.executor is None or self.executor._shutdown:
            self.create_executor()
        
        # 提交所有任务
        for task_idx, task in enumerate(tasks):
            if isinstance(task, tuple):
                future = self.executor.submit(func, *task)
            else:
                future = self.executor.submit(func, task)
            futures.append(future)
            logger.debug(f"[线程池-处理] 任务 {task_idx+1}/{len(tasks)} 已提交")
        
        # 获取所有结果
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                logger.info(f"[线程池-处理] 任务执行成功")
            except Exception as e:
                logger.error(f"[线程池-处理] 任务执行异常: {e}")
                results.append(None)
        
        logger.info(f"[线程池-处理] 所有任务处理完成，总计: {len(results)}个任务")
        return results
    
    def __enter__(self):
        """支持上下文管理器协议"""
        self.create_executor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭线程池"""
        self.shutdown(wait=True)
        return False  # 不抑制异常

# 简单的线程池辅助函数
def create_thread_pool(max_workers=8, thread_name_prefix='Worker'):
    """创建线程池的便捷函数"""
    return ThreadPoolManager(max_workers, thread_name_prefix)

def process_tasks_parallel(func, tasks, max_workers=8):
    """并行处理任务的便捷函数"""
    thread_pool = ThreadPoolManager(max_workers)
    try:
        return thread_pool.process_tasks_parallel(func, tasks)
    finally:
        thread_pool.close()