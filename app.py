import streamlit as st

st.set_page_config(page_title="Colab Pipeline", layout="wide")
st.title("🛠️ データ分析パイプライン・コードジェネレーター")

tabs = st.tabs(["1. 読込", "2. 型変換", "2.5 特徴量", "3. 可視化", "4. 分析"])

# --- 1. 読込 ---
with tabs[0]:
    f_type = st.radio("形式", ["CSV", "Excel"], key="f_type_1")
    f_name = st.text_input("ファイル名", "data.csv", key="f_name_1")
    if st.button("生成", key="btn_1"):
        st.code("...", language="python")

# --- 2. 型変換 ---
with tabs[1]:
    num_cols = st.text_input("数値カラム", key="num_2")
    date_cols = st.text_input("日付カラム", key="date_2")
    if st.button("生成", key="btn_2"):
        st.code("...", language="python")

# --- 2.5. 特徴量 ---
with tabs[2]:
    new_col = st.text_input("新カラム名", key="new_25")
    logic = st.selectbox("ロジック", ["列A * 列B", "曜日抽出"], key="logic_25")
    if logic == "列A * 列B":
        c1 = st.text_input("A", key="c1_25")
        c2 = st.text_input("B", key="c2_25")
    if st.button("生成", key="btn_25"):
        st.code("...", language="python")

# --- 3. 可視化 ---
with tabs[3]:
    x = st.text_input("X軸", key="x_3")
    y = st.text_input("Y軸", key="y_3")
    if st.button("生成", key="btn_3"):
        st.code("...", language="python")

# --- 4. 分析 ---
with tabs[4]:
    task = st.radio("選択", ["機械学習", "統計検定"], key="task_4")
    if st.button("生成", key="btn_4"):
        st.code("...", language="python")
