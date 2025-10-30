"""
Mini Streamlit app demonstrating a Material-style table using st_mui_table.

This file supports TWO ways to run:
1) Directly (double-click or Run ▶ in VS Code): it will auto-launch `streamlit run` on itself and open in your browser.
2) The usual way: `streamlit run streamlit_material_table_app.py`

Dependencies (one-time):
    pip install streamlit pandas st-mui-table
"""

from __future__ import annotations
import os
import sys
import subprocess
from typing import List

APP_ENV_FLAG = "STREAMLIT_RUNNING"


def _launched_by_streamlit() -> bool:
    """Detect if this file is being executed under Streamlit."""
    return os.environ.get(APP_ENV_FLAG) == "true"


def _launch_via_streamlit() -> None:
    """Re-invoke this script via `python -m streamlit run <thisfile>` and exit."""
    script_path = os.path.abspath(__file__)
    cmd = [sys.executable, "-m", "streamlit", "run", script_path]
    env = os.environ.copy()
    env[APP_ENV_FLAG] = "true"  # tell the child process not to re-spawn
    subprocess.Popen(cmd, env=env)
    sys.exit(0)


# ----------------------- Streamlit application code -------------------------

def run_streamlit_app() -> None:
    import pandas as pd
    import streamlit as st

    # Try to import the Material UI table component
    try:
        from st_mui_table import st_mui_table  # type: ignore
        HAS_MUI = True
    except Exception:
        HAS_MUI = False

    st.set_page_config(page_title="Material Table Demo", page_icon="📊", layout="wide")

    st.title("Material-Style Table in Streamlit")
    st.caption("Using `st_mui_table` with custom CSS for compact rows, zebra striping, and age pills.")

    # --- Sample data --------------------------------------------------------
    def load_sample_df(rows: int = 25) -> pd.DataFrame:
        base_names = [
            "Alice", "Bob", "Charlie", "Diana", "Ethan",
            "Fiona", "Gina", "Henry", "Iris", "Jack",
        ]
        df = pd.DataFrame({"Name": base_names * max(1, rows // 10)})
        df = df.head(rows)

        ages = ((pd.Series(range(20, 20 + len(df))) % 50) + 18).tolist()
        df["Age"] = ages
        df["City"] = (
            [
                "Denver", "Austin", "Phoenix", "Nashville", "Seattle",
                "Miami", "Chicago", "Boston", "Atlanta", "San Diego",
            ]
            * max(1, len(df) // 10)
        )[: len(df)]

        # Convert Age to a pill/badge via HTML (safe for demo; avoid untrusted content)
        def age_badge(age: int) -> str:
            return (
                f"<span style=\"display:inline-block;padding:2px 10px;"
                f"border-radius:999px;background:#E0E7FF;color:#1E3A8A;"
                f"font-weight:600;font-size:12px;line-height:18px;\">{age}</span>"
            )

        df["Age"] = [age_badge(a) for a in ages]

        # Details column with unique IDs
        messages = [
            "Good standing", "Review pending", "Priority", "Eligible", "N/A",
            "Check docs", "Escalated", "Complete", "Draft", "Follow-up",
        ]
        details: List[str] = []
        repeat = max(1, len(df) // len(messages)) + 1
        i = 0
        for _ in range(repeat):
            for msg in messages:
                details.append(f"<b>{msg}</b> (ID-{i:04d})")
                i += 1
                if len(details) >= len(df):
                    break
            if len(details) >= len(df):
                break
        df["Details"] = details[: len(df)]
        return df.reset_index(drop=True)

    with st.sidebar:
        st.header("Controls")
        rows = st.slider("Rows", min_value=10, max_value=200, value=30, step=10)
        show_index = st.checkbox("Show index", value=False)
        sticky_header = st.checkbox("Sticky header", value=True)
        size = st.selectbox("Row size", options=["small", "medium"], index=0)
        padding = st.selectbox("Cell padding", options=["none", "normal", "checkbox"], index=0)
        page_sizes = st.multiselect(
            "Pagination sizes", options=[5, 10, 25, 50, 100], default=[10, 25, 50]
        )
        zebra = st.checkbox("Zebra striping", value=True)
        compact = st.checkbox("Extra compact height", value=True)

    _df = load_sample_df(rows)

    # --- Custom CSS for st_mui_table ---------------------------------------
    css_rules: List[str] = []
    if compact:
        css_rules.append(
            ".MuiTableCell-root{padding-top:4px;padding-bottom:4px;padding-left:8px;padding-right:8px;}"
        )
    if zebra:
        css_rules.append(
            "tbody .MuiTableRow-root:nth-of-type(even){background-color:#FAFAFA;}"
        )
    css_rules.append(
        ".MuiTableHead-root .MuiTableCell-root{padding-top:6px;padding-bottom:6px;}"
    )
    custom_css = "\n".join(css_rules)

    # --- Render table -------------------------------------------------------
    if HAS_MUI:
        st.subheader("Material UI Table (st_mui_table)")
        st_mui_table(
            _df,
            enablePagination=True,
            customCss=custom_css,
            paginationSizes=page_sizes or [10, 25, 50],
            size=size,
            padding=padding,
            stickyHeader=sticky_header,
            showIndex=show_index,
            detailColumns=["Details"],
            detailColNum=1,
            detailsHeader="More Info",
        )
    else:
        st.subheader("Fallback: st.dataframe (component not installed)")
        st.info(
            "`st_mui_table` isn't installed. Install it with:\n\n"
            "    pip install st-mui-table\n\n"
            "Then rerun this app to use the Material UI table component."
        )
        st.dataframe(_df, use_container_width=True)

    # --- Notes --------------------------------------------------------------
    with st.expander("Notes on security & usage"):
        st.markdown(
            "- `st_mui_table` allows HTML in cells (used for the Age pill). Avoid passing untrusted input.\n"
            "- You can tweak paddings and zebra colors via the sidebar toggles or by editing the CSS rules.\n"
            "- For advanced editing/grouping, consider `streamlit-aggrid`."
        )


if __name__ == "__main__":
    if not _launched_by_streamlit():
        _launch_via_streamlit()
    run_streamlit_app()
