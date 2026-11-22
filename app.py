
import streamlit as st
import plotly.express as px

from modules.shared import load_custom_css, get_dataset


# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="STATPRO | Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_custom_css()

# =====================================
# LOAD DATASET
# =====================================

df = get_dataset()


# =====================================
# DASHBOARD HEADER
# =====================================

st.markdown(
    """
    <div style="padding:10px 0 20px 0;">
        <p style="color:#2563EB;font-weight:600;">
            STATISTICAL ANALYSIS PLATFORM
        </p>
        <h1 style="font-size:36px;color:#172554;">
            Dashboard Overview
        </h1>
        <p style="color:#64748B;">
            Monitor your dataset and access statistical analysis tools.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# =====================================
# EMPTY DATASET STATE
# =====================================

if df is None:

    st.markdown("## Welcome to STATPRO")

    st.info(
        "Upload a CSV or Excel dataset using the sidebar "
        "to begin your statistical analysis."
    )

    st.subheader("Your Analysis Workspace")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🔍 Data Quality")
        st.write("Inspect missing values, duplicates and potential outliers.")

    with col2:
        st.markdown("### 📈 Descriptive Statistics")
        st.write("Explore distributions and statistical summaries.")

    with col3:
        st.markdown("### 🧪 Hypothesis Testing")
        st.write("Perform t-tests, ANOVA and Chi-square tests.")

    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown("### 🔗 Correlation")
        st.write("Measure relationships between variables.")

    with col5:
        st.markdown("### 📊 Regression")
        st.write("Build and evaluate regression models.")

    with col6:
        st.markdown("### 📄 Reports")
        st.write("Access and export analysis results.")

    st.stop()


# =====================================
# DATASET METRICS
# =====================================

st.subheader("Dataset Performance")

total_rows = len(df)
total_columns = len(df.columns)
missing_values = int(df.isnull().sum().sum())
duplicate_rows = int(df.duplicated().sum())

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Records",
    f"{total_rows:,}",
)

col2.metric(
    "Total Variables",
    total_columns,
)

col3.metric(
    "Missing Values",
    f"{missing_values:,}",
)

col4.metric(
    "Duplicate Rows",
    f"{duplicate_rows:,}",
)

st.divider()


# =====================================
# DATASET INFORMATION
# =====================================

left, right = st.columns([1.5, 1])

with left:

    st.subheader("Dataset Preview")

    st.dataframe(
        df.head(10),
        use_container_width=True,
        hide_index=True,
    )

with right:

    st.subheader("Variable Information")

    variable_info = df.dtypes.astype(str).value_counts()

    st.bar_chart(
        variable_info,
        x_label="Data Type",
        y_label="Number of Variables",
    )


# =====================================
# INTERACTIVE VISUALIZATION
# =====================================

st.divider()

st.subheader("Explore Your Data")

numeric_columns = df.select_dtypes(
    include="number"
).columns.tolist()

if numeric_columns:

    selected_column = st.selectbox(
        "Choose a numeric variable",
        numeric_columns,
    )

    chart = px.histogram(
        df,
        x=selected_column,
        title=f"Distribution of {selected_column}",
        template="plotly_white",
        color_discrete_sequence=["#2563EB"],
    )

    chart.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="#172554",
    )

    st.plotly_chart(
        chart,
        use_container_width=True,
    )

else:

    st.info("No numeric variables available for visualization.")


# =====================================
# FOOTER
# =====================================

st.divider()

st.markdown(
    """
    <div style="text-align:center;padding:15px;">
        <p style="color:#64748B;font-size:13px;">
            STATPRO | Statistical Analysis & Reporting System
        </p>
        <p style="color:#94A3B8;font-size:12px;">
            Built with Python, Streamlit and Statistical Libraries
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
