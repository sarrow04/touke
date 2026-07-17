import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ページ設定
st.set_page_config(page_title="汚れたデータ生成アプリ", layout="wide")

st.title("データ分析練習用：汚れたCSV生成ツール")

# サイドバー設定
st.sidebar.header("データ生成パラメータ")
num_rows = st.sidebar.slider("行数", 20, 500, 100)

def generate_dirty_data(rows):
    # 1. 基本データの生成
    base_date = datetime(2026, 1, 1)
    dates = [base_date + timedelta(days=np.random.randint(0, 100)) for _ in range(rows)]
    
    df = pd.DataFrame({
        "Date": dates,
        "ID": range(1, rows + 1),
        "Price": np.random.randint(500, 5000, rows),
        "Category": np.random.choice(["イタリアン", "和食", "中華"], rows),
    })

    # 2. 意図的な汚れの注入
    # Date列に汚れ（文字列混入・表記ゆれ）
    dirty_date_idx = np.random.choice(df.index, size=int(rows * 0.15), replace=False)
    for idx in dirty_date_idx:
        options = ["2026/01/01", "エラー", "不明", "2026-01-01 00:00:00"]
        df.at[idx, "Date"] = np.random.choice(options)

    # Price列に汚れ（文字列混入・異常値）
    dirty_price_idx = np.random.choice(df.index, size=int(rows * 0.1), replace=False)
    for idx in dirty_price_idx:
        df.at[idx, "Price"] = "5000円" if np.random.rand() > 0.5 else 999999

    # 欠損値(NaN)の注入
    for col in df.columns:
        df.loc[df.sample(frac=0.05).index, col] = np.nan

    return df

# アプリのメイン処理
if st.button("新しい汚れたデータを生成"):
    st.session_state['dirty_df'] = generate_dirty_data(num_rows)

if 'dirty_df' in st.session_state:
    df = st.session_state['dirty_df']
    
    st.write("### 生成されたデータプレビュー")
    st.dataframe(df.head(20))

    # CSVダウンロード処理
    # エラー防止のため、一度全データを文字列型に変換してからCSV化
    csv = df.astype(str).replace('nan', '').to_csv(index=False).encode('utf-8-sig')
    
    st.download_button(
        label="CSVをダウンロード",
        data=csv,
        file_name='dirty_dataset.csv',
        mime='text/csv',
    )
    
    st.info("""
    **【分析者向けTips】**
    このCSVを読み込んだ後、以下のクレンジングを試してみてください：
    1. `pd.to_datetime(df['Date'], errors='coerce')` で日付を整形する。
    2. `pd.to_numeric(df['Price'], errors='coerce')` で価格を数値化する。
    3. `df.dropna()` で欠損行を処理する。
    """)
else:
    st.write("左のボタンを押すとデータが生成されます。")
