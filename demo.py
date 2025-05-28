from DrissionPage import ChromiumPage, ChromiumOptions
from urllib.parse import urlparse, parse_qs
#
# try:
#     co = ChromiumOptions().set_paths(browser_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
#     # co.set_argument("--remote-debugging-port=9222")
#     co.headless(False)  # 确保浏览器可见
#     page = ChromiumPage(co)
#     print("浏览器已启动，标题：", page.title)
#
#     tab1 = page.new_tab('https://www.baidu.com')
#     tab2 = page.new_tab('https://xyy.jxschot.com/mobile-template/index.html?goodsCode=WDDX205G')
#     # 请求回调函数
#     def handle_request(request):
#         print(f"请求 URL: {request.url}")
#         print(f"请求方法: {request.method}")
#         print(f"请求头: {request.headers}")
#         print("-" * 60)
#     # 响应回调函数
#     def handle_response(request, response):
#         print(f"响应 URL: {request.url}")
#         print(f"状态码: {response.status_code}")
#         print(f"响应头: {response.headers}")
#         print(f"响应内容: {response.text[:200]}...")  # 只打印前200字符
#         print("=" * 60)
#
#     tab2.listen.start('/getSms')  # 启动监听器
#     ele = tab2.ele('#phone')
#     # 输入对文本框输入账号
#     ele.input('13058122955')
#     # 定位到密码文本框并输入密码
#     # page.ele('#user_password').input('123456')
#     # 点击登录按钮
#     ele1 = tab1.ele('#kw')
#     # 输入对文本框输入账号
#     ele1.input('哈哈哈')
#
#     tab2.ele('#get_verify_code').click()
#
#
#     # 监听所有请求和响应
#     res = tab2.listen.wait()
#     print(f"响应头: {res.response.body}")
#
# except Exception as e:
#     print(f"发生错误：{e}")

if __name__ == '__main__':


    co = ChromiumOptions().set_paths(browser_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    # co.set_argument("--remote-debugging-port=9222")
    co.headless(False)  # 确保浏览器可见
    page = ChromiumPage(co)
    print("浏览器已启动，标题：", page.title)
    tab1 = page.new_tab('https://xyy.jxschot.com/mobile-template/index.html?p=D8043BE088B8A92B1BDFF97496EA1F007F5BA585D8E5AE6655FD4B2ED9731C9D&a=1')
    print(tab1.url)

    # 解析 URL
    for tab in page.get_tabs():
        if "a=1" in str(tab.url):
            url = tab.url
            parsed_url = urlparse(url)
            # 获取查询参数
            query_params = parse_qs(parsed_url.query)
            # 提取 p 的值
            p_value = query_params.get('p', [None])[0]
            print(p_value)