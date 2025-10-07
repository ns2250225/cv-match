import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class DeepSeekService:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        
    def analyze_match(self, job_description, resume_content):
        """
        分析岗位描述和简历的匹配度
        """
        if not self.api_key or self.api_key == 'your_deepseek_api_key_here':
            # 如果没有配置API密钥，返回模拟数据
            print("使用模拟数据（API密钥未配置或为默认值）")
            return self._get_mock_result(job_description, resume_content)
        

        prompt = self._build_prompt(job_description, resume_content)
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            print(f"调用DeepSeek API，请求数据长度: {len(prompt)} 字符")
            response = requests.post(self.base_url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"DeepSeek API调用成功，返回内容长度: {len(content)} 字符")
            
            # 解析返回的JSON内容
            parsed_result = self._parse_response(content)
            print(f"解析结果: {parsed_result.get('total_score', 0)}分")
            return parsed_result
            
        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API网络请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应状态码: {e.response.status_code}")
                print(f"响应内容: {e.response.text}")
            return self._get_mock_result(job_description, resume_content)
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return self._get_mock_result(job_description, resume_content)
    
    def _build_prompt(self, job_description, resume_content):
        """构建提示词"""
        result_example = """
        {
            "dimension_scores": {
                "职位职能": {"score": 85, "reason": "简历中的工作经历与岗位职能高度相关", "suggestion": "可以进一步突出相关项目经验"},
                "学历要求": {"score": 90, "reason": "学历符合岗位要求", "suggestion": "无"},
                "专业要求": {"score": 80, "reason": "专业背景基本匹配", "suggestion": "可以补充相关专业课程"},
                "工作年限": {"score": 75, "reason": "工作经验略低于要求", "suggestion": "突出项目经验和技能成长"},
                "专业技能": {"score": 88, "reason": "具备岗位所需的核心技能", "suggestion": "可以增加具体技术栈的深度描述"}
            },
            "total_score": 83.6,
            "overall_assessment": "简历与岗位匹配度良好，具备较强的竞争力",
            "improvement_suggestions": [
                "增加相关项目经验的详细描述",
                "突出技术栈的深度和广度",
                "量化工作成果和贡献"
            ]
        }
        """
        
        return f"""# 你是一个招聘大数据智能分析助手，请帮我评估现有【岗位描述】、【候选人简历】之间的匹配度。
# 岗位描述：{job_description}
# 候选人简历：{resume_content}

- 根据岗位描述获取该岗位需要以下哪些任职要求：职位职能,学历要求,专业要求,工作年限,学校要求,任职公司要求,专业技能要求,软性技能要求,加分技能要求,语言要求,证书,性别要求,年龄要求,管理能力要求,职能经验要求,行业经验要求。
- 根据获取到的岗位任职要求和简历信息作多维度细化分析，岗位介绍中没有提及的任职要求对简历不做要求，计算得出简历和岗位涉及到任职要求的匹配度。
- 整理并逐条以json的格式返回下面信息：各维度匹配得分、打分原因、修改建议、匹配度总分(总分为100%)。不返回岗位任职要求。

请确保返回的是有效的JSON格式。
返回结果的json例子为:
{result_example}
"""
    
    def _parse_response(self, content):
        """解析API返回的内容"""
        try:
            # 尝试从内容中提取JSON
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                json_str = content.split('```')[1].strip()
            else:
                json_str = content.strip()
            
            # 清理可能的非JSON内容
            json_str = json_str.replace('```', '').strip()
            
            result = json.loads(json_str)
            return result
            
        except json.JSONDecodeError:
            # 如果解析失败，返回默认结构
            return self._get_default_structure()
    
    def _get_mock_result(self, job_description, resume_content):
        """获取模拟结果（用于测试或API不可用时）"""
        return {
            "dimension_scores": {
                "职位职能": {"score": 85, "reason": "简历中的工作经历与岗位职能高度相关", "suggestion": "可以进一步突出相关项目经验"},
                "学历要求": {"score": 90, "reason": "学历符合岗位要求", "suggestion": "无"},
                "专业要求": {"score": 80, "reason": "专业背景基本匹配", "suggestion": "可以补充相关专业课程"},
                "工作年限": {"score": 75, "reason": "工作经验略低于要求", "suggestion": "突出项目经验和技能成长"},
                "专业技能": {"score": 88, "reason": "具备岗位所需的核心技能", "suggestion": "可以增加具体技术栈的深度描述"}
            },
            "total_score": 83.6,
            "overall_assessment": "简历与岗位匹配度良好，具备较强的竞争力",
            "improvement_suggestions": [
                "增加相关项目经验的详细描述",
                "突出技术栈的深度和广度",
                "量化工作成果和贡献"
            ]
        }
    
    def _get_default_structure(self):
        """获取默认的返回结构"""
        return {
            "dimension_scores": {},
            "total_score": 0,
            "overall_assessment": "分析结果解析失败",
            "improvement_suggestions": []
        }