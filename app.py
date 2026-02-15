import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Finanzplanung Pro", page_icon="📊", layout="wide")

# CSS HACK: Padding oben reduzieren für Dashboard-Look
st.markdown(" <style> div.block-container{padding-top:1rem;} </style> ", unsafe_allow_html=True)

st.title("📊 Financial Projection & Cashflow Engine")

# ==============================================================================
# INPUT SECTION (TABS STATT SIDEBAR)
# ==============================================================================

# Wir gruppieren die Eingaben logisch in 4 Haupt-Tabs
tab_set, tab_job, tab_home, tab_life = st.tabs([
    "⚙️ Setup & Szenarien", 
    "💼 Karriere & Einkommen", 
    "🏠 Wohnen & Immobilien", 
    "🛒 Lifestyle, Auto & Familie"
])

# --- TAB 1: SETUP ---
with tab_set:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Profil")
        age_now = st.number_input("Aktuelles Alter", 20, 65, 31)
        age_end = st.number_input("Ziel Alter (Rente)", 35, 90, 67)
        capital = st.number_input("Startkapital (Depot) €", value=50000)
    
    with c2:
        st.subheader("Markt-Szenario")
        scenario = st.selectbox("Marktphase", ["Basis (5% / 2%)", "Bullish (7% / 1.5%)", "Bearish (3% / 4%)"])
        if "Basis" in scenario: r_inv = 0.05; r_inf = 0.02
        elif "Bullish" in scenario: r_inv = 0.07; r_inf = 0.015
        else: r_inv = 0.03; r_inf = 0.04
        
        # Manuelle Overrides möglich machen, aber kompakt
        col_sub1, col_sub2 = st.columns(2)
        invest_return = col_sub1.number_input("Ø Rendite %", value=r_inv*100, step=0.1)/100
        inflation = col_sub2.number_input("Ø Inflation %", value=r_inf*100, step=0.1)/100
    
    with c3:
        st.subheader("Haushalt & Split")
        split_share = st.slider("Mein Kostenanteil (%)", 0, 100, 65, help="Wieviel % der gemeinsamen Kosten (Miete, Essen) zahlst DU?") / 100
        has_partner = st.checkbox("Partner im Haushalt?", value=True)

# --- TAB 2: KARRIERE ---
with tab_job:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Aktuelle Situation")
        salary_brutto = st.number_input("Jahresbrutto (Aktuell) €", value=100000, step=1000)
        salary_var_pct = st.slider("Variabler Anteil (Bonus) %", 0, 100, 20)/100
        salary_growth = st.number_input("Gehaltssteigerung p.a. %", value=2.0)/100
        
        bonus_save_rate = st.slider("Bonus Sparquote %", 0, 100, 50, help="Wieviel vom Netto-Bonus wird gespart?")/100

    with c2:
        st.markdown("##### Karriere-Sprung (Beförderung)")
        promo_active = st.checkbox("Beförderung simulieren?")
        promo_age, promo_brutto = 0, 0
        if promo_active:
            sc1, sc2 = st.columns(2)
            promo_age = sc1.number_input("Alter bei Sprung", value=36)
            promo_brutto = sc2.number_input("Zielgehalt Brutto €", value=140000)

# --- TAB 3: WOHNEN ---
with tab_home:
    mode_housing = st.radio("Wohnstrategie", ["Miete", "Eigenheim Kauf"], horizontal=True)
    
    c1, c2, c3 = st.columns(3)
    
    # Init variables
    rent_cold, rent_incr_type, rent_incr_val = 0, "Index", 0
    buy_age, house_price, down_payment, interest, amortization, maintenance = 0,0,0,0,0,0
    loan_calc_mode = "Annuität"
    
    # Fixkosten Wohnen (immer da)
    with c1:
        st.markdown("##### Nebenkosten (Gesamt)")
        nk_total = st.number_input("Warm/Strom/Internet (Total) €", value=450)
    
    if mode_housing == "Miete":
        with c2:
            st.markdown("##### Miet-Details")
            rent_cold = st.number_input("Kaltmiete (Total) €", value=1600)
        with c3:
            st.markdown("##### Steigerung")
            rent_incr_type = st.selectbox("Art der Erhöhung", ["Index (%)", "Staffel (€)"])
            if rent_incr_type == "Index (%)":
                rent_incr_val = st.number_input("Steigerung %", value=2.0)/100
            else:
                rent_incr_val = st.number_input("Erhöhung € (pauschal)", value=30)
    else:
        with c2:
            st.markdown("##### Kauf-Parameter")
            buy_age = st.number_input("Kaufalter", value=35)
            house_price = st.number_input("Kaufpreis (All-In) €", value=600000)
            down_pay_total = st.number_input("Eigenkapital (Total) €", value=120000)
            maintenance = st.number_input("Instandhaltung (mtl.) €", value=400)
        
        with c3:
            st.markdown("##### Finanzierung")
            interest = st.number_input("Sollzins %", value=3.5)/100
            
            calc_target = st.radio("Zielgröße", ["Rate vorgeben", "Laufzeit vorgeben"])
            loan_amount = house_price - down_pay_total
            
            sim_rate_total = 0
            if calc_target == "Rate vorgeben":
                sim_rate_total = st.number_input("Wunschrate (Zins+Tilgung) €", value=2300)
            else:
                target_years = st.number_input("Soll-Laufzeit (Jahre)", value=25)
                # Annuitätenformel
                q = 1 + interest/12
                n = target_years * 12
                if loan_amount > 0:
                    sim_rate_total = loan_amount * (q**n * (q-1))/(q**n - 1)
                st.info(f"Notwendige Rate: **{sim_rate_total:,.2f} €**")

# --- TAB 4: LIFESTYLE ---
with tab_life:
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown("##### 🛒 Geteilt (Haushalt)")
        st.caption("Essen, Drogerie, Gemeinsames")
        cost_shared_var = st.number_input("Lebenshaltung Total €", value=800)
        cost_shared_fun = st.number_input("Gemeinsam Freizeit €", value=200)
    
    with c2:
        st.markdown("##### 🕺 Privat (Nur Du)")
        st.caption("Handy, Hobby, Rauchen")
        cost_pers_fix = st.number_input("Abos & Handy €", value=60)
        cost_pers_fun = st.number_input("Spaß / Hobby / Laster €", value=300)
        cost_pers_gift = st.number_input("Geschenke €", value=100)
        
    with c3:
        st.markdown("##### ✈️ Sonderausgaben (Jahr)")
        vacation_budget = st.number_input("Urlaubsbudget (Total) €", value=4000)
        xmas_budget = st.number_input("Weihnachten (Privat) €", value=500)
        
    with c4:
        st.markdown("##### 🚗 Auto & Familie")
        car_mode = st.selectbox("Auto", ["Leasing", "Kauf", "Kein Auto"])
        car_cost, car_invest, car_cycle = 0,0,0
        if car_mode == "Leasing":
            car_cost = st.number_input("Rate + Vers. €", value=500)
        elif car_mode == "Kauf":
            car_invest = st.number_input("Kaufpreis €", value=35000)
            car_cycle = st.number_input("Alle X Jahre", value=8)
            car_cost = st.number_input("Reparatur/Vers. mtl €", value=200)
            
        has_kids = st.checkbox("Kinderplanung?")
        kids_n, kids_age, kids_cost, k_geld = 0,0,0,0
        if has_kids:
            kids_n = st.number_input("Anzahl", 1, 4, 2)
            kids_age = st.number_input("Alter bei 1. Kind", value=33)
            kids_cost = st.number_input("Kosten/Kind €", value=500)
            k_geld = 250

# ==============================================================================
# LOGIC ENGINE
# ==============================================================================

def calc_tax_simplified(brutto):
    # Sehr einfache DE Steuer-Logik für Simulation
    # SV ca 20%, Steuer progressiv
    sv = min(brutto * 0.2, 16000) # BBG Cap Deckelung
    taxable = brutto - sv - 1200 # WK
    if taxable < 11600: tax = 0
    elif taxable < 66000: tax = (taxable - 11600) * 0.35
    else: tax = 19000 + (taxable - 66000) * 0.42
    return max(0, brutto - sv - tax)

def run_simulation():
    months = (age_end - age_now) * 12
    data = []
    
    # State Vars
    wealth = capital
    loan_bal = 0
    house_val = 0
    own_house = False
    
    # Current pointers
    cur_brutto = salary_brutto
    cur_rent = rent_cold
    cur_nk = nk_total
    
    cur_shared_living = cost_shared_var + cost_shared_fun
    cur_pers_living = cost_pers_fix + cost_pers_fun + cost_pers_gift
    
    cur_car_mtl = car_cost
    cur_vacation = vacation_budget
    cur_xmas = xmas_budget
    cur_kids_c = kids_cost
    
    sim_rate = 0 # Für Hypothek
    
    for m in range(months + 1):
        idx_yr = m // 12
        idx_mo = m % 12
        age = age_now + idx_yr
        year = 2026 + idx_yr
        
        # --- A. JÄHRLICHE ANPASSUNG (Inflation) ---
        if m > 0 and idx_mo == 0:
            f_inf = (1 + inflation)
            cur_nk *= f_inf
            cur_shared_living *= f_inf
            cur_pers_living *= f_inf
            cur_car_mtl *= f_inf
            cur_vacation *= f_inf
            cur_xmas *= f_inf
            cur_kids_c *= f_inf
            
            cur_brutto *= (1 + salary_growth)
            
            if own_house:
                house_val *= f_inf
            elif mode_housing == "Miete":
                if rent_incr_type == "Index (%)": cur_rent *= (1 + rent_incr_val)
                else: cur_rent += rent_incr_val
            
            # Auto Kauf Event (Cash)
            if car_mode == "Kauf" and idx_yr > 0 and idx_yr % car_cycle == 0:
                price_adj = car_invest * (f_inf ** idx_yr)
                wealth -= price_adj

        # --- B. EVENTS ---
        if promo_active and age == promo_age and idx_mo == 0:
            cur_brutto = promo_brutto
            
        if mode_housing == "Eigenheim Kauf" and age == buy_age and idx_mo == 0 and not own_house:
            # Kauf findet statt
            # Wir nehmen an, DU zahlst deinen Share am EK oder alles? 
            # Hier: Split Share vom EK wird vom Vermögen abgezogen
            ek_invest_mine = down_pay_total * split_share
            wealth -= ek_invest_mine
            
            loan_bal = loan_amount
            sim_rate = sim_rate_total
            house_val = house_price
            own_house = True
            cur_rent = 0 
            
        # --- C. INCOME ---
        netto_year = calc_tax_simplified(cur_brutto)
        netto_base = (netto_year * (1 - salary_var_pct)) / 12
        
        bonus_payout = 0
        if idx_mo == 11: # Dezember Bonus
            bonus_full = netto_year * salary_var_pct
            # Bonus Konsum abziehen (Wir addieren nur den Sparanteil zum Wealth)
            # ODER: Wir addieren alles zum Income und ziehen den Konsum bei Ausgaben ab
            # User Logik: Split Bonus Saved.
            # Einkommen = Fix + Bonus. Ausgabe = Bonus * (1-SaveRate)
            bonus_payout = bonus_full
        
        income_mo = netto_base + bonus_payout
        
        # Kindergeld
        n_kids_active = 0
        if has_kids and age >= kids_age and age < (kids_age + 20):
            n_kids_active = kids_n
            income_mo += (n_kids_active * k_geld)

        # --- D. AUSGABEN (SPLIT LOGIK) ---
        
        # 1. Wohnen (Total)
        cost_housing_total = cur_rent + cur_nk
        if own_house:
            cost_housing_total = sim_rate + cur_nk + maintenance # maintenance steigt nicht im Loop, evtl fixen? lassen wir flat.
            # Tilgung
            interest_eur = loan_bal * (interest/12)
            tilgung_eur = sim_rate - interest_eur
            loan_bal -= tilgung_eur
            if loan_bal < 0: loan_bal = 0
            
        # 2. Variable Shared (Total)
        # Urlaub im Juli (Monat 6)
        cost_shared_mo = cur_shared_living
        if idx_mo == 6: cost_shared_mo += cur_vacation
        
        # DEIN ANTEIL (SPLIT)
        my_housing = cost_housing_total * split_share
        my_shared_living = cost_shared_mo * split_share
        
        # 3. Persönlich (100% Du)
        my_personal = cur_pers_living + cur_car_mtl
        if idx_mo == 11: my_personal += cur_xmas
        
        # Kinder (Split?) -> Annahme: Kinderkosten werden geteilt
        cost_kids_total = n_kids_active * cur_kids_c
        my_kids_cost = cost_kids_total * split_share
        
        # Bonus Konsum (Dez)
        if idx_mo == 11 and bonus_payout > 0:
            my_personal += (bonus_payout * (1 - bonus_save_rate))
            
        total_expenses = my_housing + my_shared_living + my_personal + my_kids_cost
        
        # --- E. CASHFLOW & WEALTH ---
        cf = income_mo - total_expenses
        
        wealth *= (1 + invest_return)**(1/12)
        wealth += cf
        
        # Net Worth Share (Haus Equity)
        equity = max(0, house_val - loan_bal) * split_share
        
        data.append({
            "Alter": age, "Jahr": year, "Monat": idx_mo+1,
            "Netto": round(income_mo),
            "Ausgaben": round(total_expenses),
            "Cashflow": round(cf),
            "Vermögen": round(wealth),
            "Immo_Equity": round(equity),
            "Total_Net_Worth": round(wealth + equity),
            "Schulden_Total": round(loan_bal),
            # Details für Analyse
            "Kosten_Wohnen": my_housing,
            "Kosten_Leben": my_shared_living + my_personal,
            "Kosten_Kinder": my_kids_cost
        })
        
    return pd.DataFrame(data)

df = run_simulation()

# ==============================================================================
# OUTPUT / DASHBOARD
# ==============================================================================
st.divider()

# --- KPIs ---
last = df.iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Endvermögen (Dein Anteil)", f"{last['Total_Net_Worth']:,.0f} €", delta="Liquid + Immo")
c2.metric("Liquides Depot", f"{last['Vermögen']:,.0f} €")
c3.metric("Immobilien Equity (Netto)", f"{last['Immo_Equity']:,.0f} €")
if last['Schulden_Total'] > 1000:
    c4.metric("Restschuld Haus (Gesamt)", f"{last['Schulden_Total']:,.0f} €", "⚠️ Noch offen")
else:
    c4.metric("Haus Status", "Schuldenfrei ✅")

# --- CHARTS AREA ---
tab_ch1, tab_ch2, tab_data = st.tabs(["📈 Analyse & Charts", "🍩 Ausgaben Struktur", "📋 Rohdaten"])

with tab_ch1:
    col_g1, col_g2 = st.columns([2,1])
    
    with col_g1:
        st.subheader("Vermögensentwicklung")
        fig_nw = go.Figure()
        fig_nw.add_trace(go.Scatter(x=df["Alter"], y=df["Vermögen"], name="Liquide (Depot)", stackgroup='one', line=dict(width=0)))
        if mode_housing == "Eigenheim Kauf":
            fig_nw.add_trace(go.Scatter(x=df["Alter"], y=df["Immo_Equity"], name="Immo Equity", stackgroup='one', line=dict(width=0)))
        fig_nw.update_layout(hovermode="x unified", margin=dict(l=0,r=0,t=0,b=0), height=400)
        st.plotly_chart(fig_nw, use_container_width=True)
        
    with col_g2:
        st.subheader("Cashflow (Jährlich)")
        df_yr = df.groupby("Alter").sum(numeric_only=True).reset_index()
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(x=df_yr["Alter"], y=df_yr["Netto"], name="Einnahmen", marker_color="#4CAF50"))
        fig_cf.add_trace(go.Bar(x=df_yr["Alter"], y=df_yr["Ausgaben"], name="Ausgaben", marker_color="#F44336"))
        fig_cf.update_layout(barmode='overlay', margin=dict(l=0,r=0,t=0,b=0), height=400, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_cf, use_container_width=True)

with tab_ch2:
    st.subheader("Wofür gibst du dein Geld aus?")
    st.caption("Durchschnittliche Verteilung über die gesamte Laufzeit (Dein Anteil)")
    
    # Summen über alles
    avg_housing = df["Kosten_Wohnen"].mean()
    avg_living = df["Kosten_Leben"].mean()
    avg_kids = df["Kosten_Kinder"].mean()
    avg_save = df["Cashflow"].mean()
    
    labels = ["Wohnen", "Leben/Auto/Spaß", "Kinder", "Sparrate"]
    values = [avg_housing, avg_living, avg_kids, avg_save]
    
    c_pie1, c_pie2 = st.columns(2)
    with c_pie1:
        fig_pie = px.pie(names=labels, values=values, hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_pie, use_container_width=True)
    with c_pie2:
        st.markdown(f"""
        **Analyse:**
        * Durchschnittliche Sparrate: **{avg_save:,.0f} € / Monat**
        * Wohnkostenquote: **{(avg_housing/(avg_housing+avg_living+avg_kids+avg_save))*100:.1f}%**
        """)

with tab_data:
    st.dataframe(df, use_container_width=True)
    st.download_button("CSV Exportieren", df.to_csv(sep=";", decimal=",").encode('utf-8'), "finanzplan.csv")
