import datetime as dt
import pandas as pd
import streamlit as st
from bom_engine import parse_bom, parse_so, explode, summarise, size_matrix, to_excel

st.set_page_config(page_title="SO Raw Material Requirement", page_icon="🧵", layout="wide")
st.title("🧵 Sales Order → Raw Material Requirement")
st.caption("Upload the SAP ByD Sales Order report and BOM report(s). FG BOMs are exploded through "
           "any SFG levels found in the uploaded BOMs down to raw materials.")

# ------------------------------------------------------------ inputs
c1, c2 = st.columns(2)
with c1:
    so_file = st.file_uploader("1️⃣ Sales Order report (CSV)", type="csv")
with c2:
    bom_files = st.file_uploader("2️⃣ BOM report(s) — FG and SFG (CSV, multiple allowed)",
                                 type="csv", accept_multiple_files=True)

with st.sidebar:
    st.header("Settings")
    basis = st.radio("Requirement basis", ["Requested Qty", "Open Qty"],
                     help="Open Qty = Requested − Fulfilled")
    include_zero = st.checkbox("Include zero-priced (FOC/extra) SO lines", value=True)
    extra = st.number_input("Extra allowance on top of BOM (%)", 0.0, 100.0, 0.0, 0.5,
                            help="BOM input qty already includes BOM wastage. Use this only for an additional buffer.")

if not so_file or not bom_files:
    st.info("Upload both reports to calculate the requirement.")
    st.stop()

# ------------------------------------------------------------ processing
try:
    so = parse_so(so_file)
    bom = parse_bom(bom_files)
except Exception as e:
    st.error(f"Could not read the files: {e}")
    st.stop()

sos = sorted(so["Sales Order"].unique())
sel = st.multiselect("Sales Orders", sos, default=sos)
so_sel = so[so["Sales Order"].isin(sel)].copy()
if not include_zero and "List Price Value" in so_sel.columns:
    so_sel = so_sel[so_sel["List Price Value"] > 0]

try:
    detail, missing = explode(so_sel, bom, qty_col=basis)
except ValueError as e:
    st.error(str(e))
    st.stop()

if missing:
    st.warning(f"No BOM found for {len(missing)} FG(s) — they are excluded. Upload their BOMs: "
               + ", ".join(f"{i} ({d})" for i, d in missing))
if detail.empty:
    st.error("Nothing to explode — check that the BOM report contains the FGs on the sales order.")
    st.stop()

summary = summarise(detail, extra)
matrix = size_matrix(detail)

# ------------------------------------------------------------ output
k1, k2, k3, k4 = st.columns(4)
k1.metric("SO lines", len(so_sel))
k2.metric(f"FG qty ({basis})", f"{so_sel[basis].sum():,.0f} {so_sel['UoM'].iloc[0] if len(so_sel) else ''}")
k3.metric("BOMs loaded (FG+SFG)", bom["Parent"].nunique())
k4.metric("Raw materials", len(summary))

t1, t2, t3, t4, t5 = st.tabs(["RM Requirement", "RM by FG", "BOM Explosion", "Sales Order Lines", "BOM Master"])
with t1:
    q = st.text_input("Filter RM", placeholder="e.g. FABRIC, THREAD, 10044314")
    view = summary
    if q:
        view = summary[summary.apply(lambda r: q.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
    st.dataframe(view, width="stretch", hide_index=True,
                 column_config={c: st.column_config.NumberColumn(format="%.4f")
                                for c in ["BOM Requirement", "Total Requirement"]})
with t2:
    st.dataframe(matrix, width="stretch", hide_index=True)
with t3:
    st.dataframe(detail, width="stretch", hide_index=True)
with t4:
    st.dataframe(so_sel, width="stretch", hide_index=True)
with t5:
    st.dataframe(bom.drop(columns=["InQty", "OutQty"]), width="stretch", hide_index=True)

meta = (f"SO: {', '.join(sel)} | Basis: {basis} | Extra allowance: {extra}% | "
        f"Generated {dt.datetime.now():%Y-%m-%d %H:%M}")
xlsx = to_excel(summary, detail, so_sel, bom, matrix, missing, meta)
st.download_button("⬇️ Download Excel", xlsx, file_name=f"RM_Requirement_{'_'.join(sel)}.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   type="primary")
