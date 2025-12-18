import streamlit as st
import cv2
import numpy as np
import pandas as pd # 新增：用于展示专业的数据表格
import time

# -----------------------------------------------------------------------------
# 1. 全局配置：宽屏模式 (Web端大气布局的基础)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BioPocket Pro", 
    page_icon="🧬", 
    layout="wide", # 必须宽屏
    initial_sidebar_state="expanded" # 侧边栏默认展开
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
        /* 调整 Metric 指标卡片的样式，增加边框和阴影 */
        div[data-testid="stMetric"] {
            background-color: #F0F2F6;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #FF4B4B; /* 红色科研警戒线风格 */
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        /* 侧边栏背景微调 (Streamlit默认已支持，这里不做过度破坏) */
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 侧边栏：控制中心 (Control Panel)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022288.png", width=60)
    st.title("BioPocket")
    st.caption("v2.1.0 | Enterprise Edition")
    
    st.markdown("---")
    
    # 导航菜单
    menu = st.radio(
        "功能导航 (Navigation)", 
        ["📊 综合看板 (Dashboard)", "🧫 菌落计数 (Counter)", "📷 仪器识别 (Lens)", "📄 文献速读 (Reader)"],
        index=0
    )
    
    st.markdown("---")
    
    # 模拟系统状态（增加专业感）
    st.subheader("🖥️ 系统状态")
    st.text("CPU Usage:")
    st.progress(0.45) # 模拟 45% 占用
    st.text("Memory:")
    st.progress(0.72) # 模拟 72% 占用
    st.caption("Cloud Node: AWS-US-East-1 (Online)")

# -----------------------------------------------------------------------------
# 4. 主界面逻辑
# -----------------------------------------------------------------------------

# === 页面 1: 综合看板 (充满数据的首页) ===
if "Dashboard" in menu:
    st.title("📊 实验室综合管控台")
    st.markdown("欢迎回来，**Researcher_007**。系统运行正常，今日实验数据已同步。")
    
    st.markdown("### 🚀 核心指标 (Key Metrics)")
    
    # 使用 4 列布局展示关键数据
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="今日分析样本", value="142", delta="12%")
    with col2:
        st.metric(label="AI 识别准确率", value="98.4%", delta="0.2%")
    with col3:
        st.metric(label="文献库收录", value="1,024", delta="5 New")
    with col4:
        st.metric(label="云端算力延迟", value="32ms", delta="-5ms", delta_color="inverse")
    
    st.markdown("---")
    
    # 分栏：左边是实时日志，右边是快捷入口
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("📋 实时实验日志 (Real-time Logs)")
        # 伪造一个专业的数据表格
        data = {
            "Time": ["10:42:01", "10:38:55", "10:15:20", "09:55:12", "09:30:00"],
            "User": ["Lab_User_A", "Lab_User_B", "Admin", "Lab_User_A", "System"],
            "Action": ["Run PCR Analysis", "Upload Image", "Update Database", "Colony Count", "Daily Backup"],
            "Status": ["✅ Success", "✅ Success", "⚠️ Pending", "✅ Success", "✅ Success"]
        }
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    with c2:
        st.subheader("🔔 系统通知")
        st.info("**系统维护：** 服务器将于今晚 24:00 进行例行维护。")
        st.warning("**库存预警：** 实验室 DMEM 培养基剩余不足 10%。")
        st.success("**新功能：** 文献速读模块已升级至 GPT-4o 模型。")

# === 页面 2: 菌落计数 (更专业的参数面板) ===
elif "Counter" in menu:
    st.title("🧫 智能菌落计数 (Bio-Counter)")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.markdown("#### ⚙️ 处理参数设置")
        # 把参数放在主界面的左侧，显得更像专业软件的操作台
        st.slider("亮度阈值 (Threshold)", 0, 255, 120)
        st.slider("最小半径 (Min Radius)", 1, 50, 5)
        st.slider("最大半径 (Max Radius)", 50, 200, 100)
        st.checkbox("启用边缘平滑 (Anti-aliasing)", value=True)
        st.checkbox("排除边缘噪点", value=True)
        
        uploaded_file = st.file_uploader("上传培养皿图像", type=['jpg', 'png'])
    
    with c2:
        st.markdown("#### 🖼️ 实时分析视图")
        if uploaded_file:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, 1)
            # 这里简单展示，实际可以画框
            st.image(image, caption="已加载图像 (1024x1024)", use_container_width=True)
            
            st.success("✅ 分析完成：检测到 **35** 个目标菌落 (CFU)。")
            # 假装展示一个分布图
            st.bar_chart({"<1mm": 5, "1-3mm": 20, ">3mm": 10})
        else:
            st.info("请在左侧上传图像以开始分析。")

# === 页面 3: 仪器识别 ===
elif "Lens" in menu:
    st.title("📷 实验室 AI 慧眼 (Lab Lens)")
    st.markdown("利用多模态视觉模型实时识别实验室设备并获取 SOP。")
    
    col1, col2 = st.columns(2)
    with col1:
        st.camera_input("拍摄设备", key="camera")
        st.caption("支持设备：离心机、PCR仪、显微镜、超净台")
    
    with col2:
        st.subheader("🧠 识别结果分析")
        # 即使没拍照，也展示一个占位符，保持界面饱满
        with st.container(border=True):
            st.markdown("**设备名称：** 等待输入...")
            st.markdown("**置信度：** --%")
            st.markdown("**安全等级：** --")
            st.markdown("---")
            st.markdown("*请拍摄清晰的设备正面照片*")

# === 页面 4: 文献速读 ===
elif "Reader" in menu:
    st.title("📄 文献 AI 速读 (Paper Pal)")
    
    # 使用 Expander 折叠详细信息，让界面更整洁
    with st.expander("ℹ️ 使用说明 (点击展开)", expanded=False):
        st.write("支持 PDF/图片格式，模型将自动提取：摘要、实验方法、关键数据。")
    
    uploaded_pdf = st.file_uploader("拖拽上传文献 (PDF)", type="pdf")
    
    if uploaded_pdf:
        with st.spinner("正在解析 PDF 结构树..."):
            time.sleep(1)
        st.success("解析成功！")
        
        c1, c2 = st.columns(2)
        with c1:
            st.info("📑 **摘要 (Abstract)**")
            st.write("This paper presents a novel approach for...")
        with c2:
            st.warning("⚠️ **潜在风险提示**")
            st.write("实验步骤 3 中涉及剧毒试剂，请查阅 SDS。")
