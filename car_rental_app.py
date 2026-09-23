import streamlit as st
import pandas as pd
import json
import base64
from datetime import datetime, timedelta
import requests

# ==========================================
# 🔧 ตั้งค่า
# ==========================================
APP_NAME = "FR Motor Bike"
VALID_USERS = {
    "admin": "123456",
    "frmotor": "phuket2026"
}

st.set_page_config(page_title=APP_NAME, layout="wide")

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
    GITHUB_BRANCH = st.secrets["GITHUB_BRANCH"]
    DATA_DIR = st.secrets["GITHUB_DATA_DIR"]
except Exception as e:
    st.error("⚠️ ยังไม่ได้ตั้งค่า Secrets ที่หน้า Streamlit Settings")
    st.stop()

FILES = {
    "cars": f"{DATA_DIR}/cars.csv",
    "customers": f"{DATA_DIR}/customers.csv",
    "bookings": f"{DATA_DIR}/bookings.csv"
}

# ==========================================
# 🔌 ฟังก์ชันอ่าน-เขียนข้อมูล
# ==========================================
def github_api(path, method="GET", data=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    res = requests.request(method, url, headers=headers, data=json.dumps(data) if data else None)
    return res.json() if res.status_code in [200, 201] else None

def read_csv(path):
    resp = github_api(path)
    if not resp or "content" not in resp:
        return pd.DataFrame()
    content = base64.b64decode(resp["content"]).decode("utf-8-sig")
    from io import StringIO
    return pd.read_csv(StringIO(content), dtype=str)

def save_csv(df, path):
    resp = github_api(path)
    sha = resp["sha"] if resp and "content" in resp else None
    content = df.to_csv(index=False, encoding="utf-8-sig")
    data = {
        "message": f"update {path} — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(content.encode("utf-8-sig")).decode(),
        "branch": GITHUB_BRANCH
    }
    if sha: data["sha"] = sha
    return github_api(path, "PUT", data) is not None

def init_csv(path, columns):
    df = read_csv(path)
    if df.empty:
        save_csv(pd.DataFrame(columns=columns), path)

# ==========================================
# 🚀 เริ่มทำงาน
# ==========================================
init_csv(FILES["cars"], ["รหัสรถ", "ยี่ห้อ-รุ่น/ป้าย", "ราคาต่อวัน", "สถานะ", "หมายเหตุ"])
init_csv(FILES["customers"], ["ชื่อ-นามสกุล", "เบอร์โทร", "ที่อยู่"])
init_csv(FILES["bookings"], ["รหัสจอง", "รหัสรถ", "ชื่อลูกค้า", 
         "วันที่เริ่ม", "เวลาเริ่ม", "วันที่คืน", "เวลาคืน",
         "สถานะการจอง", "จำนวนวัน", "ค่าเช่ารวม", "เงินมัดจำ", "หมายเหตุ", "วันที่ทำรายการ"])

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title(f"🔒 เข้าสู่ระบบ — {APP_NAME}")
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
    st.stop()

st.sidebar.title(f"🏍️ {APP_NAME}")
st.sidebar.write(f"สวัสดีค่ะ, {st.session_state.username}")
if st.sidebar.button("🚪 ออกจากระบบ"):
    st.session_state.logged_in = False
    st.rerun()
st.sidebar.markdown("---")

menu = st.sidebar.radio("เลือกเมนู", [
    "🏍️ จัดการข้อมูลรถ",
    "👤 จัดการข้อมูลลูกค้า",
    "📅 ทำการจอง",
    "📊 ปฏิทินการจอง",
    "📈 รายงานสรุป"
])

st.title(f"🏍️ {APP_NAME}")
st.markdown("ระบบจัดการเช่ารถ — ข้อมูลบันทึกขึ้น GitHub อัตโนมัติ")

def calculate_days_by_hour(start_date, start_time, end_date, end_time):
    try:
        start_dt = datetime.combine(pd.to_datetime(start_date).date(), start_time)
        end_dt = datetime.combine(pd.to_datetime(end_date).date(), end_time)
        total_hours = (end_dt - start_dt).total_seconds() / 3600
        days_full = int(total_hours // 24)
        remainder = total_hours % 24
        grace = 2
        days = days_full if remainder <= grace else days_full + 1
        return max(1, days), round(total_hours, 1)
    except:
        return 1, 0

def get_next_booking_id():
    df = read_csv(FILES["bookings"])
    if df.empty or "รหัสจอง" not in df.columns:
        return "B001"
    nums = df["รหัสจอง"].str.extract(r"(\d+)$")[0].dropna()
    return f"B{nums.astype(int).max()+1:03d}" if not nums.empty else "B001"

# ====== จัดการข้อมูลรถ ======
if menu == "🏍️ จัดการข้อมูลรถ":
    st.header("🏍️ ข้อมูลรถ")
    df = read_csv(FILES["cars"])
    
    edit_id = st.selectbox("✏️ แก้ไข — เลือกรถ", [""] + list(df["รหัสรถ"].unique()) if not df.empty else [])
    if edit_id:
        row = df[df["รหัสรถ"] == edit_id].iloc[0]
        with st.form("edit_car"):
            c1,c2=st.columns(2)
            with c1:
                cid = st.text_input("รหัสรถ", value=row["รหัสรถ"], disabled=True)
                name = st.text_input("ชื่อ/รุ่น/ป้าย", value=row["ยี่ห้อ-รุ่น/ป้าย"])
            with c2:
                price = st.number_input("ราคาต่อวัน", min_value=0, value=int(float(row["ราคาต่อวัน"] or 300)))
                status = st.selectbox("สถานะ", ["ว่าง","จองแล้ว","กำลังใช้งาน","ซ่อมบำรุง"],
                    index=["ว่าง","จองแล้ว","กำลังใช้งาน","ซ่อมบำรุง"].index(row["สถานะ"]))
                note = st.text_input("หมายเหตุ", value=row["หมายเหตุ"])
            if st.form_submit_button("💾 บันทึก"):
                df.loc[df["รหัสรถ"]==edit_id] = [cid,name,price,status,note]
                save_csv(df, FILES["cars"])
                st.success("✅ บันทึกสำเร็จ")
                st.rerun()
    
    with st.form("add_car"):
        c1,c2=st.columns(2)
        with c1:
            cid = st.text_input("รหัสรถ เช่น V001")
            name = st.text_input("ชื่อ/รุ่น/ป้าย")
        with c2:
            price = st.number_input("ราคาต่อวัน", min_value=0, value=300)
            status = st.selectbox("สถานะ", ["ว่าง","จองแล้ว","กำลังใช้งาน","ซ่อมบำรุง"])
            note = st.text_input("หมายเหตุ")
        if st.form_submit_button("✅ เพิ่มรถ"):
            if cid and name:
                if not df.empty and cid in df["รหัสรถ"].values:
                    st.error("❌ มีรหัสนี้แล้ว ใช้แก้ไขด้านบน")
                else:
                    df = pd.concat([df, pd.DataFrame([{"รหัสรถ":cid,"ยี่ห้อ-รุ่น/ป้าย":name,"ราคาต่อวัน":price,"สถานะ":status,"หมายเหตุ":note}])], ignore_index=True)
                    save_csv(df, FILES["cars"])
                    st.success("✅ เพิ่มสำเร็จ")
                    st.rerun()
    
    st.subheader("รายการทั้งหมด")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        del_id = st.selectbox("🗑️ ลบ — เลือกรถ", [""] + list(df["รหัสรถ"].unique()))
        if st.button("🗑️ ลบทันที") and del_id:
            df = df[df["รหัสรถ"]!=del_id]
            save_csv(df, FILES["cars"])
            st.success("✅ ลบสำเร็จ")
            st.rerun()

# ====== จัดการลูกค้า ======
elif menu == "👤 จัดการข้อมูลลูกค้า":
    st.header("👤 ข้อมูลลูกค้า")
    df = read_csv(FILES["customers"])
    
    edit_idx = st.selectbox("✏️ แก้ไข — เลือกลูกค้า", [""] + list(df.index+1) if not df.empty else [])
    if edit_idx:
        row = df.iloc[int(edit_idx)-1]
        with st.form("edit_cust"):
            name = st.text_input("ชื่อ-นามสกุล", value=row["ชื่อ-นามสกุล"])
            phone = st.text_input("เบอร์โทร", value=row["เบอร์โทร"])
            addr = st.text_area("ที่อยู่", value=row["ที่อยู่"])
            if st.form_submit_button("💾 บันทึก"):
                df.loc[int(edit_idx)-1] = [name,phone,addr]
                save_csv(df, FILES["customers"])
                st.success("✅ บันทึกสำเร็จ")
                st.rerun()
    
    with st.form("add_cust"):
        name = st.text_input("ชื่อ-นามสกุล")
        phone = st.text_input("เบอร์โทร")
        addr = st.text_area("ที่อยู่")
        if st.form_submit_button("✅ เพิ่มลูกค้า"):
            if name:
                df = pd.concat([df, pd.DataFrame([{"ชื่อ-นามสกุล":name,"เบอร์โทร":phone,"ที่อยู่":addr}])], ignore_index=True)
                save_csv(df, FILES["customers"])
                st.success("✅ เพิ่มสำเร็จ")
                st.rerun()
    
    st.subheader("รายการทั้งหมด")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        del_idx = st.selectbox("🗑️ ลบ — เลือกลูกค้า", [""] + list(df.index+1))
        if st.button("🗑️ ลบทันที") and del_idx:
            df = df.drop(int(del_idx)-1).reset_index(drop=True)
            save_csv(df, FILES["customers"])
            st.success("✅ ลบสำเร็จ")
            st.rerun()

# ====== ทำการจอง ======
elif menu == "📅 ทำการจอง":
    st.header("📅 ทำการจอง")
    df_car = read_csv(FILES["cars"])
    df_cust = read_csv(FILES["customers"])
    
    if df_car.empty or df_cust.empty:
        st.warning("⚠️ เพิ่มข้อมูลรถและลูกค้าก่อนทำการจอง")
    else:
        sel_car = st.selectbox("เลือกรถ", df_car["รหัสรถ"].tolist())
        sel_cust = st.selectbox("เลือกลูกค้า", df_cust["ชื่อ-นามสกุล"].tolist())
        
        c1,c2=st.columns(2)
        with c1:
            s_date = st.date_input("วันที่เริ่มเช่า")
            s_time = st.time_input("เวลาเริ่ม", value=datetime.strptime("09:00","%H:%M").time())
        with c2:
            e_date = st.date_input("วันที่คืนรถ")
            e_time = st.time_input("เวลาคืน", value=datetime.strptime("18:00","%H:%M").time())
        
        status_booking = st.selectbox("สถานะ", ["จองแล้ว", "กำลังใช้งาน"])
        
        car_row = df_car[df_car["รหัสรถ"]==sel_car].iloc[0]
        price_day = float(car_row["ราคาต่อวัน"])
        days, hours = calculate_days_by_hour(s_date, s_time, e_date, e_time)
        total = price_day * days
        st.info(f"💰 {price_day:,.0f} บาท/วัน | {hours:.1f} ชม. = {days} วัน | รวม {total:,.0f} บาท\n💡 คืนล่าช้าได้ไม่เกิน 2 ชม.")
        
        deposit = st.text_input("💰 เงินมัดจำ (บาท)")
        note = st.text_input("หมายเหตุ")
        
        if st.button("✅ บันทึกการจอง"):
            df_book = read_csv(FILES["bookings"])
            bid = get_next_booking_id()
            new_row = {
                "รหัสจอง":bid, "รหัสรถ":sel_car, "ชื่อลูกค้า":sel_cust,
                "วันที่เริ่ม":s_date, "เวลาเริ่ม":s_time.strftime("%H:%M"),
                "วันที่คืน":e_date, "เวลาคืน":e_time.strftime("%H:%M"),
                "สถานะการจอง":status_booking, "จำนวนวัน":days,
                "ค่าเช่ารวม":f"{total:.0f}", "เงินมัดจำ":deposit,
                "หมายเหตุ":note, "วันที่ทำรายการ":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            df_book = pd.concat([df_book, pd.DataFrame([new_row])], ignore_index=True)
            save_csv(df_book, FILES["bookings"])
            
            df_car.loc[df_car["รหัสรถ"]==sel_car, "สถานะ"] = status_booking
            save_csv(df_car, FILES["cars"])
            
            st.success(f"✅ บันทึกสำเร็จ! รหัส: {bid} | ข้อมูลส่งขึ้น GitHub แล้ว")
            st.balloons()
            st.rerun()
    
    st.markdown("---")
    st.subheader("รายการจองทั้งหมด")
    df_book = read_csv(FILES["bookings"])
    if not df_book.empty:
        cols = ["รหัสจอง","รหัสรถ","ชื่อลูกค้า","วันที่เริ่ม","เวลาเริ่ม","วันที่คืน","เวลาคืน","สถานะการจอง","จำนวนวัน","ค่าเช่ารวม","เงินมัดจำ","หมายเหตุ"]
        st.dataframe(df_book[[c for c in cols if c in df_book.columns]], use_container_width=True)
        
        edit_bid = st.selectbox("🔄 เปลี่ยนสถานะ — เลือกรหัสจอง", [""]+list(df_book["รหัสจอง"].unique()))
        if edit_bid:
            new_stat = st.selectbox("สถานะใหม่", ["จองแล้ว","กำลังใช้งาน","ว่าง"])
            if st.button("✅ อัปเดต"):
                df_book.loc[df_book["รหัสจอง"]==edit_bid, "สถานะการจอง"] = new_stat
                car_id = df_book.loc[df_book["รหัสจอง"]==edit_bid, "รหัสรถ"].iloc[0]
                df_car = read_csv(FILES["cars"])
                df_car.loc[df_car["รหัสรถ"]==car_id, "สถานะ"] = new_stat
                save_csv(df_book, FILES["bookings"])
                save_csv(df_car, FILES["cars"])
                st.success(f"✅ เปลี่ยนเป็น: {new_stat}")
                st.rerun()
        
        del_bid = st.selectbox("🗑️ ลบ — เลือกรหัสจอง", [""]+list(df_book["รหัสจอง"].unique()))
        if st.button("🗑️ ลบทันที") and del_bid:
            car_id = df_book.loc[df_book["รหัสจอง"]==del_bid, "รหัสรถ"].iloc[0]
            df_book = df_book[df_book["รหัสจอง"]!=del_bid]
            df_car = read_csv(FILES["cars"])
            df_car.loc[df_car["รหัสรถ"]==car_id, "สถานะ"] = "ว่าง"
            save_csv(df_book, FILES["bookings"])
            save_csv(df_car, FILES["cars"])
            st.success("✅ ลบสำเร็จ — คืนสถานะเป็นว่าง")
            st.rerun()

# ====== ปฏิทิน ======
elif menu == "📊 ปฏิทินการจอง":
    st.header("📊 ปฏิทินการจอง")
    today = datetime.today()
    m = st.selectbox("เดือน", list(range(1,13)), index=today.month-1)
    y = st.selectbox("ปี", list(range(2025,2031)), index=2026-2025)
    
    # คำนวณจำนวนวันในเดือน
    if m == 12:
        days_in_month = 31
    else:
        days_in_month = (datetime(y, m + 1, 1) - timedelta(days=1)).days
    
    df_car = read_csv(FILES["cars"])
    df_book = read_csv(FILES["bookings"])
    
    st.markdown(f"### 📅 ปฏิทิน — {m}/{y}")
    
    html = """
    <style>.cal-table{border-collapse:collapse;width:100%;font-size:11px;}
    .cal-table th,.cal-table td{border:1px solid #ddd;padding:4px;text-align:center;height:30px;}
    .cal-table th{background:#2c3e50;color:white;}
    .cell-red{background:#e74c3c;color:white;}
    .cell-orange{background:#ff9f43;color:white;}
    .cell-white{background:#fff;}
    .col-fixed{background:#f8f9fa;position:sticky;left:0;z-index:1;}
    </style>
    <table class="cal-table"><tr>
    <th class="col-fixed">รหัส</th><th class="col-fixed">สถานะ</th>
    """
    html += "".join(f"<th>{d}</th>" for d in range(1, days_in_month+1))
    html += "</tr>"
    
    for _, car in df_car.iterrows():
        cid = car["รหัสรถ"]
        cstat = car["สถานะ"]
        html += f"<tr><td class='col-fixed'><strong>{cid}</strong></td><td class='col-fixed'>{cstat}</td>"
        
        bookings = []
        if not df_book.empty:
            for _, bk in df_book[df_book["รหัสรถ"]==cid].iterrows():
                try:
                    s = datetime.strptime(str(bk["วันที่เริ่ม"]), "%Y-%m-%d").date()
                    e = datetime.strptime(str(bk["วันที่คืน"]), "%Y-%m-%d").date()
                    bookings.append((s, e, bk["สถานะการจอง"]))
                except:
                    pass
        
        for d in range(1, days_in_month+1):
            day = datetime(y, m, d).date()
            tstat = None
            for s, e, bstatus in bookings:
                if s <= day <= e:
                    tstat = bstatus
                    break
            
            if tstat == "กำลังใช้งาน":
                cls = "cell-red"
            elif tstat == "จองแล้ว":
                cls = "cell-orange"
            else:
                cls = "cell-white"
            
            html += f"<td class='{cls}'></td>"
        html += "</tr>"
    
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("🔴 แดง=กำลังใช้งาน | 🟠 ส้ม=จองแล้ว | ⬜ ขาว=ว่าง")

# ====== รายงานสรุป ======
elif menu == "📈 รายงานสรุป":
    st.header("📈 รายงานสรุป")
    df_car = read_csv(FILES["cars"])
    df_cust = read_csv(FILES["customers"])
    df_book = read_csv(FILES["bookings"])
    
    total_rent = pd.to_numeric(df_book["ค่าเช่ารวม"], errors="coerce").sum() or 0 if not df_book.empty else 0
    total_dep = pd.to_numeric(df_book["เงินมัดจำ"], errors="coerce").sum() or 0 if not df_book.empty else 0
    
    c1,c2,c3 = st.columns(3)
    c1.metric("🚗 รถทั้งหมด", len(df_car))
    c2.metric("👤 ลูกค้าทั้งหมด", len(df_cust))
    c3.metric("📅 การจองทั้งหมด", len(df_book))
    
    c4,c5 = st.columns(2)
    c4.metric("💰 รวมค่าเช่า", f"{total_rent:,.0f} บาท")
    c5.metric("🔒 รวมเงินมัดจำ", f"{total_dep:,.0f} บาท")
    
    st.subheader("ข้อมูลรถ")
    st.dataframe(df_car, use_container_width=True)
    st.subheader("ข้อมูลลูกค้า")
    st.dataframe(df_cust, use_container_width=True, hide_index=True)
    st.subheader("ข้อมูลการจอง")
    if not df_book.empty:
        cols = ["รหัสจอง","รหัสรถ","ชื่อลูกค้า","วันที่เริ่ม","เวลาเริ่ม","วันที่คืน","เวลาคืน","สถานะการจอง","จำนวนวัน","ค่าเช่ารวม","เงินมัดจำ","หมายเหตุ"]
        st.dataframe(df_book[[c for c in cols if c in df_book.columns]], use_container_width=True)
