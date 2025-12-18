import streamlit as st
import cv2
import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# 1. 全局配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BioPocket V8", 
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
    st.caption("v8.0.0 | ROI Focus Edition")
    st.markdown("---")
    menu = st.radio("功能导航", ["📊 综合看板", "🧫 菌落计数 (聚焦版)", "📷 仪器识别", "📄 文献速读"], index=1)

# -----------------------------------------------------------------------------
# 4. 主逻辑
# -----------------------------------------------------------------------------

# === 页面 1: 综合看板 ===
if "看板" in menu:
    st.title("📊 实验室综合管控台")
    st.info("（看板内容已折叠，专注于菌落计数调试）")

# === 页面 2: 菌落计数 (V8 边缘剔除版) ===
elif "菌落" in menu:
    st.title("🧫 智能菌落计数 (边缘剔除版)")
    
    c1, c2 = st.columns([1, 2])
    
    # --- 左侧：核心参数 ---
    with c1:
        st.markdown("### 🎯 第一步：区域锁定 (ROI)")
        with st.container(border=True):
            st.info("👇 调小这个值，把培养皿边缘的塑料圈裁掉！")
            # ROI 半径控制
            roi_radius = st.slider("有效区域半径 (ROI Radius)", 10, 500, 280, help="缩小此圆圈以排除边缘反光干扰")
        
        st.markdown("### 🛠️ 第二步：图像增强")
        with st.container(border=True):
            use_clahe = st.checkbox("启用 CLAHE 增强", value=True, help="对于中间模糊的菌落，开启此项可显著提高对比度")
            thresh_val = st.slider("亮度阈值 (Threshold)", 0, 255, 140, help="越小识别越黑的物体，越大识别范围越广")
            min_area = st.slider("最小菌落面积 (Min Area)", 1, 200, 10)

        uploaded_file = st.file_uploader("上传培养皿图像", type=['jpg', 'png'])

    # --- 右侧：可视化分析 ---
    with c2:
        if uploaded_file:
            # 1. 读取图像
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            original_image = cv2.imdecode(file_bytes, 1)
            
            # 缩放图片以加快处理 (固定宽度处理，防止大图卡顿)
            scale_percent = 60 # 缩小一点
            width = int(original_image.shape[1] * scale_percent / 100)
            height = int(original_image.shape[0] * scale_percent / 100)
            dim = (width, height)
            image = cv2.resize(original_image, dim, interpolation = cv2.INTER_AREA)
            
            # 获取中心点
            h, w = image.shape[:2]
            center_x, center_y = w // 2, h // 2

            # 2. 核心步骤：创建圆形掩膜 (ROI Mask)
            # 创建一个全黑的图
            mask = np.zeros((h, w), dtype=np.uint8)
            # 在中间画个白色的圆 (大小由滑块控制)
            cv2.circle(mask, (center_x, center_y), roi_radius, 255, -1)
            
            # 3. 预处理
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 可选：CLAHE 增强 (对付中间对比度低的问题)
            if use_clahe:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)

            # 4. 应用掩膜 (只保留圆圈内的图像，圆圈外变黑)
            masked_gray = cv2.bitwise_and(gray, gray, mask=mask)

            # 5. 阈值处理
            blurred = cv2.GaussianBlur(masked_gray, (5, 5), 0)
            # THRESH_BINARY_INV 适合：白底黑菌。如果是黑底白菌，请去掉 _INV
            _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
            
            # 再次应用掩膜 (确保边缘切断的切口不被识别为轮廓)
            thresh = cv2.bitwise_and(thresh, thresh, mask=mask)

            # 6. 轮廓查找
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            result_img = image.copy()
            # 画出红色的 ROI 圈，告诉用户现在的分析范围在哪
            cv2.circle(result_img, (center_x, center_y), roi_radius, (0, 0, 255), 2)
            
            count = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if min_area < area < 2000: # 增加最大面积限制，防止识别错误的色块
                    count += 1
                    cv2.drawContours(result_img, [cnt], -1, (0, 255, 0), 2)

            # 7. 结果展示
            st.markdown("#### 👁️ 视觉分析结果")
            
            img_c1, img_c2 = st.columns(2)
            with img_c1:
                st.image(result_img, channels="BGR", caption=f"最终识别 (红色圈内为有效区)", use_container_width=True)
            with img_c2:
                st.image(masked_gray, caption="算法视角 (已剔除边缘 + 增强)", use_container_width=True)
                
            st.success(f"✅ 剔除边缘干扰后，共计数：**{count}** CFU")

        else:
            st.info("👈 请上传图片，然后尝试调节 '有效区域半径' 滑块。")

# === 其他页面保留 ===
elif "仪器" in menu:
    st.title("📷 仪器识别")
elif "文献" in menu:
    st.title("📄 文献速读")
