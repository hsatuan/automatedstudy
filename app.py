import streamlit as st
import os
from database import get_approved_news, get_pending_news, approve_news, reject_news
from utils import generate_content, text_to_speech
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Hệ Sinh Thái Tri Thức Tự Động Hóa",
    page_icon="🤖",
    layout="wide"
)

# Khởi tạo bộ nhớ tạm để giữ trạng thái hệ thống ổn định
if "ai_response" not in st.session_state:
    st.session_state.ai_response = None
if "audio_ready" not in st.session_state:
    st.session_state.audio_ready = False
if "topic_from_news" not in st.session_state:
    st.session_state.topic_from_news = ""
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# THANH ĐIỀU HƯỚNG SIDEBAR
st.sidebar.title("🤖 MENU HỆ THỐNG")
menu_selected = st.sidebar.radio(
    "Di chuyển giữa các phân hệ:",
    ["📰 Bản Tin Tự Động Hóa (Báo Mới)", "📚 Trợ Lý Bài Giảng AI (Phần 1)", "🔐 Tab Quản Trị Hệ Thống"]
)

# -----------------------------------------------------------------
# PHÂN HỆ 1: BẢN TIN TỰ ĐỘNG HÓA (GIAO DIỆN CHUẨN BAOMOI.COM 3 TẦNG)
# -----------------------------------------------------------------
if menu_selected == "📰 Bản Tin Tự Động Hóa (Báo Mới)":
    st.title("📰 Tin Tức & Ứng Dụng Mới Ngành Tự Động Hóa")
    st.caption("Kênh tổng hợp thông tin cấu trúc đa tầng chuẩn phong cách Baomoi.com")
    st.markdown("---")
    
    approved_articles = get_approved_news()
    
    if not approved_articles:
        st.info("Chưa có bản tin nào được duyệt đăng. Vui lòng vào 'Tab Quản Trị' nhập mật khẩu và quét tin tức từ Internet!")
    else:
        # Cấu trúc lặp qua từng cụm Block (Mỗi block tối đa 5 bài tin)
        # Để tạo sự đa dạng, chúng ta gom nhóm các bài báo thành từng Block lớn
        block_size = 5
        for b_idx in range(0, len(approved_articles), block_size):
            block_articles = approved_articles[b_idx:b_idx + block_size]
            
            st.markdown(f"### 🌐 CỤM TIN CÔNG NGHỆ CHUYỂN ĐỘNG #{ (b_idx//block_size) + 1 }")
            
            # --- TẦNG 1: Dòng đầu tiên - 1 Tin lớn có ảnh to chiếm trọn không gian ---
            hot_news = block_articles[0]
            col_hot_img, col_hot_txt = st.columns([1, 1], gap="medium")
            with col_hot_img:
                if hot_news[3]:
                    st.image(hot_news[3], width="stretch")
                else:
                    st.image("https://via.placeholder.com/600x350", width="stretch")
            with col_hot_txt:
                st.subheader(hot_news[1])
                st.caption(f"📅 *Báo mới đăng* | {hot_news[4]}")
                st.write("Bản tin tự động hóa công nghiệp được chọn lọc phân tích chuyên sâu.")
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f'<a href="{hot_news[2]}" target="_blank"><button style="background-color: #008CBA; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-weight: bold; width: 100%;">🔗 Xem bài gốc</button></a>', unsafe_allow_html=True)
                with c2:
                    if st.button("🤖 Chuyển thành bài giảng AI", key=f"btn_hot_{hot_news[0]}", use_container_width=True):
                        st.session_state.topic_from_news = hot_news[1]
                        st.success("Đã ghi nhớ! Mời qua tab Trợ Lý AI.")
            
            st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
            
            # --- TẦNG 2: Dòng thứ hai - Chia thành 2 cột độc lập, mỗi cột 1 tin ---
            sub_articles_tier2 = block_articles[1:3]
            if sub_articles_tier2:
                col_t2_1, col_t2_2 = st.columns(2, gap="large")
                
                for idx, news in enumerate(sub_articles_tier2):
                    target_col = col_t2_1 if idx == 0 else col_t2_2
                    with target_col:
                        if news[3]:
                            st.image(news[3], width="stretch")
                        else:
                            st.image("https://via.placeholder.com/300x180", width="stretch")
                        st.markdown(f"##### {news[1]}")
                        st.caption(f"📅 {news[4]}")
                        
                        cx1, cx2 = st.columns(2)
                        with cx1:
                            st.markdown(f'<a href="{news[2]}" target="_blank" style="text-decoration:none; color:#008CBA; font-weight:bold; font-size:13px;">👉 Đọc nguồn</a>', unsafe_allow_html=True)
                        with cx2:
                            if st.button("🤖 Học bài", key=f"btn_t2_{news[0]}"):
                                st.session_state.topic_from_news = news[1]
                                st.success("Đã nạp tiêu đề!")
            
            st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
            
            # --- TẦNG 3: Dòng thứ ba trở đi - Trở về dạng 1 cột dọc bài viết ---
            sub_articles_tier3 = block_articles[3:5]
            for news in sub_articles_tier3:
                col_t3_img, col_t3_txt = st.columns([1, 4])
                with col_t3_img:
                    if news[3]:
                        st.image(news[3], width="stretch")
                    else:
                        st.image("https://via.placeholder.com/150", width="stretch")
                with col_t3_txt:
                    st.markdown(f"**{news[1]}**")
                    st.caption(f"📅 {news[4]} | [🔗 Ghé thăm trang gốc]({news[2]})")
                    if st.button("🤖 Chuyển sang phòng học AI", key=f"btn_t3_{news[0]}"):
                        st.session_state.topic_from_news = news[1]
                        st.success("Đã chuyển!")
                st.markdown("<hr style='margin: 10px 0; border-top: 1px dashed #ddd;' />", unsafe_allow_html=True)
            
            st.markdown("<br><hr style='border-top: 3px double #bbb;' /><br>", unsafe_allow_html=True)

# -----------------------------------------------------------------
# PHÂN HỆ 2: TRỢ LÝ BÀI GIẢNG AI (CẬP NHẬT TRÁNH CRASH KHI HẾT QUOTA GEMINI)
# -----------------------------------------------------------------
elif menu_selected == "📚 Trợ Lý Bài Giảng AI (Phần 1)":
    st.title("📚 Trợ Lý Học Tập Tự Động Hóa Thông Minh")
    st.markdown("---")
    
    cap_do = st.sidebar.radio("Cấp độ bài học:", ["Dễ hiểu", "Trung bình", "Chuyên sâu"], index=1)
    default_topic = st.session_state.topic_from_news if st.session_state.topic_from_news else "Lập trình hệ thống tự động hóa PLC, SCADA"
    user_input = st.text_input("Chủ đề học tập:", value=default_topic)
    
    if st.button("🚀 Kích hoạt phòng học AI"):
        with st.spinner("Giáo sư AI đang biên soạn giáo trình..."):
            res = generate_content(user_input, cap_do)
            
            # Bắt lỗi cạn kiệt Quota API để dừng xử lý TTS, bảo vệ hệ thống
            if "RESOURCE_EXHAUSTED" in res or "Lỗi" in res:
                st.session_state.ai_response = res
                st.session_state.audio_ready = False
            else:
                st.session_state.ai_response = res
                audio_file_path = "lesson_audio.mp3"
                if os.path.exists(audio_file_path):
                    try: os.remove(audio_file_path)
                    except: pass
                success = text_to_speech(res, audio_file_path)
                st.session_state.audio_ready = success

    if st.session_state.ai_response:
        if "RESOURCE_EXHAUSTED" in st.session_state.ai_response:
            st.error("⚠️ Khóa API Gemini Miễn Phí của bạn hiện tại đã tạm thời hết lượt dùng trong ngày hôm nay (Vượt quá Quota giới hạn). Vui lòng thử lại sau vài phút hoặc đổi API Key mới trong file `.env` nhé!")
        else:
            tab1, tab2 = st.tabs(["📖 Bài Giảng & Audio", "✍️ Phiếu Trắc Nghiệm Đánh Giá"])
            with tab1:
                if st.session_state.audio_ready and os.path.exists("lesson_audio.mp3"):
                    st.audio("lesson_audio.mp3", format="audio/mp3")
                st.markdown(st.session_state.ai_response.split("---")[0])
            with tab2:
                if "---" in st.session_state.ai_response:
                    st.markdown(st.session_state.ai_response.split("---")[1])

# -----------------------------------------------------------------
# PHÂN HỆ 3: TAB QUẢN TRỊ HỆ THỐNG
# -----------------------------------------------------------------
elif menu_selected == "🔐 Tab Quản Trị Hệ Thống":
    st.title("🔐 Cổng Quản Trị Hệ Thống")
    st.markdown("---")
    
    correct_password = os.getenv("ADMIN_PASSWORD", "123456")
    
    if not st.session_state.admin_logged_in:
        password_input = st.text_input("Nhập mật khẩu quản trị:", type="password")
        if st.button("🔑 Đăng nhập"):
            if password_input == correct_password:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Mật khẩu sai!")
                
    if st.session_state.admin_logged_in:
        col_actions, col_view = st.columns([1, 1], gap="medium")
        with col_actions:
            st.subheader("🛠️ Hành động")
            # Nút quét dữ liệu được cô lập
            if st.button("🔍 Quét & Tìm kiếm dữ liệu mới", type="primary"):
                from utils import scrape_automation_news
                with st.spinner("Đang cào dữ liệu công nghệ..."):
                    num = scrape_automation_news()
                    st.success(f"Tìm thấy thành công {num} bài viết mới trong hàng đợi!")
                    st.rerun()
            
            if st.button("🚪 Đăng xuất"):
                st.session_state.admin_logged_in = False
                st.rerun()
                
        with col_view:
            st.subheader("📋 Danh sách chờ phê duyệt (Pending)")
            pending_list = get_pending_news()
            if not pending_list:
                st.info("Hàng chờ trống! Hãy nhấn nút quét để nạp dữ liệu.")
            else:
                for news_id, title, link, image, pub_date in pending_list:
                    with st.expander(f"📰 {title}"):
                        st.write(f"Nguồn: {link}")
                        if image: st.image(image, width=150)
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Duyệt", key=f"ok_{news_id}"):
                                approve_news(news_id)
                                st.rerun()
                        with c2:
                            if st.button("❌ Bỏ qua", key=f"no_{news_id}"):
                                reject_news(news_id)
                                st.rerun()