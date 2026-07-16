import streamlit as st

# ---------------------------------------------------------
# ページ設定
# ---------------------------------------------------------
st.set_page_config(page_title="Colab 4-Step Pipeline Generator", layout="wide")
st.title("🛠️ 4段階確実実行型コードジェネレーター (Colab専用)")
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
# フェーズ1: 読込・プレビュー ➡️ 【カラム名の確認】へ
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
        code1 = f"import pandas as pd\nimport numpy as np\nimport unicodedata\nimport plotly.express as px\n\n"
        code1 += f"# 1. データの読み込み (すべて文字列として取得)\n"
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

        code1 += "# 3. データ構造の初期プレビュー\n"
        code1 += "print('▼ 現在のデータ型とメモリ使用量')\n"
        code1 += "display(df.info())\n"
        
        code1 += "print('\\n▼ 各カラムのデータの種類数(ユニーク数)と欠損値数')\n"
        code1 += "summary_df = pd.DataFrame({'ユニークなデータの種類数': df.nunique(), '欠損値の数': df.isnull().sum()})\n"
        code1 += "display(summary_df)\n"
        
        code1 += "print('\\n▼ データのプレビュー (先頭5行)')\n"
        code1 += "display(df.head(5))\n"

        st.markdown("---")
        st.write("💡 **【アクション】 以下のコードをColabで実行し、正確な「カラム名」と「データの種類数」を確認してください。**")
        st.code(code1, language="python")

# =========================================================
# フェーズ2: 型変換・異常値 ➡️ 【綺麗なデータ完成】へ
# =========================================================
with tabs[1]:
    st.header("2. データ型の適正化と異常値ハンドリング")
    st.warning("⚠️ フェーズ1で出力された結果を見ながら、変換したいカラム名をカンマ区切りで入力してください。")
    
    numeric_cols_input = st.text_input("📊 数値型 (int/float) に変換", placeholder="例: 月間乗車回数, 年齢, 総合満足度")
    datetime_cols_input = st.text_input("📅 日付型 (datetime) に変換", placeholder="例: 利用日, 登録日時")
    string_cols_input = st.text_input("🔤 文字列型 (str) に変換・保持", placeholder="例: 顧客ID, 最寄駅")
    
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
                code2 += "# 2. 異常値フラグ付与 (数値型カラムのみ対象)\n"
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
            st.write("💡 **【アクション】 以下のコードを実行し、データ型が正しく変換されたことを確認してください。**")
            st.code(code2, language="python")
        else:
            st.error("少なくとも1つのカラム名を入力してください。")

# =========================================================
# フェーズ3: 分析・可視化 ➡️ 【傾向の確認】へ
# =========================================================
with tabs[2]:
    st.header("3. データの絞り込みと構造的可視化")
    st.write("※綺麗なデータを使って、対象を絞り込み仮説を立てるための可視化を行います。")
    
    st.subheader("データの絞り込み (オプション)")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        st.write("📅 日付で絞り込む")
        filter_date_col = st.text_input("日付カラム名", placeholder="例: 利用日")
        filter_date_start = st.text_input("開始日 (YYYY-MM-DD)", placeholder="例: 2026-01-01")
        filter_date_end = st.text_input("終了日 (YYYY-MM-DD)", placeholder="例: 2026-12-31")
        
    with col_f2:
        st.write("📊 数値で絞り込む")
        filter_num_col = st.text_input("数値カラム名", placeholder="例: 月間乗車回数")
        filter_num_op = st.selectbox("条件", ["<=", ">=", "==", "<", ">"])
        filter_num_val = st.text_input("値 (数値)", placeholder="例: 10")
        
    with col_f3:
        st.write("🔤 カテゴリで絞り込む")
        filter_cat_col = st.text_input("文字列カラム名", placeholder="例: 最寄駅")
        filter_cat_val = st.text_input("一致する値", placeholder="例: 阿佐ヶ谷")

    st.markdown("---")
    st.subheader("可視化設定")
    x_col = st.text_input("X軸のカラム名", placeholder="例: 月間乗車回数")
    y_col = st.text_input("Y軸のカラム名 (数値推奨)", placeholder="例: 総合満足度")
    chart_type = st.radio("グラフの種類", ["散布図", "箱ひげ図", "棒グラフ", "折れ線グラフ (時系列用)"])
    color_outlier = st.checkbox("異常値フラグ (is_outlier) で色分けする", value=True)

    if st.button("🚀 フェーズ3のコードを生成", type="primary"):
        code3 = "# 1. データの絞り込み\n"
        code3 += "target_df = df.copy()\n\n"
        
        # 絞り込みコードの生成
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

        # 可視化コードの生成
        if x_col and y_col:
            code3 += "# 2. 構造的可視化 (Plotly)\n"
            code3 += "if len(target_df) > 0:\n"
            if color_outlier:
                code3 += "    if 'is_outlier' in target_df.columns:\n"
                code3 += "        target_df['データ区分'] = target_df['is_outlier'].map({0: '正常値', 1: '異常値'})\n"
                code3 += "        color_col = 'データ区分'\n"
                code3 += "        color_map = {'正常値': '#1f77b4', '異常値': '#d62728'}\n"
                code3 += "    else:\n"
                code3 += "        color_col = None\n"
                code3 += "        color_map = None\n\n"
            else:
                code3 += "    color_col = None\n"
                code3 += "    color_map = None\n\n"

            if chart_type == "散布図":
                code3 += f"    fig = px.scatter(target_df, x='{x_col.strip()}', y='{y_col.strip()}', color=color_col, color_discrete_map=color_map, template='plotly_white')\n"
            elif chart_type == "箱ひげ図":
                code3 += f"    fig = px.box(target_df, x='{x_col.strip()}', y='{y_col.strip()}', color=color_col, color_discrete_map=color_map, template='plotly_white')\n"
            elif chart_type == "棒グラフ":
                code3 += f"    fig = px.bar(target_df, x='{x_col.strip()}', y='{y_col.strip()}', color=color_col, color_discrete_map=color_map, template='plotly_white')\n"
            else:
                code3 += f"    fig = px.line(target_df, x='{x_col.strip()}', y='{y_col.strip()}', color=color_col, color_discrete_map=color_map, template='plotly_white')\n"
            
            code3 += "    fig.show()\n"
            code3 += "else:\n"
            code3 += "    print('条件に合致するデータが0件のためグラフは描画されません。')\n"

        if code3:
            st.markdown("---")
            st.write("💡 **【アクション】 以下のコードを実行し、データの傾向を分析してください。**")
            st.code(code3, language="python")
        else:
            st.warning("X軸とY軸のカラム名を入力してください。")

# =========================================================
# フェーズ4: モデリング・検定 ➡️ 【エビデンスの導出】へ
# =========================================================
with tabs[3]:
    st.header("4. エビデンスの導出 (モデリング・統計検定)")
    
    task_type = st.radio("実行するタスク", ["機械学習 (SHAP要因分析)", "統計検定 (2群間のT検定)"])
    
    if task_type == "機械学習 (SHAP要因分析)":
        target_col = st.text_input("目的変数 (予測したい数値カラム名)", placeholder="例: 総合満足度")
        feature_cols_input = st.text_input("説明変数 (カンマ区切り)", placeholder="例: 年齢, 月間乗車回数")
        
    elif task_type == "統計検定 (2群間のT検定)":
        group_col = st.text_input("グループ分けに使うカテゴリ変数", placeholder="例: 最寄駅")
        val_col = st.text_input("比較する数値変数", placeholder="例: 総合満足度")

    if st.button("🚀 フェーズ4のコードを生成", type="primary"):
        code4 = ""
        if task_type == "機械学習 (SHAP要因分析)" and target_col and feature_cols_input:
            code4 += "# --- 機械学習モデリングとSHAP値可視化 ---\n"
            code4 += "import shap\n"
            code4 += "from sklearn.ensemble import RandomForestRegressor\n"
            code4 += "from sklearn.model_selection import train_test_split\n\n"
            
            code4 += f"features = {parse_input(feature_cols_input)}\n"
            code4 += f"target = '{target_col.strip()}'\n\n"
            
            code4 += "ml_data = df[features + [target]].dropna()\n"
            code4 += "X, y = ml_data[features], ml_data[target]\n"
            code4 += "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n\n"
            
            code4 += "model = RandomForestRegressor(n_estimators=50, random_state=42)\n"
            code4 += "model.fit(X_train, y_train)\n"
            code4 += "print(f'モデル精度 (R2 Score): {model.score(X_test, y_test):.4f}')\n\n"
            
            code4 += "# SHAP値の計算と可視化\n"
            code4 += "explainer = shap.TreeExplainer(model)\n"
            code4 += "shap_values = explainer.shap_values(X)\n"
            code4 += "shap_importance = np.abs(shap_values).mean(axis=0)\n"
            code4 += "importance_df = pd.DataFrame({'説明変数': features, '平均SHAP値': shap_importance}).sort_values(by='平均SHAP値', ascending=True)\n\n"
            
            code4 += "fig_shap = px.bar(importance_df, x='平均SHAP値', y='説明変数', orientation='h', title='予測値への影響度 (SHAP)', template='plotly_white')\n"
            code4 += "fig_shap.show()\n"
            
        elif task_type == "統計検定 (2群間のT検定)" and group_col and val_col:
            code4 += "# --- 2群間の統計検定 (T検定) ---\n"
            code4 += "from scipy import stats\n\n"
            code4 += f"group_col, val_col = '{group_col.strip()}', '{val_col.strip()}'\n"
            code4 += "clean_df = df.dropna(subset=[group_col, val_col])\n"
            code4 += "unique_groups = clean_df[group_col].unique()\n\n"
            
            code4 += "if len(unique_groups) >= 2:\n"
            code4 += "    group_a, group_b = unique_groups[0], unique_groups[1]\n"
            code4 += "    data_a = clean_df[clean_df[group_col] == group_a][val_col]\n"
            code4 += "    data_b = clean_df[clean_df[group_col] == group_b][val_col]\n\n"
            code4 += "    t_stat, p_val = stats.ttest_ind(data_a, data_b, equal_var=False)\n"
            code4 += "    print(f'【T検定】 {group_a} vs {group_b}')\n"
            code4 += "    print(f'p値: {p_val:.5f} -> ', '有意差あり' if p_val < 0.05 else '有意差なし')\n"
            code4 += "else:\n"
            code4 += "    print('比較対象のグループが不足しています。')\n"

        if code4:
            st.markdown("---")
            st.write("💡 **【アクション】 以下のコードを実行し、分析の最終的なエビデンスを獲得してください。**")
            st.code(code4, language="python")
        else:
            st.warning("必要なカラム名を入力してください。")
