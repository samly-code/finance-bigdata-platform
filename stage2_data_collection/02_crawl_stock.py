# -*- coding: utf-8 -*-
"""
项目一 · 阶段② 第 2 步：A股日线行情爬虫
============================================
干什么：从免费数据源抓取 A 股日线行情，写入 niit 虚拟机 MySQL 的 daily_quote 表
跑在哪：Windows 本地（PyCharm 或命令行）
怎么跑：python 02_crawl_stock.py
依赖：   pip install -r requirements.txt （akshare + pymysql）

整体思路（四步）：
    ① 准备：配置 MySQL 连接信息、要爬的股票名单
    ② 抓数：用 akshare 免费接口拿某只股票的历史日线
    ③ 入库：把抓到的每一行写入 MySQL（同股同日自动跳过，不重复）
    ④ 汇报：打印成功/跳过/失败数量，让你知道发生了什么

⚠️ 密码安全：脚本里的 MySQL 密码是占位符，运行前改成你自己的密码。
"""

# ============================================================
# 第 0 步：导入需要用到的库
# ============================================================
import time          # 标准库：time.sleep() 用来控制爬取节奏（别把接口打爆）
import pymysql       # 第三方库：Python 连接 MySQL 的驱动
import akshare as ak # 第三方库：免费金融数据接口（新浪/东财数据源）

# ============================================================
# 第 1 步：配置区（每次换环境/换密码，只改这里）
# ============================================================

# --- MySQL 连接信息（niit 虚拟机的 MySQL）---
MYSQL_HOST = "192.168.65.101"   # niit 的 IP
MYSQL_PORT = 3306               # MySQL 默认端口
MYSQL_USER = "root"             # 用户名
MYSQL_PASSWORD = "你的MySQL密码"  # ⚠️ 改成你自己的 root 密码
MYSQL_DB = "finance_db"         # 库名（01_mysql_init.sql 里建的）

# --- 演示股票名单（先跑通链路，只用 3 只）---
# 元组里每个元素是 (股票代码, 股票名称)
# 想加股票，按同样格式往列表里加一行即可
STOCK_LIST = [
    ("600519", "贵州茅台"),
    ("601318", "中国平安"),
    ("000001", "平安银行"),
]

# --- 爬取参数 ---
START_DATE = "20230101"   # 起始日期（含），格式 YYYYMMDD
END_DATE   = "20231231"   # 结束日期（含），格式 YYYYMMDD
SLEEP_SEC  = 1.5          # 每只股票抓完休息 1.5 秒，防止请求过快被封

# ============================================================
# 第 2 步：连接 MySQL
# ============================================================
# connect() 会真的去连 niit 的 MySQL，连不上会抛异常，下面的 try 捕获并提示
try:
    conn = pymysql.connect(
        host=MYSQL_HOST,          # 目标主机
        port=MYSQL_PORT,          # 端口
        user=MYSQL_USER,          # 用户名
        password=MYSQL_PASSWORD,  # 密码
        database=MYSQL_DB,        # 数据库
        charset="utf8mb4",        # 字符集，和建库时保持一致（支持中文）
        autocommit=True,          # 每条 SQL 执行完自动提交，不用手动 commit
    )
    print(f"[OK] 已连接 MySQL：{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
except Exception as e:
    print(f"[失败] 连不上 MySQL，请检查：")
    print(f"       1. niit 虚拟机是否开机、MySQL 是否启动")
    print(f"       2. 是否执行过『远程访问授权』（见 README 第一节）")
    print(f"       3. 密码是否正确")
    print(f"       原始错误：{e}")
    exit(1)   # 连接失败直接退出，不往下走

# 游标：执行 SQL 的"手"。pymysql.cursors.DictCursor 让查询结果以字典形式返回，
# 方便用列名取值（row["trade_date"] 而不是 row[0]）
cursor = conn.cursor(pymysql.cursors.DictCursor)

# ============================================================
# 第 3 步：定义「抓一只股票 + 写 MySQL」的函数
# ============================================================
def crawl_and_save_one(code, name):
    """
    抓取单只股票的历史日线，写入 daily_quote 表。
    参数 code: 股票代码（如 "600519"）
    参数 name: 股票名称（如 "贵州茅台"）
    返回：本只股票新增写入的行数
    """
    print(f"\n>>> 正在处理：{name} ({code})")

    # ---------- 3.1 用 akshare 抓数据 ----------
    # stock_zh_a_hist：东方财富数据源的个股历史行情接口
    # 参数含义：
    #   symbol   = 股票代码
    #   period   = "daily" 日线（可选 weekly 周线 / monthly 月线）
    #   start_date / end_date = 起止日期
    #   adjust   = "qfq" 前复权（复权=把分红送股折算进价格，更贴近真实收益）
    # 返回的是 pandas DataFrame（一张表：日期/开盘/最高/最低/收盘/成交量/成交额...）
    try:
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=START_DATE,
            end_date=END_DATE,
            adjust="qfq",
        )
    except Exception as e:
        print(f"    [跳过] {name} 数据抓取失败：{e}")
        return 0

    # 防御性检查：接口偶尔返回空表（比如停牌期无数据）
    if df is None or df.empty:
        print(f"    [跳过] {name} 没有返回数据（可能停牌或不在区间内）")
        return 0

    print(f"    [抓取] {name} 共 {len(df)} 天数据，开始写入 MySQL...")

    # ---------- 3.2 逐行写入 MySQL ----------
    # 写一条 INSERT 语句，数据变化时自动更新：
    #   INSERT INTO ... VALUES (...) ON DUPLICATE KEY UPDATE ...
    #   ON DUPLICATE KEY：撞到唯一键 uk_code_date（同股同日）时，
    #   不是报错，而是"更新"这一行（价格可能变，比如除权后复权值变化）
    # 这样爬虫重复跑也不会产生重复数据。
    insert_sql = """
        INSERT INTO daily_quote
            (stock_code, stock_name, trade_date,
             open_price, high_price, low_price, close_price,
             volume, amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            stock_name = VALUES(stock_name),
            open_price  = VALUES(open_price),
            high_price  = VALUES(high_price),
            low_price   = VALUES(low_price),
            close_price = VALUES(close_price),
            volume      = VALUES(volume),
            amount      = VALUES(amount)
    """

    saved = 0          # 计数器：实际新增/更新的行数
    for _, row in df.iterrows():   # 遍历 DataFrame 的每一行
        # row 是这一天的行情，列名是 akshare 返回的中文列名
        # 注意 akshare 中文列名：日期/开盘/最高/最低/收盘/成交量/成交额
        # 我们用 VALUES(...) 参数化传值（%s 占位），防止 SQL 注入，也保证类型正确
        params = (
            code,                         # 股票代码
            name,                         # 股票名称
            str(row["日期"]),              # 交易日期（先转字符串，MySQL 自动识别为 DATE）
            float(row["开盘"]),            # 开盘价
            float(row["最高"]),            # 最高价
            float(row["最低"]),            # 最低价
            float(row["收盘"]),            # 收盘价
            int(row["成交量"]),            # 成交量（手）
            float(row["成交额"]),          # 成交额（元）
        )
        try:
            cursor.execute(insert_sql, params)   # 执行 INSERT
            saved += 1                           # 每成功一行计数 +1
        except Exception as e:
            # 某一行失败不中断整只股票，打印出来继续
            print(f"    [警告] 日期 {row['日期']} 写入失败：{e}")

    # autocommit=True 时 execute 即生效，无需手动 commit
    print(f"    [完成] {name} 写入 {saved} 行")
    return saved


# ============================================================
# 第 4 步：主流程 —— 循环处理每一只股票
# ============================================================
def main():
    print("=" * 55)
    print("A股日线行情爬虫开始")
    print(f"股票数量：{len(STOCK_LIST)} 只 | 日期区间：{START_DATE} ~ {END_DATE}")
    print("=" * 55)

    total = 0                       # 全部股票累计写入行数
    for code, name in STOCK_LIST:
        total += crawl_and_save_one(code, name)   # 抓一只、写一只
        time.sleep(SLEEP_SEC)                    # 每只之间休息，别太频繁

    # 收尾汇报
    print("\n" + "=" * 55)
    print(f"全部完成！共写入 {total} 行行情数据")
    print("下一步验证：在 niit 上执行")
    print("    USE finance_db; SELECT COUNT(*) FROM daily_quote;")
    print("=" * 55)

    # 用完要关闭游标和连接（好习惯，释放资源）
    cursor.close()
    conn.close()


# Python 的标准写法：只有"直接运行本文件"时才执行 main()
# 这样以后别人 import 这个文件时不会误触发爬虫
if __name__ == "__main__":
    main()
