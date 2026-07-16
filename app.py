import streamlit as st

# ---------------------------------------------------------
# ページ設定
# ---------------------------------------------------------
st.set_page_config(page_title="Colab 3-Step Pipeline Generator", layout="wide")
st.title("🛠️ 3段階パイプライン型コードジェネレーター (Colab専用)")
st.write("Colab上でデータを確認しながら、安全かつ確実に分析ステップを進めるためのジェネレーターです。")

tabs = st.tabs(["フェーズ1: 読込・前処理", "フェーズ2: データ分析・可視化", "フェーズ3: 高度なモデリング・検定"])

def parse_input(text):
    if not text: return "[]"
    return "[" + ", ".join([f"'{x.strip()}'" for x in text.split(",")]) + "]"

# =========================================================
# フェーズ1: 読込・前処理 ➡️ 【データ確認】へ
# =========================================================
with tabs[0]:
    st.header("1. データの読み込みと前処理 (土台構築)")
    col_file1, col_file2 = st.columns(2)
    with col_file1:
        file_type = st.radio("ファイル形式", ["CSV", "Excel"], key="file_type")
    with col_file2:
        file_name = st.text_input("Colabにアップロードしたファイル名", "data.csv" if file_type == "CSV" else "data.xlsx")

    numeric_cols_input = st.text_input("数値型に強制変換するカラム名 (カンマ区切り)", placeholder="例: 売上金額, 年齢")
    outlier_handling = st.checkbox("IQR法による異常値フラグ (is_outlier) の付与を行う", value=True)

    if st.button("🚀 読込・前処理コードを生成", type="primary"):
        code1 = f"import pandas as pd\nimport numpy as np\nimport unicodedata\nimport plotly.express as px\n\n"
        code1 += f"# 1. データの読み込み\n"
        if file_type == "CSV":
            code1 += f"df = pd.read_csv('{file_name}', dtype=str)\n\n"
        else:
            code1 += f"df = pd.read_excel('{file_name}', dtype=str)\n\n"
            
        code1 += "# 2. 文字列の自動クレンジング (全角半角の統一・空白削除)\n"
        code1 += "def clean_text(text):\n"
        code1 += "    if pd.isnull(text): return text\n"
        code1 += "    text = unicodedata.normalize('NFKC', str(text))\n"
        code1 += "    return text.strip()\n\n"
        code1 += "str_cols = df.select_dtypes(include=['object']).columns\n"
        code1 += "for col in str_cols:\n"
        code1 += "    df[col] = df[col].apply(clean_text)\n\n"
            
        if numeric_cols_input.strip():
            code1 += "# 3. データ型の適正化\n"
            code1 += f"num_cols = {parse_input(numeric_cols_input)}\n"
            code1 += "for col in num_cols:\n"
            code1 += "    if col in df.columns:\n"
            code1 += "        df[col] = pd.to_numeric(df[col], errors='coerce')\n\n"
            
            if outlier_handling:
                code1 += "# 4. 異常値フラグ付与\n"
                code1 += "target_num_cols = [c for c in num_cols if c in df.columns]\n"
                code1 += "df['is_outlier'] = 0\n"
                code1 += "for col in target_num_cols:\n"
                code1 += "    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)\n"
                code1 += "    iqr = q3 - q1\n"
                code1 += "    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr\n"
                code1 += "    outlier_cond = (df[col] < lower_bound) | (df[col] > upper_bound)\n"
                code1 += "    df.loc[outlier_cond, 'is_outlier'] = 1\n\n"

        code1 += "# 5. データ確認 (Colabでの目視用)\n"
        code1 += "print('▼ データ構造と欠損値')\n"
        code1 += "display(df.info())\n"
        code1 += "print('\\n▼ 処理後データのプレビュー')\n"
        code1 += "display(df.head(5))\n"

        st.markdown("---")
        st.write("💡 **【アクション】 以下のコードをColabで実行し、データが正しく読み込まれたことを確認してください。**")
        st.code(code1, language="python")

# =========================================================
# フェーズ2: データ分析・可視化 ➡️ 【傾向の確認】へ
# =========================================================
with tabs[1]:
    st.header("2. データ分析と構造的可視化")
    st.write("※フェーズ1で作成した `df` を使用して分析を行います。")
    
    query_input = st.text_input("SQL風抽出条件 (空欄で全件対象)", placeholder="例: 年齢 >= 30")
    
    st.subheader("可視化設定")
    x_col = st.text_input("X軸のカラム名")
    y_col = st.text_input("Y軸のカラム名 (数値推奨)")
    chart_type = st.radio("グラフの種類", ["散布図", "箱ひげ図", "棒グラフ"])
    color_outlier = st.checkbox("異常値フラグ (is_outlier) で色分けする", value=True)

    if st.button("🚀 分析・可視化コードを生成", type="primary"):
        code2 = ""
        if query_input.strip():
            code2 += f"# 1. 条件抽出\n"
            code2 += f"target_df = df.query(\"{query_input.strip()}\").copy()\n"
            code2 += "print(f'抽出件数: {len(target_df)}件')\n\n"
        else:
            code2 += "# 1. 対象データ (全件)\n"
            code2 += "target_df = df.copy()\n\n"

        if x_col and y_col:
            code2 += "# 2. 構造的可視化 (Plotly)\n"
            if color_outlier:
                code2 += "if 'is_outlier' in target_df.columns:\n"
                code2 += "    target_df['データ区分'] = target_df['is_outlier'].map({0: '正常値', 1: '異常値'})\n"
                code2 += "    color_col = 'データ区分'\n"
                code2 += "    color_map = {'正常値': '#1f77b4', '異常値': '#d62728'}\n"
                code2 += "else:\n"
                code2 += "    color_col = None\n"
                code2 += "    color_map = None\n\n"
            else:
                code2 += "color_col = None\n"
                code2 += "color_map = None\n\n"

            if chart_type == "散布図":
                code2 += f"fig = px.scatter(target_df, x='{x_col.strip()}', y='{y_col.strip()}', color=color_col, color_discrete_map=color_map, template='plotly_white')\n"
            elif chart_type == "箱ひげ図":
                code2 += f"fig = px.box(target_df, x='{x_col.strip()}', y='{y_col.strip()}', color=color_col, color_discrete_map=color_map, template='plotly_white')\n"
            else:
                code2 += f"fig = px.bar(target_df, x='{x_col.strip()}', y='{y_col.strip()}', color=color_col, color_discrete_map=color_map, template='plotly_white')\n"
            
            code2 += "fig.show()\n"

        if code2:
            st.markdown("---")
            st.write("💡 **【アクション】 以下のコードをColabの次のセルで実行し、データの傾向を分析してください。**")
            st.code(code2, language="python")
        else:
            st.warning("X軸とY軸のカラム名を入力してください。")

# =========================================================
# フェーズ3: 高度なモデリング・検定 ➡️ 【エビデンスの導出】へ
# =========================================================
with tabs[2]:
    st.header("3. モデリング・統計検定 (エビデンス抽出)")
    st.write("※フェーズ2で傾向を掴んだ後、論理的な裏付けを行うためのコードを発行します。")
    
    task_type = st.radio("実行するタスク", ["機械学習 (SHAP要因分析)", "統計検定 (2群間のT検定)"])
    
    if task_type == "機械学習 (SHAP要因分析)":
        target_col = st.text_input("目的変数 (予測したい数値カラム名)")
        feature_cols_input = st.text_input("説明変数 (カンマ区切り)")
        
    elif task_type == "統計検定 (2群間のT検定)":
        group_col = st.text_input("グループ分けに使うカテゴリ変数 (例: 最寄駅)")
        val_col = st.text_input("比較する数値変数 (例: 総合満足度)")

    if st.button("🚀 モデリング・検定コードを生成", type="primary"):
        code3 = ""
        if task_type == "機械学習 (SHAP要因分析)" and target_col and feature_cols_input:
            code3 += "# --- 機械学習モデリングとSHAP値可視化 ---\n"
            code3 += "import shap\n"
            code3 += "from sklearn.ensemble import RandomForestRegressor\n"
            code3 += "from sklearn.model_selection import train_test_split\n\n"
            
            code3 += f"features = {parse_input(feature_cols_input)}\n"
            code3 += f"target = '{target_col.strip()}'\n\n"
            
            code3 += "ml_data = df[features + [target]].dropna()\n"
            code3 += "X, y = ml_data[features], ml_data[target]\n"
            code3 += "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n\n"
            
            code3 += "model = RandomForestRegressor(n_estimators=50, random_state=42)\n"
            code3 += "model.fit(X_train, y_train)\n"
            code3 += "print(f'モデル精度 (R2 Score): {model.score(X_test, y_test):.4f}')\n\n"
            
            code3 += "# SHAP値の計算と可視化\n"
            code3 += "explainer = shap.TreeExplainer(model)\n"
            code3 += "shap_values = explainer.shap_values(X)\n"
            code3 += "shap_importance = np.abs(shap_values).mean(axis=0)\n"
            code3 += "importance_df = pd.DataFrame({'説明変数': features, '平均SHAP値': shap_importance}).sort_values(by='平均SHAP値', ascending=True)\n\n"
            
            code3 += "fig_shap = px.bar(importance_df, x='平均SHAP値', y='説明変数', orientation='h', title='予測値への影響度 (SHAP)', template='plotly_white')\n"
            code3 += "fig_shap.show()\n"
            
        elif task_type == "統計検定 (2群間のT検定)" and group_col and val_col:
            code3 += "# --- 2群間の統計検定 (T検定) ---\n"
            code3 += "from scipy import stats\n\n"
            code3 += f"group_col, val_col = '{group_col.strip()}', '{val_col.strip()}'\n"
            code3 += "clean_df = df.dropna(subset=[group_col, val_col])\n"
            code3 += "unique_groups = clean_df[group_col].unique()\n\n"
            
            code3 += "if len(unique_groups) >= 2:\n"
            code3 += "    group_a, group_b = unique_groups[0], unique_groups[1]\n"
            code3 += "    data_a = clean_df[clean_df[group_col] == group_a][val_col]\n"
            code3 += "    data_b = clean_df[clean_df[group_col] == group_b][val_col]\n\n"
            code3 += "    t_stat, p_val = stats.ttest_ind(data_a, data_b, equal_var=False)\n"
            code3 += "    print(f'【T検定】 {group_a} vs {group_b}')\n"
            code3 += "    print(f'p値: {p_val:.5f} -> ', '有意差あり' if p_val < 0.05 else '有意差なし')\n"
            code3 += "else:\n"
            code3 += "    print('比較対象のグループが不足しています。')\n"

        if code3:
            st.markdown("---")
            st.write("💡 **【アクション】 以下のコードで、分析結果の論理的なエビデンスを確認してください。**")
            st.code(code3, language="python")
        else:
            st.warning("必要なカラム名を入力してください。")
