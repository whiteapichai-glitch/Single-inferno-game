import streamlit as st
import random
import graphviz
import pandas as pd

# --- 💅 1. CUSTOM CSS ---
st.set_page_config(layout="wide", page_title="Single's Inferno Simulator")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { background-color: #ff4b1f; color: white; border-radius: 8px; border: none; height: 3em; width: 100%; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { background-color: #ff9068; transform: scale(1.02); }
    .stExpander { border: 1px solid #333; border-radius: 10px; background-color: #1f1f1f; }
    h1, h2, h3 { color: #ff9068 !important; font-family: 'Helvetica', sans-serif; }
    .status-tag { padding: 2px 8px; border-radius: 5px; font-size: 0.8em; margin-left: 5px; }
    .status-closed { background-color: #555; color: #aaa; border: 1px solid #777; }
    .status-open { background-color: #004d00; color: #00ff00; border: 1px solid #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# --- ⚙️ 2. CONFIG ---
MAX_HEART = 20  # เพิ่มเพดานคะแนนหน่อยเพราะวันเยอะขึ้น
MAX_DAYS = 13   # เพิ่มวันให้เด็กใหม่มีเวลาหายใจ
DEF_M_NAMES = ["เจษ", "บลู", "มีน", "โอ๊ต", "มอส", "นนกุล"]
DEF_F_NAMES = ["ใบเฟิร์น", "เก้า", "วี", "มายด์", "ฮันน่า", "โจริญ"]
DEF_M_IMG = "https://cdn-icons-png.flaticon.com/512/4128/4128176.png"
DEF_F_IMG = "https://cdn-icons-png.flaticon.com/512/6997/6997662.png"

# --- 📦 3. INITIAL STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "SETUP"
    st.session_state.master_pool = []
    st.session_state.cast = []
    st.session_state.weights = {} 
    st.session_state.score_history = [] 
    st.session_state.day = 1
    st.session_state.logs = [] 
    st.session_state.paradise_visitors = [] # คนที่ไปสวรรค์
    st.session_state.island_date_couples = [] # คนที่เดตในเกาะ
    st.session_state.statuses = {} # เก็บสถานะ: 'CLOSED' หรือ 'OPEN'
    st.session_state.played_today = []
    st.session_state.game_over = False
    st.session_state.finale_phase = None
    st.session_state.final_couples = []

# --- 🧪 4. FUNCTIONS ---
def update_rel(a, b, val):
    if a in st.session_state.weights and b in st.session_state.weights[a]:
        # เช็คสถานะพิเศษ
        status = st.session_state.statuses.get(b, None)
        final_val = val
        
        # Logic: ถ้าคนรับ (b) ปิดใจอยู่
        if status == 'CLOSED':
            final_val = 0 # จีบไม่ติดเลย
            # คนส่ง (a) อาจจะเสียความมั่นใจ
            if val > 0: 
                # ลดคะแนนความชอบของ a ที่มีต่อ b เพราะโดนเมิน
                if a in st.session_state.weights and b in st.session_state.weights[a]:
                     curr = st.session_state.weights[a][b]
                     st.session_state.weights[a][b] = max(0, curr - 1)
                return "BLOCKED" # ส่งสัญญาณว่าโดนบล็อก

        # Logic: ถ้าคนรับ (b) เปิดใจ (Rebound mode)
        elif status == 'OPEN' and val > 0:
            final_val += 1 # บวกเพิ่มพิเศษ

        new_score = st.session_state.weights[a][b] + final_val
        st.session_state.weights[a][b] = max(0, min(new_score, MAX_HEART))
        return "SUCCESS"
    return "ERROR"

def get_top_crush(name):
    scores = st.session_state.weights.get(name, {})
    if not scores: return None
    # ต้องมีคะแนนมากกว่า 0 ถึงจะนับว่าเป็น crush
    valid_scores = {k: v for k, v in scores.items() if v > 0}
    if valid_scores:
        return max(valid_scores, key=valid_scores.get)
    return None

def save_daily_history():
    snapshot = {sender: targets.copy() for sender, targets in st.session_state.weights.items()}
    st.session_state.score_history.append({"day": st.session_state.day, "scores": snapshot})

# --- 🏗️ 5. UI: SETUP ---
if st.session_state.step == "SETUP":
    st.title("🔥 Single's Inferno: Cast Setup")
    col1, col2 = st.columns(2)
    m_inputs, f_inputs = [], []
    with col1:
        st.subheader("♂️ Men Pool")
        for i in range(5):
            name = st.text_input(f"ชาย {i+1}", DEF_M_NAMES[i], key=f"m_n{i}")
            file = st.file_uploader(f"รูป {name}", type=['jpg','png'], key=f"m_u{i}")
            m_inputs.append({"name": name, "img": file if file else DEF_M_IMG, "gender": "M", "is_upload": file is not None})
    with col2:
        st.subheader("♀️ Women Pool")
        for i in range(5):
            name = st.text_input(f"หญิง {i+1}", DEF_F_NAMES[i], key=f"f_n{i}")
            file = st.file_uploader(f"รูป {name}", type=['jpg','png'], key=f"f_u{i}")
            f_inputs.append({"name": name, "img": file if file else DEF_F_IMG, "gender": "F", "is_upload": file is not None})

    if st.button("🚀 ยืนยันรายชื่อและเปิดเกาะ"):
        st.session_state.master_pool = m_inputs + f_inputs
        st.session_state.cast = m_inputs[:4] + f_inputs[:4] # เริ่ม 4-4
        names = [p['name'] for p in st.session_state.master_pool]
        st.session_state.weights = {n: {target: 0 for target in names if target != n} for n in names}
        save_daily_history() 
        st.session_state.logs.append({"type": "System", "txt": "☀️ --- รายการเริ่ม! สมาชิก 8 คนแรกพร้อมแล้ว --- ☀️"})
        st.session_state.step = "GAME"; st.rerun()

# --- 🏝️ 6. UI: GAMEPLAY ---
elif not st.session_state.game_over:
    st.title(f"☀️ Inferno Island - DAY {st.session_state.day} / {MAX_DAYS}")
    
    # --- Sidebar Status ---
    with st.sidebar:
        if st.button("🧹 Reset Game"):
            st.session_state.clear(); st.rerun()
        st.divider(); st.header(f"💘 Heart Score")
        for p in st.session_state.cast:
            name = p['name']
            status_icon = ""
            if name in st.session_state.statuses:
                s = st.session_state.statuses[name]
                status_icon = "❤️‍🩹(ปิดใจ)" if s == 'CLOSED' else "🔓(เปิดใจ)"
            
            st.markdown(f"**{name}** {status_icon}")
            sc = sorted(st.session_state.weights[name].items(), key=lambda x: x[1], reverse=True)
            for t, v in sc[:2]: 
                if v > 0: st.caption(f"❤️ {t} ({v})")
            st.divider()

    # --- 📊 Relationship Graph ---
    with st.expander("📊 แผนผังความสัมพันธ์ (Real-time)", expanded=True):
        col_m1, col_m2 = st.columns([3, 1])
        with col_m1:
            dot = graphviz.Digraph(); dot.attr(rankdir='LR', bgcolor='#0e1117')
            for p in st.session_state.cast:
                color = "#00a8ff" if p['gender'] == "M" else "#ff4dff"
                status_color = "red" if st.session_state.statuses.get(p['name']) == 'CLOSED' else ("green" if st.session_state.statuses.get(p['name']) == 'OPEN' else "white")
                penwidth = 3 if p['name'] in st.session_state.statuses else 0
                
                if not p['is_upload']:
                    label = f'<<TABLE BORDER="{penwidth}" COLOR="{status_color}" CELLBORDER="0"><TR><TD FIXEDSIZE="TRUE" WIDTH="50" HEIGHT="50"><IMG SRC="{p["img"]}"/></TD></TR><TR><TD><FONT COLOR="white">{p["name"]}</FONT></TD></TR></TABLE>>'
                    dot.node(p['name'], label=label, shape="none")
                else:
                    icon = "🤵" if p['gender'] == "M" else "💃"
                    dot.node(p['name'], label=f"{icon} {p['name']}", color=color, fontcolor="white", style="filled")
            
            for c in st.session_state.cast:
                sc = st.session_state.weights[c['name']]
                # วาดเส้นเฉพาะ Top 1 ที่คะแนน > 0
                if any(v > 0 for v in sc.values()):
                    t = max(sc, key=sc.get); v = sc[t]
                    if v > 0: dot.edge(c['name'], t, penwidth=str(min(v, 5)), color="#ff4b1f", tooltip=f"Score: {v}")
            st.graphviz_chart(dot)

    # --- 🎬 PRODUCER CONTROL ---
    st.divider()
    with st.expander("🎬 Producer Control (ผู้ควบคุมรายการ)", expanded=True):
        t_entry, t_invisible = st.tabs(["➕ ส่งสมาชิกเพิ่ม (Newcomer)", "🖐️ Invisible Hand"])
        
        with t_entry:
            active_names = [c['name'] for c in st.session_state.cast]
            waiting = [p for p in st.session_state.master_pool if p['name'] not in active_names]
            if waiting:
                c1, c2 = st.columns(2)
                to_add = c1.selectbox("เลือกคนเข้าเกาะ:", [p['name'] for p in waiting])
                p_obj = next(p for p in waiting if p['name'] == to_add)
                
                privilege = c2.checkbox("⭐ สิทธิ์เดตสวรรค์ทันที (Buff แรง!)")
                partner_name = c2.selectbox("เลือกคู่เดตแรก:", active_names) if privilege else None
                
                if st.button(f"🚀 ส่ง {to_add} เข้าเกาะ"):
                    st.session_state.cast.append(p_obj)
                    st.session_state.logs.append({"type": "System", "txt": f"📢 เปิดตัวสมาชิกใหม่: {to_add}!"})
                    
                    if privilege and partner_name:
                        st.session_state.paradise_visitors.extend([to_add, partner_name])
                        # Buff แรงสำหรับเด็กใหม่: +4 ถึง +6 ไปเลยจะได้ตามทัน
                        p1, p2 = random.randint(4, 6), random.randint(2, 4)
                        update_rel(to_add, partner_name, p1)
                        update_rel(partner_name, to_add, p2)
                        st.session_state.logs.append({"type":"Paradise", "p1":p_obj, "p2":next(c for c in st.session_state.cast if c['name']==partner_name), "txt":f"เดตแรกของเด็กใหม่! คะแนนพุ่ง (+{p1} | +{p2})"})
                        
                        # --- TRIGGER JEALOUSY FOR NEWCOMER DATE ---
                        # ใครก็ตามที่ชอบ partner_name อยู่ จะต้องอกหัก
                        for p in st.session_state.cast:
                            if p['name'] not in [to_add, partner_name]:
                                crush = get_top_crush(p['name'])
                                if crush == partner_name:
                                    status_roll = random.choice(['CLOSED', 'OPEN'])
                                    st.session_state.statuses[p['name']] = status_roll
                                    st.session_state.logs.append({"type":"System", "txt":f"💔 {p['name']} ช็อคที่ {crush} ไปกับเด็กใหม่! -> สถานะ: {status_roll}"})
                    st.rerun()
            else:
                st.info("สมาชิกครบทุกคนแล้ว")

        with t_invisible:
            inv_c1, inv_c2, inv_c3 = st.columns(3)
            ps = inv_c1.selectbox("Source:", active_names)
            pr = inv_c2.selectbox("Target:", [n for n in active_names if n != ps])
            cmd = inv_c3.selectbox("Action:", ["Force +2", "Force -2", "Set Status: CLOSED", "Set Status: OPEN"])
            if st.button("⚡ Execute Command"):
                if "Status" in cmd:
                    st = cmd.split(": ")[1]
                    st.session_state.statuses[ps] = st
                    st.session_state.logs.append({"type":"System", "txt":f"⚡ อาถรรพ์รายการ: {ps} ติดสถานะ {st}"})
                elif "+" in cmd: update_rel(ps, pr, 2)
                else: update_rel(ps, pr, -2)
                st.rerun()

    # --- 🕹️ ACTIVITIES ---
    st.divider()
    st.subheader("🕹️ Activities Panel")
    
    # คนที่อยู่บนเกาะ (ไม่ได้ไปสวรรค์ และ ไม่ได้เดตในเกาะ)
    busy_people = st.session_state.paradise_visitors + [x for couple in st.session_state.island_date_couples for x in couple]
    on_island = [c for c in st.session_state.cast if c['name'] not in busy_people]
    
    act_c1, act_c2, act_c3, act_c4 = st.columns(4)

    # 1. PARADISE DATE (MAIN EVENT)
    with act_c1:
        st.markdown("#### 🏆 แข่งชิง Paradise")
        if len(on_island) >= 2:
            if st.button("🏁 แข่งเกมชิงสิทธิ์"):
                gender_mode = random.choice(['M','F']) # สุ่มชายหรือหญิงชนะ
                candidates = [c for c in on_island if c['gender'] == gender_mode]
                
                if len(candidates) > 0:
                    winner = random.choice(candidates)
                    # ผู้ชนะเลือกคน
                    # Logic: เลือกคนที่ชอบที่สุดในใจ หรือถ้าไม่มีชอบเลย ให้สุ่มคนที่เพศตรงข้าม
                    crush = get_top_crush(winner['name'])
                    avail_partners = [x for x in on_island if x['gender'] != winner['gender']]
                    
                    target = None
                    if crush and any(p['name'] == crush for p in avail_partners):
                        target = next(p for p in avail_partners if p['name'] == crush)
                    elif avail_partners:
                        target = random.choice(avail_partners)
                    
                    if target:
                        st.session_state.paradise_visitors.extend([winner['name'], target['name']])
                        p1, p2 = random.randint(2, 4), random.randint(1, 3)
                        update_rel(winner['name'], target['name'], p1)
                        update_rel(target['name'], winner['name'], p2)
                        st.session_state.logs.append({"type":"Paradise", "p1":winner, "p2":target, "txt":f"ชนะเกม! เลือกพาไปสวรรค์ (+{p1} | +{p2})"})

                        # --- 💔 SYSTEM: JEALOUSY & STATUS ---
                        # ตรวจสอบคนทีเหลือบนเกาะ ว่ามีใครชอบ winner หรือ target ไหม
                        leftovers = [x for x in st.session_state.cast if x['name'] not in st.session_state.paradise_visitors]
                        for person in leftovers:
                            my_crush = get_top_crush(person['name'])
                            # ถ้าคนที่ฉันชอบ (my_crush) ดันเป็นคนที่ไปสวรรค์ (winner หรือ target)
                            if my_crush in [winner['name'], target['name']]:
                                # สุ่มสถานะทันที
                                result = random.choice(['CLOSED', 'OPEN'])
                                st.session_state.statuses[person['name']] = result
                                msg = "ปิดประตูใจ (ใครคุยด้วย=0)" if result == 'CLOSED' else "เปิดใจ (เหงามาก โอกาส+เยอะ)"
                                st.session_state.logs.append({"type":"System", "txt":f"💔 {person['name']} เห็น {my_crush} ไปกับคนอื่น! -> สถานะ: {msg}"})
                        
                        st.rerun()
                    else:
                        st.error("ไม่มีคู่ให้เลือก!")
        else:
            st.caption("คนไม่พอ")

    # 2. ISLAND DATE (NEW)
    with act_c2:
        st.markdown("#### 🌴 แข่งชิงเดตในเกาะ")
        # กิจกรรมรอง สำหรับคนที่ไม่ได้ไปสวรรค์
        if len(on_island) >= 2:
            if st.button("☕ แข่งเดตกาแฟ/อาหาร"):
                gender_mode = random.choice(['M','F'])
                candidates = [c for c in on_island if c['gender'] == gender_mode]
                if candidates:
                    winner = random.choice(candidates)
                    # เลือกคู่
                    avail_partners = [x for x in on_island if x['gender'] != winner['gender'] and x['name'] != winner['name']]
                    if avail_partners:
                        # พยายามเลือกคนที่ชอบก่อน
                        crush = get_top_crush(winner['name'])
                        target = next((p for p in avail_partners if p['name'] == crush), random.choice(avail_partners))
                        
                        st.session_state.island_date_couples.append((winner['name'], target['name']))
                        
                        # คะแนนขึ้นน้อยกว่า Paradise แต่ปลอดภัยจากคนอื่น
                        p1, p2 = random.randint(1, 2), random.randint(0, 2)
                        update_rel(winner['name'], target['name'], p1)
                        update_rel(target['name'], winner['name'], p2)
                        st.session_state.logs.append({"type":"Date", "p1":winner, "p2":target, "txt":f"เดตมื้ออาหารในเกาะ (+{p1} | +{p2})"})
                        st.rerun()
        else:
            st.caption("คนไม่พอ")

    # 3. BONFIRE (TRUTH OR DARE)
    with act_c3:
        st.markdown("#### 🔥 รอบกองไฟ (Bonfire)")
        rem = [c for c in on_island if c['name'] not in st.session_state.played_today]
        if len(rem) > 0 and st.button(f"🎲 หมุนขวด ({len(rem)})"):
            a = random.choice(rem)
            # สุ่มคนถาม (เพศตรงข้าม)
            opps = [c for c in on_island if c['gender'] != a['gender']]
            if opps:
                t = random.choice(opps)
                st.session_state.played_today.append(a['name'])
                
                # คะแนนแบบมหกรรมเสี่ยงดวง (-2 ถึง 2)
                score_change = random.choice([-2, -1, 0, 1, 2])
                txt_res = ""
                if score_change == -2: txt_res = "คำตอบดับฝัน (Turn off) 💔 -2"
                elif score_change == -1: txt_res = "ตอบอึกอัก ไม่ชัดเจน ☁️ -1"
                elif score_change == 0: txt_res = "ตอบกว้างๆ เพื่อนกันครับ 😐 0"
                elif score_change == 1: txt_res = "หยอดเบาๆ พอให้ลุ้น 😉 +1"
                elif score_change == 2: txt_res = "สารภาพตรงๆ ว่ามีใจ! 😍 +2"
                
                update_rel(t['name'], a['name'], score_change) # คนถามรู้สึกยังไงกับคนตอบ
                st.session_state.logs.append({"type":"Game", "p1":a, "p2":t, "txt":f"โดนถามกลางวง: {txt_res}"})
                st.rerun()
            else:
                st.error("ไม่มีคู่ต่างเพศให้ถาม")
        else:
            st.caption("เล่นครบ/คนน้อย")

    # 4. FREE TIME (AUTO)
    with act_c4:
        st.markdown("#### 💬 Free Time")
        if st.button("เดินเกมอิสระ (ทุกคน)"):
            st.session_state.logs.append({"type": "System", "txt": "👣 --- ช่วงเวลา Free Time: ใครจะเดินเกมหาใคร? ---"})
            count_moves = 0
            for p in on_island:
                # เลือกเป้าหมาย: คนที่ชอบที่สุด หรือ สุ่ม
                crush = get_top_crush(p['name'])
                opps = [x for x in on_island if x['gender']!=p['gender']]
                if not opps: continue
                
                target_name = crush if (crush and any(o['name'] == crush for o in opps)) else random.choice(opps)['name']
                
                # คำนวณคะแนน
                val = random.choice([0, 1, 1, 2]) # ส่วนใหญ่เป็นบวก
                res = update_rel(p['name'], target_name, val)
                
                target_obj = next(x for x in st.session_state.cast if x['name'] == target_name)
                
                if res == "BLOCKED":
                    st.session_state.logs.append({"type":"Fail", "p1":p, "p2":target_obj, "txt":f"เข้าหาผิดจังหวะ! อีกฝ่ายปิดใจอยู่ (Score 0, ผู้เข้าหา -1)"})
                elif res == "SUCCESS":
                    bonus_txt = " (Boost!)" if st.session_state.statuses.get(target_name) == 'OPEN' else ""
                    st.session_state.logs.append({"type":"Beach", "p1":p, "p2":target_obj, "txt":f"นั่งคุยริมหาด (+{val}){bonus_txt}"})
                count_moves += 1
            st.rerun()

    # --- END DAY ---
    st.divider()
    if st.button("🌙 จบวัน (End Day) - ล้างสถานะ & บันทึกคะแนน", type="primary"):
        save_daily_history()
        st.session_state.day += 1
        st.session_state.paradise_visitors = []
        st.session_state.island_date_couples = []
        st.session_state.played_today = []
        st.session_state.statuses = {} # Reset Status ทุกเช้าวันใหม่ (ให้โอกาส Move on)
        
        if st.session_state.day > MAX_DAYS:
            st.session_state.game_over = True
            st.session_state.finale_phase = "START"
        st.rerun()

    # --- LOGS ---
    st.subheader("📝 บันทึกเหตุการณ์ล่าสุด")
    for entry in reversed(st.session_state.logs[-10:]): # โชว์แค่ 10 อันล่าสุดพอ
        if entry['type'] == "System": 
            st.info(entry['txt'])
        else:
            with st.container():
                c1, c2, c3 = st.columns([1,5,1])
                if 'p1' in entry: c1.image(entry['p1']['img'], width=60)
                c2.markdown(f"<div style='text-align:center; padding-top:10px;'>{entry.get('p1',{}).get('name','')} ➡️ {entry['txt']} ➡️ {entry.get('p2',{}).get('name','')}</div>", unsafe_allow_html=True)
                if 'p2' in entry: c3.image(entry['p2']['img'], width=60)
                st.markdown("---")

# --- 💖 7. FINALE (บทสรุป) ---
else:
    st.title("💖 The Finale: บทสรุปความรัก")
    
    if st.session_state.finale_phase == "START":
        st.balloons()
        if st.button("เริ่มพิธีเลือกคู่สุดท้าย"):
            women = [p for p in st.session_state.cast if p['gender'] == 'F']
            random.shuffle(women)
            st.session_state.female_order = women
            st.session_state.current_f_idx = 0
            st.session_state.finale_phase = "TURN"
            st.rerun()
            
    elif st.session_state.finale_phase == "TURN":
        if st.session_state.current_f_idx < len(st.session_state.female_order):
            curr_w = st.session_state.female_order[st.session_state.current_f_idx]
            st.markdown(f"## 👩 ถึงตาของ: {curr_w['name']}")
            c1, c2 = st.columns([1, 2])
            c1.image(curr_w['img'], width=200)
            
            # Logic การเลือก: ผู้ชายที่ชอบผู้หญิงคนนี้ที่สุด และต้องมีคะแนน > 0
            suitors = []
            for m in st.session_state.cast:
                if m['gender'] == 'M':
                    top_pick = get_top_crush(m['name'])
                    if top_pick == curr_w['name']:
                        suitors.append(m)
            
            with c2:
                st.write("### 📢 ผู้ชายที่ก้าวออกมา:")
                if suitors:
                    cols = st.columns(len(suitors))
                    for i, s in enumerate(suitors):
                        cols[i].image(s['img'], width=100)
                        cols[i].caption(s['name'])
                    
                    # ผู้หญิงเลือกใคร? (คนที่มีคะแนนให้มากสุด)
                    best_m = max(suitors, key=lambda x: st.session_state.weights[curr_w['name']].get(x['name'], 0))
                    w_score_to_m = st.session_state.weights[curr_w['name']].get(best_m['name'], 0)
                    
                    st.divider()
                    if w_score_to_m > 0:
                        st.success(f"🎉 เธอเลือกจับมือกับ **{best_m['name']}**! (Score: {w_score_to_m})")
                        st.session_state.final_couples.append((best_m, curr_w))
                    else:
                        st.warning(f"เธอปฏิเสธทุกคน! (ไม่ได้ชอบใครในกลุ่มนี้เลย)")
                else:
                    st.error("💨 ไม่มีใครออกมาหาเธอเลย...")
            
            if st.button("คนต่อไป >>"):
                st.session_state.current_f_idx += 1
                st.rerun()
        else:
            st.session_state.finale_phase = "RESULTS"
            st.rerun()
            
    elif st.session_state.finale_phase == "RESULTS":
        st.header("📸 ภาพรวมคู่รักที่สมหวัง")
        if not st.session_state.final_couples:
            st.write("ไม่มีใครสมหวังเลยสักคู่... 😱")
        
        for m, w in st.session_state.final_couples:
            st.success(f"❤️ Couple: {m['name']} & {w['name']}")
            c1, c2, c3 = st.columns([1,1,3])
            c1.image(m['img'], width=100); c2.image(w['img'], width=100)
            
            # Graph
            with c3:
                data = []
                for h in st.session_state.score_history:
                    d = {"Day": h['day']}
                    d[m['name']] = h['scores'][m['name']].get(w['name'], 0)
                    d[w['name']] = h['scores'][w['name']].get(m['name'], 0)
                    data.append(d)
                st.line_chart(pd.DataFrame(data).set_index("Day"))
                
        if st.button("🔄 New Game"):
            st.session_state.clear()
            st.rerun()
