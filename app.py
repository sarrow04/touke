import streamlit as st
import pandas as pd
import numpy as np
import io

st.title("データ分析用：汚れたCSV生成ツール")

# 設定：汚れの強度をユーザーが調整できるようにする
st.sidebar.header("汚れの設定")
num_rows = st.sidebar.slider("行数", 10, 1000, 100)
nan_ratio = st.sidebar.slider("欠損値の割合", 0.0, 0.5, 0.1)

def generate_dirty_data(rows, nan_prob):
    # 基本データの作成
    data = {
        "ID": range(1, rows + 1),
        "Price": np.random.randint(500, 5000, rows),
        "Category": np.random.choice(["イタリアン", "和食", "中華", "French"], rows),
        "Rating": np.random.uniform(1, 5, rows).round(1)
    }
    df = pd.DataFrame(data)

    # 1. 欠損値の注入
    mask = np.random.choice([True, False], size=(rows, len(df.columns)), p=[nan_prob, 1-nan_prob])
    df[mask] = np.nan

    # 2. 表記ゆれの注入 (Category列)
    df.loc[df.sample(frac=0.1).index, "Category"] = "Italian" # 英語表記混在

    # 3. 異常値の注入 (Price列)
    df.loc[df.sample(frac=0.05).index, "Price"] = 999999 # 桁間違い

    return df

if st.button("汚れたデータを生成"):
    df = generate_dirty_data(num_rows, nan_ratio)
    st.session_state['dirty_df'] = df
    st.write("生成されたデータ（一部）:")
    st.dataframe(df.head(20))

# ダウンロード機能
if 'dirty_df' in st.session_state:
    csv = st.session_state['dirty_df'].to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="汚れたCSVをダウンロード",
        data=csv,
        file_name='dirty_dataset.csv',
        mime='text/csv',
    )
    
    st.info("このデータには、欠損値、表記ゆれ（イタリアン/Italian）、外れ値（999999）が含まれています。Pandasでどうクレンジングするか練習してみてください！")
