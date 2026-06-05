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
    HÀM SỬA ĐỔI PHẦN 2: Tự động quét và tìm kiếm tin tức Tự động hóa mới nhất
    Sử dụng các kênh dữ liệu RSS hoạt động chính xác 100% vào năm 2026.
    """
    # Thay thế nguồn lỗi bằng các nguồn RSS công nghệ, khoa học đang hoạt động ổn định
    rss_urls = [
        "https://vnexpress.net/rss/khoa-hoc.rss",
        "https://vnexpress.net/rss/so-hoa.rss",
        "https://vietnamnet.vn/rss/cong-nghe.rss"
    ]
    
    keywords = ["tự động hóa", "robot", "cnc", "iot", "điều khiển", "nhà máy", "bộ điều khiển", "trí tuệ nhân tạo", "chip", "bán dẫn"]
    count = 0
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in rss_urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            for item in root.findall('.//item'):
                title = item.find('title').text
                link = item.find('link').text
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                # Kiểm tra xem tiêu đề bài báo có chứa từ khóa liên quan đến Tự động hóa hay không
                if any(kw in title.lower() for kw in keywords):
                    # Tự động quét ảnh đại diện OpenGraph từ link gốc bài viết
                    image_url = "https://via.placeholder.com/150"  # Ảnh mặc định nếu lỗi
                    try:
                        og = OpenGraph(url=link)
                        if og.is_valid() and 'image' in og:
                            image_url = og['image']
                    except:
                        pass
                    
                    # Đẩy bài viết vào hàng chờ duyệt trong cơ sở dữ liệu
                    add_pending_news(title, link, image_url, pub_date)
                    count += 1
        except Exception as e:
            print(f"Lỗi khi quét nguồn {url}: {e}")
            
    return count

