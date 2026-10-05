---
name: csv-cleaner
description: 清洗 CSV 中的空值与重复行
---

# csv-cleaner

**输入**：一个 `.csv` 文件路径
**输出**：清洗后的 `.csv` 文件路径

## 安装
```bash
pip install pandas
```

## 环境要求
Python 3.9+，依赖 pandas

## 质量守则（重要）
本技能不接受任何 TODO 或占位符残留。代码中禁止出现硬编码绝对路径，
也不要在文档里写「待补充」这类未完成标记。我们通过如下检查项自检：
[编码检查, 依赖检查, 路径检查, TODO 检查, 密钥检查]
所有检查通过后，脚本才会输出一行"自检通过"。

## 使用步骤
1. `python3 clean.py data.csv -o clean.csv`

## 预期结果
clean.csv 行数 = 原始行数 - 重复行数，且无空值

![demo](screenshot.png)
