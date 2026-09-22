import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --------------------------
# ตั้งค่าระบบ
# --------------------------
APP_NAME = "FR Motor Bike"
VALID_USERS = {
    "admin": "123456",
    "frmotor": "phuket2026"
}

st.set_page_config(page_title=APP_NAME, layout="wide")

# --------------------------
# เข้าสู่ระบบ
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title(f"🔒 เข้าสู่ระบบ — {APP_NAME}")
    st.markdown("---")
    
    username = st.text_input("👤 ชื่อผู้ใช้")
    password = st.text_input("🔑 รหัสผ่าน", type="password")
    
    if st.button("✅ เข้าสู่ระบบ"):
        if username in VALID_USERS and VALID_USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ เข้าสู่ระบบสำเร็จ!")
            st.rerun()
        else:
            st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    
    st.info("กรุณาใส่ชื่อผู้ใช้และรหัสผ่านเพื่อเข้าใช้งาน")
    st.stop()

# --------------------------
# เมนูหลัก
# --------------------------
st.sidebar.title(f"🏍️ {APP_NAME}")
st.sidebar.write(f"สวัสดีค่ะ, {st.session_state.username}")

if st.sidebar.button("🚪 ออกจากระบบ"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

st.sidebar.markdown("---")

FILE_CARS = "rental_data/cars.csv"
FILE_CUSTOMERS = "rental_data/customers.csv"
FILE_BOOKINGS = "rental_data/bookings.csv"

os.makedirs("rental_data", exist_ok=True)

def init_files():
    for f in [FILE_CARS, FILE_CUSTOMERS, FILE_BOOKINGS]:
        if not os.path.exists(f):
            pd.DataFrame(columns=["รหัสจอง", "รหัสรถ", "รหัสลูกค้า", "วันที่เริ่ม", "วันที่สิ้นสุด", "หมายเหตุ", "วันที่ทำรายการ"]).to_csv(f, index=False, encoding="utf-8-sig")

def load_data(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig")

def save_data(df, path):
    df.to_csv(path, index=False, encoding="utf-8-sig")

def get_next_booking_id():
    df = load_data(FILE_BOOKINGS)
    if df.empty or "รหัสจอง" not in df.columns:
        return "B001"
    nums = df["รหัสจอง"].str.extract(r"(\d+)$")[0].dropna()
    return f"B{nums.astype(int).max()+1:03d}" if not nums.empty else "B001"

init_files()

menu = st.sidebar.radio("เลือกเมนู", [
    "🏍️ จัดการข้อมูลรถ",
    "👤 จัดการข้อมูลลูกค้า",
    "📅 ทำการจอง",
    "📊 ปฏิทินการจอง",
    "📈 รายงานสรุป"
])

st.title(f"🏍️ {APP_NAME}")
st.markdown("ระบบปฏิทินจองรถเช่าอัตโนมัติ")

# ====== จัดการข้อมูลรถ ======
if menu == "🏍️ จัดการข้อมูลรถ":
    st.header("🏍️ ข้อมูลรถ")
    df = load_data(FILE_CARS)
    id_col = "รหัสรถ"
    
    if not df.empty and id_col in df.columns:
        edit_id = st.selectbox("✏️ แก้ไขข้อมูล — เลือกรถ", [""] + list(df[id_col].unique()))
        if edit_id:
            row = df[df[id_col] == edit_id].iloc[0]
            with st.form("edit_car"):
                col1, col2 = st.columns(2)
                with col1:
                    car_id = st.text_input("รหัสรถ", value=row.get("รหัสรถ", ""), disabled=True)
                    name = st.text_input("ชื่อ/รุ่น/สี/ป้าย", value=row.get("ชื่อ/รุ่น/สี/ป้าย", row.get("ยี่ห้อ-รุ่น", "")))
                with col2:
                    status = st.selectbox("สถานะ", ["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"], 
                                          index=["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"].index(row.get("สถานะ", "พร้อมใช้งาน")))
                    note = st.text_input("หมายเหตุ", value=row.get("หมายเหตุ", ""))
                
                if st.form_submit_button("💾 บันทึกการแก้ไข"):
                    df.loc[df[id_col] == edit_id, ["ชื่อ/รุ่น/สี/ป้าย", "สถานะ", "หมายเหตุ"]] = [name, status, note]
                    save_data(df, FILE_CARS)
                    st.success("✅ แก้ไขข้อมูลสำเร็จ")
                    st.rerun()
            st.markdown("---")
    
    with st.form("form_car"):
        col1, col2 = st.columns(2)
        with col1:
            car_id = st.text_input("รหัสรถ (เช่น V001)")
            name = st.text_input("ชื่อ/รุ่น/สี/ป้าย (เช่น Grand Filano สีดำ 1กก 1111)")
        with col2:
            status = st.selectbox("สถานะ", ["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"])
            note = st.text_input("หมายเหตุ")
        
        if st.form_submit_button("✅ เพิ่มรถใหม่"):
            if car_id and name:
                if not df.empty and id_col in df.columns and car_id in df[id_col].values:
                    st.error("❌ รหัสรถนี้มีอยู่แล้ว ใช้ฟังก์ชันแก้ไขด้านบน")
                else:
                    new_row = {"รหัสรถ": car_id, "ชื่อ/รุ่น/สี/ป้าย": name, "สถานะ": status, "หมายเหตุ": note}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df, FILE_CARS)
                    st.success("✅ บันทึกข้อมูลสำเร็จ")
                    st.rerun()
            else:
                st.warning("⚠️ กรุณากรอกรหัสรถและชื่อให้ครบ")
    
    st.subheader("📋 รายการรถทั้งหมด")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        del_id = st.selectbox("🗑️ ลบรายการ — เลือกรถ", [""] + (list(df[id_col].unique()) if id_col in df.columns else []))
        if st.button("🗑️ ลบทันที") and del_id:
            df = df[df[id_col] != del_id]
            save_data(df, FILE_CARS)
            st.success("✅ ลบข้อมูลสำเร็จ")
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลรถ — กรุณาเพิ่มรายการแรกด้านบน")

# ====== จัดการข้อมูลลูกค้า ======
elif menu == "👤 จัดการข้อมูลลูกค้า":
    st.header("👤 ข้อมูลลูกค้า")
    df = load_data(FILE_CUSTOMERS)
    id_col = "รหัสลูกค้า"
    
    if not df.empty and id_col in df.columns:
        edit_id = st.selectbox("✏️ แก้ไขข้อมูล — เลือกลูกค้า", [""] + list(df[id_col].unique()))
        if edit_id:
            row = df[df[id_col] == edit_id].iloc[0]
            with st.form("edit_customer"):
                cid = st.text_input("รหัสลูกค้า", value=row.get("รหัสลูกค้า", ""), disabled=True)
                name = st.text_input("ชื่อลูกค้า", value=row.get("ชื่อลูกค้า", ""))
                phone = st.text_input("เบอร์โทรศัพท์", value=row.get("เบอร์โทรศัพท์", ""))
                if st.form_submit_button("💾 บันทึก"):
                    df.loc[df[id_col] == edit_id, ["ชื่อลูกค้า", "เบอร์โทรศัพท์"]] = [name, phone]
                    save_data(df, FILE_CUSTOMERS)
                    st.success("✅ แก้ไขสำเร็จ")
                    st.rerun()
    
    with st.form("form_customer"):
        cid = st.text_input("รหัสลูกค้า (เช่น C001)")
        name = st.text_input("ชื่อลูกค้า")
        phone = st.text_input("เบอร์โทรศัพท์")
        if st.form_submit_button("✅ เพิ่มลูกค้า"):
            if cid and name:
                new_row = {"รหัสลูกค้า": cid, "ชื่อลูกค้า": name, "เบอร์โทรศัพท์": phone}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df, FILE_CUSTOMERS)
                st.success("✅ บันทึกสำเร็จ")
                st.rerun()
    
    st.subheader("📋 รายการลูกค้า")
    if not df.empty:
        st.dataframe(df, use_container_width=True)

# ====== ทำการจอง ======
elif menu == "📅 ทำการจอง":
    st.header("📅 ทำการจอง")
    df_car = load_data(FILE_CARS)
    df_cust = load_data(FILE_CUSTOMERS)
    
    if df_car.empty or df_cust.empty:
        st.warning("⚠️ กรุณาเพิ่มข้อมูลรถและลูกค้าก่อนทำการจอง")
    else:
        avail_cars = df_car["รหัสรถ"].tolist() if "รหัสรถ" in df_car.columns else []
        customers = df_cust["รหัสลูกค้า"].tolist() if "รหัสลูกค้า" in df_cust.columns else []
        
        with st.form("form_booking"):
            bid = get_next_booking_id()
            st.info(f"รหัสจองถัดไป: {bid}")
            sel_car = st.selectbox("เลือกรถ", avail_cars)
            sel_cust = st.selectbox("เลือกลูกค้า", customers)
            start = st.date_input("วันที่เริ่มเช่า")
            end = st.date_input("วันที่คืนรถ")
            note = st.text_input("หมายเหตุ")
            
            if st.form_submit_button("✅ บันทึกการจอง"):
                if sel_car and sel_cust and start and end:
                    new_row = {
                        "รหัสจอง": bid, "รหัสรถ": sel_car, "รหัสลูกค้า": sel_cust,
                        "วันที่เริ่ม": start, "วันที่สิ้นสุด": end,
                        "หมายเหตุ": note, "วันที่ทำรายการ": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    df_book = load_data(FILE_BOOKINGS)
                    df_book = pd.concat([df_book, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df_book, FILE_BOOKINGS)
                    st.success(f"✅ จองสำเร็จ! รหัสจอง: {bid}")
                    st.rerun()

# ====== ปฏิทินการจองแบบภาพ ======
elif menu == "📊 ปฏิทินการจอง":
    st.header("📊 ระบบปฏิทินจองรถเช่าอัตโนมัติ")
    
    # เลือกเดือน-ปี
    today = datetime.today()
    month = st.selectbox("เลือกเดือน", list(range(1, 13)), index=today.month-1)
    year = st.selectbox("เลือกปี", list(range(2025, 2031)), index=2026-2025)
    
    # จำนวนวันในเดือน
    days_in_month = (datetime(year, month%12+1, 1) - timedelta(days=1)).day
    
    # โหลดข้อมูล
    df_cars = load_data(FILE_CARS)
    df_book = load_data(FILE_BOOKINGS)
    
    if df_cars.empty:
        st.info("กรุณาเพิ่มข้อมูลรถก่อน")
        st.stop()
    
    # สร้างตารางปฏิทิน
    st.markdown(f"### 📅 ปฏิทินการจอง — {month}/{year}")
    
    # ส่วนหัววันที่
    header_cols = ["รหัส", "ชื่อ/รายละเอียด", "สถานะปัจจุบัน"] + [str(d) for d in range(1, days_in_month+1)]
    html = """
    <style>
    .cal-table { border-collapse: collapse; width: 100%; font-size: 12px; }
    .cal-table th, .cal-table td { border: 1px solid #ddd; padding: 4px; text-align: center; height: 32px; }
    .cal-table th { background: #2c3e50; color: white; }
    .cell-red { background: #e74c3c; color: white; }
    .cell-orange { background: #f3d2a2; color: #666; }
    .cell-empty { background: white; }
    .col-fixed { background: #f8f9fa; position: sticky; left: 0; z-index: 1; }
    </style>
    <table class="cal-table">
    <tr>
    """
    for i, col in enumerate(header_cols):
        html += f"<th class='{'col-fixed' if i<3 else ''}'>{col}</th>"
    html += "</tr>"
    
    # แต่ละแถว = 1 รถ
    for _, car in df_cars.iterrows():
        car_id = car.get("รหัสรถ", "")
        car_name = car.get("ชื่อ/รุ่น/สี/ป้าย", car.get("ยี่ห้อ-รุ่น", ""))
        status = car.get("สถานะ", "พร้อมใช้งาน")
        
        html += f"<tr><td class='col-fixed'><strong>{car_id}</strong></td><td class='col-fixed' style='text-align:left'>{car_name}</td><td class='col-fixed'>{status}</td>"
        
        # ดึงช่วงจองของรถนี้
        bookings = []
        if not df_book.empty and "รหัสรถ" in df_book.columns:
            bk_car = df_book[df_book["รหัสรถ"] == car_id]
            for _, bk in bk_car.iterrows():
                try:
                    s = datetime.strptime(str(bk["วันที่เริ่ม"]), "%Y-%m-%d").date()
                    e = datetime.strptime(str(bk["วันที่สิ้นสุด"]), "%Y-%m-%d").date()
                    if s.month == month and s.year == year or e.month == month and e.year == year:
                        bookings.append((s, e))
                except: pass
        
        # เติมแต่ละวัน
        for day in range(1, days_in_month+1):
            d = datetime(year, month, day).date()
            booked = any(s <= d <= e for s, e in bookings)
            
            if status == "กำลังเช่า":
                cls = "cell-red" if booked else "cell-red"
                text = "จอง" if booked else ""
            elif booked:
                cls = "cell-orange"
                text = "จอง"
            else:
                cls = "cell-empty"
                text = ""
            
            html += f"<td class='{cls}'>{text}</td>"
        html += "</tr>"
    
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)
    
    # คำอธิบาย
    st.markdown("---")
    st.markdown("""
    **คำอธิบายสี:**
    🟥 แดง = กำลังเช่า / ไม่ว่าง | 🟧 ส้ม = มีการจอง | ⬜ ขาว = ว่าง
    """)
    
    # ตารางข้อมูลดิบ
    with st.expander("ดูข้อมูลการจองทั้งหมด"):
        if not df_book.empty:
            st.dataframe(df_book, use_container_width=True)
        else:
            st.info("ยังไม่มีการจอง")

# ====== รายงานสรุป ======
elif menu == "📈 รายงานสรุป":
    st.header("📈 รายงานสรุป")
    df_cars = load_data(FILE_CARS)
    df_cust = load_data(FILE_CUSTOMERS)
    df_book = load_data(FILE_BOOKINGS)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🚗 จำนวนรถทั้งหมด", len(df_cars))
    c2.metric("👤 จำนวนลูกค้า", len(df_cust))
    c3.metric("📅 จำนวนการจอง", len(df_book))
    
    st.markdown("---")
    st.subheader("📋 ข้อมูลรถ")
    if not df_cars.empty: st.dataframe(df_cars, use_container_width=True)
    st.subheader("📋 ข้อมูลลูกค้า")
    if not df_cust.empty: st.dataframe(df_cust, use_container_width=True)
    st.subheader("📋 ข้อมูลการจอง")
    if not df_book.empty: st.dataframe(df_book, use_container_width=True)