# 文件处理转换系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于FastAPI的Web应用程序,将Office文档(Word、Excel、PowerPoint)和PDF文件转换为Markdown格式。通过调用Unstructured API进行文档解析,提供简洁友好的Web界面。

## ✨ 功能特性

- 📤 **文件上传**: 支持拖拽上传和点击选择文件
- 🔄 **格式转换**: 自动将文档转换为Markdown格式
- 📊 **多格式支持**: Word (.doc, .docx)、Excel (.xls, .xlsx)、PowerPoint (.ppt, .pptx)、PDF (.pdf)
- ⚡ **快速处理**: 同步处理,实时返回结果
- 🎨 **友好界面**: 现代化Web界面,操作简单直观
- 🔒 **安全验证**: 文件类型和大小验证,防止恶意上传
- 📝 **详细日志**: 完整的操作日志记录

## 📋 系统要求

- Python 3.8 或更高版本
- 稳定的网络连接(需要访问Unstructured API)
- 推荐配置: 4GB内存,2核CPU

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd json2md
```

### 2. 配置API密钥

编辑 `config.yaml` 文件,填入您的Unstructured API密钥:

```yaml
unstructured:
  api_url: "https://api.unstructured.io/general/v0/general"
  api_key: "YOUR_API_KEY_HERE"  # 替换为您的API密钥
```

> 📌 如何获取API密钥:
> 1. 访问 [Unstructured.io](https://unstructured.io/)
> 2. 注册账号并创建API密钥
> 3. 将密钥填入配置文件

### 3. 启动服务

使用启动脚本(推荐):

```bash
./start.sh
```

或手动启动:

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

### 4. 访问应用

服务启动后,打开浏览器访问:

```
http://localhost:8000
```

## 📖 使用说明

### Web界面使用

1. 打开浏览器访问 `http://localhost:8000`
2. 点击上传区域或拖拽文件到上传区
3. 选择要转换的文件(支持Word、Excel、PowerPoint、PDF)
4. 点击"开始转换"按钮
5. 等待处理完成,自动下载生成的Markdown文件

### API接口使用

#### 文件转换接口

**请求:**

```bash
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@/path/to/your/document.pdf"
```

**响应:**

成功时返回Markdown文件流,浏览器会自动下载。

**错误码:**

- `400`: 文件验证失败(格式不支持或大小超限)
- `500`: 服务器内部错误
- `503`: Unstructured API服务不可用

#### 健康检查接口

```bash
curl http://localhost:8000/health
```

响应示例:

```json
{
  "status": "ok",
  "timestamp": "2025-12-09T15:30:00",
  "service": "文件处理转换系统"
}
```

## ⚙️ 配置说明

### 配置文件结构 (config.yaml)

```yaml
# Unstructured API配置
unstructured:
  api_url: "https://api.unstructured.io/general/v0/general"
  api_key: "YOUR_API_KEY"
  timeout: 60          # API调用超时时间(秒)
  max_retries: 3       # 最大重试次数

# 文件上传配置
upload:
  max_size: 52428800   # 最大文件大小(50MB)
  allowed_extensions:  # 允许的文件扩展名
    - doc
    - docx
    - xls
    - xlsx
    - ppt
    - pptx
    - pdf
  temp_dir: "./temp"   # 临时文件目录

# 服务器配置
server:
  host: "0.0.0.0"      # 监听地址
  port: 8000           # 服务端口

# 日志配置
logging:
  level: "INFO"        # 日志级别
  file: "./logs/app.log"  # 日志文件路径
```

### 环境变量支持

敏感配置可通过环境变量覆盖:

```bash
export UNSTRUCTURED_API_KEY="your-api-key"
export UNSTRUCTURED_API_URL="https://api.unstructured.io/general/v0/general"
```

## 📂 项目结构

```
json2md/
├── main.py              # FastAPI主程序
├── config.py            # 配置管理模块
├── converter.py         # JSON到Markdown转换引擎
├── api_client.py        # Unstructured API客户端
├── file_handler.py      # 文件处理和验证模块
├── config.yaml          # 配置文件
├── requirements.txt     # Python依赖
├── start.sh            # 启动脚本
├── static/             # 静态文件目录
│   └── index.html      # Web界面
├── temp/               # 临时文件目录(自动创建)
└── logs/               # 日志目录(自动创建)
```

## 🔧 开发指南

### 安装开发依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
pytest tests/
```

### 代码风格

项目遵循PEP 8代码规范,建议使用以下工具:

```bash
# 代码格式化
black .

# 代码检查
flake8 .
```

## 📝 转换规则

系统将Unstructured API返回的JSON元素映射为Markdown格式:

| JSON元素类型 | Markdown格式 | 说明 |
|-------------|-------------|------|
| Title | `# 标题` | 一级标题 |
| Header | `## 标题` | 二级标题 |
| NarrativeText | 正文 | 普通段落 |
| ListItem | `- 列表项` | 无序列表 |
| Table | 代码块 | 表格内容 |
| Image | `![图片](路径)` | 图片引用 |

## ⚠️ 注意事项

1. **API密钥安全**: 请妥善保管您的Unstructured API密钥,不要提交到版本控制
2. **文件大小限制**: 默认最大支持50MB文件,可在配置文件中调整
3. **网络要求**: 需要稳定的网络连接访问Unstructured API
4. **转换质量**: 复杂格式(如复杂表格、图表)的转换效果依赖于Unstructured API的解析能力
5. **临时文件清理**: 系统会自动清理1天前的临时文件

## 🐛 常见问题

### Q: 启动时提示"请在配置文件中设置有效的API密钥"

A: 请编辑 `config.yaml` 文件,将 `YOUR_API_KEY_HERE` 替换为您的实际API密钥。

### Q: 文件上传后转换失败

A: 检查以下几点:
- 网络连接是否正常
- Unstructured API密钥是否有效
- API服务是否可用
- 查看日志文件 `logs/app.log` 了解详细错误信息

### Q: 如何修改端口号

A: 编辑 `config.yaml` 中的 `server.port` 配置项。

### Q: 支持哪些文件格式

A: 目前支持:
- Microsoft Word: .doc, .docx
- Microsoft Excel: .xls, .xlsx
- Microsoft PowerPoint: .ppt, .pptx
- PDF: .pdf

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交Issue和Pull Request!

## 📧 联系方式

如有问题或建议,欢迎联系项目维护者。

---

**祝使用愉快! 🎉**
