# -*- coding: utf-8 -*-
import logging
import threading

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - [%(thread)d:%(threadName)s] - %(message)s')
logger = logging.getLogger(__name__)

class OrderProcessor:
    """订单处理器，负责处理手机号订单和验证码相关操作"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取OrderProcessor单例实例"""
        if cls._instance is None:
            cls._instance = OrderProcessor()
        return cls._instance
        
    def __init__(self):
        """初始化订单处理器"""
        logger.info("[订单处理器-初始化] 创建订单处理器实例")
    
    def process_phone_number(self, browser_pool, phone_number):
        """
        处理单个手机号的函数
        
        Args:
            browser_pool: 浏览器实例池
            phone_number: 要处理的手机号
            
        Returns:
            bool: 处理是否成功
        """
        browser_instance = None
        tab = None
        thread_name = threading.current_thread().name
        process_id = f"[手机号处理-{phone_number}]"
        
        try:
            logger.info(f"{process_id} 开始处理，线程: {thread_name}")
            
            # 获取可用的浏览器实例
            logger.info(f"{process_id} 开始获取浏览器实例")
            browser_instance = browser_pool.get_browser_instance()
            if not browser_instance or not browser_instance.page:
                error_msg = "无法获取有效的浏览器实例"
                logger.error(f"{process_id} {error_msg}")
                raise Exception(error_msg)
            
            instance_id = browser_instance.instance_id
            logger.info(f"{process_id} 成功获取浏览器实例 {instance_id}")
      
            # 打开新标签页
            logger.info(f"{process_id} 使用浏览器实例 {instance_id} 打开目标页面")
            tab = browser_instance.page.new_tab("https://ju.hb.189.cn/shop/wap/DIS_102162161_61150.html")
            logger.info(f"{process_id} 页面打开成功，开始操作流程")
            
            # 点击立即办理按钮
            logger.info(f"{process_id} 步骤1/4: 查找并点击立即办理按钮")
            confirm_btn = tab.ele('.btnBox')
            if confirm_btn:
                confirm_btn.click()
                logger.info(f"{process_id} 步骤1/4: 立即办理按钮点击成功")
            else:
                error_msg = "立即办理按钮未找到"
                logger.error(f"{process_id} 步骤1/4: 异常 - {error_msg}")
                raise Exception(f"RPA填写手机号异常: {error_msg}")
                
            # 填写手机号
            logger.info(f"{process_id} 步骤2/4: 查找并输入手机号")
            phone_input = tab.eles('.smsinput')[1]
            if phone_input:
                phone_input.clear()
                phone_input.input(phone_number)
                logger.info(f"{process_id} 步骤2/4: 手机号 {phone_number} 输入成功")
            else:
                error_msg = "手机号输入框未找到"
                logger.error(f"{process_id} 步骤2/4: 异常 - {error_msg}")
                raise Exception(f"RPA填写手机号异常: {error_msg}")
            
            # 启动监听器
            logger.info(f"{process_id} 步骤3/4: 启动网络请求监听器")
            tab.listen.start('/random.action')
            logger.info(f"{process_id} 步骤3/4: 监听器启动成功")
            
            # 点击获取验证码按钮
            logger.info(f"{process_id} 步骤4/4: 查找并点击获取验证码按钮")
            verify_code_btn = tab.ele('#id_getMessage')
            if verify_code_btn:
                verify_code_btn.click()
                logger.info(f"{process_id} 步骤4/4: 获取验证码按钮点击成功")
            else:
                error_msg = "获取验证码按钮未找到"
                logger.error(f"{process_id} 步骤4/4: 异常 - {error_msg}")
                raise Exception(f"RPA发送验证码异常: {error_msg}")
            
            # 等待并捕获短信请求的响应
            logger.info(f"{process_id} 等待验证码发送响应，超时时间30秒")
            try:
                res = tab.listen.wait(timeout=30)  # 等待最多30秒
                if res and res.response:
                    request_data = str(res.request.postData)
                    logger.info(f"{process_id} 成功捕获验证码发送请求，请求数据: {request_data}")
                    
                    response_body = res.response.body
                    logger.info(f"{process_id} 验证码发送响应: {response_body}")
                    
                    if res.response.body.get("flag") != '0':
                        logger.warning(f"{process_id} 验证码发送失败，返回状态非成功")
                    else:
                        logger.info(f"{process_id} 验证码发送成功")
                else:
                    error_msg = "未捕获到验证码发送响应"
                    logger.error(f"{process_id} {error_msg}")
                    raise Exception(f"验证码发送异常: {error_msg}")
            except Exception as e:
                logger.error(f"{process_id} 捕获验证码响应时发生错误: {str(e)}")
                raise Exception(f"验证码发送异常: 无法获取响应 - {str(e)}")
            
            logger.info(f"{process_id} 处理流程完成，结果: 成功")
            return True
        
        except Exception as e:
            logger.error(f"{process_id} 处理过程中发生异常: {str(e)}")
            return False
        finally:
            # 关闭标签页
            if tab:
                try:
                    tab.close()
                    logger.info(f"{process_id} 标签页已关闭")
                except Exception as e:
                    logger.error(f"{process_id} 关闭标签页失败: {str(e)}")
    
    def process_order(self, browser_pool, order_data):
        """
        处理单个订单
        
        Args:
            browser_pool: 浏览器实例池
            order_data: 订单数据，包含手机号等信息
            
        Returns:
            dict: 处理结果
        """
        order_id = order_data.get('order_id', 'unknown')
        phone_number = order_data.get('phone_number')
        
        if not phone_number:
            logger.error(f"[订单处理-{order_id}] 错误：订单数据中缺少手机号")
            return {
                'order_id': order_id,
                'phone_number': None,
                'success': False,
                'error': '缺少手机号'
            }
        
        # 调用手机号处理函数
        result = self.process_phone_number(browser_pool, phone_number)
        
        return {
            'order_id': order_id,
            'phone_number': phone_number,
            'success': result,
            'error': None if result else '处理失败'
        }
    
    def batch_process_orders(self, browser_pool, orders_list):
        """
        批量处理订单（需要在线程池中调用才能并行）
        
        Args:
            browser_pool: 浏览器实例池
            orders_list: 订单列表
            
        Returns:
            list: 处理结果列表
        """
        results = []
        
        for order in orders_list:
            result = self.process_order(browser_pool, order)
            results.append(result)
        
        return results

# 全局订单处理器实例
_order_processor_instance = None

def get_order_processor():
    """
    获取订单处理器单例
    
    Returns:
        OrderProcessor: 订单处理器实例
    """
    global _order_processor_instance
    if _order_processor_instance is None:
        _order_processor_instance = OrderProcessor()
    return _order_processor_instance

# 便捷函数
def process_phone_number(browser_pool, phone_number):
    """
    便捷函数：处理单个手机号
    
    Args:
        browser_pool: 浏览器实例池
        phone_number: 手机号
        
    Returns:
        bool: 处理是否成功
    """
    processor = get_order_processor()
    return processor.process_phone_number(browser_pool, phone_number)


def process_order(browser_pool, order_data):
    """
    便捷函数：处理单个订单
    
    Args:
        browser_pool: 浏览器实例池
        order_data: 订单数据
        
    Returns:
        dict: 处理结果
    """
    processor = get_order_processor()
    return processor.process_order(browser_pool, order_data)