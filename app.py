import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# ページ設定
# ---------------------------------------------------------
st.set_page_config(page_title="Data Pipeline Code Generator", layout="wide")
st.title("🛠️ Python分析コード自動生成アプリ")
st.write("アップロードしたデータの構造を読み取り、最適な前処理・可視化・機械学習のコードを自動生成します。")

# ---------------------------------------------------------
# ステップ1: データの読み込みと構造解析
# ---------------------------------------------------------
st.header("1. データのアップロード (スキーマ読み取り用)")
uploaded_file = st.file_uploader("列名や行数を把握するため、対象のCSVをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    # 0落ち防止のため一旦すべて文字列として読み込み
    df = pd.read_csv(uploaded_file, dtype=str)
    row_count = len(df)
    cols = df.columns.tolist()
    
    st.success(f"データを読み込みました。 (総行数: {row_count}行 / 総カラム数: {len(cols)}列)")

    # ---------------------------------------------------------
    # ステップ2: 前処理・異常値設定
    # ---------------------------------------------------------
    st.header("2. 前処理と異常値ハンドリング")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("文字クレンジング")
        clean_text = st.checkbox("全角・半角の統一と空白削除 (NFKC正規化)", value=True)
        numeric_cols = st.multiselect("数値型(float/int)に強制変換するカラム", cols)
        
    with col2:
        st.subheader("異常値 (外れ値) の処理")
        outlier_handling = st.radio(
            "IQR法による異常値の処理方針", 
            ["処理しない", "異常フラグ(is_outlier)のカラムを追加する (推奨)", "異常値を含む行を除外する"]
        )

    # ---------------------------------------------------------
    # ステップ3: モデリング・時系列予測の設定
    # ---------------------------------------------------------
    st.header("3. 機械学習 / 時系列モデルの選択")
    
    # データ数に応じたレコメンドロジック
    recommend_text = ""
    if row_count < 1000:
        recommend_text = "💡 **【推奨】** データ数が1,000件未満のため、過学習を起こしにくい **Random Forest** や **線形回帰 (Linear/Ridge)** がおすすめです。"
    elif row_count < 100000:
        recommend_text = "💡 **【推奨】** データ数が十分にあるため、精度と速度のバランスに優れた **LightGBM** や **XGBoost** が最適です。"
    else:
        recommend_text = "💡 **【推奨】** データ数が10万件を超える大規模データのため、高速処理が可能な **LightGBM** を強く推奨します。"
        
    st.info(recommend_text)
    
    task_type = st.radio("分析タスク", ["回帰 (数値を予測)", "分類 (カテゴリを予測)", "時系列予測 (未来の推移を予測)"])
    
    target_col = st.selectbox("目的変数 (予測したいカラム)", cols)
    feature_cols = st.multiselect("説明変数 (予測の手がかりにするカラム)", [c for c in cols if c != target_col])
    
    if task_type == "回帰 (数値を予測)":
        model_selection = st.selectbox("使用するモデル", ["RandomForestRegressor", "LGBMRegressor", "XGBRegressor", "LinearRegression"])
    elif task_type == "分類 (カテゴリを予測)":
        model_selection = st.selectbox("使用するモデル", ["RandomForestClassifier", "LGBMClassifier", "XGBClassifier", "LogisticRegression"])
    else:
        time_col = st.selectbox("日付・時刻のカラム", [c for c in cols if c != target_col])
        model_selection = st.selectbox("使用するモデル", ["Prophet", "SARIMA (statsmodels)"])

    # ---------------------------------------------------------
    # コード生成処理
    # ---------------------------------------------------------
    if st.button("🚀 実行可能なPythonコードを生成", type="primary"):
        st.markdown("---")
        st.subheader("生成されたコード")
        st.write("以下のコードをコピーし、Jupyter NotebookやGoogle Colabに貼り付けて実行してください。")
        
        # コードの組み立て
        code = f"import pandas as pd\nimport numpy as np\nimport unicodedata\nimport plotly.express as px\n\n"
        code += f"# 1. データの読み込み\n"
        code += f"df = pd.read_csv('{uploaded_file.name}', dtype=str)\n\n"
        
        if clean_text:
            code += "# 2. 文字列のクレンジング (全角半角の統一・空白削除)\n"
            code += "def clean_text(text):\n"
            code += "    if pd.isnull(text): return text\n"
            code += "    text = unicodedata.normalize('NFKC', str(text))\n"
            code += "    return text.strip()\n\n"
            code += "str_cols = df.select_dtypes(include=['object']).columns\n"
            code += "for col in str_cols:\n"
            code += "    df[col] = df[col].apply(clean_text)\n\n"
            
        if numeric_cols:
            code += "# 3. データ型の適正化 (数値型への変換)\n"
            code += f"num_cols = {numeric_cols}\n"
            code += "for col in num_cols:\n"
            code += "    df[col] = pd.to_numeric(df[col], errors='coerce')\n"
            code += "df = df.dropna(subset=num_cols)\n\n"
            
        if outlier_handling != "処理しない" and numeric_cols:
            code += "# 4. 異常値 (外れ値) の検出とハンドリング (IQR法)\n"
            if outlier_handling == "異常フラグ(is_outlier)のカラムを追加する (推奨)":
                code += "df['is_outlier'] = 0\n"
                code += "for col in num_cols:\n"
                code += "    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)\n"
                code += "    iqr = q3 - q1\n"
                code += "    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr\n"
                code += "    outlier_cond = (df[col] < lower_bound) | (df[col] > upper_bound)\n"
                code += "    df.loc[outlier_cond, 'is_outlier'] = 1\n\n"
                
                code += "# 異常値のハイライト可視化 (Plotly)\n"
                code += "df['データ区分'] = df['is_outlier'].map({0: '正常値', 1: '異常値'})\n"
                if len(numeric_cols) >= 2:
                    code += f"fig = px.scatter(df, x='{numeric_cols[0]}', y='{numeric_cols[1]}', color='データ区分',\n"
                    code += "                 color_discrete_map={'正常値': '#1f77b4', '異常値': '#d62728'},\n"
                    code += "                 template='plotly_white', title='異常値ハイライト')\n"
                    code += "fig.show()\n\n"
            else:
                code += "for col in num_cols:\n"
                code += "    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)\n"
                code += "    iqr = q3 - q1\n"
                code += "    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr\n"
                code += "    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]\n\n"

        code += "# 5. 機械学習 / 時系列モデルの構築\n"
        if task_type in ["回帰 (数値を予測)", "分類 (カテゴリを予測)"]:
            code += f"features = {feature_cols}\n"
            code += f"target = '{target_col}'\n\n"
            code += "from sklearn.model_selection import train_test_split\n"
            code += "X = df[features]\n"
            code += "y = df[target]\n"
            code += "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n\n"
            
            if "LGBM" in model_selection:
                code += "import lightgbm as lgb\n"
                code += f"model = lgb.{model_selection}()\n"
            elif "RandomForest" in model_selection:
                code += "from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier\n"
                code += f"model = {model_selection}(random_state=42)\n"
            elif "XGB" in model_selection:
                code += "import xgboost as xgb\n"
                code += f"model = xgb.{model_selection}(random_state=42)\n"
            else:
                code += "from sklearn.linear_model import LinearRegression, LogisticRegression\n"
                code += f"model = {model_selection}()\n"
                
            code += "model.fit(X_train, y_train)\n"
            code += "print(f'モデル学習完了: {model.score(X_test, y_test):.4f} (Accuracy/R2 Score)')\n"
            
        elif task_type == "時系列予測 (未来の推移を予測)":
            if model_selection == "Prophet":
                code += "from prophet import Prophet\n"
                code += f"ts_df = df[['{time_col}', '{target_col}']].rename(columns={{'{time_col}': 'ds', '{target_col}': 'y'}})\n"
                code += "ts_df['ds'] = pd.to_datetime(ts_df['ds'])\n"
                code += "ts_df['y'] = pd.to_numeric(ts_df['y'])\n"
                code += "ts_df = ts_df.dropna()\n\n"
                code += "model = Prophet()\n"
                code += "model.fit(ts_df)\n"
                code += "future = model.make_future_dataframe(periods=30)\n"
                code += "forecast = model.predict(future)\n"
                code += "fig = model.plot(forecast)\n"
            elif model_selection == "SARIMA (statsmodels)":
                code += "import statsmodels.api as sm\n"
                code += f"ts_df = df[['{time_col}', '{target_col}']].copy()\n"
                code += f"ts_df['{time_col}'] = pd.to_datetime(ts_df['{time_col}'])\n"
                code += f"ts_df = ts_df.set_index('{time_col}')\n"
                code += f"ts_df['{target_col}'] = pd.to_numeric(ts_df['{target_col}'])\n"
                code += "ts_df = ts_df.dropna()\n\n"
                code += f"model = sm.tsa.statespace.SARIMAX(ts_df['{target_col}'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))\n"
                code += "results = model.fit()\n"
                code += "print(results.summary())\n"

        st.code(code, language="python")
