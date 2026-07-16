import streamlit as st

# ---------------------------------------------------------
# ページ設定
# ---------------------------------------------------------
st.set_page_config(page_title="Secure Code Generator", layout="wide")
st.title("🛠️ Python分析コード自動生成アプリ (高セキュリティ版)")
st.write("データを読み込まず、設定項目の選択と入力のみで最適な分析コードを発行します。")

# ---------------------------------------------------------
# ステップ1: データ形式と基本設定
# ---------------------------------------------------------
st.header("1. 元データの設定")
col_file1, col_file2 = st.columns(2)
with col_file1:
    file_type = st.radio("ファイル形式を選択", ["CSV", "Excel"])
with col_file2:
    file_name = st.text_input("読み込むファイル名", "data.csv" if file_type == "CSV" else "data.xlsx")

st.info("💡 【標準搭載】 すべての文字列データに対する全角半角の統一（NFKC正規化）と空白削除のクレンジング処理は、自動でコードに組み込まれます。")

# ---------------------------------------------------------
# ステップ2: 前処理・異常値ハンドリング
# ---------------------------------------------------------
st.header("2. 前処理と異常値ハンドリング")
numeric_cols_input = st.text_input(
    "数値型に強制変換するカラム名 (カンマ区切りで入力)", 
    placeholder="例: 売上金額, 年齢, 月間乗車回数"
)

outlier_handling = st.radio(
    "IQR法による異常値 (外れ値) の処理方針", 
    ["処理しない", "異常フラグ(is_outlier)のカラムを追加する (推奨)", "異常値を含む行を除外する"]
)

# ---------------------------------------------------------
# ステップ3: モデリング・時系列予測の設定
# ---------------------------------------------------------
st.header("3. 機械学習 / 時系列モデルの選択")

task_type = st.radio("分析タスク", ["回帰 (数値を予測)", "分類 (カテゴリを予測)", "時系列予測 (未来の推移を予測)"])

col_target, col_features = st.columns(2)
with col_target:
    target_col = st.text_input("目的変数 (予測したいカラム名)", placeholder="例: 総合満足度")
with col_features:
    if task_type != "時系列予測 (未来の推移を予測)":
        feature_cols_input = st.text_input("説明変数 (予測の手がかりにするカラム名・カンマ区切り)", placeholder="例: 年齢, 月間乗車回数, 平均遅延遭遇率")
    else:
        time_col = st.text_input("日付・時刻のカラム名", placeholder="例: 登録日")

if task_type == "回帰 (数値を予測)":
    model_selection = st.selectbox("使用するモデル", ["LightGBM (LGBMRegressor) - 中〜大規模データ推奨", "RandomForestRegressor - 小規模データ推奨", "XGBRegressor", "LinearRegression"])
elif task_type == "分類 (カテゴリを予測)":
    model_selection = st.selectbox("使用するモデル", ["LightGBM (LGBMClassifier) - 中〜大規模データ推奨", "RandomForestClassifier - 小規模データ推奨", "XGBClassifier", "LogisticRegression"])
else:
    model_selection = st.selectbox("使用するモデル", ["Prophet - 汎用・トレンド予測", "SARIMA (statsmodels) - 厳密な統計モデル"])

# ---------------------------------------------------------
# コード生成処理
# ---------------------------------------------------------
if st.button("🚀 実行可能なPythonコードを生成", type="primary"):
    st.markdown("---")
    st.subheader("生成されたコード")
    
    # 入力されたカンマ区切りの文字列をリスト形式に変換するヘルパー関数
    def parse_input(text):
        if not text: return "[]"
        items = [f"'{x.strip()}'" for x in text.split(",")]
        return "[" + ", ".join(items) + "]"

    # コードの組み立て
    code = f"import pandas as pd\nimport numpy as np\nimport unicodedata\nimport plotly.express as px\n\n"
    code += f"# 1. データの読み込み (0落ち防止のためすべて文字列として読み込み)\n"
    
    if file_type == "CSV":
        code += f"df = pd.read_csv('{file_name}', dtype=str)\n\n"
    else:
        code += f"df = pd.read_excel('{file_name}', dtype=str)\n\n"
        
    code += "# 2. 文字列の自動クレンジング (全角半角の統一・空白削除)\n"
    code += "def clean_text(text):\n"
    code += "    if pd.isnull(text): return text\n"
    code += "    text = unicodedata.normalize('NFKC', str(text))\n"
    code += "    return text.strip()\n\n"
    code += "str_cols = df.select_dtypes(include=['object']).columns\n"
    code += "for col in str_cols:\n"
    code += "    df[col] = df[col].apply(clean_text)\n\n"
        
    if numeric_cols_input.strip():
        code += "# 3. データ型の適正化 (数値型への変換)\n"
        code += f"num_cols = {parse_input(numeric_cols_input)}\n"
        code += "for col in num_cols:\n"
        code += "    if col in df.columns:\n"
        code += "        df[col] = pd.to_numeric(df[col], errors='coerce')\n"
        code += "df = df.dropna(subset=[c for c in num_cols if c in df.columns])\n\n"
        
    if outlier_handling != "処理しない" and numeric_cols_input.strip():
        code += "# 4. 異常値 (外れ値) の検出とハンドリング (IQR法)\n"
        code += "target_num_cols = [c for c in num_cols if c in df.columns]\n"
        if outlier_handling == "異常フラグ(is_outlier)のカラムを追加する (推奨)":
            code += "df['is_outlier'] = 0\n"
            code += "for col in target_num_cols:\n"
            code += "    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)\n"
            code += "    iqr = q3 - q1\n"
            code += "    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr\n"
            code += "    outlier_cond = (df[col] < lower_bound) | (df[col] > upper_bound)\n"
            code += "    df.loc[outlier_cond, 'is_outlier'] = 1\n\n"
            code += "# 異常値のハイライト可視化 (Plotly)\n"
            code += "df['データ区分'] = df['is_outlier'].map({0: '正常値', 1: '異常値'})\n"
            code += "if len(target_num_cols) >= 2:\n"
            code += "    fig = px.scatter(df, x=target_num_cols[0], y=target_num_cols[1], color='データ区分',\n"
            code += "                     color_discrete_map={'正常値': '#1f77b4', '異常値': '#d62728'},\n"
            code += "                     template='plotly_white', title='異常値ハイライト')\n"
            code += "    fig.show()\n\n"
        else:
            code += "for col in target_num_cols:\n"
            code += "    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)\n"
            code += "    iqr = q3 - q1\n"
            code += "    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr\n"
            code += "    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]\n\n"

    code += "# 5. 機械学習 / 時系列モデルの構築\n"
    if task_type in ["回帰 (数値を予測)", "分類 (カテゴリを予測)"]:
        code += f"features = {parse_input(feature_cols_input)}\n"
        code += f"target = '{target_col.strip()}'\n\n"
        code += "from sklearn.model_selection import train_test_split\n"
        code += "X = df[features]\n"
        code += "y = df[target]\n"
        code += "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n\n"
        
        if "LGBM" in model_selection:
            code += "import lightgbm as lgb\n"
            if "Regressor" in model_selection:
                code += "model = lgb.LGBMRegressor()\n"
            else:
                code += "model = lgb.LGBMClassifier()\n"
        elif "RandomForest" in model_selection:
            code += "from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier\n"
            if "Regressor" in model_selection:
                code += "model = RandomForestRegressor(random_state=42)\n"
            else:
                code += "model = RandomForestClassifier(random_state=42)\n"
        elif "XGB" in model_selection:
            code += "import xgboost as xgb\n"
            if "Regressor" in model_selection:
                code += "model = xgb.XGBRegressor(random_state=42)\n"
            else:
                code += "model = xgb.XGBClassifier(random_state=42)\n"
        else:
            code += "from sklearn.linear_model import LinearRegression, LogisticRegression\n"
            if "LinearRegression" in model_selection:
                code += "model = LinearRegression()\n"
            else:
                code += "model = LogisticRegression()\n"
            
        code += "model.fit(X_train, y_train)\n"
        code += "print(f'モデル学習完了: {model.score(X_test, y_test):.4f} (Accuracy/R2 Score)')\n"
        
    elif task_type == "時系列予測 (未来の推移を予測)":
        if "Prophet" in model_selection:
            code += "from prophet import Prophet\n"
            code += f"ts_df = df[['{time_col.strip()}', '{target_col.strip()}']].rename(columns={{'{time_col.strip()}': 'ds', '{target_col.strip()}': 'y'}})\n"
            code += "ts_df['ds'] = pd.to_datetime(ts_df['ds'])\n"
            code += "ts_df['y'] = pd.to_numeric(ts_df['y'])\n"
            code += "ts_df = ts_df.dropna()\n\n"
            code += "model = Prophet()\n"
            code += "model.fit(ts_df)\n"
            code += "future = model.make_future_dataframe(periods=30)\n"
            code += "forecast = model.predict(future)\n"
            code += "fig = model.plot(forecast)\n"
        elif "SARIMA" in model_selection:
            code += "import statsmodels.api as sm\n"
            code += f"ts_df = df[['{time_col.strip()}', '{target_col.strip()}']].copy()\n"
            code += f"ts_df['{time_col.strip()}'] = pd.to_datetime(ts_df['{time_col.strip()}'])\n"
            code += f"ts_df = ts_df.set_index('{time_col.strip()}')\n"
            code += f"ts_df['{target_col.strip()}'] = pd.to_numeric(ts_df['{target_col.strip()}'])\n"
            code += "ts_df = ts_df.dropna()\n\n"
            code += f"model = sm.tsa.statespace.SARIMAX(ts_df['{target_col.strip()}'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))\n"
            code += "results = model.fit()\n"
            code += "print(results.summary())\n"

    st.code(code, language="python")
