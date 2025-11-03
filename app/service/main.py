import time
from app.service.service_manager import start_services, stop_services


if __name__ == "__main__":
    # 启动服务示例
    services = start_services()
    
    try:
        # 保持程序运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # 捕获Ctrl+C，优雅停止服务
        stop_services(services)
        print("程序已退出")