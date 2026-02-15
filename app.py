import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ultimate Cashflow Master", page_icon="🏛️", layout="wide")
# Padding reduzieren
st.markdown(" <style> div.block-container{padding-top:1rem;} </style> ", unsafe_allow_html=True)

st.title("🏛️ Ultimate Cashflow: Detail-Planung & Partner-Split")

# ==============================================================================
# 1. SETUP & HAUSHALT (GLOBAL)
# ==============================================================================
tab_setup, tab_job, tab_house, tab_life, tab_res = st.tabs([
    "1. Setup & Partner", 
    "2. Karriere (Mehrstufig)", 
    "3. Wohnen (Kauf/Miete)", 
    "4. Lifestyle & Details",
    "5. Analyse & Meilensteine"
])

with tab_setup:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Basis Daten")
        age_start = st.number_input("Startalter", value=31)
        age_end = st.number_input("Endalter", value=70)
        start_cap = st.number_input("Startkapital (Du) €", value=0)
        
    with c2:
        st.subheader("Markt")
        r_invest = st.number_input("Rendite p.a. (%)", value=7.0)/100
        r_infla = st.number_input("Inflation p.a. (%)", value=2.0)/100
        
    with c3:
        st.subheader("Haushalt & Split")
        partner_share = st.slider("Mein Kostenanteil (%)", 0, 100, 65, help="Wieviel % der GEMEINSAMEN Kosten trägst du?") / 100
        has_partner = st.checkbox("Partner vorhanden?", value=True)
        
    st.divider()
    st.subheader("Kinderplanung")
    has_kids = st.checkbox("Kinder einplanen?")
    kids_data = []
    if has_kids:
        n_kids = st.number_input("Anzahl Kinder", 1, 5, 2)
        k_geld_val = st.number_input("Kindergeld pro Kind €", value=250)
        cols = st.columns(n_kids)
        for i in range(n_kids):
            with cols[i]:
                birth_age = st.number_input(f"Dein Alter bei Kind {i+1}", value=33 + (i*2))
                kids_data.append(birth_age)
    else:
        k_geld_val = 0

# ==============================================================================
# 2. KARRIERE (MEHRERE STUFEN)
# ==============================================================================
with tab_job:
    st.info("Definiere deine Karriere-Stufen. Steuer wird automatisch geschätzt.")
    
    # STUFE 1 (START)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown("**Phase 1 (Start)**")
    s1_brutto = c1.number_input("Brutto p.a. €", value=100000)
    s1_fix_share = c1.slider("Fix-Anteil % (Rest Bonus)", 0, 100, 80, key="s1") / 100
    s1_growth = c1.number_input("Steigerung p.a. %", value=1.0, key="g1") / 100
    
    # STUFE 2
    with c2: 
        st.markdown("**Phase 2 (Beförderung)**")
        s2_active = st.checkbox("Aktivieren", key="s2on")
        s2_age = st.number_input("Alter bei Start", value=36)
        s2_brutto = st.number_input("Brutto p.a. €", value=130000, key="b2")
        s2_fix_share = st.slider("Fix-Anteil %", 0, 100, 75, key="s2") / 100
        s2_growth = st.number_input("Steigerung p.a. %", value=1.5, key="g2") / 100
        
    # STUFE 3
    with c3: 
        st.markdown("**Phase 3 (Senior/Exec)**")
        s3_active = st.checkbox("Aktivieren", key="s3on")
        s3_age = st.number_input("Alter bei Start", value=42, key="a3")
        s3_brutto = st.number_input("Brutto p.a. €", value=160000, key="b3")
        s3_fix_share = st.slider("Fix-Anteil %", 0, 100, 70, key="s3") / 100
        s3_growth = st.number_input("Steigerung p.a. %", value=1.0, key="g3") / 100
        
    # SCHENKUNG
    with c4:
        st.markdown("**Schenkung / Erbe**")
        gift_active = st.checkbox("Schenkung?")
        gift_age = st.number_input("Alter", value=50)
        gift_val = st.number_input("Betrag €", value=100000)

# ==============================================================================
# 3. WOHNEN (MIETE vs KAUF RECHNER)
# ==============================================================================
with tab_house:
    house_mode = st.radio("Strategie", ["Miete", "Kauf"], horizontal=True)
    
    # Initialisierung aller Variablen (WICHTIG gegen NameError)
    rent_start = 0
    rent_incr_mode = "Index (%)"
    rent_incr_val = 0
    
    buy_age = 0
    price_total = 0
    ek_total = 0
    loan_amount = 0
    interest_rate = 0
    sim_rate_total = 0
    maintenance = 0
    
    # NEBENKOSTEN LOGIK (PERSONENABHÄNGIG)
    st.subheader("Nebenkosten (Gesamt-Haushalt)")
    st.caption("Basis für 1-3+ Personen Haushalt. Wird automatisch skaliert.")
    c1, c2, c3 = st.columns(3)
    nk_base_1 = c1.number_input("NK Basis (1 Person) €", value=200)
    nk_add_p = c2.number_input("Zusatz pro weitere Person €", value=75) # Damit bei 2 Pers ca 350 rauskommt (200+150)
    
    if house_mode == "Miete":
        c1, c2 = st.columns(2)
        rent_start = c1.number_input("Kaltmiete Start (Gesamt) €", value=1600)
        rent_incr_mode = c2.radio("Steigerung", ["Index (%)", "Staffel (€)"])
        if rent_incr_mode == "Index (%)":
            rent_incr_val = c2.number_input("Index %", value=2.0) / 100
        else:
            rent_incr_val = c2.number_input("Staffel € (jährl.)", value=30)
            
    else: # KAUF
        st.divider()
        st.markdown("### 🏠 Kauf-Finanzierung (Profi-Rechner)")
        k1, k2, k3 = st.columns(3)
        buy_age = k1.number_input("Kaufalter", value=38)
        price_total = k1.number_input("Kaufpreis (inkl. NK) €", value=700000)
        ek_total = k2.number_input("Eigenkapital (Gesamt) €", value=150000)
        loan_amount = price_total - ek_total
        
        k2.metric("Kreditsumme", f"{loan_amount:,.0f} €")
        
        interest_rate = k3.number_input("Sollzins %", value=3.4) / 100
        calc_method = k3.radio("Berechnung", ["Rate fixieren (Wann fertig?)", "Laufzeit fixieren (Welche Rate?)"])
        
        if calc_method == "Rate fixieren (Wann fertig?)":
            sim_rate_total = k3.number_input("Wunschrate (Zins+Tilgung) €", value=2300)
        else:
            target_years = k3.number_input("Laufzeit (Jahre)", value=25)
            # Annuität: R = K * q^n * (q-1) / (q^n - 1)
            q = 1 + interest_rate/12
            n = target_years * 12
            if loan_amount > 0:
                sim_rate_total = loan_amount * (q**n * (q-1)) / (q**n - 1)
            k3.success(f"Notwendige Rate: {sim_rate_total:,.2f} €")
            
        maintenance = k1.number_input("Instandhaltung (Gesamt) €", value=400)

# ==============================================================================
# 4. LIFESTYLE & DETAILS (GRANULAR)
# ==============================================================================
with tab_life:
    st.markdown("### Geteilte Kosten (Haushalt Total)")
    st.caption("Diese Posten werden addiert und dann mit deinem Split-Faktor verrechnet.")
    
    l1, l2, l3 = st.columns(3)
    # Variable Details
    cost_groc = l1.number_input("Supermarkt/Drogerie €", value=600)
    cost_food = l1.number_input("Essen gehen/Bestellen €", value=200)
    cost_internet = l2.number_input("Internet/Festnetz €", value=50)
    cost_electr = l2.number_input("Strom (Separat) €", value=100)
    cost_gez = l2.number_input("Rundfunk/Sonst. Wohnen €", value=20)
    
    # Urlaube (Mehrfach)
    st.markdown("---")
    st.markdown("### Urlaube & Events (Jährlich Total)")
    u1, u2 = st.columns(2)
    n_vacations = u1.number_input("Anzahl Urlaube p.a.", 1, 5, 3)
    budget_vac_total = 0
    for v in range(n_vacations):
        budget_vac_total += u2.number_input(f"Budget Urlaub {v+1} €", value=1500, key=f"vac{v}")
        
    cost_xmas = u1.number_input("Weihnachten (Pauschal) €", value=500)
    
    st.markdown("---")
    st.markdown("### Persönliche Kosten (100% Du)")
    p1, p2 = st.columns(2)
    # Fix & Variable Persönlich
    pers_streaming = p1.number_input("Streaming/Abos €", value=30)
    pers_insur = p1.number_input("Eigene Versicherungen €", value=80)
    pers_fun = p2.number_input("Hobby/Freizeit/Bar €", value=200)
    pers_mobile = p2.number_input("Handyvertrag €", value=40)
    
    # AUTO
    st.markdown("---")
    st.markdown("### Dein Auto")
    car_type = st.selectbox("Typ", ["Leasing (All-In)", "Leasing (+Extra)", "Kauf (Bar)", "Kein Auto"])
    car_cost_mo = 0
    car_tax_yr = 0
    car_buy_price = 0
    car_cycle = 6
    
    if "Leasing" in car_type:
        car_cost_mo = st.number_input("Leasingrate €", value=450)
        if "Extra" in car_type:
            car_tax_yr = st.number_input("Versicherung/Steuer (Jahr) €", value=800)
    elif "Kauf" in car_type:
        car_buy_price = st.number_input("Kaufpreis (Basis heute) €", value=35000)
        car_cycle = st.number_input("Neukauf alle X Jahre", value=6)
        car_cost_mo = st.number_input("Rücklage Reparatur/Wartung mtl €", value=150)
        car_tax_yr = st.number_input("Versicherung/Steuer (Jahr) €", value=800)


# ==============================================================================
# LOGIC ENGINE (DER KERN)
# ==============================================================================

def calc_tax(brutto):
    # Solide DE Schätzung für Simulation (Stkl 1)
    sv = min(brutto * 0.20, 16000) 
    taxable = brutto - sv - 1200
    if taxable < 11600: tax = 0
    elif taxable < 66000: tax = (taxable - 11600) * 0.35
    else: tax = 19000 + (taxable - 66000) * 0.42
    return brutto - sv - tax

def simulate():
    months = (age_end - age_start) * 12
    data = []
    
    # State Vars
    wealth = start_cap
    loan_bal = 0
    house_val = 0
    own_house = False
    
    # Current Pointers (Wachsen mit Infla oder Karriere)
    cur_brutto = s1_brutto
    cur_fix_share = s1_fix_share
    cur_growth = s1_growth
    
    cur_rent = rent_start
    
    # Startwerte für Kosten (werden inflatiert)
    # Haushalt (Basis)
    c_nk_base = nk_base_1
    c_nk_add = nk_add_p
    c_groc = cost_groc
    c_food = cost_food
    c_inet = cost_internet
    c_elec = cost_electr
    c_gez = cost_gez
    # Variable c_maint sicherstellen (auf 0 fallback wenn nicht Kauf)
    c_maint = maintenance
    
    # Events
    c_vac_total = budget_vac_total
    c_xmas = cost_xmas
    
    # Persönlich
    c_stream = pers_streaming
    c_insur = pers_insur
    c_fun = pers_fun
    c_mob = pers_mobile
    c_car_mo = car_cost_mo
    c_car_tax = car_tax_yr
    
    sim_rate = 0 # Hypothek
    
    for m in range(months + 1):
        idx_yr = m // 12
        idx_mo = m % 12
        age = age_start + idx_yr
        year = 2026 + idx_yr
        
        # --- A. INFLATION & ANPASSUNGEN (Januar) ---
        if m > 0 and idx_mo == 0:
            f_inf = (1 + r_infla)
            
            # Alle inflationären Kosten hochziehen
            c_nk_base *= f_inf; c_nk_add *= f_inf
            c_groc *= f_inf; c_food *= f_inf
            c_inet *= f_inf; c_elec *= f_inf; c_gez *= f_inf
            c_maint *= f_inf
            c_vac_total *= f_inf; c_xmas *= f_inf
            c_stream *= f_inf; c_insur *= f_inf; c_fun *= f_inf; c_mob *= f_inf
            c_car_mo *= f_inf; c_car_tax *= f_inf
            
            # Gehalt wächst (auf Basis der aktuellen Stufe)
            cur_brutto *= (1 + cur_growth)
            
            # Miete
            if not own_house and house_mode == "Miete":
                if rent_incr_mode == "Index (%)": cur_rent *= (1 + rent_incr_val)
                else: cur_rent += rent_incr_val
            
            # Hauswert
            if own_house: house_val *= f_inf
            
            # Auto Neukauf (Treppen-Effekt)
            if "Kauf" in car_type and idx_yr > 0 and idx_yr % int(car_cycle) == 0:
                price_now = car_buy_price * (f_inf ** idx_yr)
                wealth -= price_now
                
        # --- B. KARRIERE EVENTS ---
        if s2_active and age == s2_age and idx_mo == 0:
            cur_brutto = s2_brutto; cur_fix_share = s2_fix_share; cur_growth = s2_growth
        if s3_active and age == s3_age and idx_mo == 0:
            cur_brutto = s3_brutto; cur_fix_share = s3_fix_share; cur_growth = s3_growth
            
        # --- C. HAUSKAUF EVENT ---
        if house_mode == "Kauf" and age == buy_age and idx_mo == 0 and not own_house:
            # Wir nehmen an, DU zahlst deinen Share am EK
            ek_invest = ek_total * partner_share
            wealth -= ek_invest
            
            loan_bal = loan_amount
            sim_rate = sim_rate_total
            house_val = price_total
            own_house = True
            cur_rent = 0
            
        # --- D. SCHENKUNG ---
        if gift_active and age == gift_age and idx_mo == 6:
            wealth += gift_val

        # --- E. EINKOMMEN ---
        netto_jahr = calc_tax(cur_brutto)
        
        # Split Fix/Variabel
        netto_fix_mo = (netto_jahr * cur_fix_share) / 12
        netto_var_yr = netto_jahr * (1 - cur_fix_share)
        
        income_flow = netto_fix_mo
        bonus_flow = 0
        if idx_mo == 11:
            income_flow += netto_var_yr
            bonus_flow = netto_var_yr
            
        # Kindergeld
        n_kids_act = 0
        if has_kids:
            for k_birth in kids_data:
                if k_birth <= age < (k_birth + 20): # Bis 20 Jahre
                    n_kids_act += 1
        income_flow += (n_kids_act * k_geld_val)
        
        # --- F. AUSGABEN (DETAILLIERT & GESPLITTET) ---
        
        # 1. HAUSHALTSGRÖSSE (Für Nebenkosten)
        # Partner (1) + Du (1) + Kinder
        persons = (2 if has_partner else 1) + n_kids_act
        # Kosten: Basis (1) + (N-1)*Zusatz
        nk_total = c_nk_base + max(0, (persons - 1)) * c_nk_add
        
        # 2. WOHNEN (HAUSHALT TOTAL)
        cost_housing_tot = cur_rent + nk_total + c_elec + c_inet + c_gez
        if own_house:
            cost_housing_tot = sim_rate + nk_total + c_elec + c_inet + c_gez + c_maint
            # Tilgung
            zins_eur = loan_bal * (interest_rate/12)
            loan_bal -= (sim_rate - zins_eur)
            if loan_bal < 0: loan_bal = 0
            
        # 3. LIFESTYLE (HAUSHALT TOTAL)
        cost_life_tot = c_groc + c_food 
        # Urlaub im Juli
        if idx_mo == 6: cost_life_tot += c_vac_total
        
        # ===> SPLIT APPLICATION <===
        my_housing = cost_housing_tot * partner_share
        my_life_share = cost_life_tot * partner_share
        
        # 4. PERSÖNLICH (100% DU)
        my_pers = c_stream + c_insur + c_fun + c_mob + c_car_mo
        if idx_mo == 0: my_pers += c_car_tax # KFZ Steuer Jan
        if idx_mo == 11: my_pers += c_xmas # Weihnachten
        
        # Bonus Sparen Logic (Wir nehmen an: Was nicht gespart wird, ist Konsum)
        # Hier vereinfacht: Alles geht ins Wealth, Ausgaben senken es.
        
        total_expenses = my_housing + my_life_share + my_pers
        
        # --- G. CASHFLOW ---
        cf = income_flow - total_expenses
        
        wealth *= (1 + r_invest)**(1/12)
        wealth += cf
        
        # Net Worth Share
        equity = max(0, house_val - loan_bal) * partner_share
        
        # DATA LOGGING (JEDE SPALTE!)
        data.append({
            "Alter": age, "Jahr": year, "Monat": idx_mo+1,
            "Netto_Total": round(income_flow),
            "Sparrate": round(cf),
            "Vermögen_Liquid": round(wealth),
            "Immo_Equity": round(equity),
            "Gesamtvermögen": round(wealth + equity),
            "Restschuld_Haus": round(loan_bal),
            # DETAIL SPALTEN (DEIN ANTEIL)
            "Kosten_Wohnen_Anteil": round(my_housing),
            "Kosten_Supermarkt_Anteil": round(c_groc * partner_share),
            "Kosten_Urlaub_Anteil": round((c_vac_total if idx_mo==6 else 0) * partner_share),
            "Kosten_Auto": round(c_car_mo + (c_car_tax if idx_mo==0 else 0)),
            "Kosten_Persönlich_Fix": round(c_stream + c_insur + c_mob),
            "Kosten_Spaß": round(c_fun),
        })
        
    return pd.DataFrame(data)

df = simulate()

# ==============================================================================
# 5. OUTPUT & MEILENSTEINE
# ==============================================================================
with tab_res:
    # KPI
    curr_nw = df.iloc[-1]["Gesamtvermögen"]
    curr_liq = df.iloc[-1]["Vermögen_Liquid"]
    st.metric("Dein Endvermögen (Alter 70)", f"{curr_nw:,.0f} €", f"Davon Depot: {curr_liq:,.0f} €")
    
    st.divider()
    
    st.markdown("### 📌 5-Jahres-Meilensteine (Die Excel-Ansicht)")
    st.caption("Zeigt den Stand jeweils im Januar des Jahres.")
    
    # Filter für Meilensteine (Januar Werte)
    milestones = [35, 40, 45, 50, 55, 60, 65, 70]
    mask = (df["Alter"].isin(milestones)) & (df["Monat"] == 1)
    df_miles = df.loc[mask, ["Alter", "Gesamtvermögen", "Vermögen_Liquid", "Immo_Equity", "Restschuld_Haus", "Sparrate"]]
    
    # Schön formatieren
    st.dataframe(df_miles.style.format("{:,.0f} €"), use_container_width=True)
    
    st.divider()
    
    st.markdown("### 🔬 Deep Dive: Alle Spalten")
    st.dataframe(df, use_container_width=True)
    st.download_button("Excel/CSV Download", df.to_csv(sep=";", decimal=",").encode('utf-8'), "detail_plan.csv")
    
    # Charts
    st.markdown("### 📈 Visualisierung")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Alter"], y=df["Vermögen_Liquid"], name="Depot", stackgroup='one'))
    if house_mode == "Kauf":
        fig.add_trace(go.Scatter(x=df["Alter"], y=df["Immo_Equity"], name="Haus Equity (Deins)", stackgroup='one'))
    st.plotly_chart(fig, use_container_width=True)
