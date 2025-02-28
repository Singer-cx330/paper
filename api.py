import os
import json
import logging
import requests
import re
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class DeepSeekAPI:
    def __init__(self):
        """初始化DeepSeek API客户端"""
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY环境变量")
        
        self.api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
        self.model = "deepseek-chat"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _call_api(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Dict[str, Any]:
        """调用DeepSeek API"""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"响应状态码: {e.response.status_code}")
                logger.error(f"响应内容: {e.response.text}")
            raise
    
    def analyze_paper(self, text: str, analysis_type: str = "summary") -> str:
        """分析论文内容"""
        try:
            # 根据分析类型构建提示
            prompts = {
                "summary": "请对以下论文内容进行摘要总结，包括研究目的、方法、主要发现和结论：",
                "methodology": "请详细分析以下论文的研究方法，包括实验设计、数据收集和分析方法：",
                "results": "请详细分析以下论文的研究结果，包括主要发现和数据分析：",
                "conclusion": "请总结以下论文的结论和未来研究方向："
            }
            
            prompt = prompts.get(analysis_type, prompts["summary"])
            
            # 限制文本长度，避免超出API限制
            max_length = 15000
            if len(text) > max_length:
                text = text[:max_length] + "...[内容过长，已截断]"
            
            messages = [
                {"role": "system", "content": "你是一个专业的学术论文分析助手，擅长分析和解释学术论文的内容。请用中文回答。"},
                {"role": "user", "content": f"{prompt}\n\n{text}"}
            ]
            
            response = self._call_api(messages)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"论文分析失败: {str(e)}")
            raise
    
    def answer_question(self, text: str, question: str) -> str:
        """回答关于论文的问题"""
        try:
            # 限制文本长度
            max_length = 15000
            if len(text) > max_length:
                text = text[:max_length] + "...[内容过长，已截断]"
            
            messages = [
                {"role": "system", "content": "你是一个专业的学术论文分析助手，擅长回答关于学术论文的问题。请基于提供的论文内容回答问题，如果论文中没有相关信息，请明确说明。请用中文回答。"},
                {"role": "user", "content": f"论文内容：\n\n{text}\n\n问题：{question}"}
            ]
            
            response = self._call_api(messages)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"回答问题失败: {str(e)}")
            raise
    
    def extract_key_points(self, text: str) -> Dict[str, Any]:
        """提取论文的关键信息"""
        try:
            # 限制文本长度
            max_length = 15000
            if len(text) > max_length:
                text = text[:max_length] + "...[内容过长，已截断]"
            
            prompt = """
            请从以下论文中提取关键信息，并以JSON格式返回。JSON应包含以下字段：
            - title: 论文标题
            - authors: 作者列表（数组）
            - keywords: 关键词列表（数组）
            - research_purpose: 研究目的
            - methodology: 包含approach（方法论）、data_collection（数据收集）和analysis_methods（分析方法，数组）的对象
            - main_findings: 主要发现（数组）
            - conclusions: 结论（数组）
            - future_work: 未来工作（数组）
            
            请确保返回的是有效的JSON格式，不要包含任何其他文本。
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的学术论文分析助手，擅长从论文中提取结构化信息。请用中文回答，并确保返回有效的JSON格式。"},
                {"role": "user", "content": f"{prompt}\n\n{text}"}
            ]
            
            response = self._call_api(messages, temperature=0.3)
            content = response["choices"][0]["message"]["content"]
            
            # 尝试解析JSON
            try:
                # 使用正则表达式提取JSON部分
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content
                
                # 清理可能的非JSON内容
                json_str = re.sub(r'^[^{]*', '', json_str)
                json_str = re.sub(r'[^}]*$', '', json_str)
                
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
                return {
                    "error": True,
                    "message": "API返回的内容不是有效的JSON格式",
                    "raw_response": content
                }
        except Exception as e:
            logger.error(f"提取关键信息失败: {str(e)}")
            return {
                "error": True,
                "message": str(e)
            } 