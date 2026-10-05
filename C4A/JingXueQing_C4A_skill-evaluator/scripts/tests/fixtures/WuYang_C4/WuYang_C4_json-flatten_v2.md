---
name: json-flatten
description: 展开嵌套 JSON（v2 修复数组处理）
---

# json-flatten v2

**输入**：JSON 文件路径（.json）
**输出**：扁平化后的 JSON 文件路径（.json）

## 安装
```bash
pip install json5
```

## 环境要求
Python 3.9+，依赖 json5

## 使用步骤
1. `python3 flatten.py in.json -o out.json`

## 预期结果
v2 相对 v1 的改进：数组元素正确展开为 `a.0.b`，并新增 --indent 参数
