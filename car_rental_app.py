import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --------------------------
# ตั้งค่าชื่อระบบและบัญชีผู้ใช้
# --------------------------
APP_NAME = "FR Motor Bike"
VALID_USERS = {
    "admin": "123456",
    "frmotor": "phuket2026"
}

# --------------------------
# ตรวจสอบการเข้าสู่ระบบ
# --------------------------
st.set_page_config(page_title=APP_NAME, layout="wide")

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

menu = st.sidebar.radio("เลือกเมนู", [
    "🏍️ จัดการข้อมูลรถ",
    "👤 จัดการข้อมูลลูกค้า",
    "📅 ทำการจอง",
    "📊 ปฏิทินการจอง",
    "📈 รายงานสรุป"
])

st.title(f"🏍️ {APP_NAME}")
st.markdown("ระบบจัดการข้อมูลและการเช่ารถจักรยานยนต์")

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
                    brand = st.text_input("ยี่ห้อ-รุ่น", value=row.get("ยี่ห้อ-รุ่น", ""))
                    plate = st.text_input("ป้ายทะเบียน", value=row.get("ป้ายทะเบียน", ""))
                with col2:
                    price = st.text_input("ราคาต่อวัน", value=row.get("ราคาต่อวัน", ""))
                    status = st.selectbox("สถานะ", ["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"], 
                                          index=["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"].index(row.get("สถานะ", "พร้อมใช้งาน")))
                    note = st.text_input("หมายเหตุ", value=row.get("หมายเหตุ", ""))
                
                if st.form_submit_button("💾 บันทึกการแก้ไข"):
                    df.loc[df[id_col] == edit_id, ["ยี่ห้อ-รุ่น", "ป้ายทะเบียน", "ราคาต่อวัน", "สถานะ", "หมายเหตุ"]] = [
                        brand, plate, price, status, note
                    ]
                    save_data(df, FILE_CARS)
                    st.success("✅ แก้ไขข้อมูลสำเร็จ")
                    st.rerun()
            st.markdown("---")
    
    with st.form("form_car"):
        col1, col2 = st.columns(2)
        with col1:
            car_id = st.text_input("รหัสรถ (ใหม่)")
            brand = st.text_input("ยี่ห้อ-รุ่น")
            plate = st.text_input("ป้ายทะเบียน")
        with col2:
            price = st.text_input("ราคาต่อวัน")
            status = st.selectbox("สถานะ", ["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"])
            note = st.text_input("หมายเหตุ")
        
        if st.form_submit_button("✅ เพิ่มรถใหม่"):
            if car_id and brand and price:
                if not df.empty and id_col in df.columns and car_id in df[id_col].values:
                    st.error("❌ รหัสรถนี้มีอยู่แล้ว ใช้ฟังก์ชันแก้ไขด้านบน")
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
    
    st.subheader("📋 รายการรถทั้งหมด")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.subheader("🗑️ ลบรายการ")
        del_id = st.selectbox("เลือกรถที่ต้องการลบ", [""] + (list(df[id_col].unique()) if id_col in df.columns else []))
        if st.button("🗑️ ลบรายการนี้") and del_id:
            df = df[df[id_col] != del_id]
            save_data(df, FILE_CARS)
            st.success("✅ ลบข้อมูลสำเร็จ")
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลรถ")

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
                addr = st.text_area("ที่อยู่", value=row.get("ที่อยู่", ""))
                
                if st.form_submit_button("💾 บันทึกการแก้ไข"):
                    df.loc[df[id_col] == edit_id, ["ชื่อลูกค้า", "เบอร์โทรศัพท์", "ที่อยู่"]] = [name, phone, addr]
                    save_data(df, FILE_CUSTOMERS)
                    st.success("✅ แก้ไขข้อมูลสำเร็จ")
                    st.rerun()
            st.markdown("---")
    
    with st.form("form_customer"):
        cid = st.text_input("รหัสลูกค้า (ใหม่)")
        name = st.text_input("ชื่อลูกค้า")
        phone = st.text_input("เบอร์โทรศัพท์")
        addr = st.text_area("ที่อยู่")
        if st.form_submit_button("✅ เพิ่มลูกค้าใหม่"):
            if cid and name:
                if not df.empty and id_col in df.columns and cid in df[id_col].values:
                    st.error("❌ รหัสลูกค้านี้มีอยู่แล้ว ใช้ฟังก์ชันแก้ไขด้านบน")
                else:
                    new_row = {"รหัสลูกค้า": cid, "ชื่อลูกค้า": name, "เบอร์โทรศัพท์": phone, "ที่อยู่": addr}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df, FILE_CUSTOMERS)
                    st.success("✅ บันทึกข้อมูลสำเร็จ")
                    st.rerun()
            else:
                st.warning("⚠️ กรุณากรอกข้อมูลที่จำเป็น")
    
    st.subheader("📋 รายการลูกค้าทั้งหมด")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.subheader("🗑️ ลบรายการ")
        del_id = st.selectbox("เลือกลูกค้าที่ต้องการลบ", [""] + (list(df[id_col].unique()) if id_col in df.columns else []))
        if st.button("🗑️ ลบรายการนี้") and del_id:
            df = df[df[id_col] != del_id]
            save_data(df, FILE_CUSTOMERS)
            st.success("✅ ลบข้อมูลสำเร็จ")
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลลูกค้า")

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
                        "รหัสจอง": bid,
                        "รหัสรถ": sel_car,
                        "รหัสลูกค้า": sel_cust,
                        "วันที่เริ่ม": start,
                        "วันที่สิ้นสุด": end,
                        "หมายเหตุ": note,
                        "วันที่ทำรายการ": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    df_book = load_data(FILE_BOOKINGS)
                    df_book = pd.concat([df_book, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df_book, FILE_BOOKINGS)
                    st.success(f"✅ จองสำเร็จ! รหัสจอง: {bid}")
                    st.rerun()
                else:
                    st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")

# ====== ปฏิทินการจอง ======
elif menu == "📊 ปฏิทินการจอง":
    st.header("📊 ปฏิทินการจอง")
    df = load_data(FILE_BOOKINGS)
    
    if df.empty:
        st.info("ยังไม่มีข้อมูลการจอง")
    else:
        desired_order = ["รหัสจอง", "รหัสรถ", "รหัสลูกค้า", "วันที่เริ่ม", "วันที่สิ้นสุด", "หมายเหตุ", "วันที่ทำรายการ"]
        existing_cols = [c for c in desired_order if c in df.columns]
        other_cols = [c for c in df.columns if c not in desired_order]
        df = df[existing_cols + other_cols]
        
        st.dataframe(df, use_container_width=True)
        
        st.subheader("🗑️ ลบรายการจอง")
        if "รหัสจอง" in df.columns:
            del_id = st.selectbox("เลือกรหัสจองที่ต้องการลบ", [""] + list(df["รหัสจอง"].unique()))
            if st.button("🗑️ ลบรายการนี้") and del_id:
                df = df[df["รหัสจอง"] != del_id]
                save_data(df, FILE_BOOKINGS)
                st.success("✅ ลบข้อมูลสำเร็จ")
                st.rerun()

# ====== รายงานสรุป ======
elif menu == "📈 รายงานสรุป":
    st.header("📈 รายงานสรุป")
    
    df_cars = load_data(FILE_CARS)
    df_cust = load_data(FILE_CUSTOMERS)
    df_book = load_data(FILE_BOOKINGS)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🚗 จำนวนรถทั้งหมด", len(df_cars))
    with col2:
        st.metric("👤 จำนวนลูกค้า", len(df_cust))
    with col3:
        st.metric("📅 จำนวนการจอง", len(df_book))
    
    st.markdown("---")
    
    st.subheader("📋 ข้อมูลรถทั้งหมด")
    if not df_cars.empty:
        st.dataframe(df_cars, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลรถ")
    
    st.markdown("---")
    
    st.subheader("📋 ข้อมูลลูกค้าทั้งหมด")
    if not df_cust.empty:
        st.dataframe(df_cust, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลลูกค้า")
    
    st.markdown("---")
    
    st.subheader("📋 ข้อมูลการจองทั้งหมด")
    if not df_book.empty:
        desired_order = ["รหัสจอง", "รหัสรถ", "รหัสลูกค้า", "วันที่เริ่ม", "วันที่สิ้นสุด", "หมายเหตุ", "วันที่ทำรายการ"]
        existing_cols = [c for c in desired_order if c in df_book.columns]
        other_cols = [c for c in df_book.columns if c not in desired_order]
        df_book = df_book[existing_cols + other_cols]
        st.dataframe(df_book, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลการจอง")