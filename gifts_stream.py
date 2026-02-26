import streamlit as st
import pandas as pd
from pathlib import Path
from urllib.parse import quote_plus

st.title("Federal Gifts Wikidata Search")

DATA_FILENAME = 'data/givers_to_lookup.csv'

st.subheader("Instructions")
st.write("""If you cannot find a Wikidata ID for an entry, enter NIL. If an entry contains multiple givers (so and so and spouse), enter FAMILY. """)


def get_coding_data(DATA_FILENAME):
    """Grab data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    df = pd.read_csv(DATA_FILENAME)
    return df

def save_edits(df, column, filepath):
    for idx, val in st.session_state.edits.items():
        df.at[idx, column] = val
    df.to_csv(filepath, index=False)
    st.success("Saved successfully.")


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

def show_screen(current_row, remaining_indices):
    st.header("Information to search")
    st.write("Original giver information: " + str(current_row["giver_orig"]))
    st.write("Abbreviated giver information: " + str(current_row["giver_name"]))
    st.write(f"Current index: {st.session_state.idx + 1} out of {len(remaining_indices)}")
    st.text_input("WikidataID", key="wikidata_input")
    search_term = quote_plus(str(current_row["giver_name"]))
    url = f"https://www.wikidata.org/w/index.php?search={search_term}&language=en&title=Special%3ASearch&ns0=1"
    st.write(f"[Search on Wikidata]({url})")

def show_navigation(current_original_idx, remaining_indices, gifts_df):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Previous") and st.session_state.idx > 0:
            st.session_state.idx -= 1
            st.rerun()
    with col2:
        if st.button("Submit & Next"):
            st.session_state.edits[current_original_idx] = st.session_state.wikidata_input
            if st.session_state.idx < len(remaining_indices) - 1:
                st.session_state.idx += 1
            st.rerun()
    with col3:
        if st.button("Next") and st.session_state.idx < len(remaining_indices) - 1:
            st.session_state.idx += 1
            st.rerun()
    with col4:
        if st.button("Save"):
            save_edits(gifts_df,'WikidataID',DATA_FILENAME)
            #for idx, val in st.session_state.edits.items():
            #    gifts_df.at[idx, "WikidataID"] = val
            #gifts_df.to_csv("data/givers_to_lookup.csv", index=False)
            #st.success("Saved successfully.")

gifts_df = get_coding_data(DATA_FILENAME)

remaining_df = gifts_df[
    gifts_df["WikidataID"].isna() |
    (gifts_df["WikidataID"].astype(str).str.strip() == "")
]

init_session_state()

remaining_indices = remaining_df.index.tolist()
current_original_idx = remaining_indices[st.session_state.idx]
current_row = gifts_df.loc[current_original_idx]

# Only preload when index changes
if st.session_state.last_loaded_idx != current_original_idx:
    st.session_state.last_loaded_idx = current_original_idx
    if current_original_idx in st.session_state.edits:
        st.session_state.wikidata_input = st.session_state.edits[current_original_idx]
    elif pd.notna(current_row.get("WikidataID", None)):
        st.session_state.wikidata_input = current_row["WikidataID"]
    else:
        st.session_state.wikidata_input = ""
        
    st.session_state.last_loaded_idx = current_original_idx

show_skip(remaining_indices)

current_row = gifts_df.loc[current_original_idx]

show_screen(current_row, remaining_indices)
show_navigation(current_original_idx, remaining_indices, gifts_df)
