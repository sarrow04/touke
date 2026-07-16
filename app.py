import streamlit as st

st.set_page_config(page_title="Data Specialist Pipeline", layout="wide")
st.title("🛠️ データ分析パイプライン・コードジェネレーター (完全網羅版)")

tabs = st.tabs(["1. 読込", "1.5 質的診断", "2. 型変換", "2.5 特徴量", "3. 可視化", "4. 分析"])

def parse_input(text):
    if not text: return "[]"
    return "[" + ", ".join([f"'{x.strip()}'" for x in text.split(",")]) + "]"

# --- 1. 読込 ---
with tabs[0]:
    st.header("1. データの読み込み")
    f_type = st.radio("形式", ["CSV", "Excel"], key="f1")
    f_name = st.text_input("ファイル名", "data.csv", key="f1_name")
    if st.button("🚀 コード生成", key="b1"):
        code = "!pip install japanize-matplotlib\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport japanize_matplotlib\n\n"
        code += f"df = pd.read_{f_type.lower()}('{f_name}', dtype=str)\n"
        code += "for col in df.select_dtypes(include=['object']).columns:\n"
        code += "    df[col] = df[col].str.normalize('NFKC').str.strip()\n"
        st.code(code, "python")

# --- 1.5. 質的診断 ---
with tabs[1]:
    st.header("1.5 質的診断 (欠損・分布・相関)")
    if st.button("🚀 診断コード生成", key="b15"):
        code = """# 欠損値のメカニズムと分布・多重共線性の確認
import missingno as msno
msno.matrix(df)
plt.show()

# 全数値データの分布確認
df.select_dtypes(include=np.number).hist(bins=30, figsize=(20, 15))
plt.show()

# 多重共線性チェック (相関行列)
plt.figure(figsize=(12, 10))
sns.heatmap(df.select_dtypes(include=np.number).corr(), annot=True, cmap='coolwarm', fmt='.2f')
plt.show()"""
        st.code(code, "python")

# --- 2. 型変換 ---
with tabs[2]:
    st.header("2. データ型の適正化と異常値")
    num_cols = st.text_input("数値カラム", key="num_2")
    date_cols = st.text_input("日付カラム", key="date_2")
    bin_cols = st.text_input("0/1文字列を数値化", key="bin_2")
    outlier = st.checkbox("IQR法で異常値フラグ付与", True, key="out_2")
    if st.button("🚀 コード生成", key="b2"):
        code = f"num_cols, date_cols, bin_cols = {parse_input(num_cols)}, {parse_input(date_cols)}, {parse_input(bin_cols)}\n"
        code += "for c in num_cols: df[c] = pd.to_numeric(df[c], errors='coerce')\n"
        code += "for c in date_cols: df[c] = pd.to_datetime(df[c], errors='coerce')\n"
        code += "for c in bin_cols: df[c] = df[c].map({'0': 0, '1': 1, 0: 0, 1: 1})\n"
        if outlier:
            code += "for c in num_cols:\n    q1, q3 = df[c].quantile([0.25, 0.75])\n    df['is_outlier'] = ((df[c] < q1 - 1.5*(q3-q1)) | (df[c] > q3 + 1.5*(q3-q1))).astype(int)\n"
        st.code(code, "python")

# --- 2.5. 特徴量 ---
with tabs[3]:
    st.header("2.5 特徴量エンジニアリング")
    new_col = st.text_input("新カラム名", key="new_25")
    logic = st.selectbox("ロジック", ["列A * 列B", "曜日抽出", "文字列フラグ"], key="logic_25")
    c1 = st.text_input("カラム1", key="c1_25")
    c2 = st.text_input("カラム2/キーワード", key="c2_25")
    if st.button("🚀 生成", key="b25"):
        if logic == "列A * 列B":
            code = f"df['{new_col}'] = df['{c1}'].astype(float) * df['{c2}'].astype(float)"
        elif logic == "曜日抽出":
            code = f"df['{new_col}'] = pd.to_datetime(df['{c1}']).dt.day_name()"
        else:
            code = f"df['{new_col}'] = df['{c1}'].str.contains('{c2}', na=False).astype(int)"
        st.code(code, "python")

# --- 3. 可視化 ---
with tabs[4]:
    st.header("3. データの絞り込みと可視化")
    x, y = st.text_input("X軸", key="x_3"), st.text_input("Y軸", key="y_3")
    charts = st.multiselect("グラフ", ["散布図", "箱ひげ図", "棒グラフ"], ["散布図"], key="c_3")
    if st.button("🚀 コード生成", key="b3"):
        code = "for c in " + str(charts) + ":\n    plt.figure(figsize=(10, 6))\n    kind = {'散布図':'scatterplot', '箱ひげ図':'boxplot', '棒グラフ':'barplot'}[c]\n    getattr(sns, kind)(data=df, x='" + x + "', y='" + y + "')\n    plt.show()"
        st.code(code, "python")

# --- 4. 分析 ---
with tabs[5]:
    st.header("4. エビデンス導出 (ML / 統計検定)")
    task = st.radio("選択", ["機械学習", "統計検定"], key="task_4")
    if task == "機械学習":
        target = st.text_input("目的変数", key="ml_target")
        feats = st.text_input("説明変数 (カンマ区切り)", key="ml_feats")
        unit_price = st.number_input("リスク換算用単価", value=1000, key="price_4")
        if st.button("🚀 コード生成", key="b4_ml"):
            code = f"""from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
X, y = df[{parse_input(feats)}].dropna(), df['{target}'].dropna()
model = RandomForestRegressor().fit(X, y)
pred = model.predict(X)
print(f"想定リスク額: {{mean_absolute_error(y, pred) * {unit_price}:,.0f}} 円")
import shap
explainer = shap.TreeExplainer(model)
shap.summary_plot(explainer.shap_values(X), X)"""
            st.code(code, "python")
    else:
        g, v = st.text_input("グループ列", key="g_4"), st.text_input("数値列", key="v_4")
        if st.button("🚀 コード生成", key="b4_stat"):
            code = f"from scipy import stats\ngroups = [df[df['{g}']==cat]['{v}'].dropna() for cat in df['{g}'].unique()]\nprint(stats.ttest_ind(*groups) if len(groups)==2 else stats.f_oneway(*groups))"
            st.code(code, "python")
