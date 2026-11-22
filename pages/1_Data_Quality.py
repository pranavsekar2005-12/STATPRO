
import streamlit as st
import pandas as pd
import plotly.express as px

from modules.shared import load_custom_css, get_dataset
from modules.data_quality import analyze_data_quality


# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="STATPRO | Data Quality",
    page_icon="🔍",
    layout="wide",
)

load_custom_css()
df = get_dataset()


# =====================================
# PAGE HEADER
# =====================================

st.title("Data Quality Analysis")

st.caption(
    "Evaluate dataset completeness, consistency and potential outliers."
)

st.divider()


if df is None:
    st.info("Upload a dataset using the sidebar to begin.")
    st.stop()


# =====================================
# RUN ANALYSIS
# =====================================

if st.button("Run Data Quality Analysis", type="primary"):

    try:
        result = analyze_data_quality(df)
        st.session_state["quality_result"] = result

    except Exception as error:
        st.error(str(error))


result = st.session_state.get("quality_result")


if result is not None:

    st.subheader("Quality Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Records", f"{result['total_rows']:,}")
    col2.metric("Variables", result["total_columns"])
    col3.metric("Missing Cells", int(df.isnull().sum().sum()))
    col4.metric("Duplicate Rows", result["duplicate_count"])

    st.divider()

    # =================================
    # MISSING VALUE ANALYSIS
    # =================================

    st.subheader("Missing Value Analysis")

    missing_data = df.isnull().sum()

    missing_data = missing_data[missing_data > 0]

    if missing_data.empty:
        st.success("No missing values detected.")
    else:
        missing_df = missing_data.reset_index()
        missing_df.columns = ["Variable", "Missing Count"]

        fig = px.bar(
            missing_df,
            x="Variable",
            y="Missing Count",
            title="Missing Values by Variable",
            template="plotly_white",
            color_discrete_sequence=["#2563EB"],
        )

        st.plotly_chart(fig, use_container_width=True)

    # =================================
    # DUPLICATE ANALYSIS
    # =================================

    st.subheader("Duplicate Record Analysis")

    if result["duplicate_count"] == 0:
        st.success("No duplicate records detected.")
    else:
        st.warning(
            f"{result['duplicate_count']} duplicate rows detected."
        )

    # =================================
    # NUMERIC SUMMARY
    # =================================

    st.subheader("Numeric Variable Summary")

    st.dataframe(
        result["numeric_summary"],
        use_container_width=True,
    )

    # =================================
    # OUTLIER ANALYSIS
    # =================================

    st.subheader("Potential Outlier Analysis")

    outlier_df = pd.DataFrame(
        list(result["outlier_counts"].items()),
        columns=["Variable", "Outlier Count"],
    )

    if outlier_df.empty:
        st.info("No numeric variables available for outlier analysis.")
    else:
        fig = px.bar(
            outlier_df,
            x="Variable",
            y="Outlier Count",
            title="Potential Outliers by Variable",
            template="plotly_white",
            color_discrete_sequence=["#F59E0B"],
        )

        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(outlier_df, use_container_width=True)

    # =================================
    # FINAL SUMMARY
    # =================================

    st.divider()

    st.subheader("Data Quality Summary")

    st.write(
        f"- Total records: {result['total_rows']:,}"
    )

    st.write(
        f"- Total variables: {result['total_columns']}"
    )

    st.write(
        f"- Missing cells: {int(df.isnull().sum().sum())}"
    )

    st.write(
        f"- Duplicate rows: {result['duplicate_count']}"
    )

    st.info(
        "Potential outliers are flagged for investigation. "
        "They are not automatically treated as errors."
    )

else:
    st.info("Click 'Run Data Quality Analysis' to generate your results.")


# =====================================
# FOOTER
# =====================================

st.divider()
st.caption("STATPRO | Data Quality Analysis")
