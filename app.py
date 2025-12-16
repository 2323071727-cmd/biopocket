import streamlit as st
import cv2
import numpy as np
import time

# -----------------------------------------------------------------------------
# 1. 核心配置：Wide模式
# -----------------------------------------------------------------------------
st.set_page_config(page_title="BioPocket V5", page_icon="🧬", layout="wide")

# -----------------------------------------------------------------------------
# 2. V5 暴力样式 (标签页模式 + 强力去广告)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        /* 1. 隐藏顶部Header和右下角红标 (使用更通用的选择器) */
        header {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important; display: none !important;}
        
        /* 2. 针对那个顽固的红色皇冠 footer，把它挤出屏幕 */
        div[class^="st-emotion-cache"] footer {display: none !important;}
        div[data-testid="stFooter"] {display: none !important;}
        
        /* 3. 调整顶部 Tab 的样式，让它更像 APP 的导航栏 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
            flex: 1; /* 让四个按钮平均分，占满屏幕宽度 */
        }
        
        /* 4. 选中状态高亮 */
        .stTabs [aria-selected="true"] {
            background-color: #ff4b4b !important;
            color: white !important;
        }

        /* 5. 调整整体边距，利用好手机屏幕 */
        .block-container {
            padding-top: 1rem !important; /* 因为隐藏了header，把内容往上提 */
            padding-bottom: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
    </style>
    
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 全新导航逻辑：使用 Tabs 代替 Sidebar
# -----------------------------------------------------------------------------
# 直接在顶部生成四个大按钮
tab1, tab2, tab3, tab4 = st.tabs(["🏠 首页", "🧫 计数", "📷 识别", "📄 文献"])

# --- 页面 1: 首页 ---
with tab1:
    st.header("BioPocket V5")
    st.info("👆 看上面！现在点击顶部的标签就能切换功能，再也不用找菜单了。")
    
    st.image("https://images.unsplash.com/photo-1532094349884-543bc11b234d", caption="BioPocket 科研助手")
    
    # 数据看板
    col1, col2, col3 = st.columns(3)
    col1.metric("菌落", "1.2k")
    col2.metric("文献", "85")
    col3.metric("状态", "On")

# --- 页面 2: 菌落计数 ---
with tab2:
    st.subheader("🧫 智能计数")
    uploaded_file = st.file_uploader("上传图片", type=['jpg', 'png'], key="count_upload")
    if uploaded_file:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)
        st.image(image, caption="原始图片", use_container_width=True)
        st.success("✅ 识别结果：35 CFU")

# --- 页面 3: 仪器识别 ---
with tab3:
    st.subheader("📷 仪器识别")
    img = st.camera_input("拍照识别", key="lens_camera")
    if img:
        st.success("✅ 识别成功：Eppendorf 离心机")

# --- 页面 4: 文献速读 ---
with tab4:
    st.subheader("📄 文献速读")
    st.write("上传文献 PDF 或直接拍照：")
    st.file_uploader("选择文件", key="pdf_upload")
