import streamlit as st
import cv2
import numpy as np
import time

# --- 1. 页面基础设置 ---
st.set_page_config(page_title="BioPocket 随身实验室", page_icon="🧬", layout="centered")

# --- 插入这段全屏代码 Start ---
st.markdown("""
    <style>
        /* 隐藏 Streamlit 默认的汉堡菜单和页脚 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;} 
    </style>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
""", unsafe_allow_html=True)
# --- 插入这段全屏代码 End ---
# 隐藏默认菜单
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 侧边栏导航 ---
st.sidebar.title("🧬 BioPocket")
st.sidebar.info("全场景移动端科研智能体")
option = st.sidebar.selectbox("功能切换", [
    "🏠 项目首页", 
    "🧫 菌落/凝胶计数 (Bio-Counter)", 
    "📷 AI 慧眼 (Lab Lens)", 
    "📄 文献速读 (Paper Pal)"
])

# ==================================================
# 功能 1：项目首页
# ==================================================
if option == "🏠 项目首页":
    st.title("BioPocket 随身生物实验室")
    st.write("### 创新 · 智能 · 高效")
    st.success("欢迎进入 BioPocket。本项目旨在通过 AI 视觉与大模型技术，解决生物实验中的痛点。")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("已识别菌落", "1,240+", "+12%")
    with col2:
        st.metric("文献阅读", "85 篇", "+5")
    with col3:
        st.metric("仪器数据库", "Online", "v2.0")

    st.image("https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&q=80&w=1000", caption="AI 赋能每一位科研人员")

# ==================================================
# 功能 2：菌落/凝胶计数 (真实可用版)
# ==================================================
elif option == "🧫 菌落/凝胶计数 (Bio-Counter)":
    st.header("🧫 智能计数器")
    st.caption("技术核心：OpenCV 动态阈值分割算法")
    
    # 侧边栏微调
    st.sidebar.markdown("---")
    st.sidebar.write("🛠 **算法参数调试**")
    thresh_val = st.sidebar.slider("亮度阈值", 0, 255, 120)
    min_area = st.sidebar.slider("最小面积 (去除噪点)", 1, 200, 10)
    
    uploaded_file = st.file_uploader("上传培养皿图片", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file is not None:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(image, channels="BGR", caption="原始图片", use_container_width=True)
            
        # 算法处理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (11, 11), 0)
        _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        result_img = image.copy()
        count = 0
        for cnt in contours:
            if cv2.contourArea(cnt) > min_area:
                count += 1
                cv2.drawContours(result_img, [cnt], -1, (0, 255, 0), 2)
        
        with col2:
            st.image(result_img, channels="BGR", caption=f"识别结果: {count}", use_container_width=True)
        
        st.success(f"✅ 分析完成！共检测到 {count} 个目标。")

# ==================================================
# 功能 3：AI 慧眼 (演示版 - 模拟大模型)
# ==================================================
elif option == "📷 AI 慧眼 (Lab Lens)":
    st.header("📷 AI 仪器与试剂识别")
    st.caption("技术核心：多模态视觉大模型 (Vision LLM)")
    
    st.info("💡 演示模式：请拍摄实验室中的设备（如离心机、PCR仪）")
    
    img_file = st.camera_input("点击拍摄")
    
    if img_file is not None:
        st.image(img_file, caption="已捕获图像", width=300)
        
        # 模拟 AI 思考动画
        with st.spinner('正在上传云端进行特征提取...'):
            time.sleep(1.5)
        with st.spinner('正在匹配生物安全数据库 (SDS)...'):
            time.sleep(1.0)
            
        # 结果展示区
        st.success("✅ 识别成功！置信度 98.5%")
        
        # 这里使用 Markdown 模拟一个完美的 AI 回答
        st.markdown("""
        ### 🔬 识别结果：Eppendorf 高速冷冻离心机
        
        **📌 功能简介：**
        该设备主要用于生物样品的分离与沉淀，支持低温（4°C）环境下的 DNA/RNA 提取操作。
        
        **⚠️ 安全操作警示 (SDS摘要)：**
        1.  **配平至关重要：** 放入样品前，请务必使用天平配平，误差需小于 0.1g。
        2.  **转头盖锁定：** 启动前请再次检查气密性转头盖是否旋紧。
        3.  **最高转速限制：** 当前转头最高耐受转速为 14,000 rpm，请勿超速。
        
        > **🤖 AI 助手建议：**
        > 检测到您正在进行核酸提取实验，建议您提前 5 分钟开启预冷模式（FastTemp）。
        """)

# ==================================================
# 功能 4：文献速读 (演示版 - 模拟文本分析)
# ==================================================
elif option == "📄 文献速读 (Paper Pal)":
    st.header("📄 英文文献 AI 速读")
    st.caption("技术核心：NLP 自然语言处理 + 知识图谱")
    
    st.write("请上传文献 PDF 或拍摄摘要部分：")
    upload_doc = st.file_uploader("上传文件", type=['pdf', 'png', 'jpg'])
    
    # 模拟输入一段文字
    txt_input = st.text_area("或者直接粘贴一段英文摘要：", height=100)
    
    if st.button("生成中文导读") and (upload_doc or txt_input):
        with st.spinner('正在解析学术专有名词...'):
            time.sleep(2)
            
        st.success("✅ 解析完成！已生成结构化笔记")
        
        st.markdown("""
        #### 📑 文章标题：CRISPR-Cas9 介导的基因编辑在免疫治疗中的应用
        
        **💡 核心结论 (TL;DR):**
        本研究提出了一种改进的 Cas9 递送系统，能够显著提高 T 细胞的编辑效率，使 CAR-T 疗法的持久性提升了 **3.5倍**。
        
        **🔍 关键术语解释:**
        * **Cytokine Release Syndrome (CRS):** 细胞因子释放综合征。这是免疫治疗常见的一种副作用，表现为发烧和多器官功能障碍。
        * **Off-target Effect:** 脱靶效应。指基因编辑工具错误地切割了非目标DNA序列。
        
        **🧠 实验方法摘要:**
        1.  构建 sgRNA 质粒库。
        2.  利用电穿孔技术转染 T 细胞。
        3.  流式细胞术 (FACS) 检测编辑效率。
        """)