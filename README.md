# 论文分析助手

基于DeepSeek和Streamlit的论文分析工具，支持PDF文档的智能分析、内容解释和图片提取。

## 功能特点

- 📄 PDF文档解析
- 🔍 智能内容分析
- 📊 数据提取和可视化
- 🖼️ 图片提取和展示
- ❓ 智能问答功能

## 安装说明

1. 克隆项目到本地
```bash
git clone [项目地址]
cd paper-analysis-assistant
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
创建 `.env` 文件并添加以下内容：
```
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_URL=your_api_url_here
```

4. 运行应用
```bash
streamlit run main.py
```

## 使用说明

1. 启动应用后，在浏览器中打开显示的地址
2. 点击"上传论文PDF"按钮选择要分析的PDF文件
3. 使用不同的功能标签页进行分析：
   - 内容分析：获取论文的核心内容和摘要
   - 数据解析：提取论文中的关键数据和结果
   - 图片提取：自动提取论文中的图表
   - 智能问答：针对论文内容提问

## 注意事项

- 支持的PDF文件大小上限为200MB
- 请确保PDF文件格式正确，不支持加密的PDF文件
- 图片提取功能可能需要一定处理时间，请耐心等待

## 技术栈

- Streamlit：Web界面框架
- PyMuPDF：PDF处理
- DeepSeek API：智能分析
- Python-dotenv：环境变量管理
- Pandas：数据处理
- Pillow：图像处理

## 许可证

MIT License 