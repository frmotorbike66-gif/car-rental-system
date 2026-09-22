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
    for f, cols in [
        (FILE_CARS, ["รหัสรถ", "ยี่ห้อ-รุ่น/ป้าย", "ราคาต่อวัน", "สถานะ", "หมายเหตุ"]),
        (FILE_CUSTOMERS, ["ชื่อ-นามสกุล", "เบอร์โทร", "ที่อยู่"]),
        (FILE_BOOKINGS, ["รหัสจอง", "รหัสรถ", "ชื่อลูกค้า", 
                         "วันที่เริ่ม", "เวลาเริ่ม", 
                         "วันที่คืน", "เวลาคืน", 
                         "จำนวนวัน", "ค่าเช่ารวม", "เงินมัดจำ", "หมายเหตุ", "วันที่ทำรายการ"])
    ]:
        if not os.path.exists(f):
            pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8-sig")

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

# ✅ สูตรที่ถูกต้อง: 24ชม./วัน + อนุโลม 2ชม. เฉพาะเวลาคืน
def calculate_days_by_hour(start_date, start_time, end_date, end_time):
    try:
        start_dt = datetime.combine(pd.to_datetime(start_date).date(), start_time)
        end_dt = datetime.combine(pd.to_datetime(end_date).date(), end_time)
        
        total_hours = (end_dt - start_dt).total_seconds() / 3600
        
        # คำนวณ: วันเต็ม + ตรวจสอบชม.ที่เกินเวลาคืน
        days_full = int(total_hours // 24)           # จำนวนวันเต็ม
        remainder = total_hours % 24                  # ชม.ที่เหลือหลังจากวันเต็ม
        grace = 2                                     # อนุโลมให้เกินได้ 2 ชม.
        
        if remainder <= grace:
            days = days_full if days_full > 0 else 1
        else:
            days = days_full + 1
        
        # อย่างน้อยต้องเป็น 1 วัน
        days = max(1, days)
        
        return days, round(total_hours, 1)
    except Exception as e:
        return 1, 0

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
    
    if not df.empty and "รหัสรถ" in df.columns:
        edit_id = st.selectbox("✏️ แก้ไขข้อมูล — เลือกรถ", [""] + list(df["รหัสรถ"].unique()))
        if edit_id:
            row = df[df["รหัสรถ"] == edit_id].iloc[0]
            with st.form("edit_car"):
                col1, col2 = st.columns(2)
                with col1:
                    car_id = st.text_input("รหัสรถ", value=row.get("รหัสรถ", ""), disabled=True)
                    name = st.text_input("ชื่อ/รุ่น/สี/ป้าย", value=row.get("ยี่ห้อ-รุ่น/ป้าย", ""))
                with col2:
                    price = st.number_input("ราคาต่อวัน (บาท)", min_value=0, value=int(float(row.get("ราคาต่อวัน", 300) or 300)))
                    status = st.selectbox("สถานะ", ["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"], 
                                          index=["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"].index(row.get("สถานะ", "พร้อมใช้งาน")))
                    note = st.text_input("หมายเหตุ", value=row.get("หมายเหตุ", ""))
                
                if st.form_submit_button("💾 บันทึกการแก้ไข"):
                    df.loc[df["รหัสรถ"] == edit_id, ["ยี่ห้อ-รุ่น/ป้าย", "ราคาต่อวัน", "สถานะ", "หมายเหตุ"]] = [name, price, status, note]
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
            price = st.number_input("ราคาต่อวัน (บาท)", min_value=0, value=300)
            status = st.selectbox("สถานะ", ["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"])
            note = st.text_input("หมายเหตุ")
        
        if st.form_submit_button("✅ เพิ่มรถใหม่"):
            if car_id and name:
                if not df.empty and "รหัสรถ" in df.columns and car_id in df["รหัสรถ"].values:
                    st.error("❌ รหัสรถนี้มีอยู่แล้ว ใช้ฟังก์ชันแก้ไขด้านบน")
                else:
                    new_row = {"รหัสรถ": car_id, "ยี่ห้อ-รุ่น/ป้าย": name, "ราคาต่อวัน": price, "สถานะ": status, "หมายเหตุ": note}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df, FILE_CARS)
                    st.success("✅ บันทึกข้อมูลสำเร็จ")
                    st.rerun()
            else:
                st.warning("⚠️ กรุณากรอกรหัสรถและชื่อให้ครบ")
    
    st.subheader("📋 รายการรถทั้งหมด")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        del_id = st.selectbox("🗑️ ลบรายการ — เลือกรถ", [""] + (list(df["รหัสรถ"].unique()) if "รหัสรถ" in df.columns else []))
        if st.button("🗑️ ลบทันที") and del_id:
            df = df[df["รหัสรถ"] != del_id]
            save_data(df, FILE_CARS)
            st.success("✅ ลบข้อมูลสำเร็จ")
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลรถ — กรุณาเพิ่มรายการแรกด้านบน")

# ====== จัดการข้อมูลลูกค้า ======
elif menu == "👤 จัดการข้อมูลลูกค้า":
    st.header("👤 ข้อมูลลูกค้า")
    df = load_data(FILE_CUSTOMERS)
    desired_cols = ["ชื่อ-นามสกุล", "เบอร์โทร", "ที่อยู่"]
    df = df[[c for c in desired_cols if c in df.columns]].copy()
    
    if not df.empty:
        edit_idx = st.selectbox("✏️ แก้ไขข้อมูล — เลือกลูกค้า", [""] + list(df.index + 1), format_func=lambda x: "เลือก..." if x=="" else f"รายการที่ {x}")
        if edit_idx:
            row = df.iloc[int(edit_idx)-1]
            with st.form("edit_customer"):
                name = st.text_input("ชื่อ-นามสกุล", value=row.get("ชื่อ-นามสกุล", ""))
                phone = st.text_input("เบอร์โทร", value=row.get("เบอร์โทร", ""))
                addr = st.text_area("ที่อยู่", value=row.get("ที่อยู่", ""))
                if st.form_submit_button("💾 บันทึกการแก้ไข"):
                    df.loc[int(edit_idx)-1] = {"ชื่อ-นามสกุล": name, "เบอร์โทร": phone, "ที่อยู่": addr}
                    save_data(df, FILE_CUSTOMERS)
                    st.success("✅ แก้ไขข้อมูลสำเร็จ")
                    st.rerun()
            st.markdown("---")
    
    with st.form("form_customer"):
        name = st.text_input("ชื่อ-นามสกุล")
        phone = st.text_input("เบอร์โทร")
        addr = st.text_area("ที่อยู่")
        if st.form_submit_button("✅ เพิ่มลูกค้า"):
            if name:
                new_row = {"ชื่อ-นามสกุล": name, "เบอร์โทร": phone, "ที่อยู่": addr}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df, FILE_CUSTOMERS)
                st.success("✅ บันทึกข้อมูลสำเร็จ")
                st.rerun()
            else:
                st.warning("⚠️ กรุณากรอกชื่อ-นามสกุล")
    
    st.subheader("📋 รายการลูกค้าทั้งหมด")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        del_idx = st.selectbox("🗑️ ลบรายการ — เลือกลูกค้า", [""] + list(df.index + 1), format_func=lambda x: "เลือก..." if x=="" else f"รายการที่ {x}")
        if st.button("🗑️ ลบทันที") and del_idx:
            df = df.drop(int(del_idx)-1).reset_index(drop=True)
            save_data(df, FILE_CUSTOMERS)
            st.success("✅ ลบข้อมูลสำเร็จ")
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลลูกค้า")

# ====== ทำการจอง — สูตรใหม่ ======
elif menu == "📅 ทำการจอง":
    st.header("📅 ทำการจอง")
    df_car = load_data(FILE_CARS)
    df_cust = load_data(FILE_CUSTOMERS)
    
    if df_car.empty or df_cust.empty:
        st.warning("⚠️ กรุณาเพิ่มข้อมูลรถและลูกค้าก่อนทำการจอง")
    else:
        avail_cars = df_car["รหัสรถ"].tolist() if "รหัสรถ" in df_car.columns else []
        cust_names = df_cust["ชื่อ-นามสกุล"].tolist() if "ชื่อ-นามสกุล" in df_cust.columns else []
        
        with st.form("form_booking"):
            bid = get_next_booking_id()
            st.info(f"รหัสจองถัดไป: {bid}")
            
            sel_car = st.selectbox("เลือกรถ", avail_cars)
            sel_cust = st.selectbox("เลือกลูกค้า", cust_names)
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("วันที่เริ่มเช่า")
                start_time = st.time_input("เวลาเริ่มเช่า", value=datetime.strptime("09:00", "%H:%M").time())
            with col2:
                end_date = st.date_input("วันที่คืนรถ")
                end_time = st.time_input("เวลาคืนรถ", value=datetime.strptime("18:00", "%H:%M").time())
            
            price_per_day = 0
            days = 1
            total_price = 0
            total_hours = 0
            if sel_car and "ราคาต่อวัน" in df_car.columns:
                car_row = df_car[df_car["รหัสรถ"] == sel_car]
                if not car_row.empty:
                    price_per_day = float(car_row.iloc[0]["ราคาต่อวัน"])
                    days, total_hours = calculate_days_by_hour(start_date, start_time, end_date, end_time)
                    total_price = price_per_day * days
                    st.info(f"💰 ราคาต่อวัน: {price_per_day:,.0f} บาท | ช่วงเวลา: {total_hours:.1f} ชม. | จำนวนวัน: {days} วัน | **ค่าเช่ารวม: {total_price:,.0f} บาท**\n💡 24 ชม./วัน คืนล่าช้าได้ไม่เกิน 2 ชม.")
            
            deposit = st.text_input("💰 เงินมัดจำ (บาท)", placeholder="เช่น 500")
            note = st.text_input("หมายเหตุ")
            
            if st.form_submit_button("✅ บันทึกการจอง"):
                if sel_car and sel_cust and start_date and end_date:
                    days, _ = calculate_days_by_hour(start_date, start_time, end_date, end_time)
                    car_row = df_car[df_car["รหัสรถ"] == sel_car]
                    price_per_day = float(car_row.iloc[0]["ราคาต่อวัน"]) if not car_row.empty else 0
                    total_price = price_per_day * days
                    
                    new_row = {
                        "รหัสจอง": bid,
                        "รหัสรถ": sel_car,
                        "ชื่อลูกค้า": sel_cust,
                        "วันที่เริ่ม": start_date,
                        "เวลาเริ่ม": start_time.strftime("%H:%M"),
                        "วันที่คืน": end_date,
                        "เวลาคืน": end_time.strftime("%H:%M"),
                        "จำนวนวัน": days,
                        "ค่าเช่ารวม": f"{total_price:.0f}",
                        "เงินมัดจำ": deposit,
                        "หมายเหตุ": note,
                        "วันที่ทำรายการ": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    df_book = load_data(FILE_BOOKINGS)
                    df_book = pd.concat([df_book, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df_book, FILE_BOOKINGS)
                    st.success(f"✅ จองสำเร็จ! รหัสจอง: {bid} | {total_hours:.1f} ชม. = {days} วัน | รวม {total_price:,.0f} บาท")
                    st.balloons()
                    st.rerun()
                else:
                    st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
    
    st.markdown("---")
    st.subheader("📋 รายการจองทั้งหมด")
    df_book = load_data(FILE_BOOKINGS)
    
    if not df_book.empty:
        display_cols = ["รหัสจอง", "รหัสรถ", "ชื่อลูกค้า", 
                        "วันที่เริ่ม", "เวลาเริ่ม", "วันที่คืน", "เวลาคืน",
                        "จำนวนวัน", "ค่าเช่ารวม", "เงินมัดจำ", "หมายเหตุ"]
        cols = [c for c in display_cols if c in df_book.columns]
        st.dataframe(df_book[cols], use_container_width=True)
        
        st.markdown("#### 🗑️ ลบรายการจอง")
        del_booking = st.selectbox("เลือกรหัสจองที่ต้องการลบ", [""] + list(df_book["รหัสจอง"].unique()))
        if st.button("🗑️ ลบรายการนี้") and del_booking:
            df_book = df_book[df_book["รหัสจอง"] != del_booking]
            save_data(df_book, FILE_BOOKINGS)
            st.success("✅ ลบรายการสำเร็จ")
            st.rerun()
    else:
        st.info("ยังไม่มีรายการจอง")

# ====== ปฏิทินการจอง ======
elif menu == "📊 ปฏิทินการจอง":
    st.header("📊 ปฏิทินการจอง")
    
    today = datetime.today()
    month = st.selectbox("เลือกเดือน", list(range(1, 13)), index=today.month-1)
    year = st.selectbox("เลือกปี", list(range(2025, 2031)), index=2026-2025)
    
    days_in_month = (datetime(year, month%12+1, 1) - timedelta(days=1)).day
    
    df_cars = load_data(FILE_CARS)
    df_book = load_data(FILE_BOOKINGS)
    
    if df_cars.empty:
        st.info("กรุณาเพิ่มข้อมูลรถก่อน")
        st.stop()
    
    st.markdown(f"### 📅 ปฏิทินการจอง — {month}/{year}")
    
    header_cols = ["รหัส", "สถานะ"] + [str(d) for d in range(1, days_in_month+1)]
    html = """
    <style>
    .cal-table { border-collapse: collapse; width: 100%; font-size: 12px; }
    .cal-table th, .cal-table td { border: 1px solid #ddd; padding: 4px; text-align: center; height: 32px; }
    .cal-table th { background: #2c3e50; color: white; }
    .cell-red { background: #e74c3c; color: white; }
    .cell-orange { background: #ff9f43; color: white; }
    .cell-empty { background: white; }
    .col-fixed { background: #f8f9fa; position: sticky; left: 0; z-index: 1; }
    </style>
    <table class="cal-table">
    <tr>
    """
    for i, col in enumerate(header_cols):
        html += f"<th class='{'col-fixed' if i<2 else ''}'>{col}</th>"
    html += "</tr>"
    
    for _, car in df_cars.iterrows():
        car_id = car.get("รหัสรถ", "")
        status = car.get("สถานะ", "พร้อมใช้งาน")
        
        html += f"<tr><td class='col-fixed'><strong>{car_id}</strong></td><td class='col-fixed'>{status}</td>"
        
        bookings = []
        if not df_book.empty and "รหัสรถ" in df_book.columns:
            bk_car = df_book[df_book["รหัสรถ"] == car_id]
            for _, bk in bk_car.iterrows():
                try:
                    s = datetime.strptime(str(bk["วันที่เริ่ม"]), "%Y-%m-%d").date()
                    e = datetime.strptime(str(bk["วันที่คืน"]), "%Y-%m-%d").date()
                    if (s.month == month and s.year == year) or (e.month == month and e.year == year):
                        bookings.append((s, e))
                except: pass
        
        for day in range(1, days_in_month+1):
            d = datetime(year, month, day).date()
            booked = any(s <= d <= e for s, e in bookings)
            
            if status == "กำลังเช่า":
                cls = "cell-red"
            elif booked:
                cls = "cell-orange"
            else:
                cls = "cell-empty"
            
            html += f"<td class='{cls}'></td>"
        html += "</tr>"
    
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("🔴 แดง = กำลังเช่า | 🟠 ส้ม = มีการจอง | ⬜ ขาว = ว่าง")
    
    with st.expander("ดูข้อมูลการจองทั้งหมด"):
        if not df_book.empty:
            desired_order = ["รหัสจอง", "รหัสรถ", "ชื่อลูกค้า", "วันที่เริ่ม", "เวลาเริ่ม", "วันที่คืน", "เวลาคืน", "จำนวนวัน", "ค่าเช่ารวม", "เงินมัดจำ", "หมายเหตุ"]
            cols = [c for c in desired_order if c in df_book.columns]
            st.dataframe(df_book[cols], use_container_width=True)
        else:
            st.info("ยังไม่มีการจอง")

# ====== รายงานสรุป ======
elif menu == "📈 รายงานสรุป":
    st.header("📈 รายงานสรุป")
    
    df_cars = load_data(FILE_CARS)
    df_cust = load_data(FILE_CUSTOMERS)
    df_book = load_data(FILE_BOOKINGS)
    
    total_rent = 0
    total_deposit = 0
    if not df_book.empty:
        if "ค่าเช่ารวม" in df_book.columns:
            total_rent = pd.to_numeric(df_book["ค่าเช่ารวม"], errors="coerce").sum() or 0
        if "เงินมัดจำ" in df_book.columns:
            total_deposit = pd.to_numeric(df_book["เงินมัดจำ"], errors="coerce").sum() or 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🚗 จำนวนรถทั้งหมด", len(df_cars))
    c2.metric("👤 จำนวนลูกค้า", len(df_cust))
    c3.metric("📅 จำนวนการจอง", len(df_book))
    
    c4, c5 = st.columns(2)
    c4.metric("💰 รวมค่าเช่าทั้งหมด", f"{total_rent:,.0f} บาท")
    c5.metric("🔒 รวมเงินมัดจำทั้งหมด", f"{total_deposit:,.0f} บาท")
    
    st.markdown("---")
    st.subheader("📋 ข้อมูลรถ")
    if not df_cars.empty: st.dataframe(df_cars, use_container_width=True)
    st.subheader("📋 ข้อมูลลูกค้า")
    if not df_cust.empty: st.dataframe(df_cust, use_container_width=True, hide_index=True)
    st.subheader("📋 ข้อมูลการจอง")
    if not df_book.empty:
        desired_order = ["รหัสจอง", "รหัสรถ", "ชื่อลูกค้า", "วันที่เริ่ม", "เวลาเริ่ม", "วันที่คืน", "เวลาคืน", "จำนวนวัน", "ค่าเช่ารวม", "เงินมัดจำ", "หมายเหตุ"]
        cols = [c for c in desired_order if c in df_book.columns]
        st.dataframe(df_book[cols], use_container_width=True)