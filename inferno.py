import streamlit as st
import random
import graphviz
import time
import pandas as pd

# --- 💅 1. CUSTOM CSS: INFERNO THEME ---
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; color: #ffffff; }
    .stButton>button { background-color: #ff4b1f; color: white; border-radius: 10px; border: none; height: 3em; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: #ff9068; color: white; border: 1px solid white; }
    .stExpander { border: 1px solid #ff4b1f; border-radius: 10px; background-color: #262626; }
    h1, h2, h3 { color: #ff9068 !important; }
    .stAlert { background-color: #333333; border: 1px solid #ff4b1f; color: white; }
    .stSidebar { background-color: #000000; border-right: 1px solid #ff4b1f; }
    /* ปรับขนาด File Uploader ให้เข้ากับธีม */
    .stFileUploader { background-color: #262626; padding: 10px; border-radius: 10px; border: 1px dashed #ff4b1f; }
    </style>
    """, unsafe_allow_html=True)

# --- ⚙️ 2. CONFIG ---
MAX_HEART = 15

# --- 📦 3. INITIAL STATE ---
if 'step' not in st.session_state:
    st.session_state.step = "SETUP"
    st.session_state.master_pool = []
    st.session_state.cast = []
    st.session_state.weights = {} 
    st.session_state.score_history = [] 
    st.session_state.day = 1
    st.session_state.logs = [] 
    st.session_state.daily_event = "ท้องฟ้าสดใส (ปกติ)"
    st.session_state.netizen_comment = "ยินดีต้อนรับสู่เกาะนรก ซีซั่นนี้เดือดแน่นอน!"
    st.session_state.paradise_visitors = []
    st.session_state.played_today = []
    st.session_state.game_over = False
    st.session_state.finale_phase = None
    st.session_state.female_order = []
    st.session_state.current_f_idx = 0
    st.session_state.final_couples = []

# --- 🧪 4. FUNCTIONS ---
def update_rel(a, b, val):
    if a in st.session_state.weights and b in st.session_state.weights[a]:
        new_score = st.session_state.weights[a][b] + val
        st.session_state.weights[a][b] = max(0, min(new_score, MAX_HEART))

def save_daily_history():
    snapshot = {sender: targets.copy() for sender, targets in st.session_state.weights.items()}
    st.session_state.score_history.append({"day": st.session_state.day, "scores": snapshot})

def get_netizen_comment():
    comments = ["คู่นี้เคมีเข้ากันมาก!", "ฉันว่ามีคนกำลังหึง...", "รอดูวันสุดท้ายไม่ไหวแล้ว!", "จะมีรักสามเส้าไหมนะวันนี้?", "ทีมงานสุ่มคนมาได้นัวมาก"]
    return random.choice(comments)

# --- 🏗️ 5. UI: SETUP ---
if st.session_state.step == "SETUP":
    st.title("🔥 Single's Inferno: Setup 12 Casts")
    st.write("อัปโหลดรูปภาพสมาชิก 12 คน (ชาย 6 หญิง 6) จากคลังรูปภาพของคุณ")
    
    col1, col2 = st.columns(2)
    
    # รูปไอคอน Default กรณีไม่ได้อัปโหลด
    def_m = "https://cdn-icons-png.flaticon.com/512/4128/4128176.png"
    def_f = "https://cdn-icons-png.flaticon.com/512/6997/6997662.png"

    with col1:
        st.subheader("♂️ Men Pool")
        m_pool_inputs = []
        for i in range(6):
            name = st.text_input(f"ชื่อชาย {i+1}", f"Man_{i+1}", key=f"m_n{i}")
            up_file = st.file_uploader(f"เลือกรูป {name}", type=['jpg','png','jpeg'], key=f"m_u{i}")
            # ถ้ามีไฟล์ให้ใช้ไฟล์ ถ้าไม่มีให้ใช้ Default
            img = up_file if up_file else def_m
            m_pool_inputs.append({"name": name, "img": img, "gender": "M"})
            st.divider()

    with col2:
        st.subheader("♀️ Women Pool")
        f_pool_inputs = []
        for i in range(6):
            name = st.text_input(f"ชื่อหญิง {i+1}", f"Girl_{i+1}", key=f"f_n{i}")
            up_file = st.file_uploader(f"เลือกรูป {name}", type=['jpg','png','jpeg'], key=f"f_u{i}")
            img = up_file if up_file else def_f
            f_pool_inputs.append({"name": name, "img": img, "gender": "F"})
            st.divider()

    if st.button("🚀 ยืนยันรายชื่อและไปที่เกาะนรก"):
        st.session_state.master_pool = m_pool_inputs + f_pool_inputs
        names = [p['name'] for p in st.session_state.master_pool]
        st.session_state.weights = {n: {target: 0 for target in names if target != n} for n in names}
        save_daily_history() 
        st.session_state.logs.append({"type": "System", "txt": "☀️ --- เริ่มต้นรายการ: DAY 1 --- ☀️"})
        st.session_state.step = "GAME"
        st.rerun()

# --- 🏝️ 6. UI: GAMEPLAY & FINALE ---
else:
    if st.session_state.game_over:
        st.title("💖 Final Journey: Selection Zone")
        if st.session_state.finale_phase == "START":
            if st.button("เริ่มพิธีการเลือกคู่"):
                women = [p for p in st.session_state.cast if p['gender'] == 'F']
                random.shuffle(women); st.session_state.female_order = women
                st.session_state.current_f_idx = 0; st.session_state.finale_phase = "TURN"; st.rerun()
        
        elif st.session_state.finale_phase == "TURN":
            if st.session_state.current_f_idx < len(st.session_state.female_order):
                curr_w = st.session_state.female_order[st.session_state.current_f_idx]
                st.subheader(f"👩 ลำดับที่ {st.session_state.current_f_idx + 1}: {curr_w['name']}")
                st.image(curr_w['img'], width=200)
                suitors = [m for m in st.session_state.cast if m['gender']=='M' and any(v > 0 for v in st.session_state.weights[m['name']].values()) and max(st.session_state.weights[m['name']], key=st.session_state.weights[m['name']].get) == curr_w['name']]
                if not suitors: st.warning("ไม่มีใครเดินออกมาหาเธอ...")
                else:
                    st.success(f"🔥 มีผู้ชาย {len(suitors)} คนเดินออกมาหา!")
                    cols = st.columns(len(suitors))
                    for i, s in enumerate(suitors):
                        cols[i].image(s['img'], width=150); cols[i].write(s['name'])
                    best_m = max(suitors, key=lambda x: st.session_state.weights[curr_w['name']][x['name']])
                    if st.session_state.weights[curr_w['name']][best_m['name']] > 0:
                        st.balloons(); st.markdown(f"### 💖 เธอเลือก **{best_m['name']}**!"); st.session_state.final_couples.append((best_m, curr_w))
                if st.button("คนต่อไป >>"): st.session_state.current_f_idx += 1; st.rerun()
            else: st.session_state.finale_phase = "RESULTS"; st.rerun()

        elif st.session_state.finale_phase == "RESULTS":
            st.header("🏆 ทำเนบคู่รัก & กราฟเส้นทางรัก")
            for m, w in st.session_state.final_couples:
                st.divider()
                c_m, c_h, c_w, c_g = st.columns([1.5, 0.5, 1.5, 4])
                c_m.image(m['img'], width=150, caption=m['name'])
                c_h.markdown("<h1 style='text-align: center; color: red;'>❤️</h1>", unsafe_allow_html=True)
                c_w.image(w['img'], width=150, caption=w['name'])
                with c_g:
                    hist = []
                    for h in st.session_state.score_history:
                        hist.append({"Day": h['day'], f"{m['name']}": h['scores'][m['name']][w['name']], f"{w['name']}": h['scores'][w['name']][m['name']]})
                    st.line_chart(pd.DataFrame(hist).set_index("Day"))
            if st.button("🔄 เริ่มรายการใหม่"): st.session_state.clear(); st.rerun()

    else:
        # --- NORMAL GAMEPLAY ---
        st.title(f"☀️ Inferno Island - DAY {st.session_state.day} / 10")
        
        with st.sidebar:
            st.header("📱 Netizen Feedback")
            st.info(f"💬 {st.session_state.netizen_comment}")
            st.divider()
            st.header(f"💘 Heart Score")
            top_picks = {p['name']: max(st.session_state.weights[p['name']], key=st.session_state.weights[p['name']].get) for p in st.session_state.cast if any(v > 0 for v in st.session_state.weights[p['name']].values())}
            for p in st.session_state.cast:
                name = p['name']
                sorted_sc = sorted(st.session_state.weights[name].items(), key=lambda x: x[1], reverse=True)
                st.write(f"**{name}**")
                for t, v in sorted_sc[:3]:
                    if v > 0: st.caption(f"❤️ {t} ({v} pts)")
                st.divider()

        # แผนผัง & กราฟความฮอต (FIXED: รูปภาพในผัง)
        with st.expander("📊 แผนผังความสัมพันธ์ & กราฟความนิยม", expanded=True):
            if st.session_state.cast:
                col_m1, col_m2 = st.columns([2, 1])
                with col_m1:
                    dot = graphviz.Digraph(); dot.attr(rankdir='LR', bgcolor='#1a1a1a')
                    for p in st.session_state.cast:
                        # เนื่องจาก Graphviz บนเว็บดึงรูปจาก File Upload ไม่ได้ 
                        # พี่เลยแก้ให้มันโชว์เป็น "วงกลมสี" แทนจ้ะ (ชายฟ้า หญิงชมพู)
                        color = "#00a8ff" if p['gender'] == "M" else "#ff4dff"
                        dot.node(p['name'], label=p['name'], color=color, fontcolor="white", style="filled")
                    for c in st.session_state.cast:
                        sc = st.session_state.weights[c['name']]
                        if any(v > 0 for v in sc.values()):
                            t = max(sc, key=sc.get); v = sc[t]
                            if v > 0: dot.edge(c['name'], t, penwidth=str(min(v, 5)), color="#ff4b1f")
                    st.graphviz_chart(dot)
                with col_m2:
                    pop = {p['name']: sum(st.session_state.weights[o['name']][p['name']] for o in st.session_state.cast if o['name']!=p['name']) for p in st.session_state.cast}
                    st.bar_chart(pd.DataFrame(list(pop.items()), columns=['Name', 'Score']).set_index('Name'))

        # 🎬 PRODUCER CONTROL
        st.divider()
        with st.expander("🎬 Producer Control Center", expanded=True):
            t_entry, t_invisible, t_confess = st.tabs(["➕ ส่งสมาชิกเข้าเกาะ", "🖐️ Invisible Hand", "🎤 Confession Room"])
            
            with t_entry:
                active_names = [c['name'] for c in st.session_state.cast]
                waiting_room = [p for p in st.session_state.master_pool if p['name'] not in active_names]
                if waiting_room:
                    to_enter = st.multiselect("เลือกชื่อที่ต้องการส่งเข้าเกาะ:", [p['name'] for p in waiting_room])
                    if st.button("🚀 ส่งสมาชิกเข้าสู่เกาะ"):
                        for name in to_enter:
                            p_obj = next(p for p in waiting_room if p['name'] == name)
                            st.session_state.cast.append(p_obj)
                            st.session_state.logs.append({"type":"System", "txt":f"📢 เปิดตัวสมาชิกใหม่: {p_obj['name']}!"})
                        st.rerun()
                else: st.success("สมาชิกครบ 12 คนแล้วจ้ะ!")

            with t_invisible:
                if st.session_state.cast:
                    inv_c1, inv_c2, inv_c3, inv_c4 = st.columns(4)
                    ps = inv_c1.selectbox("คนส่ง:", active_names)
                    pr = inv_c2.selectbox("คนรับ:", [n for n in active_names if n != ps])
                    pa = inv_c3.selectbox("คำสั่ง:", ["บวกหัวใจ (+2)", "หักหัวใจ (-2)", "ส่งไป Paradise"])
                    if inv_c4.button("⚡ EXECUTE"):
                        if pa == "บวกหัวใจ (+2)": update_rel(ps, pr, 2)
                        elif pa == "หักหัวใจ (-2)": update_rel(ps, pr, -2)
                        else: st.session_state.paradise_visitors.extend([ps, pr])
                        st.rerun()

            with t_confess:
                if st.session_state.cast:
                    cp_name = st.selectbox("เลือกคนสัมภาษณ์:", active_names)
                    c_obj = next(p for p in st.session_state.cast if p['name'] == cp_name)
                    if st.button(f"ฟังสัมภาษณ์ {cp_name}"):
                        sc = st.session_state.weights[cp_name]; val = max(sc.values() or [0]); targ = max(sc, key=sc.get) if val > 0 else "ใครบางคน"
                        prn = "ผม" if c_obj['gender'] == "M" else "ฉัน"
                        st.subheader(f"💬 \"{prn}เริ่มสนใจ {targ} แล้วล่ะ\"")

        # 🕹️ แผงควบคุมกิจกรรม
        st.divider()
        on_is = [c for c in st.session_state.cast if c['name'] not in st.session_state.paradise_visitors]
        has_m = any(c['gender'] == "M" for c in on_is)
        has_f = any(c['gender'] == "F" for c in on_is)

        if st.session_state.day == 10:
            if st.button("💘 FINAL SELECTION", type="primary", use_container_width=True):
                st.session_state.game_over = True; st.session_state.finale_phase = "START"; st.rerun()
        else:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                if has_m and has_f:
                    if st.button("🔥 ทุกคนเดินเกม!"):
                        for p in on_is:
                            opps = [x for x in on_is if x['gender']!=p['gender']]
                            if opps:
                                t = random.choice(opps)
                                update_rel(p['name'], t['name'], 1); update_rel(t['name'], p['name'], 1)
                        st.rerun()
            with c2:
                if len(on_is) >= 4 and has_m and has_f:
                    if st.button("🏆 แข่ง Paradise"):
                        winners = random.sample([c for c in on_is if c['gender'] == random.choice(['M','F'])], 2)
                        for w in winners:
                            avail = [x for x in on_is if x['gender']!=w['gender'] and x['name'] not in st.session_state.paradise_visitors]
                            if avail:
                                pick = random.choice(avail)
                                st.session_state.paradise_visitors.extend([w['name'], pick['name']])
                                update_rel(w['name'], pick['name'], 2); update_rel(pick['name'], w['name'], 2)
                        st.rerun()
            with c3:
                rem = [c for c in on_is if c['name'] not in st.session_state.played_today]
                if has_m and has_f and rem:
                    if st.button(f"🎲 T or D"):
                        actor = random.choice(rem); target = random.choice([c for c in on_is if c['gender']!=actor['gender']])
                        st.session_state.played_today.append(actor['name'])
                        update_rel(actor['name'], target['name'], 1); st.session_state.logs.append({"type":"Game", "p1":actor, "p2":target, "txt":f"🎲 สารภาพรัก"})
                        st.rerun()
            with c4:
                if len(on_is) >= 2:
                    if st.button("✉️ ส่งจดหมาย"):
                        for p in on_is: update_rel(p['name'], max(st.session_state.weights[p['name']], key=st.session_state.weights[p['name']].get), 1)
                        st.rerun()
            with c5:
                if st.button("🌅 จบวัน"):
                    save_daily_history(); st.session_state.day += 1; st.session_state.paradise_visitors = []; st.session_state.played_today = []
                    st.session_state.netizen_comment = get_netizen_comment()
                    st.rerun()

        # 🟢 LOGS
        st.subheader("🎬 บันทึกเหตุการณ์")
        for entry in reversed(st.session_state.logs):
            if entry['type'] == "System": st.info(entry['txt'])
            else:
                with st.container():
                    l, m, r = st.columns([1,4,1])
                    if entry.get('p1'): l.image(entry['p1']['img'], width=80)
                    p1_n = entry['p1']['name'] if entry.get('p1') else ""; p2_n = entry['p2']['name'] if entry.get('p2') else ""
                    m.markdown(f"**{p1_n}** ➔ {entry['txt']} ➔ **{p2_n}**")
                    if entry.get('p2'): r.image(entry['p2']['img'], width=80)
                    st.divider()
