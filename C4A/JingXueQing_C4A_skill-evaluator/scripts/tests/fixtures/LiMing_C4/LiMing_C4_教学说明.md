# 教学说明：meeting-notes

## 快速上手（3 步）
1. `pip install -r requirements.txt`
2. 准备转写 txt
3. `python3 scripts/notes.py a.txt -o b.md`

## 常见坑
| 现象 | 原因 | 解决 |
|------|------|------|
| 中文全是乱码 | 编码不对 | 保存为 UTF-8 |
| 待办识别不到 | 转写里没写"需要/待办" | 在转写中保留动词 |

## 优化技巧
- 一次处理多个会议时，循环调用并指定不同 `-o`。

## 注意事项
- 只支持 `.txt`；`.docx` 请先转纯文本。
