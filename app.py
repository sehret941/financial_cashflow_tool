import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ultimate Cashflow Master", page_icon="🏛️", layout="wide")
st.markdown(" <style> div.block-container{padding-top:1rem;} </style> ", unsafe_allow_html=True)

st.title("🏛️ Ultimate Cashflow: Detail-Planung & Analysen")

# ==============================================================================
# 1. SETUP & HAUSHALT (GLOBAL)
# ==============================================================================
tab_setup, tab_job, tab_house, tab_life, tab_res = st.tabs([
    "1. Setup & Partner", 
    "2. Karriere", 
    "3. Wohnen (Miete/Kauf)", 
    "4. Lifestyle & Shopping",
    "5. 📊 ANALYSE (Neu)"
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
# 2. KARRIERE
# ==============================================================================
with tab_job:
    st.info("Definiere deine Karriere-Stufen. Steuer wird automatisch geschätzt.")
    c1, c2, c3 = st.columns(3)
    
    with c1: 
        st.markdown("**Phase 1 (Start)**")
        s1_brutto = st.number_input("Brutto p.a. €", value=100000)
        s1_fix_share = st.slider("Fix-Anteil %", 0, 100, 80, key="s1") / 100
        s1_growth = st.number_input("Steigerung p.a. %", value=1.0, key="g1") / 100
    
    with c2: 
        st.markdown("**Phase 2 (Beförderung)**")
        s2_active = st.checkbox("Aktivieren", key="s2on")
        s2_age = st.number_input("Alter bei Start", value=36)
        s2_brutto = st.number_input("Brutto p.a. €", value=130000, key="b2")
        s2_fix_share = st.slider("Fix-Anteil %", 0, 100, 75, key="s2") / 100
        s2_growth = st.number_input("Steigerung p.a. %", value=1.5, key="g2") / 100
        
    with c3: 
        st.markdown("**Phase 3 (Senior)**")
        s3_active = st.checkbox("Aktivieren", key="s3on")
        s3_age = st.number_input("Alter bei Start", value=42, key="a3")
        s3_brutto = st.number_input("Brutto p.a. €", value=160000, key="b3")
        s3_fix_share = st.slider("Fix-Anteil %", 0, 100, 70, key="s3") / 100
        s3_growth = st.number_input("Steigerung p.a. %", value=1.0, key="g3") / 100

    st.markdown("---")
    gift_active = st.checkbox("Schenkung/Erbe?")
    if gift_active:
        c4, c5 = st.columns(2)
        gift_age = c4.number_input("Alter bei Schenkung", value=50)
        gift_val = c5.number_input("Betrag €", value=100000)
    else:
        gift_age = 0; gift_val = 0

# ==============================================================================
# 3. WOHNEN (MIETE & KAUF LOGIK)
# ==============================================================================
with tab_house:
    st.subheader("Aktuelle Situation (Miete)")
    st.caption("Diese Miete zahlst du ab heute (bis ans Ende oder bis zum Hauskauf).")
    
    c_rent1, c_rent2, c_rent3 = st.columns(3)
    rent_start = c_rent1.number_input("Kaltmiete Start (Gesamt) €", value=1600)
    rent_incr_mode = c_rent2.radio("Steigerung", ["Index (%)", "Staffel (€)"])
    if rent_incr_mode == "Index (%)":
        rent_incr_val = c_rent3.number_input("Index %", value=2.0) / 100
    else:
        rent_incr_val = c_rent3.number_input("Staffel € (jährl.)", value=30)
        
    st.divider()
    
    house_mode = st.radio("Zukunfts-Strategie", ["Für immer Miete", "Eigenheim Kaufen"], horizontal=True)
    
    buy_age = 0; price_total = 0; ek_total = 0; loan_amount = 0
    interest_rate = 0; sim_rate_total = 0; maintenance = 0
    
    if house_mode == "Eigenheim Kaufen":
        st.markdown("### 🏠 Kauf-Finanzierung")
        k1, k2, k3 = st.columns(3)
        buy_age = k1.number_input("Kaufalter", value=38)
        price_total = k1.number_input("Kaufpreis (inkl. NK) €", value=700000)
        ek_total = k2.number_input("Eigenkapital (Gesamt) €", value=150000)
        loan_amount = price_total - ek_total
        
        k2.metric("Kreditsumme", f"{loan_amount:,.0f} €")
        
        interest_rate = k3.number_input("Sollzins %", value=3.4) / 100
        calc_method = k3.radio("Berechnung", ["Rate fixieren", "Laufzeit fixieren"])
        
        if calc_method == "Rate fixieren":
            sim_rate_total = k3.number_input("Wunschrate (Zins+Tilgung) €", value=2300)
        else:
            target_years = k3.number_input("Laufzeit (Jahre)", value=25)
            q = 1 + interest_rate/12
            n = target_years * 12
            if loan_amount > 0:
                sim_rate_total = loan_amount * (q**n * (q-1)) / (q**n - 1)
            k3.success(f"Notwendige Rate: {sim_rate_total:,.2f} €")
            
        maintenance = k1.number_input("Instandhaltung (Gesamt) €", value=400)
        
    st.divider()
    st.subheader("Nebenkosten (Gesamt-Haushalt)")
    st.caption("Skaliert mit Personenanzahl im Haushalt.")
    nc1, nc2 = st.columns(2)
    nk_base_1 = nc1.number_input("NK Basis (1 Person) €", value=200)
    nk_add_p = nc2.number_input("Zusatz pro weitere Person €", value=75)

# ==============================================================================
# 4. LIFESTYLE & SHOPPING
# ==============================================================================
with tab_life:
    col_share, col_pers = st.columns(2)
    
    with col_share:
        st.markdown("### Geteilte Kosten (Haushalt)")
        st.caption("Dein Anteil: " + str(partner_share*100) + "%")
        cost_groc = st.number_input("Supermarkt/Drogerie €", value=600)
        cost_food = st.number_input("Gastro/Bestellen €", value=200)
        cost_internet = st.number_input("Internet/Strom/TV €", value=170)
        
        st.markdown("#### Urlaube (Gesamt)")
        n_vacations = st.number_input("Anzahl Urlaube p.a.", 1, 5, 3)
        budget_vac_total = 0
        for v in range(n_vacations):
            budget_vac_total += st.number_input(f"Budget Urlaub {v+1} €", value=1500, key=f"vac{v}")
            
    with col_pers:
        st.markdown("### 100% Deine Kosten")
        pers_streaming = st.number_input("Streaming/Abos €", value=30)
        pers_insur = st.number_input("Eigene Vers. (Haft/BU) €", value=80)
        pers_fun = st.number_input("Hobby/Freizeit/Bar €", value=200)
        pers_mobile = st.number_input("Handyvertrag €", value=40)
        
        st.markdown("#### Jährliche Sonderausgaben (Du)")
        cost_clothes = st.number_input("Klamotten (Jahr) €", value=1000)
        cost_gadgets = st.number_input("Gadgets/Tech (Jahr) €", value=1000)
        cost_xmas = st.number_input("Weihnachten/Geschenke (Jahr) €", value=500)
        
        st.markdown("#### Dein Auto")
        car_type = st.selectbox("Typ", ["Leasing", "Kauf (Bar)", "Kein Auto"])
        car_cost_mo = 0; car_tax_yr = 0; car_buy_price = 0; car_cycle = 6
        
        if car_type == "Leasing":
            car_cost_mo = st.number_input("Rate (inkl. Vers) €", value=550)
        elif car_type == "Kauf (Bar)":
            car_buy_price = st.number_input("Kaufpreis (Heute) €", value=35000)
            car_cycle = st.number_input("Neukauf alle X Jahre", value=6)
            car_cost_mo = st.number_input("Rücklage Reparatur €", value=150)
            car_tax_yr = st.number_input("Steuer/Versicherung (Jahr) €", value=800)


# ==============================================================================
# LOGIC ENGINE
# ==============================================================================

def calc_tax(brutto):
    sv = min(brutto * 0.20, 16000) 
    taxable = brutto - sv - 1200
    if taxable < 11600: tax = 0
    elif taxable < 66000: tax = (taxable - 11600) * 0.35
    else: tax = 19000 + (taxable - 66000) * 0.42
    return brutto - sv - tax

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
    
    c_car_mo = car_cost_mo; c_car_tax = car_tax_yr
    c_maint = maintenance
    
    sim_rate = 0 
    
    for m in range(months + 1):
        idx_yr = m // 12
        idx_mo = m % 12
        age = age_start + idx_yr
        year = 2026 + idx_yr
        
        # --- JANUAR UPDATES ---
        if m > 0 and idx_mo == 0:
            f_inf = (1 + r_infla)
            # Inflation
            c_nk_base *= f_inf; c_nk_add *= f_inf
            c_groc *= f_inf; c_food *= f_inf; c_util *= f_inf
            c_vac_total *= f_inf; c_cloth *= f_inf; c_gadget *= f_inf; c_xmas *= f_inf
            c_stream *= f_inf; c_insur *= f_inf; c_fun *= f_inf; c_mob *= f_inf
            c_car_mo *= f_inf; c_car_tax *= f_inf
            c_maint *= f_inf
            
            # Gehalt
            cur_brutto *= (1 + cur_growth)
            
            # Miete (falls noch Miete)
            if not own_house:
                if rent_incr_mode == "Index (%)": cur_rent *= (1 + rent_incr_val)
                else: cur_rent += rent_incr_val
            
            # Hauswert
            if own_house: house_val *= f_inf
            
            # Auto Kauf (Cash)
            if car_type == "Kauf (Bar)" and idx_yr > 0 and idx_yr % int(car_cycle) == 0:
                wealth -= (car_buy_price * (f_inf ** idx_yr))

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
            house_val = price_total
            own_house = True
            cur_rent = 0
            
        if gift_active and age == gift_age and idx_mo == 6:
            wealth += gift_val

        # --- INCOME ---
        netto_jahr = calc_tax(cur_brutto)
        netto_fix_mo = (netto_jahr * cur_fix_share) / 12
        netto_var_yr = netto_jahr * (1 - cur_fix_share)
        
        income = netto_fix_mo
        if idx_mo == 11: income += netto_var_yr
        
        # Kindergeld
        n_kids_act = 0
        if has_kids:
            for k_birth in kids_data:
                if k_birth <= age < (k_birth + 20): n_kids_act += 1
        income += (n_kids_act * k_geld_val)
        
        # --- EXPENSES ---
        persons = (2 if has_partner else 1) + n_kids_act
        nk_curr = c_nk_base + max(0, (persons - 1)) * c_nk_add
        
        # 1. FIXE KOSTEN (Kategorisierung für Analyse)
        # Miete, Kredit, NK, Versicherungen, Internet, Handy, Auto Rate
        cost_fix_total = 0
        
        # Wohnen
        if own_house:
            housing_cost_shared = sim_rate + nk_curr + c_maint + c_util
            # Tilgung
            zins_eur = loan_bal * (interest_rate/12)
            loan_bal -= (sim_rate - zins_eur)
            if loan_bal < 0: loan_bal = 0
        else:
            housing_cost_shared = cur_rent + nk_curr + c_util
        
        my_housing = housing_cost_shared * partner_share
        
        # Persönliche Fixe
        my_fix_pers = c_stream + c_insur + c_mob + c_car_mo
        if idx_mo == 0: my_fix_pers += c_car_tax
        
        total_fix_output = my_housing + my_fix_pers
        
        # 2. VARIABLE KOSTEN
        # Essen, Spaß, Klamotten, Urlaub, Weihnachten
        shared_var = c_groc + c_food
        if idx_mo == 6: shared_var += c_vac_total # Urlaub Juli
        
        my_var_share = shared_var * partner_share
        
        my_var_pers = c_fun
        if idx_mo == 4: my_var_pers += c_cloth # Mai Shopping?
        if idx_mo == 10: my_var_pers += c_gadget # Nov Tech?
        if idx_mo == 11: my_var_pers += c_xmas
        
        total_var_output = my_var_share + my_var_pers
        
        # GESAMT
        total_out = total_fix_output + total_var_output
        
        cf = income - total_out
        wealth *= (1 + r_invest)**(1/12)
        wealth += cf
        
        equity = max(0, house_val - loan_bal) * partner_share
        
        data.append({
            "Alter": age, "Jahr": year, "Monat": idx_mo+1,
            "Netto": round(income),
            "Ausgaben_Fix": round(total_fix_output),
            "Ausgaben_Variabel": round(total_var_output),
            "Ausgaben_Total": round(total_out),
            "Sparrate": round(cf),
            "Vermögen": round(wealth),
            "Immo_Equity": round(equity),
            "Gesamtvermögen": round(wealth + equity),
            "Restschuld": round(loan_bal),
            "Urlaubs_Kosten_Anteil": round((c_vac_total if idx_mo == 6 else 0) * partner_share)
        })
        
    return pd.DataFrame(data)

df = simulate()

# ==============================================================================
# 5. ANALYSE
# ==============================================================================
with tab_res:
    st.subheader("📊 Deine Finanz-Analyse")
    
    last = df.iloc[-1]
    st.metric("Endvermögen (Alter " + str(age_end) + ")", f"{last['Gesamtvermögen']:,.0f} €", f"Depot: {last['Vermögen']:,.0f} €")
    
    st.divider()
    
    # --- NEU: FIX VS VARIABEL HEUTE VS 20 JAHRE ---
    st.markdown("### 🔮 Kosten-Struktur: Heute vs. in 20 Jahren")
    
    # Jahr 1 Daten
    row_now = df[(df['Jahr'] == 2026)].sum(numeric_only=True)
    fix_now = row_now['Ausgaben_Fix']
    var_now = row_now['Ausgaben_Variabel']
    
    # Jahr 20 Daten
    row_fut = df[(df['Jahr'] == 2046)].sum(numeric_only=True)
    fix_fut = row_fut['Ausgaben_Fix']
    var_fut = row_fut['Ausgaben_Variabel']
    
    col_comp1, col_comp2 = st.columns(2)
    
    with col_comp1:
        st.markdown(f"**Jahr 2026 (Gesamt)**")
        st.bar_chart({"Fix": fix_now, "Variabel": var_now}, horizontal=True, color=["#FF4B4B", "#FFA500"])
        st.caption(f"Fixkosten-Quote: {fix_now/(fix_now+var_now)*100:.1f}%")

    with col_comp2:
        st.markdown(f"**Jahr 2046 (Gesamt)**")
        st.bar_chart({"Fix": fix_fut, "Variabel": var_fut}, horizontal=True, color=["#FF4B4B", "#FFA500"])
        st.caption(f"Fixkosten-Quote: {fix_fut/(fix_fut+var_fut)*100:.1f}%")
        
    st.info("Hinweis: Wenn du ein Haus kaufst, bleiben die Fixkosten (Kredit) oft stabil, während variable Kosten (Essen/Urlaub) mit der Inflation steigen. Das senkt deine Fixkostenquote langfristig!")

    st.divider()
    
    # Urlaubs Aggregation
    total_vacation_spend = df["Urlaubs_Kosten_Anteil"].sum()
    st.metric("🌴 Gesamtausgaben für Urlaub (Dein Anteil, aggregiert)", f"{total_vacation_spend:,.0f} €")
    
    st.divider()
    
    st.markdown("### 📌 Meilensteine (5-Jahres-Schritte)")
    milestones = [35, 40, 45, 50, 55, 60, 65, 70]
    mask = (df["Alter"].isin(milestones)) & (df["Monat"] == 1)
    st.dataframe(df.loc[mask, ["Alter", "Gesamtvermögen", "Restschuld", "Ausgaben_Fix", "Ausgaben_Variabel"]].style.format("{:,.0f} €"), use_container_width=True)

    st.download_button("📥 Alle Daten herunterladen (CSV)", df.to_csv(sep=";", decimal=",").encode('utf-8'), "finanzplan_final.csv")
