"""
FastAPI Web服务主程序
提供文件上传转换的HTTP API接口
"""

import logging
import sys
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import config_manager, AppConfig
from file_handler import FileHandler, FileValidationError
from api_client import UnstructuredAPIClient, UnstructuredAPIError
from converter import convert_json_to_markdown


# 全局变量
app_config: Optional[AppConfig] = None
file_handler: Optional[FileHandler] = None
api_client: Optional[UnstructuredAPIClient] = None


def setup_logging(config: AppConfig):
    """配置日志系统"""
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.logging.file, encoding='utf-8')
        ]
    )
    
    # 设置第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global app_config, file_handler, api_client
    
    # 启动时执行
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("文件处理转换系统启动中...")
    
    try:
        # 加载配置
        app_config = config_manager.load_config()
        logger.info("✓ 配置加载成功")
        
        # 配置日志
        setup_logging(app_config)
        logger.info("✓ 日志系统配置完成")
        
        # 初始化文件处理器
        file_handler = FileHandler(
            temp_dir=app_config.upload.temp_dir,
            allowed_extensions=app_config.upload.allowed_extensions,
            max_size=app_config.upload.max_size
        )
        logger.info("✓ 文件处理器初始化完成")
        
        # 初始化API客户端
        api_client = UnstructuredAPIClient(
            api_url=app_config.unstructured.api_url,
            timeout=app_config.unstructured.timeout,
            max_retries=app_config.unstructured.max_retries,
            default_strategy=app_config.unstructured.default_strategy
        )
        logger.info("✓ API客户端初始化完成")
        
        # 清理旧的临时文件
        file_handler.cleanup_old_files(days=1)
        
        logger.info("=" * 60)
        logger.info(f"服务已启动: http://{app_config.server.host}:{app_config.server.port}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ 启动失败: {e}")
        sys.exit(1)
    
    yield
    
    # 关闭时执行
    logger.info("服务正在关闭...")
    logger.info("再见!")


# 创建FastAPI应用
app = FastAPI(
    title="文件处理转换系统",
    description="将Office文档和PDF文件转换为Markdown格式",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    pass  # 如果static目录不存在,忽略错误


@app.get("/")
async def root():
    """根路径,返回欢迎页面"""
    try:
        return FileResponse("static/index.html")
    except Exception:
        return {
            "message": "文件处理转换系统",
            "version": "1.0.0",
            "endpoints": {
                "convert": "POST /api/convert - 上传文件并转换为Markdown",
                "health": "GET /health - 健康检查"
            }
        }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "文件处理转换系统"
    }


@app.post("/api/convert")
async def convert_file(
    request: Request,
    file: UploadFile = File(...),
    enable_ocr: bool = Form(False)
):
    """
    文件上传转换接口
    
    Args:
        file: 上传的文件
        enable_ocr: 是否启用OCR(仅PDF有效)
        
    Returns:
        FileResponse: Markdown文件下载响应
        
    Raises:
        HTTPException: 处理错误
    """
    logger = logging.getLogger(__name__)
    temp_file_path = None
    
    try:
        # 读取文件内容
        file_content = await file.read()
        original_filename = file.filename or "unknown"
        
        logger.info(f"收到文件上传请求: {original_filename}, 大小: {len(file_content)} 字节")
        
        # 保存临时文件
        try:
            temp_file_path = file_handler.save_temp_file(file_content, original_filename)
        except FileValidationError as e:
            logger.warning(f"文件验证失败: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # 根据文件类型和OCR选项决定strategy
        strategy = file_handler.get_strategy_for_file(original_filename, enable_ocr)
        logger.info(f"使用strategy: {strategy}, OCR启用: {enable_ocr}")
        
        # 调用Unstructured API
        try:
            logger.info(f"调用Unstructured API处理文件: {original_filename}")
            json_data = api_client.process_file(temp_file_path, strategy=strategy)
        except UnstructuredAPIError as e:
            logger.error(f"Unstructured API调用失败: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Unstructured API服务暂时不可用: {str(e)}"
            )
        
        # 转换为Markdown
        try:
            logger.info(f"将JSON转换为Markdown: {original_filename}")
            markdown_content = convert_json_to_markdown(json_data)
        except Exception as e:
            logger.error(f"JSON转换失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"文件转换失败: {str(e)}"
            )
        
        # 生成输出文件名
        output_filename = file_handler.get_safe_filename(original_filename)
        
        # 保存Markdown到临时文件
        output_path = temp_file_path + ".md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"转换完成: {original_filename} -> {output_filename}")
        
        # 返回文件下载响应
        def cleanup():
            """清理临时文件"""
            if temp_file_path:
                file_handler.cleanup_file(temp_file_path)
            file_handler.cleanup_file(output_path)
        
        # 注册后台清理任务
        request.app.state.cleanup = cleanup
        
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type="text/markdown",
            background=None  # 先返回响应,不立即清理
        )
    
    except HTTPException:
        # 清理临时文件
        if temp_file_path:
            file_handler.cleanup_file(temp_file_path)
        raise
    
    except Exception as e:
        logger.error(f"处理请求时发生未知错误: {e}", exc_info=True)
        
        # 清理临时文件
        if temp_file_path:
            file_handler.cleanup_file(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger = logging.getLogger(__name__)
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "服务器内部错误",
            "timestamp": datetime.now().isoformat()
        }
    )


def main():
    """主函数"""
    # 先加载配置以获取服务器配置
    try:
        config = config_manager.load_config()
    except Exception as e:
        print(f"错误: 配置加载失败: {e}")
        print("请检查config.yaml文件是否存在且配置正确")
        sys.exit(1)
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
        log_level=config.logging.level.lower()
    )


if __name__ == "__main__":
    main()
