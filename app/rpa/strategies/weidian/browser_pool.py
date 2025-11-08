# -*- coding: utf-8 -*-
import os
import time
import threading
import logging
import requests
import json
import random
from DrissionPage import ChromiumPage, ChromiumOptions

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - [%(thread)d:%(threadName)s] - %(message)s')
logger = logging.getLogger(__name__)

class BrowserInstance:
    """浏览器实例类，用于跟踪每个浏览器的使用情况"""
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.page = None
        self.tab_open_times = []  # 记录标签页打开的时间
        self.lock = threading.Lock()  # 用于线程安全
        logger.info(f"[浏览器实例-初始化] 创建浏览器实例 {instance_id}")
        self.init_browser(instance_id)
    
    def init_browser(self, instance_id):
        """初始化浏览器实例"""
        try:
            logger.info(f"[浏览器实例-配置] 开始配置浏览器实例 {instance_id}")
            # 使用最基本的配置，让DrissionPage自动处理浏览器启动
            browser_path = ""
            if os.name == 'posix':  # Linux 系统
                browser_path = r"/opt/google/chrome/google-chrome"  # 或者 "/usr/bin/chromium-browser"
                logger.info(f"[浏览器实例-配置] Linux系统，使用浏览器路径: {browser_path}")
            elif os.name == 'nt':  # Windows 系统
                browser_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                logger.info(f"[浏览器实例-配置] Windows系统，使用浏览器路径: {browser_path}")
            co = ChromiumOptions().set_paths(browser_path=browser_path)
            co.headless(False)
            co.incognito(False)  # 匿名模式
            co.set_argument('--ignore_https_errors')
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-dev-shm-usage')
            debug_port = 9222 + instance_id
            co.set_argument(f"--remote-debugging-port={debug_port}")
            co.set_argument("--disable-web-security")
            co.set_argument("--allow-running-insecure-content")
            co.set_argument('--ignore-certificate-errors', True)
            # 生成10000-65535范围内的随机端口
            random_port = random.randint(10000, 65535)
            logger.info(f"[浏览器实例-配置] 实例 {instance_id} 使用随机端口: {random_port}")
            co.set_local_port(random_port)
            
            logger.info(f"[浏览器实例-代理] 实例 {instance_id} 开始获取代理服务器")
            proxy_server = self.get_proxy_from_api()
            if proxy_server:
                co.set_proxy(proxy_server)
                logger.info(f"[浏览器实例-代理] 实例 {instance_id} 成功设置代理服务器: {proxy_server}")
            else:
                logger.warning(f"[浏览器实例-代理] 实例 {instance_id} 未获取到有效代理，继续无代理访问")
            co.ignore_certificate_errors()
            
            logger.info(f"[浏览器实例-启动] 实例 {instance_id} 开始启动浏览器")
            # 不指定端口，让库自动分配
            self.page = ChromiumPage(co, timeout=90)
            logger.info(f"[浏览器实例-导航] 实例 {instance_id} 导航到检测页面")
            self.page.get("https://2025.ip138.com")
            logger.info(f"[浏览器实例-初始化] 浏览器实例 {self.instance_id} 初始化成功")
        except Exception as e:
            logger.error(f"[浏览器实例-初始化] 浏览器实例 {self.instance_id} 初始化失败: {e}")
            self.page = None
    
    def can_open_tab(self):
        """检查是否可以打开新标签页（1分钟内不超过2次）"""
        with self.lock:
            current_time = time.time()
            # 清理1分钟前的记录
            self.tab_open_times = [t for t in self.tab_open_times if current_time - t < 60]
            result = len(self.tab_open_times) < 2
            logger.debug(f"[浏览器实例-检查] 实例 {self.instance_id} 可打开标签页: {result}, 当前打开次数: {len(self.tab_open_times)}")
            return result
    
    def get_wait_time(self):
        """获取需要等待的时间（如果都超过2次）"""
        with self.lock:
            if not self.tab_open_times or len(self.tab_open_times) < 2:
                return 0
            # 找出最早的记录，计算还需要等待多久
            sorted_times = sorted(self.tab_open_times)
            if len(sorted_times) >= 2:
                oldest_time = sorted_times[0]  # 最早的记录
                wait_time = 60 - (time.time() - oldest_time)
                logger.debug(f"[浏览器实例-等待] 实例 {self.instance_id} 需要等待: {max(0, wait_time):.2f}秒")
                return max(0, wait_time)
            return 0
    
    def record_tab_open(self):
        """记录标签页打开时间"""
        with self.lock:
            self.tab_open_times.append(time.time())
            logger.debug(f"[浏览器实例-记录] 实例 {self.instance_id} 记录标签页打开，当前打开次数: {len(self.tab_open_times)}")
    
    def close(self):
        """关闭浏览器实例"""
        try:
            if self.page:
                self.page.quit()
                logger.info(f"[浏览器实例-关闭] 浏览器实例 {self.instance_id} 关闭成功")
        except Exception as e:
            logger.error(f"[浏览器实例-关闭] 浏览器实例 {self.instance_id} 关闭失败: {e}")

    def get_proxy_from_api(self, max_retries=3, retry_interval=2):
        """通过代理服务器API获取代理地址（带重试机制）"""
        api_url = "https://share.proxy.qg.net/get?key=3L6TDGM5"
        instance_info = f"[浏览器实例-{self.instance_id}-代理获取]"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"{instance_info} 正在从API获取代理地址 (尝试 {attempt + 1}/{max_retries}): {api_url}")
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"{instance_info} API返回结果: {data}")
                    
                    # 检查返回状态
                    if data.get("code") == "SUCCESS" and data.get("data") and len(data["data"]) > 0:
                        server = data["data"][0].get("server")
                        if server:
                            logger.info(f"{instance_info} 成功获取到代理服务器: {server}")
                            return server
                        else:
                            logger.error(f"{instance_info} 错误: 返回数据中没有server字段")
                    else:
                        logger.error(f"{instance_info} 错误: API返回失败，状态码: {data.get('code')}")
                else:
                    logger.error(f"{instance_info} 错误: 请求失败，HTTP状态码: {response.status_code}")
                    # 打印响应内容，看看服务器返回了什么错误信息
                    try:
                        error_data = response.json()
                        logger.error(f"{instance_info} 错误详情: {error_data}")
                    except:
                        logger.error(f"{instance_info} 错误详情: {response.text}")
            
            except json.JSONDecodeError:
                logger.error(f"{instance_info} 错误: API返回的不是有效的JSON格式")
            except requests.Timeout:
                logger.error(f"{instance_info} 错误: 请求超时")
            except Exception as e:
                logger.error(f"{instance_info} 获取代理地址时发生错误: {type(e).__name__}: {e}")
            
            # 如果不是最后一次尝试，就等待一段时间后重试
            if attempt < max_retries - 1:
                logger.info(f"{instance_info} {retry_interval}秒后重试...")
                time.sleep(retry_interval)
        
        logger.warning(f"{instance_info} 所有重试都失败了，未获取到可用代理")
        return None

class BrowserPool:
    """浏览器实例池"""
    def __init__(self, pool_size=3):
        self.pool_size = pool_size
        self.browser_instances = []
        self.lock = threading.Lock()
        logger.info(f"[浏览器池-初始化] 创建浏览器实例池，池大小: {pool_size}")
        self.init_pool()
    
    def init_pool(self):
        """初始化浏览器实例池"""
        # 不指定浏览器路径，让DrissionPage自动查找
        logger.info(f"[浏览器池-初始化] 开始初始化浏览器实例池，计划创建 {self.pool_size} 个实例")
        
        # 初始化浏览器实例
        for i in range(self.pool_size):
            logger.info(f"[浏览器池-初始化] 创建第 {i+1}/{self.pool_size} 个浏览器实例")
            browser_instance = BrowserInstance(i+1)  # 从1开始编号
            if browser_instance.page:
                self.browser_instances.append(browser_instance)
                logger.info(f"[浏览器池-初始化] 第 {i+1} 个浏览器实例创建成功")
            else:
                logger.error(f"[浏览器池-初始化] 第 {i+1} 个浏览器实例创建失败")
            # 添加短暂延迟，避免同时启动多个浏览器导致冲突
            time.sleep(1)
        
        logger.info(f"[浏览器池-初始化] 浏览器实例池初始化完成，可用实例数: {len(self.browser_instances)}")
    
    def get_browser_instance(self):
        """获取可用的浏览器实例"""
        thread_info = f"[浏览器池-分配] 线程 {threading.current_thread().name}"
        attempt = 1
        
        while True:
            with self.lock:
                # 优先选择1分钟内打开次数少于2次的实例
                available_instances = [inst for inst in self.browser_instances if inst.can_open_tab()]
                if available_instances:
                    # 选择打开次数最少的实例
                    selected = min(available_instances, key=lambda x: len(x.tab_open_times))
                    selected.record_tab_open()
                    logger.info(f"{thread_info} 成功获取浏览器实例 {selected.instance_id}，当前实例打开标签数: {len(selected.tab_open_times)}")
                    return selected
                
                # 所有实例都超过限制，计算需要等待的时间
                wait_times = [inst.get_wait_time() for inst in self.browser_instances]
                wait_time = min(wait_times)
            
            logger.warning(f"{thread_info} 所有浏览器实例都达到使用限制，等待 {wait_time:.2f} 秒后重试 (尝试 {attempt})")
            time.sleep(min(wait_time, 10))  # 最多等待10秒，然后重新检查
            attempt += 1
    
    def close_all(self):
        """关闭所有浏览器实例"""
        logger.info(f"[浏览器池-关闭] 开始关闭所有浏览器实例，总计 {len(self.browser_instances)} 个实例")
        for i, instance in enumerate(self.browser_instances):
            logger.info(f"[浏览器池-关闭] 正在关闭浏览器实例 {i+1}/{len(self.browser_instances)}")
            instance.close()
        self.browser_instances.clear()
        logger.info(f"[浏览器池-关闭] 所有浏览器实例已关闭")