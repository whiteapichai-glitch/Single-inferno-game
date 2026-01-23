import streamlit as st
import random
import graphviz
import pandas as pd

# --- 💅 1. CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; color: #ffffff; }
    .stButton>button { background-color: #ff4b1f; color: white; border-radius: 10px; border: none; height: 3em; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: #ff9068; color: white; border: 1px solid white; }
    .stExpander { border: 1px solid #ff4b1f; border-radius: 10px; background-color: #262626; }
    h1, h2, h3 { color: #ff9068 !important; }
    .stAlert { background-color: #333333; border: 1px solid #ff4b1f; color: white; }
    .stSidebar { background-color: #000000; border-right: 1px solid #ff4b1f; }
    </style>
    """, unsafe_allow_html=True)

# --- ⚙️ 2. CONFIG ---
MAX_HEART = 15
DEF_M_NAMES = ["บลู", "จุง", "โฟร์ท", "เจษ", "วิน", "เจเจ"]
DEF_F_NAMES = ["ใบเฟิร์น", "เจนเย่", "แพต", "คาริสา", "เนเน่", "วี"]
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
    st.session_state.paradise_visitors = []
    st.session_state.played_today = []
    st.session_state.game_over = False
    st.session_state.finale_phase = None
    st.session_state.final_couples = []

# --- 🧪 4. FUNCTIONS ---
def update_rel(a, b, val):
    if a in st.session_state.weights and b in st.session_state.weights[a]:
        new_score = st.session_state.weights[a][b] + val
        st.session_state.weights[a][b] = max(0, min(new_score, MAX_HEART))

def save_daily_history():
    snapshot = {sender: targets.copy() for sender, targets in st.session_state.weights.items()}
    st.session_state.score_history.append({"day": st.session_state.day, "scores": snapshot})

# --- 🏗️ 5. UI: SETUP ---
if st.session_state.step == "SETUP":
    st.title("🔥 Single's Inferno: Cast Setup")
    st.write("ตั้งชื่อและอัปโหลดรูปสมาชิกทั้ง 12 คน (จะเริ่มด้วยชาย 4 หญิง 4 คนแรกจ้ะ)")
    col1, col2 = st.columns(2)
    m_inputs, f_inputs = [], []
    with col1:
        st.subheader("♂️ Men Pool")
        for i in range(6):
            name = st.text_input(f"ชื่อชาย {i+1}", DEF_M_NAMES[i], key=f"m_n{i}")
            file = st.file_uploader(f"รูป {name}", type=['jpg','png','jpeg'], key=f"m_u{i}")
            m_inputs.append({"name": name, "img": file if file else DEF_M_IMG, "gender": "M", "is_upload": file is not None})
            st.divider()
    with col2:
        st.subheader("♀️ Women Pool")
        for i in range(6):
            name = st.text_input(f"ชื่อหญิง {i+1}", DEF_F_NAMES[i], key=f"f_n{i}")
            file = st.file_uploader(f"รูป {name}", type=['jpg','png','jpeg'], key=f"f_u{i}")
            f_inputs.append({"name": name, "img": file if file else DEF_F_IMG, "gender": "F", "is_upload": file is not None})
            st.divider()

    if st.button("🚀 ยืนยันรายชื่อและเปิดเกาะ"):
        st.session_state.master_pool = m_inputs + f_inputs
        st.session_state.cast = m_inputs[:4] + f_inputs[:4]
        names = [p['name'] for p in st.session_state.master_pool]
        st.session_state.weights = {n: {target: 0 for target in names if target != n} for n in names}
        save_daily_history() 
        st.session_state.logs.append({"type": "System", "txt": "☀️ --- รายการเริ่ม! สมาชิก 8 คนแรกพร้อมแล้ว --- ☀️"})
        st.session_state.step = "GAME"; st.rerun()

# --- 🏝️ 6. UI: GAMEPLAY ---
elif not st.session_state.game_over:
    st.title(f"☀️ Inferno Island - DAY {st.session_state.day} / 10")
    with st.sidebar:
        if st.button("🧹 Reset Game"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        st.divider(); st.header(f"💘 Heart Score")
        for p in st.session_state.cast:
            name = p['name']; sc = sorted(st.session_state.weights[name].items(), key=lambda x: x[1], reverse=True)
            st.write(f"**{name}**")
            for t, v in sc[:2]: 
                if v > 0: st.caption(f"❤️ {t} ({v} pts)")
            st.divider()

    # 📊 แผนผังความสัมพันธ์ (FIXED: พยายามโชว์รูป)
    with st.expander("📊 แผนผังความสัมพันธ์", expanded=True):
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            dot = graphviz.Digraph(); dot.attr(rankdir='LR', bgcolor='#1a1a1a')
            for p in st.session_state.cast:
                color = "#00a8ff" if p['gender'] == "M" else "#ff4dff"
                # ถ้าเป็น URL (รูป Default) จะโชว์รูปในผังจ้ะ
                if not p['is_upload']:
                    dot.node(p['name'], label=f'<<TABLE BORDER="0"><TR><TD FIXEDSIZE="TRUE" WIDTH="40" HEIGHT="40"><IMG SRC="{p["img"]}"/></TD></TR><TR><TD><FONT COLOR="white">{p["name"]}</FONT></TD></TR></TABLE>>', shape="none")
                else:
                    icon = "🤵" if p['gender'] == "M" else "💃"
                    dot.node(p['name'], label=f"{icon} {p['name']}", color=color, fontcolor="white", style="filled")
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
    with st.expander("🎬 Producer Control", expanded=True):
        t_entry, t_invisible, t_confess = st.tabs(["➕ ส่งสมาชิกเพิ่ม", "🖐️ Invisible Hand", "🎤 Confession Room"])
        with t_entry:
            active_names = [c['name'] for c in st.session_state.cast]
            waiting = [p for p in st.session_state.master_pool if p['name'] not in active_names]
            if waiting:
                to_add = st.selectbox("เลือกคนที่จะส่งเข้าเกาะ:", [p['name'] for p in waiting])
                p_obj = next(p for p in waiting if p['name'] == to_add)
                privilege = st.checkbox("⭐ ให้สิทธิ์ Paradise ทันที")
                partner_name = st.selectbox("เลือกคู่เดท:", active_names) if privilege else None
                if st.button(f"🚀 ส่ง {to_add} เข้าเกาะ"):
                    st.session_state.cast.append(p_obj)
                    st.session_state.logs.append({"type": "System", "txt": f"📢 เปิดตัว {to_add} เข้าสู่เกาะ!"})
                    if privilege and partner_name:
                        st.session_state.paradise_visitors.extend([to_add, partner_name])
                        p1, p2 = random.randint(1, 3), random.randint(1, 3)
                        update_rel(to_add, partner_name, p1); update_rel(partner_name, to_add, p2)
                        st.session_state.logs.append({"type":"Paradise", "p1":p_obj, "p2":next(c for c in st.session_state.cast if c['name']==partner_name), "txt":f"สิทธิ์เด็กใหม่ไปสวรรค์! (+{p1} | +{p2})"})
                    st.rerun()
        with t_invisible:
            inv_c1, inv_c2, inv_c3, inv_c4 = st.columns(4)
            ps = inv_c1.selectbox("คนส่ง:", active_names); pr = inv_c2.selectbox("คนรับ:", [n for n in active_names if n != ps])
            pa = inv_c3.selectbox("คำสั่ง:", ["บวกหัวใจ (+2)", "หักหัวใจ (-2)", "ส่งไป Paradise"])
            if inv_c4.button("⚡ EXECUTE"):
                if pa == "บวกหัวใจ (+2)": update_rel(ps, pr, 2)
                elif pa == "หักหัวใจ (-2)": update_rel(ps, pr, -2)
                else: st.session_state.paradise_visitors.extend([ps, pr])
                st.session_state.logs.append({"type":"System", "txt":f"⚡ สั่งการพิเศษ: {ps} -> {pr}!"}); st.rerun()
        with t_confess:
            cp_name = st.selectbox("เลือกคนสัมภาษณ์:", active_names)
            c_obj = next(p for p in st.session_state.cast if p['name'] == cp_name)
            if st.button(f"ฟังสัมภาษณ์ {cp_name}"):
                sc = st.session_state.weights[cp_name]; val = max(sc.values() or [0]); targ = max(sc, key=sc.get) if val > 0 else "ใครบางคน"
                st.subheader(f"💬 \"ตอนนี้เริ่มสนใจ {targ} แล้วล่ะ\"")

    # 🕹️ แผงควบคุมกิจกรรม
    st.divider()
    on_is = [c for c in st.session_state.cast if c['name'] not in st.session_state.paradise_visitors]
    has_m = any(c['gender'] == "M" for c in on_is); has_f = any(c['gender'] == "F" for c in on_is)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("🔥 ทุกคนเดินเกม!", disabled=not (has_m and has_f)):
            st.session_state.logs.append({"type": "System", "txt": f"🌅 DAY {st.session_state.day}: แยกย้ายกันทำคะแนน!"})
            for p in on_is:
                opps = [x for x in on_is if x['gender']!=p['gender']]
                if opps:
                    t = random.choice(opps); p1, p2 = random.choice([0,1]), random.choice([0,1])
                    update_rel(p['name'], t['name'], p1); update_rel(t['name'], p['name'], p2)
                    st.session_state.logs.append({"type":"Beach", "p1":p, "p2":t, "txt":f"คุยริมหาดอย่างใกล้ชิด (+{p1} | +{p2})"})
            st.rerun()
    with c2:
        if st.button("🏆 แข่ง Paradise", disabled=len(on_is) < 4):
            mode = random.choice(['M','F']); el = [c for c in on_is if c['gender']==mode]
            if len(el) >= 2:
                winners = random.sample(el, 2)
                # --- ระบบหึงหวง (Jealousy) ---
                for w in winners:
                    avail = [x for x in on_is if x['gender']!=w['gender'] and x['name'] not in st.session_state.paradise_visitors]
                    if avail:
                        pick = random.choice(avail); st.session_state.paradise_visitors.extend([w['name'], pick['name']])
                        p1, p2 = random.randint(0, 2), random.randint(0, 2)
                        update_rel(w['name'], pick['name'], p1); update_rel(pick['name'], w['name'], p2)
                        st.session_state.logs.append({"type":"Paradise", "p1":w, "p2":pick, "txt":f"ไปสวรรค์ทำคะแนน (+{p1} | +{p2})"})
                # เช็กคนหึง
                for p in on_is:
                    if p['name'] not in st.session_state.paradise_visitors:
                        sc = st.session_state.weights[p['name']]
                        if any(v > 0 for v in sc.values()):
                            crush = max(sc, key=sc.get)
                            if crush in st.session_state.paradise_visitors:
                                update_rel(p['name'], crush, -1)
                                st.session_state.logs.append({"type":"System", "txt":f"💔 {p['name']} หึงที่ {crush} ไปสวรรค์กับคนอื่น! (-1)"})
            st.rerun()
    with c3:
        rem = [c for c in on_is if c['name'] not in st.session_state.played_today]
        if st.button(f"🎲 T or D ({len(rem)})", disabled=not rem):
            a = random.choice(rem); t = random.choice([c for c in on_is if c['gender']!=a['gender']])
            st.session_state.played_today.append(a['name'])
            update_rel(a['name'], t['name'], 1); st.session_state.logs.append({"type":"Game", "p1":a, "p2":t, "txt":f"🎲 สารภาพกลางวง! (+1)"}); st.rerun()
    with c4:
        if st.button("✉️ ส่งจดหมาย"):
            st.session_state.logs.append({"type": "System", "txt": f"✉️ --- คืนวันที่ {st.session_state.day}: พิธีจดหมายนิรนาม ---"})
            for p in on_is:
                sc = st.session_state.weights[p['name']]; target_name = max(sc, key=sc.get) if any(v > 0 for v in sc.values()) else random.choice([x['name'] for x in on_is if x['gender'] != p['gender']])
                update_rel(p['name'], target_name, 1)
                st.session_state.logs.append({"type":"Letter", "p1":p, "p2":next(x for x in st.session_state.cast if x['name'] == target_name), "txt":"ส่งจดหมายบอกความนัย (+1 ฝั่งคนส่ง)"})
            st.rerun()
    with c5:
        if st.button("🌅 จบวัน"):
            save_daily_history(); st.session_state.day += 1; st.session_state.paradise_visitors = []; st.session_state.played_today = []
            if st.session_state.day > 10: st.session_state.game_over = True; st.session_state.finale_phase = "START"
            st.rerun()

    # 🟢 LOGS
    st.subheader("🎬 บันทึกเหตุการณ์")
    for entry in reversed(st.session_state.logs):
        if entry['type'] == "System": st.info(entry['txt'])
        else:
            with st.container():
                l, m, r = st.columns([1,4,1])
                if entry.get('p1'): l.image(entry['p1']['img'], width=80)
                p1_n, p2_n = (entry['p1']['name'] if entry.get('p1') else ""), (entry['p2']['name'] if entry.get('p2') else "")
                m.markdown(f"<div style='text-align: center; padding-top: 20px;'><strong>{p1_n}</strong> ➔ {entry['txt']} ➔ <strong>{p2_n}</strong></div>", unsafe_allow_html=True)
                if entry.get('p2'): r.image(entry['p2']['img'], width=80)
                st.divider()

# --- 💖 7. FINALE ---
else:
    st.title("💖 Final Journey: Selection Zone")
    if st.session_state.finale_phase == "START":
        if st.button("เริ่มพิธีเลือกคู่"):
            women = [p for p in st.session_state.cast if p['gender'] == 'F']; random.shuffle(women); st.session_state.female_order = women
            st.session_state.current_f_idx = 0; st.session_state.finale_phase = "TURN"; st.rerun()
    elif st.session_state.finale_phase == "TURN":
        if st.session_state.current_f_idx < len(st.session_state.female_order):
            curr_w = st.session_state.female_order[st.session_state.current_f_idx]
            st.subheader(f"👩 ลำดับที่ {st.session_state.current_f_idx + 1}: {curr_w['name']}"); st.image(curr_w['img'], width=200)
            suitors = [m for m in st.session_state.cast if m['gender']=='M' and any(v > 0 for v in st.session_state.weights[m['name']].values()) and max(st.session_state.weights[m['name']], key=st.session_state.weights[m['name']].get) == curr_w['name']]
            if suitors:
                st.success(f"ผู้ชาย {len(suitors)} คนเดินออกมาหา!"); cols = st.columns(len(suitors))
                for i, s in enumerate(suitors): cols[i].image(s['img'], width=100); cols[i].write(s['name'])
                best_m = max(suitors, key=lambda x: st.session_state.weights[curr_w['name']][x['name']])
                if st.session_state.weights[curr_w['name']][best_m['name']] > 0:
                    st.balloons(); st.markdown(f"### 💖 เธอเลือก **{best_m['name']}**!"); st.session_state.final_couples.append((best_m, curr_w))
            else: st.warning("ไม่มีใครเดินออกมาหาเธอ...")
            if st.button("คนต่อไป >>"): st.session_state.current_f_idx += 1; st.rerun()
        else: st.session_state.finale_phase = "RESULTS"; st.rerun()
    elif st.session_state.finale_phase == "RESULTS":
        st.header("🏆 ทำเนบคู่รัก & กราฟเส้นทางรัก")
        for m, w in st.session_state.final_couples:
            st.divider(); c1, c2, c3 = st.columns([1,1,3])
            c1.image(m['img'], width=150, caption=m['name']); c2.image(w['img'], width=150, caption=w['name'])
            with c3:
                hist = [{"Day": h['day'], f"{m['name']}": h['scores'][m['name']][w['name']], f"{w['name']}": h['scores'][w['name']][m['name']]} for h in st.session_state.score_history]
                st.line_chart(pd.DataFrame(hist).set_index("Day"))
        if st.button("🔄 เริ่มรายการใหม่"): st.session_state.clear(); st.rerun()
