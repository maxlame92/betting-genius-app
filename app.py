import streamlit as st
import google.generativeai as genai
import requests
import json
import re
import os
from datetime import date

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="BettingGenius Debug", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    .status-box { padding: 10px; border-radius: 5px; margin-bottom: 10px; border: 1px solid #334155; }
    .error-box { background-color: #450a0a; color: #fca5a5; padding: 15px; border-radius: 8px; border: 1px solid #f87171; }
    .success-box { background-color: #064e3b; color: #6ee7b7; padding: 15px; border-radius: 8px; border: 1px solid #34d399; }
    .match-box { background: #1E293B; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #3B82F6; display: flex; justify-content: space-between; align-items: center; }
    .stButton>button { width: 100%; background: #3B82F6; color: white; font-weight: bold; border-radius: 8px; height: 50px; border: none; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR & CLÉS
# ==========================================
with st.sidebar:
    st.title("🛠️ BettingGenius")
    st.caption("Mode Diagnostic & Réparation")
    
    # TA CLÉ RAPIDAPI (Celle que tu as fournie)
    # Si elle ne marche pas, c'est qu'elle a atteint son quota ou est désactivée.
    default_rapid_key = "f3ab5bacccmshb976c3672642272p11e8e8jsn6fd372d8e64b"
    
    rapid_key = st.text_input("Clé API-Football", value=default_rapid_key, type="password")
    gemini_key = st.text_input("Clé Gemini AI", type="password")
    
    # BOUTON TEST DIAGNOSTIC
    if st.button("🔴 TESTER MA CLÉ API"):
        url = "https://api-football-v1.p.rapidapi.com/v3/status"
        headers = {
            "X-RapidAPI-Key": rapid_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        try:
            r = requests.get(url, headers=headers)
            data = r.json()
            if "errors" in data and data["errors"]:
                st.error(f"ERREUR CLÉ : {data['errors']}")
            else:
                account = data.get('response', {}).get('account', {})
                st.success(f"✅ Clé Valide ! Prénom: {account.get('firstname')}")
                st.info(f"Quota utilisé : {data.get('response', {}).get('requests', {}).get('current', 0)} / {data.get('response', {}).get('requests', {}).get('limit_day', 100)}")
        except Exception as e:
            st.error(f"Erreur connexion : {e}")

# ==========================================
# 3. LOGIQUE ROBUSTE
# ==========================================

def get_season(selected_date):
    year = selected_date.year
    month = selected_date.month
    # Pour la Premier League et championnats majeurs :
    # Si on est en Aout-Decembre 2025, c'est la saison 2025.
    # Si on est en Janvier-Mai 2026, c'est la saison 2025.
    if month >= 7: return year
    return year - 1

def get_fixtures_debug(api_key, league_id, date_obj):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    season = get_season(date_obj)
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    querystring = {"league": str(league_id), "season": str(season), "date": str(date_obj)}
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        
        # 1. Vérification d'erreurs explicites de l'API
        if "message" in data:
            st.error(f"🛑 Message API : {data['message']}")
            return []
            
        if "errors" in data and data["errors"]:
            # L'API renvoie souvent un objet vide [] ou un message si erreur
            st.markdown(f"""
            <div class="error-box">
                <strong>L'API a refusé la connexion :</strong><br>
                {data['errors']}
            </div>
            """, unsafe_allow_html=True)
            return []
        
        # 2. Vérification des résultats
        results = data.get('results', 0)
        if results == 0:
            st.warning(f"⚠️ L'API a répondu 'OK' (Code 200) mais a trouvé 0 matchs.")
            st.write(f"🔎 Détails requête : Ligue ID {league_id} | Saison {season} | Date {date_obj}")
            st.info("💡 Conseil : Essayez une date où vous êtes sûr qu'il y a match (ex: un Samedi).")
            return []
            
        return data.get('response', [])
        
    except Exception as e:
        st.error(f"Crash Technique : {e}")
        return []

def get_predictions(api_key, fixture_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/predictions"
    headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, params={"fixture": fixture_id})
        return json.dumps(r.json()['response'][0], indent=2)
    except: return None

def build_prompt(match, stats):
    return f"""
    Analyse ce match : {match}. 
    Données API : {stats}
    
    Fais un pronostic JSON STRICT :
    ```json
    {{ "match": "{match}", "pari_principal": "X", "score_exact": "X-X", "confiance": 80, "categorie": "SAFE", "analyse_courte": "..." }}
    ```
    """

# ==========================================
# 4. INTERFACE
# ==========================================
st.title("⚡ BettingGenius - Réparation")

if not gemini_key:
    st.warning("⚠️ Clé Gemini manquante.")
else:
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        leagues = {
            "Premier League": 39, "La Liga": 140, "Bundesliga": 78, "Serie A": 135, "Ligue 1": 61,
            "Champions League": 2, "Saudi Pro League": 307
        }
        l_choice = st.selectbox("Championnat", list(leagues.keys()))
        l_id = leagues[l_choice]
    with c2:
        d_choice = st.date_input("Date", date.today())
    with c3:
        st.write("")
        st.write("")
        btn = st.button("CHERCHER")

    if btn:
        with st.spinner("Interrogation de l'API..."):
            matches = get_fixtures_debug(rapid_key, l_id, d_choice)
            st.session_state.matches = matches

    if 'matches' in st.session_state and st.session_state.matches:
        st.success(f"✅ {len(st.session_state.matches)} matchs trouvés !")
        for m in st.session_state.matches:
            home = m['teams']['home']['name']
            away = m['teams']['away']['name']
            fid = m['fixture']['id']
            time_m = m['fixture']['date'][11:16]
            
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f'<div class="match-box"><b>{time_m}</b> {home} vs {away}</div>', unsafe_allow_html=True)
            with col_b:
                if st.button("Analyser", key=fid):
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    stats = get_predictions(rapid_key, fid)
                    if stats:
                        res = model.generate_content(build_prompt(f"{home}-{away}", stats))
                        st.code(res.text, language="json")
                    else:
                        st.error("Pas de stats API.")