#!/usr/bin/env python3
"""
任务模板库和执行计划生成器
提供丰富的预定义模板和智能计划生成能力
"""

import json
import os
import re
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TemplateCategory(Enum):
    """模板类别"""
    DATA_ANALYSIS = "数据分析"
    DOCUMENT_CREATION = "文档创建"
    MARKETING = "市场营销"
    PRODUCT_DEVELOPMENT = "产品开发"
    OPERATIONS = "运营管理"
    CUSTOM = "自定义"

@dataclass
class TaskTemplate:
    """任务模板定义"""
    id: str
    name: str
    category: TemplateCategory
    description: str
    complexity: str  # simple, medium, complex
    typical_scenarios: List[str]
    subtask_definitions: List[Dict[str, Any]]
    dependencies: List[Tuple[str, List[str]]]
    skill_requirements: List[str]
    estimated_time_range: Dict[str, int]  # min, max in minutes
    success_criteria: List[str]
    output_deliverables: List[str]
    tags: List[str]
    usage_count: int = 0
    success_rate: float = 0.0
    last_used: Optional[float] = None
    
class TemplateLibrary:
    """模板库管理器"""
    
    def __init__(self, templates_dir: str = None):
        self.templates_dir = templates_dir or os.path.join(os.path.dirname(__file__), "templates")
        os.makedirs(self.templates_dir, exist_ok=True)
        
        self.templates = self._load_templates()
        self._create_default_templates()
    
    def _load_templates(self) -> Dict[str, TaskTemplate]:
        """加载模板库"""
        templates = {}
        
        # 从文件加载
        template_files = [f for f in os.listdir(self.templates_dir) if f.endswith('.json')]
        
        for file_name in template_files:
            try:
                file_path = os.path.join(self.templates_dir, file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                template = TaskTemplate(**data)
                templates[template.id] = template
                
            except Exception as e:
                logger.error(f"加载模板文件 {file_name} 失败: {e}")
        
        return templates
    
    def _create_default_templates(self):
        """创建默认模板"""
        default_templates = [
            TaskTemplate(
                id="market_analysis_full",
                name="市场分析完整报告",
                category=TemplateCategory.DATA_ANALYSIS,
                description="完整的市场分析报告生成流程，包括数据收集、分析、可视化和报告撰写",
                complexity="complex",
                typical_scenarios=[
                    "新产品上市前市场调研",
                    "季度/年度市场趋势分析",
                    "竞争对手分析报告",
                    "市场机会评估"
                ],
                subtask_definitions=[
                    {
                        "id": "market_research",
                        "name": "市场调研",
                        "description": "收集市场数据、竞品信息和行业趋势",
                        "required_skills": ["search", "data_collection"],
                        "estimated_time": 60,
                        "outputs": ["调研数据汇总", "竞品分析表"]
                    },
                    {
                        "id": "data_cleaning",
                        "name": "数据清洗",
                        "description": "清洗和整理收集到的市场数据",
                        "required_skills": ["data_analysis", "data_processing"],
                        "estimated_time": 45,
                        "outputs": ["清洗后数据集", "数据质量报告"]
                    },
                    {
                        "id": "trend_analysis",
                        "name": "趋势分析",
                        "description": "分析市场趋势、增长率和潜在机会",
                        "required_skills": ["data_analysis", "statistics"],
                        "estimated_time": 90,
                        "outputs": ["趋势分析报告", "增长率预测"]
                    },
                    {
                        "id": "visualization",
                        "name": "可视化",
                        "description": "创建数据可视化图表和仪表板",
                        "required_skills": ["data_visualization", "chart_generation"],
                        "estimated_time": 75,
                        "outputs": ["可视化图表集", "交互式仪表板"]
                    },
                    {
                        "id": "report_writing",
                        "name": "报告撰写",
                        "description": "撰写完整的市场分析报告",
                        "required_skills": ["document_creation", "writing"],
                        "estimated_time": 120,
                        "outputs": ["市场分析报告.docx", "执行摘要"]
                    },
                    {
                        "id": "presentation",
                        "name": "演示材料",
                        "description": "准备演示用的PPT和讲解材料",
                        "required_skills": ["presentation", "slide_creation"],
                        "estimated_time": 60,
                        "outputs": ["演示文稿.pptx", "演讲笔记"]
                    }
                ],
                dependencies=[
                    ("data_cleaning", ["market_research"]),
                    ("trend_analysis", ["data_cleaning"]),
                    ("visualization", ["trend_analysis"]),
                    ("report_writing", ["visualization", "trend_analysis"]),
                    ("presentation", ["report_writing"])
                ],
                skill_requirements=["search", "data_analysis", "data_visualization", "document_creation", "presentation"],
                estimated_time_range={"min": 300, "max": 480},
                success_criteria=[
                    "报告覆盖所有关键市场指标",
                    "数据分析准确无误",
                    "可视化清晰易懂",
                    "报告结构完整逻辑清晰"
                ],
                output_deliverables=[
                    "市场调研数据汇总",
                    "竞品分析报告",
                    "市场趋势分析",
                    "数据可视化图表",
                    "完整市场分析报告",
                    "演示文稿"
                ],
                tags=["市场分析", "研究报告", "数据分析", "可视化", "商业智能"]
            ),
            TaskTemplate(
                id="product_launch_page",
                name="产品发布落地页",
                category=TemplateCategory.PRODUCT_DEVELOPMENT,
                description="产品发布所需的完整落地页开发流程",
                complexity="medium",
                typical_scenarios=[
                    "新产品上线推广",
                    "功能更新发布",
                    "营销活动推广页",
                    "产品演示页面"
                ],
                subtask_definitions=[
                    {
                        "id": "product_research",
                        "name": "产品研究",
                        "description": "分析产品特性和目标用户",
                        "required_skills": ["research", "user_analysis"],
                        "estimated_time": 45,
                        "outputs": ["产品特性列表", "用户画像"]
                    },
                    {
                        "id": "content_strategy",
                        "name": "内容策划",
                        "description": "制定页面内容策略和文案",
                        "required_skills": ["content_strategy", "copywriting"],
                        "estimated_time": 60,
                        "outputs": ["内容大纲", "文案草稿"]
                    },
                    {
                        "id": "design_concept",
                        "name": "设计概念",
                        "description": "创建页面视觉设计和布局",
                        "required_skills": ["ui_design", "graphic_design"],
                        "estimated_time": 90,
                        "outputs": ["设计稿", "色彩方案", "字体规范"]
                    },
                    {
                        "id": "image_generation",
                        "name": "图像生成",
                        "description": "生成产品图片和视觉素材",
                        "required_skills": ["image_generation", "graphic_design"],
                        "estimated_time": 60,
                        "outputs": ["产品图片", "图标集", "背景素材"]
                    },
                    {
                        "id": "web_development",
                        "name": "网页开发",
                        "description": "开发落地页代码和交互功能",
                        "required_skills": ["web_development", "frontend"],
                        "estimated_time": 120,
                        "outputs": ["HTML/CSS/JS代码", "响应式页面"]
                    },
                    {
                        "id": "testing_optimization",
                        "name": "测试优化",
                        "description": "测试页面功能和性能优化",
                        "required_skills": ["testing", "performance"],
                        "estimated_time": 45,
                        "outputs": ["测试报告", "优化建议"]
                    }
                ],
                dependencies=[
                    ("content_strategy", ["product_research"]),
                    ("design_concept", ["content_strategy"]),
                    ("image_generation", ["design_concept"]),
                    ("web_development", ["design_concept", "image_generation"]),
                    ("testing_optimization", ["web_development"])
                ],
                skill_requirements=["research", "design", "image_generation", "web_development", "testing"],
                estimated_time_range={"min": 240, "max": 360},
                success_criteria=[
                    "页面加载速度快",
                    "视觉设计美观一致",
                    "内容清晰有说服力",
                    "移动端适配良好",
                    "转化率达标"
                ],
                output_deliverables=[
                    "产品研究和用户画像",
                    "内容策略和文案",
                    "视觉设计稿",
                    "产品图片素材",
                    "完整落地页代码",
                    "测试报告"
                ],
                tags=["产品发布", "落地页", "网页开发", "UI设计", "营销"]
            ),
            TaskTemplate(
                id="social_media_campaign",
                name="社交媒体营销活动",
                category=TemplateCategory.MARKETING,
                description="社交媒体营销活动的完整策划和执行流程",
                complexity="medium",
                typical_scenarios=[
                    "品牌推广活动",
                    "产品促销活动",
                    "节日营销活动",
                    "用户增长活动"
                ],
                subtask_definitions=[
                    {
                        "id": "campaign_planning",
                        "name": "活动策划",
                        "description": "制定活动目标、策略和时间表",
                        "required_skills": ["strategy", "planning"],
                        "estimated_time": 60,
                        "outputs": ["活动策划案", "时间表", "预算"]
                    },
                    {
                        "id": "content_creation",
                        "name": "内容创作",
                        "description": "创建活动相关的图文视频内容",
                        "required_skills": ["content_creation", "copywriting"],
                        "estimated_time": 90,
                        "outputs": ["文案", "图片", "视频", "海报"]
                    },
                    {
                        "id": "visual_design",
                        "name": "视觉设计",
                        "description": "设计活动视觉形象和素材",
                        "required_skills": ["graphic_design", "branding"],
                        "estimated_time": 75,
                        "outputs": ["视觉规范", "设计素材", "模板"]
                    },
                    {
                        "id": "platform_setup",
                        "name": "平台设置",
                        "description": "设置社交媒体账号和活动页面",
                        "required_skills": ["social_media", "setup"],
                        "estimated_time": 45,
                        "outputs": ["账号设置", "页面配置", "跟踪代码"]
                    },
                    {
                        "id": "scheduling",
                        "name": "内容排期",
                        "description": "安排内容发布时间和频率",
                        "required_skills": ["scheduling", "automation"],
                        "estimated_time": 30,
                        "outputs": ["内容日历", "发布计划"]
                    },
                    {
                        "id": "analytics_setup",
                        "name": "分析设置",
                        "description": "设置数据跟踪和分析工具",
                        "required_skills": ["analytics", "tracking"],
                        "estimated_time": 45,
                        "outputs": ["跟踪设置", "分析仪表板", "报告模板"]
                    }
                ],
                dependencies=[
                    ("content_creation", ["campaign_planning"]),
                    ("visual_design", ["campaign_planning"]),
                    ("platform_setup", ["campaign_planning"]),
                    ("scheduling", ["content_creation", "visual_design"]),
                    ("analytics_setup", ["platform_setup"])
                ],
                skill_requirements=["strategy", "content", "design", "social_media", "analytics"],
                estimated_time_range={"min": 210, "max": 300},
                success_criteria=[
                    "活动参与度达标",
                    "内容质量和一致性",
                    "平台覆盖度",
                    "ROI达到预期",
                    "数据分析完整"
                ],
                output_deliverables=[
                    "活动策划方案",
                    "内容素材库",
                    "视觉设计规范",
                    "社交媒体设置",
                    "内容日历",
                    "分析报告模板"
                ],
                tags=["社交媒体", "营销活动", "内容营销", "品牌推广", "数字营销"]
            ),
            TaskTemplate(
                id="data_dashboard_project",
                name="数据仪表板项目",
                category=TemplateCategory.OPERATIONS,
                description="数据仪表板的完整开发项目",
                complexity="complex",
                typical_scenarios=[
                    "业务运营监控",
                    "KPI追踪仪表板",
                    "实时数据大屏",
                    "管理决策支持系统"
                ],
                subtask_definitions=[
                    {
                        "id": "requirements_analysis",
                        "name": "需求分析",
                        "description": "分析业务需求和数据指标",
                        "required_skills": ["business_analysis", "requirements"],
                        "estimated_time": 60,
                        "outputs": ["需求文档", "指标清单", "用户故事"]
                    },
                    {
                        "id": "data_pipeline",
                        "name": "数据管道",
                        "description": "建立数据收集和处理管道",
                        "required_skills": ["data_engineering", "etl"],
                        "estimated_time": 120,
                        "outputs": ["数据管道代码", "数据模型", "ETL脚本"]
                    },
                    {
                        "id": "dashboard_design",
                        "name": "仪表板设计",
                        "description": "设计仪表板布局和交互",
                        "required_skills": ["ui_design", "dashboard_design"],
                        "estimated_time": 90,
                        "outputs": ["设计原型", "交互规范", "布局方案"]
                    },
                    {
                        "id": "visualization_development",
                        "name": "可视化开发",
                        "description": "开发数据可视化组件",
                        "required_skills": ["data_visualization", "frontend"],
                        "estimated_time": 150,
                        "outputs": ["图表组件", "交互功能", "响应式适配"]
                    },
                    {
                        "id": "backend_api",
                        "name": "后端API",
                        "description": "开发数据API和后端服务",
                        "required_skills": ["backend", "api_development"],
                        "estimated_time": 120,
                        "outputs": ["API接口", "数据服务", "安全认证"]
                    },
                    {
                        "id": "deployment_monitoring",
                        "name": "部署监控",
                        "description": "部署系统和设置监控",
                        "required_skills": ["devops", "deployment"],
                        "estimated_time": 60,
                        "outputs": ["部署配置", "监控设置", "性能报告"]
                    }
                ],
                dependencies=[
                    ("data_pipeline", ["requirements_analysis"]),
                    ("dashboard_design", ["requirements_analysis"]),
                    ("visualization_development", ["dashboard_design"]),
                    ("backend_api", ["data_pipeline"]),
                    ("deployment_monitoring", ["visualization_development", "backend_api"])
                ],
                skill_requirements=["business_analysis", "data_engineering", "design", "web_development", "devops"],
                estimated_time_range={"min": 480, "max": 720},
                success_criteria=[
                    "数据准确实时",
                    "界面友好易用",
                    "性能稳定高效",
                    "扩展性强",
                    "监控报警完善"
                ],
                output_deliverables=[
                    "需求分析文档",
                    "数据管道系统",
                    "仪表板设计原型",
                    "可视化组件库",
                    "后端API服务",
                    "部署和监控系统"
                ],
                tags=["数据仪表板", "数据可视化", "业务智能", "监控系统", "数据分析"]
            )
        ]
        
        # 添加默认模板到库中
        for template in default_templates:
            if template.id not in self.templates:
                self.templates[template.id] = template
                self._save_template(template)
    
    def _save_template(self, template: TaskTemplate):
        """保存模板到文件"""
        file_path = os.path.join(self.templates_dir, f"{template.id}.json")
        
        # 转换为字典
        template_dict = asdict(template)
        
        # 处理枚举类型
        template_dict["category"] = template.category.value
        template_dict["last_used"] = template.last_used
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(template_dict, f, ensure_ascii=False, indent=2)
    
    def find_matching_templates(self, user_request: str, category: str = None) -> List[TaskTemplate]:
        """根据用户请求查找匹配的模板"""
        matched_templates = []
        
        # 关键词匹配
        keywords = user_request.lower()
        
        for template in self.templates.values():
            # 类别筛选
            if category and template.category.value != category:
                continue
            
            # 计算匹配分数
            score = self._calculate_template_match_score(template, keywords)
            
            if score > 0.3:  # 匹配阈值
                matched_templates.append((template, score))
        
        # 按匹配分数排序
        matched_templates.sort(key=lambda x: x[1], reverse=True)
        
        return [t[0] for t in matched_templates[:5]]  # 返回前5个
    
    def _calculate_template_match_score(self, template: TaskTemplate, keywords: str) -> float:
        """计算模板匹配分数"""
        score = 0.0
        
        # 模板名称匹配
        if template.name.lower() in keywords:
            score += 0.4
        
        # 描述匹配
        if template.description.lower() in keywords:
            score += 0.3
        
        # 标签匹配
        for tag in template.tags:
            if tag.lower() in keywords:
                score += 0.1
        
        # 典型场景匹配
        for scenario in template.typical_scenarios:
            if scenario.lower() in keywords:
                score += 0.2
        
        # 技能要求匹配
        for skill in template.skill_requirements:
            if skill.lower() in keywords:
                score += 0.05
        
        # 使用频率和成功率权重
        score += template.usage_count * 0.001
        score += template.success_rate * 0.1
        
        return min(score, 1.0)  # 限制最大分数为1.0
    
    def get_template(self, template_id: str) -> Optional[TaskTemplate]:
        """获取指定ID的模板"""
        return self.templates.get(template_id)
    
    def create_custom_template(self, user_request: str, execution_plan: Dict[str, Any], 
                              execution_results: Dict[str, Any]) -> TaskTemplate:
        """从执行结果创建自定义模板"""
        
        # 分析用户请求确定模板属性
        template_id = f"custom_{int(time.time())}"
        
        # 自动分类
        category = self._detect_category(user_request)
        
        # 确定复杂度
        subtask_count = len(execution_plan.get('subtasks', []))
        if subtask_count <= 3:
            complexity = "simple"
        elif subtask_count <= 6:
            complexity = "medium"
        else:
            complexity = "complex"
        
        # 提取技能要求
        skill_requirements = list(set(
            skill for subtask in execution_plan.get('subtasks', []) 
            for skill in subtask.get('required_skills', [])
        ))
        
        # 创建模板
        template = TaskTemplate(
            id=template_id,
            name=f"自定义模板: {user_request[:30]}...",
            category=category,
            description=f"基于请求 '{user_request}' 创建的自定义模板",
            complexity=complexity,
            typical_scenarios=[user_request],
            subtask_definitions=[
                {
                    "id": st.get('id'),
                    "name": st.get('description', '').split()[0] if st.get('description') else st.get('id'),
                    "description": st.get('description', ''),
                    "required_skills": st.get('required_skills', []),
                    "estimated_time": st.get('estimated_time', 60),
                    "outputs": [f"输出_{st.get('id')}"]
                }
                for st in execution_plan.get('subtasks', [])
            ],
            dependencies=execution_plan.get('dependencies', []),
            skill_requirements=skill_requirements,
            estimated_time_range={
                "min": execution_results.get('total_time', 60) // 60,
                "max": (execution_results.get('total_time', 60) * 1.5) // 60
            },
            success_criteria=[
                "所有子任务执行成功",
                "产出符合预期",
                "执行时间在预估范围内"
            ],
            output_deliverables=[
                f"{st.get('id')}_output" for st in execution_plan.get('subtasks', [])
            ],
            tags=["自定义", "自动生成", f"复杂度:{complexity}"]
        )
        
        # 保存模板
        self.templates[template_id] = template
        self._save_template(template)
        
        logger.info(f"已创建自定义模板: {template_id}")
        return template
    
    def _detect_category(self, user_request: str) -> TemplateCategory:
        """检测用户请求的类别"""
        request_lower = user_request.lower()
        
        category_keywords = {
            TemplateCategory.DATA_ANALYSIS: ["分析", "数据", "统计", "报表", "趋势", "预测"],
            TemplateCategory.DOCUMENT_CREATION: ["报告", "文档", "PPT", "幻灯片", "撰写", "编写"],
            TemplateCategory.MARKETING: ["营销", "推广", "市场", "品牌", "广告", "活动"],
            TemplateCategory.PRODUCT_DEVELOPMENT: ["产品", "开发", "设计", "功能", "原型", "测试"],
            TemplateCategory.OPERATIONS: ["运营", "管理", "监控", "流程", "优化", "效率"]
        }
        
        max_score = 0
        detected_category = TemplateCategory.CUSTOM
        
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in request_lower)
            if score > max_score:
                max_score = score
                detected_category = category
        
        return detected_category
    
    def update_template_stats(self, template_id: str, success: bool):
        """更新模板使用统计"""
        template = self.templates.get(template_id)
        if not template:
            return
        
        template.usage_count += 1
        template.last_used = time.time()
        
        # 更新成功率
        if success:
            # 简化计算：成功次数 = 成功率 * 使用次数
            success_count = template.success_rate * (template.usage_count - 1)
            template.success_rate = (success_count + 1) / template.usage_count
        else:
            success_count = template.success_rate * (template.usage_count - 1)
            template.success_rate = success_count / template.usage_count
        
        self._save_template(template)
    
    def export_templates(self, export_dir: str):
        """导出所有模板"""
        os.makedirs(export_dir, exist_ok=True)
        
        for template in self.templates.values():
            file_path = os.path.join(export_dir, f"{template.id}.json")
            template_dict = asdict(template)
            template_dict["category"] = template.category.value
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已导出 {len(self.templates)} 个模板到 {export_dir}")

class ExecutionPlanGenerator:
    """执行计划生成器"""
    
    def __init__(self, template_library: TemplateLibrary):
        self.template_library = template_library
    
    def generate_from_template(self, template: TaskTemplate, customization: Dict[str, Any] = None) -> Dict[str, Any]:
        """基于模板生成执行计划"""
        
        logger.info(f"基于模板 {template.id} 生成执行计划")
        
        # 应用自定义设置
        customization = customization or {}
        
        # 创建子任务定义
        subtasks = []
        for subtask_def in template.subtask_definitions:
            # 应用自定义设置
            custom_config = customization.get(subtask_def["id"], {})
            
            subtask = {
                "id": subtask_def["id"],
                "name": subtask_def["name"],
                "description": custom_config.get("description", subtask_def["description"]),
                "required_skills": custom_config.get("required_skills", subtask_def["required_skills"]),
                "estimated_time": custom_config.get("estimated_time", subtask_def["estimated_time"]),
                "priority": custom_config.get("priority", "normal"),
                "outputs": custom_config.get("outputs", subtask_def["outputs"])
            }
            subtasks.append(subtask)
        
        # 构建执行计划
        execution_plan = {
            "template_id": template.id,
            "template_name": template.name,
            "category": template.category.value,
            "complexity": template.complexity,
            "description": template.description,
            "subtasks": subtasks,
            "dependencies": template.dependencies,
            "skill_requirements": template.skill_requirements,
            "estimated_time": {
                "min": template.estimated_time_range["min"],
                "max": template.estimated_time_range["max"],
                "unit": "minutes"
            },
            "success_criteria": template.success_criteria,
            "output_deliverables": template.output_deliverables,
            "created_at": time.time(),
            "customization_applied": bool(customization)
        }
        
        return execution_plan
    
    def optimize_parallel_execution(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """优化并行执行顺序"""
        
        subtasks = execution_plan["subtasks"]
        dependencies = execution_plan.get("dependencies", [])
        
        # 构建依赖图
        dep_graph = {}
        for subtask in subtasks:
            dep_graph[subtask["id"]] = []
        
        # 添加依赖关系
        for dep in dependencies:
            if isinstance(dep, tuple) and len(dep) == 2:
                task_id, deps = dep
                if isinstance(deps, str):
                    deps = [deps]
                dep_graph[task_id] = deps
        
        # 拓扑排序
        def topological_sort(graph):
            visited = set()
            result = []
            
            def dfs(node):
                if node in visited:
                    return
                visited.add(node)
                
                for neighbor in graph.get(node, []):
                    dfs(neighbor)
                
                result.append(node)
            
            for node in graph:
                dfs(node)
            
            return result
        
        # 获取执行顺序
        execution_order = topological_sort(dep_graph)
        
        # 识别并行组（没有依赖关系的任务可以并行执行）
        parallel_groups = []
        current_group = []
        
        for task_id in execution_order:
            if not dep_graph.get(task_id, []):
                current_group.append(task_id)
            else:
                if current_group:
                    parallel_groups.append(current_group.copy())
                    current_group = []
                parallel_groups.append([task_id])
        
        if current_group:
            parallel_groups.append(current_group)
        
        # 更新执行计划
        execution_plan["execution_order"] = execution_order
        execution_plan["parallel_groups"] = parallel_groups
        
        # 计算理论最小执行时间（假设理想并行）
        task_times = {st["id"]: st["estimated_time"] for st in subtasks}
        
        max_parallel_time = 0
        for group in parallel_groups:
            group_time = max(task_times.get(task_id, 0) for task_id in group)
            max_parallel_time += group_time
        
        execution_plan["optimized_estimated_time"] = {
            "sequential": sum(task_times.values()),
            "parallel_ideal": max_parallel_time,
            "improvement_rate": (sum(task_times.values()) - max_parallel_time) / sum(task_times.values())
        }
        
        logger.info(f"执行计划优化完成: 顺序执行{execution_plan['optimized_estimated_time']['sequential']}秒, 并行理想{max_parallel_time}秒")
        
        return execution_plan
    
    def generate_custom_plan(self, user_request: str, detected_skills: List[str]) -> Dict[str, Any]:
        """根据检测到的技能生成自定义执行计划"""
        
        logger.info(f"为请求 '{user_request}' 生成自定义执行计划")
        
        # 根据技能创建子任务
        subtasks = []
        for i, skill in enumerate(detected_skills):
            subtask_id = f"custom_task_{i+1}"
            
            # 根据技能类型确定任务描述
            task_descriptions = {
                "search": "收集相关信息和数据",
                "data_analysis": "分析数据和提取洞察",
                "document_creation": "创建文档和报告",
                "image_generation": "生成视觉素材和图片",
                "web_development": "开发网页和交互界面",
                "automation": "自动化流程和任务"
            }
            
            description = task_descriptions.get(skill, f"执行{skill}相关任务")
            
            subtask = {
                "id": subtask_id,
                "name": f"{skill}任务",
                "description": description,
                "required_skills": [skill],
                "estimated_time": 90,  # 默认1.5分钟
                "priority": "normal",
                "outputs": [f"{skill}_output"]
            }
            subtasks.append(subtask)
        
        # 创建依赖关系（默认顺序执行）
        dependencies = []
        for i in range(1, len(subtasks)):
            dependencies.append((subtasks[i]["id"], [subtasks[i-1]["id"]]))
        
        # 创建执行计划
        execution_plan = {
            "template_id": "custom_generated",
            "template_name": "智能生成计划",
            "category": "custom",
            "complexity": "medium" if len(subtasks) <= 4 else "complex",
            "description": f"为请求 '{user_request}' 智能生成的自定义执行计划",
            "subtasks": subtasks,
            "dependencies": dependencies,
            "skill_requirements": detected_skills,
            "estimated_time": {
                "min": len(subtasks) * 60,
                "max": len(subtasks) * 120,
                "unit": "seconds"
            },
            "success_criteria": [
                "所有检测到的技能任务执行成功",
                "产出满足用户需求",
                "执行流程逻辑合理"
            ],
            "output_deliverables": [st["id"] + "_output" for st in subtasks],
            "created_at": time.time(),
            "customization_applied": False
        }
        
        # 优化并行执行
        execution_plan = self.optimize_parallel_execution(execution_plan)
        
        return execution_plan

def main():
    """演示模板库和执行计划生成器"""
    
    # 创建模板库
    library = TemplateLibrary()
    
    print("模板库已加载:")
    print(f"  模板总数: {len(library.templates)}")
    print(f"  模板类别: {[c.value for c in TemplateCategory]}")
    print()
    
    # 演示模板查找
    test_request = "我需要一个市场分析报告，包含数据分析和可视化"
    
    print(f"测试请求: {test_request}")
    print("查找匹配模板...")
    
    matched_templates = library.find_matching_templates(test_request)
    
    print(f"找到 {len(matched_templates)} 个匹配模板:")
    for template in matched_templates:
        print(f"  - {template.name} ({template.category.value}, 复杂度: {template.complexity})")
        print(f"    描述: {template.description}")
        print(f"    预估时间: {template.estimated_time_range['min']}-{template.estimated_time_range['max']}分钟")
        print()
    
    # 演示执行计划生成
    if matched_templates:
        selected_template = matched_templates[0]
        
        print(f"选择模板: {selected_template.name}")
        
        # 创建执行计划生成器
        generator = ExecutionPlanGenerator(library)
        
        # 生成执行计划
        plan = generator.generate_from_template(selected_template)
        
        print("生成的执行计划:")
        print(f"  模板ID: {plan['template_id']}")
        print(f"  子任务数: {len(plan['subtasks'])}")
        print(f"  预估时间范围: {plan['estimated_time']['min']}-{plan['estimated_time']['max']} {plan['estimated_time']['unit']}")
        print(f"  产出物: {', '.join(plan['output_deliverables'][:3])}...")
        print()
        
        # 演示优化
        optimized_plan = generator.optimize_parallel_execution(plan)
        
        print("优化后的执行计划:")
        print(f"  执行顺序: {', '.join(optimized_plan['execution_order'][:5])}...")
        print(f"  并行组数: {len(optimized_plan['parallel_groups'])}")
        print(f"  理论改进率: {optimized_plan['optimized_estimated_time']['improvement_rate']:.1%}")
    
    # 演示自定义计划生成
    print("\n" + "="*50)
    print("演示自定义计划生成:")
    
    custom_request = "帮我创建一个产品介绍页面，需要图片和数据分析"
    detected_skills = ["search", "data_analysis", "image_generation", "web_development"]
    
    custom_plan = generator.generate_custom_plan(custom_request, detected_skills)
    
    print(f"自定义请求: {custom_request}")
    print(f"检测到的技能: {detected_skills}")
    print(f"生成的子任务数: {len(custom_plan['subtasks'])}")
    print(f"执行顺序: {custom_plan['execution_order']}")

if __name__ == "__main__":
    main()