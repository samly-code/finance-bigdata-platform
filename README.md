# 金融大数据全链路平台（Finance BigData Platform）

基于 Hadoop 生态自建的金融数据全链路平台，用于学习与简历项目展示。
从真实数据源采集 A 股行情与 LPR 利率，跑通 **采集 → 存储 → 数仓分析 → 快速查询 → 实时流** 完整链路。

## 技术栈

- **集群**：Hadoop 3.3.0（HDFS + YARN）、Hive 2.3.8、HBase 2.2.4、Sqoop、Kafka 0.10.2.1、Flume、ZooKeeper、MySQL
- **开发**：Python 3（akshare / pymysql）、Java、Scala、SpringBoot、MATLAB、Ollama
- **环境**：三节点 CentOS7 虚拟机（niit / niit02 / niit03，VMware）

## 7 个项目路线

| # | 项目 | 状态 |
|---|---|---|
| 1 | 金融大数据全链路平台（本项目，底座） | 🔄 进行中（阶段② 数据采集） |
| 2 | 量化策略回测系统（Python） | ⏳ 待启动 |
| 3 | MATLAB 金融时间序列与投资组合优化 | ⏳ 待启动 |
| 4 | Ollama 金融研报智能分析助手（RAG） | ⏳ 待启动 |
| 5 | Scala + Spark 金融数据分析 | ⏳ 待启动 |
| 6 | 利率预测 Web 系统重构（Java 全栈） | ⏳ 待启动 |
| 7 | 上市公司知识图谱问答（Neo4j） | ⏳ 待启动 |

## 项目一 · 阶段进度

- [x] 阶段① 集群环境恢复（三节点 Hadoop 生态验收通过）
- [ ] 阶段② 数据采集（当前）——爬虫 → MySQL → Sqoop → HDFS
- [ ] 阶段③ Hive 数仓离线分析
- [ ] 阶段④ HBase 实时点查
- [ ] 阶段⑤ Kafka + Flume 实时数据链路

## 目录结构

```
finance-bigdata-platform/
├── README.md                 # 项目总览（本文件）
├── stage2_data_collection/   # 阶段② 数据采集
│   ├── 00_README_使用说明.md    # 使用说明（前置条件/执行顺序/验证）
│   ├── 01_mysql_init.sql       # MySQL 建库建表
│   ├── 02_crawl_stock.py       # A股日线爬虫（akshare → MySQL）
│   ├── 03_crawl_lpr.py         # LPR 利率爬虫（akshare → MySQL）
│   ├── 04_sqoop_import.sh      # Sqoop 全量/增量导入 HDFS
│   └── requirements.txt        # Python 依赖
└── (后续阶段代码陆续加入)
```

## 使用说明

详见 [`stage2_data_collection/00_README_使用说明.md`](stage2_data_collection/00_README_使用说明.md)。

## 安全提示

- 仓库内所有脚本的数据库密码均为**占位符**，请在使用时替换为自己的密码，**切勿将真实密码提交到仓库**。
- 本项目数据仅用于学习研究，请遵守数据源使用规范。
