import streamlit as st
import pandas as pd
from pathlib import Path
from urllib.parse import quote_plus
#import gspread
from streamlit_gsheets import GSheetsConnection
st.set_page_config(layout="wide")

st.title("Federal Gifts Wikidata Search")

DATA_FILENAME = 'data/givers_to_lookup.csv'

instructions = """Please look up the listed entity on Wikidata. Entities might be a person, family, country or organization.

Examples:  
> Jimmy Carter: type in Q23685  
> European Commission: type in Q8880  
> Serbia: type in Q403  

Only enter a valid Wikidata ID in the WikidataID field with the following exceptions:

> If an entry contains multiple givers that are part of a family (for example, President and Mrs Elena Ceausescu), type in FAMILY  
> If an entry contains multiple givers that are not part of a family (for example, James Bond and Q), type in GROUP  
> If the Wikidata match is unclear (for example, multiple branches of the Hungarian Ministry of Foreign Affairs, each with their own Wiki ID, type in UNCLEAR  
> If you cannot find a Wikidata ID for an entry (the individual has no WIkipedia page, for example), type in NIL
 """ 
    
#**Original giver information** shows the full entry which might include title and country. 

#**Abbreviated giver information** shows only the parsed value. 

#st.subheader("Instructions", help="Please look up the listed entity on [Wikidata](https://www.wikidata.org). Entities might be a person, family, country or organization.")

#move_to_side = st.toggle("Move to sidebar")
#activated = st.toggle("Show instructions", value=not move_to_side, disabled=move_to_side)
#activated = st.toggle("Hide instructions", value=False)
#if not activated:
#    st.write(instructions)

col1, col2 = st.columns([2.04, 1], vertical_alignment="center")

with col1:
    st.subheader(
        "Instructions",
        help="Please look up the listed entity on Wikidata. "
             "Entities might be a person, family, country or organization."
    )

with col2:
    hide_instructions = st.toggle("Hide", value=False, help="Hide instructions")

left, right = st.columns([3, 1])

if not hide_instructions:
    with left:
        st.info(instructions)

#if activated and not move_to_side:
#    st.write(instructions)
    
#if move_to_side:
#    with st.sidebar:
#        st.subheader("Instructions", help="Please look up the listed entity on [Wikidata](https://www.wikidata.org).") 
#        st.write(instructions)

#student = st.selectbox("Select your worksheet:", ["Carlos", "Gabe", "Laura", "Skylar", "Vicky"])

conn = st.connection("gsheets", type=GSheetsConnection)

def get_coding_data(student):
    df = conn.read(worksheet=student, ttl=0)
    df['WikidataID'] = df['WikidataID'].astype(str)
    df['WikidataID'] = df['WikidataID'].str.replace("nan", "")
    return df

def save_edits(df, column,student):
    for idx, val in st.session_state.edits.items():
        df.at[idx, column] = val
    #sh.sheet1.update([df.columns.values.tolist()] + df.values.tolist())
    conn.update(data=df,worksheet=student)
    st.session_state.edits = {}
    st.success("Saved successfully.")
    st.rerun()
    
def init_session_state():
    defaults = {
        "idx": 0,
        "edits": {},
        "wikidata_input": "",
        "last_loaded_idx": None,
        "skip_key_counter": 0
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def show_skip(remaining_indices):
    st.header("Move to specific row in dataframe")
    skip_input = st.text_input("Skip to entry", key=f"skip_entry_{st.session_state.skip_key_counter}")
    if st.button("Go") and skip_input:
        st.session_state.idx = max(0, min(int(skip_input) - 1, len(remaining_indices) - 1))
        st.session_state.skip_key_counter += 1
        st.rerun()
    st.write(f"Current index: {st.session_state.idx + 1} out of {len(remaining_indices)}")

def show_screen(current_row, remaining_indices,student):
    st.header(f"Welcome :blue[{student}]")
    st.header("Information to search")
    st.write("Original giver information: " + str(current_row["giver_orig"]))
    st.write("Abbreviated giver information: " + str(current_row["giver_name"]))
    #st.write(f"Current index: {st.session_state.idx + 1} out of {len(remaining_indices)}")
    search_term = quote_plus(str(current_row["giver_name"]))
    url = f"https://www.wikidata.org/w/index.php?search={search_term}&language=en&title=Special%3ASearch&ns0=1"
    st.write(f"[Search on Wikidata]({url})")
    st.text_input("WikidataID", key="wikidata_input", width=200)

def show_navigation(current_original_idx, remaining_indices, gifts_df):
    col1, col2, col3, col4,col5 = st.columns([1,1,1,1,.5])
    with col1:
        if st.button("Previous", help="Move to previous entry in file") and st.session_state.idx > 0:
            st.session_state.idx -= 1
            st.rerun()
    with col2:
        if st.button("Submit & Next", help="Submit Wikidata ID and move to next entry."):
            st.session_state.edits[current_original_idx] = st.session_state.wikidata_input
            if st.session_state.idx < len(remaining_indices) - 1:
                st.session_state.idx += 1
            st.rerun()
    with col3:
        if st.button("Next", help = "Move to next entry in file") and st.session_state.idx < len(remaining_indices) - 1:
            st.session_state.idx += 1
            st.rerun()
    with col4:
        if st.button("Save", help="Write changes to file"):
            save_edits(gifts_df,'WikidataID',student)
            #for idx, val in st.session_state.edits.items():
            #    gifts_df.at[idx, "WikidataID"] = val
            #gifts_df.to_csv("data/givers_to_lookup.csv", index=False)
            #st.success("Saved successfully.")

init_session_state()
with st.sidebar:
    #st.write("show sidebar")
    #show_skip(remaining_indices)
    student = st.selectbox("Select your worksheet:", ["Carlos", "Gabe", "Laura", "Skylar", "Vicky"],index=None,placeholder="Select your worksheet")

#gifts_df = get_coding_data(DATA_FILENAME)
gifts_df = get_coding_data(student)

remaining_df = gifts_df[
    gifts_df["WikidataID"].isna() |
    (gifts_df["WikidataID"].astype(str).str.strip() == "") |
    (gifts_df["WikidataID"].astype(str).str.lower() == "nan")
]
st.write(len(remaining_df))
#init_session_state()


if "idx" not in st.session_state:
    st.session_state.idx = 0

remaining_indices = remaining_df.index.tolist()
if not remaining_indices or st.session_state.idx > len(remaining_indices):
    st.session_state.idx = 0

current_original_idx = remaining_indices[st.session_state.idx]
current_row = gifts_df.loc[current_original_idx].astype(str)

# Only preload when index changes
if st.session_state.last_loaded_idx != current_original_idx:
    if current_original_idx in st.session_state.edits:
        st.session_state.wikidata_input = st.session_state.edits[current_original_idx]
    elif current_row.get("WikidataID", "").strip():
        st.session_state.wikidata_input = current_row["WikidataID"]
    else:
        st.session_state.wikidata_input = ""
    
    st.session_state.last_loaded_idx = current_original_idx


with st.sidebar:
    #st.write("show sidebar")
    show_skip(remaining_indices)

current_row = gifts_df.loc[current_original_idx]

show_screen(current_row, remaining_indices, student)
show_navigation(current_original_idx, remaining_indices, gifts_df)
