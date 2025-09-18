# professional_dashboard.py (全版本兼容版)

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import altair as alt

# --- 数据库文件名 ---
DATABASE_FILE = 'sales_database.db'

# --- 页面配置 ---
st.set_page_config(layout="wide", page_title="专业销售数据仪表盘")

# --- 数据加载函数 ---
@st.cache_data(ttl=600)
def load_data_from_db():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        df = pd.read_sql_query("SELECT * FROM sales", conn)
        conn.close()
        df['日期 (Date)'] = pd.to_datetime(df['日期 (Date)'])
        return df
    except Exception:
        return pd.DataFrame()

df_all = load_data_from_db()

# --- 自然语言理解 (NLU) 核心 ---
def parse_query(query, data_df):
    query = query.lower()
    reps = data_df['销售代表 (Rep)'].unique()
    regions = data_df['销售区域 (Region)'].unique()
    categories = data_df['产品大类 (Category)'].unique()
    found_rep = [rep for rep in reps if rep.lower() in query]
    found_region = [region for region in regions if region in query]
    found_category = [category for category in categories if category.lower() in query]
    filtered_df = data_df.copy()
    if found_rep:
        filtered_df = filtered_df[filtered_df['销售代表 (Rep)'].isin(found_rep)]
    if found_region:
        filtered_df = filtered_df[filtered_df['销售区域 (Region)'].isin(found_region)]
    if found_category:
        filtered_df = filtered_df[filtered_df['产品大类 (Category)'].isin(found_category)]
    if '订单' in query or '卖了多少笔' in query:
        count = len(filtered_df)
        return f"查询到 **{count}** 笔相关订单。"
    else:
        total_sales = filtered_df['销售额 (Sales)'].sum()
        return f"查询到的相关总销售额为: **¥ {total_sales:,.2f}**"

# --- 仪表盘主界面 ---
st.title("🚀 专业销售数据智能仪表盘")

if df_all.empty:
    st.warning("数据库中尚无数据。请先运行 `update_database.py` 来添加数据。")
    st.stop()

# --- 智能问答区域 (使用兼容所有版本的 st.form) ---
st.markdown("---")
st.header("💡 智能问答引擎")
st.write("您可以像聊天一样提问，例如：“张三在华东的总业绩是多少？” 或 “软件产品有多少笔订单？”")

with st.form(key='qna_form'):
    user_query = st.text_input("请在这里输入您的问题:", key='query_input')
    submit_button = st.form_submit_button(label='提交问题')

if submit_button and user_query:
    with st.spinner("正在分析您的问题并查询数据..."):
        answer = parse_query(user_query, df_all)
    st.success(f"**问:** {user_query}\n\n**答:** {answer}") # 使用 st.success 来展示回答
st.markdown("---")


# --- 侧边栏筛选器 ---
st.sidebar.header("筛选与导航")
selected_date = st.sidebar.date_input(
    "选择查看日期",
    value=df_all['日期 (Date)'].max(),
    min_value=df_all['日期 (Date)'].min(),
    max_value=df_all['日期 (Date)'].max(),
    key="date_selector"
)

selected_date = pd.to_datetime(selected_date)
df_selected = df_all[df_all['日期 (Date)'].dt.date == selected_date.date()]
df_previous = df_all[df_all['日期 (Date)'].dt.date == (selected_date - timedelta(days=1)).date()]

st.header(f"{selected_date.strftime('%Y-%m-%d')} 常规仪表盘")

# --- 主界面内容 (与之前版本保持一致) ---
if df_selected.empty:
    st.warning(f"在 {selected_date.strftime('%Y-%m-%d')} 没有找到销售数据。")
else:
    # (KPIs, 本日明星, 标签页图表等代码和之前一样，这里为了简洁省略，但在您粘贴时请确保是完整的)
    total_sales_selected = df_selected['销售额 (Sales)'].sum()
    total_sales_previous = df_previous['销售额 (Sales)'].sum()
    growth_rate = ((total_sales_selected - total_sales_previous) / total_sales_previous) * 100 if total_sales_previous > 0 else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("总销售额", f"¥ {total_sales_selected:,.2f}", f"{growth_rate:.2f}% vs 昨日")
    col2.metric("订单数", f"{len(df_selected)} 单")
    col3.metric("平均客单价", f"¥ {df_selected['销售额 (Sales)'].mean():,.2f}")
    st.markdown("---")
    st.subheader("本日明星分析")
    col_rep, col_prod = st.columns(2)
    with col_rep:
        st.markdown("##### 🏆 **Top 销售代表**")
        top_reps = df_selected.groupby('销售代表 (Rep)')['销售额 (Sales)'].sum().nlargest(5)
        st.dataframe(top_reps)
    with col_prod:
        st.markdown("##### 🚀 **Top 畅销产品**")
        top_products = df_selected.groupby('产品名称 (Product)')['销售额 (Sales)'].sum().nlargest(5)
        st.dataframe(top_products)
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊 各维度图表分析", "📈 历史趋势", "🔮 专业销售预测"])
    with tab1:
        st.subheader("各维度销售额详情")
        chart_type = st.selectbox("选择分析维度", ['销售区域', '产品大类'])
        if chart_type == '销售区域':
            display_data = df_selected.groupby('销售区域 (Region)')['销售额 (Sales)'].sum()
        else:
            display_data = df_selected.groupby('产品大类 (Category)')['销售额 (Sales)'].sum()
        st.bar_chart(display_data)
    with tab2:
        st.subheader("历史销售总额趋势")
        daily_sales_history = df_all.groupby(df_all['日期 (Date)'].dt.date)['销售额 (Sales)'].sum()
        st.line_chart(daily_sales_history)
    with tab3:
        st.subheader("未来7日销售额预测 (线性回归模型)")
        history_df = df_all[df_all['日期 (Date)'] <= selected_date].copy()
        daily_history = history_df.groupby(history_df['日期 (Date)'].dt.date)['销售额 (Sales)'].sum().reset_index()
        daily_history.rename(columns={'日期 (Date)': 'Date', '销售额 (Sales)': 'Sales'}, inplace=True)
        if len(daily_history) < 10:
            st.warning("历史数据不足10天，无法进行可靠的趋势预测。")
        else:
            daily_history['time_index'] = (pd.to_datetime(daily_history['Date']) - pd.to_datetime(daily_history['Date']).min()).dt.days
            X_train = daily_history[['time_index']]
            y_train = daily_history['Sales']
            model = LinearRegression()
            model.fit(X_train, y_train)
            last_time_index = daily_history['time_index'].max()
            future_indices = pd.DataFrame({'time_index': range(last_time_index + 1, last_time_index + 8)})
            future_predictions = model.predict(future_indices)
            future_dates = pd.to_datetime(daily_history['Date'].max()) + pd.to_timedelta(range(1, 8), unit='D')
            prediction_df = pd.DataFrame({'日期': future_dates, '预测销售额': future_predictions})
            st.write("模型基于至今为止的所有历史数据，预测未来7天的销售趋势 (将鼠标悬停在图表上查看详细数据):")
            chart = alt.Chart(prediction_df).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X('日期:T', title='日期'),
                y=alt.Y('预测销售额:Q', title='预测销售额 (元)'),
                tooltip=[alt.Tooltip('日期:T', format='%Y-%m-%d'), alt.Tooltip('预测销售额:Q', format=',.2f')]
            ).interactive()
            st.altair_chart(chart, use_container_width=True)