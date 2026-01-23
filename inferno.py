import streamlit as st
import random
import graphviz
import pandas as pd
import time

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
    .stExpander { border: 1px solid #333; border-radius: 10px; background-color: #1f1f1f; }
    h1, h2, h3 { background: -webkit-linear-gradient(#ff4b1f, #ff9068); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .status-tag { padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; display: inline-block; margin-right: 5px; }
    .tag-soulmate { background: #ff006e; color: white; }
    .tag-awkward { background: #3a86ff; color: white; }
    .tag-friend { background: #8338ec; color: white; }
    .log-box { background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 4px solid #ff4b1f; margin-bottom: 10px; }
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
    st.session_state.master_pool = []       # 12 คน
    st.session_state.cast = []              # คนในเกาะปัจจุบัน
    st.session_state.waiting_list = []      # คนรอเข้า
    st.session_state.weights = {}           # Scores
    st.session_state.score_history = []
    st.session_state.day = 1
    st.session_state.logs = []
    st.session_state.paradise_visitors = [] # คนไปสวรรค์ (ห้ามยุ่ง)
    st.session_state.statuses = {}          # CLOSED/OPEN
    st.session_state.couple_vibe = {}       # ผลลัพธ์ Paradise (Soulmate/Awkward)
    st.session_state.info_revealed = False  # เปิดเผยอาชีพยัง
    st.session_state.game_over = False
    st.session_state.finale_phase = None
    st.session_state.final_couples = []

# --- 🧪 4. LOGIC FUNCTIONS ---
def log_event(type, text, p1=None, p2=None):
    entry = {"day": st.session_state.day, "type": type, "txt": text, "p1": p1, "p2": p2}
    st.session_state.logs.append(entry)

def update_rel(a, b, val, reason=""):
    if a not in st.session_state.weights or b not in st.session_state.weights[a]: return "ERROR"
    
    # 1. เช็ค Vibe Check (Awkward)
    pair_key = tuple(sorted((a, b)))
    if st.session_state.couple_vibe.get(pair_key) == "AWKWARD":
        return "BLOCKED_BY_AWKWARD" # คะแนนไม่ขึ้น 1 วัน

    # 2. เช็ค Status (Closed/Open)
    status = st.session_state.statuses.get(b, None)
    final_val = val
    
    # ถ้าคู่เป็น Soulmate คะแนนขึ้นไว x2
    if st.session_state.couple_vibe.get(pair_key) == "SOULMATE" and val > 0:
        final_val *= 2

    if status == 'CLOSED':
        final_val = 0 # จีบไม่ติด
        if val > 0: # คนจีบเสียความรู้สึก
            curr = st.session_state.weights[a][b]
            st.session_state.weights[a][b] = max(0, curr - 1)
        return "BLOCKED_BY_CLOSED"
    elif status == 'OPEN' and val > 0:
        final_val += 2 # เปิดใจรับเต็มที่

    current_score = st.session_state.weights[a][b]
    new_score = max(0, min(current_score + final_val, MAX_HEART))
    st.session_state.weights[a][b] = new_score
    return "SUCCESS"

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
    if "Hunter" in trait: # จีบคนฮอตสุด
        hotness = {o['name']: sum(st.session_state.weights[x['name']].get(o['name'], 0) for x in st.session_state.cast) for o in opps}
        target = max(opps, key=lambda x: hotness.get(x['name'], 0))
    elif "Loyal" in trait: # รักเดียว
        crush = get_top_crush(person['name'])
        if crush:
             target = next((o for o in opps if o['name'] == crush), random.choice(opps))
        else: target = random.choice(opps)
    elif "Villain" in trait: # แย่งซีนคนมีคู่ (คนที่เพิ่งไปสวรรค์มา)
        prev_visitors = [o for o in opps if o['name'] in st.session_state.paradise_visitors]
        target = random.choice(prev_visitors) if prev_visitors else random.choice(opps)
    else: # Socialite
        target = random.choice(opps)
    
    return target

def paradise_mechanic(p1_name, p2_name):
    # สุ่ม Vibe
    roll = random.randint(1, 100)
    pair_key = tuple(sorted((p1_name, p2_name)))
    
    if roll <= 15: # 15% Dead Air
        res = "AWKWARD"
        desc = "บรรยากาศเดตมาคุ... Dead Air ถามคำตอบคำ"
        update_rel(p1_name, p2_name, -1); update_rel(p2_name, p1_name, -1)
    elif roll <= 40: # 25% Friendzone
        res = "FRIENDZONE"
        desc = "คุยถูกคอแต่ฟีลพี่น้อง! (Friendzone)"
        update_rel(p1_name, p2_name, 1); update_rel(p2_name, p1_name, 1)
    elif roll <= 85: # 45% Good
        res = "GOOD"
        desc = "เดตโรแมนติก ความรู้สึกดีๆ เริ่มก่อตัว"
        update_rel(p1_name, p2_name, 3); update_rel(p2_name, p1_name, 2)
    else: # 15% Soulmate
        res = "SOULMATE"
        desc = "สปาร์คแรงมาก! คุยกันยันเช้าเหมือนพรหมลิขิต"
        update_rel(p1_name, p2_name, 5); update_rel(p2_name, p1_name, 5)
    
    st.session_state.couple_vibe[pair_key] = res
    return desc, res

# --- 🏗️ 5. UI: SETUP PHASE ---
if st.session_state.step == "SETUP":
    st.title("🔥 Single's Inferno: Casting (Original Netflix Style)")
    st.markdown("### ตั้งค่าผู้เข้าแข่งขัน 12 คน (ชาย 6 หญิง 6)")
    st.info("ℹ️ ระบบจะสุ่ม อายุ, อาชีพ, และนิสัย (Hidden Stats) ให้เองเมื่อเริ่มเกม")

    col1, col2 = st.columns(2)
    m_data, f_data = [], []

    with col1:
        st.subheader("♂️ ฝ่ายชาย (6 คน)")
        for i in range(6):
            c1, c2 = st.columns([3, 1])
            name = c1.text_input(f"M{i+1}", DEFAULT_CAST_M[i], key=f"m_{i}")
            img = c2.text_input(f"Img Link {i+1}", "", placeholder="Optional URL", key=f"mi_{i}")
            m_data.append({"name": name, "img": img if img else DEF_IMG_M, "gender": "M"})
            
    with col2:
        st.subheader("♀️ ฝ่ายหญิง (6 คน)")
        for i in range(6):
            c1, c2 = st.columns([3, 1])
            name = c1.text_input(f"F{i+1}", DEFAULT_CAST_F[i], key=f"f_{i}")
            img = c2.text_input(f"Img Link {i+1}", "", placeholder="Optional URL", key=f"fi_{i}")
            f_data.append({"name": name, "img": img if img else DEF_IMG_F, "gender": "F"})

    st.divider()
    if st.button("🚀 ยืนยันรายชื่อ & เริ่มรายการ!"):
        # Generate Hidden Stats
        full_pool = []
        for p in m_data + f_data:
            p['age'] = random.randint(21, 35)
            p['job'] = random.choice(JOBS)
            p['trait'] = random.choice(TRAITS)
            full_pool.append(p)
        
        st.session_state.master_pool = full_pool
        # เลือก 4 คนแรกของแต่ละเพศเข้าเกาะ
        st.session_state.cast = m_data[:4] + f_data[:4]
        # ที่เหลือเข้า Waiting List
        st.session_state.waiting_list = m_data[4:] + f_data[4:]
        
        # Initialize Weights
        names = [p['name'] for p in st.session_state.master_pool]
        st.session_state.weights = {n: {target: 0 for target in names if target != n} for n in names}
        
        log_event("System", f"☀️ --- DAY 1 เริ่มต้นขึ้นแล้ว! สมาชิก 8 คนแรกเดินทางมาถึงเกาะนรก ---")
        st.session_state.step = "GAME"
        st.rerun()

# --- 🏝️ 6. UI: GAMEPLAY ---
elif not st.session_state.game_over:
    st.title(f"🔥 Inferno Island - DAY {st.session_state.day}")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🛠️ Control Center")
        if st.button("🧹 Reset All"): st.session_state.clear(); st.rerun()
        
        st.divider()
        st.markdown("### 💘 Heart Status")
        for p in st.session_state.cast:
            # Show Status Tags
            tags = ""
            if p['name'] in st.session_state.statuses:
                s = st.session_state.statuses[p['name']]
                tags += f" <span class='status-tag' style='background:#555'>🔒CLOSED</span>" if s == 'CLOSED' else f" <span class='status-tag' style='background:#2ca02c'>🔓OPEN</span>"
            
            # Show Vibe Tags (Soulmate/Friendzone)
            for pair_key, vibe in st.session_state.couple_vibe.items():
                if p['name'] in pair_key:
                    partner = pair_key[0] if pair_key[1] == p['name'] else pair_key[1]
                    if vibe == "SOULMATE": tags += f" <span class='status-tag tag-soulmate'>💖{partner}</span>"
                    elif vibe == "AWKWARD": tags += f" <span class='status-tag tag-awkward'>🧊{partner}</span>"
                    elif vibe == "FRIENDZONE": tags += f" <span class='status-tag tag-friend'>🤝{partner}</span>"

            st.markdown(f"**{p['name']}** {tags}", unsafe_allow_html=True)
            
            # Top Crush
            sc = st.session_state.weights[p['name']]
            top = sorted(sc.items(), key=lambda x:x[1], reverse=True)[:1]
            if top and top[0][1] > 0:
                st.caption(f"❤️ {top[0][0]} ({top[0][1]} pts)")
        
        st.divider()
        st.info(f"รอเข้าเกาะ: {len(st.session_state.waiting_list)} คน")

    # --- MAIN DASHBOARD ---
    # 1. GRAPH
    with st.expander("📊 Relationship Map (Live)", expanded=True):
        col_g1, col_g2 = st.columns([3, 1])
        with col_g1:
            dot = graphviz.Digraph(engine='circo'); dot.attr(bgcolor='#0e1117')
            for p in st.session_state.cast:
                color = "#00a8ff" if p['gender'] == "M" else "#ff4dff"
                penwidth = "3" if p['name'] in st.session_state.statuses else "0"
                border_col = "red" if st.session_state.statuses.get(p['name'])=='CLOSED' else "green"
                
                label = f'<<TABLE BORDER="{penwidth}" COLOR="{border_col}" CELLBORDER="0"><TR><TD FIXEDSIZE="TRUE" WIDTH="50" HEIGHT="50"><IMG SRC="{p["img"]}"/></TD></TR><TR><TD><FONT COLOR="white"><B>{p["name"]}</B></FONT></TD></TR></TABLE>>'
                dot.node(p['name'], label=label, shape="none")
            
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
                st.warning("ข้อมูลลับยังไม่ถูกเปิดเผย")

    # 2. PRODUCER CONTROLS
    st.divider()
    st.markdown("### 🎬 Producer Actions")
    
    tab1, tab2, tab3 = st.tabs(["➕ เพิ่มสมาชิก (Newcomer)", "🔮 อีเวนต์พิเศษ (Special)", "🌪️ ข่าวลือ (Rumors)"])
    
    with tab1:
        if st.session_state.waiting_list:
            c1, c2 = st.columns([2, 1])
            to_add_name = c1.selectbox("เลือกคนเข้า:", [p['name'] for p in st.session_state.waiting_list])
            if c2.button("🚀 ส่งเข้าเกาะ"):
                p_obj = next(p for p in st.session_state.waiting_list if p['name'] == to_add_name)
                st.session_state.waiting_list.remove(p_obj)
                st.session_state.cast.append(p_obj)
                log_event("System", f"📢 NEWCOMER ALERT! {to_add_name} เดินลงมาที่ชายหาดแล้ว!", p1=p_obj)
                st.rerun()
        else:
            st.success("สมาชิกครบ 12 คนแล้ว!")

    with tab2:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if not st.session_state.info_revealed:
                if st.button("🎭 คืนเปิดเผยข้อมูล (Age/Job Reveal)"):
                    st.session_state.info_revealed = True
                    log_event("System", "🎭 คืนเปิดเผยข้อมูล! ทุกคนได้รู้อายุและอาชีพกันแล้ว...")
                    # คำนวณ Compatibility
                    txt_list = []
                    for p in st.session_state.cast:
                        crush = get_top_crush(p['name'])
                        if crush:
                            target = next(x for x in st.session_state.cast if x['name'] == crush)
                            # Logic: อาชีพเดียวกัน +2, อายุต่างกันเกิน 5 ปี -1
                            change = 0
                            if p['job'] == target['job']: 
                                change += 3
                                txt_list.append(f"{p['name']} ปลื้ม {target['name']} ที่ทำงานสายเดียวกัน (+3)")
                            if abs(p['age'] - target['age']) > 5:
                                change -= 1
                                txt_list.append(f"{p['name']} กังวลเรื่องช่องว่างระหว่างวัยกับ {target['name']} (-1)")
                            update_rel(p['name'], target['name'], change)
                    if txt_list: log_event("Reveal", " | ".join(txt_list))
                    st.rerun()
            else:
                st.info("เปิดเผยข้อมูลไปแล้ว")
        
        with col_s2:
             if st.button("🔥 บังคับสลับคู่ (Shuffle)"):
                 log_event("System", "🌪️ กฎพิเศษ: ห้ามคุยกับคู่เดิม! ต้องเปลี่ยนเป้าหมาย")
                 st.rerun()

    with tab3:
        if st.button("🗣️ ปล่อยข่าวลือ (Rumor)"):
            victim = random.choice(st.session_state.cast)
            rumor_type = random.choice(["BAD", "GOOD", "LOVE"])
            
            if rumor_type == "BAD":
                txt = f"มีข่าวลือว่า {victim['name']} พูดจาลับหลังคนอื่นไม่ดี..."
                # ลดคะแนนทุกคนที่มีต่อ victim
                for p in st.session_state.cast: 
                    if p != victim: update_rel(p['name'], victim['name'], -2)
            elif rumor_type == "GOOD":
                txt = f"เขาว่ากันว่า {victim['name']} ตื่นมาทำอาหารให้ทุกคนกิน เช้ามาก!"
                for p in st.session_state.cast: 
                    if p != victim: update_rel(p['name'], victim['name'], 2)
            else: # LOVE
                target = random.choice([c for c in st.session_state.cast if c != victim])
                txt = f"มีคนเห็น {victim['name']} แอบมอง {target['name']} ตาเป็นมัน!"
                # ทำให้คู่แข่งหึง
                for p in st.session_state.cast:
                    crush = get_top_crush(p['name'])
                    if crush == target['name'] and p['name'] != victim['name']:
                        st.session_state.statuses[p['name']] = "CLOSED"
                        log_event("System", f"😡 {p['name']} ได้ยินข่าวลือแล้วหึง! ปิดใจทันที")

            log_event("Rumor", f"🤫 Pssst... {txt}", p1=victim)
            st.rerun()

    # 3. ACTIVITIES
    st.divider()
    st.markdown("### 🕹️ Activities")
    
    # Filter people
    busy_people = st.session_state.paradise_visitors
    on_island = [c for c in st.session_state.cast if c['name'] not in busy_people]
    
    ac1, ac2, ac3 = st.columns(3)
    
    with ac1:
        st.markdown("#### 🏆 1. แข่งชิง Paradise")
        if len(on_island) >= 2 and st.button("🏁 เริ่มการแข่งขัน"):
            gender = random.choice(['M', 'F'])
            comps = [c for c in on_island if c['gender'] == gender]
            if len(comps) < 2: 
                st.error("คนไม่พอแข่ง")
            else:
                random.shuffle(comps)
                winner = comps[0]
                runner_up = comps[1]
                
                # Narration
                game_desc = random.choice(["วิ่งแข่งริมหาด", "มวยปล้ำในโคลน", "ดึงธงชิงไหวพริบ"])
                desc = f"การแข่ง {game_desc} สุดเดือด! {runner_up['name']} ไล่กวดมาติดๆ แต่สุดท้าย {winner['name']} เข้าเส้นชัยเป็นที่ 1! 🥇"
                log_event("Game", desc, p1=winner)
                
                # Winner chooses date
                opps = [x for x in on_island if x['gender'] != winner['gender']]
                if opps:
                    # AI Choice logic
                    target = ai_choose_target(winner, on_island)
                    if not target: target = random.choice(opps) # fallback
                    
                    st.session_state.paradise_visitors.extend([winner['name'], target['name']])
                    
                    # Vibe Check
                    vibe_txt, vibe_res = paradise_mechanic(winner['name'], target['name'])
                    
                    log_event("Paradise", f"บินไปเกาะสวรรค์กับ {target['name']}... {vibe_txt}", p1=winner, p2=target)
                    
                    # Trigger Jealousy
                    for p in on_island:
                        my_crush = get_top_crush(p['name'])
                        if my_crush == target['name']:
                            st.session_state.statuses[p['name']] = "CLOSED"
                            log_event("System", f"💔 {p['name']} เห็นคนที่ชอบไปกับคนอื่น -> ปิดประตูใจ")
                            
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
                     # Date ในเกาะ ผลน้อยกว่า Paradise แต่ปลอดภัย
                    score = random.randint(1, 3)
                    update_rel(winner['name'], target['name'], score)
                    update_rel(target['name'], winner['name'], score - 1)
                    log_event("Date", f"ชนะเกมชิงมื้อเที่ยง! ชวน {target['name']} ไปกินข้าว (+{score})", p1=winner, p2=target)
                    st.rerun()

    with ac3:
        st.markdown("#### 👣 3. Free Time (AI Walk)")
        if st.button("ปล่อยเดินเกมอิสระ"):
            log_event("System", "👣 --- Free Time: ถึงเวลาทำคะแนน ---")
            for p in on_island:
                target = ai_choose_target(p, on_island)
                if target:
                    res = update_rel(p['name'], target['name'], 1)
                    trait_txt = f"({p['trait']})"
                    if res == "BLOCKED_BY_CLOSED":
                        log_event("Fail", f"{trait_txt} เข้าหาผิดจังหวะ! อีกฝ่ายปิดใจอยู่", p1=p, p2=target)
                    elif res == "BLOCKED_BY_AWKWARD":
                        log_event("Fail", f"{trait_txt} เข้าหาแต่บรรยากาศยังมาคุจากเมื่อวาน", p1=p, p2=target)
                    else:
                        log_event("Talk", f"{trait_txt} เนียนเข้าไปคุยทำคะแนนสำเร็จ", p1=p, p2=target)
            st.rerun()

    # --- END DAY ---
    st.divider()
    if st.button("🌙 จบวัน (End Day) & บันทึกผล", type="primary"):
        # Save History
        snapshot = {sender: targets.copy() for sender, targets in st.session_state.weights.items()}
        st.session_state.score_history.append({"day": st.session_state.day, "scores": snapshot})
        
        # Reset Daily States
        st.session_state.day += 1
        st.session_state.paradise_visitors = []
        # Statuses (Closed/Open) ล้างทุกวัน หรือจะเก็บไว้ก็ได้ (ในที่นี้ล้างเพื่อให้โอกาสแก้ตัว)
        st.session_state.statuses = {} 
        # Couple Vibe เก็บไว้โชว์วันรุ่งขึ้น แต่ต้องเคลียร์ของเก่าไหม? ในที่นี้เก็บทับเลย
        
        # Check Game Over
        if st.session_state.day > MAX_DAYS:
            st.session_state.game_over = True
            st.session_state.finale_phase = "START"
        
        log_event("System", f"💤 จบวัน! ทุกคนแยกย้ายกันนอน... เตรียมเข้าสู่ DAY {st.session_state.day}")
        st.rerun()

    # --- LOGS DISPLAY ---
    st.subheader("📝 บันทึกเหตุการณ์ (Logs)")
    for log in reversed(st.session_state.logs[-15:]):
        color_border = "#ff4b1f" if log['type'] in ["Paradise", "Game"] else "#444"
        bg = "#222"
        icon = "📌"
        if log['type'] == "Paradise": icon = "🚁"
        elif log['type'] == "System": icon = "☀️"
        elif log['type'] == "Fail": icon = "💔"; color_border = "#ff0000"
        
        with st.container():
            st.markdown(f"""
            <div class="log-box" style="border-left: 4px solid {color_border};">
                <small style="color:#888">DAY {log['day']} | {log['type']}</small><br>
                <b>{icon} {log['txt']}</b>
            </div>
            """, unsafe_allow_html=True)

# --- 💖 7. FINALE ---
else:
    st.title("💖 THE FINALE: บทสรุปความรัก")
    
    if st.session_state.finale_phase == "START":
        st.markdown("### ถึงเวลาตัดสินใจครั้งสุดท้าย...")
        if st.button("เริ่มพิธีเลือกคู่"):
            # สุ่มลำดับผู้หญิงออกมาเลือก
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
                st.markdown(f"## 👩 {curr_w['name']} เดินออกมาหน้าหลุมรัก")
                st.write("ผู้ชายคนไหนจะก้าวออกมา?")
                
                # Logic: ผู้ชายจะออกมาถ้าชอบผู้หญิงคนนี้ที่สุด และคะแนน > 5
                suitors = []
                for m in st.session_state.cast:
                    if m['gender'] == 'M':
                        crush = get_top_crush(m['name'])
                        score = st.session_state.weights[m['name']].get(curr_w['name'], 0)
                        if crush == curr_w['name'] and score > 5:
                            suitors.append(m)
                
                if suitors:
                    cols = st.columns(len(suitors))
                    for i, s in enumerate(suitors):
                        cols[i].image(s['img'], width=100)
                        cols[i].caption(s['name'])
                    
                    st.divider()
                    # ผู้หญิงเลือกใคร?
                    # 1. ดูคะแนนที่ผู้หญิงมีต่อผู้ชาย
                    best_m = max(suitors, key=lambda x: st.session_state.weights[curr_w['name']].get(x['name'], 0))
                    w_score = st.session_state.weights[curr_w['name']].get(best_m['name'], 0)
                    
                    # TWIST ENDINGS
                    if w_score >= 15: # รักกันมาก
                        res_txt = f"💍 **THE WEDDING ENDING!** {curr_w['name']} เลือก {best_m['name']} ทั้งคู่สวมแหวนและเดินออกไปอย่างมีความสุข (Score: {w_score})"
                        st.session_state.final_couples.append((best_m, curr_w, "MARRIAGE"))
                        st.success(res_txt)
                        st.balloons()
                    elif w_score >= 5: # ปกติ
                        res_txt = f"❤️ {curr_w['name']} เลือกจับมือกับ {best_m['name']} (Score: {w_score})"
                        st.session_state.final_couples.append((best_m, curr_w, "COUPLE"))
                        st.success(res_txt)
                    else: # Friendzone / Betrayal
                        # เช็คว่าผู้หญิงมีใจให้คนอื่นไหม
                        real_crush = get_top_crush(curr_w['name'])
                        if real_crush and real_crush != best_m['name']:
                             res_txt = f"😱 **THE BETRAYAL!** {curr_w['name']} ปฏิเสธ {best_m['name']} เพราะเธอยังลืม {real_crush} ไม่ได้!"
                        else:
                             res_txt = f"🤝 **FRIENDZONE!** {curr_w['name']} บอกว่าขอเป็นพี่น้องกันดีกว่า (Score น้อยเกินไป)"
                        st.warning(res_txt)
                else:
                    st.error("💨 ไม่มีใครก้าวออกมาหาเธอ...")
            
            if st.button("คนต่อไป >>"):
                st.session_state.current_f_idx += 1
                st.rerun()
        else:
            st.session_state.finale_phase = "RESULTS"
            st.rerun()

    elif st.session_state.finale_phase == "RESULTS":
        st.header("📸 บทสรุปคู่รัก")
        for m, w, status in st.session_state.final_couples:
            st.success(f"[{status}] {m['name']} ❤️ {w['name']}")
            c1, c2, c3 = st.columns([1,1,3])
            c1.image(m['img'], width=100); c2.image(w['img'], width=100)
            with c3:
                # Graph plot
                data = []
                for h in st.session_state.score_history:
                    data.append({"Day": h['day'], m['name']: h['scores'][m['name']][w['name']], w['name']: h['scores'][w['name']][m['name']]})
                st.line_chart(pd.DataFrame(data).set_index("Day"))
        
        if st.button("🔄 New Game"):
            st.session_state.clear()
            st.rerun()
