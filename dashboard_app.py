# dashboard_app.py

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# --- 数据库文件名 ---
DATABASE_FILE = 'sales_database.db'

# --- 页面配置 (设置为宽屏模式) ---
st.set_page_config(layout="wide", page_title="销售数据仪表盘")


# --- 数据加载函数 ---
# @st.cache_data 告诉 Streamlit 缓存数据，除非代码改变，否则不用重复加载，提高速度
@st.cache_data(ttl=600)  # ttl=600 表示缓存每10分钟过期一次
def load_data_from_db():
    """从SQLite数据库中加载销售数据"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        # 从数据库的 'sales' 表中读取所有数据
        df = pd.read_sql_query("SELECT * FROM sales", conn)
        conn.close()
        # 将“日期”列转换为标准的日期时间格式，这对后续按日期筛选和画图至关重要
        df['日期 (Date)'] = pd.to_datetime(df['日期 (Date)'])
        return df
    except Exception as e:
        # 如果数据库或表不存在，返回一个空的DataFrame
        st.error(f"加载数据库时出错: {e}")
        return pd.DataFrame()


# 加载数据
df_all = load_data_from_db()

# --- 仪表盘主界面 ---
st.title("📊 销售数据智能仪表盘")

# 检查是否有数据
if df_all.empty:
    st.warning("数据库中尚无数据。请先运行 `update_database.py` 来添加数据。")
    # 如果没有数据，停止运行后续代码
    st.stop()

# --- 侧边栏筛选器 ---
st.sidebar.header("筛选器")
# 日期选择器，让用户选择要查看的日期
selected_date = st.sidebar.date_input(
    "选择查看日期",
    value=df_all['日期 (Date)'].max(),  # 默认显示最新的一天
    min_value=df_all['日期 (Date)'].min(),
    max_value=df_all['日期 (Date)'].max(),
    key="date_selector"  # 给控件一个唯一的key
)

# --- 根据选择的日期筛选数据 ---
# 将选择的日期转换为datetime对象以便于比较
selected_date = pd.to_datetime(selected_date)
# 筛选出所选日期和前一天的数据
df_selected = df_all[df_all['日期 (Date)'].dt.date == selected_date.date()]
df_previous = df_all[df_all['日期 (Date)'].dt.date == (selected_date - timedelta(days=1)).date()]

# --- 主界面内容 ---
if df_selected.empty:
    st.warning(f"在 {selected_date.strftime('%Y-%m-%d')} 没有找到销售数据。")
else:
    # --- 关键指标 (KPIs) ---
    total_sales_selected = df_selected['销售额 (Sales)'].sum()
    total_sales_previous = df_previous['销售额 (Sales)'].sum()

    # 计算日环比，处理分母为0的情况
    growth_rate = ((
                               total_sales_selected - total_sales_previous) / total_sales_previous) * 100 if total_sales_previous > 0 else 0

    st.header(f"{selected_date.strftime('%Y-%m-%d')} 销售概览")
    col1, col2, col3 = st.columns(3)
    col1.metric("总销售额", f"¥ {total_sales_selected:,.2f}", f"{growth_rate:.2f}% vs 昨日")
    col2.metric("订单数", f"{len(df_selected)} 单")
    col3.metric("平均客单价", f"¥ {df_selected['销售额 (Sales)'].mean():,.2f}")

    st.markdown("---")  # 分割线

    # --- 使用标签页来组织图表和分析 ---
    tab1, tab2, tab3 = st.tabs(["📊 各区域销售图表", "📈 历史趋势", "🔮 简单预测"])

    with tab1:
        st.subheader(f"{selected_date.strftime('%Y-%m-%d')} 各区域销售额详情")
        regional_sales = df_selected.groupby('销售区域 (Region)')['销售额 (Sales)'].sum().sort_values(ascending=False)
        st.bar_chart(regional_sales)

    with tab2:
        st.subheader("历史销售总额趋势")
        # 按天汇总所有历史数据
        daily_sales_history = df_all.groupby(df_all['日期 (Date)'].dt.date)['销售额 (Sales)'].sum()
        st.line_chart(daily_sales_history)

    with tab3:
        st.subheader("明日销售额简单预测")
        if not df_previous.empty:
            avg_sales = (total_sales_selected + total_sales_previous) / 2
            st.write(f"基于近两日数据，简单预测明日总销售额约为: **¥ {avg_sales:,.2f}**")
        else:
            st.write("需要至少连续两天的数据才能进行简单预测。")