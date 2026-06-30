import pyodbc
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, time

# ==================== CẤU HÌNH ====================
DB_CONFIG = {
    'server': '192.168.132.20',
    'database': 'security_db',
    'username': 'sa',
    'password': 'www.111.com'
}

SMTP_CONFIG = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'sender': 'hienahihi111@gmail.com',
    'password': 'sysc kwvu dxxr dmxe'
}

RECEIVER = 'hienahihi111@gmail.com'

# Danh sách PIN cần lấy
PIN_LIST = ['83294', '81474', '82367', '82630', '80068']

# ==================== HÀM XỬ LÝ ====================

def get_db_connection(config):
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={config['server']};"
        f"DATABASE={config['database']};"
        f"UID={config['username']};"
        f"PWD={config['password']};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

def fetch_data():
    # Ngày test cố định (bạn có thể sửa lại)
    today = datetime.now().date()
    # today = datetime.strptime("2026-06-29", "%Y-%m-%d").date()
    start_time = datetime.combine(today, time(12, 0, 0))
    end_time   = datetime.combine(today, time(13, 0, 0))

    placeholders = ','.join(['?'] * len(PIN_LIST))
    query = f"""
        SELECT pin, create_time, dev_alias, area_name, name
        FROM dbo.acc_transaction
        WHERE pin IN ({placeholders})
          AND create_time >= ?
          AND create_time < ?
          AND area_name <> 'HMT'
        ORDER BY pin, create_time   -- Sắp xếp theo pin để nhóm dễ dàng
    """
    params = PIN_LIST + [start_time, end_time]

    with get_db_connection(DB_CONFIG) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows, start_time, end_time

def build_email_body(rows, start_time, end_time):
    if not rows:
        return f"<p><b>Không có dữ liệu trong khoảng {start_time} – {end_time}.</b></p>"

    html = f"""
    <html>
    <body>
        <h3>Dữ liệu từ bảng acc_transaction</h3>
        <p>Khoảng thời gian: {start_time} – {end_time}</p>
    """

    current_pin = None
    for row in rows:
        if row.pin != current_pin:
            # Đóng bảng trước đó (nếu có)
            if current_pin is not None:
                html += "</table>"
                html += "<hr>"   # Đường kẻ ngang phân cách giữa các PIN
            current_pin = row.pin
            # Tiêu đề cho PIN mới
            html += f"<h4>Mã PIN: {current_pin}</h4>"
            # Mở bảng mới
            html += """
            <table>
                <tr>
                    <th>PIN</th>
                    <th>Thời gian</th>
                    <th>Thiết bị</th>
                    <th>Khu vực</th>
                    <th>Tên</th>
                </tr>
            """
        # Thêm dòng dữ liệu
        html += f"""
            <tr>
                <td>{row.pin}</td>
                <td>{row.create_time}</td>
                <td>{row.dev_alias}</td>
                <td>{row.area_name}</td>
                <td>{row.name}</td>
            </tr>
        """
    # Đóng bảng cuối cùng
    if current_pin is not None:
        html += "</table>"

    html += "</body></html>"
    return html

def send_email(subject, body_html, receiver):
    msg = MIMEMultipart('alternative')
    msg['From'] = SMTP_CONFIG['sender']
    msg['To'] = receiver
    msg['Subject'] = subject

    part_plain = MIMEText("Dữ liệu đính kèm dạng bảng. Vui lòng xem email hỗ trợ HTML.", 'plain')
    part_html = MIMEText(body_html, 'html')
    msg.attach(part_plain)
    msg.attach(part_html)

    with smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port']) as server:
        server.starttls()
        server.login(SMTP_CONFIG['sender'], SMTP_CONFIG['password'])
        server.send_message(msg)

def main():
    try:
        rows, start_time, end_time = fetch_data()
        subject = f"Báo cáo dữ liệu - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        body = build_email_body(rows, start_time, end_time)
        send_email(subject, body, RECEIVER)
        print("✅ Gửi mail thành công!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main()