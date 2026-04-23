from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.pdf_handler import extract_text_from_pdf
from app.services.llm_service import llm_service
import shutil
import os

router = APIRouter()


@router.post("/parse")
async def parse_file(file: UploadFile = File(...)):
    # 预定义变量，确保安全
    raw_text = ""
    temp_path = f"temp_{file.filename}"

    # 1. 严格校验格式
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="当前模式仅支持 PDF 文件")

    print(f"\n[开始处理] 收到文件: {file.filename}")

    try:
        # 2. 保存到本地临时文件
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"[1/3] 文件已暂存至: {temp_path}")

        # 3. 提取 PDF 文本
        raw_text = extract_text_from_pdf(temp_path)
        if not raw_text or len(raw_text.strip()) == 0:
            print("[错误] PDF 提取内容为空，请检查是否为扫描件")
            raise HTTPException(status_code=400, detail="无法从 PDF 中提取文字，请确保不是图片类 PDF")

        print(f"[2/3] 文本提取成功，长度: {len(raw_text)} 字符")

        # 4. 调用 AI 解析
        print("[3/3] 正在请求 DeepSeek 进行结构化解析...")
        result = await llm_service.clean_pdf_text(raw_text)

        # 检查 AI 服务返回的是否是错误对象
        if isinstance(result, dict) and "error" in result:
            print(f"[错误] AI 解析环节失败: {result['error']}")
            raise HTTPException(status_code=500, detail=f"AI 解析失败: {result['error']}")

        print("[完成] 解析成功，准备返回 JSON 数据")
        return {"questions": result}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[崩溃] 发生未捕获异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

    finally:
        # 5. 无论成功失败，必须清理战场
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"[清理] 临时文件 {temp_path} 已删除")
