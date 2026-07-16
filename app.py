import streamlit as st

# ページ設定
st.set_page_config(page_title="Colab Data Pipeline Generator", layout="wide")
st.title("🛠️ データ分析パイプライン・コードジェネレーター")
st.write("Colab環境での分析を最適化する完全版ジェネレーターです。")

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
        code += "sns.set_style('whitegrid')\n"
        code += f"df = pd.read_{file_type.lower()}('{file_name}', dtype=str)\n\n"
        code += "# ベクトル化による高速クレンジング\n"
        code += "str_cols = df.select_dtypes(include=['object']).columns\n"
        code += "for col in str_cols:\n"
        code += "    df[col] = df[col].str.normalize('NFKC').str.strip()\n\n"
        code += "print('▼ データ型・メモリ状況')\n"
        code += "df.info()\n"
        code += "print('\\n▼ ユニーク数と欠損値')\n"
        code += "display(pd.DataFrame({'ユニーク数': df.nunique(), '欠損値': df.isnull().sum()}))\n"
        code += "display(df.head())\n"
        st.code(code, language="python")

# --- フェーズ 2: 型変換・異常値 ---
with tabs[1]:
    st.header("2. データ型の適正化と異常値")
    num_cols = st.text_input("📊 数値型にするカラム (カンマ区切り)")
    date_cols = st.text_input("📅 日付型にするカラム (カンマ区切り)")
    str_cols = st.text_input("🔤 文字列型にするカラム (カンマ区切り)")
    outlier = st.checkbox("IQR法で異常値フラグ(is_outlier)を付与する", True)

    if st.button("🚀 コード生成 (フェーズ2)", type="primary"):
        code = f"num_cols = {parse_input(num_cols)}\n"
        code += f"date_cols = {parse_input(date_cols)}\n"
        code += f"str_cols = {parse_input(str_cols)}\n\n"
        code += "for c in num_cols: df[c] = pd.to_numeric(df[c], errors='coerce')\n"
        code += "for c in date_cols: df[c] = pd.to_datetime(df[c], errors='coerce')\n"
        code += "for c in str_cols: df[c] = df[c].astype(str)\n\n"
        if outlier:
            code += "for c in [c for c in num_cols if c in df.columns]:\n"
            code += "    q1, q3 = df[c].quantile([0.25, 0.75])\n"
            code += "    df['is_outlier'] = ((df[c] < q1 - 1.5*(q3-q1)) | (df[c] > q3 + 1.5*(q3-q1))).astype(int)\n"
        code += "display(df.describe(include='all'))\n"
        st.code(code, language="python")

# --- フェーズ 2.5: 特徴量作成 ---
with tabs[2]:
    st.header("2.5 特徴量エンジニアリング")
    new_col = st.text_input("新しいカラム名")
    feat_logic = st.selectbox("作成ロジック", ["列A * 列B", "日付から曜日抽出", "文字列検索フラグ"])
    
    if st.button("🚀 コード生成 (フェーズ2.5)", type="primary"):
        code = f"# 特徴量作成: {new_col}\n"
        if feat_logic == "列A * 列B":
            a, b = st.text_input("カラムA"), st.text_input("カラムB")
            code += f"df['{new_col}'] = df['{a}'] * df['{b}']\n"
        elif feat_logic == "日付から曜日抽出":
            date_col = st.text_input("日付カラム")
            code += f"df['{new_col}'] = df['{date_col}'].dt.day_name()\n"
        code += "display(df.head())\n"
        st.code(code, language="python")

# --- フェーズ 3: 分析・可視化 ---
with tabs[3]:
    st.header("3. データの絞り込みと可視化")
    st.write("※絞り込み条件（数値比較など）はColab側で必要に応じて修正してください。")
    x, y = st.text_input("X軸"), st.text_input("Y軸")
    charts = st.multiselect("グラフ種類", ["散布図", "箱ひげ図", "棒グラフ", "折れ線グラフ"], ["散布図"])
    
    if st.button("🚀 コード生成 (フェーズ3)", type="primary"):
        code = "plt.figure(figsize=(10, 6))\n"
        for c in charts:
            kind = {"散布図": "scatterplot", "箱ひげ図": "boxplot", "棒グラフ": "barplot", "折れ線グラフ": "lineplot"}[c]
            code += f"sns.{kind}(data=df, x='{x}', y='{y}', hue='is_outlier' if 'is_outlier' in df.columns else None)\n"
            code += "plt.show()\n"
        st.code(code, language="python")

# --- フェーズ 4: モデリング・検定 ---
with tabs[4]:
    st.header("4. エビデンス導出 (ML / 統計検定)")
    task = st.radio("タスク選択", ["機械学習", "統計検定"])
    
    if st.button("🚀 コード生成 (フェーズ4)", type="primary"):
        code = "from scipy import stats\n"
        if task == "統計検定":
            g, v = st.text_input("グループ列"), st.text_input("数値列")
            code += f"groups = [df[df['{g}']==cat]['{v}'].dropna() for cat in df['{g}'].unique()]\n"
            code += "if len(groups) == 2: print(stats.ttest_ind(*groups))\n"
            code += "else: print(stats.f_oneway(*groups))\n"
        else:
            code += "from sklearn.ensemble import RandomForestRegressor\n"
            code += "X, y = df[num_cols].dropna().drop(columns=['target']), df['target'].dropna()\n"
            code += "model = RandomForestRegressor().fit(X, y)\n"
        st.code(code, language="python")
