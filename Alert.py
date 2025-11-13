# Alert.py — Oracle Alert Log Analyzer Pro (Enhanced UI)
# Run: streamlit run Alert.py

import re
import os
import io
import time
import traceback
import pandas as pd
import streamlit as st
from datetime import datetime, timezone, timedelta, date, time as dtime
from dateutil import parser
import pandas.api.types as ptypes

# Optional: Mistral AI client
try:
    from mistralai import Mistral
except Exception:
    Mistral = None

# ---------------- Config ----------------
LOCAL_TZ = timezone(timedelta(hours=5, minutes=30))  # IST +05:30
MAX_PROMPT_CHARS = 9000

st.set_page_config(
    page_title="Oracle Alert Log Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "Oracle Alert Log Analyzer Pro - Advanced diagnostic tool for DBAs"
    }
)

# ---------------- Theme Switcher ----------------
theme_choice = st.sidebar.radio(
    "🎨 Theme Mode", ["Light Mode", "Dark Mode"], index=0, key="theme_toggle"
)

if theme_choice == "Dark Mode":
    DARK_CSS = """
    <style>
        /* ----------- Global Background & Text ----------- */
        html, body, .main {
            background-color: #0f1117 !important;
            color: #e6e6e6 !important;
        }

        /* ----------- Headings & Text ----------- */
        h1, h2, h3, h4, h5, h6, p, label, span, div {
            color: #e6e6e6 !important;
        }

        /* ----------- Cards / Expanders / Containers ----------- */
        .stExpander, .stDataFrame, .stMarkdown, .stTextInput, 
        .stTextArea, .stSelectbox, .stRadio, .stTabs, .stAlert, .stFileUploader {
            background: #1b1e27 !important;
            border-radius: 12px !important;
            border: 1px solid #2a2f3a !important;
            color: #e6e6e6 !important;
        }

        /* ----------- Upload Box ----------- */
        [data-testid="stFileUploaderDropzone"] {
            background: #232735 !important;
            border: 2px dashed #3e4452 !important;
            border-radius: 12px !important;
        }
        [data-testid="stFileUploaderDropzone"] p, 
        [data-testid="stFileUploaderDropzone"] span,
        [data-testid="stFileUploaderDropzone"] label {
            color: #d8d8d8 !important;
        }

        /* ----------- Buttons ----------- */
        .stButton > button {
            background: linear-gradient(135deg, #4f7cff 0%, #4adede 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 2rem !important;
            font-weight: 600 !important;
            box-shadow: 0 3px 8px rgba(0,0,0,0.3);
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.4);
        }

        /* ----------- Download Button ----------- */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            box-shadow: 0 3px 8px rgba(0,0,0,0.3);
        }

        /* ----------- Tabs ----------- */
        .stTabs [data-baseweb="tab"] {
            background: #2a2f3a !important;
            color: #cfd2dc !important;
            border-radius: 8px 8px 0 0 !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #4f7cff 0%, #4adede 100%) !important;
            color: #fff !important;
        }

        /* ----------- Metrics ----------- */
        [data-testid="stMetricValue"] {
            color: #4adede !important;
            font-weight: 700 !important;
        }

        /* ----------- Footer ----------- */
        footer, .stMarkdown a {
            color: #e6e6e6 !important;
        }
    </style>
    """
    st.markdown(DARK_CSS, unsafe_allow_html=True)




# ---------------- Custom CSS for Enhanced Design ----------------
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* Card-like containers */
    .stExpander {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border: none;
    }
    
    /* Header styling */
    h1 {
        color: white;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    
    h2, h3 {
        color: #667eea;
        font-weight: 600;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    
    /* Info/Warning boxes */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    
    /* File uploader */
    .stFileUploader {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 8px;
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: white;
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.5rem;
        background: white;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Plotly charts */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Header Section ----------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>🧠 Oracle Alert Log Analyzer</h1>
        <p style='color: white; font-size: 1.2rem; opacity: 0.9;'>Advanced Diagnostic Tool for DBAs</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------- Regex & Helpers ----------------
TIMESTAMP_RE = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+(?:[\+\-]\d{2}:\d{2}))")
ORA_RE = re.compile(r"\bORA-(\d{3,5}):?\s*(.*)")
WARN_RE = re.compile(r"\bWARNING\b|\bWarning\b|\bwarning\b")
TRACE_RE = re.compile(r"(\/[\w\/\.\-\+]*\.trc)")

def lines_from_uploaded_file(f):
    raw = f.read().decode("utf-8", errors="ignore")
    return raw.splitlines()

def analyze_alert_log_lines(lines, source_name="uploaded"):
    ora_errors = []
    warnings = []
    current_timestamp = None

    trace_locations = [(i, TRACE_RE.search(line).group(1)) for i, line in enumerate(lines) if TRACE_RE.search(line)]
    def find_nearby_trace(idx):
        for t_idx, t_path in trace_locations:
            if 0 <= t_idx - idx <= 5:
                return t_path
        return "Not Found"

    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        if not line.strip():
            continue

        ts_m = TIMESTAMP_RE.search(line)
        if ts_m:
            current_timestamp = ts_m.group(1)
            continue

        ora_m = ORA_RE.search(line)
        if ora_m:
            code = f"ORA-{ora_m.group(1)}"
            if code not in {"ORA-0", "ORA-03136", "ORA-3136"}:
                ora_errors.append({
                    "Timestamp": current_timestamp or "Not Found",
                    "ORA Error": code,
                    "Error Text": ora_m.group(2).strip(),
                    "Trace File": find_nearby_trace(i),
                    "Source": source_name,
                    "Raw Line": line,
                })
        elif WARN_RE.search(line):
            warnings.append({
                "Timestamp": current_timestamp or "Not Found",
                "Warning Message": line.strip(),
                "Trace File": find_nearby_trace(i),
                "Source": source_name,
                "Raw Line": line,
            })
    return ora_errors, warnings

def parse_iso_timestamp(ts):
    if not ts or ts == "Not Found":
        return None
    try:
        dt = parser.isoparse(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=LOCAL_TZ)
        return dt
    except Exception:
        try:
            dt = parser.parse(ts, fuzzy=True)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=LOCAL_TZ)
            return dt
        except Exception:
            return None

def detect_instance_summary_and_events(all_lines):
    info = {
        "Instance Names": set(),
        "Hostnames": set(),
        "Oracle Releases": set(),
        "Startup Events": [],
        "Shutdown Events": [],
        "Crash Events": []
    }
    release_re = re.compile(r"(Release\s+\d+(?:\.\d+)*)", re.I)
    start_re = re.compile(r"(Starting\s+ORACLE\s+instance|PMON has started|Starting up ORACLE)", re.I)
    shutdown_re = re.compile(r"(Shutting down|shutdown\s+complete|Shutdown\s+normal|shutdown complete)", re.I)
    crash_re = re.compile(r"(Instance terminated|terminated abnormally|abort|crash|ORA-00600|ORA-07445|core dump)", re.I)
    inst_re = re.compile(r"Instance\s+name[:\s]*([A-Za-z0-9_\-\.]+)", re.I)
    host_re = re.compile(r"Host\s*[:=]\s*([A-Za-z0-9\-\._]+)", re.I)
    ts_re = TIMESTAMP_RE

    for idx, line in enumerate(all_lines):
        r = release_re.search(line)
        if r:
            info["Oracle Releases"].add(r.group(1))
        m = inst_re.search(line)
        if m:
            info["Instance Names"].add(m.group(1))
        h = host_re.search(line)
        if h:
            info["Hostnames"].add(h.group(1))

        ts = ts_re.search(line)
        ts_val = ts.group(1) if ts else "Not Found"

        if start_re.search(line):
            info["Startup Events"].append({"Timestamp": ts_val, "Line": line.strip(), "Index": idx})
        elif shutdown_re.search(line):
            info["Shutdown Events"].append({"Timestamp": ts_val, "Line": line.strip(), "Index": idx})
        elif crash_re.search(line):
            info["Crash Events"].append({"Timestamp": ts_val, "Line": line.strip(), "Index": idx})

    for k in ["Instance Names", "Hostnames", "Oracle Releases"]:
        info[k] = sorted(info[k])
    return info

def compare_two_parsed_lists(list_a, list_b):
    df_a = pd.DataFrame(list_a) if list_a else pd.DataFrame(columns=["ORA Error","Error Text"])
    df_b = pd.DataFrame(list_b) if list_b else pd.DataFrame(columns=["ORA Error","Error Text"])
    a_counts = df_a["ORA Error"].value_counts().rename("A_Count") if not df_a.empty else pd.Series(dtype=int)
    b_counts = df_b["ORA Error"].value_counts().rename("B_Count") if not df_b.empty else pd.Series(dtype=int)
    counts = pd.concat([a_counts, b_counts], axis=1).fillna(0).astype(int).reset_index().rename(columns={"index":"ORA Error"})
    a_set = set((r["ORA Error"], r["Error Text"]) for r in list_a) if list_a else set()
    b_set = set((r["ORA Error"], r["Error Text"]) for r in list_b) if list_b else set()
    new_in_b = [{"ORA Error": x[0], "Error Text": x[1]} for x in (b_set - a_set)]
    new_in_a = [{"ORA Error": x[0], "Error Text": x[1]} for x in (a_set - b_set)]
    return {"counts": counts, "new_in_b": new_in_b, "new_in_a": new_in_a}


# ---------------- Mistral AI Section ----------------
def ai_generate(prompt: str) -> str:
    try:
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            return "⚠️ AI Error: MISTRAL_API_KEY not found in environment."
        if Mistral is None:
            return "⚠️ Mistral client not installed."

        client = Mistral(api_key=api_key)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an Oracle DBA expert. Analyze ONLY the provided alert log text. "
                    "Do NOT invent or assume additional ORA errors not present in the provided logs. "
                    "If no ORA or warnings exist in the supplied segment, explicitly state that. "
                    "Provide a concise summary suitable for production DBAs (3–5 sentences)."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        ai_summary = None
        for attempt in range(3):
            try:
                response = client.chat.complete(
                    model="mistral-large-latest",
                    messages=messages,
                    temperature=0.2,
                )
                ai_summary = response.choices[0].message.content.strip()
                break
            except Exception as e:
                msg = str(e)
                if any(x in msg.lower() for x in ["timeout", "connection", "reset", "429", "capacity", "10054"]):
                    if attempt < 2:
                        time.sleep(5 * (attempt + 1))
                        continue
                return f"⚠️ AI Error: {msg}"
        else:
            return "⚠️ Mistral API connection issue persisted."

        ora_codes = sorted(set(re.findall(r"\bORA-\d{3,5}\b", prompt)))
        if ora_codes:
            link_lines = ["\n\n### 🔗 Related Oracle Support Links"]
            for code in ora_codes:
                google_link = f"https://www.google.com/search?q={code}+site:support.oracle.com"
                link_lines.append(f"- **{code}** → [Oracle Support]({google_link})")
            ora_links_block = "\n".join(link_lines)
        else:
            ora_links_block = ""
        
        # --- UPDATED: Using Markdown and an emoji for a universal warning format ---
        ai_note = (
            "\n\n"
            "**⚠️ Note:** Since the recommendations are generated through AI-based analysis, they may not always be fully accurate. For validation and further details, please refer to the official Oracle Support documentation and knowledge base articles linked below."
        )
        # --- END: Updated Note ---

        return f"### 🧠 AI Summary\n{ai_summary}{ai_note}{ora_links_block}"

    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"

# ---------------- File Upload Section ----------------
st.markdown("""
<div style='background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 2rem;'>
    <h3 style='margin-top: 0; color: #667eea;'>📁 Upload Alert Log Files</h3>
    <p style='color: #666; margin-bottom: 1rem;'>Select one or more Oracle alert log files to analyze</p>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader("", type=["log","txt"], accept_multiple_files=True, label_visibility="collapsed")

if not uploaded_files:
    st.markdown("""
    <div style='background: white; padding: 3rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
        <h2 style='color: #667eea; margin-bottom: 1rem;'>👋 Welcome!</h2>
        <p style='font-size: 1.1rem; color: #666;'>Upload your Oracle alert log files above to begin analysis</p>
        <p style='color: #999; margin-top: 1rem;'>Supports .log and .txt files</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Parse uploaded files
all_raw_lines = []
per_file_lines = {}
combined_ora = []
combined_warnings = []

with st.spinner("🔄 Processing uploaded files..."):
    for f in uploaded_files:
        name = getattr(f, "name", "uploaded")
        lines = lines_from_uploaded_file(f)
        per_file_lines[name] = lines
        all_raw_lines.append(f"--- BEGIN FILE: {name} ---")
        all_raw_lines.extend(lines)
        all_raw_lines.append(f"--- END FILE: {name} ---")
        o, w = analyze_alert_log_lines(lines, source_name=name)
        combined_ora.extend(o)
        combined_warnings.extend(w)

df_ora_all = pd.DataFrame(combined_ora) if combined_ora else pd.DataFrame(columns=["Timestamp","ORA Error","Error Text","Trace File","Source","Raw Line"])
df_warn_all = pd.DataFrame(combined_warnings) if combined_warnings else pd.DataFrame(columns=["Timestamp","Warning Message","Trace File","Source","Raw Line"])

if not df_ora_all.empty:
    df_ora_all["ParsedTimestamp"] = df_ora_all["Timestamp"].apply(parse_iso_timestamp)
else:
    df_ora_all["ParsedTimestamp"] = pd.Series(dtype="datetime64[ns]")

if not df_warn_all.empty:
    df_warn_all["ParsedTimestamp"] = df_warn_all["Timestamp"].apply(parse_iso_timestamp)
else:
    df_warn_all["ParsedTimestamp"] = pd.Series(dtype="datetime64[ns]")

# ---------------- Quick Stats Dashboard ----------------
st.markdown("### 📊 Quick Statistics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📄 Files Uploaded", len(uploaded_files))
with col2:
    st.metric("🔴 ORA Errors", len(combined_ora))
with col3:
    st.metric("🟡 Warnings", len(combined_warnings))
with col4:
    unique_ora = len(df_ora_all["ORA Error"].unique()) if not df_ora_all.empty else 0
    st.metric("🔢 Unique ORA Codes", unique_ora)

st.markdown("---")

# ---------------- Instance Summary & Events ----------------
with st.expander("🗂️ Instance Summary & Events", expanded=True):
    info = detect_instance_summary_and_events(all_raw_lines)
    
    st.markdown("#### 🖥️ Instance Information")
    cols = st.columns(3)
    with cols[0]:
        st.info(f"**Instance Names**\n\n{', '.join(info['Instance Names']) or 'N/A'}")
    with cols[1]:
        st.info(f"**Hostnames**\n\n{', '.join(info['Hostnames']) or 'N/A'}")
    with cols[2]:
        st.info(f"**Oracle Releases**\n\n{', '.join(info['Oracle Releases']) or 'N/A'}")

    st.markdown("#### 🚀 Startup Events")
    if info["Startup Events"]:
        df = pd.DataFrame(info["Startup Events"])
        df["Parsed"] = df["Timestamp"].apply(parse_iso_timestamp)
        st.dataframe(df[["Timestamp","Parsed","Line"]], use_container_width=True)
    else:
        st.success("✅ No startup events detected")

    st.markdown("#### 🔻 Shutdown Events")
    if info["Shutdown Events"]:
        df = pd.DataFrame(info["Shutdown Events"])
        df["Parsed"] = df["Timestamp"].apply(parse_iso_timestamp)
        st.dataframe(df[["Timestamp","Parsed","Line"]], use_container_width=True)
    else:
        st.success("✅ No shutdown events detected")

    st.markdown("#### 💥 Crash / Termination Events")
    if info["Crash Events"]:
        df = pd.DataFrame(info["Crash Events"])
        df["Parsed"] = df["Timestamp"].apply(parse_iso_timestamp)
        st.dataframe(df[["Timestamp","Parsed","Line"]], use_container_width=True)
    else:
        st.success("✅ No crash or abnormal termination events detected 🎉")

# ---------------- Global Filters ----------------
with st.expander("🔍 Filters & Search", expanded=False):
    tab1, tab2 = st.tabs(["📅 Date/Time Filter", "🔎 Keyword Search"])
    
    with tab1:
        today = date.today()
        if not df_ora_all.empty and df_ora_all["ParsedTimestamp"].notna().any():
            min_ts = df_ora_all["ParsedTimestamp"].min()
            max_ts = df_ora_all["ParsedTimestamp"].max()
            default_start = min_ts.astimezone(LOCAL_TZ).date()
            default_end = max_ts.astimezone(LOCAL_TZ).date()
        else:
            default_start = default_end = today

        col1, col2 = st.columns(2)
        with col1:
            global_start_date = st.date_input("Start date", default_start, key="global_start_date")
            global_start_time = st.time_input("Start time", dtime(0,0), key="global_start_time")
        with col2:
            global_end_date = st.date_input("End date", default_end, key="global_end_date")
            global_end_time = st.time_input("End time", dtime(23,59), key="global_end_time")

        global_start_dt = datetime.combine(global_start_date, global_start_time).replace(tzinfo=LOCAL_TZ)
        global_end_dt = datetime.combine(global_end_date, global_end_time).replace(tzinfo=LOCAL_TZ)
        st.info(f"📅 Filtering range: {global_start_dt} — {global_end_dt}")
    
    with tab2:
        search_q = st.text_input("🔍 Search ORA code, error text, trace path, source, or any keyword", "").strip()
        if search_q:
            st.info(f"🔍 Active search filter: **{search_q}**")

# Apply filters
def apply_global_date_filter(df, start_dt, end_dt):
    if df.empty or "ParsedTimestamp" not in df.columns:
        return df
    df = df[df["ParsedTimestamp"].notna()].copy()
    df = df[(df["ParsedTimestamp"] >= start_dt) & (df["ParsedTimestamp"] <= end_dt)]
    return df

if search_q:
    q = search_q.lower()
    df_ora_display = df_ora_all[df_ora_all.apply(lambda r:
        q in str(r.get("ORA Error","")).lower()
        or q in str(r.get("Error Text","")).lower()
        or q in str(r.get("Trace File","")).lower()
        or q in str(r.get("Source","")).lower()
    , axis=1)].copy()
    df_warn_display = df_warn_all[df_warn_all.apply(lambda r:
        q in str(r.get("Warning Message","")).lower()
        or q in str(r.get("Trace File","")).lower()
        or q in str(r.get("Source","")).lower()
    , axis=1)].copy()
else:
    df_ora_display = df_ora_all.copy()
    df_warn_display = df_warn_all.copy()

df_ora_display = apply_global_date_filter(df_ora_display, global_start_dt, global_end_dt)
df_warn_display = apply_global_date_filter(df_warn_display, global_start_dt, global_end_dt)

# ---------------- ORA Errors & Warnings Tabs ----------------
tab_ora, tab_warn = st.tabs(["🔴 ORA Errors", "🟡 Warnings"])

with tab_ora:
    with st.expander("📋 ORA Error Details", expanded=True):
        if not df_ora_display.empty:
            st.dataframe(df_ora_display.drop(columns=["ParsedTimestamp"], errors="ignore"), use_container_width=True)
            
            st.markdown("#### 📊 Error Distribution")
            counts = df_ora_display["ORA Error"].value_counts().reset_index()
            counts.columns = ["ORA Error", "Count"]
            st.dataframe(counts, use_container_width=True)
        else:
            st.info("✅ No ORA errors found in selected range/search")

with tab_warn:
    with st.expander("📋 Warning Details", expanded=True):
        if not df_warn_display.empty:
            st.dataframe(df_warn_display.drop(columns=["ParsedTimestamp"], errors="ignore"), use_container_width=True)
            
            st.markdown("#### 📊 Top Warnings")
            top_w = df_warn_display["Warning Message"].value_counts().head(20).reset_index()
            top_w.columns = ["Warning Message", "Count"]
            st.dataframe(top_w, use_container_width=True)
        else:
            st.info("✅ No warnings found in selected range/search")

# ---------------- Error Frequency Chart ----------------
with st.expander("📈 ORA Error Frequency Chart", expanded=False):
    if df_ora_all.empty or df_ora_all["ParsedTimestamp"].isna().all():
        st.info("No timestamped ORA data available to plot")
    else:
        log_col = None
        if "AlertLogName" in df_ora_all.columns:
            log_col = "AlertLogName"
        elif "Filename" in df_ora_all.columns:
            log_col = "Filename"
        elif "Source" in df_ora_all.columns:
            log_col = "Source"

        if log_col is None:
            df_ora_all["__AlertLogGroup__"] = "All Logs Combined"
            log_col = "__AlertLogGroup__"

        log_list = sorted(df_ora_all[log_col].dropna().unique())

        if len(log_list) > 1:
            selected_log = st.selectbox("📂 Select Alert Log", log_list, key="selected_alert_log")
            df_selected = df_ora_all[df_ora_all[log_col] == selected_log].copy()
        else:
            selected_log = log_list[0]
            st.info(f"📂 Showing: **{selected_log}**")
            df_selected = df_ora_all.copy()

        if df_selected.empty:
            st.warning("No ORA errors found in the selected alert log")
        else:
            overall_min = df_selected["ParsedTimestamp"].min()
            overall_max = df_selected["ParsedTimestamp"].max()

            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                chart_start_date = st.date_input("Chart start date", overall_min.astimezone(LOCAL_TZ).date(), key="chart_start_date")
                chart_start_time = st.time_input("Chart start time", overall_min.astimezone(LOCAL_TZ).time(), key="chart_start_time")
            with col2:
                chart_end_date = st.date_input("Chart end date", overall_max.astimezone(LOCAL_TZ).date(), key="chart_end_date")
                chart_end_time = st.time_input("Chart end time", overall_max.astimezone(LOCAL_TZ).time(), key="chart_end_time")
            with col3:
                view_mode = st.radio("Granularity", ["Hourly", "Daily"], key="chart_view")

            chart_start_dt = datetime.combine(chart_start_date, chart_start_time).replace(tzinfo=LOCAL_TZ)
            chart_end_dt = datetime.combine(chart_end_date, chart_end_time).replace(tzinfo=LOCAL_TZ)

            df_chart_base = df_selected[df_selected["ParsedTimestamp"].notna()].copy()
            df_chart_base = df_chart_base[
                (df_chart_base["ParsedTimestamp"] >= chart_start_dt)
                & (df_chart_base["ParsedTimestamp"] <= chart_end_dt)
            ]

            if df_chart_base.empty:
                st.warning("No ORA errors in the selected chart time window")
            else:
                if view_mode == "Hourly":
                    df_chart_base["TimeBucket"] = df_chart_base["ParsedTimestamp"].dt.floor("H")
                    df_chart_base["MinuteStr"] = df_chart_base["ParsedTimestamp"].dt.strftime("%Y-%m-%d %H:%M")
                else:
                    df_chart_base["TimeBucket"] = df_chart_base["ParsedTimestamp"].dt.floor("D")
                    df_chart_base["MinuteStr"] = df_chart_base["ParsedTimestamp"].dt.strftime("%Y-%m-%d")

                freq = df_chart_base.groupby(["TimeBucket", "ORA Error"]).size().reset_index(name="Count")

                if view_mode == "Hourly":
                    sample_minutes = df_chart_base.groupby(["TimeBucket", "ORA Error"])["MinuteStr"].agg(
                        lambda s: ", ".join(sorted(set(s))[:6])
                    ).reset_index(name="SampleMinutes")
                    freq = freq.merge(sample_minutes, on=["TimeBucket", "ORA Error"], how="left")
                else:
                    freq["SampleMinutes"] = freq["TimeBucket"].dt.strftime("%Y-%m-%d")

                import plotly.graph_objects as go
                x_vals = sorted(freq["TimeBucket"].unique())
                ora_codes = sorted(freq["ORA Error"].unique())

                fig = go.Figure()
                colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7']
                
                for idx, ora in enumerate(ora_codes):
                    sub = freq[freq["ORA Error"] == ora].set_index("TimeBucket").reindex(x_vals, fill_value=0).reset_index()
                    sample_map = dict(zip(sub["TimeBucket"], sub["SampleMinutes"]))
                    hover_text = [
                        f"Time: {x}<br>ORA: {ora}<br>Count: {int(cnt)}"
                        + (f"<br>Sample: {sample_map.get(x, '')}" if sample_map.get(x) else "")
                        for x, cnt in zip(sub["TimeBucket"], sub["Count"])
                    ]
                    fig.add_trace(go.Bar(
                        x=sub["TimeBucket"],
                        y=sub["Count"],
                        name=ora,
                        text=sub["Count"],
                        hovertext=hover_text,
                        hoverinfo="text",
                        marker_color=colors[idx % len(colors)]
                    ))

                x_label = "Hour" if view_mode == "Hourly" else "Date"
                fig.update_layout(
                    barmode="stack",
                    title=f"ORA Error Frequency ({view_mode}) — {selected_log}",
                    xaxis=dict(
                        title=x_label,
                        tickangle=-45,
                        type="category",
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.05)',
                    ),
                    yaxis=dict(title="Occurrences", showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
                    legend_title_text="ORA Error",
                    height=560,
                    margin=dict(l=20, r=20, t=60, b=120),
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font=dict(family="Arial, sans-serif", size=12, color="#333"),
                )

                st.plotly_chart(fig, use_container_width=True)

# ---------------- Compare Two Logs ----------------
with st.expander("🔄 Compare Two Uploaded Logs", expanded=False):
    file_names = list(per_file_lines.keys())
    if len(file_names) < 2:
        st.info("📤 Upload at least two files to compare")
    else:
        col1, col2 = st.columns(2)
        with col1:
            file_a = st.selectbox("📄 File A (baseline)", file_names, index=0)
        with col2:
            file_b = st.selectbox("📄 File B (compare)", file_names, index=1 if len(file_names) > 1 else 0)

        if st.button("🔍 Run Compare", use_container_width=True):
            with st.spinner("Comparing logs..."):
                ora_a, warn_a = analyze_alert_log_lines(per_file_lines[file_a], source_name=file_a)
                ora_b, warn_b = analyze_alert_log_lines(per_file_lines[file_b], source_name=file_b)
                comp = compare_two_parsed_lists(ora_a, ora_b)
            
            st.markdown("#### 📊 Counts by ORA Error (A vs B)")
            st.dataframe(comp["counts"], use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### ➕ New in B (not in A)")
                if comp["new_in_b"]:
                    st.dataframe(pd.DataFrame(comp["new_in_b"]), use_container_width=True)
                else:
                    st.success("✅ No new ORA entries in B")
            
            with col2:
                st.markdown("#### ➖ Only in A (missing in B)")
                if comp["new_in_a"]:
                    st.dataframe(pd.DataFrame(comp["new_in_a"]), use_container_width=True)
                else:
                    st.success("✅ No unique entries in A")

# ---------------- Mistral AI Analysis ----------------
with st.expander("🤖 Mistral AI Analysis (Oracle Performance Expert)", expanded=False):
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 8px; color: white; margin-bottom: 1rem;'>
        <h4 style='margin: 0 0 0.5rem 0;'>🧠 AI-Powered Analysis</h4>
        <p style='margin: 0; opacity: 0.9;'>Get expert insights from Mistral AI about your Oracle alert logs</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_prompt = st.text_area("💬 Your instruction:", 
                               "Analyze logs between 18:00 and 19:00 on 2025-10-14 for performance issues",
                               height=120)
    use_filtered_segment = st.checkbox("🎯 Use currently filtered segment for AI analysis", value=True)

    logs = {name: "\n".join(lines) for name, lines in per_file_lines.items()} if per_file_lines else {}

    if not logs:
        st.warning("⚠️ Please upload at least one alert log to use Mistral AI analysis")
    else:
        if len(logs) > 1:
            selected_log = st.selectbox("📂 Select Alert Log to Analyze:", list(logs.keys()))
        else:
            selected_log = list(logs.keys())[0]
            st.info(f"📂 Selected: **{selected_log}**")

        if "mistral_cache" not in st.session_state:
            st.session_state.mistral_cache = {}

        if st.button("🚀 Run Mistral AI Analysis", use_container_width=True):
            if not user_prompt.strip():
                st.warning("⚠️ Please enter your instruction before running analysis")
            else:
                snippet_lines = []
                if use_filtered_segment and (not df_ora_display.empty or not df_warn_display.empty):
                    file_lines = per_file_lines.get(selected_log, [])
                    def add_context_from_df(df):
                        for _, row in df[df["Source"] == selected_log].iterrows():
                            raw_line = row.get("Raw Line", "")
                            if not raw_line:
                                continue
                            try:
                                idx = next((i for i, l in enumerate(file_lines) if raw_line in l), None)
                            except Exception:
                                idx = None
                            if isinstance(idx, int):
                                start_i = max(0, idx - 3)
                                end_i = min(len(file_lines), idx + 4)
                                snippet_lines.extend(file_lines[start_i:end_i])
                            else:
                                snippet_lines.append(raw_line)

                    add_context_from_df(df_ora_display if not df_ora_display.empty else pd.DataFrame())
                    add_context_from_df(df_warn_display if not df_warn_display.empty else pd.DataFrame())

                    if not snippet_lines:
                        snippet_lines = file_lines
                else:
                    snippet_lines = per_file_lines.get(selected_log, [])

                snippet = "\n".join(snippet_lines)[:MAX_PROMPT_CHARS]
                if not snippet.strip():
                    st.warning("⚠️ No log content available to send to AI")
                else:
                    error_summary = "\n".join([f"{r['Timestamp']} - {r['ORA Error']}: {r['Error Text']}" 
                                               for _, r in df_ora_display[df_ora_display["Source"] == selected_log].iterrows()]) \
                                    if not df_ora_display.empty else "No ORA errors in selected segment"
                    full_prompt = f"""
You are an Oracle Performance Expert analyzing the following alert log segment.
User instruction:
{user_prompt}

Detected ORA Errors:
{error_summary}

Alert Log Extract:
{snippet}
"""

                    cache_key = f"{selected_log}||{user_prompt.strip()}||{use_filtered_segment}||{global_start_dt.isoformat()}||{global_end_dt.isoformat()}"
                    if cache_key in st.session_state.mistral_cache:
                        ai_result = st.session_state.mistral_cache[cache_key]
                    else:
                        with st.spinner("🤖 Analyzing with Mistral AI..."):
                            ai_result = ai_generate(full_prompt)
                        st.session_state.mistral_cache[cache_key] = ai_result

                    st.markdown("""
                    <div style='background: white; padding: 2rem; border-radius: 8px; 
                                border-left: 4px solid #667eea; margin-top: 1rem;'>
                    """, unsafe_allow_html=True)
                    st.markdown(ai_result)
                    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Download Section ----------------
with st.expander("💾 Download Parsed Results", expanded=False):
    if (not combined_ora) and (not combined_warnings):
        st.info("📭 No parsed data to download")
    else:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 1.5rem; border-radius: 8px; color: white; margin-bottom: 1rem;'>
            <h4 style='margin: 0 0 0.5rem 0;'>📥 Export Your Analysis</h4>
            <p style='margin: 0; opacity: 0.9;'>Download complete parsed results in Excel format</p>
        </div>
        """, unsafe_allow_html=True)
        
        df_all = pd.concat([df_ora_all, df_warn_all], axis=0, ignore_index=True)
        
        for col in df_all.columns:
            try:
                if ptypes.is_datetime64_any_dtype(df_all[col]):
                    try:
                        if hasattr(df_all[col].dt, "tz") and df_all[col].dt.tz is not None:
                            df_all[col] = df_all[col].dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
                        else:
                            df_all[col] = df_all[col]
                    except Exception:
                        df_all[col] = pd.to_datetime(df_all[col].astype(str), errors="coerce")
            except Exception:
                pass

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            try:
                df_all.to_excel(writer, index=False, sheet_name="Parsed Log Data")
            except Exception:
                if not df_ora_all.empty:
                    pd.DataFrame(df_ora_all).to_excel(writer, index=False, sheet_name="ORA_Errors")
                if not df_warn_all.empty:
                    pd.DataFrame(df_warn_all).to_excel(writer, index=False, sheet_name="Warnings")

        filename = f"parsed_alert_log_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        st.download_button(
            "📥 Download Excel Report", 
            data=buf.getvalue(), 
            file_name=filename, 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ---------------- Footer ----------------
st.markdown("---")

footer_color = "#000000" if theme_choice == "Light Mode" else "#f0f0f0"
footer_bg = "#f9f9f9" if theme_choice == "Light Mode" else "#1e1e1e"

st.markdown(f"""
<div style='text-align: center; padding: 2rem; color: {footer_color}; 
            background: {footer_bg}; border-radius: 8px; opacity: 0.9;'>
    <p style='margin: 0;'>🧠 Oracle Alert Log Analyzer Pro | Built for DBAs | Powered by Streamlit & Mistral AI</p>
    <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem;'>© 2025 | Advanced Diagnostic Tool</p>
</div>
""", unsafe_allow_html=True)

