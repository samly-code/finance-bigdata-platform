# -*- coding: utf-8 -*-
"""
项目一 · 阶段② 第 3 步：LPR 利率爬虫
============================================
干什么：抓取中国人民银行公布的 LPR（贷款市场报价利率）历史数据，
        写入 niit 虚拟机 MySQL 的 lpr_rate 表
跑在哪：Windows 本地
怎么跑：python 03_crawl_lpr.py
依赖：   akshare + pymysql（和 02 一样）

和 02_crawl_stock.py 的差别：
    - 02 是"多只股票 × 每天一行"的明细表
    - 03 是"每个公布日期一行"的利率表（一个月才公布一次，数据量很小）
    - 核心流程完全一样：连库 → 抓数 → 入库 → 汇报
"""

# ============================================================
# 第 0 步：导入库
# ============================================================
import time          # 控制节奏
import pymysql       # MySQL 驱动
import akshare as ak # 金融数据接口

# ============================================================
# 第 1 步：配置区（和 02 保持一致，密码同样改成你自己的）
# ============================================================
MYSQL_HOST = "192.168.65.101"    # niit 的 IP
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "你的MySQL密码"   # ⚠️ 改成你自己的
MYSQL_DB = "finance_db"

# ============================================================
# 第 2 步：连接 MySQL（和 02 相同，不再重复解释）
# ============================================================
try:
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset="utf8mb4",
        autocommit=True,
    )
    print(f"[OK] 已连接 MySQL：{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
except Exception as e:
    print(f"[失败] 连不上 MySQL：{e}")
    exit(1)

cursor = conn.cursor(pymysql.cursors.DictCursor)

# ============================================================
# 第 3 步：抓 LPR 数据并写入 MySQL
# ============================================================
def crawl_lpr():
    """
    抓取 LPR 历史数据写入 lpr_rate 表。
    返回：写入行数
    """
    print("\n>>> 正在抓取 LPR 历史数据...")

    # ---------- 3.1 用 akshare 抓数据 ----------
    # macro_china_lpr：中国 LPR 历史数据接口（数据来自中国人民银行官网口径）
    # 返回 DataFrame，通常包含：日期 / 1年期LPR / 5年期以上LPR
    try:
        df = ak.macro_china_lpr()
    except Exception as e:
        print(f"[失败] LPR 数据抓取失败：{e}")
        print("       akshare 接口偶尔调整，若报错请换用备选接口：")
        print("       ak.macro_china_lpr()  →  检查 akshare 版本是否最新：pip install -U akshare")
        return 0

    if df is None or df.empty:
        print("[失败] LPR 接口返回空数据")
        return 0

    # 打印列名，方便确认接口返回的字段（版本不同列名可能略有差异）
    print(f"[抓取] LPR 接口返回 {len(df)} 条记录，字段：{list(df.columns)}")

    # ---------- 3.2 写入 MySQL ----------
    # 同样用 ON DUPLICATE KEY UPDATE：同一公布日期重复抓取时更新不报错
    insert_sql = """
        INSERT INTO lpr_rate (lpr_date, lpr_1y, lpr_5y)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            lpr_1y = VALUES(lpr_1y),
            lpr_5y = VALUES(lpr_5y)
    """

    saved = 0
    for _, row in df.iterrows():
        # 列名按 akshare 常规返回：日期 / 1年期LPR / 5年期以上LPR
        # 如果接口列名不同，把下面三个 row[...] 里的中文换成实际列名
        params = (
            str(row["日期"]),            # 公布日期
            float(row["1年期LPR"]),      # 1 年期 LPR（%）
            float(row["5年期以上LPR"]),  # 5 年期以上 LPR（%）
        )
        try:
            cursor.execute(insert_sql, params)
            saved += 1
        except Exception as e:
            print(f"    [警告] 日期 {row['日期']} 写入失败：{e}")

    print(f"[完成] LPR 写入 {saved} 条记录")
    return saved


# ============================================================
# 第 4 步：主流程
# ============================================================
def main():
    print("=" * 55)
    print("LPR 利率爬虫开始")
    print("=" * 55)

    total = crawl_lpr()

    print("\n" + "=" * 55)
    print(f"全部完成！共写入 {total} 条 LPR 记录")
    print("下一步验证：在 niit 上执行")
    print("    USE finance_db; SELECT * FROM lpr_rate ORDER BY lpr_date DESC LIMIT 5;")
    print("=" * 55)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
