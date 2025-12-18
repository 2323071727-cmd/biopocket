import streamlit as st
import cv2
import numpy as np
import pandas as pd
import time

# -----------------------------------------------------------------------------
# 1. 全局配置：宽屏模式 (Web端大气布局的基础)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BioPocket Pro V7", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. 注入“科研风” CSS 样式
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        /* 调整主标题字体，增加科技感 */
        h1 {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-weight: 700;
            color: #0E1117;
        }
        /* 调整 Metric 指标卡片的样式 */
        div[data-testid="stMetric"] {
            background-color: #F0F2F6;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #FF4B4B;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        /* 图片标题样式 */
        .stImage caption {
            font-weight: bold;
            color: #555;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 侧边栏：控制中心 (Control Panel)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022288.png", width=60)
    st.title("BioPocket")
    st.caption("v7.0.0 | Pro Edition")
    
    st.markdown("---")
    
    # 导航菜单
    menu = st.radio(
        "功能导航 (Navigation)", 
        ["📊 综合看板 (Dashboard)", "🧫 菌落计数 (Counter)", "📷 仪器识别 (Lens)", "📄 文献速读 (Reader)"],
        index=1 # 默认跳到计数页面方便调试
    )
    
    st.markdown("---")
    st.subheader("🖥️ 系统状态")
    st.text("CPU Usage:")
    st.progress(0.55)
    st.caption("Cloud Node: AWS-US-East-1 (Online)")

# -----------------------------------------------------------------------------
# 4. 主界面逻辑
# -----------------------------------------------------------------------------

# === 页面 1: 综合看板 ===
if "Dashboard" in menu:
    st.title("📊 实验室综合管控台")
    # ... (此处省略了看板代码，与V6相同，为了节省篇幅，实际使用请保留V6的看板代码)
    st.info("（看板内容已隐藏，专注于菌落计数功能展示）")

# === 页面 2: 菌落计数 (V7 核心增强版) ===
elif "Counter" in menu:
    st.title("🧫 智能菌落计数 (Bio-Counter Pro)")
    
    # 主界面分栏：左侧参数(窄)，右侧图像(宽)
    c1, c2 = st.columns([1, 3])
    
    # --- 左侧：参数调试区 ---
    with c1:
        st.markdown("### 🛠️ 算法参数调试")
        with st.container(border=True):
            st.markdown("**图像预处理**")
            # 真实的交互滑块
            thresh_val = st.slider("亮度阈值 (Threshold)", 0, 255, 125, help="调整此值以区分菌落与背景，观察右侧黑白图变化。")
            
            st.markdown("---")
            st.markdown("**形态学过滤**")
            # 使用面积过滤更直观
            min_area = st.slider("最小面积 (Min Area)", 1, 500, 20, help="去除小于此像素值的噪点。")
            max_area = st.slider("最大面积 (Max Area)", 500, 5000, 2000, help="排除过大的粘连区域。")
        
        st.markdown("### 📂 数据输入")
        uploaded_file = st.file_uploader("上传培养皿图像 (JPG/PNG)", type=['jpg', 'png'])

    # --- 右侧：双屏可视化分析区 ---
    with c2:
        if uploaded_file:
            # 1. 读取和解码图片
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, 1)
            
            # 2. OpenCV 核心处理流程 (实时计算!)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # 高斯模糊去噪
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            # 动态阈值分割 (使用左侧滑块的值!)
            _, thresh_img = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV) # 这里用了INV(反向)，假设菌落是深色的，背景是浅色的。如果是荧光菌落，去掉_INV
            
            # 查找轮廓
            contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 过滤和绘制
            result_img = image.copy()
            count = 0
            filtered_contours = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if min_area < area < max_area:
                    count += 1
                    filtered_contours.append(cnt)
                    # 在原图上画绿圈
                    cv2.drawContours(result_img, [cnt], -1, (0, 255, 0), 2)

            # 3. 双屏展示结果
            st.markdown("#### 📊 实时分析视图 (Dual-View Analysis)")
            
            # 在 c2 里面再分两列
            img_col1, img_col2 = st.columns(2)
            
            with img_col1:
                st.image(result_img, channels="BGR", caption=f"视图 A: 识别结果叠加 (计数: {count})", use_container_width=True)
            
            with img_col2:
                # 展示二值化图像，这才是算法真正看到的
                st.image(thresh_img, caption=f"视图 B: 算法阈值视角 (二值化)", use_container_width=True)

            # 结果汇总横幅
            st.success(f"✅ 分析完成！根据当前参数，共检测到 **{count}** 个目标菌落 (CFU)。")
            
        else:
            # 没有上传图片时的占位符
            st.info("👈 请在左侧上传图像以开始分析。")
            # 放个示例图占位，保持布局美观
            st.image("https://www.thermofisher.com/blog/food-and-beverage/wp-content/uploads/sites/6/2017/07/IMG_3176-e1500396773551.jpg", caption="示例：待分析的培养皿", width=400)

# === 页面 3 & 4 (保持不变，为了完整性建议保留 V6 的代码) ===
elif "Lens" in menu:
    st.title("📷 仪器识别")
    st.write("（此处保留 V6 代码）")
elif "Reader" in menu:
    st.title("📄 文献速读")
    st.write("（此处保留 V6 代码）")
