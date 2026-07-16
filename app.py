import streamlit as st

# ページ設定
st.set_page_config(page_title="Colab Data Pipeline Generator", layout="wide")
st.title("🛠️ データ分析パイプライン・コードジェネレーター")

# データを全フェーズで保持するための session_state 初期化
if 'df_info' not in st.session_state:
    st.session_state.df_info = None

tabs = st.tabs(["1. 読込・プレビュー", "2. 型変換・異常値", "2.5 特徴量作成", "3. 分析・可視化", "4. モデリング・検定"])

def parse_input(text):
    if not text: return "[]"
    return "[" + ", ".join([f"'{x.strip()}'" for x in text.split(",")]) + "]"

# --- フェーズ 1: 読込・プレビュー ---
with tabs[0]:
    st.header("1. データの読み込みと初期プレビュー")
    col1, col2 = st.columns(2)
    file_type = col1.radio("ファイル形式", ["CSV", "Excel"])
    file_name = col2.text_input("Colabにアップロードしたファイル名", "data.csv")

    if st.button("🚀 コード生成 (フェーズ1)", type="primary"):
        code = "!pip install japanize-matplotlib\n\n"
        code += "import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport japanize_matplotlib\n\n"
        code += f"df = pd.read_{file_type.lower()}('{file_name}', dtype=str)\n\n"
        code += "# ベクトル化による高速クレンジング\n"
        code += "for col in df.select_dtypes(include=['object']).columns:\n"
        code += "    df[col] = df[col].str.normalize('NFKC').str.strip()\n\n"
        code += "df.info()\n"
        code += "display(df.head())\n"
        st.code(code, language="python")
        st.session_state.df_info = "loaded" # データが存在することを記録

# --- フェーズ 2.5: 特徴量作成 (修正版) ---
with tabs[2]:
    st.header("2.5 特徴量エンジニアリング")
    
    # ここに「フェーズ1が完了しているか」のチェックを追加
    if st.session_state.df_info:
        new_col = st.text_input("作成する新しいカラム名")
        feat_logic = st.selectbox("作成ロジック", ["列A * 列B", "日付から曜日抽出", "文字列検索フラグ"])
        
        # 演算用入力（表示を整理）
        if feat_logic == "列A * 列B":
            a = st.text_input("カラムA名")
            b = st.text_input("カラムB名")
            if st.button("🚀 コード生成 (フェーズ2.5)", type="primary"):
                code = f"df['{new_col}'] = df['{a}'].astype(float) * df['{b}'].astype(float)\n"
                code += "display(df.head())"
                st.code(code, language="python")
        elif feat_logic == "日付から曜日抽出":
            date_col = st.text_input("日付カラム名")
            if st.button("🚀 コード生成 (フェーズ2.5)", type="primary"):
                code = f"df['{new_col}'] = pd.to_datetime(df['{date_col}']).dt.day_name()\n"
                code += "display(df.head())"
                st.code(code, language="python")
    else:
        st.warning("⚠️ まず「1. 読込・プレビュー」でデータを読み込んでください。")

# (以降のフェーズも同様に st.session_state.df_info をチェックするように構造化すると安定します)
