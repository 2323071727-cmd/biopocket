import streamlit as st
import cv2
import numpy as np
import pandas as pd
import time
import base64
from openai import OpenAI  # 引入通用库

# -----------------------------------------------------------------------------
# 1. 全局配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BioPocket V12 CN", 
    page_icon="🇨🇳", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. 样式优化
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        h1 {font-family: 'Helvetica Neue', sans-serif; font-weight: 700; color: #0E1117;}
        .result-card {
            background-color: #f0f8ff; padding: 20px; border-radius: 10px;
            border-left: 5px solid #007bff; margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 侧边栏
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022288.png", width=60)
    st.title("BioPocket")
    st.caption("v12.0 | 国产大模型版")
    st.markdown("---")
    menu = st.radio("功能导航", ["📊 看板", "🧫 菌落计数", "📷 仪器识别 (国产AI)", "📄 文献速读"], index=2)
    
    # === 关键：国产 AI 配置 ===
    if "仪器" in menu:
        st.markdown("---")
        st.markdown("#### 🔑 模型配置")
        st.info("推荐使用 **智谱GLM-4V** (国产视觉最强)")
        
        # 让用户填 Key
        api_key = st.text_input("API Key (智谱/DeepSeek)", type="password")
        
        # 高级设置：允许用户换模型 (比如换成 DeepSeek 写文案，换 GLM-4V 看图)
        with st.expander("高级模型设置"):
            base_url = st.text_input("Base URL", value="https://open.bigmodel.cn/api/paas/v4/")
            model_name = st.text_input("Model Name", value="glm-4v")
            st.caption("说明：如果是DeepSeek，URL填 https://api.deepseek.com，模型填 deepseek-chat (但在看图功能会报错)")

# -----------------------------------------------------------------------------
# 4. 辅助函数：图片转 Base64 (国产模型通用的看图方式)
# -----------------------------------------------------------------------------
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# -----------------------------------------------------------------------------
# 5. 主逻辑
# -----------------------------------------------------------------------------

# === 页面 1 & 2 (看板/菌落) 保持不变，为了篇幅省略，请保留之前的代码 ===
if "看板" in menu:
    st.title("📊 实验室综合管控台")
    st.info("Dashboard Ready.")

elif "菌落" in menu:
    st.title("🧫 智能菌落计数 (V9 完美版)")
    # ... (此处请把 V9 的菌落计数代码完整复制过来，或者我帮你留个占位符)
    # ⚠️ 为了代码完整性，请务必保留之前的菌落计数逻辑！
    st.warning("请将 V9 的菌落计数代码粘贴回这里，保持功能完整。")

# === 页面 3: 国产 AI 仪器识别 (V12) ===
elif "仪器" in menu:
    st.title("📷 实验室 AI 慧眼 (Powered by GLM-4V)")
    
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
                    st.error("请先在侧边栏填写 API Key！")
                else:
                    try:
                        with st.spinner("🚀 正在连接国产智算中心..."):
                            # 1. 初始化通用客户端
                            client = OpenAI(
                                api_key=api_key,
                                base_url=base_url
                            )
                            
                            # 2. 图片转码
                            base64_image = encode_image(final_img.getvalue())
                            
                            # 3. 发送请求 (OpenAI 视觉标准格式)
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": "你是一个生物实验室安全专家。请识别图中的仪器，并按格式输出：名称、功能、SOP(3点)、风险(2点)。"},
                                            {
                                                "type": "image_url",
                                                "image_url": {
                                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                                }
                                            }
                                        ]
                                    }
                                ],
                                max_tokens=1000  # 稍微限制一下字数
                            )
                            
                            # 4. 获取结果
                            result_text = response.choices[0].message.content
                            
                            # 5. 展示
                            st.markdown(f"""
                            <div class="result-card">
                                <h3>🔍 识别报告</h3>
                                {result_text.replace(chr(10), '<br>')}
                            </div>
                            """, unsafe_allow_html=True)
                            st.success("✅ 识别成功！数据来源：国产大模型")

                    except Exception as e:
                        st.error(f"请求失败: {e}")
                        st.info("如果你用的是 DeepSeek，请注意：DeepSeek 目前 API 不支持直接看图，请改用智谱 GLM-4V。")

# === 页面 4: 文献 ===
elif "文献" in menu:
    st.title("📄 文献速读")
    st.write("Coming soon...")
