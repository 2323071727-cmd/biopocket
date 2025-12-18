import streamlit as st
import cv2
import numpy as np
import pandas as pd
import time
import base64
from openai import OpenAI
import pdfplumber
import re

# -----------------------------------------------------------------------------
# 1. 全局配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BioPocket", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="collapsed" # 默认收起侧边栏，让手机视野更大
)

# -----------------------------------------------------------------------------
# 2. 界面样式 (关键：隐藏网页元素 + 强制黑字)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        /* 【关键】隐藏 Streamlit 顶部的红线、汉堡菜单和 Footer */
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: hidden;}
        
        /* 全局字体与卡片样式 */
        body {font-family: sans-serif;}
        
        .result-card {
            background-color: #f8f9fa; 
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #0d6efd; 
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        /* 强制黑字，防止手机深色模式导致看不清 */
        .result-card, .result-card * {
            color: #212529 !important; 
        }
        
        .result-card h3 { 
            color: #0b5ed7 !important; 
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 10px;
            margin-top: 0 !important;
        }

        .reagent-card { background-color: #f1f8f5; border-left: 5px solid #198754; }
        .reagent-card h3 { color: #157347 !important; }
        
        .protocol-card { background-color: #fff8f0; border-left: 5px solid #fd7e14; }
        .protocol-card h3 { color: #e65100 !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 辅助函数 (核弹级清洗)
# -----------------------------------------------------------------------------
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def read_full_pdf(uploaded_file):
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: text += t + "\n"
        return text
    except Exception as e:
        return None

# === 核弹级清洗函数：只提取 HTML 标签内的内容 ===
def clean_html_output(text):
    if not text: return ""
    # 1. 尝试找到 <div class="result-card"> 的位置
    start_marker = '<div class="result-card"'
    start_index = text.find(start_marker)
    
    # 2. 找到最后一个 </div> 的位置
    end_index = text.rfind('</div>')
    
    # 3. 如果找到了，只截取中间这一段，丢弃所有 Markdown 符号和废话
    if start_index != -1 and end_index != -1:
        return text[start_index : end_index + 6]
    
    # 4. 如果没找到标准头，退回到暴力去除 markdown
    text = re.sub(r'^```html', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^```', '', text)
    text = re.sub(r'```$', '', text)
    return text.strip()

# -----------------------------------------------------------------------------
# 4. 侧边栏
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("[https://cdn-icons-png.flaticon.com/512/3022/3022288.png](https://cdn-icons-png.flaticon.com/512/3022/3022288.png)", width=60)
    st.title("BioPocket")
    st.caption("v21.2 | Mobile Native")
    st.markdown("---")
    
    menu = st.radio(
        "功能模组", 
        ["🏠 工作台", "🧫 智能计数", "📷 仪器识别", "📄 文献精读"], 
        index=0
    )
    
    if menu in ["📷 仪器识别", "📄 文献精读"]:
        st.markdown("---")
        st.info("推荐模型：**智谱 GLM-4**")
        api_key = st.text_input("API Key", type="password")
        with st.expander("设置"):
            base_url = st.text_input("Base URL", value="[https://open.bigmodel.cn/api/paas/v4/](https://open.bigmodel.cn/api/paas/v4/)")

# -----------------------------------------------------------------------------
# 5. 主逻辑区
# -----------------------------------------------------------------------------

if "工作台" in menu:
    st.markdown("### 🚀 实验室工作台")
    col1, col2 = st.columns(2)
    col1.metric("今日样本", "12")
    col2.metric("文献库", "102")
    st.image("[https://images.unsplash.com/photo-1579154204601-01588f351e67](https://images.unsplash.com/photo-1579154204601-01588f351e67)", use_container_width=True)

elif "智能计数" in menu:
    st.markdown("### 🧫 智能计数")
    with st.expander("🛠️ 调整参数", expanded=True):
        count_mode = st.radio("模式", ["细菌 (CFU)", "噬菌体 (PFU)", "细胞"])
        if "细菌" in count_mode: d_l, d_m = True, 10
        elif "噬菌体" in count_mode: d_l, d_m = False, 5
        else: d_l, d_m = False, 2
        roi = st.slider("范围", 10, 500, 280)
        th_val = st.slider("灵敏度", 0, 255, 140)
    
    up = st.file_uploader("上传图片", type=['jpg','png'])
    if up:
        fb = np.asarray(bytearray(up.read()), dtype=np.uint8)
        img = cv2.imdecode(fb, 1)
        # 缩小图片以加快手机处理
        img = cv2.resize(img, (int(img.shape[1]*0.5), int(img.shape[0]*0.5)))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(gray)
        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (img.shape[1]//2, img.shape[0]//2), roi, 255, -1)
        masked = cv2.bitwise_and(gray, gray, mask=mask)
        blur = cv2.GaussianBlur(masked, (5,5), 0)
        if d_l: _, th = cv2.threshold(blur, th_val, 255, cv2.THRESH_BINARY)
        else: _, th = cv2.threshold(blur, th_val, 255, cv2.THRESH_BINARY_INV)
        th = cv2.bitwise_and(th, th, mask=mask)
        cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        res = img.copy()
        cv2.circle(res, (img.shape[1]//2, img.shape[0]//2), roi, (0,0,255), 2)
        c = 0
        for ct in cnts:
            if d_m < cv2.contourArea(ct) < 3000:
                c+=1
                cv2.drawContours(res, [ct], -1, (0,255,0), 2)
        st.image(res, channels="BGR", use_container_width=True)
        st.success(f"计数结果：{c}")

elif "仪器识别" in menu:
    st.markdown("### 📷 仪器识别")
    f_img = st.camera_input("拍照")
    if not f_img: f_img = st.file_uploader("或上传相册", type=["jpg","png"])
    
    if f_img and st.button("开始识别"):
        if not api_key: st.error("请填入 API Key")
        else:
            try:
                with st.spinner("分析中..."):
                    cli = OpenAI(api_key=api_key, base_url=base_url)
                    b64 = encode_image(f_img.getvalue())
                    p = "识别仪器。输出HTML class='result-card'。包括名称、功能、SOP、风险。"
                    r = cli.chat.completions.create(model="glm-4v", messages=[{"role":"user","content":[{"type":"text","text":p},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}] )
                    # 使用核弹级清洗
                    st.markdown(clean_html_output(r.choices[0].message.content), unsafe_allow_html=True)
            except Exception as e: st.error(f"Error: {e}")

elif "文献精读" in menu:
    st.markdown("### 📄 文献精读")
    uploaded_pdf = st.file_uploader("上传 PDF", type=["pdf"])
    if uploaded_pdf and st.button("开始分析"):
        if not api_key: st.error("请填入 API Key")
        else:
            try:
                with st.spinner("读取中..."):
                    full_text = read_full_pdf(uploaded_pdf)
                    if not full_text: st.error("无法读取文本")
                    else:
                        truncated_text = full_text[:80000]
                        with st.spinner("AI 思考中..."):
                            client = OpenAI(api_key=api_key, base_url=base_url)
                            deep_prompt = """
                            精读全文。必须中文。直接输出HTML。
                            结构要求：
                            <div class="result-card"><h3>📑 深度导读</h3>...</div>
                            <div class="result-card reagent-card"><h3>📦 试剂耗材</h3>...</div>
                            <div class="result-card protocol-card"><h3>⚗️ 实验步骤</h3>...</div>
                            """
                            response = client.chat.completions.create(model="glm-4-flash", messages=[{"role": "user", "content": f"{deep_prompt}\n\n{truncated_text}"}], max_tokens=3000)
                            # 使用核弹级清洗
                            st.markdown(clean_html_output(response.choices[0].message.content), unsafe_allow_html=True)
            except Exception as e: st.error(f"Error: {e}")
