import streamlit as st
import cv2
import numpy as np
import pandas as pd
import time
import base64
from openai import OpenAI
import pdfplumber # 换用更强的 PDF 解析库

# -----------------------------------------------------------------------------
# 1. 全局配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BioPocket V19 CN", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. 样式优化 (强制黑字 + 中文排版优化)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        h1 {font-family: 'Helvetica Neue', sans-serif; font-weight: 700; color: #0E1117;}
        
        /* 结果卡片 */
        .result-card {
            background-color: #e3f2fd; 
            padding: 25px;
            border-radius: 12px;
            border-left: 6px solid #1565c0; 
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* 强制黑字 & 优化阅读体验 */
        .result-card, .result-card p, .result-card li, .result-card div, .result-card span {
            color: #1a1a1a !important; 
            font-size: 16px !important;
            line-height: 1.8 !important; /* 增加行高，更易读 */
            font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif !important;
        }
        
        .result-card h3 { 
            color: #0d47a1 !important; 
            margin-top: 0 !important; 
            margin-bottom: 20px !important;
            font-size: 20px !important;
            font-weight: 800 !important; 
            border-bottom: 1px solid #bbdefb;
            padding-bottom: 10px;
        }
        
        .result-card h4 { 
            color: #0277bd !important; 
            font-weight: bold !important; 
            margin-top: 20px !important;
            margin-bottom: 10px !important;
            font-size: 18px !important;
        }

        /* 试剂卡片 (绿色) */
        .reagent-card {
            background-color: #e8f5e9;
            border-left: 6px solid #2e7d32;
        }
        .reagent-card h3 { color: #1b5e20 !important; }
        
        /* 流程卡片 (橙色) */
        .protocol-card {
            background-color: #fff3e0;
            border-left: 6px solid #ef6c00;
        }
        .protocol-card h3 { color: #e65100 !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 辅助函数
# -----------------------------------------------------------------------------
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# V19 升级版：使用 pdfplumber 解析 (抗乱码能力强)
def read_full_pdf(uploaded_file):
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # 遍历每一页
            for page in pdf.pages:
                # 提取文字
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        return None

# -----------------------------------------------------------------------------
# 4. 侧边栏
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022288.png", width=60)
    st.title("BioPocket")
    st.caption("v19.0 | 中文深度解析版")
    st.markdown("---")
    
    menu = st.radio("功能导航", ["📊 看板", "🧫 智能计数", "📷 仪器识别", "📄 文献深读 (Pro)"], index=3)
    
    if menu in ["📷 仪器识别", "📄 文献深读 (Pro)"]:
        st.markdown("---")
        st.markdown("#### 🔑 AI 模型配置")
        st.info("推荐使用 **智谱GLM-4V**")
        api_key = st.text_input("API Key (粘贴在这里)", type="password")
        
        with st.expander("高级设置"):
            base_url = st.text_input("Base URL", value="https://open.bigmodel.cn/api/paas/v4/")
            model_name = st.text_input("Model Name", value="glm-4v")

# -----------------------------------------------------------------------------
# 5. 主逻辑
# -----------------------------------------------------------------------------

if "看板" in menu:
    st.title("📊 实验室综合管控台")
    col1, col2, col3 = st.columns(3)
    col1.metric("已识别样本", "1,520+", "+24%")
    col2.metric("深度阅读", "102 篇", "+12")
    col3.metric("AI 算力", "Online", "GLM-4V")
    st.image("https://images.unsplash.com/photo-1532094349884-543bc11b234d", caption="AI 赋能每一位科研人员", use_container_width=True)

elif "计数" in menu:
    # (保持 V16 完整代码，此处简写)
    st.title("🧫 智能生物计数 (Bio-Counter)")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("### 🛠️ 模式与参数")
        with st.container(border=True):
            count_mode = st.radio("检测目标", ["🧫 细菌菌落", "🦠 噬菌体空斑", "🩸 细胞/微粒"])
            if count_mode == "🧫 细菌菌落": d_l, d_m = True, 10
            elif count_mode == "🦠 噬菌体空斑": d_l, d_m = False, 5
            else: d_l, d_m = False, 2
            roi = st.slider("ROI半径", 10, 500, 280)
            is_light = st.checkbox("目标是亮的", value=d_l)
            clahe = st.checkbox("增强", value=True)
            th_val = st.slider("阈值", 0, 255, 140)
            min_a = st.slider("最小面积", 1, 200, d_m)
        up = st.file_uploader("上传", type=['jpg','png'])
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
            st.image(res, channels="BGR", caption=f"Count: {c}")
            st.success(f"计数: {c}")

elif "仪器" in menu:
    # (保持 V14 完整代码，Prompt 使用中文)
    st.title("📷 实验室 AI 慧眼")
    c1, c2 = st.columns([1, 1.5])
    with c1:
        cam = st.camera_input("拍照")
        up = st.file_uploader("或上传", type=["jpg","png"], key="i_up")
        f_img = cam if cam else up
    with c2:
        if f_img and st.button("识别", key="btn_i"):
            if not api_key: st.error("No Key")
            else:
                try:
                    cli = OpenAI(api_key=api_key, base_url=base_url)
                    b64 = encode_image(f_img.getvalue())
                    p = "你是一位专家。请识别仪器名称、功能、SOP和风险。使用中文。用HTML输出class='result-card'。"
                    r = cli.chat.completions.create(model=model_name, messages=[{"role":"user","content":[{"type":"text","text":p},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}])
                    st.markdown(r.choices[0].message.content, unsafe_allow_html=True)
                except Exception as e: st.error(str(e))

# === 页面 4: 文献深读 (V19 修复版) ===
elif "文献" in menu:
    st.title("📄 文献深度解析 (Deep Reader CN)")
    
    st.info("💡 独家功能：自动提取【试剂清单】并生成【中文实验流程】。支持中英文 PDF。")
    
    uploaded_pdf = st.file_uploader("上传 PDF 全文", type=["pdf"], key="pdf_full")
    
    if uploaded_pdf and st.button("🚀 开始中文深度解析", key="btn_full_pdf"):
        if not api_key:
            st.error("❌ 请先在侧边栏填写 API Key！")
        else:
            try:
                with st.spinner("1/3 正在使用 pdfplumber 精准提取文本..."):
                    # 1. 提取文本
                    full_text = read_full_pdf(uploaded_pdf)
                    
                    if not full_text or len(full_text) < 200:
                        st.error("❌ 无法提取文本！这可能是一个【纯图片/扫描版】的 PDF。请上传带有文字层的 PDF。")
                    else:
                        # 显示提取字数，让用户放心
                        st.toast(f"成功提取 {len(full_text)} 字符，正在发送给 AI...", icon="📑")
                        
                        # 截取 (防止 Token 溢出)
                        truncated_text = full_text[:25000] 
                        
                        with st.spinner("2/3 AI 正在阅读并强制翻译为中文..."):
                            client = OpenAI(api_key=api_key, base_url=base_url)
                            
                            # === V19 强力中文提示词 ===
                            deep_prompt = """
                            你是一位精通中英文的资深生物学家。请阅读这篇文献。
                            
                            **核心指令：**
                            1. **必须完全使用中文回答**，禁止出现大段英文。
                            2. **输出内容必须详实**，不要只写一两句话。
                            3. **严格遵守以下 HTML 结构**。

                            请输出以下三张卡片：

                            <div class="result-card">
                                <h3>📑 深度导读 (Deep Review)</h3>
                                <h4>1. 论文标题 (中文翻译)</h4>
                                <p>[在此处翻译标题]</p>
                                <h4>2. 核心发现 (TL;DR)</h4>
                                <p>[用通俗的中文概括核心结论，至少100字]</p>
                                <h4>3. 关键数据支持</h4>
                                <p>[提取文中的关键数据，例如：X指标提升了50%...]</p>
                            </div>

                            <div class="result-card reagent-card">
                                <h3>🧪 智能试剂/设备清单</h3>
                                <p><i>（AI 自动从 Methods 章节提取）</i></p>
                                <ul>
                                   <li><b>关键试剂：</b> [名称] (厂家/型号)</li>
                                   <li><b>关键试剂：</b> [名称] (厂家/型号)</li>
                                   <li><b>实验仪器：</b> [名称] (型号)</li>
                                </ul>
                            </div>

                            <div class="result-card protocol-card">
                                <h3>📋 Step-by-Step 实验流程</h3>
                                <p><i>（复现指南）</i></p>
                                <ol>
                                   <li><b>步骤 1：</b> [详细描述]</li>
                                   <li><b>步骤 2：</b> [详细描述，包含温度、时间等条件]</li>
                                   <li><b>步骤 3：</b> [详细描述]</li>
                                   <li><b>步骤 4：</b> [详细描述]</li>
                                </ol>
                            </div>

                            以下是文献原文内容：
                            """
                            
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": f"{deep_prompt}\n\n{truncated_text}"
                                    }
                                ],
                                max_tokens=2500 # 允许更长的输出
                            )
                            
                        with st.spinner("3/3 正在渲染中文报告..."):
                            time.sleep(1)
                            st.markdown(response.choices[0].message.content, unsafe_allow_html=True)
                            st.success("✅ 中文解析完成！")
                            
            except Exception as e:
                st.error(f"分析出错: {e}")
