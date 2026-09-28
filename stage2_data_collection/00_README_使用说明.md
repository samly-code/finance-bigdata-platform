# 项目一 · 阶段② 数据采集 —— 使用说明

> 目标：用 Python 爬虫抓取 **A股日线行情 + LPR 利率**，写入 niit 虚拟机 MySQL，
> 再用 Sqoop 把数据导入 HDFS，为阶段③ Hive 数仓分析备好数据。
> 完整链路：`爬虫 → MySQL → Sqoop → HDFS`

---

## 一、前置条件（先检查，缺一不可）

| 检查项 | 怎么做 | 成功标志 |
|---|---|---|
| 1. 三台虚拟机已开机 | VMware 里启动 niit / niit02 / niit03 | 能 ping 通 192.168.65.101 |
| 2. MySQL 已启动（niit 上） | MobaXterm 连 niit：`systemctl status mysqld` | active (running) |
| 3. Windows 能连 niit 的 MySQL | 见下方「MySQL 远程访问授权」 | 能连上 |
| 4. Hadoop 集群已启动（Sqoop 才需要） | 按检查清单顺序启动 ZK → HDFS → YARN | 9870 网页能打开 |

### MySQL 远程访问授权（重要，只做一次）
niit 上执行（root 登录 MySQL 后）：
```sql
-- 允许 root 从任意主机远程登录（密码换成你自己的）
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY '你的MySQL密码' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```
> 说明：默认 MySQL 只允许 localhost 登录，Windows 爬虫是"另一台机器"，必须开远程权限。

## 二、Windows 本地安装依赖

打开命令行（cmd 或 PyCharm 终端），用**你的 Python 环境**执行：
```bash
pip install -r requirements.txt
```
requirements.txt 内容：
```
akshare>=1.12.0     # 免费金融数据接口库（A股、LPR）
pymysql>=1.1.0      # Python 连接 MySQL 的驱动
```

> 提示：akshare 依赖较多，首次安装可能 1-2 分钟，耐心等。

## 三、执行顺序（按编号一步步来）

| 步骤 | 命令 | 在哪台机器 | 干什么 |
|---|---|---|---|
| 1 | `mysql -u root -p < 01_mysql_init.sql` | **niit 虚拟机** | 建库建表 |
| 2 | `python 02_crawl_stock.py` | **Windows 本地** | 爬 A股日线写 MySQL |
| 3 | `python 03_crawl_lpr.py` | **Windows 本地** | 爬 LPR 写 MySQL |
| 4 | `bash 04_sqoop_import.sh` | **niit 虚拟机** | MySQL → HDFS 全量+增量 |
| 5 | 验证（见下） | Windows / niit | 确认数据到位 |

## 四、每步怎么验证（不要跳过）

### 验证① 表建好了
```sql
USE finance_db;
SHOW TABLES;                      -- 应看到 daily_quote、lpr_rate 两张表
DESC daily_quote;                 -- 看表结构
```

### 验证② 爬虫写入成功
```sql
SELECT COUNT(*) FROM daily_quote;   -- 应 > 0
SELECT * FROM daily_quote LIMIT 5;  -- 看前 5 行数据长什么样
SELECT COUNT(*) FROM lpr_rate;      -- 应 > 0
```

### 验证③ Sqoop 导入成功
```bash
hdfs dfs -ls /finance/daily_quote       # 应看到 part-m-00000 文件
hdfs dfs -cat /finance/daily_quote/part-m-00000 | head -5   # 看前 5 行
hdfs dfs -ls /finance/lpr_rate          # LPR 目录
```

## 五、常见问题排查

| 现象 | 原因 | 解决办法 |
|---|---|---|
| `ModuleNotFoundError: akshare` | 依赖没装 | `pip install -r requirements.txt` |
| `Can't connect to MySQL server on '192.168.65.101'` | MySQL 没开远程权限 / 防火墙 | 执行第一节授权 SQL；或检查防火墙：`firewall-cmd --add-port=3306/tcp --permanent && firewall-cmd --reload` |
| 爬虫报接口异常/字段为空 | akshare 接口偶尔变动 | 看报错提示换备选接口（见代码注释） |
| Sqoop 报 driver 找不到 | 缺 mysql-connector-java | 下载 jar 放到 `/training/sqoop/lib/` |
| 爬虫很慢 | 逐只股票爬 | 演示就用 3-5 只；扩展全量见 README 第六节 |

## 六、扩展成全部 A 股（可选，进阶）

演示代码只爬 3-5 只股票，先跑通链路。
想抓全部 A 股，在 `02_crawl_stock.py` 顶部把 `STOCK_LIST` 换成：
```python
import akshare as ak
# 获取全部 A 股代码列表（约 5000+ 只）
df_list = ak.stock_zh_a_spot_em()
STOCK_LIST = df_list['代码'].tolist()
```
> ⚠️ 全量爬取会很慢（几千只 × 每只请求一次），建议先用演示名单跑通，再决定是否扩展。

## 七、安全提示

- 所有脚本里 MySQL 密码都留了占位符，**请改成你自己的密码**，不要提交到公共仓库。
- 本项目数据仅用于学习研究，请遵守数据源的使用规范。
