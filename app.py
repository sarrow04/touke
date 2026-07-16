import streamlit as st

# ---------------------------------------------------------
# ページ設定
# ---------------------------------------------------------
st.set_page_config(page_title="Colab 4-Step Pipeline Generator", layout="wide")
st.title("🛠️ 4段階確実実行型コードジェネレーター (japanize-matplotlib版)")
st.write("データの実態をColab上で確認しながら、論理的かつ安全に分析ステップを組み立てます。")

tabs = st.tabs([
    "フェーズ1: 読込・プレビュー", 
    "フェーズ2: 型変換・異常値", 
    "フェーズ3: 分析・可視化", 
    "フェーズ4: モデリング・検定"
])

def parse_input(text):
    if not text: return "[]"
    return "[" + ", ".join([f"'{x.strip()}'" for x in text.split(",")]) + "]"

# =========================================================
# フェーズ1: 読込・プレビュー
# =========================================================
with tabs[0]:
    st.header("1. データの読み込みと初期プレビュー")
    st.write("まずはすべて文字列として読み込み、ベースとなるクレンジングを行います。")
    
    col_file1, col_file2 = st.columns(2)
    with col_file1:
        file_type = st.radio("ファイル形式", ["CSV", "Excel"], key="file_type")
    with col_file2:
        file_name = st.text_input("Colabにアップロードしたファイル名", "data.csv" if file_type == "CSV" else "data.xlsx")

    if st.button("🚀 フェーズ1のコードを生成", type="primary"):
        code1 = "!pip install japanize-matplotlib\n\n"
        code1 += "import pandas as pd\nimport numpy as np\nimport unicodedata\n"
        code1 += "import matplotlib.pyplot as plt\nimport seaborn as sns\nimport japanize_matplotlib\n\n"
        code1 += "# グラフのスタイル設定\n"
        code1 += "sns.set_style('whitegrid')\n"
        code1 += "japanize_matplotlib.japanize()\n\n"

        code1 += f"# 1. データの読み込み (すべて文字列として取得)\n"
        if file_type == "CSV":
            code1 += f"df = pd.read_csv('{file_name}', dtype=str)\n\n"
        else:
            code1 += f"df = pd.read_excel('{file_name}', dtype=str)\n\n"
            
        code1 += "# 2. 文字列の自動クレンジング\n"
        code1 += "def clean_text(text):\n"
        code1 += "    if pd.isnull(text): return text\n"
        code1 += "    text = unicodedata.normalize('NFKC', str(text))\n"
        code1 += "    return text.strip()\n\n"
        code1 += "str_cols = df.select_dtypes(include=['object']).columns\n"
        code1 += "for col in str_cols:\n"
        code1 += "    df[col] = df[col].apply(clean_text)\n\n"

        code1 += "# 3. データ構造の初期プレビュー\n"
        code1 += "print('▼ 現在のデータ型とメモリ使用量')\n"
        code1 += "display(df.info())\n"
        code1 += "print('\\n▼ 各カラムのデータの種類数(ユニーク数)と欠損値数')\n"
        code1 += "summary_df = pd.DataFrame({'ユニークなデータの種類数': df.nunique(), '欠損値の数': df.isnull().sum()})\n"
        code1 += "display(summary_df)\n"
        code1 += "print('\\n▼ データのプレビュー (先頭5行)')\n"
        code1 += "display(df.head(5))\n"

        st.markdown("---")
        st.write("💡 ( **アクション** ) 以下のコードをColabで実行し、正確な「カラム名」と「データの種類数」を確認してください。")
        st.code(code1, language="python")

# =========================================================
# フェーズ2: 型変換・異常値
# =========================================================
with tabs[1]:
    st.header("2. データ型の適正化と異常値ハンドリング")
    st.warning("⚠️ フェーズ1で出力された結果を見ながら、変換したいカラム名をカンマ区切りで入力してください。")
    
    numeric_cols_input = st.text_input("📊 数値型 (int/float) に変換", placeholder="例: 月間乗車回数, 年齢, 総合満足度")
    datetime_cols_input = st.text_input("📅 日付型 (datetime) に変換", placeholder="例: 利用日")
    string_cols_input = st.text_input("🔤 文字列型 (str) に変換・保持", placeholder="例: 顧客ID")
    
    outlier_handling = st.checkbox("数値型カラムに対し、IQR法による異常値フラグ (is_outlier) の付与を行う", value=True)

    if st.button("🚀 フェーズ2のコードを生成", type="primary"):
        code2 = "# 1. データ型の適正化\n"
        has_input = False

        if numeric_cols_input.strip():
            has_input = True
            code2 += f"num_cols = {parse_input(numeric_cols_input)}\n"
            code2 += "for col in num_cols:\n"
            code2 += "    if col in df.columns:\n"
            code2 += "        df[col] = pd.to_numeric(df[col], errors='coerce')\n\n"
            
        if datetime_cols_input.strip():
            has_input = True
            code2 += f"date_cols = {parse_input(datetime_cols_input)}\n"
            code2 += "for col in date_cols:\n"
            code2 += "    if col in df.columns:\n"
            code2 += "        df[col] = pd.to_datetime(df[col], errors='coerce')\n\n"

        if string_cols_input.strip():
            has_input = True
            code2 += f"str_cols = {parse_input(string_cols_input)}\n"
            code2 += "for col in str_cols:\n"
            code2 += "    if col in df.columns:\n"
            code2 += "        df[col] = df[col].astype(str)\n\n"

        if has_input:
            if outlier_handling and numeric_cols_input.strip():
                code2 += "# 2. 異常値フラグ付与\n"
                code2 += "target_num_cols = [c for c in num_cols if c in df.columns]\n"
                code2 += "df['is_outlier'] = 0\n"
                code2 += "for col in target_num_cols:\n"
                code2 += "    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)\n"
                code2 += "    iqr = q3 - q1\n"
                code2 += "    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr\n"
                code2 += "    outlier_cond = (df[col] < lower_bound) | (df[col] > upper_bound)\n"
                code2 += "    df.loc[outlier_cond, 'is_outlier'] = 1\n\n"

            code2 += "# 3. 変換後の最終確認\n"
            code2 += "print('▼ 変換後のデータ型')\n"
            code2 += "display(df.dtypes)\n"
            code2 += "print('\\n▼ 基本統計量 (全体)')\n"
            code2 += "display(df.describe(include='all'))\n"

            st.markdown("---")
            st.write("💡 ( **アクション** ) 以下のコードを実行し、データ型が正しく変換されたことを確認してください。")
            st.code(code2, language="python")
        else:
            st.error("少なくとも1つのカラム名を入力してください。")

# =========================================================
# フェーズ3: 分析・可視化
# =========================================================
with tabs[2]:
    st.header("3. データの絞り込みと構造的可視化")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_date_col = st.text_input("📅 絞り込み: 日付カラム")
        filter_date_start = st.text_input("開始日 (YYYY-MM-DD)")
        filter_date_end = st.text_input("終了日 (YYYY-MM-DD)")
    with col_f2:
        filter_num_col = st.text_input("📊 絞り込み: 数値カラム")
        filter_num_op = st.selectbox("条件", ["<=", ">=", "==", "<", ">"])
        filter_num_val = st.text_input("値 (数値)")
    with col_f3:
        filter_cat_col = st.text_input("🔤 絞り込み: カテゴリカラム")
        filter_cat_val = st.text_input("一致する値")

    st.markdown("---")
    x_col = st.text_input("X軸のカラム名")
    y_col = st.text_input("Y軸のカラム名 (数値推奨)")
    chart_types = st.multiselect("グラフの種類", ["散布図", "箱ひげ図", "棒グラフ", "折れ線グラフ"], default=["散布図"])
    color_outlier = st.checkbox("異常値フラグ (is_outlier) で色分けする", value=True)

    if st.button("🚀 フェーズ3のコードを生成", type="primary"):
        code3 = "# 1. データの絞り込み\n"
        code3 += "target_df = df.copy()\n\n"
        
        if filter_date_col and (filter_date_start or filter_date_end):
            if filter_date_start:
                code3 += f"target_df = target_df[target_df['{filter_date_col.strip()}'] >= '{filter_date_start.strip()}']\n"
            if filter_date_end:
                code3 += f"target_df = target_df[target_df['{filter_date_col.strip()}'] <= '{filter_date_end.strip()}']\n"
        if filter_num_col and filter_num_val:
            code3 += f"target_df = target_df[target_df['{filter_num_col.strip()}'] {filter_num_op} {filter_num_val.strip()}]\n"
        if filter_cat_col and filter_cat_val:
            code3 += f"target_df = target_df[target_df['{filter_cat_col.strip()}'] == '{filter_cat_val.strip()}']\n"

        code3 += "print(f'絞り込み後の対象件数: {len(target_df)}件')\n\n"

        if x_col and y_col and chart_types:
            code3 += "# 2. 構造的可視化 (Seaborn)\n"
            code3 += "if len(target_df) > 0:\n"
            if color_outlier:
                code3 += "    if 'is_outlier' in target_df.columns:\n"
                code3 += "        target_df['データ区分'] = target_df['is_outlier'].map({0: '正常値', 1: '異常値'})\n"
                code3 += "        hue_col = 'データ区分'\n"
                code3 += "        palette = {'正常値': '#1f77b4', '異常値': '#d62728'}\n"
                code3 += "    else:\n"
                code3 += "        hue_col = None\n"
                code3 += "        palette = None\n\n"
            else:
                code3 += "    hue_col = None\n"
                code3 += "    palette = None\n\n"

            for c_type in chart_types:
                code3 += f"    plt.figure(figsize=(10, 6))\n"
                if c_type == "散布図":
                    code3 += f"    sns.scatterplot(data=target_df, x='{x_col.strip()}', y='{y_col.strip()}', hue=hue_col, palette=palette)\n"
                elif c_type == "箱ひげ図":
                    code3 += f"    sns.boxplot(data=target_df, x='{x_col.strip()}', y='{y_col.strip()}', hue=hue_col, palette=palette)\n"
                elif c_type == "棒グラフ":
                    code3 += f"    sns.barplot(data=target_df, x='{x_col.strip()}', y='{y_col.strip()}', hue=hue_col, palette=palette, errorbar=None)\n"
                else:
                    code3 += f"    sns.lineplot(data=target_df, x='{x_col.strip()}', y='{y_col.strip()}', hue=hue_col, palette=palette)\n"
                code3 += f"    plt.title('{c_type}: {x_col.strip()} vs {y_col.strip()}')\n"
                code3 += f"    plt.tight_layout()\n"
                code3 += f"    plt.show()\n\n"
                
        if code3 and x_col and y_col:
            st.markdown("---")
            st.write("💡 ( **アクション** ) 以下のコードを実行し、データの傾向を分析してください。")
            st.code(code3, language="python")

# =========================================================
# フェーズ4: モデリング・検定 ➡️ 大幅アップデート！
# =========================================================
with tabs[3]:
    st.header("4. エビデンスの導出 (モデリング・統計検定)")
    
    task_type = st.radio("実行するタスク", ["機械学習モデル構築 (SHAP分析つき)", "統計検定 (自動判別)"])
    
    if task_type == "機械学習モデル構築 (SHAP分析つき)":
        ml_task = st.radio("予測タイプ", ["回帰 (数値を予測)", "分類 (カテゴリを予測)"])
        ml_model = st.selectbox("使用するモデル", ["LightGBM", "Random Forest", "XGBoost"])
        target_col = st.text_input("目的変数 (予測したいカラム名)", placeholder="例: 総合満足度")
        feature_cols_input = st.text_input("説明変数 (カンマ区切り)", placeholder="例: 年齢, 月間乗車回数")
        
    elif task_type == "統計検定 (自動判別)":
        st.info("💡 グループの数を自動でカウントし、「2群ならT検定」「3群以上ならANOVA」を自動実行します。")
        group_col = st.text_input("グループ分けに使うカテゴリ変数", placeholder="例: 最寄駅")
        val_col = st.text_input("比較する数値変数", placeholder="例: 総合満足度")

    if st.button("🚀 フェーズ4のコードを生成", type="primary"):
        code4 = ""
        
        # --- 機械学習ブロック ---
        if task_type == "機械学習モデル構築 (SHAP分析つき)" and target_col and feature_cols_input:
            code4 += "# --- 機械学習モデリングとSHAP値可視化 ---\n"
            code4 += "import shap\n"
            code4 += "from sklearn.model_selection import train_test_split\n"
            
            if ml_task == "回帰 (数値を予測)":
                if ml_model == "LightGBM":
                    code4 += "import lightgbm as lgb\nmodel = lgb.LGBMRegressor(random_state=42)\n"
                elif ml_model == "Random Forest":
                    code4 += "from sklearn.ensemble import RandomForestRegressor\nmodel = RandomForestRegressor(n_estimators=100, random_state=42)\n"
                elif ml_model == "XGBoost":
                    code4 += "import xgboost as xgb\nmodel = xgb.XGBRegressor(random_state=42)\n"
                score_metric = "R2 Score"
            else:
                if ml_model == "LightGBM":
                    code4 += "import lightgbm as lgb\nmodel = lgb.LGBMClassifier(random_state=42)\n"
                elif ml_model == "Random Forest":
                    code4 += "from sklearn.ensemble import RandomForestClassifier\nmodel = RandomForestClassifier(n_estimators=100, random_state=42)\n"
                elif ml_model == "XGBoost":
                    code4 += "import xgboost as xgb\nmodel = xgb.XGBClassifier(random_state=42)\n"
                score_metric = "Accuracy"
            
            code4 += f"\nfeatures = {parse_input(feature_cols_input)}\n"
            code4 += f"target = '{target_col.strip()}'\n\n"
            code4 += "ml_data = df[features + [target]].dropna()\n"
            code4 += "X, y = ml_data[features], ml_data[target]\n"
            code4 += "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n\n"
            
            code4 += "model.fit(X_train, y_train)\n"
            code4 += f"print(f'モデル精度 ({score_metric}): {{model.score(X_test, y_test):.4f}}')\n\n"
            
            code4 += "# SHAP値の計算と可視化\n"
            code4 += "explainer = shap.TreeExplainer(model)\n"
            code4 += "shap_values = explainer.shap_values(X)\n\n"
            
            code4 += "# 分類モデルでリスト形式が返却された場合の安全処理\n"
            code4 += "if isinstance(shap_values, list):\n"
            code4 += "    shap_values = shap_values[1]\n\n"
            
            code4 += "shap_importance = np.abs(shap_values).mean(axis=0)\n"
            code4 += "importance_df = pd.DataFrame({'説明変数': features, '平均SHAP値': shap_importance}).sort_values(by='平均SHAP値', ascending=False)\n\n"
            
            code4 += "plt.figure(figsize=(10, 6))\n"
            code4 += "sns.barplot(data=importance_df, x='平均SHAP値', y='説明変数', color='steelblue')\n"
            code4 += "plt.title(f'予測値への影響度 (SHAP / {ml_model})')\n"
            code4 += "plt.tight_layout()\n"
            code4 += "plt.show()\n"
            
        # --- 統計検定ブロック ---
        elif task_type == "統計検定 (自動判別)" and group_col and val_col:
            code4 += "# --- 統計検定 (データ数に基づく自動判別) ---\n"
            code4 += "from scipy import stats\n\n"
            code4 += f"group_col, val_col = '{group_col.strip()}', '{val_col.strip()}'\n"
            code4 += "clean_df = df.dropna(subset=[group_col, val_col])\n"
            code4 += "unique_groups = clean_df[group_col].unique()\n"
            code4 += "n_groups = len(unique_groups)\n\n"
            
            code4 += "if n_groups == 2:\n"
            code4 += "    # 2群間の比較 (ウェルチのT検定)\n"
            code4 += "    group_a, group_b = unique_groups[0], unique_groups[1]\n"
            code4 += "    data_a = clean_df[clean_df[group_col] == group_a][val_col]\n"
            code4 += "    data_b = clean_df[clean_df[group_col] == group_b][val_col]\n"
            code4 += "    t_stat, p_val = stats.ttest_ind(data_a, data_b, equal_var=False)\n"
            code4 += "    print(f'【自動判別: ウェルチのT検定】 {group_a} vs {group_b}')\n"
            code4 += "    print(f'p値: {p_val:.5f} -> ', '有意差あり' if p_val < 0.05 else '有意差なし')\n"
            code4 += "elif n_groups >= 3:\n"
            code4 += "    # 3群以上の比較 (一元配置分散分析: ANOVA)\n"
            code4 += "    groups_data = [clean_df[clean_df[group_col] == g][val_col] for g in unique_groups]\n"
            code4 += "    f_stat, p_val = stats.f_oneway(*groups_data)\n"
            code4 += "    print(f'【自動判別: 分散分析(ANOVA)】 {n_groups}グループ間の比較')\n"
            code4 += "    print(f'p値: {p_val:.5f} -> ', '有意差あり' if p_val < 0.05 else '有意差なし')\n"
            code4 += "else:\n"
            code4 += "    print('比較対象のグループが不足しています（2つ以上必要です）。')\n\n"
            
            code4 += "if n_groups >= 2:\n"
            code4 += "    plt.figure(figsize=(8, 5))\n"
            code4 += "    sns.boxplot(data=clean_df, x=group_col, y=val_col, palette='Set2')\n"
            code4 += "    plt.title('グループ間の分布比較')\n"
            code4 += "    plt.tight_layout()\n"
            code4 += "    plt.show()\n"

        if code4:
            st.markdown("---")
            st.write("💡 ( **アクション** ) 以下のコードを実行し、分析の最終的なエビデンスを獲得してください。")
            st.code(code4, language="python")
        else:
            st.warning("必要なカラム名を入力してください。")
