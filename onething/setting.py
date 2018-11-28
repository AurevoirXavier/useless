# 账号文件的名字
ACCOUNTS = 'accounts.txt'
# 记录文件的名字
WORKER = '1'
# 指定兑换日期
DATE = '20181115'
# 策略, 1 优先账号, 2 优先卡
PLAN = 2
# 支付方式, 1 兑换完立刻支付, 2 最后支付
PAY = 1
# 自动导出, True 开启, False 关闭, 仅在支付方式 1 下生效
EXPORT = False
# 手动配置代理, 仅兑换时生效
MANUAL_PROXY = {
    'http': '1.20.103.71:47363',
    'https': '1.20.103.71:47363'
}
# 是否全局代理, True 开启, False 关闭, 仅兑换时生效
PROXY = False
# 私钥文件夹, 请以钱包地址命名私钥文件
UTCS_PATH = 'utcs/'
# 钱包通用密码
PASSWD = '123456789'
# 翻墙代理地址, 仅启用支付功能时生效
PROXIES = {
    'http': '127.0.0.1:1087',
    'https': '127.0.0.1:1087'
}
# 兑换的种类, 顺序可调, 不需要的请注释掉, 切勿修改后面为 False
AVAILABLE = {
    '年': True,
    '半年': True,
    '钻年': True,
    '季': True,
    '月': True,
    '周': True,
    # '钻': True,
}
