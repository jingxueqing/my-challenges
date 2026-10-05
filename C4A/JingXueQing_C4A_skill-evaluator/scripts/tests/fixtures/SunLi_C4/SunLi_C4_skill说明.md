---
name: log-analyzer
description: 分析服务器日志找错误
---

# log-analyzer

**输入**：服务器日志文件路径
**输出**：错误统计报告（Markdown）

## 安装
把 log_analyzer.py 放到 /Users/sunli/tools/ 目录下，然后 pip install requests

## 环境要求
Python 3.8+，需要 requests 库

## 使用步骤
1. 修改脚本里的 LOG_PATH = "/Users/sunli/logs/app.log"
2. 运行 `python3 log_analyzer.py`

## 预期结果
生成 report.md，含错误类型统计表
