import streamlit as st
import random
import graphviz
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
    </style>
    """, unsafe_allow_html=True)

# --- ⚙️ 2. CONFIG ---
MAX_HEART = 15

# --- 📦 3. INITIAL STATE & PRESETS ---
# สร้างรายชื่อ 12 คนเตรียมไว้ (ชาย 6 หญิง 6)
DEF_M_IMG = "https://cdn-icons-png.flaticon.com/512/4128/4128176.png"
DEF_F_IMG = "https://cdn-icons-png.flaticon.com/512/6997/6997662.png"

DEFAULT_POOL = [
    {"name": f"ชาย {i+1}", "img": DEF_M_IMG, "gender": "M"} for i in range(6)
] + [
    {"name": f"หญิง {i+1}", "img": DEF_F_IMG, "gender": "F"} for i in range(6)
]

if 'step' not in st.session_state:
    st.session_state.step = "GAME" # ข้ามหน้า Setup ไปหน้าเกมเลย
    st.session_state.master_pool = DEFAULT_POOL
    # เริ่มต้นด้วย ชาย 4 (0-3) และ หญิง 4 (6-9)
    st.session_state.cast = DEFAULT_POOL[0:4] + DEFAULT_POOL[6:10]
    
    names = [p['name'] for p in DEFAULT_POOL]
    st.session_state.weights = {n: {target: 0 for target in names if target != n} for n in names}
    
    st.session_state.score_history = [] 
    st.session_state.day = 1
    st.session_state.logs = [{"type": "System", "txt": "☀️ --- รายการเริ่ม! สมาชิก 8 คนแรกพร้อมแล้ว --- ☀️"}] 
    st.session_state.daily_event = "ปกติ"
    st.session_state.netizen_comment = "ยินดีต้อนรับสู่เกาะนรก ซีซั่นนี้เดือดแน่นอน!"
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

def get_netizen_comment():
    comments = ["คู่นี้เคมีเข้ากันมาก!", "ฉันว่ามีคนกำลังหึง...", "รอดูวันสุดท้ายไม่ไหวแล้ว!", "จะมีรักสามเส้าไหมนะวันนี้?"]
    return random.choice(comments)

# --- 🏝️ 5. UI: GAMEPLAY ---
if not st.session_state.game_over:
    st.title(f"☀️ Inferno Island - DAY {st.session_state.day} / 10")
    
    with st.sidebar:
        if st.button("🧹 ล้างระบบ (เริ่มใหม่หมด)"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        st.divider()
        st.header(f"💘 Heart Score")
        top_picks = {p['name']: max(st.session_state.weights[p['name']], key=st.session_state.weights[p['name']].get) for p in st.session_state.cast if any(v > 0 for v in st.session_state.weights[p['name']].values())}
        for p in st.session_state.cast:
            name = p['name']
            sorted_sc = sorted(st.session_state.weights[name].items(), key=lambda x: x[1], reverse=True)
            tri = " ⚡" if list(top_picks.values()).count(name) >= 2 else ""
            st.write(f"**{name}{tri}**")
            for t, v in sorted_sc[:2]:
                if v > 0: st.caption(f"❤️ {t} ({v} pts)")
            st.divider()

    # แผนผังความสัมพันธ์
    with st.expander("📊 แผนผังความสัมพันธ์", expanded=True):
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            dot = graphviz.Digraph(); dot.attr(rankdir='LR', bgcolor='#1a1a1a')
            for p in st.session_state.cast:
                color = "#00a8ff" if p['gender'] == "M" else "#ff4dff"
                dot.node(p['name'], label=p['name'], color=color, fontcolor="white", style="filled")
            for c in st.session_state.cast:
                sc = st.session_state.weights[c['name']]
                if any(v > 0 for v in sc.values()):
                    t = max(sc, key=sc.get); v = sc[t]
                    if v > 0: dot.edge(c['name'], t, penwidth=str(min(v, 5)), color="#ff4b1f")
            st.graphviz_chart(dot)
        with col_m2:
            st.write("**📈 Popularity Ranking**")
            pop = {p['name']: sum(st.session_state.weights[o['name']][p['name']] for o in st.session_state.cast if o['name']!=p['name']) for p in st.session_state.cast}
            st.bar_chart(pd.DataFrame(list(pop.items()), columns=['Name', 'Score']).set_index('Name'))

    # 🎬 PRODUCER: ส่งคนเข้าเกาะ (FIXED: เพิ่มระบบเลือกคู่ Paradise)
    st.divider()
    with st.expander("🎬 Producer Control: จัดการสมาชิกและสั่งการ", expanded=True):
        t_entry, t_invisible, t_confess = st.tabs(["➕ ส่งสมาชิกเพิ่ม", "🖐️ Invisible Hand", "🎤 Confession Room"])
        
        with t_entry:
            active_names = [c['name'] for c in st.session_state.cast]
            waiting = [p for p in st.session_state.master_pool if p['name'] not in active_names]
            if waiting:
                to_add = st.selectbox("เลือกคนที่จะส่งเข้าเกาะ:", [p['name'] for p in waiting])
                p_obj = next(p for p in waiting if p['name'] == to_add)
                
                privilege = st.checkbox("⭐ ให้สิทธิ์ Paradise ทันที (เลือกคู่เดทด้านล่าง)")
                partner = None
                if privilege:
                    opp_gender = "F" if p_obj['gender'] == "M" else "M"
                    avail_partners = [c['name'] for c in st.session_state.cast if c['gender'] == opp_gender]
                    partner = st.selectbox("เลือกคู่เดทที่จะพาไป Paradise:", avail_partners)

                if st.button(f"🚀 ส่ง {to_add} เข้าเกาะ"):
                    st.session_state.cast.append(p_obj)
                    st.session_state.logs.append({"type": "System", "txt": f"📢 เปิดตัว {to_add} เข้าสู่เกาะ!"})
                    if privilege and partner:
                        st.session_state.paradise_visitors.extend([to_add, partner])
                        update_rel(to_add, partner, 3); update_rel(partner, to_add, 3)
                        p_obj_partner = next(c for c in st.session_state.cast if c['name'] == partner)
                        st.session_state.logs.append({"type":"Paradise", "p1":p_obj, "p2":p_obj_partner, "txt":"ไปสวรรค์ทันที! (+3 | +3)"})
                    st.rerun()
            else: st.success("สมาชิกครบ 12 คนแล้ว!")

        with t_invisible:
            inv1, inv2, inv3, inv4 = st.columns(4)
            ps = inv1.selectbox("คนส่ง:", active_names)
            pr = inv2.selectbox("คนรับ:", [n for n in active_names if n != ps])
            pa = inv3.selectbox("คำสั่ง:", ["บวกหัวใจ (+2)", "หักหัวใจ (-2)", "ส่งไป Paradise"])
            if inv4.button("⚡ EXECUTE"):
                if pa == "บวกหัวใจ (+2)": update_rel(ps, pr, 2)
                elif pa == "หักหัวใจ (-2)": update_rel(ps, pr, -2)
                else: st.session_state.paradise_visitors.extend([ps, pr])
                st.session_state.logs.append({"type":"System", "txt":f"⚡ สั่งการพิเศษ: {ps} -> {pr}!"}); st.rerun()

        with t_confess:
            cp = st.selectbox("เลือกคนสัมภาษณ์:", active_names)
            c_obj = next(p for p in st.session_state.cast if p['name'] == cp)
            if st.button(f"ฟังสัมภาษณ์ {cp}"):
                sc = st.session_state.weights[cp]; val = max(sc.values() or [0]); targ = max(sc, key=sc.get) if val > 0 else "ใครบางคน"
                st.subheader(f"💬 \"ตอนนี้เริ่มสนใจ {targ} แล้วล่ะ\"")

    # 🕹️ แผงควบคุมกิจกรรมประจำวัน (FIXED: เพิ่ม Log ตอนเดินเกม)
    st.divider()
    on_is = [c for c in st.session_state.cast if c['name'] not in st.session_state.paradise_visitors]
    has_m = any(c['gender'] == "M" for c in on_is); has_f = any(c['gender'] == "F" for c in on_is)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("🔥 ทุกคนเดินเกม!", disabled=not (has_m and has_f)):
            st.session_state.logs.append({"type": "System", "txt": f"🌅 DAY {st.session_state.day}: ทุกคนแยกย้ายกันทำคะแนน!"})
            for p in on_is:
                opps = [x for x in on_is if x['gender']!=p['gender']]
                if opps:
                    t = random.choice(opps)
                    p1, p2 = random.choice([0,1]), random.choice([0,1])
                    update_rel(p['name'], t['name'], p1); update_rel(t['name'], p['name'], p2)
                    # เพิ่ม Log ของแต่ละคน
                    st.session_state.logs.append({"type":"Beach", "p1":p, "p2":t, "txt":f"คุยริมหาดอย่างใกล้ชิด (+{p1} | +{p2})"})
            st.rerun()
    with c2:
        if st.button("🏆 แข่ง Paradise", disabled=len(on_is) < 4):
            mode = random.choice(['M','F']); el = [c for c in on_is if c['gender']==mode]
            if len(el) >= 2:
                winners = random.sample(el, 2)
                for w in winners:
                    pick = random.choice([x for x in on_is if x['gender']!=w['gender'] and x['name'] not in st.session_state.paradise_visitors])
                    st.session_state.paradise_visitors.extend([w['name'], pick['name']])
                    update_rel(w['name'], pick['name'], 2); update_rel(pick['name'], w['name'], 2)
                    st.session_state.logs.append({"type":"Paradise", "p1":w, "p2":pick, "txt":"ไปสวรรค์ทำคะแนน (+2 | +2)"})
            st.rerun()
    with c3:
        rem = [c for c in on_is if c['name'] not in st.session_state.played_today]
        if st.button(f"🎲 T or D ({len(rem)})", disabled=not rem):
            a = random.choice(rem); t = random.choice([c for c in on_is if c['gender']!=a['gender']])
            st.session_state.played_today.append(a['name'])
            update_rel(a['name'], t['name'], 1); st.session_state.logs.append({"type":"Game", "p1":a, "p2":t, "txt":f"🎲 สารภาพกลางวง! (+1)"})
            st.rerun()
    with c4:
        if st.button("✉️ ส่งจดหมาย"):
            for p in on_is: update_rel(p['name'], max(st.session_state.weights[p['name']], key=st.session_state.weights[p['name']].get), 1)
            st.session_state.logs.append({"type": "System", "txt": "✉️ ทุกคนส่งจดหมายนิรนามบอกความในใจ!"})
            st.rerun()
    with c5:
        if st.button("🌅 จบวัน"):
            save_daily_history(); st.session_state.day += 1; st.session_state.paradise_visitors = []; st.session_state.played_today = []
            st.session_state.netizen_comment = get_netizen_comment()
            if st.session_state.day > 10: st.session_state.game_over = True; st.session_state.finale_phase = "START"
            st.rerun()

    # 🟢 10. LOGS
    st.subheader("🎬 บันทึกเหตุการณ์")
    for entry in reversed(st.session_state.logs):
        if entry['type'] == "System": st.info(entry['txt'])
        else:
            with st.container():
                l, m, r = st.columns([1,4,1])
                if entry.get('p1'): l.image(entry['p1']['img'], width=70)
                p1_n = entry['p1']['name'] if entry.get('p1') else ""; p2_n = entry['p2']['name'] if entry.get('p2') else ""
                m.markdown(f"<div style='text-align: center; padding-top: 15px;'><strong>{p1_n}</strong> ➔ {entry['txt']} ➔ <strong>{p2_n}</strong></div>", unsafe_allow_html=True)
                if entry.get('p2'): r.image(entry['p2']['img'], width=70)
                st.divider()

# --- 💖 11. FINALE ---
else:
    st.title("💖 Final Journey: Selection Zone")
    if st.session_state.finale_phase == "START":
        if st.button("เริ่มพิธีเลือกคู่"):
            women = [p for p in st.session_state.cast if p['gender'] == 'F']
            random.shuffle(women); st.session_state.female_order = women
            st.session_state.current_f_idx = 0; st.session_state.finale_phase = "TURN"; st.rerun()
    elif st.session_state.finale_phase == "TURN":
        if st.session_state.current_f_idx < len(st.session_state.female_order):
            curr_w = st.session_state.female_order[st.session_state.current_f_idx]
            st.subheader(f"👩 ลำดับที่ {st.session_state.current_f_idx + 1}: {curr_w['name']}")
            st.image(curr_w['img'], width=200)
            suitors = [m for m in st.session_state.cast if m['gender']=='M' and any(v > 0 for v in st.session_state.weights[m['name']].values()) and max(st.session_state.weights[m['name']], key=st.session_state.weights[m['name']].get) == curr_w['name']]
            if suitors:
                st.success(f"ผู้ชาย {len(suitors)} คนเดินออกมาหา!")
                cols = st.columns(len(suitors))
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
            st.divider()
            c1, c2, c3 = st.columns([1,1,3])
            c1.image(m['img'], width=150, caption=m['name'])
            c2.image(w['img'], width=150, caption=w['name'])
            with c3:
                hist = [{"Day": h['day'], f"{m['name']}": h['scores'][m['name']][w['name']], f"{w['name']}": h['scores'][w['name']][m['name']]} for h in st.session_state.score_history]
                st.line_chart(pd.DataFrame(hist).set_index("Day"))
        if st.button("🔄 เริ่มรายการใหม่"): st.session_state.clear(); st.rerun()
