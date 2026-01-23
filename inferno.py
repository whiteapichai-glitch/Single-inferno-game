import streamlit as st
import random
import graphviz
import pandas as pd

# --- 💅 1. CUSTOM CSS & CONFIG ---
st.set_page_config(layout="wide", page_title="Single's Inferno: The Original", page_icon="🔥")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Prompt', sans-serif; }
    .main { background-color: #0e1117; color: #e0e0e0; }
    .stButton>button { 
        background: linear-gradient(90deg, #ff4b1f 0%, #ff9068 100%); 
        color: white; border: none; border-radius: 8px; height: 3em; width: 100%; font-weight: bold; 
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255, 75, 31, 0.4); }
    .status-tag { padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; display: inline-block; margin-right: 5px; }
    .tag-soulmate { background: #ff006e; color: white; }
    .tag-awkward { background: #3a86ff; color: white; }
    .tag-friend { background: #8338ec; color: white; }
    
    /* Log Style */
    .log-text { text-align: center; font-size: 1.1em; padding-top: 10px; }
    .log-score { color: #ff9068; font-weight: bold; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# --- ⚙️ 2. CONSTANTS & DATA ---
MAX_DAYS = 13
MAX_HEART = 20
DEFAULT_CAST_M = ["บลู", "เจษ", "เจเจ", "วิน", "จุง", "โฟร์ท"]
DEFAULT_CAST_F = ["เจนเย่", "ใบเฟิร์น", "เนเน่", "วี", "แพต", "คาริสา"]
JOBS = ["นายแบบ/นางแบบ", "นักธุรกิจ", "หมอ", "นักแสดง", "เชฟ", "ยูทูบเบอร์", "นักกีฬา", "ศิลปิน"]
TRAITS = ["Hunter (นักล่า)", "Loyal (รักเดียว)", "Socialite (เฟรนด์ลี่)", "Villain (ตัวร้าย)"]
DEF_IMG_M = "https://cdn-icons-png.flaticon.com/512/4128/4128176.png"
DEF_IMG_F = "https://cdn-icons-png.flaticon.com/512/6997/6997662.png"

# --- 📦 3. INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state.step = "SETUP"
    st.session_state.master_pool = []       
    st.session_state.cast = []              
    st.session_state.waiting_list = []      
    st.session_state.weights = {}           
    st.session_state.score_history = []
    st.session_state.day = 1
    st.session_state.logs = []
    st.session_state.paradise_visitors = [] 
    st.session_state.statuses = {}          
    st.session_state.couple_vibe = {}       
    st.session_state.info_revealed = False  
    st.session_state.game_over = False
    st.session_state.finale_phase = None
    st.session_state.final_couples = []

# --- 🧪 4. LOGIC FUNCTIONS ---
def log_event(type, text, p1=None, p2=None):
    entry = {"day": st.session_state.day, "type": type, "txt": text, "p1": p1, "p2": p2}
    st.session_state.logs.append(entry)

def update_rel(a, b, val):
    # ฟังก์ชันนี้คืนค่าคะแนนจริงที่บวกเพิ่ม (Actual Score Added)
    if a not in st.session_state.weights or b not in st.session_state.weights[a]: return 0, "ERROR"
    
    pair_key = tuple(sorted((a, b)))
    
    # 1. Check Vibe (Awkward)
    if st.session_state.couple_vibe.get(pair_key) == "AWKWARD":
        return 0, "BLOCKED" # คะแนนไม่ขึ้น

    # 2. Check Status (Closed/Open)
    status = st.session_state.statuses.get(b, None)
    final_val = val
    
    # Soulmate Buff
    if st.session_state.couple_vibe.get(pair_key) == "SOULMATE" and val > 0:
        final_val += 1 # Bonus

    if status == 'CLOSED':
        final_val = 0 # จีบไม่ติด
        return 0, "CLOSED"
    elif status == 'OPEN' and val > 0:
        final_val += 1 # เปิดใจรับ

    current_score = st.session_state.weights[a][b]
    new_score = max(0, min(current_score + final_val, MAX_HEART))
    st.session_state.weights[a][b] = new_score
    
    return final_val, "SUCCESS"

def get_top_crush(name):
    scores = st.session_state.weights.get(name, {})
    if not scores: return None
    valid_scores = {k: v for k, v in scores.items() if v > 0}
    if valid_scores:
        return max(valid_scores, key=valid_scores.get)
    return None

def ai_choose_target(person, on_island):
    trait = person['trait']
    opps = [x for x in on_island if x['gender'] != person['gender']]
    if not opps: return None

    target = None
    if "Hunter" in trait: 
        hotness = {o['name']: sum(st.session_state.weights[x['name']].get(o['name'], 0) for x in st.session_state.cast) for o in opps}
        target = max(opps, key=lambda x: hotness.get(x['name'], 0))
    elif "Loyal" in trait: 
        crush = get_top_crush(person['name'])
        if crush:
             target = next((o for o in opps if o['name'] == crush), random.choice(opps))
        else: target = random.choice(opps)
    elif "Villain" in trait: 
        prev_visitors = [o for o in opps if o['name'] in st.session_state.paradise_visitors]
        target = random.choice(prev_visitors) if prev_visitors else random.choice(opps)
    else: 
        target = random.choice(opps)
    return target

# --- 🏗️ 5. UI: SETUP PHASE ---
if st.session_state.step == "SETUP":
    st.title("🔥 Single's Inferno: Casting")
    col1, col2 = st.columns(2)
    m_data, f_data = [], []

    with col1:
        st.subheader("♂️ ฝ่ายชาย")
        for i in range(6):
            c1, c2 = st.columns([3, 2])
            name = c1.text_input(f"M{i+1}", DEFAULT_CAST_M[i], key=f"m_{i}")
            uploaded = c2.file_uploader(f"รูป {name}", type=['jpg','png','jpeg'], key=f"mi_{i}")
            img_src = uploaded if uploaded else DEF_IMG_M
            m_data.append({"name": name, "img": img_src, "gender": "M"})
            
    with col2:
        st.subheader("♀️ ฝ่ายหญิง")
        for i in range(6):
            c1, c2 = st.columns([3, 2])
            name = c1.text_input(f"F{i+1}", DEFAULT_CAST_F[i], key=f"f_{i}")
            uploaded = c2.file_uploader(f"รูป {name}", type=['jpg','png','jpeg'], key=f"fi_{i}")
            img_src = uploaded if uploaded else DEF_IMG_F
            f_data.append({"name": name, "img": img_src, "gender": "F"})

    st.divider()
    if st.button("🚀 ยืนยันรายชื่อ & เริ่มรายการ!"):
        full_pool = []
        for p in m_data + f_data:
            p['age'] = random.randint(21, 32)
            p['job'] = random.choice(JOBS)
            p['trait'] = random.choice(TRAITS)
            full_pool.append(p)
        
        st.session_state.master_pool = full_pool
        st.session_state.cast = m_data[:4] + f_data[:4]
        st.session_state.waiting_list = m_data[4:] + f_data[4:]
        
        names = [p['name'] for p in st.session_state.master_pool]
        st.session_state.weights = {n: {target: 0 for target in names if target != n} for n in names}
        
        log_event("System", f"☀️ --- DAY 1 เริ่มต้นขึ้นแล้ว! ---")
        st.session_state.step = "GAME"
        st.rerun()

# --- 🏝️ 6. UI: GAMEPLAY ---
elif not st.session_state.game_over:
    st.title(f"🔥 Inferno Island - DAY {st.session_state.day}")
    
    # Sidebar
    with st.sidebar:
        if st.button("🧹 Reset All"): st.session_state.clear(); st.rerun()
        st.divider()
        st.markdown("### 💘 Heart Status")
        for p in st.session_state.cast:
            tags = ""
            if p['name'] in st.session_state.statuses:
                s = st.session_state.statuses[p['name']]
                tags += f" <span class='status-tag' style='background:#555'>🔒</span>" if s == 'CLOSED' else f" <span class='status-tag' style='background:#2ca02c'>🔓</span>"
            
            for pair_key, vibe in st.session_state.couple_vibe.items():
                if p['name'] in pair_key:
                    partner = pair_key[0] if pair_key[1] == p['name'] else pair_key[1]
                    if vibe == "SOULMATE": tags += f" <span class='status-tag tag-soulmate'>💖{partner}</span>"
                    elif vibe == "AWKWARD": tags += f" <span class='status-tag tag-awkward'>🧊{partner}</span>"

            st.markdown(f"**{p['name']}** {tags}", unsafe_allow_html=True)
            sc = st.session_state.weights[p['name']]
            top = sorted(sc.items(), key=lambda x:x[1], reverse=True)[:1]
            if top and top[0][1] > 0:
                st.caption(f"❤️ {top[0][0]} ({top[0][1]})")
        
        st.divider()
        st.info(f"รอเข้าเกาะ: {len(st.session_state.waiting_list)} คน")

    # --- MAIN DASHBOARD ---
    with st.expander("📊 Relationship Map", expanded=True):
        col_g1, col_g2 = st.columns([3, 1])
        with col_g1:
            dot = graphviz.Digraph(engine='circo'); dot.attr(bgcolor='#0e1117')
            for p in st.session_state.cast:
                penwidth = "3" if p['name'] in st.session_state.statuses else "0"
                border_col = "red" if st.session_state.statuses.get(p['name'])=='CLOSED' else "green"
                if isinstance(p['img'], str): 
                    label = f'<<TABLE BORDER="{penwidth}" COLOR="{border_col}" CELLBORDER="0"><TR><TD FIXEDSIZE="TRUE" WIDTH="50" HEIGHT="50"><IMG SRC="{p["img"]}"/></TD></TR><TR><TD><FONT COLOR="white"><B>{p["name"]}</B></FONT></TD></TR></TABLE>>'
                    dot.node(p['name'], label=label, shape="none")
                else: 
                    icon = "🤵" if p['gender'] == "M" else "💃"
                    dot.node(p['name'], label=f"{icon} {p['name']}", color="white", style="filled")
            for p in st.session_state.cast:
                sc = st.session_state.weights[p['name']]
                if any(v > 0 for v in sc.values()):
                    t = max(sc, key=sc.get); v = sc[t]
                    if v > 0: dot.edge(p['name'], t, penwidth=str(min(v, 4)), color="#ff4b1f")
            st.graphviz_chart(dot)
        with col_g2:
            st.write("#### 🕵️ Hidden Info")
            if st.session_state.info_revealed:
                for p in st.session_state.cast:
                    st.caption(f"**{p['name']}**: {p['age']} ปี, {p['job']}")
            else:
                st.warning("ความลับยังไม่เปิดเผย")

    # PRODUCER CONTROLS (คงเดิม)
    st.divider()
    st.markdown("### 🎬 Producer Actions")
    tab1, tab2, tab3 = st.tabs(["➕ เพิ่มสมาชิก", "🔮 อีเวนต์พิเศษ", "🌪️ ข่าวลือ"])
    with tab1:
        if st.session_state.waiting_list:
            st.write("### 🆕 เปิดตัวสมาชิกใหม่")
            c1, c2 = st.columns(2)
            
            # 1. เลือกคนเข้าเกาะ
            to_add_name = c1.selectbox("เลือกคนเข้า:", [p['name'] for p in st.session_state.waiting_list])
            
            # 2. ออปชันเสริม: สิทธิ์พิเศษพาไปสวรรค์
            use_privilege = c2.checkbox("⭐ ให้สิทธิ์พาไปสวรรค์ทันที!")
            partner_choice = None
            
            if use_privilege:
                # เลือกคู่เดตจากคนที่มีอยู่ในเกาะตอนนี้
                current_cast_names = [c['name'] for c in st.session_state.cast]
                partner_choice = c2.selectbox("เลือกคนที่จะพาไป:", current_cast_names)

            # 3. ปุ่มกดส่งเข้าเกาะ
            if st.button("🚀 ส่งเข้าเกาะ"):
                # ย้ายคนจาก Waiting List -> Cast
                p_obj = next(p for p in st.session_state.waiting_list if p['name'] == to_add_name)
                st.session_state.waiting_list.remove(p_obj)
                st.session_state.cast.append(p_obj) 
                
                main_txt = f"📢 NEWCOMER! {to_add_name} มาแล้ว!"
                
                # ถ้าใช้สิทธิ์พิเศษ
                if use_privilege and partner_choice:
                    st.session_state.paradise_visitors.extend([to_add_name, partner_choice])
                    
                    # สุ่มคะแนนเดตแรก (เด็กใหม่มักได้บัฟคะแนนดีหน่อย)
                    s1 = random.randint(3, 5) # เด็กใหม่ให้คะแนน
                    s2 = random.randint(2, 4) # คู่เดตให้คะแนนกลับ
                    
                    real_s1, _ = update_rel(to_add_name, partner_choice, s1)
                    real_s2, _ = update_rel(partner_choice, to_add_name, s2)
                    
                    # ตั้งค่า Vibe (ส่วนใหญ่เดตแรกเด็กใหม่มักจะ Good หรือ Soulmate)
                    st.session_state.couple_vibe[tuple(sorted((to_add_name, partner_choice)))] = "GOOD"
                    
                    main_txt += f" และใช้สิทธิ์พา {partner_choice} ไปสวรรค์ทันที! <br><span class='log-score'>({to_add_name} +{real_s1} | {partner_choice} +{real_s2})</span>"
                    
                    # ระบบหึง (Jealousy Trigger)
                    for p in st.session_state.cast:
                        if p['name'] not in [to_add_name, partner_choice]:
                            my_crush = get_top_crush(p['name'])
                            if my_crush == partner_choice:
                                st.session_state.statuses[p['name']] = "CLOSED"
                                log_event("System", f"💔 {p['name']} ช็อคที่ {partner_choice} โดนปาดหน้าเค้ก! -> ปิดใจ")

                log_event("System", main_txt, p1=p_obj)
                st.rerun()
        else:
            st.success("สมาชิกครบแล้ว!")
    with tab2:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if not st.session_state.info_revealed:
                if st.button("🎭 คืนเปิดเผยข้อมูล"):
                    st.session_state.info_revealed = True
                    log_event("System", "🎭 คืนเปิดเผยข้อมูล! ทุกคนได้รู้อายุและอาชีพกันแล้ว...")
                    txt_list = []
                    for p in st.session_state.cast:
                        crush = get_top_crush(p['name'])
                        if crush:
                            target = next(x for x in st.session_state.cast if x['name'] == crush)
                            change, _ = update_rel(p['name'], target['name'], 2 if p['job'] == target['job'] else 0)
                            if change > 0: txt_list.append(f"{p['name']} ปลื้ม {target['name']} (+{change})")
                    st.rerun()
        with col_s2:
             if st.button("🔥 สลับคู่"):
                 log_event("System", "🌪️ กฎพิเศษ: ห้ามคุยกับคู่เดิม! ต้องเปลี่ยนเป้าหมาย")
                 st.rerun()
    with tab3:
        if st.button("🗣️ ปล่อยข่าวลือ"):
            victim = random.choice(st.session_state.cast)
            rumor_type = random.choice(["BAD", "GOOD", "LOVE"])
            if rumor_type == "BAD":
                txt = f"ลือว่า {victim['name']} พูดจาลับหลังคนอื่นไม่ดี..."
                for p in st.session_state.cast: 
                    if p != victim: update_rel(p['name'], victim['name'], -2)
            elif rumor_type == "GOOD":
                txt = f"ลือว่า {victim['name']} ตื่นมาทำอาหารให้ทุกคนกิน น่ารักมาก!"
                for p in st.session_state.cast: 
                    if p != victim: update_rel(p['name'], victim['name'], 2)
            else: 
                target = random.choice([c for c in st.session_state.cast if c != victim])
                txt = f"เห็น {victim['name']} แอบมอง {target['name']} ตาเป็นมัน!"
                for p in st.session_state.cast:
                    crush = get_top_crush(p['name'])
                    if crush == target['name'] and p['name'] != victim['name']:
                        st.session_state.statuses[p['name']] = "CLOSED"
                        log_event("System", f"😡 {p['name']} ได้ยินข่าวลือแล้วหึง! ปิดใจทันที")
            log_event("Rumor", f"🤫 Pssst... {txt}", p1=victim)
            st.rerun()

    # --- 🕹️ ACTIVITIES (ระบบใหม่: คะแนน 2 ฝั่ง) ---
    st.divider()
    st.markdown("### 🕹️ Activities")
    busy_people = st.session_state.paradise_visitors
    on_island = [c for c in st.session_state.cast if c['name'] not in busy_people]
    ac1, ac2, ac3 = st.columns(3)
    
    with ac1:
        st.markdown("#### 🏆 1. แข่งชิง Paradise")
        if len(on_island) >= 2 and st.button("🏁 เริ่มการแข่งขัน"):
            gender = random.choice(['M', 'F'])
            comps = [c for c in on_island if c['gender'] == gender]
            if len(comps) >= 2:
                random.shuffle(comps)
                winner, runner_up = comps[0], comps[1]
                game_desc = random.choice(["วิ่งแข่งริมหาด", "มวยปล้ำในโคลน", "ดึงธงชิงไหวพริบ"])
                desc = f"แข่ง {game_desc}: {winner['name']} ชนะ {runner_up['name']} หวุดหวิด! 🥇"
                log_event("Game", desc, p1=winner, p2=runner_up)
                
                opps = [x for x in on_island if x['gender'] != winner['gender']]
                if opps:
                    target = ai_choose_target(winner, on_island) or random.choice(opps)
                    st.session_state.paradise_visitors.extend([winner['name'], target['name']])
                    
                    # สุ่มคะแนน 2 ฝั่ง (ฐานเยอะ เพราะไปสวรรค์)
                    s1_base = random.randint(3, 5) # ผู้ชนะ รู้สึก
                    s2_base = random.randint(2, 5) # ผู้ถูกเลือก รู้สึก
                    
                    real_s1, _ = update_rel(winner['name'], target['name'], s1_base)
                    real_s2, _ = update_rel(target['name'], winner['name'], s2_base)
                    
                    # Vibe Effect
                    roll = random.randint(1, 100)
                    if roll <= 15: 
                        st.session_state.couple_vibe[tuple(sorted((winner['name'], target['name'])))] = "AWKWARD"
                        vibe_txt = "แต่บรรยากาศอึดอัด (Dead Air)"
                    elif roll >= 85:
                        st.session_state.couple_vibe[tuple(sorted((winner['name'], target['name'])))] = "SOULMATE"
                        vibe_txt = "สปาร์คแรงมาก! (Soulmate)"
                    else: vibe_txt = "บรรยากาศดีโรแมนติก"

                    log_event("Paradise", 
                              f"บินไปเกาะสวรรค์ {vibe_txt}<br><span class='log-score'>({winner['name']} +{real_s1} | {target['name']} +{real_s2})</span>", 
                              p1=winner, p2=target)
                    
                    for p in on_island:
                        my_crush = get_top_crush(p['name'])
                        if my_crush == target['name']:
                            st.session_state.statuses[p['name']] = "CLOSED"
                            log_event("System", f"💔 {p['name']} เห็นคนที่ชอบไปกับคนอื่น -> ปิดใจ", p1=p)
                    st.rerun()

    with ac2:
        st.markdown("#### 🌴 2. แข่งชิงเดตในเกาะ")
        if len(on_island) >= 2 and st.button("☕ แข่งชิงมื้ออาหาร"):
            gender = random.choice(['M', 'F'])
            comps = [c for c in on_island if c['gender'] == gender]
            if comps:
                winner = random.choice(comps)
                target = ai_choose_target(winner, on_island)
                if target:
                    # สุ่มคะแนน 2 ฝั่ง (ฐานปานกลาง)
                    s1_base = random.randint(1, 3)
                    s2_base = random.randint(0, 2)
                    
                    real_s1, _ = update_rel(winner['name'], target['name'], s1_base)
                    real_s2, _ = update_rel(target['name'], winner['name'], s2_base)
                    
                    log_event("Date", 
                              f"ชนะเกม! ชวนเดตมื้อเที่ยง<br><span class='log-score'>({winner['name']} +{real_s1} | {target['name']} +{real_s2})</span>", 
                              p1=winner, p2=target)
                    st.rerun()

    with ac3:
        st.markdown("#### 👣 3. Free Time")
        if st.button("ปล่อยเดินเกมอิสระ"):
            log_event("System", "👣 --- Free Time: จับคู่นั่งคุย ---")
            for p in on_island:
                target = ai_choose_target(p, on_island)
                if target:
                    # สุ่มคะแนน 2 ฝั่ง (ฐานน้อย-ปานกลาง)
                    s1_base = random.randint(0, 2) # คนเดินไปหา
                    s2_base = random.randint(0, 1) # คนถูกหา
                    
                    real_s1, res1 = update_rel(p['name'], target['name'], s1_base)
                    real_s2, res2 = update_rel(target['name'], p['name'], s2_base)
                    
                    trait_txt = f"({p['trait']})"
                    
                    if res1 == "BLOCKED" or res1 == "CLOSED":
                        log_event("Fail", f"เดินไปหาแต่บรรยากาศไม่เป็นใจ (0 คะแนน)", p1=p, p2=target)
                    else:
                        log_event("Talk", 
                                  f"{trait_txt} เดินไปชวนนั่งคุยริมหาด<br><span class='log-score'>({p['name']} +{real_s1} | {target['name']} +{real_s2})</span>", 
                                  p1=p, p2=target)
            st.rerun()

    # --- END DAY ---
    st.divider()
    if st.button("🌙 จบวัน (End Day)", type="primary"):
        snapshot = {sender: targets.copy() for sender, targets in st.session_state.weights.items()}
        st.session_state.score_history.append({"day": st.session_state.day, "scores": snapshot})
        st.session_state.day += 1
        st.session_state.paradise_visitors = []
        st.session_state.statuses = {} 
        if st.session_state.day > MAX_DAYS:
            st.session_state.game_over = True
            st.session_state.finale_phase = "START"
        log_event("System", f"💤 จบวัน! แยกย้ายกันนอน... เตรียมเข้าสู่ DAY {st.session_state.day}")
        st.rerun()

    # --- LOGS DISPLAY ---
    st.subheader("📝 บันทึกเหตุการณ์ (Visual Logs)")
    for log in reversed(st.session_state.logs[-15:]):
        if log['type'] == "System":
            st.info(f"☀️ DAY {log['day']}: {log['txt']}")
        elif log.get('p1') and log.get('p2'):
            with st.container():
                c1, c2, c3 = st.columns([1, 4, 1])
                c1.image(log['p1']['img'], width=80) 
                with c2:
                    st.markdown(f"""
                    <div class="log-text">
                        <b>{log['p1']['name']}</b> ➔ <b>{log['p2']['name']}</b><br>
                        {log['txt']}
                    </div>
                    """, unsafe_allow_html=True)
                    st.divider()
                c3.image(log['p2']['img'], width=80) 
        elif log.get('p1'):
            with st.container():
                c1, c2 = st.columns([1, 5])
                c1.image(log['p1']['img'], width=80)
                c2.warning(f"**{log['p1']['name']}**: {log['txt']}")
                st.divider()

# --- 💖 7. FINALE ---
else:
    st.title("💖 THE FINALE")
    if st.session_state.finale_phase == "START":
        if st.button("เริ่มพิธีเลือกคู่"):
            women = [p for p in st.session_state.cast if p['gender'] == 'F']
            random.shuffle(women)
            st.session_state.female_order = women
            st.session_state.current_f_idx = 0
            st.session_state.finale_phase = "TURN"
            st.rerun()
    elif st.session_state.finale_phase == "TURN":
        if st.session_state.current_f_idx < len(st.session_state.female_order):
            curr_w = st.session_state.female_order[st.session_state.current_f_idx]
            c1, c2 = st.columns([1, 3])
            c1.image(curr_w['img'], width=200)
            with c2:
                st.markdown(f"## 👩 {curr_w['name']} เดินออกมา")
                suitors = []
                for m in st.session_state.cast:
                    if m['gender'] == 'M':
                        score = st.session_state.weights[m['name']].get(curr_w['name'], 0)
                        if get_top_crush(m['name']) == curr_w['name'] and score > 5:
                            suitors.append(m)
                if suitors:
                    cols = st.columns(len(suitors))
                    for i, s in enumerate(suitors):
                        cols[i].image(s['img'], width=100); cols[i].caption(s['name'])
                    st.divider()
                    best_m = max(suitors, key=lambda x: st.session_state.weights[curr_w['name']].get(x['name'], 0))
                    w_score = st.session_state.weights[curr_w['name']].get(best_m['name'], 0)
                    if w_score >= 15:
                        st.balloons(); st.success(f"💍 **MARRIED!** เลือก {best_m['name']} (Score: {w_score})")
                        st.session_state.final_couples.append((best_m, curr_w, "MARRIAGE"))
                    elif w_score >= 5:
                        st.success(f"❤️ **COUPLE!** เลือก {best_m['name']} (Score: {w_score})")
                        st.session_state.final_couples.append((best_m, curr_w, "COUPLE"))
                    else:
                        st.warning(f"🤝 **FRIENDZONE** เลือก {best_m['name']} แต่คะแนนไม่ถึง")
                else:
                    st.error("💨 ไม่มีใครก้าวออกมาหาเธอ...")
            if st.button("คนต่อไป >>"): st.session_state.current_f_idx += 1; st.rerun()
        else:
            st.session_state.finale_phase = "RESULTS"; st.rerun()
    elif st.session_state.finale_phase == "RESULTS":
        st.header("📸 บทสรุปคู่รัก")
        for m, w, status in st.session_state.final_couples:
            st.success(f"[{status}] {m['name']} ❤️ {w['name']}")
            c1, c2, c3 = st.columns([1,1,3])
            c1.image(m['img'], width=100); c2.image(w['img'], width=100)
            with c3:
                data = [{"Day": h['day'], m['name']: h['scores'][m['name']][w['name']], w['name']: h['scores'][w['name']][m['name']]} for h in st.session_state.score_history]
                st.line_chart(pd.DataFrame(data).set_index("Day"))
        if st.button("🔄 New Game"): st.session_state.clear(); st.rerun()


