#!/bin/bash
# =====================================================================
# 项目一 · 阶段② 第 4 步：Sqoop 导入脚本（MySQL → HDFS）
# =====================================================================
# 干什么：把 MySQL 里爬好的数据搬到 HDFS，供阶段③ Hive 建表分析
# 跑在哪：niit 虚拟机（MobaXterm 里，注意不是 Windows！）
# 怎么跑：bash 04_sqoop_import.sh
# 前提：  Hadoop 集群已启动（ZK → HDFS → YARN），Sqoop 已安装（仅 niit）
# =====================================================================

# ---------------------------------------------------------------------
# 0. 变量区（改成你自己的 MySQL 密码）
# ---------------------------------------------------------------------
MYSQL_HOST="localhost"            # Sqoop 在 niit 本机跑，直接连 localhost 最快
MYSQL_PORT="3306"
MYSQL_USER="root"
MYSQL_PASSWORD="你的MySQL密码"     # ⚠️ 改成你自己的 MySQL root 密码
MYSQL_DB="finance_db"
HDFS_BASE="/finance"              # HDFS 上的存放根目录

# ---------------------------------------------------------------------
# 1. 全量导入 daily_quote（第一次跑：把整张表搬过去）
# ---------------------------------------------------------------------
# 参数逐个解释：
#   --connect        JDBC 连接串：告诉 Sqoop 连哪个数据库（jdbc:mysql://地址:端口/库名）
#   --username/password 数据库账号密码
#   --table          要导出的表名（Sqoop 自动读表结构）
#   --target-dir     HDFS 上的目标目录（注意：目录已存在会报错，先删）
#   --m 1            用 1 个 mapper 任务（数据量小，1 个够；大表可调大并行）
#   --fields-terminated-by '\t'  列与列之间用制表符分隔（Hive 建表要对应）
#   --delete-target-dir  目标目录存在就先删掉，保证脚本可重复执行
echo "===== [1/3] 全量导入 daily_quote 到 HDFS ====="
hdfs dfs -rm -r -f ${HDFS_BASE}/daily_quote 2>/dev/null   # 清掉旧目录（忽略不存在报错）
sqoop import \
    --connect "jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DB}?useSSL=false&serverTimezone=Asia/Shanghai" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PASSWORD}" \
    --table daily_quote \
    --target-dir ${HDFS_BASE}/daily_quote \
    --m 1 \
    --fields-terminated-by '\t' \
    --delete-target-dir

# ---------------------------------------------------------------------
# 2. 增量导入 daily_quote（第二次及以后跑：只搬新增的数据）
# ---------------------------------------------------------------------
# 原理：Sqoop 记录上次导入的最大 id（保存在 Sqoop 自己的 metastore 里），
#       下次只搬 id 比上次大的新行。
#   --incremental append    增量模式：新数据追加（适合自增 id 这种只增不减的表）
#   --check-column id       用 id 列判断新数据（值一直变大）
#   --last-value            上次的最大 id；不写就默认从 0 开始（相当于全量）
echo "===== [2/3] 增量导入 daily_quote（只会搬新增行）====="
# 演示：这里用 -last-value 0 说明"从 0 开始"；以后真实增量跑，写上次的最大 id 即可
sqoop import \
    --connect "jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DB}?useSSL=false&serverTimezone=Asia/Shanghai" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PASSWORD}" \
    --table daily_quote \
    --target-dir ${HDFS_BASE}/daily_quote_increment \
    --incremental append \
    --check-column id \
    --last-value 0 \
    --m 1 \
    --fields-terminated-by '\t'

# ---------------------------------------------------------------------
# 3. 导入 lpr_rate（数据量小，全量一次搞定）
# ---------------------------------------------------------------------
echo "===== [3/3] 导入 lpr_rate 到 HDFS ====="
hdfs dfs -rm -r -f ${HDFS_BASE}/lpr_rate 2>/dev/null
sqoop import \
    --connect "jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DB}?useSSL=false&serverTimezone=Asia/Shanghai" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PASSWORD}" \
    --table lpr_rate \
    --target-dir ${HDFS_BASE}/lpr_rate \
    --m 1 \
    --fields-terminated-by '\t' \
    --delete-target-dir

# ---------------------------------------------------------------------
# 4. 验证：列出 HDFS 上的结果文件
# ---------------------------------------------------------------------
echo ""
echo "===== 验证：HDFS 上的文件 ====="
hdfs dfs -ls ${HDFS_BASE}/daily_quote
hdfs dfs -ls ${HDFS_BASE}/lpr_rate
echo ""
echo "===== daily_quote 前 5 行内容 ====="
hdfs dfs -cat ${HDFS_BASE}/daily_quote/part-m-00000 2>/dev/null | head -5
echo ""
echo "===== 全部完成！下一步进入阶段③：Hive 建表分析 ====="
