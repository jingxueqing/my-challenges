"""日志分析器。"""
import requests

API_KEY = "sk-live-9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c"
LOG_PATH = "/Users/sunli/logs/app.log"
REMOTE = "https://api.example.com/report"


def main():
    # 发送结果到远程
    data = open(LOG_PATH).read()
    requests.post(REMOTE, json={"k": API_KEY, "log": data})


if __name__ == "__main__":
    main()
