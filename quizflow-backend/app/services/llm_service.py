# app/services/llm_service.py
from openai import OpenAI
from app.core.config import settings
import json
import re  # 导入正则


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )

    def _preprocess_json_string(self, raw_content: str) -> str:
        """
        企业级防御：利用正则表达式从 AI 的回复中提取纯净的 JSON 字符串
        防止 AI 返回类似 ```json ... ``` 的格式导致解析失败
        """
        # 寻找被 ```json 和 ``` 包裹的内容
        match = re.search(r'```json\s*(.*?)\s*```', raw_content, re.DOTALL)
        if match:
            return match.group(1).strip()
        # 如果没找到标签，尝试去掉可能的空白符直接返回
        return raw_content.strip()

    async def clean_pdf_text(self, raw_text: str):
        prompt = f"""
        请将文本转化为题目 JSON 列表。
        要求：
        1. 简答题 (ESSAY) 的 answer 字段请严格控制在 100 字以内，只保留核心要点。
        2. 严格输出 JSON 数组，不要任何开头或结尾的废话。
        3. 如果题目太多，请仅解析最重要的前 10 道题。

        文本内容：
        {raw_text}
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system",
                     "content": "你是一个严格的 JSON 解析器，只输出合法的 JSON 数组，不包含任何解释文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 降低随机性，使输出更稳定
                max_tokens=4096  # 显式增加输出上限，防止中途截断
            )

            raw_content = response.choices[0].message.content
            print(f"--- AI 原始返回内容 --- \n{raw_content}\n--- 结束 ---")

            # 1. 预处理内容（剥离 Markdown 标签）
            json_str = self._preprocess_json_string(raw_content)

            # 2. 尝试解析 JSON
            try:
                questions_data = json.loads(json_str)
                # 如果 AI 返回的是对象而不是列表，统一转为列表（增强兼容性）
                if isinstance(questions_data, dict) and "questions" in questions_data:
                    return questions_data["questions"]
                return questions_data
            except json.JSONDecodeError as e:
                print(f"JSON 格式解析失败: {e}")
                return {"error": "AI 返回格式有误，无法解析为 JSON", "raw": json_str}

        except Exception as e:
            # 捕获网络、API Key 或其他未知异常
            print(f"调用 AI 服务发生异常: {str(e)}")
            return {"error": "AI 服务调用失败", "details": str(e)}

    def _force_fix_json(self, json_str: str) -> str:
        json_str = json_str.strip()
        # 如果不是以 ] 结尾，尝试补齐
        if not json_str.endswith(']'):
            # 补齐引号、大括号、中括号
            if not json_str.endswith('"'): json_str += '"'
            if not json_str.endswith('}'): json_str += '}'
            if not json_str.endswith(']'): json_str += ']'
        return json_str


llm_service = LLMService()
