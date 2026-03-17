#!/usr/bin/env python3
"""
多技能智能编排引擎核心模块
负责任务拆解、技能匹配、执行编排和异常处理
"""

import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"

class SkillType(Enum):
    """技能类型枚举"""
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_CREATION = "document_creation"
    IMAGE_GENERATION = "image_generation"
    WEB_DEVELOPMENT = "web_development"
    SEARCH = "search"
    AUTOMATION = "automation"
    OTHER = "other"

@dataclass
class Subtask:
    """子任务定义"""
    id: str
    description: str
    required_skills: List[SkillType]
    dependencies: List[str]  # 依赖的其他子任务ID
    estimated_time: int  # 预估执行时间（秒）
    max_retries: int = 3
    current_retries: int = 0
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    assigned_skill: Optional[str] = None
    
@dataclass
class SkillProfile:
    """技能配置文件"""
    name: str
    skill_type: SkillType
    description: str
    capabilities: List[str]
    input_requirements: List[str]
    output_format: str
    execution_time_estimate: Dict[str, int]  # 不同复杂度的时间估计
    success_rate: float
    compatibility: List[SkillType]  # 可组合的技能类型
    
@dataclass
class ExecutionPlan:
    """执行计划"""
    task_id: str
    subtasks: List[Subtask]
    execution_order: List[str]  # 子任务执行顺序
    parallel_groups: List[List[str]]  # 可并行执行的子任务组
    estimated_total_time: int
    skill_mapping: Dict[str, str]  # 子任务ID -> 技能名称映射

class MultiSkillOrchestrator:
    """多技能智能编排器"""
    
    def __init__(self):
        self.skill_profiles = self._load_skill_profiles()
        self.task_templates = self._load_task_templates()
        self.execution_history = []
        
    def _load_skill_profiles(self) -> Dict[str, SkillProfile]:
        """加载技能配置文件"""
        # 这里从配置文件或数据库中加载技能信息
        # 实际实现中应该从外部文件加载
        return {
            "data_analysis": SkillProfile(
                name="数据分析",
                skill_type=SkillType.DATA_ANALYSIS,
                description="数据清洗、分析和可视化",
                capabilities=["数据清洗", "统计分析", "图表生成", "趋势预测"],
                input_requirements=["CSV/Excel文件", "JSON数据", "数据库连接"],
                output_format="分析报告、可视化图表",
                execution_time_estimate={"simple": 60, "medium": 300, "complex": 900},
                success_rate=0.95,
                compatibility=[SkillType.DOCUMENT_CREATION, SkillType.WEB_DEVELOPMENT]
            ),
            "document_creation": SkillProfile(
                name="文档创建",
                skill_type=SkillType.DOCUMENT_CREATION,
                description="创建和编辑各种文档",
                capabilities=["报告撰写", "PPT制作", "文档格式化", "多语言翻译"],
                input_requirements=["文本内容", "数据表格", "图片素材"],
                output_format="Word文档、PPT、PDF报告",
                execution_time_estimate={"simple": 120, "medium": 600, "complex": 1800},
                success_rate=0.90,
                compatibility=[SkillType.DATA_ANALYSIS, SkillType.IMAGE_GENERATION]
            ),
            "image_generation": SkillProfile(
                name="图像生成",
                skill_type=SkillType.IMAGE_GENERATION,
                description="AI图像生成和编辑",
                capabilities=["文生图", "图生图", "图像编辑", "风格迁移"],
                input_requirements=["文本描述", "参考图片", "风格要求"],
                output_format="PNG/JPG图片、图像序列",
                execution_time_estimate={"simple": 30, "medium": 90, "complex": 300},
                success_rate=0.85,
                compatibility=[SkillType.DOCUMENT_CREATION, SkillType.WEB_DEVELOPMENT]
            ),
            "web_development": SkillProfile(
                name="网页开发",
                skill_type=SkillType.WEB_DEVELOPMENT,
                description="创建交互式网页和仪表板",
                capabilities=["HTML/CSS开发", "JavaScript编程", "数据可视化", "API集成"],
                input_requirements=["设计需求", "数据源", "功能说明"],
                output_format="HTML文件、Web应用、交互式仪表板",
                execution_time_estimate={"simple": 300, "medium": 1200, "complex": 3600},
                success_rate=0.88,
                compatibility=[SkillType.DATA_ANALYSIS, SkillType.IMAGE_GENERATION]
            )
        }
    
    def _load_task_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载任务模板"""
        return {
            "market_analysis_report": {
                "name": "市场分析报告",
                "description": "完整市场分析报告生成流程",
                "subtasks": [
                    {"id": "data_collection", "description": "收集市场数据", "skills": [SkillType.SEARCH, SkillType.DATA_ANALYSIS]},
                    {"id": "data_analysis", "description": "分析市场趋势", "skills": [SkillType.DATA_ANALYSIS]},
                    {"id": "chart_generation", "description": "生成分析图表", "skills": [SkillType.DATA_ANALYSIS, SkillType.IMAGE_GENERATION]},
                    {"id": "report_writing", "description": "撰写分析报告", "skills": [SkillType.DOCUMENT_CREATION]},
                    {"id": "presentation_prep", "description": "准备演示材料", "skills": [SkillType.DOCUMENT_CREATION]}
                ],
                "dependencies": [
                    ("data_analysis", "data_collection"),
                    ("chart_generation", "data_analysis"),
                    ("report_writing", "chart_generation"),
                    ("presentation_prep", "report_writing")
                ]
            },
            "product_landing_page": {
                "name": "产品落地页",
                "description": "产品推广落地页开发",
                "subtasks": [
                    {"id": "product_research", "description": "产品调研分析", "skills": [SkillType.SEARCH, SkillType.DATA_ANALYSIS]},
                    {"id": "content_creation", "description": "创建页面内容", "skills": [SkillType.DOCUMENT_CREATION]},
                    {"id": "image_generation", "description": "生成产品图片", "skills": [SkillType.IMAGE_GENERATION]},
                    {"id": "web_development", "description": "开发网页界面", "skills": [SkillType.WEB_DEVELOPMENT]},
                    {"id": "testing", "description": "测试和优化", "skills": [SkillType.AUTOMATION]}
                ],
                "dependencies": [
                    ("content_creation", "product_research"),
                    ("image_generation", "product_research"),
                    ("web_development", ["content_creation", "image_generation"]),
                    ("testing", "web_development")
                ]
            }
        }
    
    def analyze_requirements(self, user_request: str) -> Dict[str, Any]:
        """分析用户需求，识别任务类型和复杂度"""
        logger.info(f"分析用户需求: {user_request}")
        
        # 关键词匹配和需求分析
        analysis_result = {
            "complexity": "medium",
            "estimated_skill_count": 0,
            "detected_skills": [],
            "task_type": "custom"
        }
        
        # 检测关键词
        keywords = {
            SkillType.DATA_ANALYSIS: ["分析", "数据", "统计", "趋势", "报表", "图表"],
            SkillType.DOCUMENT_CREATION: ["报告", "文档", "PPT", "幻灯片", "撰写", "编写"],
            SkillType.IMAGE_GENERATION: ["图片", "图像", "生成", "设计", "视觉", "海报"],
            SkillType.WEB_DEVELOPMENT: ["网页", "网站", "界面", "应用", "仪表板", "大屏"],
            SkillType.SEARCH: ["搜索", "查找", "调研", "收集", "信息"],
            SkillType.AUTOMATION: ["自动化", "批量", "重复", "流程", "执行"]
        }
        
        for skill_type, kw_list in keywords.items():
            for keyword in kw_list:
                if keyword in user_request:
                    if skill_type not in analysis_result["detected_skills"]:
                        analysis_result["detected_skills"].append(skill_type)
        
        analysis_result["estimated_skill_count"] = len(analysis_result["detected_skills"])
        
        # 根据技能数量判断复杂度
        if analysis_result["estimated_skill_count"] <= 2:
            analysis_result["complexity"] = "simple"
        elif analysis_result["estimated_skill_count"] <= 4:
            analysis_result["complexity"] = "medium"
        else:
            analysis_result["complexity"] = "complex"
        
        # 尝试匹配现有模板
        for template_id, template in self.task_templates.items():
            template_skills = set()
            for subtask in template["subtasks"]:
                for skill in subtask["skills"]:
                    template_skills.add(skill)
            
            if set(analysis_result["detected_skills"]).issubset(template_skills):
                analysis_result["task_type"] = template_id
                break
        
        return analysis_result
    
    def decompose_task(self, user_request: str, analysis_result: Dict[str, Any]) -> List[Subtask]:
        """将复杂任务分解为子任务"""
        logger.info(f"分解任务: {user_request}")
        
        subtasks = []
        
        if analysis_result["task_type"] in self.task_templates:
            # 使用模板分解
            template = self.task_templates[analysis_result["task_type"]]
            for i, subtask_def in enumerate(template["subtasks"]):
                subtask = Subtask(
                    id=subtask_def["id"],
                    description=subtask_def["description"],
                    required_skills=subtask_def["skills"],
                    dependencies=[],
                    estimated_time=120,  # 默认2分钟
                    max_retries=3
                )
                subtasks.append(subtask)
        else:
            # 智能分解
            # 根据检测到的技能创建子任务
            for i, skill_type in enumerate(analysis_result["detected_skills"]):
                skill_name = skill_type.value
                subtask = Subtask(
                    id=f"subtask_{i+1}",
                    description=f"执行{skill_name}相关任务",
                    required_skills=[skill_type],
                    dependencies=[],
                    estimated_time=180,
                    max_retries=3
                )
                subtasks.append(subtask)
        
        return subtasks
    
    def match_skills(self, subtasks: List[Subtask]) -> Dict[str, str]:
        """为子任务匹配合适的技能"""
        logger.info("开始技能匹配")
        
        skill_mapping = {}
        
        for subtask in subtasks:
            best_skill = None
            best_score = 0
            
            for skill_name, skill_profile in self.skill_profiles.items():
                # 检查技能类型匹配
                if skill_profile.skill_type not in subtask.required_skills:
                    continue
                
                # 计算匹配分数
                score = self._calculate_skill_match_score(skill_profile, subtask)
                
                if score > best_score:
                    best_score = score
                    best_skill = skill_name
            
            if best_skill:
                skill_mapping[subtask.id] = best_skill
                subtask.assigned_skill = best_skill
                logger.info(f"子任务 {subtask.id}: {subtask.description} -> 技能 {best_skill}")
            else:
                logger.warning(f"未找到适合子任务 {subtask.id} 的技能")
        
        return skill_mapping
    
    def _calculate_skill_match_score(self, skill_profile: SkillProfile, subtask: Subtask) -> float:
        """计算技能匹配分数"""
        score = 0.0
        
        # 基础匹配分数
        if skill_profile.skill_type in subtask.required_skills:
            score += 0.5
        
        # 成功率权重
        score += skill_profile.success_rate * 0.3
        
        # 执行时间权重（越短越好）
        avg_time = sum(skill_profile.execution_time_estimate.values()) / len(skill_profile.execution_time_estimate)
        time_score = max(0, 1 - avg_time / 1800)  # 30分钟内为满分
        score += time_score * 0.2
        
        return score
    
    def create_execution_plan(self, subtasks: List[Subtask], skill_mapping: Dict[str, str]) -> ExecutionPlan:
        """创建执行计划，包括依赖分析和并行优化"""
        logger.info("创建执行计划")
        
        # 构建依赖图
        dependency_graph = {}
        for subtask in subtasks:
            dependency_graph[subtask.id] = subtask.dependencies
        
        # 拓扑排序确定执行顺序
        execution_order = self._topological_sort(dependency_graph)
        
        # 识别可并行执行的任务组
        parallel_groups = self._identify_parallel_groups(dependency_graph, execution_order)
        
        # 计算预估总时间
        estimated_total_time = sum(subtask.estimated_time for subtask in subtasks)
        
        # 创建执行计划
        plan = ExecutionPlan(
            task_id=f"task_{int(time.time())}",
            subtasks=subtasks,
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            estimated_total_time=estimated_total_time,
            skill_mapping=skill_mapping
        )
        
        logger.info(f"执行计划创建完成: {plan.task_id}")
        logger.info(f"执行顺序: {execution_order}")
        logger.info(f"并行组: {parallel_groups}")
        logger.info(f"预估总时间: {estimated_total_time}秒")
        
        return plan
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """拓扑排序"""
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
    
    def _identify_parallel_groups(self, graph: Dict[str, List[str]], execution_order: List[str]) -> List[List[str]]:
        """识别可并行执行的任务组"""
        parallel_groups = []
        current_group = []
        
        for task_id in execution_order:
            # 检查任务是否有依赖
            dependencies = graph.get(task_id, [])
            
            if not dependencies:
                # 没有依赖的任务可以并行执行
                current_group.append(task_id)
            else:
                # 有依赖的任务需要单独处理
                if current_group:
                    parallel_groups.append(current_group.copy())
                    current_group = []
                parallel_groups.append([task_id])
        
        if current_group:
            parallel_groups.append(current_group)
        
        return parallel_groups
    
    def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """执行编排计划"""
        logger.info(f"开始执行计划: {plan.task_id}")
        
        execution_results = {
            "plan_id": plan.task_id,
            "start_time": time.time(),
            "subtask_results": {},
            "overall_status": "completed",
            "total_time": 0,
            "errors": []
        }
        
        # 按顺序执行任务
        for task_group in plan.parallel_groups:
            group_results = []
            
            # 理论上可以并行执行，这里简化处理为顺序执行
            for task_id in task_group:
                subtask = next((st for st in plan.subtasks if st.id == task_id), None)
                if not subtask:
                    continue
                
                result = self._execute_subtask(subtask, plan)
                group_results.append(result)
                
                # 记录结果
                execution_results["subtask_results"][task_id] = {
                    "status": subtask.status.value,
                    "result": subtask.result,
                    "error": subtask.error,
                    "retries": subtask.current_retries
                }
                
                # 检查错误
                if subtask.status == TaskStatus.FAILED:
                    execution_results["errors"].append(f"子任务 {task_id} 执行失败: {subtask.error}")
                    execution_results["overall_status"] = "partial_failure"
            
            # 等待组内所有任务完成（简化处理）
            time.sleep(1)
        
        execution_results["end_time"] = time.time()
        execution_results["total_time"] = execution_results["end_time"] - execution_results["start_time"]
        
        # 如果所有任务都失败，标记为完全失败
        if all(result["status"] == "failed" for result in execution_results["subtask_results"].values()):
            execution_results["overall_status"] = "failed"
        
        logger.info(f"计划执行完成: 状态={execution_results['overall_status']}, 耗时={execution_results['total_time']:.2f}秒")
        
        return execution_results
    
    def _execute_subtask(self, subtask: Subtask, plan: ExecutionPlan) -> Dict[str, Any]:
        """执行单个子任务（模拟执行）"""
        logger.info(f"执行子任务: {subtask.id} - {subtask.description}")
        
        subtask.status = TaskStatus.RUNNING
        
        try:
            # 模拟执行过程
            time.sleep(0.5)  # 模拟执行时间
            
            # 模拟成功或失败
            import random
            success_probability = 0.9  # 90%成功率
            
            if random.random() < success_probability:
                subtask.status = TaskStatus.COMPLETED
                subtask.result = {
                    "output": f"子任务 {subtask.id} 执行成功",
                    "generated_files": [f"output_{subtask.id}.txt"],
                    "execution_time": random.randint(10, 60)
                }
                logger.info(f"子任务 {subtask.id} 执行成功")
            else:
                subtask.status = TaskStatus.FAILED
                subtask.error = "模拟执行失败"
                logger.error(f"子任务 {subtask.id} 执行失败: {subtask.error}")
                
                # 重试逻辑
                if subtask.current_retries < subtask.max_retries:
                    subtask.current_retries += 1
                    subtask.status = TaskStatus.RETRYING
                    logger.info(f"准备重试子任务 {subtask.id} (第{subtask.current_retries}次)")
                    return self._execute_subtask(subtask, plan)
            
        except Exception as e:
            subtask.status = TaskStatus.FAILED
            subtask.error = str(e)
            logger.error(f"子任务 {subtask.id} 执行异常: {e}")
        
        return {
            "task_id": subtask.id,
            "status": subtask.status.value,
            "result": subtask.result,
            "error": subtask.error
        }
    
    def save_template(self, plan: ExecutionPlan, execution_results: Dict[str, Any], template_name: str):
        """保存执行成功的流程为模板"""
        logger.info(f"保存模板: {template_name}")
        
        template = {
            "name": template_name,
            "description": f"基于任务 {plan.task_id} 生成的模板",
            "created_at": time.time(),
            "execution_stats": {
                "total_time": execution_results["total_time"],
                "success_rate": sum(1 for r in execution_results["subtask_results"].values() if r["status"] == "completed") / len(execution_results["subtask_results"]),
                "subtask_count": len(plan.subtasks)
            },
            "subtasks": [
                {
                    "id": st.id,
                    "description": st.description,
                    "assigned_skill": st.assigned_skill,
                    "estimated_time": st.estimated_time
                }
                for st in plan.subtasks
            ],
            "execution_order": plan.execution_order,
            "parallel_groups": plan.parallel_groups,
            "skill_mapping": plan.skill_mapping
        }
        
        # 保存模板到文件
        template_file = f"/tmp/template_{template_name}_{int(time.time())}.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        logger.info(f"模板已保存到: {template_file}")
        return template_file

def main():
    """主函数，演示编排器使用"""
    orchestrator = MultiSkillOrchestrator()
    
    # 示例用户请求
    user_request = "帮我分析销售数据，生成可视化图表，并创建一份市场分析报告"
    
    print(f"用户请求: {user_request}")
    print("=" * 50)
    
    # 1. 分析需求
    analysis_result = orchestrator.analyze_requirements(user_request)
    print(f"需求分析结果: {json.dumps(analysis_result, ensure_ascii=False, indent=2)}")
    
    # 2. 分解任务
    subtasks = orchestrator.decompose_task(user_request, analysis_result)
    print(f"\n分解出的子任务 ({len(subtasks)}个):")
    for st in subtasks:
        print(f"  - {st.id}: {st.description} (需要技能: {[s.value for s in st.required_skills]})")
    
    # 3. 技能匹配
    skill_mapping = orchestrator.match_skills(subtasks)
    print(f"\n技能匹配结果: {skill_mapping}")
    
    # 4. 创建执行计划
    plan = orchestrator.create_execution_plan(subtasks, skill_mapping)
    
    # 5. 执行计划
    results = orchestrator.execute_plan(plan)
    
    print(f"\n执行结果:")
    print(f"  计划ID: {results['plan_id']}")
    print(f"  总体状态: {results['overall_status']}")
    print(f"  总耗时: {results['total_time']:.2f}秒")
    print(f"  错误数: {len(results['errors'])}")
    
    # 6. 保存模板（如果执行成功）
    if results['overall_status'] == 'completed':
        template_file = orchestrator.save_template(plan, results, "market_analysis_template")
        print(f"\n模板已保存: {template_file}")

if __name__ == "__main__":
    main()