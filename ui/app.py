import streamlit as st
from engine.builder import build_deck

st.set_page_config(page_title="MTG AI Coach", layout="wide")

st.title("MTG AI Coach — Deckbuilder & Tutor (MVP)")

with st.form("build"):
    fmt = st.selectbox("Format", ["standard","commander"])
    seed = st.text_input("Seed card or archetype", "Monastery Swiftspear")
    submitted = st.form_submit_button("Build deck")
    if submitted:
        deck = build_deck(seed, fmt)
        st.subheader("Decklist")
        st.code("\n".join(deck.get("mainboard", [])) or "// TODO")
        st.subheader("Explanation")
        st.write(deck.get("explanation","(stub)"))
