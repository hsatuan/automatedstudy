import streamlit as st
import os
from database import get_approved_news, get_pending_news, approve_news, reject_news
from utils import generate_content, text_to_speech, scrape_automation_news
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Hệ Sinh Thái Tri Thức Tự Động Hóa",
    page_icon="🤖",
    layout="wide"
)

# Khởi tạo bộ nhớ tạm để giữ trạng thái bài giảng
if "ai_response" not in st.session_state:
    st.session_state.ai_response = None
if "audio_ready" not in st.session_state:
    st.session_state.audio_ready = False
if "topic_from_news" not in st.session_state:
    st.session_state.topic_from_news = ""

# THANH ĐIỀU HƯỚNG SIDEBAR
st.sidebar.title("🤖 MENU HỆ THỐNG")
menu_selected = st.sidebar.radio(
    "Di chuyển giữa các phân hệ:",
    ["📰 Bản Tin Tự Động Hóa (Báo Mới)", "📚 Trợ Lý Bài Giảng AI (Phần 1)", "🔐 Tab Quản Trị Hệ Thống"]
)

# -----------------------------------------------------------------
# PHÂN HỆ 1: BẢN TIN TỰ ĐỘNG HÓA (GIAO DIỆN PHONG CÁCH BAOMOI)
# -----------------------------------------------------------------
if menu_selected == "📰 Bản Tin Tự Động Hóa (Báo Mới)":
    st.title("📰 Tin Tức & Ứng Dụng Mới Ngành Tự Động Hóa")
    st.caption("Kênh tổng hợp thông tin công nghệ tiên tiến được chọn lọc từ người quản trị.")
    st.markdown("---")
    
    approved_articles = get_approved_news()
    
    if not approved_articles:
        st.info("Chưa có bản tin nào được duyệt đăng. Vui lòng vào 'Tab Quản Trị' nhập mật khẩu và quét tin tức từ Internet!")
    else:
        for article_id, title, link, image, pub_date in approved_articles:
            # Tạo layout dạng khung bao giống Báo Mới: Ảnh bên trái, Tiêu đề bên phải
            col1, col2 = st.columns([1, 4])
            with col1:
                if image:
                    st.image(image, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150", use_container_width=True)
            with col2:
                st.subheader(title)
                st.write(f"📅 *Ngày đăng:* {pub_date}")
                
                # MỞ TAB MỚI THEO YÊU CẦU: Sử dụng thẻ HTML Target="_blank" để bảo vệ bản quyền trang gốc
                link_html = f'<a href="{link}" target="_blank" style="text-decoration: none;"><button style="background-color: #008CBA; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: bold;">🔗 Đọc bài viết gốc</button></a>'
                st.markdown(link_html, unsafe_allow_html=True)
                
                st.write("")
                # NÚT ĐẨY SANG HỌC TẬP: Lưu chủ đề bài báo vào bộ nhớ và nhảy sang Tab Trợ lý học tập
                if st.button(f"🤖 Chuyển bài viết này thành bài giảng AI", key=f"learn_{article_id}"):
                    st.session_state.topic_from_news = title
                    st.success(f"Đã ghi nhớ chủ đề! Hãy bấm chọn mục '📚 Trợ Lý Bài Giảng AI (Phần 1)' ở cột trái để bắt đầu học.")

# -----------------------------------------------------------------
# PHÂN HỆ 2: TRỢ LÝ BÀI GIẢNG AI (PHẦN 1 ĐÃ HOÀN THÀNH)
# -----------------------------------------------------------------
elif menu_selected == "📚 Trợ Lý Bài Giảng AI (Phần 1)":
    st.title("📚 Trợ Lý Học Tập Tự Động Hóa Thông Minh")
    st.caption("Cá nhân hóa tri thức: Bài giảng chuyên sâu - Giọng đọc AI - 5 Câu hỏi trắc nghiệm")
    st.markdown("---")
    
    st.sidebar.header("🎯 Cấu hình bài học")
    cap_do = st.sidebar.radio(
        "Chọn cấp độ giải thích:",
        ["Dễ hiểu (Mới bắt đầu)", "Trung bình (Có nền tảng)", "Chuyên sâu (Nghiên cứu cấu trúc kỹ thuật)"], index=1
    )
    
    # Nếu học sinh vừa chọn nút đẩy từ bài báo sang, tự động điền tiêu đề vào ô nhập liệu
    default_topic = st.session_state.topic_from_news if st.session_state.topic_from_news else "Lập trình hệ thống tự động hóa PLC, SCADA"
    
    user_input = st.text_input("Chủ đề cụ thể bạn muốn nghiên cứu học tập:", value=default_topic)
    
    if st.button("🚀 Kích hoạt phòng học AI"):
        with st.spinner("Giáo sư AI đang biên soạn giáo trình và tạo đề kiểm tra..."):
            res = generate_content(user_input, cap_do)
            st.session_state.ai_response = res
            
            audio_file_path = "lesson_audio.mp3"
            if os.path.exists(audio_file_path):
                try: os.remove(audio_file_path)
                except: pass
                
            with st.spinner("Đang chuyển ngữ bài giảng thành file nghe..."):
                success = text_to_speech(res, audio_file_path)
                st.session_state.audio_ready = success

    if st.session_state.ai_response:
        full_text = st.session_state.ai_response
        if "---" in full_text:
            parts = full_text.split("---")
            bai_giang_part = parts[0]
            quiz_part = parts[1]
        else:
            bai_giang_part = full_text
            quiz_part = ""

        tab1, tab2 = st.tabs(["📖 Bài Giảng & Audio", "✍️ Phiếu Trắc Nghiệm Đánh Giá"])
        with tab1:
            if st.session_state.audio_ready and os.path.exists("lesson_audio.mp3"):
                st.audio("lesson_audio.mp3", format="audio/mp3")
            st.markdown(bai_giang_part)
        with tab2:
            if quiz_part:
                st.markdown(quiz_part)
            else:
                st.info("Câu hỏi trắc nghiệm tích hợp trực tiếp trong văn bản bài giảng.")

# -----------------------------------------------------------------
# PHÂN HỆ 3: TAB QUẢN TRỊ BẢO MẬT (DUYỆT TIN TỨC)
# -----------------------------------------------------------------
elif menu_selected == "🔐 Tab Quản Trị Hệ Thống":
    st.title("🔐 Cổng Quản Trị & Phê Duyệt Tin Tức Internet")
    st.markdown("---")
    
    # Kiểm tra mật khẩu an toàn
    password_input = st.text_input("Nhập mật khẩu quản trị để truy cập:", type="password")
    correct_password = os.getenv("ADMIN_PASSWORD", "123456")
    
    if password_input != correct_password:
        st.warning("Vui lòng nhập chính xác mật khẩu Admin được cấu hình trong file .env để thực hiện duyệt bài.")
    else:
        st.success("Mật khẩu chính xác! Đang mở bảng điều khiển quản trị.")
        
        # NÚT BẤM KÍCH HOẠT SCRAPE CÀO TIN TỰ ĐỘNG TRONG 3 NGÀY GẦN NHẤT
        if st.button("🔍 Quét & Tìm kiếm tin tức Tự động hóa mới trên Internet"):
            with st.spinner("Hệ thống robot đang dò tìm bài viết từ các trang khoa học công nghệ uy tín..."):
                num_scraped = scrape_automation_news()
                st.balloons()
                st.success(f"Quét thành công! Tìm thấy thêm {num_scraped} bài viết liên quan ngành Tự động hóa ở hàng chờ.")
        
        st.subheader("📋 Danh sách các bài viết chờ phê duyệt (Pending)")
        pending_list = get_pending_news()
        
        if not pending_list:
            st.info("Hiện tại hàng chờ trống. Hãy bấm nút 'Quét & Tìm kiếm' ở trên để cập nhật tin mới từ Internet.")
        else:
            for news_id, title, link, image, pub_date in pending_list:
                with st.expander(f"📰 {title} ({pub_date})"):
                    st.write(f"🔗 **Đường dẫn gốc:** {link}")
                    if image:
                        st.image(image, width=200)
                    
                    # Tạo 2 nút Duyệt đăng hoặc Bỏ qua trên cùng 1 hàng
                    c1, c2, c3 = st.columns([1, 1, 4])
                    with c1:
                        if st.button("✅ Duyệt Đăng", key=f"app_{news_id}"):
                            approve_news(news_id)
                            st.rerun()
                    with c2:
                        if st.button("❌ Bỏ Qua", key=f"rej_{news_id}"):
                            reject_news(news_id)
                            st.rerun()