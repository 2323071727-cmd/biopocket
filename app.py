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
    page_title="BioPocket Pro", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. 界面样式
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        body {font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;}
        
        .result-card {
            background-color: #f8f9fa; 
            padding: 24px;
            border-radius: 8px;
            border-left: 5px solid #0d6efd; 
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        /* 强制黑字 */
        .result-card, .result-card p, .result-card li, .result-card div, .result-card span {
            color: #212529 !important; 
            font-size: 16px !important;
            line-height: 1.75 !important;
            font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif !important;
        }
        
        .result-card h3 { 
            color: #0b5ed7 !important; 
            margin-top: 0 !important; 
            font-size: 1.25rem !important;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 12px;
            margin-bottom: 16px !important;
        }
        
        .result-card h4 { 
            color: #495057 !important; 
            font-weight: 700 !important; 
            margin-top: 20px !important; 
            font-size: 1.1rem !important;
        }

        .reagent-card { background-color: #f1f8f5; border-left: 5px solid #198754; }
        .reagent-card h3 { color: #157347 !important; }
        
        .protocol-card { background-color: #fff8f0; border-left: 5px solid #fd7e14; }
        .protocol-card h3 { color: #e65100 !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 辅助函数
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

# === V23 强力清洗函数 (修复显示代码的问题) ===
def clean_html_output(text):
    text = text.strip()
    # 1. 去掉开头的 ```html 或 ```xml 或 ``` 
    text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
    # 2. 去掉结尾的 ```
    text = re.sub(r'\n?```$', '', text)
    return text.strip()

# -----------------------------------------------------------------------------
# 4. 侧边栏
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022288.png", width=60)
    st.title("BioPocket")
    st.caption("v23.0 | HTML Rendering Fix")
    st.markdown("---")
    
    menu = st.radio(
        "功能模组 (Modules)", 
        ["🏠 实验室工作台", "🧫 智能计数", "📷 仪器图谱", "📄 文献精读 (Pro)"], 
        index=0
    )
    
    if menu in ["📷 仪器图谱", "📄 文献精读 (Pro)"]:
        st.markdown("---")
        st.markdown("#### 🧠 AI 引擎配置")
        st.info("推荐模型：**智谱 GLM-4**")
        api_key = st.text_input("API Key (在此输入)", type="password")
        
        with st.expander("高级参数设置", expanded=False):
            base_url = st.text_input("Base URL", value="https://open.bigmodel.cn/api/paas/v4/")

# -----------------------------------------------------------------------------
# 5. 主逻辑区
# -----------------------------------------------------------------------------

if "工作台" in menu:
    st.title("🚀 实验室工作台")
    st.markdown("**BioPocket 科研智能体** - 您的口袋实验室助手")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("累计分析样本", "1,524", "+12 今天")
    col2.metric("文献智库", "102 篇", "已索引")
    col3.metric("云端算力", "GLM-4", "Online")
    st.image("https://images.unsplash.com/photo-1532094349884-543bc11b234d", use_container_width=True)

elif "计数" in menu:
    st.title("🧫 智能计数 (AI Counter)")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("### 🛠️ 参数配置")
        with st.container(border=True):
            count_mode = st.radio("检测对象", ["🧫 细菌菌落 (CFU)", "🦠 噬菌体空斑 (PFU)", "🩸 细胞微粒 (Cells)"])
            if "细菌" in count_mode: d_l, d_m = True, 10
            elif "噬菌体" in count_mode: d_l, d_m = False, 5
            else: d_l, d_m = False, 2
            roi = st.slider("ROI 有效半径", 10, 500, 280)
            is_light = st.checkbox("目标为亮色", value=d_l)
            clahe = st.checkbox("自适应增强", value=True)
            th_val = st.slider("阈值灵敏度", 0, 255, 140)
            min_a = st.slider("最小面积过滤", 1, 200, d_m)
        up = st.file_uploader("上传实验图像", type=['jpg','png'])
    with c2:
        if up:
            fb = np.asarray(bytearray(up.read()), dtype=np.uint8)
            img = cv2.imdecode(fb, 1)
            img = cv2.resize(img, (int(img.shape[1]*0.6), int(img.shape[0]*0.6)))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if clahe: gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(gray)
            mask = np.zeros(img.shape[:2], dtype=np.uint8)
            cv2.circle(mask, (img.shape[1]//2, img.shape[0]//2), roi, 255, -1)
            masked = cv2.bitwise_and(gray, gray, mask=mask)
            blur = cv2.GaussianBlur(masked, (5,5), 0)
            if is_light: _, th = cv2.threshold(blur, th_val, 255, cv2.THRESH_BINARY)
            else: _, th = cv2.threshold(blur, th_val, 255, cv2.THRESH_BINARY_INV)
            th = cv2.bitwise_and(th, th, mask=mask)
            cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            res = img.copy()
            cv2.circle(res, (img.shape[1]//2, img.shape[0]//2), roi, (0,0,255), 2)
            c = 0
            for ct in cnts:
                if min_a < cv2.contourArea(ct) < 3000:
                    c+=1
                    cv2.drawContours(res, [ct], -1, (0,255,0), 2)
            st.image(res, channels="BGR", caption=f"识别结果: {c}", use_container_width=True)
            st.success(f"✅ 计数完成：**{c}**")

elif "仪器" in menu:
    st.title("📷 仪器图谱 (Instrument ID)")
    c1, c2 = st.columns([1, 1.5])
    with c1:
        cam = st.camera_input("拍摄")
        up = st.file_uploader("或上传", type=["jpg","png"], key="i_up")
        f_img = cam if cam else up
    with c2:
        if f_img and st.button("开始识别", key="btn_i"):
            if not api_key: st.error("❌ 请先配置 API Key")
            else:
                try:
                    with st.spinner("🚀 识别中..."):
                        cli = OpenAI(api_key=api_key, base_url=base_url)
                        b64 = encode_image(f_img.getvalue())
                        p = "你是一位专家。请识别仪器。输出HTML class='result-card'。不要使用markdown代码块。"
                        r = cli.chat.completions.create(model="glm-4v", messages=[{"role":"user","content":[{"type":"text","text":p},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}] )
                        # 使用 V23 强力清洗
                        clean = clean_html_output(r.choices[0].message.content)
                        st.markdown(clean, unsafe_allow_html=True)
                        st.success("✅ 检索成功")
                except Exception as e: st.error(f"Error: {e}")

elif "文献" in menu:
    st.title("📄 文献精读 (Paper Agent)")
    st.info("💡 全文深度解析引擎：支持超长 PDF。")
    uploaded_pdf = st.file_uploader("上传 PDF 文献全文", type=["pdf"], key="pdf_full")
    if uploaded_pdf and st.button("🚀 开始深度精读", key="btn_full_pdf"):
        if not api_key: st.error("❌ 请先配置 API Key")
        else:
            try:
                with st.spinner("1/3 提取全文..."):
                    full_text = read_full_pdf(uploaded_pdf)
                    if not full_text or len(full_text) < 200: st.error("❌ 文本提取失败")
                    else:
                        st.toast(f"提取成功，字数：{len(full_text)}", icon="📑")
                        truncated_text = full_text[:80000] 
                        with st.spinner("2/3 AI 深度分析..."):
                            cli = OpenAI(api_key=api_key, base_url=base_url)
                            deep_prompt = """
                            你是一位精通中英文的资深生物科学家。精读全文。必须中文回答。
                            **请直接输出HTML代码，不要包裹在 ```html 中。**
                            
                            输出结构（确保使用 class="result-card"）：
                            <div class="result-card"><h3>📑 深度导读</h3><h4>1.标题翻译</h4>...<h4>2.核心发现</h4>...</div>
                            <div class="result-card reagent-card"><h3>📦 关键试剂与耗材</h3><ul>...</ul></div>
                            <div class="result-card protocol-card"><h3>⚗️ 标准化实验流</h3><ol>...</ol></div>
                            """
                            resp = cli.chat.completions.create(model="glm-4-flash", messages=[{"role": "user", "content": f"{deep_prompt}\n\n{truncated_text}"}], max_tokens=3000)
                        
                        # 使用 V23 强力清洗
                        clean = clean_html_output(resp.choices[0].message.content)
                        st.markdown(clean, unsafe_allow_html=True)
                        st.success("✅ 报告已生成")
            except Exception as e: st.error(f"分析中断: {e}")
