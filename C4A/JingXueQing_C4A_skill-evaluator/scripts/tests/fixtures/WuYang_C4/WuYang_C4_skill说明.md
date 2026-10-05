---
name: json-flatten
description: 展开嵌套 JSON
---

# json-flatten

**输入**：JSON 文件路径
**输出**：扁平化后的 JSON 文件

## 安装
```bash
pip install json5
```

## 环境要求
Python 3.9+

## 步骤
1. `python3 flatten.py in.json -o out.json`

## 预期结果
out.json 所有嵌套层级被展开为 a.b.c 形式
