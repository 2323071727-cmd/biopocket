import streamlit as st
import cv2
import numpy as np
import pandas as pd
import time
import base64
from openai import OpenAI
import pypdf

# -----------------------------------------------------------------------------
# 1. 全局配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BioPocket V18 Ultra", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. 样式优化 (专业科研风)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        h1 {font-family: 'Helvetica Neue', sans-serif; font-weight: 700; color: #0E1117;}
        
        /* 结果卡片 */
        .result-card {
            background-color: #e3f2fd; 
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #1976d2; 
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        /* 强制黑字 */
        .result-card, .result-card p, .result-card li, .result-card div, .result-card span {
            color: #000000 !important; 
            font-size: 16px !important;
            line-height: 1.6 !important;
        }
        .result-card h3 { color: #0d47a1 !important; margin-top: 0 !important; font-weight: bold !important; }
        .result-card h4 { color: #1565c0 !important; font-weight: bold !important; margin-top: 15px !important;}
        .result-card strong { color: #d32f2f !important; }

        /* 独家功能卡片：试剂清单 (绿色) */
        .reagent-card {
            background-color: #e8f5e9;
            border-left: 5px solid #2e7d32;
        }
        .reagent-card h3 { color: #1b5e20 !important; }
        
        /* 独家功能卡片：实验流程 (橙色) */
        .protocol-card {
            background-color: #fff3e0;
            border-left: 5px solid #ef6c00;
        }
        .protocol-card h3 { color: #e65100 !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 辅助函数
# -----------------------------------------------------------------------------
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# 升级版 PDF 读取：尝试读取全文
def read_full_pdf(uploaded_file):
    try:
        reader = pypdf.PdfReader(uploaded_file)
        text = ""
        # 遍历所有页面读取
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return None

# -----------------------------------------------------------------------------
# 4. 侧边栏
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022288.png", width=60)
    st.title("BioPocket")
    st.caption("v18.0 | Full-Text & Analysis")
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
    # (保持 V16 完整代码，为了篇幅这里简写，请务必保留原代码)
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
            # ... (图像处理逻辑同V16) ...
            # 为了演示效果，这里只写核心逻辑，实际请用完整代码
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
    # (保持 V14 完整代码)
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
                    p = "识别仪器专业学名、SOP和风险。用HTML输出class='result-card'。"
                    r = cli.chat.completions.create(model=model_name, messages=[{"role":"user","content":[{"type":"text","text":p},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}])
                    st.markdown(r.choices[0].message.content, unsafe_allow_html=True)
                except Exception as e: st.error(str(e))

# === 页面 4: 文献深读 (V18 Pro) ===
elif "文献" in menu:
    st.title("📄 文献深度解析 (Deep Reader)")
    
    st.info("💡 独家功能：上传 PDF 全文，AI 将自动提取【实验试剂清单】并生成【可操作的实验流程图】。")
    
    uploaded_pdf = st.file_uploader("上传 PDF 全文", type=["pdf"], key="pdf_full")
    
    if uploaded_pdf and st.button("🚀 开始深度剖析 (Deep Analysis)", key="btn_full_pdf"):
        if not api_key:
            st.error("❌ 请先在侧边栏填写 API Key！")
        else:
            try:
                with st.spinner("1/3 正在读取全文内容 (这可能需要几秒钟)..."):
                    # 1. 读取全文
                    full_text = read_full_pdf(uploaded_pdf)
                    
                    if not full_text:
                        st.error("无法读取 PDF 内容。")
                    else:
                        # 截取文本 (防止 Token 溢出，取前 30000 字符，通常足够涵盖 Methods 和 Results)
                        # 如果是 GPT-4o 或 GLM-4-Plus (128k context)，可以读更多
                        truncated_text = full_text[:30000] 
                        
                        with st.spinner("2/3 AI 正在理解实验逻辑与提取数据..."):
                            client = OpenAI(api_key=api_key, base_url=base_url)
                            
                            # === V18 杀手级 Prompt ===
                            deep_prompt = """
                            你是一位顶级生物学家助手。请阅读这篇文献的全文内容。
                            你的任务不是简单的总结，而是【提取可复现的实验细节】。

                            请输出三部分内容，必须使用 HTML 格式，不要 Markdown：

                            1. **深度导读 (class="result-card")**：
                               - 标题 (中文)
                               - 核心发现 (200字以内)
                               - 关键数据支持 (例如：图3显示...提升了50%)

                            2. **独家功能：智能试剂/设备清单 (class="result-card reagent-card")**：
                               - 请从 Methods 部分提取所有提到的【关键试剂、抗体、试剂盒、仪器型号】。
                               - 格式为清单：
                                 <ul>
                                   <li><b>试剂：</b> [名称] (厂家/货号, 如果有)</li>
                                   <li><b>仪器：</b> [名称] (型号)</li>
                                 </ul>

                            3. **独家功能：Step-by-Step 实验流程 (class="result-card protocol-card")**：
                               - 将复杂的实验步骤转化为“傻瓜式”的操作流。
                               - 格式：
                                 <ol>
                                   <li><b>步骤 1 (准备)：</b> ...</li>
                                   <li><b>步骤 2 (处理)：</b> ... (注意：此处有关键条件，如 37℃ 孵育 1h)</li>
                                   <li><b>步骤 3 (检测)：</b> ...</li>
                                 </ol>
                               - 在步骤中加粗关键的【数字】（如时间、温度、浓度）。

                            文献内容如下：
                            """
                            
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": f"{deep_prompt}\n\n{truncated_text}"
                                    }
                                ],
                                max_tokens=2000 # 允许长输出
                            )
                            
                        with st.spinner("3/3 正在生成可视化报告..."):
                            time.sleep(1) # 增加一点仪式感
                            
                            # 展示结果
                            st.markdown(response.choices[0].message.content, unsafe_allow_html=True)
                            
                            st.success("✅ 深度解析完成！已生成复现指南。")
                            
            except Exception as e:
                st.error(f"分析出错 (可能是文本太长超过模型限制，建议使用 GLM-4): {e}")
