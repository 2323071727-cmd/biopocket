import streamlit as st
import cv2
import numpy as np
import pandas as pd
import time
import base64
from openai import OpenAI

# -----------------------------------------------------------------------------
# 1. 全局配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BioPocket V14 Pro", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. 样式优化 (强制黑字修复版)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        h1 {font-family: 'Helvetica Neue', sans-serif; font-weight: 700; color: #0E1117;}
        
        /* === 结果卡片样式 === */
        .result-card {
            background-color: #e3f2fd; /* 淡蓝色背景 */
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #1976d2; /* 深蓝线条 */
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        /* 强制卡片内的所有文字颜色为黑色 */
        .result-card, .result-card p, .result-card li, .result-card div {
            color: #000000 !important; 
            font-size: 16px !important;
            line-height: 1.6 !important;
        }
        
        /* 标题颜色 */
        .result-card h3 {
            color: #0d47a1 !important; /* 深蓝色标题 */
            margin-top: 0 !important;
            font-weight: bold !important;
        }
        
        /* 强调文字 */
        .result-card strong {
            color: #d32f2f !important; /* 红色强调 */
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 辅助函数：图片转 Base64
# -----------------------------------------------------------------------------
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# -----------------------------------------------------------------------------
# 4. 侧边栏
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022288.png", width=60)
    st.title("BioPocket")
    st.caption("v14.0 | Expert Edition")
    st.markdown("---")
    menu = st.radio("功能导航", ["📊 看板", "🧫 菌落计数", "📷 仪器识别 (专家版)", "📄 文献速读"], index=2)
    
    # === 国产 AI 配置 ===
    if "仪器" in menu:
        st.markdown("---")
        st.markdown("#### 🔑 模型配置")
        st.info("推荐使用 **智谱GLM-4V**")
        
        # 让用户填 Key
        api_key = st.text_input("API Key (粘贴在这里)", type="password")
        
        # 高级设置 (默认隐藏)
        with st.expander("高级模型设置"):
            base_url = st.text_input("Base URL", value="https://open.bigmodel.cn/api/paas/v4/")
            model_name = st.text_input("Model Name", value="glm-4v")

# -----------------------------------------------------------------------------
# 5. 主逻辑
# -----------------------------------------------------------------------------

# === 页面 1: 看板 ===
if "看板" in menu:
    st.title("📊 实验室综合管控台")
    col1, col2, col3 = st.columns(3)
    col1.metric("已识别菌落", "1,240+", "+12%")
    col2.metric("文献阅读", "85 篇", "+5")
    col3.metric("仪器数据库", "Online", "v2.0")
    st.info("系统运行正常。")

# === 页面 2: 菌落计数 (V9 完整版) ===
elif "菌落" in menu:
    st.title("🧫 智能菌落计数")
    
    c1, c2 = st.columns([1, 2])
    
    # --- 左侧：参数 ---
    with c1:
        st.markdown("### 🎯 区域与参数")
        with st.container(border=True):
            roi_radius = st.slider("有效区域半径 (ROI)", 10, 500, 280, help="排除边缘干扰")
            st.markdown("---")
            is_light_colony = st.checkbox("✅ 菌落是亮的 (黑底白菌)", value=True)
            use_clahe = st.checkbox("启用增强 (CLAHE)", value=True)
            thresh_val = st.slider("亮度阈值", 0, 255, 140)
            min_area = st.slider("最小面积", 1, 200, 10)

        uploaded_file = st.file_uploader("上传培养皿图像", type=['jpg', 'png'])

    # --- 右侧：分析 ---
    with c2:
        if uploaded_file:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            original_image = cv2.imdecode(file_bytes, 1)
            
            # 缩放
            scale_percent = 60
            width = int(original_image.shape[1] * scale_percent / 100)
            height = int(original_image.shape[0] * scale_percent / 100)
            image = cv2.resize(original_image, (width, height), interpolation=cv2.INTER_AREA)
            
            h, w = image.shape[:2]
            center_x, center_y = w // 2, h // 2

            # ROI 掩膜
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.circle(mask, (center_x, center_y), roi_radius, 255, -1)
            
            # 预处理
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if use_clahe:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)

            masked_gray = cv2.bitwise_and(gray, gray, mask=mask)
            blurred = cv2.GaussianBlur(masked_gray, (5, 5), 0)
            
            # 阈值处理
            if is_light_colony:
                _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
            else:
                _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
            
            thresh = cv2.bitwise_and(thresh, thresh, mask=mask)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            result_img = image.copy()
            cv2.circle(result_img, (center_x, center_y), roi_radius, (0, 0, 255), 2)
            
            count = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if min_area < area < 3000:
                    count += 1
                    cv2.drawContours(result_img, [cnt], -1, (0, 255, 0), 2)

            st.image(result_img, channels="BGR", caption=f"识别结果: {count}", use_container_width=True)
            st.success(f"✅ 计数完成：{count} CFU")

# === 页面 3: 仪器识别 (V14 鉴宝版) ===
elif "仪器" in menu:
    st.title("📷 实验室 AI 慧眼 (Expert Mode)")
    
    col_cam, col_res = st.columns([1, 1.5])

    with col_cam:
        img_input = st.camera_input("拍摄仪器")
        img_upload = st.file_uploader("或上传照片", type=["jpg", "png", "jpeg"])
        final_img = img_input if img_input else img_upload

    with col_res:
        if final_img:
            st.image(final_img, caption="待识别图像", width=300)
            
            if st.button("开始 AI 识别"):
                if not api_key:
                    st.error("❌ 请先在侧边栏填写 API Key！")
                else:
                    try:
                        with st.spinner("🚀 正在调用实验室知识库..."):
                            # 1. 初始化客户端
                            client = OpenAI(
                                api_key=api_key,
                                base_url=base_url
                            )
                            
                            # 2. 图片转码
                            base64_image = encode_image(final_img.getvalue())
                            
                            # 3. 发送请求 (V14 升级版提示词)
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": """
                                            你是一位生物实验室仪器专家。请识别这张图片中的仪器。
                                            
                                            **识别要求：**
                                            1. **只输出专业学名：** 请给出该仪器的【标准学术名称】（如：“倒置荧光显微镜”、“台式高速冷冻离心机”），**不需要**猜测具体品牌或型号。
                                            2. **拒绝笼统：** 名称必须精确，不要只说“显微镜”或“检测仪”。
                                            3. **输出格式：** 请直接使用以下HTML格式回答（不要使用Markdown代码块）：
                                            
                                            <h3>仪器名称</h3>
                                            <p>（在此处填写专业学名，例如：激光共聚焦扫描显微镜）</p>
                                            
                                            <p><strong>功能用途：</strong></p>
                                            <p>（简要描述该仪器在生物实验中的核心作用）</p>
                                            
                                            <p><strong>安全SOP：</strong></p>
                                            <ul>
                                            <li>（关键操作规范 1）</li>
                                            <li>（关键操作规范 2）</li>
                                            <li>（关键操作规范 3）</li>
                                            </ul>
                                            
                                            <p><strong>风险提示：</strong>...</p>
                                            """},
                                            {
                                                "type": "image_url",
                                                "image_url": {
                                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                                }
                                            }
                                        ]
                                    }
                                ],
                                max_tokens=1000
                            )
                            
                            # 4. 获取结果
                            result_text = response.choices[0].message.content
                            
                            # 5. 展示 (应用 CSS 修复类名)
                            st.markdown(f"""
                            <div class="result-card">
                                {result_text}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.success("✅ 识别成功！(数据源：国产大模型)")

                    except Exception as e:
                        st.error(f"请求失败: {e}")
                        st.info("请检查 API Key 是否正确，或网络是否通畅。")

# === 页面 4: 文献 ===
elif "文献" in menu:
    st.title("📄 文献速读")
    st.info("功能开发中...")
