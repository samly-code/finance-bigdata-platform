-- =====================================================================
-- 项目一 · 阶段② 第 1 步：MySQL 初始化（建库建表）
-- 作用：在 niit 虚拟机的 MySQL 里创建业务库 finance_db 和两张业务表
-- 执行位置：niit 虚拟机（MobaXterm 里）
-- 执行命令：mysql -u root -p < 01_mysql_init.sql
--          （回车后会提示输入 MySQL root 密码，输完回车即可）
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. 创建业务数据库 finance_db
--    IF NOT EXISTS：库已存在时不会报错（脚本可以重复执行）
--    utf8mb4：支持中文的字符集（股票名称里有中文）
-- ---------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS finance_db DEFAULT CHARSET utf8mb4;

-- 进入 finance_db 库，后面的建表都建在这个库里
USE finance_db;

-- ---------------------------------------------------------------------
-- 2. 创建「A股日线行情表」daily_quote
--    存什么：爬虫抓到的每只股票、每个交易日的行情（开高低收、量额）
--    字段设计要点：
--      id          自增主键，Sqoop 增量导入时用 id 判断"哪些是新数据"
--      stock_code + trade_date 唯一键，防止同一只股票同一天重复入库
--      DECIMAL     金额/价格用定点数，不用 FLOAT（避免精度丢失）
--      COMMENT     每个字段都写注释，方便以后看表结构
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_quote (
    id          BIGINT         NOT NULL AUTO_INCREMENT COMMENT '自增主键（Sqoop增量靠它）',
    stock_code  VARCHAR(10)    NOT NULL COMMENT '股票代码，如 600519',
    stock_name  VARCHAR(50)    DEFAULT NULL COMMENT '股票名称，如 贵州茅台',
    trade_date  DATE           NOT NULL COMMENT '交易日期',
    open_price  DECIMAL(10,2)  NOT NULL COMMENT '开盘价',
    high_price  DECIMAL(10,2)  NOT NULL COMMENT '最高价',
    low_price   DECIMAL(10,2)  NOT NULL COMMENT '最低价',
    close_price DECIMAL(10,2)  NOT NULL COMMENT '收盘价',
    volume      BIGINT         NOT NULL COMMENT '成交量（手）',
    amount      DECIMAL(20,2)  NOT NULL COMMENT '成交额（元）',
    create_time DATETIME       DEFAULT CURRENT_TIMESTAMP COMMENT '数据入库时间',
    PRIMARY KEY (id),                          -- 主键：唯一标识每一行
    UNIQUE KEY uk_code_date (stock_code, trade_date)  -- 唯一键：同股同日只允许一行
) ENGINE=InnoDB COMMENT='A股日线行情表';

-- ---------------------------------------------------------------------
-- 3. 创建「LPR 利率表」lpr_rate
--    存什么：中国人民银行每月公布的贷款市场报价利率（1年期、5年期以上）
--    用途：阶段③ Hive 里做利率趋势分析；项目六利率预测 Web 也复用这张表
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lpr_rate (
    id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '自增主键',
    lpr_date    DATE         NOT NULL COMMENT '公布日期',
    lpr_1y      DECIMAL(5,3) NOT NULL COMMENT '1年期LPR（%）',
    lpr_5y      DECIMAL(5,3) NOT NULL COMMENT '5年期以上LPR（%）',
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '数据入库时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_date (lpr_date)              -- 同一公布日期只存一条
) ENGINE=InnoDB COMMENT='贷款市场报价利率(LPR)表';

-- ---------------------------------------------------------------------
-- 4. 验证：显示当前库的所有表，确认两张表都建成功
-- ---------------------------------------------------------------------
SHOW TABLES;
