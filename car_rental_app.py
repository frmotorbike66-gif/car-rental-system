import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="ระบบจัดการรถเช่า", layout="wide", page_icon="🚗")
DATA_FOLDER = "rental_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

FILE_CARS = os.path.join(DATA_FOLDER, "cars.csv")
FILE_CUSTOMERS = os.path.join(DATA_FOLDER, "customers.csv")
FILE_BOOKINGS = os.path.join(DATA_FOLDER, "bookings.csv")

def init_files():
    for f, cols in [
        (FILE_CARS, ["รหัสรถ", "ยี่ห้อ-รุ่น", "ป้ายทะเบียน", "ราคาต่อวัน", "สถานะ", "หมายเหตุ"]),
        (FILE_CUSTOMERS, ["รหัสลูกค้า", "ชื่อ-นามสกุล", "เบอร์โทร", "ที่จัดส่งรถ"]),
        (FILE_BOOKINGS, ["รหัสจอง", "รหัสรถ", "รหัสลูกค้า", "วันที่เริ่ม", "เวลาส่ง", "วันที่คืน", "จำนวนวัน", "ราคารวม", "เงินมัดจำ", "ค่ามัดจำคืน", "สถานะจ่าย"])
    ]:
        if not os.path.exists(f):
            pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8-sig")

def load_data(path):
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig")

def save_data(df, path):
    df.to_csv(path, index=False, encoding="utf-8-sig")
def get_next_booking_id():
    if not os.path.exists(FILE_BOOKINGS):
        return "B001"
    df = load_data(FILE_BOOKINGS)
    if df.empty or "รหัสจอง" not in df.columns:
        return "B001"
    # ดึงเฉพาะตัวเลข กรณีข้อมูลไม่สมบูรณ์ให้ข้ามไป
    nums = df["รหัสจอง"].str.extract(r"(\d+)$")
    nums = nums[0].dropna()  # ลบค่าว่างทิ้ง
    if nums.empty:
        return "B001"
    last = nums.astype(int).max()
    return f"B{last+1:03d}"

init_files()

st.sidebar.title("🚗 ระบบจัดการรถเช่า")
menu = st.sidebar.radio("เลือกเมนู", [
    "🚗 จัดการข้อมูลรถ",
    "👤 จัดการข้อมูลลูกค้า",
    "📅 ทำการจอง",
    "📊 ปฏิทินจอง",
    "📈 รายงานสรุป"
])

# ====== 1. จัดการรถ ======
if menu == "🚗 จัดการข้อมูลรถ":
    st.header("🚗 จัดการข้อมูลรถ")
    df = load_data(FILE_CARS)
    
    with st.form("add_car"):
        c1,c2,c3 = st.columns(3)
        with c1: cid = st.text_input("รหัสรถ")
        with c2: name = st.text_input("ยี่ห้อ-รุ่น")
        with c3: plate = st.text_input("ป้ายทะเบียน")
        c4,c5,c6 = st.columns(3)
        with c4: price = st.number_input("ราคาต่อวัน", min_value=0, step=50)
        with c5: status = st.selectbox("สถานะ", ["พร้อมใช้งาน", "กำลังเช่า", "ซ่อมบำรุง"])
        with c6: note = st.text_input("หมายเหตุ")
        if st.form_submit_button("✅ เพิ่มรถ"):
            if cid in df["รหัสรถ"].values:
                st.error("มีรหัสรถนี้แล้ว!")
            else:
                df.loc[len(df)] = [cid, name, plate, price, status, note]
                save_data(df, FILE_CARS)
                st.success("เพิ่มรถสำเร็จ!")
                st.rerun()
    
    st.subheader("รายการรถ")
    if not df.empty:
        del_id = st.selectbox("เลือกรถที่ต้องการลบ", ["-- เลือก --"] + list(df["รหัสรถ"] + " | " + df["ยี่ห้อ-รุ่น"]))
        if del_id != "-- เลือก --" and st.button("🗑️ ลบรายการนี้"):
            rid = del_id.split(" | ")[0]
            df = df[df["รหัสรถ"] != rid].reset_index(drop=True)
            save_data(df, FILE_CARS)
            st.success("ลบสำเร็จ!")
            st.rerun()
    st.dataframe(df, use_container_width=True)

# ====== 2. จัดการลูกค้า ======
elif menu == "👤 จัดการข้อมูลลูกค้า":
    st.header("👤 จัดการข้อมูลลูกค้า")
    df = load_data(FILE_CUSTOMERS)
    
    with st.form("add_cust"):
        c1,c2 = st.columns(2)
        with c1: cid = st.text_input("รหัสลูกค้า")
        with c2: name = st.text_input("ชื่อ-นามสกุล")
        c3,c4 = st.columns(2)
        with c3: tel = st.text_input("เบอร์โทร")
        with c4: addr = st.text_input("ที่จัดส่งรถ")
        if st.form_submit_button("✅ เพิ่มลูกค้า"):
            if cid in df["รหัสลูกค้า"].values:
                st.error("มีรหัสลูกค้านี้แล้ว!")
            else:
                df.loc[len(df)] = [cid, name, tel, addr]
                save_data(df, FILE_CUSTOMERS)
                st.success("เพิ่มลูกค้าสำเร็จ!")
                st.rerun()
    
    st.subheader("รายการลูกค้า")
    if not df.empty:
        del_id = st.selectbox("เลือกลูกค้าที่ต้องการลบ", ["-- เลือก --"] + list(df["รหัสลูกค้า"] + " | " + df["ชื่อ-นามสกุล"]))
        if del_id != "-- เลือก --" and st.button("🗑️ ลบรายการนี้"):
            cid = del_id.split(" | ")[0]
            df = df[df["รหัสลูกค้า"] != cid].reset_index(drop=True)
            save_data(df, FILE_CUSTOMERS)
            st.success("ลบสำเร็จ!")
            st.rerun()
    st.dataframe(df, use_container_width=True)

# ====== 3. ทำการจอง ======
elif menu == "📅 ทำการจอง":
    st.header("📅 บันทึกการจอง")
    cars = load_data(FILE_CARS)
    custs = load_data(FILE_CUSTOMERS)
    books = load_data(FILE_BOOKINGS)
    cars_avail = cars[cars["สถานะ"] == "พร้อมใช้งาน"]
    
    auto_bid = get_next_booking_id()
    st.info(f"รหัสการจองจะเป็น: {auto_bid} (สร้างอัตโนมัติ)")
    
    with st.form("add_book"):
        bid = auto_bid
        car_sel = st.selectbox("เลือกรถ", cars_avail["รหัสรถ"] + " | " + cars_avail["ยี่ห้อ-รุ่น"])
        cust_sel = st.selectbox("เลือกลูกค้า", custs["รหัสลูกค้า"] + " | " + custs["ชื่อ-นามสกุล"])
        c1,c2 = st.columns(2)
        with c1: start = st.date_input("วันที่เริ่ม")
        with c2: time_deliver = st.time_input("เวลาจัดส่งรถ")
        c3,c4 = st.columns(2)
        with c3: end = st.date_input("วันที่คืน")
        with c4: deposit = st.number_input("เงินมัดจำที่รับ", min_value=0, step=100)
        paid = st.selectbox("สถานะการจ่าย", ["ยังไม่จ่าย", "จ่ายแล้ว"])
        
        if st.form_submit_button("✅ บันทึกการจอง"):
            car_id = car_sel.split(" | ")[0]
            cust_id = cust_sel.split(" | ")[0]
            days = (end - start).days
            if days <= 0:
                st.error("วันที่คืนต้องมาหลังวันที่รับ!")
            else:
                price_day = float(cars[cars["รหัสรถ"] == car_id]["ราคาต่อวัน"].iloc[0])
                total = days * price_day
                books.loc[len(books)] = [bid, car_id, cust_id, str(start), str(time_deliver), str(end), days, total, deposit, 0, paid]
                save_data(books, FILE_BOOKINGS)
                cars.loc[cars["รหัสรถ"] == car_id, "สถานะ"] = "กำลังเช่า"
                save_data(cars, FILE_CARS)
                st.success(f"จองสำเร็จ! รหัส: {bid} | ยอดรวม {total:,.0f} บาท | มัดจำ {deposit:,.0f} บาท")
                st.rerun()
    
    st.subheader("รายการจองทั้งหมด")
    st.dataframe(books, use_container_width=True)

# ====== 4. ปฏิทินจอง ======
elif menu == "📊 ปฏิทินจอง":
    st.header("📊 ปฏิทินจองรถ")
    df_cars = load_data(FILE_CARS)
    df_books = load_data(FILE_BOOKINGS)
    
    c1,_ = st.columns([1,4])
    with c1:
        now = datetime.now()
        m = st.selectbox("เลือกเดือน", list(range(1,13)), index=now.month-1)
        y = st.selectbox("เลือกปี", list(range(now.year-2, now.year+3)), index=2)
    
    days_in_month = pd.Period(f"{y}-{m}").days_in_month
    header = ["รหัสรถ", "รุ่นรถ / ป้ายทะเบียน", "สถานะปัจจุบัน"] + [str(d) for d in range(1, days_in_month+1)]
    cal_data = []
    
    for _, car in df_cars.iterrows():
        row = [car["รหัสรถ"], f"{car['ยี่ห้อ-รุ่น']} ({car['ป้ายทะเบียน']})", car["สถานะ"]] + [""] * days_in_month
        cal_data.append(row)
    
    for _, bk in df_books.iterrows():
        try:
            s = datetime.strptime(bk["วันที่เริ่ม"], "%Y-%m-%d")
            e = datetime.strptime(bk["วันที่คืน"], "%Y-%m-%d")
            if s.year == y and s.month == m:
                car_idx = df_cars.index[df_cars["รหัสรถ"] == bk["รหัสรถ"]]
                if not car_idx.empty:
                    start_d = max(1, s.day)
                    end_d = min(days_in_month, e.day)
                    for d in range(start_d, end_d+1):
                        cal_data[car_idx[0]][2+d] = "จอง"
        except: pass
    
    st.markdown(f"### ปฏิทินเดือน {m}/{y}")
    df_cal = pd.DataFrame(cal_data, columns=header)
    
    def color_cell(val):
        if val == "พร้อมใช้งาน": return "background-color: #90EE90; font-weight: bold;"
        if val == "กำลังเช่า": return "background-color: #FF0000; color: white; font-weight: bold;"
        if val == "ซ่อมบำรุง": return "background-color: #FFCC00; font-weight: bold;"
        if val == "จอง": return "background-color: #FFCC99;"
        return ""
    
    st.dataframe(df_cal.style.map(color_cell), use_container_width=True, height=600)
    
    st.subheader("✅ คืนรถ / ปิดการจอง")
    if not df_books.empty:
        bk_sel = st.selectbox("เลือกรายการจอง", df_books["รหัสจอง"] + " | " + df_books["รหัสรถ"] + " | " + df_books["สถานะจ่าย"])
        refund_amt = st.number_input("คืนเงินมัดจำ", min_value=0, step=100)
        if st.button("คืนรถแล้ว"):
            bk_id = bk_sel.split(" | ")[0]
            car_id = df_books[df_books["รหัสจอง"] == bk_id]["รหัสรถ"].iloc[0]
            df_books.loc[df_books["รหัสจอง"] == bk_id, "สถานะจ่าย"] = "จ่ายแล้ว"
            df_books.loc[df_books["รหัสจอง"] == bk_id, "ค่ามัดจำคืน"] = refund_amt
            df_cars.loc[df_cars["รหัสรถ"] == car_id, "สถานะ"] = "พร้อมใช้งาน"
            save_data(df_books, FILE_BOOKINGS)
            save_data(df_cars, FILE_CARS)
            st.success("คืนรถเรียบร้อย! บันทึกการคืนมัดจำแล้ว")
            st.rerun()

# ====== 5. รายงานสรุป ======
elif menu == "📈 รายงานสรุป":
    st.header("📈 รายงานสรุป")
    df = load_data(FILE_BOOKINGS)
    if df.empty:
        st.info("ยังไม่มีข้อมูลการจอง")
    else:
        df["ราคารวม"] = pd.to_numeric(df["ราคารวม"], errors="coerce").fillna(0)
        df["เงินมัดจำ"] = pd.to_numeric(df["เงินมัดจำ"], errors="coerce").fillna(0)
        df["ค่ามัดจำคืน"] = pd.to_numeric(df["ค่ามัดจำคืน"], errors="coerce").fillna(0)
        
        total_income = df[df["สถานะจ่าย"] == "จ่ายแล้ว"]["ราคารวม"].sum()
        pending = df[df["สถานะจ่าย"] == "ยังไม่จ่าย"]["ราคารวม"].sum()
        deposit_held = df["เงินมัดจำ"].sum()
        deposit_returned = df["ค่ามัดจำคืน"].sum()
        deposit_balance = deposit_held - deposit_returned
        
        c1,c2 = st.columns(2)
        c1.metric("💰 รายรับรวม", f"{total_income:,.0f} บาท")
        c2.metric("⏳ รอรับชำระ", f"{pending:,.0f} บาท")
        c3,c4,c5 = st.columns(3)
        c3.metric("💵 มัดจำที่รับไว้", f"{deposit_held:,.0f} บาท")
        c4.metric("💸 คืนมัดจำแล้ว", f"{deposit_returned:,.0f} บาท")
        c5.metric("🏦 มัดจำคงเหลือ", f"{deposit_balance:,.0f} บาท")
        st.metric("📋 จำนวนการจองทั้งหมด", len(df))
        
        st.subheader("ข้อมูลทั้งหมด")
        st.dataframe(df, use_container_width=True)
        
        # ส่งออก Excel
        output_file = os.path.join(DATA_FOLDER, "รายงานสรุป.xlsx")
        df.to_excel(output_file, index=False)
        with open(output_file, "rb") as f:
            st.download_button("📥 ดาวน์โหลดรายงานเป็น Excel", f, file_name="รายงานสรุป.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")