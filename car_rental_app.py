import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --------------------------
# ตั้งค่าชื่อระบบและบัญชีผู้ใช้
# --------------------------
APP_NAME = "FR Motor Bike"
# ✅ ตั้งค่าบัญชี — สามารถเปลี่ยนได้ตามต้องการ
VALID_USERS = {
    "admin": "123456",       # ชื่อ: admin , รหัส: 123456
    "frmotor": "phuket2026"  # เพิ่มผู้ใช้อีกคนได้ตามต้องการ
}

# --------------------------
# ตรวจสอบการเข้าสู่ระบบ
# --------------------------
st.set_page_config(page_title=APP_NAME, layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# หากยังไม่เข้าสู่ระบบ แสดงหน้าล็อกอิน
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
    st.stop()  # หยุดทำงานส่วนอื่น ถ้ายังไม่ล็อกอิน

# --------------------------
# ถ้าเข้าสู่ระบบแล้ว — โหลดส่วนทำงาน
# --------------------------
st.sidebar.title(f"🏍️ {APP_NAME}")
st.sidebar.write(f"สวัสดีค่ะ, {st.session_state.username}")

# ปุ่มออกจากระบบ
if st.sidebar.button("🚪 ออกจากระบบ"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

st.sidebar.markdown("---")

# ==== ตั้งค่าไฟล์ข้อมูล ====
FILE_CARS = "rental_data/cars.csv"
FILE_CUSTOMERS = "rental_data/customers.csv"
FILE_BOOKINGS = "rental_data/bookings.csv"

os.makedirs("rental_data", exist_ok=True)

def init_files():
    for f in [FILE_CARS, FILE_CUSTOMERS, FILE_BOOKINGS]:
        if not os.path.exists(f):
            pd.DataFrame().to_csv(f, index=False, encoding="utf-8-sig")

def load_data(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig")

def save_data(df, path):
    df.to_csv(path, index=False, encoding="utf-8-sig")

def get_next_booking_id():
    if not os.path.exists(FILE_BOOKINGS):
        return "B001"
    df = load_data(FILE_BOOKINGS)
    if df.empty or "รหัสจอง" not in df.columns:
        return "B001"
    nums = df["รหัสจอง"].str.extract(r"(\d+)$")
    nums = nums[0].dropna()
    if nums.empty:
        return "B001"
    last = nums.astype(int).max()
    return f"B{last+1:03d}"

init_files()

# ==== เมนูหลัก ====
menu = st.sidebar.radio("เลือกเมนู", [
    "🏍️ จัดการข้อมูลรถ",
    "👤 จัดการข้อมูลลูกค้า",
    "📅 ทำการจอง",
    "📊 ปฏิทินจอง",
    "📈 รายงานสรุป"
])

# ==== หน้าหลัก ====
st.title(f"🏍️ {APP_NAME}")
st.markdown("ระบบจัดการข้อมูลและการเช่ารถจักรยานยนต์")

# ====== จัดการข้อมูลรถ ======
if menu == "🏍️ จัดการข้อมูลรถ":
    st.header("🏍️ ข้อมูลรถ")
    df = load_data(FILE_CARS)
    
    with st.form("form_car"):
        col1, col2 = st.columns(2)
        with col1:
            car_id = st.text_input("รหัสรถ")
            brand = st.text_input("ยี่ห้อ-รุ่น")
            plate = st.text_input("ป้ายทะเบียน")
        with col2:
            price = st.text_input("ราคาต่อวัน")
            status = st.selectbox("สถานะ", ["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"])
            note = st.text_input("หมายเหตุ")
        
        if st.form_submit_button("✅ เพิ่มรถ"):
            if car_id and brand and price:
                if car_id in df["รหัสรถ"].values if "รหัสรถ" in df.columns else False:
                    st.error("❌ รหัสรถนี้มีอยู่แล้ว")
                else:
                    new_row = {
                        "รหัสรถ": car_id, "ยี่ห้อ-รุ่น": brand, "ป้ายทะเบียน": plate,
                        "ราคาต่อวัน": price, "สถานะ": status, "หมายเหตุ": note
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df, FILE_CARS)
                    st.success("✅ บันทึกข้อมูลสำเร็จ")
                    st.rerun()
            else:
                st.warning("⚠️ กรุณากรอกข้อมูลที่จำเป็น")
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.subheader("🗑️ ลบรายการ")
        del_id = st.selectbox("เลือกรถที่ต้องการลบ", [""] + list(df["รหัสรถ"].unique()) if "รหัสรถ" in df.columns else [])
        if st.button("🗑️ ลบรายการนี้") and del_id:
            df = df[df["รหัสรถ"] != del_id]
            save_data(df, FILE_CARS)
            st.success("✅ ลบข้อมูลสำเร็จ")
            st.rerun()

# ====== จัดการข้อมูลลูกค้า ======
elif menu == "👤 จัดการข้อมูลลูกค้า":
    st.header("👤 ข้อมูลลูกค้า")
    df = load_data(FILE_CUSTOMERS)
    
    with st.form("form_customer"):
        cid = st.text_input("รหัสลูกค้า")
        name = st.text_input("ชื่อลูกค้า")
        phone = st.text_input("เบอร์โทรศัพท์")
        addr = st.text_area("ที่อยู่")
        if st.form_submit_button("✅ เพิ่มลูกค้า"):
            if cid and name:
                if cid in df["รหัสลูกค้า"].values if "รหัสลูกค้า" in df.columns else False:
                    st.error("❌ รหัสลูกค้านี้มีอยู่แล้ว")
                else:
                    new_row = {"รหัสลูกค้า": cid, "ชื่อลูกค้า": name, "เบอร์โทรศัพท์": phone, "ที่อยู่": addr}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df, FILE_CUSTOMERS)
                    st.success("✅ บันทึกข้อมูลสำเร็จ")
                    st.rerun()
            else:
                st.warning("⚠️ กรุณากรอกข้อมูลที่จำเป็น")
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.subheader("🗑️ ลบรายการ")
        del_id = st.selectbox("เลือกลูกค้าที่ต้องการลบ", [""] + list(df["รหัสลูกค้า"].unique()) if "รหัสลูกค้า" in df.columns else [])
        if st.button("🗑️ ลบรายการนี้") and del_id:
            df = df[df["รหัสลูกค้า"] != del_id]
            save_data(df, FILE_CUSTOMERS)
            st.success("✅ ลบข้อมูลสำเร็จ")
            st.rerun()

# ====== ทำการจอง ======
elif menu == "📅 ทำการจอง":
    st.header("📅 ทำการจอง")
    df_car = load_data(FILE_CARS)
    df_cust = load_data(FILE_CUSTOMERS)
    
    if df_car.empty or df_cust.empty:
        st.warning("⚠️ กรุณาเพิ่มข้อมูลรถและลูกค้าก่อนทำการจอง")
    else:
        avail_cars = df_car[df_car["สถานะ"] == "พร้อมใช้งาน"]["รหัสรถ"].tolist() if "สถานะ" in df_car.columns else []
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
                        "วันที่เริ่ม": start, "วันที่สิ้นสุด": end, "หมายเหตุ": note,
                        "วันที่ทำรายการ": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    df_book = load_data(FILE_BOOKINGS)
                    df_book = pd.concat([df_book, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df_book, FILE_BOOKINGS)
                    st.success(f"✅ จองสำเร็จ! รหัสจอง: {bid}")
                    st.rerun()
                else:
                    st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")

# ====== ปฏิทินจอง ======
elif menu == "📊 ปฏิทินจอง":
    st.header("📊 ปฏิทินการจอง")
    df = load_data(FILE_BOOKINGS)
    if df.empty:
        st.info("ยังไม่มีข้อมูลการจอง")
    else:
        st.dataframe(df, use_container_width=True)

# ====== รายงานสรุป ======
elif menu == "📈 รายงานสรุป":
    st.header("📈 รายงานสรุป")
    c1, c2, c3 = st.columns(3)
    c1.metric("จำนวนรถทั้งหมด", len(load_data(FILE_CARS)))
    c2.metric("จำนวนลูกค้า", len(load_data(FILE_CUSTOMERS)))
    c3.metric("จำนวนการจอง", len(load_data(FILE_BOOKINGS)))