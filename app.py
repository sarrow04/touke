import streamlit as st

# ---------------------------------------------------------
# ページ設定
# ---------------------------------------------------------
st.set_page_config(page_title="Colab 2-Step Code Generator", layout="wide")
st.title("🛠️ 2段階コードジェネレーター (Google Colab専用)")
st.write("データを読み込まず、フェーズごとに堅牢な分析コードを発行します。")

tabs = st.tabs(["フェーズ1: 前処理・構造確認", "フェーズ2: 追加分析・モデリング"])

# =========================================================
# フェーズ1: 前処理・構造確認
# =========================================================
with tabs[0]:
    st.header("1. データの読み込み設定")
    col_file1, col_file2 = st.columns(2)
    with col_file1:
        file_type = st.radio("ファイル形式", ["CSV", "Excel"], key="file_type")
    with col_file2:
        file_name = st.text_input("Colabにアップロードするファイル名", "data.csv" if file_type == "CSV" else "data.xlsx")

    st.header("2. 前処理ルールの設定")
    numeric_cols_input = st.text_input(
        "数値型に強制変換するカラム名 (カンマ区切り)", 
        placeholder="例: 売上金額, 年齢, 月間乗車回数"
    )
    outlier_handling = st.checkbox("IQR法による異常値フラグ (is_outlier) の付与を行う", value=True)

    if st.button("🚀 フェーズ1のコードを生成", type="primary"):
        def parse_input(text):
            if not text: return "[]"
            return "[" + ", ".join([f"'{x.strip()}'" for x in text.split(",")]) + "]"

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
            code1 += "# 3. データ型の適正化 (数値型への変換)\n"
            code1 += f"num_cols = {parse_input(numeric_cols_input)}\n"
            code1 += "for col in num_cols:\n"
            code1 += "    if col in df.columns:\n"
            code1 += "        df[col] = pd.to_numeric(df[col], errors='coerce')\n\n"
            
            if outlier_handling:
                code1 += "# 4. 異常値の検出とフラグ付与 (IQR法)\n"
                code1 += "target_num_cols = [c for c in num_cols if c in df.columns]\n"
                code1 += "df['is_outlier'] = 0\n"
                code1 += "for col in target_num_cols:\n"
                code1 += "    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)\n"
                code1 += "    iqr = q3 - q1\n"
                code1 += "    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr\n"
                code1 += "    outlier_cond = (df[col] < lower_bound) | (df[col] > upper_bound)\n"
                code1 += "    df.loc[outlier_cond, 'is_outlier'] = 1\n\n"

        code1 += "# 5. 処理結果の確認 (Colabでの目視用)\n"
        code1 += "print('▼ データ型と欠損値の状況')\n"
        code1 += "display(df.info())\n"
        code1 += "print('\\n▼ 処理後データのプレビュー')\n"
        code1 += "display(df.head(5))\n"

        st.markdown("---")
        st.write("**以下のコードをColabの最初のセルに貼り付けて実行し、データが想定通りか確認してください。**")
        st.code(code1, language="python")

# =========================================================
# フェーズ2: 追加分析・モデリング
# =========================================================
with tabs[1]:
    st.header("追加分析の設定")
    st.write("※フェーズ1のコードが実行され、変数 `df` が存在することを前提とします。")
    
    task_type = st.radio("実行するタスク", ["SQL風データ抽出", "機械学習 (回帰/分類)とSHAP要因分析", "統計検定 (T検定)"])
    
    if task_type == "SQL風データ抽出":
        query_input = st.text_area("Pandasクエリ文", placeholder="例: 年齢 >= 30 and 顧客ランク == 'A'")
        
    elif task_type == "機械学習 (回帰/分類)とSHAP要因分析":
        ml_task = st.radio("予測タイプ", ["数値を予測 (回帰)", "カテゴリを予測 (分類)"])
        target_col = st.text_input("目的変数 (予測したいカラム名)")
        feature_cols_input = st.text_input("説明変数 (カンマ区切り)")
        
    elif task_type == "統計検定 (T検定)":
        group_col = st.text_input("グループ分けに使うカテゴリ変数 (例: 最寄駅)")
        val_col = st.text_input("比較する数値変数 (例: 総合満足度)")
        st.caption("※対象のカテゴリ内に存在する2つのユニークな値の平均を比較します。")

    if st.button("🚀 フェーズ2のコードを生成", type="primary"):
        st.markdown("---")
        code2 = ""
        
        if task_type == "SQL風データ抽出" and query_input:
            code2 += "# --- SQL風データ抽出 ---\n"
            code2 += f"query_str = \"{query_input.strip()}\"\n"
            code2 += "filtered_df = df.query(query_str)\n"
            code2 += "print(f'抽出結果: {len(filtered_df)}件')\n"
            code2 += "display(filtered_df.head())\n"
            
        elif task_type == "機械学習 (回帰/分類)とSHAP要因分析" and target_col and feature_cols_input:
            def parse_input_ml(text):
                return "[" + ", ".join([f"'{x.strip()}'" for x in text.split(",")]) + "]"
                
            code2 += "# --- 機械学習モデリングとSHAP値可視化 ---\n"
            code2 += "import shap\n"
            code2 += "from sklearn.model_selection import train_test_split\n"
            if ml_task == "数値を予測 (回帰)":
                code2 += "from sklearn.ensemble import RandomForestRegressor\n"
                code2 += "model = RandomForestRegressor(n_estimators=50, random_state=42)\n"
            else:
                code2 += "from sklearn.ensemble import RandomForestClassifier\n"
                code2 += "model = RandomForestClassifier(n_estimators=50, random_state=42)\n\n"
                
            code2 += f"features = {parse_input_ml(feature_cols_input)}\n"
            code2 += f"target = '{target_col.strip()}'\n\n"
            
            code2 += "# 欠損値を除外して学習データを準備\n"
            code2 += "ml_data = df[features + [target]].dropna()\n"
            code2 += "X = ml_data[features]\n"
            code2 += "y = ml_data[target]\n\n"
            
            code2 += "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n"
            code2 += "model.fit(X_train, y_train)\n"
            code2 += "print(f'モデルスコア: {model.score(X_test, y_test):.4f}')\n\n"
            
            code2 += "# SHAP値によるエビデンス可視化\n"
            code2 += "explainer = shap.TreeExplainer(model)\n"
            code2 += "shap_values = explainer.shap_values(X)\n"
            code2 += "shap_importance = np.abs(shap_values).mean(axis=0)\n"
            code2 += "importance_df = pd.DataFrame({'説明変数': features, '平均SHAP値': shap_importance}).sort_values(by='平均SHAP値', ascending=True)\n\n"
            
            code2 += "fig_shap = px.bar(importance_df, x='平均SHAP値', y='説明変数', orientation='h',\n"
            code2 += "                  title='予測値への影響度 (SHAP)', template='plotly_white')\n"
            code2 += "fig_shap.show()\n"
            
        elif task_type == "統計検定 (T検定)" and group_col and val_col:
            code2 += "# --- 2群間の統計検定 (T検定) ---\n"
            code2 += "from scipy import stats\n\n"
            code2 += f"group_col = '{group_col.strip()}'\n"
            code2 += f"val_col = '{val_col.strip()}'\n\n"
            
            code2 += "# 欠損値を除外してユニークなグループを取得\n"
            code2 += "clean_df = df.dropna(subset=[group_col, val_col])\n"
            code2 += "unique_groups = clean_df[group_col].unique()\n\n"
            
            code2 += "if len(unique_groups) >= 2:\n"
            code2 += "    group_a, group_b = unique_groups[0], unique_groups[1]\n"
            code2 += "    data_a = clean_df[clean_df[group_col] == group_a][val_col]\n"
            code2 += "    data_b = clean_df[clean_df[group_col] == group_b][val_col]\n\n"
            code2 += "    t_stat, p_val = stats.ttest_ind(data_a, data_b, equal_var=False)\n"
            code2 += "    print(f'【T検定】 {group_a} vs {group_b}')\n"
            code2 += "    print(f'p値: {p_val:.5f}')\n"
            code2 += "    if p_val < 0.05:\n"
            code2 += "        print('結果: 統計的に有意な差があります (p < 0.05)')\n"
            code2 += "    else:\n"
            code2 += "        print('結果: 統計的に有意な差は認められません')\n\n"
            code2 += "    # 比較用ボックスプロット\n"
            code2 += "    fig_box = px.box(clean_df[clean_df[group_col].isin([group_a, group_b])], \n"
            code2 += "                     x=group_col, y=val_col, template='plotly_white', title='グループ間の分布比較')\n"
            code2 += "    fig_box.show()\n"
            code2 += "else:\n"
            code2 += "    print('グループが2つ以上存在しません。')\n"

        if code2:
            st.write("**以下のコードをColabの次のセルに貼り付けて実行してください。**")
            st.code(code2, language="python")
        else:
            st.warning("必要な項目を入力してください。")
