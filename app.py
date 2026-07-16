import streamlit as st

st.set_page_config(page_title="Colab Pipeline Generator", layout="wide")
st.title("🛠️ データ分析パイプライン・コードジェネレーター")

tabs = st.tabs(["1. 読込", "2. 型変換", "2.5 特徴量", "3. 可視化", "4. 分析"])

def parse_input(text):
    if not text: return "[]"
    return "[" + ", ".join([f"'{x.strip()}'" for x in text.split(",")]) + "]"

# --- 1. 読込 ---
with tabs[0]:
    st.header("1. データの読み込み")
    f_type = st.radio("ファイル形式", ["CSV", "Excel"], key="f1_type")
    f_name = st.text_input("ファイル名", "data.csv", key="f1_name")
    if st.button("🚀 コード生成", key="b1"):
        code = "!pip install japanize-matplotlib\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport japanize_matplotlib\n\n"
        code += f"df = pd.read_{f_type.lower()}('{f_name}', dtype=str)\n"
        code += "for col in df.select_dtypes(include=['object']).columns:\n"
        code += "    df[col] = df[col].str.normalize('NFKC').str.strip()\n\n"
        code += "df.info()\nprint('\\nユニーク数と欠損値:')\ndisplay(pd.DataFrame({'ユニーク数': df.nunique(), '欠損値': df.isnull().sum()}))\ndisplay(df.head())"
        st.code(code, language="python")

# --- 2. 型変換 ---
with tabs[1]:
    st.header("2. データ型の適正化と異常値")
    num_cols = st.text_input("数値カラム", key="num_2")
    date_cols = st.text_input("日付カラム", key="date_2")
    outlier = st.checkbox("IQR法で異常値フラグ付与", True, key="out_2")
    if st.button("🚀 コード生成", key="b2"):
        code = f"num_cols, date_cols = {parse_input(num_cols)}, {parse_input(date_cols)}\n"
        code += "for c in num_cols: df[c] = pd.to_numeric(df[c], errors='coerce')\n"
        code += "for c in date_cols: df[c] = pd.to_datetime(df[c], errors='coerce')\n"
        if outlier:
            code += "for c in [c for c in num_cols if c in df.columns]:\n"
            code += "    q1, q3 = df[c].quantile([0.25, 0.75])\n"
            code += "    df['is_outlier'] = ((df[c] < q1 - 1.5*(q3-q1)) | (df[c] > q3 + 1.5*(q3-q1))).astype(int)\n"
        code += "display(df.describe(include='all'))"
        st.code(code, language="python")

# --- 2.5. 特徴量 ---
with tabs[2]:
    st.header("2.5 特徴量エンジニアリング")
    new_col = st.text_input("新しいカラム名", key="new_25")
    logic = st.selectbox("作成ロジック", ["列A * 列B", "日付から曜日抽出", "文字列検索フラグ"], key="logic_25")
    code_25 = ""
    if logic == "列A * 列B":
        c1, c2 = st.text_input("カラムA", key="c1_25"), st.text_input("カラムB", key="c2_25")
        code_25 = f"df['{new_col}'] = df['{c1}'].astype(float) * df['{c2}'].astype(float)\ndisplay(df.head())"
    elif logic == "日付から曜日抽出":
        c = st.text_input("日付カラム", key="c_25")
        code_25 = f"df['{new_col}'] = pd.to_datetime(df['{c}']).dt.day_name()\ndisplay(df.head())"
    elif logic == "文字列検索フラグ":
        c, kw = st.text_input("文字列カラム", key="str_25"), st.text_input("キーワード", key="kw_25")
        code_25 = f"df['{new_col}'] = df['{c}'].str.contains('{kw}', na=False).astype(int)\ndisplay(df.head())"
    if st.button("🚀 コード生成", key="b25"):
        st.code(code_25, language="python")

# --- 3. 可視化 ---
with tabs[3]:
    st.header("3. データの絞り込みと可視化")
    x, y = st.text_input("X軸", key="x_3"), st.text_input("Y軸", key="y_3")
    charts = st.multiselect("グラフ種類", ["散布図", "箱ひげ図", "棒グラフ", "折れ線グラフ"], ["散布図"], key="c_3")
    if st.button("🚀 コード生成", key="b3"):
        code = f"charts = {charts}\nfig, axes = plt.subplots(len(charts), 1, figsize=(10, 6*len(charts)))\nif len(charts) == 1: axes = [axes]\n"
        for i, c in enumerate(charts):
            kind = {"散布図": "scatterplot", "箱ひげ図": "boxplot", "棒グラフ": "barplot", "折れ線グラフ": "lineplot"}[c]
            code += f"sns.{kind}(data=df, x='{x}', y='{y}', ax=axes[{i}], hue='is_outlier' if 'is_outlier' in df.columns else None)\n"
            code += f"axes[{i}].set_title('{c}')\n"
        code += "plt.tight_layout()\nplt.show()"
        st.code(code, language="python")

# --- 4. 分析 ---
with tabs[4]:
    st.header("4. エビデンス導出 (ML / 統計検定)")
    task = st.radio("タスク選択", ["機械学習", "統計検定"], key="task_4")
    
    if task == "機械学習":
        mode = st.selectbox("予測タイプ", ["回帰 (数値を予測)", "分類 (カテゴリを予測)"], key="ml_mode")
        model_type = st.selectbox("使用モデル", ["LightGBM", "Random Forest", "XGBoost"], key="ml_model")
        target = st.text_input("目的変数", key="ml_target")
        feats = st.text_input("説明変数 (カンマ区切り)", key="ml_feats")
        if st.button("🚀 コード生成", key="b4_ml"):
            model_class = {"回帰 (数値を予測)": {"LightGBM": "LGBMRegressor", "Random Forest": "RandomForestRegressor", "XGBoost": "XGBRegressor"},
                           "分類 (カテゴリを予測)": {"LightGBM": "LGBMClassifier", "Random Forest": "RandomForestClassifier", "XGBoost": "XGBClassifier"}}
            m = model_class[mode][model_type]
            code = f"from sklearn.model_selection import train_test_split\nfrom sklearn.ensemble import RandomForestRegressor, RandomForestClassifier\nimport lightgbm as lgb\nimport xgboost as xgb\nimport shap\n\n"
            code += f"X, y = df[{parse_input(feats)}].dropna(), df['{target}'].dropna()\n"
            code += f"model = {m}(random_state=42).fit(X, y)\n"
            code += "explainer = shap.TreeExplainer(model)\nshap.summary_plot(explainer.shap_values(X), X)"
            st.code(code, language="python")
            
    else: # 統計検定
        g, v = st.text_input("グループ列", key="g_4"), st.text_input("数値列", key="v_4")
        if st.button("🚀 コード生成", key="b4_stat"):
            code = f"from scipy import stats\ngroups = [df[df['{g}']==cat]['{v}'].dropna() for cat in df['{g}'].unique()]\n"
            code += "if len(groups) == 2: print(stats.ttest_ind(*groups))\nelse: print(stats.f_oneway(*groups))\n"
            code += f"sns.boxplot(data=df, x='{g}', y='{v}')\nplt.show()"
            st.code(code, language="python")
