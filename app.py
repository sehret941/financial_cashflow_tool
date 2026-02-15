import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# --- PAGE SETUP ---
st.set_page_config(page_title="Ultimate Cashflow Detail", page_icon="💎", layout="wide")
st.title("💎 Ultimate Cashflow: Jede Variable einzeln")
st.markdown("""
Hier ist **alles** aufgeteilt. Fixkosten sind nicht mehr ein Block, sondern Strom, Internet, Streaming, Versicherungen sind einzelne Hebel.
Die Inflation wirkt auf jeden Posten individuell (außer Kredite/Fix-Mieten).
""")

# =========================================================
# 1. SZENARIEN & GLOBAL
# =========================================================
with st.sidebar.expander("🌍 1. Markt & Szenario", expanded=True):
    szenario = st.selectbox("Szenario", ["Basis", "Optimistisch", "Crash/Pessimistisch"])
    if szenario == "Basis":
        rendite = 5.0; inflation = 2.0
    elif szenario == "Optimistisch":
        rendite = 8.0; inflation = 1.5
    else:
        rendite = 3.0; inflation = 4.0
    
    rendite_input = st.number_input("Rendite (%)", value=rendite, step=0.1)/100
    inflation_input = st.number_input("Inflation (%)", value=inflation, step=0.1)/100

    crash_aktiv = st.checkbox("Crash simulieren?")
    if crash_aktiv:
        crash_jahr = st.number_input("Crash in Jahr X", value=5)
        crash_drop = st.slider("Verlust %", 10, 60, 30)/100
    else:
        crash_jahr = 999; crash_drop = 0

with st.sidebar.expander("👤 2. Status Quo", expanded=True):
    alter_jetzt = st.number_input("Alter", value=30)
    alter_ziel = st.number_input("Ziel-Alter", value=70)
    depot_wert = st.number_input("Startkapital €", value=30000)

# =========================================================
# 2. EINNAHMEN
# =========================================================
with st.sidebar.expander("💼 3. Einkommen", expanded=False):
    netto = st.number_input("Netto mtl. €", value=3500)
    steigerung = st.slider("Gehaltsplus p.a. %", 0.0, 10.0, 2.0, 0.1)/100
    
    st.caption("BONUS")
    bonus = st.number_input("Bonus Netto €", value=2000)
    bonus_spar = st.slider("Davon Sparen %", 0, 100, 50)/100

    st.caption("KARRIERE-SPRUNG")
    sprung_aktiv = st.checkbox("Beförderung?")
    sprung_alter = 0; sprung_netto = 0
    if sprung_aktiv:
        c1, c2 = st.columns(2)
        sprung_alter = c1.number_input("Alter Sprung", value=35)
        sprung_netto = c2.number_input("Neues Netto", value=5000)

# =========================================================
# 3. AUSGABEN (ULTRA DETAIL)
# =========================================================
with st.sidebar.expander("🏠 4. Wohnen & Nebenkosten (Detail)", expanded=True):
    wohn_modus = st.radio("Wohn-Modus", ["Miete", "Eigenheim Kauf"], horizontal=True)
    
    # NEBENKOSTEN (Fallen immer an, egal ob Miete oder Kauf)
    st.caption("NEBENKOSTEN (Strom/Wasser/Heizung)")
    nk_strom = st.number_input("Strom & Heizung €", value=150)
    nk_sonst = st.number_input("Müll/Wasser/Gebäude €", value=100)
    
    # SPECIFIC HOUSING
    miete_kalt = 0; miet_steigerung_art = ""; miet_steigerung_val = 0
    kauf_alter = 0; haus_preis = 0; ek_quote = 0; zins = 0; tilgung = 0; instandhaltung = 0
    
    if wohn_modus == "Miete":
        miete_kalt = st.number_input("Kaltmiete €", value=800)
        miet_steigerung_art = st.selectbox("Miet-Erhöhung", ["Prozent %", "Fixbetrag € (Staffel)"])
        if miet_steigerung_art == "Prozent %":
            miet_steigerung_val = st.number_input("Steigerung %", value=2.0)/100
        else:
            miet_steigerung_val = st.number_input("Steigerung € (alle 12 Mon)", value=30)
            
    else: # Kauf
        st.write("---")
        kauf_alter = st.number_input("Kauf-Alter", value=35)
        haus_preis = st.number_input("Kaufpreis €", value=500000)
        ek_quote = st.slider("Eigenkapital %", 0, 100, 20)/100
        zins = st.number_input("Zins %", value=3.5)/100
        tilgung = st.number_input("Tilgung %", value=2.0)/100
        instandhaltung = st.number_input("Instandhaltung Rücklage €", value=400)

with st.sidebar.expander("📄 5. Fixe Verträge (Detail)", expanded=False):
    st.markdown("Diese Posten steigen mit der Inflation.")
    c1, c2 = st.columns(2)
    fix_internet = c1.number_input("Internet & Handy €", value=80)
    fix_streaming = c2.number_input("Streaming/Abos €", value=40)
    fix_versich = c1.number_input("Versicherungen (Haft/Haus) €", value=60)
    fix_sonst = c2.number_input("Sonstige Verträge €", value=20)

with st.sidebar.expander("🍔 6. Variable Lifestyle (Detail)", expanded=False):
    c1, c2 = st.columns(2)
    var_supermarkt = c1.number_input("Supermarkt/Drogerie €", value=400)
    var_gastro = c2.number_input("Essen Gehen/Bestellen €", value=200)
    var_tanken = c1.number_input("Tanken/Öffis €", value=100)
    var_genuss = c2.number_input("Genuss (Zigaretten/Vape) €", value=150)
    var_geschenke = c1.number_input("Geschenke €", value=50)
    var_spass = c2.number_input("Freizeit/Bar/Hobby €", value=100)

with st.sidebar.expander("🎁 7. Jährliche Sonderausgaben (Detail)", expanded=False):
    c1, c2 = st.columns(2)
    sonder_urlaub = c1.number_input("Urlaub (Jahr) €", value=2500)
    sonder_xmas = c2.number_input("Weihnachten €", value=600)
    sonder_bday = c1.number_input("Geburtstage (Wir) €", value=300)
    sonder_kfz = c2.number_input("KfZ Vers./Steuer (Jahr) €", value=600)

with st.sidebar.expander("🚗 8. Auto Anschaffung", expanded=False):
    auto_modus = st.radio("Auto Typ", ["Leasing", "Kauf (Cash)"])
    auto_kosten = 0; auto_kauf_preis = 0; auto_intervall = 0
    if auto_modus == "Leasing":
        auto_kosten = st.number_input("Leasingrate €", value=400)
    else:
        auto_kauf_preis = st.number_input("Kaufpreis Auto €", value=30000)
        auto_intervall = st.number_input("Kauf alle X Jahre", value=8)
        auto_rep = st.number_input("Reparatur Rücklage €", value=100)

with st.sidebar.expander("👶 9. Kinder", expanded=False):
    has_kids = st.checkbox("Kinder?")
    kids_n = 1; kids_start = 33; kids_cost = 600; kindergeld = 250
    if has_kids:
        kids_n = st.number_input("Anzahl", 1, 5, 1)
        kids_start = st.number_input("Alter bei Start", value=33)
        kids_cost = st.number_input("Kosten pro Kind €", value=600)

# =========================================================
# SIMULATION ENGINE (THE BRAIN)
# =========================================================

def simulate():
    monate = (alter_ziel - alter_jetzt) * 12
    data = []
    
    # State Vars
    verm_liquid = depot_wert
    immo_wert = 0
    schulden = 0
    rate_bank = 0
    has_house = False
    
    # Current Cost Trackers (Initial Values)
    c_strom = nk_strom
    c_nk_sonst = nk_sonst
    c_miete = miete_kalt if wohn_modus == "Miete" else 0
    
    c_inet = fix_internet
    c_stream = fix_streaming
    c_vers = fix_versich
    c_fix_sonst = fix_sonst
    
    c_super = var_supermarkt
    c_gastro = var_gastro
    c_tank = var_tanken
    c_genuss = var_genuss
    c_gift = var_geschenke
    c_spass = var_spass
    
    c_auto_lease = auto_kosten if auto_modus == "Leasing" else 0
    c_auto_rep = auto_rep if auto_modus == "Kauf (Cash)" else 0
    
    c_urlaub = sonder_urlaub
    c_xmas = sonder_xmas
    c_bday = sonder_bday
    c_kfz_tax = sonder_kfz
    
    c_kid = kids_cost if has_kids else 0
    
    curr_netto = netto
    
    for m in range(monate + 1):
        jahr_idx = m // 12
        monat_idx = m % 12
        alter = alter_jetzt + jahr_idx
        jahr_kalender = 2024 + jahr_idx
        
        # --- 1. INFLATION & ANPASSUNGEN (Januar) ---
        if m > 0 and monat_idx == 0:
            # Inflationäre Posten
            f_inf = (1 + inflation_input)
            
            c_strom *= f_inf
            c_nk_sonst *= f_inf
            c_inet *= f_inf
            c_stream *= f_inf
            c_vers *= f_inf
            c_fix_sonst *= f_inf
            
            c_super *= f_inf
            c_gastro *= f_inf
            c_tank *= f_inf
            c_genuss *= f_inf
            c_gift *= f_inf
            c_spass *= f_inf
            
            c_auto_lease *= f_inf
            c_auto_rep *= f_inf
            
            c_urlaub *= f_inf
            c_xmas *= f_inf
            c_bday *= f_inf
            c_kfz_tax *= f_inf
            c_kid *= f_inf
            
            # Gehalt
            curr_netto *= (1 + steigerung)
            
            # Miete Spezial
            if not has_house and wohn_modus == "Miete":
                if miet_steigerung_art == "Prozent %":
                    c_miete *= (1 + miet_steigerung_val)
                else:
                    c_miete += miet_steigerung_val
            
            # Immo Wert
            if has_house: immo_wert *= f_inf

            # Auto Kauf Event (Cash)
            if auto_modus == "Kauf (Cash)" and jahr_idx > 0 and (jahr_idx % int(auto_intervall) == 0):
                preis_neu = auto_kauf_preis * (f_inf ** jahr_idx)
                verm_liquid -= preis_neu # Hard cash out
        
        # --- 2. EVENTS ---
        # Beförderung
        if sprung_aktiv and alter == sprung_alter and monat_idx == 0:
            curr_netto = sprung_netto
            
        # Hauskauf
        if wohn_modus == "Eigenheim Kauf" and alter == kauf_alter and monat_idx == 0 and not has_house:
            nk = haus_preis * 0.1
            ek_req = (haus_preis * ek_quote) + nk
            kredit = haus_preis * (1 - ek_quote)
            
            verm_liquid -= ek_req
            schulden = kredit
            rate_bank = (kredit * (zins + tilgung)) / 12
            has_house = True
            immo_wert = haus_preis
            c_miete = 0 # Miete fällt weg
        
        # --- 3. CASHFLOW BERECHNUNG ---
        
        # Income
        income_flow = curr_netto
        # Bonus Dez
        if monat_idx == 11:
            curr_bonus = bonus * ((1+steigerung)**jahr_idx)
            income_flow += curr_bonus
            # Wir ziehen den Konsum-Teil gleich ab (simuliert Ausgabe)
            bonus_konsum = curr_bonus * (1 - bonus_spar)
        else:
            bonus_konsum = 0
            
        # Kids
        if has_kids and kids_start <= alter < (kids_start + 20):
            income_flow += (kindergeld * kids_n)
            cost_kids_total = (c_kid * kids_n)
        else:
            cost_kids_total = 0
            
        # Ausgaben Gruppen bilden (für Übersicht)
        # Fix Wohnen
        cost_housing = c_miete + c_strom + c_nk_sonst
        if has_house: 
            cost_housing += rate_bank + instandhaltung
            # Tilgung abziehen
            zins_anteil = schulden * (zins/12)
            schulden -= (rate_bank - zins_anteil)
            if schulden < 0: schulden = 0
            
        # Fix Verträge
        cost_contracts = c_inet + c_stream + c_vers + c_fix_sonst
        
        # Variable
        cost_variable = c_super + c_gastro + c_tank + c_genuss + c_gift + c_spass
        
        # Auto
        cost_auto = c_auto_lease + c_auto_rep
        
        # Sonderausgaben (Jahresglättung / 12)
        cost_yearly_prorated = (c_urlaub + c_xmas + c_bday + c_kfz_tax) / 12
        
        total_expenses = cost_housing + cost_contracts + cost_variable + cost_auto + cost_yearly_prorated + cost_kids_total + bonus_konsum
        
        net_flow = income_flow - total_expenses
        
        # Wealth Update
        r_monat = (1+rendite_input)**(1/12)-1
        if crash_aktiv and jahr_idx == crash_jahr and monat_idx == 6:
            verm_liquid *= (1 - crash_drop)
        else:
            verm_liquid *= (1 + r_monat)
        
        verm_liquid += net_flow
        
        immo_net = max(0, immo_wert - schulden)
        
        # --- DATA LOGGING (JEDE VAR EINZELN!) ---
        data.append({
            "Alter": alter,
            "Jahr": jahr_kalender,
            "Monat": monat_idx + 1,
            # Vermögen
            "Vermögen_Liquid": round(verm_liquid),
            "Immo_Equity": round(immo_net),
            "Gesamtvermögen": round(verm_liquid + immo_net),
            # Flows
            "Einnahmen_Total": round(income_flow),
            "Ausgaben_Total": round(total_expenses),
            "Sparbetrag": round(net_flow),
            # DETAILS (Das wolltest du!)
            "Kosten_Miete": round(c_miete),
            "Kosten_Bankrate": round(rate_bank if has_house else 0),
            "Kosten_StromHeizung": round(c_strom),
            "Kosten_Internet": round(c_inet),
            "Kosten_Streaming": round(c_stream),
            "Kosten_Supermarkt": round(c_super),
            "Kosten_Gastro": round(c_gastro),
            "Kosten_Genuss": round(c_genuss),
            "Kosten_Auto_Laufend": round(cost_auto),
            "Kosten_Kinder": round(cost_kids_total)
        })

    return pd.DataFrame(data)

df = simulate()

# =========================================================
# DASHBOARD
# =========================================================

# Top KPIs
end_nw = df.iloc[-1]["Gesamtvermögen"]
end_liq = df.iloc[-1]["Vermögen_Liquid"]
col1, col2, col3 = st.columns(3)
col1.metric("Endvermögen (Gesamt)", f"{end_nw:,.0f} €")
col2.metric("Davon Depot/Cash", f"{end_liq:,.0f} €")
if "Kosten_Bankrate" in df.columns and df.iloc[-1]["Kosten_Bankrate"] > 0:
    col3.metric("Monatliche Rate (Ende)", f"{df.iloc[-1]['Kosten_Bankrate']:,.0f} €", "Bleibt fix!")
else:
    col3.metric("Miete (Ende)", f"{df.iloc[-1]['Kosten_Miete']:,.0f} €", "Inflationär")

tab1, tab2, tab3 = st.tabs(["📊 Charts", "🔬 Detail-Daten", "📥 Export"])

with tab1:
    st.subheader("Ausgaben-Struktur im Zeitverlauf")
    st.markdown("Hier siehst du, wie die Inflation die einzelnen Bereiche aufbläht, während Kredite fix bleiben.")
    
    # Aggregieren auf Jahresebene für Chart
    df_yr = df.groupby("Alter").mean(numeric_only=True).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_yr["Alter"], y=df_yr["Kosten_Miete"]+df_yr["Kosten_Bankrate"], stackgroup='one', name='Wohnen (Miete/Kredit)'))
    fig.add_trace(go.Scatter(x=df_yr["Alter"], y=df_yr["Kosten_StromHeizung"]+df_yr["Kosten_Internet"]+df_yr["Kosten_Streaming"], stackgroup='one', name='Nebenkosten & Verträge'))
    fig.add_trace(go.Scatter(x=df_yr["Alter"], y=df_yr["Kosten_Supermarkt"]+df_yr["Kosten_Gastro"]+df_yr["Kosten_Genuss"], stackgroup='one', name='Lifestyle (Essen/Spaß)'))
    fig.add_trace(go.Scatter(x=df_yr["Alter"], y=df_yr["Kosten_Kinder"], stackgroup='one', name='Kinder'))
    
    fig.update_layout(title="Monatliche Kostenblöcke (Stacked)", yaxis_title="€ pro Monat")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Blick in die Datenbank")
    st.markdown("Hier siehst du, dass wirklich **jede Variable** einzeln berechnet wurde.")
    st.dataframe(df.head(12)) # Zeige erstes Jahr

with tab3:
    st.subheader("Excel/CSV Export")
    st.markdown("Lade die Datei herunter, um in Excel weiterzuarbeiten. Alle Spalten sind enthalten.")
    csv = df.to_csv(index=False, sep=";").encode('utf-8')
    st.download_button("💾 Download Detaillierter Report (.csv)", csv, "cashflow_detail.csv", "text/csv")
