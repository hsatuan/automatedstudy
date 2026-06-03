import os
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from opengraph_py3 import OpenGraph
from google import genai
from dotenv import load_dotenv
from database import add_pending_news

# Tải cấu hình bảo mật từ file .env
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")

if gemini_key:
    client = genai.Client(api_key=gemini_key)
else:
    client = None

def clean_markdown_for_tts(text):
    if "Lỗi" in text or "NOT_FOUND" in text:
        return "Hệ thống đang xử lý dữ liệu."
    if "---" in text:
        text = text.split("---")[0]
    clean_text = re.sub(r'[\#\*\_\[\]\-\-\-\:\d\.]', ' ', text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def generate_content(topic, level):
    if not client:
        return "Lỗi: Chưa cấu hình API Key trong file .env."
        
    prompt = f"""
    Bạn là một Giáo sư Đầu ngành kiêm Giảng viên cao cấp chuyên ngành Tự động hóa.
    Hãy biên soạn một bài giảng cực kỳ chi tiết, phong phú và đầy đủ kiến thức về chủ đề hoặc bài viết sau: "{topic}".
    Yêu cầu trình độ giải thích bám sát mức độ nhận thức: {level}.
    
    Hãy cấu trúc nội dung trả về CHÍNH XÁC theo form sau:
    
    # BÀI GIẢNG CHI TIẾT
    [Viết bài giảng chuyên sâu từ 800 - 1000 từ. Phải bao gồm: Tổng quan, Cấu trúc hệ thống, Nguyên lý vận hành và Ứng dụng thực tế mới nhất].
    
    ---
    # BỘ CÂU HỎI TRẮC NGHIỆM ĐÁNH GIÁ
    [Tạo đúng 5 câu hỏi trắc nghiệm chuyên sâu, viết theo định dạng cấu trúc chính xác dưới đây]:
    
    Câu 1: Nội dung câu hỏi 1
    A. Đáp án A
    B. Đáp án B
    C. Đáp án C
    D. Đáp án D
    Đáp án đúng: A
    
    Câu 2: Nội dung câu hỏi 2
    A. Đáp án A
    B. Đáp án B
    C. Đáp án C
    D. Đáp án D
    Đáp án đúng: B
    
    Câu 3: Nội dung câu hỏi 3
    A. Đáp án A
    B. Đáp án B
    C. Đáp án C
    D. Đáp án D
    Đáp án đúng: C
    
    Câu 4: Nội dung câu hỏi 4
    A. Đáp án A
    B. Đáp án B
    C. Đáp án C
    D. Đáp án D
    Đáp án đúng: D
    
    Câu 5: Nội dung câu hỏi 5
    A. Đáp án A
    B. Đáp án B
    C. Đáp án C
    D. Đáp án D
    Đáp án đúng: A
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text
    except Exception as e:
        return f"Lỗi khi gọi Gemini API: {str(e)}"

def text_to_speech(text, output_path):
    try:
        plain_text = clean_markdown_for_tts(text)
        short_text = plain_text[:800] 
        if not short_text or len(short_text) < 5:
            return False
        command = ["edge-tts", "--voice", "vi-VN-HoaiAnNeural", "--text", short_text, "--write-media", output_path]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception as e:
        print(f"Lỗi hệ thống âm thanh TTS: {e}")
        return False

def scrape_automation_news():
    """
    HÀM ĐÃ SỬA LỖI: Tự động quét tin tức, tối ưu cấu trúc XML an toàn chống crash
    """
    # Chuẩn hóa lại các đường dẫn RSS Feeds hoạt động ổn định nhất hiện tại
    rss_urls = [
        "https://vnexpress.net/rss/khoa-hoc.rss",
        "https://vnexpress.net/rss/so-hoa.rss",
        "https://tuoitre.vn/rss/khoa-hoc-cong-nghe.rss",
        "https://vietnamnet.vn/rss/cong-nghe.rss",
        "https://thanhnien.vn/rss/cong-nghe-thong-tin.rss",
        "https://dantri.com.vn/suc-manh-so.rss",
        "https://tinhte.vn/rss/"
    ]
    
    # ĐÃ VÁ LỖI CÚ PHÁP: Bổ sung các dấu phẩy đầy đủ cho mảng từ khóa
    keywords = [
        "tự động hóa", "robot", "cnc", "iot", "điều khiển", "nhà máy", "bộ điều khiển", "trí tuệ nhân tạo",
        "kỹ thuật điều khiển", "nguyên lý điều khiển", "hệ thống cảm biến", "actuator", "điện tử",  
        "vi điều khiển", "mạch điện", "lập trình nhúng", "lập trình plc", "hệ thống giám sát scada", 
        "giao diện người – máy", "robot học", "cơ cấu robot", "điều khiển động học", "lập trình robot", 
        "mạng công nghiệp", "giao thức truyền thông công nghiệp", "lắp ráp thiết bị tự động hóa", 
        "vận hành thiết bị tự động hóa", "bảo trì thiết bị tự động hóa", "dự án tự động hóa", 
        "đo lường và cảm biến", "thiết kế điện dân dụng", "giám sát hệ thống", "quản lý dự án công nghiệp", 
        "nghiên cứu giải pháp tự động hóa", "phát triển giải pháp tự động hóa", "giải pháp tự động hóa"
    ]
    
    count = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for url in rss_urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            for item in root.findall('.//item'):
                try:
                    # BẢO VỆ AN TOÀN: Kiểm tra xem các thẻ XML có tồn tại text hay không để tránh lỗi NoneType
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    
                    if title_elem is None or link_elem is None or not title_elem.text or not link_elem.text:
                        continue  # Bỏ qua bản tin bị lỗi cấu trúc, chạy tiếp bài sau
                        
                    title = title_elem.text.strip()
                    link = link_elem.text.strip()
                    
                    pub_date_elem = item.find('pubDate')
                    pub_date = pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else ""
                    
                    # Kiểm tra từ khóa thông minh bằng cách chuẩn hóa chữ thường
                    if any(kw in title.lower() for kw in keywords):
                        image_url = "https://via.placeholder.com/150"
                        try:
                            # Tách OpenGraph lấy ảnh đại diện, bọc trong try-except để nếu lỗi link vẫn không làm dừng vòng lặp
                            og = OpenGraph(url=link)
                            if og.is_valid() and 'image' in og:
                                image_url = og['image']
                        except:
                            pass
                        
                        add_pending_news(title, link, image_url, pub_date)
                        count += 1
                except Exception as item_error:
                    # Lỗi ở một bài viết nhỏ không làm sập việc quét các bài viết khác
                    continue
                    
        except Exception as e:
            print(f"Lỗi khi quét nguồn RSS [{url}]: {e}")
            
    return count