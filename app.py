import streamlit as st
import cv2
import numpy as np
import pandas as pd
import time
import base64
from openai import OpenAI
import pdfplumber

# -----------------------------------------------------------------------------
# 1. 全局配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BioPocket V20 Stable", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. 样式优化
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
            line-height: 1.8 !important;
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

def read_full_pdf(uploaded_file):
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
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
    st.caption("v20.0 | Long-Text Fix")
    st.markdown("---")
    
    menu = st.radio("功能导航", ["📊 看板", "🧫 智能计数", "📷 仪器识别", "📄 文献深读 (Pro)"], index=3)
    
    if menu in ["📷 仪器识别", "📄 文献深读 (Pro)"]:
        st.markdown("---")
        st.markdown("#### 🔑 AI 模型配置")
        st.info("推荐使用 **智谱GLM**")
        api_key = st.text_input("API Key (粘贴在这里)", type="password")
        
        # 默认隐藏高级设置，防止误操作
        with st.expander("高级设置 (已自动优化)", expanded=False):
            base_url = st.text_input("Base URL", value="https://open.bigmodel.cn/api/paas/v4/")
            st.caption("V20更新：文献阅读将自动切换至 128k 长文本模型，无需手动设置。")

# -----------------------------------------------------------------------------
# 5. 主逻辑
# -----------------------------------------------------------------------------

if "看板" in menu:
    st.title("📊 实验室综合管控台")
    col1, col2, col3 = st.columns(3)
    col1.metric("已识别样本", "1,520+", "+24%")
    col2.metric("深度阅读", "102 篇", "+12")
    col3.metric("AI 算力", "Online", "GLM-4 Flash")
    st.image("https://images.unsplash.com/photo-1532094349884-543bc11b234d", caption="AI 赋能每一位科研人员", use_container_width=True)

elif "计数" in menu:
    # (保持 V16 完整代码)
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
    # (保持 V14 逻辑 - 视觉任务继续使用 glm-4v)
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
                    with st.spinner("🚀 视觉模型 (GLM-4V) 正在分析..."):
                        cli = OpenAI(api_key=api_key, base_url=base_url)
                        b64 = encode_image(f_img.getvalue())
                        p = "你是一位生物仪器专家。请识别仪器名称、功能、SOP和风险。只输出专业学名。使用中文。用HTML输出class='result-card'。"
                        # 注意：这里继续使用 glm-4v，因为它需要看图
                        r = cli.chat.completions.create(model="glm-4v", messages=[{"role":"user","content":[{"type":"text","text":p},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}])
                        st.markdown(r.choices[0].message.content, unsafe_allow_html=True)
                except Exception as e: st.error(f"视觉识别出错: {str(e)}")

# === 页面 4: 文献深读 (V20 长文本修复版) ===
elif "文献" in menu:
    st.title("📄 文献深度解析 (Long-Text Support)")
    
    st.info("💡 已自动切换至 **GLM-4-Flash (128k)** 模型，支持超长文献全文解析。")
    
    uploaded_pdf = st.file_uploader("上传 PDF 全文", type=["pdf"], key="pdf_full")
    
    if uploaded_pdf and st.button("🚀 开始中文深度解析", key="btn_full_pdf"):
        if not api_key:
            st.error("❌ 请先在侧边栏填写 API Key！")
        else:
            try:
                with st.spinner("1/3 正在提取全文 (pdfplumber)..."):
                    full_text = read_full_pdf(uploaded_pdf)
                    
                    if not full_text or len(full_text) < 200:
                        st.error("❌ 无法提取文本！可能是扫描版 PDF。")
                    else:
                        st.toast(f"提取成功！字数：{len(full_text)}。正在发送给长文本模型...", icon="📑")
                        
                        # V20 核心修复：放宽字数限制，因为我们换模型了！
                        # GLM-4-Flash 可以吃 128k token，所以我们可以放心传 5-8 万字都没问题
                        truncated_text = full_text[:80000] 
                        
                        with st.spinner("2/3 GLM-4-Flash 正在深度阅读全文..."):
                            client = OpenAI(api_key=api_key, base_url=base_url)
                            
                            deep_prompt = """
                            你是一位精通中英文的资深生物学家。请阅读这篇文献全文。
                            
                            **核心指令：**
                            1. **必须完全使用中文回答**。
                            2. **输出内容必须详实**，挖掘细节。
                            3. **严格遵守以下 HTML 结构**。

                            请输出以下三张卡片：

                            <div class="result-card">
                                <h3>📑 深度导读 (Deep Review)</h3>
                                <h4>1. 论文标题 (中文翻译)</h4>
                                <p>[翻译标题]</p>
                                <h4>2. 核心发现 (TL;DR)</h4>
                                <p>[至少150字，概括核心机制和结论]</p>
                                <h4>3. 关键数据支持</h4>
                                <p>[提取文中的P值、提升百分比等具体数据]</p>
                            </div>

                            <div class="result-card reagent-card">
                                <h3>🧪 智能试剂/设备清单</h3>
                                <p><i>（AI 自动从 Methods 章节提取）</i></p>
                                <ul>
                                   <li><b>关键试剂：</b> [名称] (厂家/型号)</li>
                                   <li><b>关键仪器：</b> [名称] (型号)</li>
                                </ul>
                            </div>

                            <div class="result-card protocol-card">
                                <h3>📋 Step-by-Step 实验流程</h3>
                                <p><i>（复现指南）</i></p>
                                <ol>
                                   <li><b>步骤 1：</b> [详细描述]</li>
                                   <li><b>步骤 2：</b> [详细描述，包含温度、时间、离心转速等]</li>
                                   <li><b>步骤 3：</b> [详细描述]</li>
                                </ol>
                            </div>

                            以下是文献全文：
                            """
                            
                            # === V20 关键修改：强制指定 model="glm-4-flash" ===
                            # 这个模型是免费的，且支持超长上下文，不会报 1210 错误
                            response = client.chat.completions.create(
                                model="glm-4-flash", 
                                messages=[
                                    {
                                        "role": "user",
                                        "content": f"{deep_prompt}\n\n{truncated_text}"
                                    }
                                ],
                                max_tokens=3000 # 允许超长输出
                            )
                            
                        with st.spinner("3/3 正在渲染中文报告..."):
                            time.sleep(1)
                            st.markdown(response.choices[0].message.content, unsafe_allow_html=True)
                            st.success("✅ 中文解析完成！(Model: GLM-4-Flash)")
                            
            except Exception as e:
                # 如果还是报错，提示用户
                st.error(f"分析出错: {e}")
                if "1210" in str(e):
                    st.warning("提示：如果依然报错 1210，请检查 API Key 是否开通了 glm-4-flash 权限（通常是默认开通的）。")
