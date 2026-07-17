import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.title("データ分析用：日付付き・汚れたCSV生成ツール")

# 設定
st.sidebar.header("設定")
num_rows = st.sidebar.slider("行数", 20, 200, 50)

def generate_dirty_data_with_dates(rows):
    # 1. 正しい日付の生成
    base_date = datetime(2026, 1, 1)
    dates = [base_date + timedelta(days=np.random.randint(0, 100)) for _ in range(rows)]
    
    data = {
        "Date": dates,
        "ID": range(1, rows + 1),
        "Price": np.random.randint(500, 5000, rows),
        "Category": np.random.choice(["イタリアン", "和食", "中華"], rows),
    }
    df = pd.DataFrame(data)

    # 2. 日付の表記ゆれを注入（一部を文字列や異なる形式にする）
    # 汚す場所をランダムに選定
    dirty_indices = np.random.choice(df.index, size=int(rows * 0.2), replace=False)
    
    for idx in dirty_indices:
        # ランダムな汚れ方（一部を文字列変換やフォーマット変更）
        if np.random.rand() > 0.5:
            df.at[idx, "Date"] = "2026/01/01" # スラッシュ区切り
        else:
            df.at[idx, "Date"] = "エラー" # 不正な値

    # 3. 欠損値の注入
    df.loc[df.sample(frac=0.1).index, "Date"] = np.nan

    return df

if st.button("汚れたデータ（日付付き）を生成"):
    df = generate_dirty_data_with_dates(num_rows)
    st.session_state['dirty_df'] = df
    st.write("生成されたデータ（一部）:")
    st.dataframe(df.head(20))

if 'dirty_df' in st.session_state:
    csv = st.session_state['dirty_df'].to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="CSVをダウンロード",
        data=csv,
        file_name='dirty_dataset_with_date.csv',
        mime='text/csv',
    )
    
    st.warning("""
    **分析の練習課題:**
    1. `Date` 列をすべて `datetime` 型に変換してみましょう。（エラーが出る行をどう処理しますか？）
    2. 表記ゆれ（/区切りや文字列）を統一してみましょう。
    3. `Date` をキーにして、月ごとの `Price` の平均値を計算してみましょう。
    """)
