---
name: pdf-splitter
description: 按页码区间拆分 PDF
---

# pdf-splitter

**输入**：一个 PDF 文件路径 + 起止页码
**输出**：拆分后生成的多个 PDF 文件

## 安装
```bash
pip install pypdf
```

## 环境要求
Python 3.9+，依赖 pypdf

## 使用步骤
1. `python3 split.py input.pdf 1 3 -o out/`
2. 查看 out/ 下的分片

## 预期结果
生成 out/input_p1-3.pdf，页数 = 结束页 - 起始页 + 1
