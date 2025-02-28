import fitz  # PyMuPDF
import os
import tempfile
import logging
try:
    import magic
    has_magic = True
except ImportError:
    import mimetypes
    has_magic = False
    logging.warning("无法导入magic库，将使用mimetypes作为备用方案")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, temp_dir=None):
        """初始化PDF处理器"""
        if temp_dir is None:
            # 使用系统临时目录
            self.temp_dir = os.path.join(tempfile.gettempdir(), "pdf_processor_temp")
        else:
            self.temp_dir = temp_dir
        self._ensure_temp_dir()
        logger.info(f"使用临时目录: {self.temp_dir}")
    
    def _ensure_temp_dir(self):
        """确保临时目录存在"""
        try:
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir, exist_ok=True)
                logger.info(f"创建临时目录: {self.temp_dir}")
            
            # 测试目录写入权限
            test_file = os.path.join(self.temp_dir, "test_write.txt")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            logger.error(f"临时目录创建或权限测试失败: {str(e)}")
            # 尝试使用备用临时目录
            self.temp_dir = tempfile.mkdtemp()
            logger.info(f"使用备用临时目录: {self.temp_dir}")
    
    def validate_pdf(self, file_path):
        """验证文件是否为有效的PDF"""
        try:
            if has_magic:
                mime = magic.Magic(mime=True)
                file_type = mime.from_file(file_path)
                if file_type != 'application/pdf':
                    raise ValueError(f"无效的文件类型: {file_type}")
            else:
                # 使用mimetypes作为备用方案
                file_type, _ = mimetypes.guess_type(file_path)
                if file_type != 'application/pdf':
                    # 额外检查：尝试打开文件
                    try:
                        doc = fitz.open(file_path)
                        doc.close()
                    except Exception as e:
                        raise ValueError(f"无效的PDF文件: {str(e)}")
            return True
        except Exception as e:
            logger.error(f"PDF验证失败: {str(e)}")
            raise
    
    def extract_text(self, pdf_path):
        """从PDF中提取文本"""
        try:
            self.validate_pdf(pdf_path)
            doc = fitz.open(pdf_path)
            text = []
            
            for page_num, page in enumerate(doc):
                try:
                    text.append(page.get_text())
                except Exception as e:
                    logger.warning(f"提取第{page_num+1}页文本时出错: {str(e)}")
            
            return "\n".join(text)
        except Exception as e:
            logger.error(f"文本提取失败: {str(e)}")
            raise
        finally:
            if 'doc' in locals():
                doc.close()
    
    def extract_tables(self, pdf_path):
        """从PDF中提取表格（基本实现）"""
        # TODO: 实现表格提取功能
        pass
    
    def cleanup(self):
        """清理临时文件"""
        try:
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.warning(f"删除文件失败 {file_path}: {str(e)}")
            logger.info("临时文件清理完成")
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
            raise 