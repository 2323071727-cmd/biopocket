import streamlit as st
import cv2
import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# 1. 全局配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BioPocket V9", 
    page_icon="🧫", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. 样式优化
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        h1 {font-family: 'Helvetica Neue', sans-serif; font-weight: 700; color: #0E1117;}
        div[data-testid="stMetric"] {
            background-color: #F0F2F6; padding: 15px; border-radius: 8px;
            border-left: 5px solid #28a745; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stImage caption {font-weight: bold; color: #555;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 侧边栏
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022288.png", width=60)
    st.title("BioPocket")
    st.caption("v9.0.0 | Invert Color Fix")
    st.markdown("---")
    menu = st.radio("功能导航", ["📊 综合看板", "🧫 菌落计数 (修复版)", "📷 仪器识别", "📄 文献速读"], index=1)

# -----------------------------------------------------------------------------
# 4. 主逻辑
# -----------------------------------------------------------------------------

# === 页面 1: 综合看板 ===
if "看板" in menu:
    st.title("📊 实验室综合管控台")
    st.info("（看板内容已折叠）")

# === 页面 2: 菌落计数 (V9 修复反色问题) ===
elif "菌落" in menu:
    st.title("🧫 智能菌落计数 (反色修复版)")
    
    c1, c2 = st.columns([1, 2])
    
    # --- 左侧：核心参数 ---
    with c1:
        st.markdown("### 🎯 第一步：区域锁定 (ROI)")
        with st.container(border=True):
            roi_radius = st.slider("有效区域半径 (ROI Radius)", 10, 500, 280, help="缩小此圆圈以排除边缘反光干扰")
        
        st.markdown("### 🛠️ 第二步：图像增强与阈值")
        with st.container(border=True):
            # === V9 核心修复：新增反色开关 ===
            st.markdown("**关键设置：菌落颜色**")
            is_light_colony = st.checkbox("✅ 我的菌落是亮的 (背景是暗的)", value=True, help="如果你的培养皿是黑底白菌，请勾选此项！")
            
            st.markdown("---")
            use_clahe = st.checkbox("启用 CLAHE 增强", value=True)
            thresh_val = st.slider("亮度阈值 (Threshold)", 0, 255, 140)
            min_area = st.slider("最小菌落面积 (Min Area)", 1, 200, 10)

        uploaded_file = st.file_uploader("上传培养皿图像", type=['jpg', 'png'])

    # --- 右侧：可视化分析 ---
    with c2:
        if uploaded_file:
            # 1. 读取和预处理
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            original_image = cv2.imdecode(file_bytes, 1)
            
            scale_percent = 60
            width = int(original_image.shape[1] * scale_percent / 100)
            height = int(original_image.shape[0] * scale_percent / 100)
            dim = (width, height)
            image = cv2.resize(original_image, dim, interpolation = cv2.INTER_AREA)
            
            h, w = image.shape[:2]
            center_x, center_y = w // 2, h // 2

            # 2. 创建 ROI 掩膜
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.circle(mask, (center_x, center_y), roi_radius, 255, -1)
            
            # 3. 转灰度 + CLAHE 增强
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if use_clahe:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)

            # 4. 应用掩膜 (只保留圆圈内)
            masked_gray = cv2.bitwise_and(gray, gray, mask=mask)

            # 5. 阈值处理 (V9 核心修复逻辑)
            blurred = cv2.GaussianBlur(masked_gray, (5, 5), 0)
            
            # 根据用户的选择，决定是找亮的还是找暗的
            if is_light_colony:
                # 找亮菌落：使用标准二值化 (THRESH_BINARY)
                # 大于阈值的变白(菌落)，小于的变黑(背景)
                _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
            else:
                # 找暗菌落：使用反向二值化 (THRESH_BINARY_INV)
                # 小于阈值的变白(菌落)，大于的变黑(背景)
                _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
            
            # 再次应用掩膜，确保切割干净
            thresh = cv2.bitwise_and(thresh, thresh, mask=mask)

            # 6. 轮廓查找与过滤
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            result_img = image.copy()
            cv2.circle(result_img, (center_x, center_y), roi_radius, (0, 0, 255), 2)
            
            count = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                # 稍微放宽一点面积限制
                if min_area < area < 2500:
                    count += 1
                    cv2.drawContours(result_img, [cnt], -1, (0, 255, 0), 2)

            # 7. 结果展示
            st.markdown("#### 👁️ 视觉分析结果")
            img_c1, img_c2 = st.columns(2)
            with img_c1:
                st.image(result_img, channels="BGR", caption=f"最终识别 (绿色为识别到的菌落)", use_container_width=True)
            with img_c2:
                # 这里的标题也改一下，提示用户
                algo_caption = "算法视角 (白色代表被识别的目标)"
                st.image(thresh, caption=algo_caption, use_container_width=True, clamp=True)
                
            st.success(f"✅ 分析完成，共计数：**{count}** CFU")

        else:
            st.info("👈 请上传图片。对于黑底白菌，请确保勾选了 '我的菌落是亮的'。")

# === 其他页面保留 ===
elif "仪器" in menu:
    st.title("📷 仪器识别")
elif "文献" in menu:
    st.title("📄 文献速读")
