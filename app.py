import streamlit as st

# ページ設定
st.set_page_config(page_title="Colab Pipeline Generator", layout="wide")
st.title("🛠️ データ分析パイプライン・コードジェネレーター (完全版)")

# セッション状態の初期化
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

tabs = st.tabs(["1. 読込・プレビュー", "2. 型変換・異常値", "2.5 特徴量作成", "3. 分析・可視化", "4. モデリング・検定"])

def parse_input(text):
    if not text: return "[]"
    return "[" + ", ".join([f"'{x.strip()}'" for x in text.split(",")]) + "]"

# --- 1. 読込・プレビュー ---
with tabs[0]:
    st.header("1. データの読み込み")
    f_type = st.radio("ファイル形式", ["CSV", "Excel"])
    f_name = st.text_input("ファイル名", "data.csv")
    if st.button("🚀 コード生成"):
        code = "!pip install japanize-matplotlib\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport japanize_matplotlib\n\n"
        code += f"df = pd.read_{f_type.lower()}('{f_name}', dtype=str)\n"
        code += "for col in df.select_dtypes(include=['object']).columns:\n"
        code += "    df[col] = df[col].str.normalize('NFKC').str.strip()\n\n"
        code += "df.info()\nprint('\\nユニーク数と欠損値:')\ndisplay(pd.DataFrame({'ユニーク数': df.nunique(), '欠損値': df.isnull().sum()}))\ndisplay(df.head())"
        st.code(code, language="python")
        st.session_state.data_loaded = True

# --- 2. 型変換・異常値 ---
with tabs[1]:
    st.header("2. データ型の適正化と異常値")
    num_cols = st.text_input("数値カラム (カンマ区切り)")
    date_cols = st.text_input("日付カラム (カンマ区切り)")
    outlier = st.checkbox("IQR法で異常値フラグ(is_outlier)を付与", True)
    if st.button("🚀 コード生成"):
        code = f"num_cols, date_cols = {parse_input(num_cols)}, {parse_input(date_cols)}\n"
        code += "for c in num_cols: df[c] = pd.to_numeric(df[c], errors='coerce')\n"
        code += "for c in date_cols: df[c] = pd.to_datetime(df[c], errors='coerce')\n"
        if outlier:
            code += "for c in [c for c in num_cols if c in df.columns]:\n"
            code += "    q1, q3 = df[c].quantile([0.25, 0.75])\n"
            code += "    df['is_outlier'] = ((df[c] < q1 - 1.5*(q3-q1)) | (df[c] > q3 + 1.5*(q3-q1))).astype(int)\n"
        code += "display(df.describe(include='all'))"
        st.code(code, language="python")

# --- 2.5. 特徴量作成 ---
with tabs[2]:
    st.header("2.5 特徴量エンジニアリング")
    new_col = st.text_input("作成する新しいカラム名")
    logic = st.selectbox("作成ロジック", ["列A * 列B", "日付から曜日抽出", "文字列検索フラグ"])
    if logic == "列A * 列B":
        c1, c2 = st.text_input("カラムA"), st.text_input("カラムB")
        if st.button("🚀 生成"):
            st.code(f"df['{new_col}'] = df['{c1}'].astype(float) * df['{c2}'].astype(float)\ndisplay(df.head())", "python")
    elif logic == "日付から曜日抽出":
        c = st.text_input("日付カラム")
        if st.button("🚀 生成"):
            st.code(f"df['{new_col}'] = pd.to_datetime(df['{c}']).dt.day_name()\ndisplay(df.head())", "python")
    elif logic == "文字列検索フラグ":
        c, kw = st.text_input("文字列カラム"), st.text_input("キーワード")
        if st.button("🚀 生成"):
            st.code(f"df['{new_col}'] = df['{c}'].str.contains('{kw}', na=False).astype(int)\ndisplay(df.head())", "python")

# --- 3. 分析・可視化 ---
with tabs[3]:
    st.header("3. データの絞り込みと可視化")
    x, y = st.text_input("X軸"), st.text_input("Y軸")
    charts = st.multiselect("グラフ種類", ["散布図", "箱ひげ図", "棒グラフ", "折れ線グラフ"], ["散布図"])
    if st.button("🚀 コード生成"):
        code = "fig, axes = plt.subplots(len(charts), 1, figsize=(10, 6*len(charts)))\nif len(charts) == 1: axes = [axes]\n"
        for i, c in enumerate(charts):
            kind = {"散布図": "scatterplot", "箱ひげ図": "boxplot", "棒グラフ": "barplot", "折れ線グラフ": "lineplot"}[c]
            code += f"sns.{kind}(data=df, x='{x}', y='{y}', ax=axes[{i}], hue='is_outlier' if 'is_outlier' in df.columns else None)\n"
            code += f"axes[{i}].set_title('{c}')\n"
        code += "plt.tight_layout()\nplt.show()"
        st.code(code, language="python")

# --- 4. モデリング・検定 ---
with tabs[4]:
    st.header("4. エビデンス導出 (ML / 統計検定)")
    task = st.radio("タスク選択", ["機械学習", "統計検定"])
    if st.button("🚀 コード生成"):
        if task == "統計検定":
            g, v = st.text_input("グループ列"), st.text_input("数値列")
            code = f"from scipy import stats\ngroups = [df[df['{g}']==cat]['{v}'].dropna() for cat in df['{g}'].unique()]\n"
            code += "if len(groups) == 2: print(stats.ttest_ind(*groups))\nelse: print(stats.f_oneway(*groups))\n"
            code += f"sns.boxplot(data=df, x='{g}', y='{v}')\nplt.show()"
        else:
            code = "from sklearn.ensemble import RandomForestRegressor\nfrom sklearn.model_selection import train_test_split\nimport shap\n"
            code += "X, y = df.select_dtypes(include=np.number).drop(columns=['target'], errors='ignore'), df['target'].dropna()\n"
            code += "model = RandomForestRegressor().fit(X, y)\nexplainer = shap.TreeExplainer(model)\nshap.summary_plot(explainer.shap_values(X), X)"
        st.code(code, language="python")
