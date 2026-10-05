"""CSV 清洗器。"""
import argparse
import pandas as pd


def clean(path: str) -> "pd.DataFrame":
    df = pd.read_csv(path)
    df = df.dropna().drop_duplicates()
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    df = clean(a.input)
    df.to_csv(a.output, index=False)
    print(f"清洗完成：{a.output}，共 {len(df)} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
