import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import hashlib
from scipy import stats
import shap
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
import io

# ---------------------------------------------------------
# ページ設定 & デザイン (ソリッドで機能的なデザイン)
# ---------------------------------------------------------
st.set_page_config(
    page_title="DataAnalyst Pro - オールインワン分析ツール",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ログ記録用関数
def add_log(action):
    if "logs" not in st.session_state:
        st.session_state.logs = []
    st.session_state.logs.append(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] {action}")

# ---------------------------------------------------------
# サイドバー: ファイルアップロード & 設定
# ---------------------------------------------------------
with st.sidebar:
    st.header("📁 データ読み込み設定")
    
    # 0落ち対策のオプション
    keep_str = st.checkbox("数値を文字列として読み込む (0落ち防止)", value=False, 
                           help="電話番号や社員番号などの『0から始まるID』が消えるのを防ぐため、すべてのデータを文字列として読み込みます。")
    
    uploaded_file = st.file_uploader("CSVまたはExcelファイルをアップロードしてください", type=["csv", "xlsx"])
    
    st.markdown("---")
    st.subheader("🛠 共通オプション")
    st.caption("iPadやブラウザ環境でも軽快に動作するよう、過度な描画を抑えた構造設計にしています。")

# ---------------------------------------------------------
# データ読み込み処理
# ---------------------------------------------------------
df = None
if uploaded_file is not None:
    try:
        file_name = uploaded_file.name
        if file_name.endswith(".csv"):
            # 文字化け対策: UTF-8, Shift-JIS, cp932 を順次試行
            encodings = ["utf-8", "shift-jis", "cp932", "utf-8-sig"]
            for enc in encodings:
                try:
                    uploaded_file.seek(0)
                    dtype_setting = str if keep_str else None
                    df = pd.read_csv(uploaded_file, encoding=enc, dtype=dtype_setting)
                    add_log(f"CSVファイルを読み込みました (エンコーディング: {enc}, 0落ち防止: {keep_str})")
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                st.sidebar.error("ファイルの文字コードを自動判定できませんでした。UTF-8かShift-JISで保存し直してください。")
        else:
            # Excelファイル
            dtype_setting = str if keep_str else None
            df = pd.read_excel(uploaded_file, dtype=dtype_setting)
            add_log(f"Excelファイルを読み込みました (0落ち防止: {keep_str})")
            
    except Exception as e:
        st.sidebar.error(f"ファイル読み込みエラー: {e}")

# ---------------------------------------------------------
# メイン画面のタブ構成
# ---------------------------------------------------------
if df is not None:
    st.title("📊 DataAnalyst Pro")
    st.caption(f"現在のデータ: {uploaded_file.name} ({df.shape[0]} 行 × {df.shape[1]} 列)")

    tabs = st.tabs([
        "📈 ダッシュボード", 
        "🔍 基礎統計 & 外れ値", 
        "🔗 相関分析", 
        "🛡 個人情報匿名化", 
        "💻 SQLデータ抽出", 
        "🤖 機械学習 (SHAP)", 
        "🧪 統計検定", 
        "📝 分析ログ"
    ])

    # ---------------------------------------------------------
    # タブ1: ダッシュボード
    # ---------------------------------------------------------
    with tabs[0]:
        st.subheader("📊 クイック・ダッシュボード")
        
        # 簡易的なKPI表示
        col1, col2, col3 = st.columns(3)
        col1.metric("総行数", f"{df.shape[0]} 件")
        col2.metric("総カラム数", f"{df.shape[1]} 列")
        col3.metric("欠損値の合計数", f"{df.isnull().sum().sum()} 箇所")
        
        st.markdown("---")
        
        # グラフ作成セクション
        st.write("#### 📈 データ可視化")
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
        
        col_x, col_y, col_type = st.columns(3)
        with col_x:
            x_axis = st.selectbox("X軸にするカラムを選択", options=df.columns)
        with col_y:
            y_axis = st.selectbox("Y軸にするカラムを選択 (数値推奨)", options=num_cols if num_cols else df.columns)
        with col_type:
            chart_type = st.selectbox("グラフの種類", ["散布図", "棒グラフ", "折れ線グラフ", "箱ひげ図"])
            
        if st.button("グラフを描画", key="btn_dashboard"):
            if chart_type == "散布図":
                fig = px.scatter(df, x=x_axis, y=y_axis, template="plotly_white", color_discrete_sequence=["#1f77b4"])
            elif chart_type == "棒グラフ":
                fig = px.bar(df, x=x_axis, y=y_axis, template="plotly_white", color_discrete_sequence=["#2ca02c"])
            elif chart_type == "折れ線グラフ":
                fig = px.line(df, x=x_axis, y=y_axis, template="plotly_white", color_discrete_sequence=["#ff7f0e"])
            elif chart_type == "箱ひげ図":
                fig = px.box(df, x=x_axis, y=y_axis, template="plotly_white", color_discrete_sequence=["#9467bd"])
                
            st.plotly_chart(fig, use_container_width=True)
            add_log(f"ダッシュボードにて「{chart_type} (X: {x_axis}, Y: {y_axis})」を描画しました。")

    # ---------------------------------------------------------
    # タブ2: 基礎統計 & 外れ値
    # ---------------------------------------------------------
    with tabs[1]:
        st.subheader("🔍 カラム情報と基本統計量")
        
        # カラム一覧
        st.write("#### カラムデータ型一覧")
        col_info = pd.DataFrame({
            "データ型": df.dtypes.astype(str),
            "欠損値数": df.isnull().sum(),
            "ユニーク値数": df.nunique()
        })
        st.dataframe(col_info, use_container_width=True)
        
        # 基本統計量
        st.write("#### 数値データの基本統計量 (describe)")
        if len(num_cols) > 0:
            st.dataframe(df.describe(), use_container_width=True)
        else:
            st.warning("数値カラムが存在しません。")
            
        st.markdown("---")
        st.subheader("🚨 外れ値の検出 (IQR法)")
        if len(num_cols) > 0:
            outlier_col = st.selectbox("外れ値をチェックするカラム", options=num_cols, key="outlier_select")
            
            # IQR計算
            q1 = df[outlier_col].quantile(0.25)
            q3 = df[outlier_col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = df[(df[outlier_col] < lower_bound) | (df[outlier_col] > upper_bound)]
            
            st.write(f"下限しきい値: `{lower_bound:.2f}` / 上限しきい値: `{upper_bound:.2f}`")
            st.write(f"検出された外れ値の数: `{len(outliers)}` 件")
            
            if len(outliers) > 0:
                st.dataframe(outliers, use_container_width=True)
                add_log(f"基礎統計タブで「{outlier_col}」の外れ値 {len(outliers)} 件を検出しました。")
        else:
            st.info("数値データがないため外れ値の検出はスキップします。")

    # ---------------------------------------------------------
    # タブ3: 相関分析
    # ---------------------------------------------------------
    with tabs[2]:
        st.subheader("🔗 相関係数の確認")
        if len(num_cols) >= 2:
            corr_matrix = df[num_cols].corr()
            st.write("#### 相関係数行列")
            st.dataframe(corr_matrix.style.background_gradient(cmap="coolwarm", axis=None), use_container_width=True)
            
            # ヒートマップ表示
            st.write("#### ヒートマップ表示")
            fig_corr = px.imshow(corr_matrix, text_auto=True, color_continuous_scale="RdBu_r", aspect="auto")
            st.plotly_chart(fig_corr, use_container_width=True)
            add_log("相関分析で相関係数行列を算出しました。")
        else:
            st.warning("相関を計算するには、数値カラムが2つ以上必要です。")

    # ---------------------------------------------------------
    # タブ4: 個人情報匿名化
    # ---------------------------------------------------------
    with tabs[3]:
        st.subheader("🛡 個人情報（名前・ID等）のハッシュ化（匿名化）")
        st.write("特定の個人情報カラムを選択し、SHA-256を用いて『不可逆なハッシュ値』に置き換える処理を行います。")
        
        target_col = st.selectbox("匿名化（ハッシュ変換）するカラムを選択", options=df.columns, key="anon_col")
        
        if st.button("ハッシュ匿名化を実行"):
            # 文字列に変換してからハッシュ化
            df[target_col] = df[target_col].astype(str).apply(
                lambda x: hashlib.sha256(x.encode()).hexdigest()[:12] if pd.notnull(x) and x != 'nan' else x
            )
            st.success(f"カラム「{target_col}」を正常にハッシュ化しました！")
            st.dataframe(df.head(10), use_container_width=True)
            add_log(f"個人情報保護のためカラム「{target_col}」をハッシュ化しました。")

    # ---------------------------------------------------------
    # タブ5: SQLデータ抽出
    # ---------------------------------------------------------
    with tabs[4]:
        st.subheader("💻 SQLクエリによるデータ抽出")
        st.write("Pandasデータフレームを `df` という名前の仮のテーブルとして、SQLライクな条件指定でデータを抽出できます。")
        st.caption("※内部的にPandasの `query` メソッド、またはSQLライクな構文パーサーを再現します。")
        
        sql_example = "df.query('カラム名 == 値')"
        sql_query = st.text_area("Pandasクエリ文 (例: `Age > 30` や `City == 'Tokyo'`)", value="")
        
        if st.button("クエリ実行"):
            if sql_query.strip():
                try:
                    query_result = df.query(sql_query)
                    st.write(f"🔍 抽出結果: {len(query_result)} 件")
                    st.dataframe(query_result, use_container_width=True)
                    add_log(f"SQLクエリ実行: '{sql_query}' (取得件数: {len(query_result)} 件)")
                except Exception as e:
                    st.error(f"クエリ実行エラー: {e}\nPandasのquery構文規則に従って記述してください。")
            else:
                st.warning("クエリを入力してください。")

    # ---------------------------------------------------------
    # タブ6: 機械学習 (SHAP)
    # ---------------------------------------------------------
    with tabs[5]:
        st.subheader("🤖 機械学習モデルの作成とSHAP値による要因可視化")
        st.write("指定した目的変数を予測する簡易モデルを作成し、どのカラムが予測に寄与しているかをSHAP値で可視化します。")
        
        if len(num_cols) >= 2:
            col_target, col_features = st.columns([1, 2])
            with col_target:
                target_y = st.selectbox("目的変数 (予測したい数値カラム)", options=num_cols, key="ml_target")
            with col_features:
                features_x = st.multiselect("説明変数 (予測の手がかりにする数値カラム)", 
                                             options=[c for c in num_cols if c != target_y],
                                             default=[c for c in num_cols if c != target_y][:4])
                
            if st.button("機械学習モデルを訓練してSHAPを計算"):
                if len(features_x) > 0:
                    try:
                        # 欠損値を一時的に埋める
                        ml_data = df[[target_y] + features_x].dropna()
                        X = ml_data[features_x]
                        y = ml_data[target_y]
                        
                        # モデル定義と訓練
                        model = RandomForestRegressor(n_estimators=50, random_state=42)
                        model.fit(X, y)
                        
                        # SHAP値計算
                        explainer = shap.TreeExplainer(model)
                        shap_values = explainer.shap_values(X)
                        
                        # 特徴量重要度の可視化
                        st.write("#### 📊 SHAPベースの特徴量重要度")
                        shap_importance = np.abs(shap_values).mean(axis=0)
                        importance_df = pd.DataFrame({
                            "説明変数": features_x,
                            "平均SHAP値 (重要度)": shap_importance
                        }).sort_values(by="平均SHAP値 (重要度)", ascending=True)
                        
                        fig_shap = px.bar(importance_df, x="平均SHAP値 (重要度)", y="説明変数", orientation="h",
                                          title="どの特徴量が予測値に影響を与えているか (平均SHAP値)",
                                          template="plotly_white")
                        st.plotly_chart(fig_shap, use_container_width=True)
                        
                        # 予測値と実績値のプロット
                        st.write("#### 🎯 予測値 vs 実績値")
                        preds = model.predict(X)
                        pred_df = pd.DataFrame({"実績値": y, "予測値": preds})
                        fig_pred = px.scatter(pred_df, x="実績値", y="予測値", trendline="ols", template="plotly_white")
                        st.plotly_chart(fig_pred, use_container_width=True)
                        
                        add_log(f"機械学習: 目的変数 '{target_y}' に対し、SHAP値による要因可視化を実行しました。")
                        
                    except Exception as e:
                        st.error(f"モデル訓練エラー: {e}")
                else:
                    st.warning("説明変数を1つ以上選択してください。")
        else:
            st.warning("機械学習を実行するには、数値型カラムが2つ以上必要です。")

    # ---------------------------------------------------------
    # タブ7: 統計検定
    # ---------------------------------------------------------
    with tabs[6]:
        st.subheader("🧪 2群間の統計検定 (T検定)")
        st.write("カテゴリー変数でグループを2つに分け、指定した数値カラムの平均値に有意な差があるかを検定します。")
        
        if len(cat_cols) > 0 and len(num_cols) > 0:
            col_group, col_val = st.columns(2)
            with col_group:
                group_col = st.selectbox("グループ分けに使うカテゴリ変数", options=cat_cols)
            with col_val:
                val_col = st.selectbox("比較する数値変数", options=num_cols)
                
            # ユニークなカテゴリの抽出
            unique_cats = df[group_col].dropna().unique().tolist()
            if len(unique_cats) >= 2:
                cat_a = st.selectbox("グループA", options=unique_cats, index=0)
                cat_b = st.selectbox("グループB", options=unique_cats, index=1 if len(unique_cats) > 1 else 0)
                
                if st.button("ウェルチのT検定を実行"):
                    group_a_data = df[df[group_col] == cat_a][val_col].dropna()
                    group_b_data = df[df[group_col] == cat_b][val_col].dropna()
                    
                    if len(group_a_data) > 1 and len(group_b_data) > 1:
                        t_stat, p_val = stats.ttest_ind(group_a_data, group_b_data, equal_var=False)
                        
                        st.write("#### 📊 検定結果")
                        st.write(f"**{cat_a} の平均値**: `{group_a_data.mean():.4f}` (サンプルサイズ: {len(group_a_data)})")
                        st.write(f"**{cat_b} の平均値**: `{group_b_data.mean():.4f}` (サンプルサイズ: {len(group_b_data)})")
                        st.write(f"**t統計量**: `{t_stat:.4f}`")
                        st.write(f"**p値**: `{p_val:.6f}`")
                        
                        if p_val < 0.05:
                            st.success("結果: 有意差あり (p < 0.05) ※5%水準で統計的に有意な差が認められます。")
                        else:
                            st.info("結果: 有意差なし (p >= 0.05) ※統計的に有意な差は認められません。")
                            
                        # 箱ひげ図で比較表示
                        compare_df = df[df[group_col].isin([cat_a, cat_b])]
                        fig_box = px.box(compare_df, x=group_col, y=val_col, color=group_col, template="plotly_white")
                        st.plotly_chart(fig_box, use_container_width=True)
                        
                        add_log(f"統計検定: {group_col} ({cat_a} vs {cat_b}) に対する {val_col} のT検定を実行 (p={p_val:.6f})")
                    else:
                        st.error("十分なデータがありません。各グループに最低2つ以上のサンプルが必要です。")
            else:
                st.warning("グループ分けに必要なカテゴリが2つ以上見つかりません。")
        else:
            st.warning("統計検定には、カテゴリ型カラムと数値型カラムがそれぞれ1つ以上必要です。")

    # ---------------------------------------------------------
    # タブ8: 分析ログ
    # ---------------------------------------------------------
    with tabs[7]:
        st.subheader("📝 アプリ操作・分析ログ")
        st.write("現在のセッション内での分析履歴が表示されます。")
        
        if "logs" in st.session_state and len(st.session_state.logs) > 0:
            for log in reversed(st.session_state.logs):
                st.code(log)
        else:
            st.info("まだ操作ログがありません。")

else:
    # ファイルがアップロードされていないときの初期表示
    st.title("📊 DataAnalyst Pro")
    st.info("左側のサイドバーからCSVまたはExcelファイルをアップロードして解析を開始してください。")
    
    st.markdown("""
    ### 🔥 主な搭載機能一覧
    1. **文字化け＆0落ち防止対策** Shift-JIS/UTF-8の自動判別機能、および社員番号や電話番号の先頭ゼロ(`0`)を保護したまま読み込む機能を搭載。
    2. **ダッシュボード可視化** インタラクティブな描画エンジン(Plotly)を使い、iPadでもサクサク動く高速なグラフ表示。
    3. **基礎統計 & 外れ値検出** Pandas標準の要約統計量算出に加え、IQR法を用いた外れ値レコードの自動抽出機能。
    4. **相関行列 & ヒートマップ** カラム間の相関強さを瞬時に色分け表示するヒートマップ。
    5. **個人情報のハッシュ匿名化** 名前や連絡先などのカラムに対して、復元不可能なSHA-256ハッシュを自動適用するデータ前処理。
    6. **SQL風データ抽出** Pandasの `query()` 機能を使用した簡易データフィルタ。
    7. **機械学習 & SHAP値要因分析** ランダムフォレストを裏側で高速訓練し、どのカラムが目的変数に寄与しているかをSHAP値で可視化。
    8. **2群間のT検定** カテゴリ変数でグループ分けし、平均値の差を科学的にテストする本格統計検定。
    """)
