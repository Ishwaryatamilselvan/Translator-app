import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import re
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Route Name Translator", page_icon="📍")

# தலைப்பு
st.markdown("<h2 style='text-align: center;'>📍 பஸ் வழித்தடப் பெயர் மொழிபெயர்ப்பாளர்</h2>", unsafe_allow_html=True)

def clean_text(text):
    if not isinstance(text, str): return ""
    # CamelCase-ஐ பிரித்தல் (எ.கா: TrichyCentral -> Trichy Central)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # சிம்பல்களை நீக்குதல்
    text = re.sub(r'[-_]', ' ', text)
    # '20sec' போன்ற தேவையற்ற சொற்களை நீக்குதல்
    text = re.sub(r'\s*\d+\s*sec', '', text, flags=re.IGNORECASE)
    return text.strip()

def translate_logic(text):
    if not text or pd.isna(text): return ""
    try:
        return GoogleTranslator(source='en', target='ta').translate(text)
    except:
        return text

uploaded_file = st.file_uploader("உங்கள் CSV கோப்பை பதிவேற்றவும்", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    if 'ROUTE NAME' in df.columns:
        st.success("கோப்பு தயாராக உள்ளது!")
        
        if st.button("🚀 வழித்தடங்களை மட்டும் மொழிபெயர்க்கவும்"):
            # ROUTE NAME-ல் உள்ள தனித்துவமான பெயர்களை மட்டும் எடுத்தல் (வேகத்திற்காக)
            unique_routes = df['ROUTE NAME'].dropna().unique()
            
            progress_bar = st.progress(0)
            translated_map = {}

            with st.spinner("தமிழில் மாற்றப்படுகிறது..."):
                with ThreadPoolExecutor(max_workers=10) as executor:
                    cleaned_texts = [clean_text(str(t)) for t in unique_routes]
                    results = list(executor.map(translate_logic, cleaned_texts))
                    
                    for i, original in enumerate(unique_routes):
                        translated_map[original] = results[i]
                        progress_bar.progress(int(((i + 1) / len(unique_routes)) * 100))

            # புதிய 'Route_Tamil' காலமை உருவாக்குதல்
            df['Route_Tamil'] = df['ROUTE NAME'].map(translated_map)
            
            st.subheader("✅ மொழிபெயர்க்கப்பட்ட தரவு:")
            # Name அசல் வடிவிலேயே இருக்கும், Route மட்டும் தமிழில் இருக்கும்
            st.dataframe(df[['Name', 'ROUTE NAME', 'Route_Tamil']].head(10))
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 கோப்பை பதிவிறக்கம் செய்",
                data=csv,
                file_name="translated_routes.csv",
                mime="text/csv"
            )
    else:
        st.error("பிழை: கோப்பில் 'ROUTE NAME' என்ற காலம் இல்லை!")
