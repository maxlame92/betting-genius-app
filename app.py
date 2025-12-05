import streamlit as st
import google.generativeai as genai
import requests
import json
import re
import os
from datetime import date

# ==========================================
# 1. CONFIGURATION INITIALE
# ==========================================
st.set_page_config(
    page_title="BettingGenius Auto",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. DESIGN CSS
# ==========================================
st.markdown("""
<style>
    /* BASE */
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    h1 { color: #F8FAFC; text-transform: uppercase; font-weight: 800; }
    
    /* BOUTONS */
    .stButton>button {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: white; border: none; font-weight: bold; border-radius: 8px; width: 100%;
    }
    
    /* STYLE TICKET RESULTAT */
    .coupon-container {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border: 1px solid #334155;
    }
    .border-safe { border-left: 6px solid #22C55E; }
    .border-psycho { border-left: 6px solid #A855F7; }
    .border-fun { border-left: 6px solid #F59E0B; }
    
    /* MATCH BOX */
    .match-box {
        background: #1E293B; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #3B82F6;
        display: flex; justify-content: space-between; align-items: center;
    }
    .match-time { font-weight: bold; color: #94A3B8; margin-right: 15px; }
    .match-teams { font-size: 1.1em; font-weight: bold; color: white; }
    
    /* JAUGE DE CONFIANCE */
    .progress-track { background: #334155; height: 6px; border-radius: 3px; margin-top: 5px; width: 100%; }
    .progress-bar { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #22C55E, #4ADE80); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR (JUSTE GEMINI MAINTENANT)
# ==========================================
with st.sidebar:
    st.title("⚡ BettingGenius")
    st.caption("Version API Intégrée")
    st.markdown("---")
    
    # On demande seulement la clé Google Gemini car l'autre est déjà dans le code
    gemini_key = os.environ.get("GOOGLE_API_KEY")
    if not gemini_key:
        gemini_key = st.text_input("🔑 Clé Gemini AI", type="password")
    
    st.success("✅ Clé API-Football intégrée")
    st.info("Le système est prêt à l'emploi.")
    
    model_version = st.selectbox("Modèle IA", ["gemini-1.5-flash", "gemini-2.0-flash-exp"])

# ==========================================
# 4. LOGIQUE API (AVEC TA CLÉ INTÉGRÉE)
# ==========================================

# --- TA CLÉ EST ICI ---
RAPID_API_KEY = "f3ab5bacccmshb976c3672642272p11e8e8jsn6fd372d8e64b"
RAPID_API_HOST = "api-football-v1.p.rapidapi.com"

def get_headers():
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": RAPID_API_HOST
    }

def get_season(selected_date):
    """Calcule la saison foot (Ex: Déc 2024 = Saison 2024 / Jan 2025 = Saison 2024)"""
    year = selected_date.year
    month = selected_date.month
    if month >= 7: return year
    else: return year - 1

def get_fixtures(league_id, date_obj):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    season = get_season(date_obj)
    
    querystring = {"league": str(league_id), "season": str(season), "date": str(date_obj)}
    
    try:
        response = requests.get(url, headers=get_headers(), params=querystring)
        data = response.json()
        
        # Gestion des erreurs API
        if "errors" in data and data["errors"]:
            # Souvent lié au quota ou permission
            st.error(f"Erreur API : {data['errors']}")
            return []
            
        return data.get('response', [])
    except Exception as e:
        st.error(f"Erreur connexion : {e}")
        return []

def get_match_predictions(fixture_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/predictions"
    try:
        response = requests.get(url, headers=get_headers(), params={"fixture": str(fixture_id)})
        data = response.json().get('response', [])
        return json.dumps(data[0], indent=2) if data else None
    except:
        return None

def build_api_prompt(match_title, json_data):
    return f"""
    Tu es "BettingGenius". Analyse le match : {match_title}
    
    DONNÉES TECHNIQUES API (JSON) :
    {json_data}
    
    --- MISSION ---
    1. Analyse les Stats, la Forme et les Probabilités de l'API.
    2. Déduis un pronostic logique.
    
    --- FORMAT JSON FINAL ---
    ```json
    {{
        "match": "{match_title}",
        "pari_principal": "Ex: Victoire Real",
        "score_exact": "Ex: 2-1",
        "corners": "Ex: +9.5",
        "total_buts": "Ex: +2.5",
        "confiance": 80,
        "categorie": "SAFE",
        "facteur_psycho": "Ex: FORME DOMICILE",
        "analyse_courte": "Phrase courte."
    }}
    ```
    """

# ==========================================
# 5. INTERFACE PRINCIPALE
# ==========================================

st.title("⚡ BettingGenius - Auto Mode")

if not gemini_key:
    st.warning("⚠️ Veuillez entrer votre Clé Google Gemini à gauche.")
else:
    # FILTRES
    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        leagues = {
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 39,
            "🇪🇸 La Liga": 140,
            "🇫🇷 Ligue 1": 61,
            "🇩🇪 Bundesliga": 78,
            "🇮🇹 Serie A": 135,
            "🇪🇺 Champions League": 2,
            "🇵🇹 Liga Portugal": 94,
            "🇳🇱 Eredivisie": 88,
            "🇹🇷 Süper Lig": 203,
            "🇸🇦 Saudi Pro League": 307
        }
        league_choice = st.selectbox("Championnat", list(leagues.keys()))
        league_id = leagues[league_choice]
        
    with c2:
        # Date par défaut = Aujourd'hui
        date_choice = st.date_input("Date du match", date.today())
        
    with c3:
        st.write("") 
        st.write("") 
        search_btn = st.button("🔎 CHERCHER")

    # LOGIQUE RECHERCHE
    if search_btn:
        with st.spinner(f"Recherche..."):
            matches = get_fixtures(league_id, date_choice)
            st.session_state['matches'] = matches
            st.session_state['analysis_result'] = None

    # RESULTATS LISTE
    if 'matches' in st.session_state and st.session_state['matches']:
        st.markdown(f"### {len(st.session_state['matches'])} Matchs le {date_choice}")
        
        for m in st.session_state['matches']:
            home = m['teams']['home']['name']
            away = m['teams']['away']['name']
            fid = m['fixture']['id']
            time_match = m['fixture']['date'][11:16]
            
            # Affichage Match
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"""
                <div class="match-box">
                    <div>
                        <span class="match-time">{time_match}</span>
                        <span class="match-teams">{home} vs {away}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_b:
                if st.button(f"Analyser 🧠", key=fid):
                    with st.spinner("Analyse IA en cours..."):
                        stats = get_match_predictions(fid)
                        if stats:
                            genai.configure(api_key=gemini_key)
                            model = genai.GenerativeModel(model_version)
                            try:
                                res = model.generate_content(build_api_prompt(f"{home}-{away}", stats))
                                full_text = res.text
                                # Parse
                                j_match = re.search(r'\{.*\}', full_text, re.DOTALL)
                                if j_match:
                                    j = json.loads(re.sub(r'//.*', '', j_match.group(0)))
                                    st.session_state['analysis_result'] = {"json": j, "text": full_text}
                            except Exception as e:
                                st.error(f"Erreur IA : {e}")
                        else:
                            st.error("Stats indisponibles (Trop tôt ou Ligue mineure).")
                            
    elif 'matches' in st.session_state:
        st.warning(f"🚫 Aucun match trouvé à cette date. Vérifiez que la date correspond bien à une journée de championnat.")

    # AFFICHAGE TICKET
    if 'analysis_result' in st.session_state and st.session_state['analysis_result']:
        res = st.session_state['analysis_result']
        j = res['json']
        cat = j.get('categorie', 'FUN')
        border = "border-safe" if cat=="SAFE" else "border-psycho" if cat=="PSYCHO" else "border-fun"
        
        st.markdown("---")
        st.markdown(f"""
        <div class="coupon-container {border}">
            <div style="display:flex; justify-content:space-between;">
                <h3>{j.get('match')}</h3>
                <div>
                    <span class="badge" style="background:#581C87; padding:5px; border-radius:4px;">{j.get('facteur_psycho')}</span>
                    <strong style="color:#4ADE80; font-size:1.2em;">{j.get('confiance')}%</strong>
                </div>
            </div>
            <div class="progress-track"><div class="progress-bar" style="width: {j.get('confiance')}%;"></div></div>
            
            <div style="text-align:center; margin:20px 0; background:#0F172A; padding:15px; border-radius:8px; border:1px dashed #334155;">
                <div style="color:#22C55E; font-size:1.5em; font-weight:800;">🏆 {j.get('pari_principal')}</div>
            </div>
            
            <div style="display:flex; gap:10px; text-align:center;">
                <div style="flex:1; background:#0F172A; padding:10px; border-radius:6px;">
                    <div style="color:#94A3B8; font-size:0.8em;">SCORE</div>
                    <div style="font-weight:bold;">{j.get('score_exact')}</div>
                </div>
                <div style="flex:1; background:#0F172A; padding:10px; border-radius:6px;">
                    <div style="color:#94A3B8; font-size:0.8em;">BUTS</div>
                    <div style="font-weight:bold;">{j.get('total_buts')}</div>
                </div>
            </div>
            <br>
            <div style="font-style:italic; color:#CBD5E1;">"{j.get('analyse_courte')}"</div>
        </div>
        """, unsafe_allow_html=True)