import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Cashflow Tool", layout="wide")
# Etwas CSS für einen saubereren Look
st.markdown(" <style> div.block-container{padding-top:2rem;} </style> ", unsafe_allow_html=True)

st.title("Cashflow Tool")
st.markdown("Definiere deine Parameter in den unteren Sektionen. Alle Eingaben wirken sich sofort auf die Berechnung aus.")

# ==============================================================================
# HILFSFUNKTIONEN
# ==============================================================================

def calc_netto_complex(brutto, st_klasse):
    """
    Näherungsweise Berechnung Netto (DE Simulation).
    """
    sv = min(brutto * 0.20, 18000) # SV Deckelung ca
    
    # Grundfreibetrag Simulation
    if st_klasse == "3": freibetrag = 22000 
    elif st_klasse == "4": freibetrag = 11600
    else: freibetrag = 11600
        
    zvE = max(0, brutto - sv - 1200 - freibetrag)
    
    if zvE <= 0: est = 0
    elif zvE < 62000: est = zvE * 0.30 
    elif zvE < 277000: est = 18000 + (zvE - 62000) * 0.42
    else: est = 110000 + (zvE - 277000) * 0.45

    return max(0, brutto - sv - est)

# ==============================================================================
# INPUT SECTION (EXPANDERS)
# ==============================================================================

# --- 1. SETUP ---
with st.expander("1. Grundeinstellungen, Partner & Markt", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Zeitraum & Start")
        age_start = st.number_input("Startalter", value=31)
        age_end = st.number_input("Endalter (Betrachtung)", value=70)
        start_cap = st.number_input("Startkapital (Du) €", value=0)
        
    with c2:
        st.subheader("Markt & Steuer")
        r_invest = st.number_input("Rendite p.a. (Brutto) %", value=8.0)/100
        r_infla = st.number_input("Inflation p.a. %", value=2.0)/100
        
        has_cap_tax = st.checkbox("Kapitalertragsteuer abziehen?", value=True)
        if has_cap_tax:
            cap_freibetrag = st.number_input("Sparer-Pauschbetrag €", value=1000)
            cap_tax_rate = 0.26375 
        else:
            cap_freibetrag = 99999999
            cap_tax_rate = 0.0
            
    with c3:
        st.subheader("Haushalt & Split")
        partner_share = st.slider("Mein Kostenanteil (%)", 0, 100, 65, help="Wieviel % der GEMEINSAMEN Kosten trägst du?") / 100
        has_partner = st.checkbox("Partner vorhanden?", value=True)

# --- 2. JOB ---
with st.expander("2. Karriere, Gehalt & Steuerklasse", expanded=False):
    st.info("Steuerklassen-Logik simuliert Netto basierend auf DE-Tarifzonen. Bonus wird in Fix/Variabel gesplittet.")
    
    col_st, _ = st.columns([1, 2])
    with col_st:
        tax_class = st.selectbox("Lohnsteuerklasse", ["1", "3", "4"])
    
    c1, c2, c3 = st.columns(3)
    
    # Init Vars
    s2_active, s2_age, s2_brutto, s2_fix, s2_grow = False, 0, 0, 0, 0
    s3_active, s3_age, s3_brutto, s3_fix, s3_grow = False, 0, 0, 0, 0
    
    with c1: 
        st.markdown("**Phase 1 (Start)**")
        s1_brutto = st.number_input("Brutto p.a. €", value=100000)
        s1_fix_share = st.slider("Fix-Anteil %", 0, 100, 80, key="s1") / 100
        s1_growth = st.number_input("Steigerung p.a. %", value=1.0, key="g1") / 100
    
    with c2: 
        st.markdown("**Phase 2 (Beförderung)**")
        s2_active = st.checkbox("Aktivieren", key="s2on")
        if s2_active:
            s2_age = st.number_input("Alter Start", value=36)
            s2_brutto = st.number_input("Brutto p.a. €", value=145000, key="b2")
            s2_fix_share = st.slider("Fix-Anteil %", 0, 100, 75, key="s2") / 100
            s2_growth = st.number_input("Steigerung p.a. %", value=1.0, key="g2") / 100
        else:
            s2_fix_share = s1_fix_share 
        
    with c3: 
        st.markdown("**Phase 3 (Senior)**")
        s3_active = st.checkbox("Aktivieren", key="s3on")
        if s3_active:
            s3_age = st.number_input("Alter Start", value=42, key="a3")
            s3_brutto = st.number_input("Brutto p.a. €", value=180000, key="b3")
            s3_fix_share = st.slider("Fix-Anteil %", 0, 100, 70, key="s3") / 100
            s3_growth = st.number_input("Steigerung p.a. %", value=1.0, key="g3") / 100
        else:
            s3_fix_share = s1_fix_share

    st.markdown("---")
    gift_active = st.checkbox("Schenkung/Erbe?")
    gift_age = 0; gift_val = 0
    if gift_active:
        c4, c5 = st.columns(2)
        gift_age = c4.number_input("Alter bei Schenkung", value=38)
        gift_val = c5.number_input("Betrag €", value=100000)

# --- 3. WOHNEN ---
with st.expander("3. Wohnsituation (Miete vs. Kauf)", expanded=False):
    # Init Vars
    buy_age, price_total, ek_total, loan_amount = 0,0,0,0
    interest_rate, sim_rate_total, maintenance = 0,0,0
    buy_costs_pct = 0
    sondertilgung_active, sondertilgung_amt, sondertilgung_inc = False, 0, 0
    
    c_rent1, c_rent2, c_rent3 = st.columns(3)
    rent_start = c_rent1.number_input("Aktuelle Kaltmiete (Gesamt) €", value=1700)
    rent_incr_mode = c_rent2.radio("Miet-Steigerung", ["Index (%)", "Staffel (€)"])
    if rent_incr_mode == "Index (%)":
        rent_incr_val = c_rent3.number_input("Index %", value=2.0) / 100
    else:
        rent_incr_val = c_rent3.number_input("Staffel € (jährl.)", value=30)
        
    st.divider()
    
    house_mode = st.radio("Strategie", ["Miete", "Eigenheim Kaufen"], horizontal=True)
    
    if house_mode == "Eigenheim Kaufen":
        st.markdown("### 🏠 Kauf & Finanzierung")
        k1, k2, k3 = st.columns(3)
        buy_age = k1.number_input("Kaufalter", value=38)
        price_total = k1.number_input("Kaufpreis (Objekt) €", value=800000)
        buy_costs_pct = k1.number_input("Kaufnebenkosten % (Notar/Steuer)", value=11.5)/100
        
        price_all_in = price_total * (1 + buy_costs_pct)
        ek_total = k2.number_input("Eigenkapital (Gesamt) €", value=400000)
        loan_amount = price_all_in - ek_total
        k2.metric("Kreditsumme", f"{loan_amount:,.0f} €")
        
        interest_rate = k3.number_input("Sollzins %", value=3.4) / 100
        calc_method = k3.radio("Kredit-Modus", ["Rate fixieren", "Laufzeit fixieren"])
        
        if calc_method == "Rate fixieren":
            sim_rate_total = k3.number_input("Wunschrate (Zins+Tilgung) €", value=2300)
        else:
            target_years = k3.number_input("Soll-Laufzeit (Jahre)", value=25)
            q = 1 + interest_rate/12
            n = target_years * 12
            if loan_amount > 0:
                sim_rate_total = loan_amount * (q**n * (q-1)) / (q**n - 1)
            k3.success(f"Notwendige Rate: {sim_rate_total:,.2f} €")
            
        maintenance = k1.number_input("Instandhaltung (Gesamt) €", value=400)
        
        # SONDERTILGUNG
        st.caption("Sondertilgung")
        if st.checkbox("Sondertilgung planen?"):
            sondertilgung_active = True
            sc1, sc2 = st.columns(2)
            sondertilgung_amt = sc1.number_input("Betrag pro Jahr €", value=10000)
            sondertilgung_inc = sc2.number_input("Jährliche Erhöhung €", value=0)

    st.divider()
    st.caption("Nebenkosten (skalieren mit Personenanzahl)")
    nc1, nc2 = st.columns(2)
    nk_base_1 = nc1.number_input("NK Basis (1 Person) €", value=200)
    nk_add_p = nc2.number_input("Zusatz pro weitere Person €", value=75)

# --- 4. AUTO ---
with st.expander("4. Mobilität & Auto-Historie", expanded=False):
    st.markdown("Definiere verschiedene Phasen nacheinander.")
    
    c1, c2 = st.columns(2)
    # Phase 1: Leasing A
    c1.markdown("**Phase 1: Leasing**")
    car_p1_dur = c1.number_input("Dauer (Jahre) P1", value=3)
    car_p1_cost = c1.number_input("Rate (All-In) P1 €", value=450)
    
    # Phase 2: Leasing B
    c2.markdown("**Phase 2: Leasing**")
    has_p2_car = c2.checkbox("Phase 2 an?", value=True)
    car_p2_dur = 0; car_p2_cost = 0
    if has_p2_car:
        car_p2_dur = c2.number_input("Dauer (Jahre) P2", value=3)
        car_p2_cost = c2.number_input("Rate (All-In) P2 €", value=550)
        
    # Phase 3: Leasing C
    c1.markdown("**Phase 3: Leasing**")
    has_p3_car = c1.checkbox("Phase 3 an?", value=True)
    car_p3_dur = 0; car_p3_cost = 0
    if has_p3_car:
        car_p3_dur = c1.number_input("Dauer (Jahre) P3", value=3)
        car_p3_cost = c1.number_input("Rate (All-In) P3 €", value=650)
        
    # Phase 4: Kauf
    c2.markdown("**End-Phase: Kauf & Halten**")
    has_buy_car = c2.checkbox("Wechsel auf Kauf?", value=True)
    car_buy_price = 0; car_buy_cycle = 6; car_buy_run = 0; car_buy_tax = 0
    if has_buy_car:
        car_buy_price = c2.number_input("Kaufpreis (Basis Heute) €", value=35000)
        car_buy_cycle = c2.number_input("Neukauf alle X Jahre", value=8)
        car_buy_run = c2.number_input("Rücklage Reparatur (mtl) €", value=150)
        car_buy_tax = c2.number_input("Vers./Steuer (Jahr) €", value=800)

# --- 5. LIFESTYLE & KINDER ---
with st.expander("5. Lifestyle, Kinder & Sonderausgaben", expanded=False):
    # 1. Kinder Logik (Erweitert)
    st.subheader("👶 Kinder (3-Phasen-Modell)")
    has_kids = st.checkbox("Kinder einplanen?")
    kids_list = []
    
    # Init vars
    cost_k1=0; cost_k2=0; cost_k3=0; kgeld_val=0; age_k1_end=0; age_k2_end=0; age_k3_end=0; kgeld_end=0
    
    if has_kids:
        # Konfiguration Phasen
        k_col1, k_col2, k_col3, k_col4 = st.columns(4)
        cost_k1 = k_col1.number_input("Kosten Phase 1 (Kind) €", value=800)
        age_k1_end = k_col1.number_input("Bis Alter", value=12)
        
        cost_k2 = k_col2.number_input("Kosten Phase 2 (Jugend) €", value=1000)
        age_k2_end = k_col2.number_input("Bis Alter ", value=18)
        
        cost_k3 = k_col3.number_input("Kosten Phase 3 (Student) €", value=1200)
        age_k3_end = k_col3.number_input("Bis Alter  ", value=25)
        
        kgeld_val = k_col4.number_input("Kindergeld €", value=250)
        kgeld_end = k_col4.number_input("Kindergeld Ende (Alter)", value=25)
        
        st.markdown("###### Geburtstermine")
        n_kids = st.number_input("Anzahl Kinder", 1, 5, 2)
        cols = st.columns(n_kids)
        for i in range(n_kids):
            with cols[i]:
                birth_age = st.number_input(f"Dein Alter bei Kind {i+1}", value=33 + (i*3))
                kids_list.append(birth_age)

    st.divider()
    
    # 2. Lifestyle
    col_share, col_pers = st.columns(2)
    
    with col_share:
        st.markdown("### Geteilte Kosten (Haushalt)")
        st.caption("Dein Anteil: " + str(partner_share*100) + "%")
        cost_groc = st.number_input("Supermarkt/Drogerie €", value=600)
        cost_food = st.number_input("Gastro/Bestellen €", value=500)
        cost_internet = st.number_input("Internet/Strom/TV €", value=170)
        
        st.markdown("#### Urlaube (Gesamt)")
        n_vacations = st.number_input("Anzahl Urlaube p.a.", 1, 5, 3)
        budget_vac_total = 0
        for v in range(n_vacations):
            budget_vac_total += st.number_input(f"Budget Urlaub {v+1} €", value=2000, key=f"vac{v}")
            
    with col_pers:
        st.markdown("### 100% Deine Kosten")
        pers_streaming = st.number_input("Streaming/Abos €", value=50)
        pers_insur = st.number_input("Eigene Vers. (Haft/BU) €", value=80)
        pers_fun = st.number_input("Hobby/Freizeit/Bar €", value=150)
        pers_mobile = st.number_input("Handyvertrag €", value=15)
        
        st.markdown("#### Jährliche Sonderausgaben (Du)")
        cost_clothes = st.number_input("Klamotten (Jahr) €", value=600)
        cost_gadgets = st.number_input("Gadgets/Tech (Jahr) €", value=1000)
        cost_xmas = st.number_input("Weihnachten/Geschenke (Jahr) €", value=500)

# --- 6. RENTE ---
with st.expander("6. Rentenphase & Entnahme", expanded=False):
    renten_alter = st.number_input("Renteneintrittsalter", value=67)
    gesetzl_rente = st.number_input("Erwartete Gesetzl. Rente (Netto nach Steuer) €", value=3000)
    entnahme_modus = st.radio("Entnahme-Strategie", ["Kapitalverzehr (Alles ausgeben)", "Ewige Rente (Nur Erträge)"])

# ==============================================================================
# LOGIC ENGINE
# ==============================================================================

def simulate():
    months = (age_end - age_start) * 12
    data = []
    
    wealth = start_cap
    loan_bal = 0
    house_val = 0
    own_house = False
    
    # Init Pointers
    cur_brutto = s1_brutto
    cur_fix_share = s1_fix_share
    cur_growth = s1_growth
    
    cur_rent = rent_start
    
    # Kosten Init
    c_nk_base = nk_base_1; c_nk_add = nk_add_p
    c_groc = cost_groc; c_food = cost_food; c_util = cost_internet
    c_vac_total = budget_vac_total
    
    c_stream = pers_streaming; c_insur = pers_insur; c_fun = pers_fun; c_mob = pers_mobile
    c_cloth = cost_clothes; c_gadget = cost_gadgets; c_xmas = cost_xmas
    c_maint = maintenance
    
    # Kinder Kosten (Basis heute)
    ck1 = cost_k1; ck2 = cost_k2; ck3 = cost_k3
    
    # Auto
    cbuy_price = car_buy_price; cbuy_run = car_buy_run; cbuy_tax = car_buy_tax
    
    soti_curr = sondertilgung_amt
    sim_rate = 0 
    
    # Auto Timing berechnen
    end_p1 = car_p1_dur * 12
    end_p2 = end_p1 + (car_p2_dur * 12 if has_p2_car else 0)
    end_p3 = end_p2 + (car_p3_dur * 12 if has_p3_car else 0)
    
    for m in range(months + 1):
        idx_yr = m // 12
        idx_mo = m % 12
        age = age_start + idx_yr
        year = 2026 + idx_yr
        
        is_retired = (age >= renten_alter)
        
        # --- JANUAR UPDATES (Inflation) ---
        if m > 0 and idx_mo == 0:
            f_inf = (1 + r_infla)
            # Inflation
            c_nk_base *= f_inf; c_nk_add *= f_inf
            c_groc *= f_inf; c_food *= f_inf; c_util *= f_inf
            c_vac_total *= f_inf; c_cloth *= f_inf; c_gadget *= f_inf; c_xmas *= f_inf
            c_stream *= f_inf; c_insur *= f_inf; c_fun *= f_inf; c_mob *= f_inf
            c_maint *= f_inf
            
            # Kinderkosten steigen
            ck1 *= f_inf; ck2 *= f_inf; ck3 *= f_inf
            
            # Auto Kaufpreis & Unterhalt (Buy Phase)
            cbuy_price *= f_inf; cbuy_run *= f_inf; cbuy_tax *= f_inf
            
            # Gehalt
            cur_brutto *= (1 + cur_growth)
            
            # Miete
            if not own_house:
                if rent_incr_mode == "Index (%)": cur_rent *= (1 + rent_incr_val)
                else: cur_rent += rent_incr_val
            
            if own_house: house_val *= f_inf
            soti_curr += sondertilgung_inc

        # --- EVENTS ---
        if s2_active and age == s2_age and idx_mo == 0:
            cur_brutto = s2_brutto; cur_fix_share = s2_fix_share; cur_growth = s2_growth
        if s3_active and age == s3_age and idx_mo == 0:
            cur_brutto = s3_brutto; cur_fix_share = s3_fix_share; cur_growth = s3_growth
            
        # HAUSKAUF
        if house_mode == "Eigenheim Kaufen" and age == buy_age and idx_mo == 0 and not own_house:
            ek_invest = ek_total * partner_share
            wealth -= ek_invest
            loan_bal = loan_amount
            sim_rate = sim_rate_total
            house_val = price_total # Wert = Objektpreis
            own_house = True
            cur_rent = 0
            
        if gift_active and age == gift_age and idx_mo == 6:
            wealth += gift_val

        # --- INCOME ---
        if not is_retired:
            netto_jahr = calc_netto_complex(cur_brutto, tax_class)
            netto_fix_mo = (netto_jahr * cur_fix_share) / 12
            netto_var_yr = netto_jahr * (1 - cur_fix_share)
            
            income = netto_fix_mo
            if idx_mo == 11: income += netto_var_yr
        else:
            # Rente
            income = gesetzl_rente * ((1 + 0.01)**(idx_yr)) # Annahme: Rente steigt leicht

        # Kindergeld & Kinderkosten (Phasen)
        n_kids_in_house = 0
        kids_inc_now = 0
        kids_cost_now = 0
        
        if has_kids:
            for k_birth in kids_list:
                k_age = age - k_birth
                if k_age >= 0:
                    # Welche Kostenphase?
                    c_k_curr = 0
                    if k_age < age_k1_end: c_k_curr = ck1
                    elif k_age < age_k2_end: c_k_curr = ck2
                    elif k_age < age_k3_end: c_k_curr = ck3
                    
                    if c_k_curr > 0: n_kids_in_house += 1
                    
                    # Kindergeld
                    if k_age < kgeld_end:
                        kids_inc_now += kgeld_val
                    
                    kids_cost_now += c_k_curr

        income += kids_inc_now
        
        # --- AUTO LOGIK (PHASEN) ---
        c_auto_curr = 0
        # Phase Check
        if m < end_p1:
            c_auto_curr = car_p1_cost # Leasing 1
        elif m < end_p2:
            c_auto_curr = car_p2_cost # Leasing 2
        elif m < end_p3:
            c_auto_curr = car_p3_cost # Leasing 3
        else:
            # Buy Phase
            if has_buy_car:
                c_auto_curr = cbuy_run
                if idx_mo == 0: c_auto_curr += cbuy_tax
                
                # Kauf Event alle X Jahre
                months_in_buy = m - end_p3
                if months_in_buy >= 0 and months_in_buy % (car_buy_cycle*12) == 0:
                    wealth -= cbuy_price
        
        # --- EXPENSES ---
        # Haushaltsgröße für NK
        persons = (2 if has_partner else 1) + n_kids_in_house
        nk_curr = c_nk_base + max(0, (persons - 1)) * c_nk_add
        
        # 1. Wohnen
        if own_house:
            housing_cost_shared = sim_rate + nk_curr + c_maint + c_util
            zins_eur = loan_bal * (interest_rate/12)
            loan_bal -= (sim_rate - zins_eur)
            
            if sondertilgung_active and idx_mo == 11 and loan_bal > 0:
                loan_bal -= soti_curr
                wealth -= (soti_curr * partner_share)
            
            if loan_bal < 0: loan_bal = 0
        else:
            housing_cost_shared = cur_rent + nk_curr + c_util
        
        my_housing = housing_cost_shared * partner_share
        
        # 2. Lifestyle & Kinder
        shared_var = c_groc + c_food
        if idx_mo == 6: shared_var += c_vac_total 
        
        my_var_share = shared_var * partner_share
        my_kids_share = kids_cost_now * partner_share
        
        # Persönlich
        my_pers = c_stream + c_insur + c_mob + c_fun + c_auto_curr
        if idx_mo == 4: my_pers += c_cloth
        if idx_mo == 10: my_pers += c_gadget
        if idx_mo == 11: my_pers += c_xmas
        
        total_out = my_housing + my_var_share + my_kids_share + my_pers
        
        # --- BILANZ ---
        cf = income - total_out
        
        gain = wealth * ((1 + r_invest)**(1/12) - 1)
        if has_cap_tax and gain > 0:
            taxable = max(0, gain - (cap_freibetrag/12))
            gain -= (taxable * cap_tax_rate)
            
        wealth += gain
        wealth += cf
        
        # Entnahme im Alter
        if is_retired and cf < 0 and entnahme_modus == "Kapitalverzehr (Alles ausgeben)":
            wealth += cf # negativ, also Abzug
            
        equity = max(0, house_val - loan_bal) * partner_share
        
        data.append({
            "Alter": age, "Jahr": year, "Monat": idx_mo+1,
            "Einkommen": round(income),
            "Ausgaben_Total": round(total_out),
            "Ausgaben_Wohnen": round(my_housing),
            "Ausgaben_Kinder": round(my_kids_share),
            "Ausgaben_Auto": round(c_auto_curr),
            "Ausgaben_Leben": round(my_var_share),
            "Ausgaben_Persönlich": round(my_pers),
            "Cashflow": round(cf),
            "Vermögen": round(wealth),
            "Immo_Equity": round(equity),
            "Gesamtvermögen": round(wealth + equity),
            "Restschuld": round(loan_bal),
            "Urlaub_Invest": round((c_vac_total if idx_mo == 6 else 0) * partner_share)
        })
        
    return pd.DataFrame(data)

df = simulate()

# ==============================================================================
# OUTPUT / DASHBOARD
# ==============================================================================
st.divider()
st.header("📊 Ergebnis Analyse")

last = df.iloc[-1]
c1, c2, c3 = st.columns(3)
c1.metric("Endvermögen (Alter " + str(age_end) + ")", f"{last['Gesamtvermögen']:,.0f} €", f"Restschuld: {last['Restschuld']:,.0f} €")
vac_sum = df["Urlaub_Invest"].sum()
c2.metric("Lebenszeit-Ausgabe Urlaub", f"{vac_sum:,.0f} €")
c3.metric("Liquidität (Depot)", f"{last['Vermögen']:,.0f} €")

# TABS FOR CHARTS
tab_ch1, tab_ch2, tab_data = st.tabs(["📈 Charts", "📌 Meilensteine", "📋 Rohdaten"])

with tab_ch1:
    st.subheader("🏔️ Die 'Rush Hour' deines Lebens (Ausgaben)")
    df_yr = df.groupby("Alter").sum(numeric_only=True).reset_index()
    fig_stack = go.Figure()
    fig_stack.add_trace(go.Scatter(x=df_yr["Alter"], y=df_yr["Ausgaben_Wohnen"], name="Wohnen", stackgroup='one'))
    fig_stack.add_trace(go.Scatter(x=df_yr["Alter"], y=df_yr["Ausgaben_Kinder"], name="Kinder", stackgroup='one'))
    fig_stack.add_trace(go.Scatter(x=df_yr["Alter"], y=df_yr["Ausgaben_Auto"], name="Auto", stackgroup='one'))
    fig_stack.add_trace(go.Scatter(x=df_yr["Alter"], y=df_yr["Ausgaben_Leben"], name="Lifestyle", stackgroup='one'))
    fig_stack.add_trace(go.Scatter(x=df_yr["Alter"], y=df_yr["Ausgaben_Persönlich"], name="Privat", stackgroup='one'))
    fig_stack.update_layout(height=450, yaxis_title="Jahresausgaben €", hovermode="x unified")
    st.plotly_chart(fig_stack, use_container_width=True)
    
    st.subheader("📈 Vermögensentwicklung")
    fig_w = go.Figure()
    fig_w.add_trace(go.Scatter(x=df["Alter"], y=df["Vermögen"], name="Liquides Depot", fill='tozeroy'))
    fig_w.add_trace(go.Scatter(x=df["Alter"], y=df["Immo_Equity"], name="Immo Equity (Netto)", fill='tonexty'))
    st.plotly_chart(fig_w, use_container_width=True)

with tab_ch2:
    milestones = [35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
    mask = (df["Alter"].isin(milestones)) & (df["Monat"] == 1)
    st.dataframe(df.loc[mask, ["Alter", "Gesamtvermögen", "Restschuld", "Cashflow", "Ausgaben_Kinder"]].style.format("{:,.0f} €"), use_container_width=True)

with tab_data:
    st.dataframe(df)
    st.download_button("📥 Detail-Daten (CSV)", df.to_csv(sep=";", decimal=",").encode('utf-8'), "finanzplan_final.csv")