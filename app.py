import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Expert Cashflow Simulator", page_icon="🏛️", layout="wide")
st.title("🏛️ Expert Wealth & Cashflow Simulator")
st.markdown("Detaillierte Simulation mit **Brutto-Netto Logik**, **Karriere-Stufen**, **dynamischen Nebenkosten** und **Schenkungen**.")

# ==========================================
# HILFSFUNKTION: BRUTTO -> NETTO (Vereinfacht DE)
# ==========================================
def schaetze_netto(brutto_jahr, steuerklasse=1):
    # Sehr vereinfachte Annäherung an deutsches Steuersystem für Simulationszwecke
    # Sozialabgaben ca 20% (bis Beitragsbemessungsgrenzen)
    # Steuer progressiv
    
    sozial_abgaben = min(brutto_jahr * 0.20, 15000) # Deckelung BBG ca
    zu_versteuerndes_einkommen = brutto_jahr - sozial_abgaben - 1200 # Werbungskosten pauschal
    
    # Progressive Steuerformel (Grobaunäherung)
    if zu_versteuerndes_einkommen < 11000:
        steuer = 0
    elif zu_versteuerndes_einkommen < 60000:
        steuer = (zu_versteuerndes_einkommen - 11000) * 0.30 
    elif zu_versteuerndes_einkommen < 277000:
        steuer = 14700 + (zu_versteuerndes_einkommen - 60000) * 0.42
    else:
        steuer = 105000 + (zu_versteuerndes_einkommen - 277000) * 0.45
        
    netto = brutto_jahr - sozial_abgaben - steuer
    return max(netto, 0)

# ==========================================
# 1. GRUNDLAGEN & SZENARIO
# ==========================================
with st.sidebar.expander("1. Basis & Markt", expanded=True):
    alter_start = st.number_input("Start Alter", value=31)
    alter_ende = st.number_input("End Alter", value=70)
    startkapital = st.number_input("Startkapital (€)", value=0)
    
    c1, c2 = st.columns(2)
    rendite_pa = c1.number_input("Rendite p.a. (%)", value=7.0, step=0.1) / 100
    inflation_pa = c2.number_input("Inflation p.a. (%)", value=2.0, step=0.1) / 100

# ==========================================
# 2. KARRIERE & GEHALT (MEHRSTUFIG)
# ==========================================
with st.sidebar.expander("2. Karrierepfad (Brutto)", expanded=True):
    st.info("Definiere bis zu 3 Karriere-Phasen. Das System berechnet Netto automatisch.")
    
    # STUFE 1 (Start)
    st.markdown("**Phase 1: Start (Aktuell)**")
    p1_brutto = st.number_input("P1: Brutto Jahresgehalt (€)", value=100000)
    p1_var_anteil = st.slider("P1: Davon Variabel/Bonus (%)", 0, 100, 20, key="p1v") / 100
    p1_steigerung = st.number_input("P1: Gehaltssteigerung p.a. (%)", value=1.0, key="p1s") / 100
    
    # STUFE 2
    has_p2 = st.checkbox("Beförderung 1 hinzufügen?")
    p2_start_alter, p2_brutto, p2_var_anteil, p2_steigerung = 999, 0, 0, 0
    if has_p2:
        st.markdown("**Phase 2: Beförderung 1**")
        p2_start_alter = st.number_input("Alter bei Beförderung 1", value=36)
        p2_brutto = st.number_input("P2: Brutto Zielgehalt (€)", value=130000)
        p2_var_anteil = st.slider("P2: Davon Variabel/Bonus (%)", 0, 100, 30, key="p2v") / 100
        p2_steigerung = st.number_input("P2: Gehaltssteigerung p.a. (%)", value=2.0, key="p2s") / 100

    # STUFE 3
    has_p3 = st.checkbox("Beförderung 2 hinzufügen?")
    p3_start_alter, p3_brutto, p3_var_anteil, p3_steigerung = 999, 0, 0, 0
    if has_p3:
        st.markdown("**Phase 3: Beförderung 2 (Executive)**")
        p3_start_alter = st.number_input("Alter bei Beförderung 2", value=45)
        p3_brutto = st.number_input("P3: Brutto Zielgehalt (€)", value=180000)
        p3_var_anteil = st.slider("P3: Davon Variabel/Bonus (%)", 0, 100, 40, key="p3v") / 100
        p3_steigerung = st.number_input("P3: Gehaltssteigerung p.a. (%)", value=1.5, key="p3s") / 100

# ==========================================
# 3. HAUSHALT & NEBENKOSTEN
# ==========================================
with st.sidebar.expander("3. Haushalt & Nebenkosten", expanded=False):
    partner_aktiv = st.checkbox("Partner im Haushalt?", value=True) # Default 2 Personen
    basis_nk_1person = st.number_input("NK Basis (1 Person) €", value=200, help="Strom, Heizung, Müll für Single")
    kosten_pro_person = st.number_input("Zusatzkosten pro weitere Person €", value=150)
    
    # Logic check for user requirement "350 bei 2 Personen"
    # Wenn User 200 Basis + 150 Zusatz eingibt, sind wir bei 350. Passt.
    
    st.markdown("---")
    st.markdown("**Kinderplanung**")
    kinder_geplant = st.checkbox("Kinder?")
    kinder_liste = []
    kindergeld_std = st.number_input("Kindergeld pro Kind (€)", value=250)
    
    if kinder_geplant:
        anzahl_kids = st.number_input("Anzahl Kinder", 1, 5, 2)
        for i in range(anzahl_kids):
            c1, c2 = st.columns(2)
            geburt = c1.number_input(f"Alter bei Geburt Kind {i+1}", value=33+(i*2))
            kosten = c2.number_input(f"Kosten Kind {i+1} (Start) €", value=600)
            kinder_liste.append({"geburt": geburt, "kosten": kosten})

# ==========================================
# 4. WOHNEN & IMMOBILIE
# ==========================================
with st.sidebar.expander("4. Wohnen & Immobilie", expanded=False):
    kaltmiete_start = st.number_input("Kaltmiete Start (€)", value=1600)
    miet_steigerung_typ = st.radio("Mietanpassung", ["Index (%)", "Staffel (€)"])
    if miet_steigerung_typ == "Index (%)":
        miet_anpassung = st.number_input("Miet-Inflation %", value=2.0)/100
    else:
        miet_anpassung = st.number_input("Staffel Erhöhung € (jährl.)", value=30)
        
    st.markdown("---")
    eigenheim = st.checkbox("Eigenheim Kauf geplant?")
    kauf_alter, kauf_preis, ek_quote, zins, tilgung, instand = 0,0,0,0,0,0
    if eigenheim:
        kauf_alter = st.number_input("Kauf Alter", value=40)
        kauf_preis = st.number_input("Kaufpreis (€)", value=600000)
        ek_quote = st.slider("Eigenkapital Quote %", 0, 100, 20)/100
        zins = st.number_input("Zins %", value=3.5)/100
        tilgung = st.number_input("Tilgung %", value=2.0)/100
        instand = st.number_input("Instandhaltung mtl. (€)", value=400)

# ==========================================
# 5. LIFESTYLE, URLAUB & AUTO
# ==========================================
with st.sidebar.expander("5. Lifestyle, Urlaub, Auto", expanded=False):
    st.markdown("**Basis Lebenshaltung**")
    var_leben = st.number_input("Essen, Drogerie, Freizeit (mtl.) €", value=1200)
    fix_verträge = st.number_input("Verträge (Internet, Handy, Streaming) €", value=150)
    
    st.markdown("---")
    st.markdown("**Urlaube (pro Jahr)**")
    anzahl_urlaube = st.number_input("Anzahl Urlaube", 0, 5, 3)
    urlaub_budget_ges = 0
    for u in range(anzahl_urlaube):
        urlaub_budget_ges += st.number_input(f"Budget Urlaub {u+1} (€)", value=1500, key=f"u{u}")
        
    weihnachten = st.number_input("Weihnachten Budget (€)", value=500)
    
    st.markdown("---")
    st.markdown("**Auto**")
    auto_modus = st.radio("Auto Typ", ["Leasing All-In", "Leasing + Extra", "Kauf"])
    kfz_steuer_vers = 0
    auto_kosten_mtl = 0
    
    if auto_modus == "Leasing All-In":
        auto_kosten_mtl = st.number_input("Leasingrate (All-In) €", value=600)
    elif auto_modus == "Leasing + Extra":
        auto_kosten_mtl = st.number_input("Leasingrate (Nur Auto) €", value=400)
        kfz_steuer_vers = st.number_input("Versicherung/Steuer (jährl.) €", value=800)
    else:
        # Kauf Logik vereinfacht als monatliche Rücklage + laufende Kosten
        auto_kosten_mtl = st.number_input("Rücklage Wertverlust/Reparatur €", value=400)
        kfz_steuer_vers = st.number_input("Versicherung/Steuer (jährl.) €", value=800)

# ==========================================
# 6. SONDER-EVENTS (SCHENKUNG)
# ==========================================
with st.sidebar.expander("6. Geldregen / Schenkung", expanded=False):
    schenkung_aktiv = st.checkbox("Schenkung/Erbe erhalten?")
    schenkung_alter = 0; schenkung_summe = 0
    if schenkung_aktiv:
        schenkung_alter = st.number_input("Alter bei Schenkung", value=45)
        schenkung_summe = st.number_input("Betrag (€)", value=100000)

# ==========================================
# SIMULATION ENGINE
# ==========================================
def run_sim():
    monate = (alter_ende - alter_start) * 12
    data = []
    
    # State
    vermoegen = startkapital
    immo_wert = 0
    restschuld = 0
    rate_bank = 0
    besitzt_haus = False
    
    # Laufende Werte Initialisierung
    curr_kaltmiete = kaltmiete_start
    curr_var_leben = var_leben
    curr_fix_verträge = fix_verträge
    curr_nk_basis = basis_nk_1person
    curr_nk_addon = kosten_pro_person
    
    curr_auto_mtl = auto_kosten_mtl
    curr_kfz_tax = kfz_steuer_vers
    
    curr_urlaub = urlaub_budget_ges
    curr_xmas = weihnachten
    
    # Kindergeld Standard
    k_geld_std = kindergeld_std
    
    # Current Career State Values (Start mit P1)
    curr_brutto = p1_brutto
    curr_var_share = p1_var_anteil
    curr_steigerung = p1_steigerung
    
    for m in range(monate + 1):
        jahr_idx = m // 12
        monat_idx = m % 12
        alter = alter_start + jahr_idx
        jahr_kalender = 2026 + jahr_idx # Start 2026 angenommen lt. Prompt Datum
        
        # --- A. JÄHRLICHE UPDATES (Januar) ---
        if m > 0 and monat_idx == 0:
            # Inflation
            inf_factor = (1 + inflation_pa)
            
            curr_var_leben *= inf_factor
            curr_fix_verträge *= inf_factor
            curr_nk_basis *= inf_factor
            curr_nk_addon *= inf_factor
            curr_urlaub *= inf_factor
            curr_xmas *= inf_factor
            curr_auto_mtl *= inf_factor
            curr_kfz_tax *= inf_factor
            
            # Miete
            if not besitzt_haus:
                if miet_steigerung_typ == "Index (%)":
                    curr_kaltmiete *= (1 + miet_anpassung)
                else:
                    curr_kaltmiete += miet_anpassung
            
            # Gehaltssteigerung (auf das aktuelle Brutto)
            curr_brutto *= (1 + curr_steigerung)
            
            # Immo Wert
            if besitzt_haus: immo_wert *= inf_factor

        # --- B. KARRIERE CHECK (Geburtstag / Jahreswechsel Logik) ---
        # Wir prüfen, ob eine neue Phase beginnt
        if has_p2 and alter == p2_start_alter and monat_idx == 0:
            curr_brutto = p2_brutto
            curr_var_share = p2_var_anteil
            curr_steigerung = p2_steigerung
            
        if has_p3 and alter == p3_start_alter and monat_idx == 0:
            curr_brutto = p3_brutto
            curr_var_share = p3_var_anteil
            curr_steigerung = p3_steigerung

        # --- C. INCOME BERECHNUNG ---
        # 1. Netto berechnen
        netto_jahr = schaetze_netto(curr_brutto)
        
        # Split Fix vs Variabel
        netto_var_total = netto_jahr * curr_var_share
        netto_fix_total = netto_jahr * (1 - curr_var_share)
        
        monats_netto_fix = netto_fix_total / 12
        
        # Variabler Anteil (Bonus) kommt im Dezember (oder Monat 11)
        monats_income = monats_netto_fix
        if monat_idx == 11:
            monats_income += netto_var_total
            
        # 2. Kindergeld
        # Check active kids
        active_kids_count = 0
        kids_cost_now = 0
        
        if kinder_geplant:
            for k in kinder_liste:
                # Kind kostet Geld und bringt Kindergeld zwischen Geburt und 20 (Standard)
                if k["geburt"] <= alter < (k["geburt"] + 20):
                    active_kids_count += 1
                    # Kosten inflationsbereinigt berechnen
                    # Alter des Kindes
                    age_kid = alter - k["geburt"]
                    # Inflationsfaktor seit Start
                    total_inf = (1 + inflation_pa) ** (m / 12)
                    kids_cost_now += (k["kosten"] * total_inf)
        
        monats_income += (active_kids_count * k_geld_std)

        # --- D. SCHENKUNG EVENT ---
        if schenkung_aktiv and alter == schenkung_alter and monat_idx == 6:
            vermoegen += schenkung_summe

        # --- E. HAUSKAUF EVENT ---
        if eigenheim and alter == kauf_alter and monat_idx == 0 and not besitzt_haus:
            nk_kauf = kauf_preis * 0.1
            ek_req = (kauf_preis * ek_quote) + nk_kauf
            kredit = kauf_preis * (1 - ek_quote)
            
            vermoegen -= ek_req
            restschuld = kredit
            rate_bank = (kredit * (zins + tilgung)) / 12
            besitzt_haus = True
            immo_wert = kauf_preis
            curr_kaltmiete = 0 # Bye bye Miete
            
        # --- F. AUSGABEN ---
        # 1. Wohnen (Warm)
        # Personenzahl für Nebenkosten:
        personen_haushalt = (2 if partner_aktiv else 1) + active_kids_count
        nk_total = curr_nk_basis + max(0, (personen_haushalt - 1)) * curr_nk_addon
        
        cost_housing = curr_kaltmiete + nk_total
        if besitzt_haus:
            cost_housing += rate_bank + instand
            # Tilgung
            zins_eur = restschuld * (zins/12)
            restschuld -= (rate_bank - zins_eur)
            if restschuld < 0: restschuld = 0
            
        # 2. Jährliche Einmalkosten (geglättet oder im Dez?)
        # User wollte separate Urlaube und Weihnachten.
        # Wir buchen Urlaub im Juni (Monat 5) und Dezember (Monat 11) zur Hälfte?
        # Oder einfach: Urlaub im Juli, Xmas im Dez, KFZ im Jan.
        
        cost_yearly_events = 0
        if monat_idx == 6: # Sommerurlaub Zeit
             cost_yearly_events += curr_urlaub
        if monat_idx == 11: # Weihnachten
             cost_yearly_events += curr_xmas
        if monat_idx == 0: # KFZ Steuer/Vers
             cost_yearly_events += curr_kfz_tax
             
        # 3. Laufende Kosten
        total_expenses = cost_housing + curr_var_leben + curr_fix_verträge + curr_auto_mtl + kids_cost_now + cost_yearly_events
        
        # --- G. BILANZ ---
        cashflow = monats_income - total_expenses
        
        # Rendite
        r_monat = (1+rendite_pa)**(1/12) - 1
        vermoegen *= (1 + r_monat)
        vermoegen += cashflow
        
        immo_equity = max(0, immo_wert - restschuld)
        
        data.append({
            "Alter": alter,
            "Jahr": jahr_kalender,
            "Monat": monat_idx + 1,
            "Brutto_Jahr": round(curr_brutto),
            "Netto_Monat_Fix": round(monats_netto_fix),
            "Income_Total": round(monats_income),
            "Ausgaben_Wohnen": round(cost_housing),
            "Ausgaben_Kids": round(kids_cost_now),
            "Ausgaben_Events": round(cost_yearly_events),
            "Ausgaben_Total": round(total_expenses),
            "Cashflow": round(cashflow),
            "Vermögen": round(vermoegen),
            "Immo_Netto": round(immo_equity),
            "Gesamtvermögen": round(vermoegen + immo_equity)
        })
        
    return pd.DataFrame(data)

# --- EXECUTION ---
df = run_sim()

# --- VISUALIZATION ---

# Top Metrics
end_vermoegen = df.iloc[-1]["Gesamtvermögen"]
end_cash = df.iloc[-1]["Vermögen"]
max_income = df["Income_Total"].max()

c1, c2, c3 = st.columns(3)
c1.metric("Endvermögen (70)", f"{end_vermoegen:,.0f} €")
c2.metric("Davon Depot", f"{end_cash:,.0f} €")
c3.metric("Max. Cashflow (Monat)", f"{max_income:,.0f} €", "Meist im Dezember")

tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Daten-Tabelle", "ℹ️ Logik-Check"])

with tab1:
    st.subheader("Vermögensaufbau")
    fig_w = go.Figure()
    fig_w.add_trace(go.Scatter(x=df["Alter"], y=df["Vermögen"], name="Depot/Cash", stackgroup='one'))
    if eigenheim:
        fig_w.add_trace(go.Scatter(x=df["Alter"], y=df["Immo_Netto"], name="Immobilie (Netto)", stackgroup='one'))
    
    # Add Schenkung Marker if meaningful
    if schenkung_aktiv:
        fig_w.add_vline(x=schenkung_alter, line_dash="dash", line_color="green", annotation_text="Schenkung")
        
    st.plotly_chart(fig_w, use_container_width=True)
    
    st.subheader("Cashflow Analyse (Monatlich)")
    st.caption("Achte auf die Spitzen im Dezember (Bonus + Weihnachten) und Sommer (Urlaub)")
    
    # Wir zeigen nur einen Ausschnitt (z.B. alle 5 Jahre ein Jahr komplett) oder aggregiert?
    # Besser: Jährliche Summen Bar Chart
    df_yr = df.groupby("Alter").sum(numeric_only=True).reset_index()
    
    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(x=df_yr["Alter"], y=df_yr["Income_Total"], name="Einnahmen (Jahr)", marker_color="green"))
    fig_c.add_trace(go.Bar(x=df_yr["Alter"], y=df_yr["Ausgaben_Total"], name="Ausgaben (Jahr)", marker_color="red"))
    st.plotly_chart(fig_c, use_container_width=True)

with tab2:
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("CSV Download", csv, "expert_cashflow.csv", "text/csv")

with tab3:
    st.markdown(f"""
    ### Verwendete Parameter & Logik
    
    1.  **Steuer-Logik**: Es wird eine vereinfachte deutsche Steuerformel verwendet.
        * Start Brutto: **{p1_brutto:,.0f} €**
        * Errechnetes Netto (Jahr): **{schaetze_netto(p1_brutto):,.0f} €**
        * Dies entspricht ca. **{schaetze_netto(p1_brutto)/p1_brutto*100:.1f}%** Netto-Quote.
    
    2.  **Haushalt & Nebenkosten**:
        * Basis (Single): {basis_nk_1person} €
        * Zusatz pro Person: {kosten_pro_person} €
        * Aktuell berechnet für: **{2 if partner_aktiv else 1} Erwachsene**.
        * Sobald Kinder geboren sind, steigen die NK automatisch.
        
    3.  **Karriere**:
        * Phase 1 (Start) bis Phase 2 (Alter {p2_start_alter if has_p2 else '-'}).
        * Steigerung in Phase 1: {p1_steigerung*100}% p.a. auf das Brutto.
        
    4.  **Events**:
        * Urlaub wird im Juli (Monat 7) abgebucht.
        * Weihnachten im Dezember.
        * Bonus (Variabel) im Dezember.
    """)
