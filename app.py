import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ページ設定
st.set_page_config(page_title="汚れたデータ生成アプリ", layout="wide")

st.title("データ分析練習用：汚れたCSV生成ツール")

num_rows = st.sidebar.slider("行数", 20, 500, 100)

def generate_dirty_data(rows):
    # すべて空の文字列リストとして初期化することで型エラーを防ぐ
    data = {
        "Date": ["" for _ in range(rows)],
        "ID": [str(i) for i in range(1, rows + 1)],
        "Price": [str(np.random.randint(500, 5000)) for _ in range(rows)],
        "Category": np.random.choice(["イタリアン", "和食", "中華"], rows),
    }
    
    # 全列が object (string) 型のデータフレームとして作成
    df = pd.DataFrame(data)

    # 日付の注入 (日付オブジェクトを文字列に変換してから代入)
    base_date = datetime(2026, 1, 1)
    for i in range(rows):
        date_val = base_date + timedelta(days=np.random.randint(0, 100))
        df.at[i, "Date"] = date_val.strftime("%Y-%m-%d")

    # 意図的な汚れの注入
    # 1. 日付の汚れ
    for i in np.random.choice(range(rows), size=int(rows * 0.15), replace=False):
        df.at[i, "Date"] = np.random.choice(["2026/01/01", "エラー", "不明", ""])

    # 2. 価格の汚れ
    for i in np.random.choice(range(rows), size=int(rows * 0.1), replace=False):
        df.at[i, "Price"] = np.random.choice(["5000円", "999999", "不明"])

    # 3. 欠損値の注入 (空文字列にする)
    for col in df.columns:
        for i in np.random.choice(range(rows), size=int(rows * 0.05), replace=False):
            df.at[i, col] = ""

    return df

if st.button("新しい汚れたデータを生成"):
    st.session_state['dirty_df'] = generate_dirty_data(num_rows)

if 'dirty_df' in st.session_state:
    df = st.session_state['dirty_df']
    st.dataframe(df.head(20))

    # 文字列変換済みなのでそのままエンコード
    csv = df.to_csv(index=False).encode('utf-8-sig')
    
    st.download_button(
        label="CSVをダウンロード",
        data=csv,
        file_name='dirty_dataset.csv',
        mime='text/csv',
    )
