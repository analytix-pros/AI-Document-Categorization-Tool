"""Dashboard component with batch analytics and metrics."""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
from database.db_models import create_connection


def get_system_timezone():
    """Get system timezone offset in hours."""
    if time.daylight:
        return -time.altzone / 3600
    else:
        return -time.timezone / 3600


def get_batch_data_last_10_days():
    """
    Retrieve batch data for the last 10 days, converting UTC to system timezone.
    Returns DataFrame with date, status, and count.
    """
    conn = create_connection()
    query = """
        SELECT created_datetime, status 
        FROM batch 
        WHERE created_datetime IS NOT NULL
        ORDER BY created_datetime DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return pd.DataFrame(columns=['date', 'status', 'count'])
    
    tz_offset_hours = get_system_timezone()
    df['created_datetime'] = pd.to_datetime(df['created_datetime'], utc=True)
    df['created_datetime'] = df['created_datetime'] + pd.Timedelta(hours=tz_offset_hours)
    df['date'] = df['created_datetime'].dt.date
    
    today = datetime.now().date()
    ten_days_ago = today - timedelta(days=9)
    df = df[df['date'] >= ten_days_ago]
    
    grouped = df.groupby(['date', 'status']).size().reset_index(name='count')
    
    return grouped


def get_category_counts():
    """
    Get total categories selected with category names.
    Returns DataFrame with category name and count.
    """
    conn = create_connection()
    query = """
        SELECT c.name, COUNT(*) as count
        FROM document_category dc
        JOIN category c ON dc.category_uuid = c.category_uuid
        GROUP BY c.name
        ORDER BY count DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df


def get_total_files_processed():
    """Get total files processed from completed batches."""
    conn = create_connection()
    query = """
        SELECT SUM(number_of_files) as total
        FROM batch 
        WHERE status = 'completed'
    """
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result[0] is not None else 0


def get_avg_process_time_per_file():
    """Get average process time per file from completed batches."""
    conn = create_connection()
    query = """
        SELECT AVG(CAST(process_time AS FLOAT) / CAST(number_of_files AS FLOAT)) as avg_time
        FROM batch 
        WHERE status = 'completed' AND number_of_files > 0
    """
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result[0] is not None else 0.0


def get_avg_category_confidence():
    """Get average category confidence as a percentage."""
    conn = create_connection()
    query = """
        SELECT AVG(category_confidence) as avg_confidence
        FROM document_category
        WHERE category_confidence IS NOT NULL
    """
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    
    return (result[0] * 100) if result[0] is not None else 0.0


def create_batch_stacked_bar_chart(df):
    """
    Create stacked bar chart showing batch counts by status over the last 10 days.
    Status values 'started' and 'error' are considered bad statuses.
    """
    if df.empty:
        return None
    
    df['status_type'] = df['status'].apply(
        lambda x: 'Bad' if x in ['started', 'error'] else 'Good'
    )
    
    color_map = {'Bad': '#ef4444', 'Good': '#10b981'}
    
    fig = px.bar(
        df, 
        x='date', 
        y='count', 
        color='status_type',
        color_discrete_map=color_map,
        labels={'date': 'Date', 'count': 'Number of Batches', 'status_type': 'Status Type'},
        title='Batch Processing - Last 10 Days',
        hover_data={'status': True, 'status_type': False}
    )
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Number of Batches',
        legend_title='Status',
        hovermode='x unified',
        showlegend=True
    )
    
    return fig


def create_category_bar_chart(df):
    """Create bar chart showing total categories selected."""
    if df.empty:
        return None
    
    fig = px.bar(
        df,
        x='name',
        y='count',
        labels={'name': 'Category', 'count': 'Total Selected'},
        title='Categories Selected',
        color_discrete_sequence=['#3b82f6']
    )
    
    fig.update_layout(
        xaxis_title='Category',
        yaxis_title='Total Selected',
        xaxis_tickangle=-45,
        showlegend=False
    )
    
    return fig


def render_dashboard():
    """Render the main dashboard with all metrics and charts."""
    st.header("Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_files = get_total_files_processed()
        st.metric(
            label="Total Files Processed",
            value=f"{total_files:,}"
        )
    
    with col2:
        avg_time = get_avg_process_time_per_file()
        st.metric(
            label="Avg Process Time/File",
            value=f"{avg_time:.2f}s"
        )
    
    with col3:
        avg_confidence = get_avg_category_confidence()
        st.metric(
            label="Avg Category Confidence",
            value=f"{avg_confidence:.1f}%"
        )
    
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        batch_df = get_batch_data_last_10_days()
        batch_chart = create_batch_stacked_bar_chart(batch_df)
        
        if batch_chart:
            st.plotly_chart(batch_chart, use_container_width=True)
        else:
            st.info("No batch data available for the last 10 days")
    
    with col_chart2:
        category_df = get_category_counts()
        category_chart = create_category_bar_chart(category_df)
        
        if category_chart:
            st.plotly_chart(category_chart, use_container_width=True)
        else:
            st.info("No category data available")