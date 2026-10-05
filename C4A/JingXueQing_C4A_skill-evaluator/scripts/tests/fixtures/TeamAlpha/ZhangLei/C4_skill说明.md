---
name: git-summary
description: 汇总 git 提交历史
---

# git-summary

**输入**：一个 git 仓库路径
**输出**：提交统计 Markdown 报告

## 安装
无需安装，依赖 git 与 Python 3.8+

## 使用步骤
```bash
python3 summary.py /path/to/repo
```

## 预期结果
输出 commit 数、作者数、最近 10 条提交
