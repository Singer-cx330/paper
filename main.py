import streamlit as st
import tempfile
import os
import base64
import io
from io import BytesIO
from PIL import Image
from pdf_processor import PDFProcessor
from api import DeepSeekAPI
import logging
from typing import Optional
import json
import traceback
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_session_state():
    """初始化会话状态"""
    if 'pdf_text' not in st.session_state:
        st.session_state.pdf_text = None
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "上传论文"
    if 'api_key' not in st.session_state:
        st.session_state.api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if 'api_url' not in st.session_state:
        st.session_state.api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")

def save_api_config(api_key: str, api_url: str):
    """保存API配置到.env文件"""
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(f"DEEPSEEK_API_KEY={api_key}\n")
            f.write(f"DEEPSEEK_API_URL={api_url}\n")
        st.session_state.api_key = api_key
        st.session_state.api_url = api_url
        return True
    except Exception as e:
        logger.error(f"保存API配置失败: {str(e)}")
        return False

def initialize_api():
    """初始化API客户端"""
    try:
        return DeepSeekAPI()
    except ValueError:
        return None

# 初始化处理器
pdf_processor = PDFProcessor()

def save_uploaded_file(uploaded_file) -> Optional[str]:
    """保存上传的文件并返回路径"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        logger.error(f"保存文件失败: {str(e)}")
        return None

def process_pdf(file_path: str):
    """处理PDF文件"""
    try:
        # 清理临时目录
        try:
            pdf_processor.cleanup()
        except Exception as e:
            logger.warning(f"清理临时目录失败: {str(e)}")
        
        # 提取文本
        st.session_state.pdf_text = pdf_processor.extract_text(file_path)
        return True
    except Exception as e:
        logger.error(f"处理PDF失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def display_paper_analysis(api):
    """显示论文分析结果"""
    if st.session_state.pdf_text:
        analysis_type = st.selectbox(
            "选择分析类型",
            ["summary", "methodology", "results", "conclusion"],
            format_func=lambda x: {
                "summary": "内容摘要",
                "methodology": "研究方法",
                "results": "研究结果",
                "conclusion": "结论展望"
            }[x]
        )
        
        if st.button("开始分析"):
            with st.spinner("正在分析中..."):
                try:
                    analysis = api.analyze_paper(st.session_state.pdf_text, analysis_type)
                    st.markdown("### 分析结果")
                    st.write(analysis)
                except Exception as e:
                    st.error(f"分析失败: {str(e)}")

def display_qa_section(api):
    """显示问答部分"""
    if st.session_state.pdf_text:
        question = st.text_input("请输入你的问题")
        if question and st.button("提交问题"):
            with st.spinner("正在思考..."):
                try:
                    answer = api.answer_question(st.session_state.pdf_text, question)
                    st.markdown("### 回答")
                    st.write(answer)
                except Exception as e:
                    st.error(f"回答问题失败: {str(e)}")

def display_key_points(api):
    """显示关键信息提取"""
    if st.session_state.pdf_text:
        if st.button("提取关键信息"):
            with st.spinner("正在提取关键信息..."):
                try:
                    key_points = api.extract_key_points(st.session_state.pdf_text)
                    
                    if "error" in key_points:
                        st.error(f"提取失败: {key_points.get('message', '未知错误')}")
                        if "raw_response" in key_points:
                            with st.expander("查看原始响应"):
                                st.text(key_points["raw_response"])
                        return
                    
                    # 显示基本信息
                    st.markdown("### 论文基本信息")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**标题**: {key_points.get('title', '未提供')}")
                        st.markdown("**作者**:")
                        for author in key_points.get('authors', ['未提供']):
                            st.markdown(f"- {author}")
                    with col2:
                        st.markdown("**关键词**:")
                        for keyword in key_points.get('keywords', ['未提供']):
                            st.markdown(f"- {keyword}")
                    
                    # 显示研究目的
                    st.markdown("### 研究目的")
                    st.write(key_points.get('research_purpose', '未提供'))
                    
                    # 显示研究方法
                    st.markdown("### 研究方法")
                    methodology = key_points.get('methodology', {})
                    st.markdown(f"**研究方法**: {methodology.get('approach', '未提供')}")
                    st.markdown(f"**数据收集**: {methodology.get('data_collection', '未提供')}")
                    st.markdown("**分析方法**:")
                    for method in methodology.get('analysis_methods', ['未提供']):
                        st.markdown(f"- {method}")
                    
                    # 显示主要发现
                    st.markdown("### 主要发现")
                    for finding in key_points.get('main_findings', ['未提供']):
                        st.markdown(f"- {finding}")
                    
                    # 显示结论
                    st.markdown("### 结论")
                    for conclusion in key_points.get('conclusions', ['未提供']):
                        st.markdown(f"- {conclusion}")
                    
                    # 显示未来工作
                    st.markdown("### 未来工作")
                    for work in key_points.get('future_work', ['未提供']):
                        st.markdown(f"- {work}")
                    
                    # 添加导出功能
                    if st.button("导出分析结果"):
                        json_str = json.dumps(key_points, ensure_ascii=False, indent=2)
                        st.download_button(
                            label="下载JSON文件",
                            data=json_str.encode('utf-8'),
                            file_name="paper_analysis.json",
                            mime="application/json"
                        )
                    
                except Exception as e:
                    st.error(f"提取关键信息失败: {str(e)}")
                    logger.error(f"提取关键信息时发生错误: {str(e)}")

def main():
    st.set_page_config(
        page_title="论文分析助手",
        page_icon="📚",
        layout="wide"
    )
    
    init_session_state()
    
    # 清理临时目录
    try:
        pdf_processor.cleanup()
    except Exception as e:
        logger.warning(f"清理临时目录失败: {str(e)}")
    
    # 侧边栏
    with st.sidebar:
        st.markdown("### 功能导航")
        
        # API配置部分
        st.markdown("### API配置")
        with st.expander("配置 DeepSeek API"):
            api_key = st.text_input(
                "API密钥",
                value=st.session_state.api_key,
                type="password",
                help="请输入您的DeepSeek API密钥"
            )
            api_url = st.text_input(
                "API地址",
                value=st.session_state.api_url,
                help="DeepSeek API地址"
            )
            if st.button("保存配置"):
                if api_key and api_url:
                    if save_api_config(api_key, api_url):
                        st.success("配置保存成功！")
                        # 重新加载环境变量
                        load_dotenv(override=True)
                    else:
                        st.error("配置保存失败，请检查文件权限。")
                else:
                    st.warning("请填写完整的配置信息。")
        
        st.markdown("---")
        tabs = {
            "上传论文": "📄",
            "内容分析": "📊",
            "智能问答": "❓",
            "关键信息": "📌"
        }
        selected_tab = st.radio(
            "选择功能",
            list(tabs.keys()),
            format_func=lambda x: f"{tabs[x]} {x}"
        )
        st.session_state.current_tab = selected_tab
        
        st.markdown("---")
        st.markdown("### 关于")
        st.markdown("基于DeepSeek和Streamlit的论文分析工具")
        st.markdown("支持PDF文档的智能分析、内容解释")
    
    st.title("📚 论文分析助手")
    st.markdown("---")
    
    # 检查API配置
    api = initialize_api()
    if not api:
        st.warning("请先在侧边栏配置DeepSeek API密钥。")
        return
    
    # 主要内容区域
    if st.session_state.current_tab == "上传论文":
        uploaded_file = st.file_uploader("上传PDF文件", type=['pdf'])
        if uploaded_file:
            with st.spinner("正在处理文件..."):
                file_path = save_uploaded_file(uploaded_file)
                if file_path and process_pdf(file_path):
                    st.success("文件处理成功！")
                    os.unlink(file_path)  # 清理临时文件
                else:
                    st.error("文件处理失败，请重试。")
    
    elif st.session_state.current_tab == "内容分析":
        display_paper_analysis(api)
    
    elif st.session_state.current_tab == "智能问答":
        display_qa_section(api)
    
    elif st.session_state.current_tab == "关键信息":
        display_key_points(api)

if __name__ == "__main__":
    main() 