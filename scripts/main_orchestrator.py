#!/usr/bin/env python3
"""
多技能智能编排系统主入口
整合所有组件，提供统一的对外接口
"""

import sys
import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import asdict
import argparse

# 添加当前目录到路径，以便导入本地模块
sys.path.append(os.path.dirname(__file__))

from orchestrator_engine import MultiSkillOrchestrator, Subtask, ExecutionPlan, TaskStatus
from template_library import TemplateLibrary, ExecutionPlanGenerator, TaskTemplate
from error_handling import ErrorHandler, ErrorRecord, ProcessCorrector

logger = logging.getLogger(__name__)

class MultiSkillOrchestrationSystem:
    """多技能智能编排系统"""
    
    def __init__(self, config_file: str = None):
        """初始化编排系统"""
        
        logger.info("初始化多技能智能编排系统")
        
        # 加载配置
        self.config = self._load_config(config_file)
        
        # 初始化各个组件
        self.orchestrator = MultiSkillOrchestrator()
        self.template_library = TemplateLibrary()
        self.execution_generator = ExecutionPlanGenerator(self.template_library)
        self.error_handler = ErrorHandler()
        self.process_corrector = ProcessCorrector(self.error_handler)
        
        # 执行统计
        self.execution_stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0,
            "total_execution_time": 0,
            "template_usage": {},
            "skill_usage": {}
        }
        
        logger.info("编排系统初始化完成")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "max_concurrent_tasks": 5,
            "default_retry_count": 3,
            "timeout_multiplier": 2.0,
            "enable_parallel_execution": True,
            "enable_auto_correction": True,
            "enable_template_suggestion": True,
            "log_level": "INFO",
            "persist_execution_history": True,
            "max_history_size": 1000
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # 合并配置
                default_config.update(user_config)
                logger.info(f"从 {config_file} 加载用户配置")
                
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        
        return default_config
    
    def process_user_request(self, user_request: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理用户请求，返回完整执行结果"""
        
        start_time = time.time()
        logger.info(f"开始处理用户请求: {user_request}")
        
        options = options or {}
        
        # 1. 需求分析
        analysis_result = self.orchestrator.analyze_requirements(user_request)
        logger.info(f"需求分析完成: {analysis_result}")
        
        # 2. 寻找匹配模板
        matched_templates = []
        if self.config["enable_template_suggestion"]:
            matched_templates = self.template_library.find_matching_templates(user_request)
            logger.info(f"找到 {len(matched_templates)} 个匹配模板")
        
        # 3. 生成执行计划
        execution_plan = None
        
        if matched_templates and options.get("use_template", True):
            # 使用匹配的模板
            selected_template = matched_templates[0]
            customization = options.get("customization", {})
            execution_plan = self.execution_generator.generate_from_template(
                selected_template, customization
            )
            
            # 更新模板使用统计
            self.template_library.update_template_stats(selected_template.id, False)
            
        else:
            # 智能生成自定义计划
            detected_skills = analysis_result.get("detected_skills", [])
            skill_names = [s.value for s in detected_skills]
            execution_plan = self.execution_generator.generate_custom_plan(
                user_request, skill_names
            )
        
        if not execution_plan:
            error_msg = "无法生成执行计划"
            logger.error(error_msg)
            return self._create_error_response(user_request, error_msg)
        
        logger.info(f"执行计划生成完成: {execution_plan.get('template_name')}")
        
        # 4. 执行计划
        execution_results = self.orchestrator.execute_plan(
            ExecutionPlan(
                task_id=execution_plan.get("template_id", "custom"),
                subtasks=[],  # 会被orchestrator填充
                execution_order=execution_plan.get("execution_order", []),
                parallel_groups=execution_plan.get("parallel_groups", []),
                estimated_total_time=execution_plan.get("estimated_time", {}).get("max", 300),
                skill_mapping={}
            )
        )
        
        # 5. 错误处理（如果需要）
        if execution_results["overall_status"] != "completed" and self.config["enable_auto_correction"]:
            corrected_results = self._handle_execution_errors(
                user_request, execution_plan, execution_results, options
            )
            
            # 使用纠正后的结果
            if corrected_results.get("success"):
                execution_results = corrected_results["execution_results"]
                execution_plan = corrected_results.get("execution_plan", execution_plan)
        
        # 6. 流程分析
        process_analysis = self.process_corrector.analyze_process_flow(
            execution_plan, execution_results
        )
        
        # 7. 保存成功模板（如果执行成功）
        saved_template = None
        if execution_results["overall_status"] == "completed" and options.get("save_as_template", True):
            template_name = f"user_template_{int(time.time())}"
            saved_template = self.template_library.create_custom_template(
                user_request, execution_plan, execution_results
            )
            logger.info(f"已保存为模板: {saved_template.id}")
        
        # 8. 更新统计信息
        self._update_execution_stats(execution_plan, execution_results)
        
        # 9. 生成最终响应
        end_time = time.time()
        total_time = end_time - start_time
        
        response = self._create_final_response(
            user_request=user_request,
            analysis_result=analysis_result,
            execution_plan=execution_plan,
            execution_results=execution_results,
            process_analysis=process_analysis,
            saved_template=saved_template,
            total_time=total_time,
            options=options
        )
        
        logger.info(f"请求处理完成，总耗时: {total_time:.2f}秒")
        
        return response
    
    def _handle_execution_errors(self, user_request: str, execution_plan: Dict[str, Any],
                               execution_results: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行错误，尝试纠正"""
        
        logger.info("开始处理执行错误")
        
        # 分析流程问题
        process_analysis = self.process_corrector.analyze_process_flow(execution_plan, execution_results)
        
        # 如果流程健康度差，尝试纠正
        if process_analysis["process_health"] in ["fair", "poor"]:
            logger.info(f"流程健康度较差 ({process_analysis['process_health']})，尝试纠正")
            
            # 生成纠正后的计划
            corrected_plan = self.process_corrector.correct_process_flow(execution_plan, process_analysis)
            
            # 执行纠正后的计划
            corrected_execution_plan = ExecutionPlan(
                task_id=corrected_plan.get("template_id", "corrected"),
                subtasks=[],  # 会被orchestrator填充
                execution_order=corrected_plan.get("execution_order", []),
                parallel_groups=corrected_plan.get("parallel_groups", []),
                estimated_total_time=corrected_plan.get("estimated_time", {}).get("max", 300),
                skill_mapping={}
            )
            
            corrected_results = self.orchestrator.execute_plan(corrected_execution_plan)
            
            return {
                "success": corrected_results["overall_status"] == "completed",
                "execution_plan": corrected_plan,
                "execution_results": corrected_results,
                "correction_applied": True
            }
        
        return {"success": False}
    
    def _update_execution_stats(self, execution_plan: Dict[str, Any], execution_results: Dict[str, Any]):
        """更新执行统计信息"""
        
        self.execution_stats["total_tasks"] += 1
        
        if execution_results["overall_status"] == "completed":
            self.execution_stats["successful_tasks"] += 1
        else:
            self.execution_stats["failed_tasks"] += 1
        
        # 更新执行时间统计
        exec_time = execution_results.get("total_time", 0)
        self.execution_stats["total_execution_time"] += exec_time
        
        total_tasks = self.execution_stats["total_tasks"]
        if total_tasks > 0:
            self.execution_stats["average_execution_time"] = (
                self.execution_stats["total_execution_time"] / total_tasks
            )
        
        # 更新模板使用统计
        template_id = execution_plan.get("template_id")
        if template_id:
            self.execution_stats["template_usage"][template_id] = \
                self.execution_stats["template_usage"].get(template_id, 0) + 1
        
        # 更新技能使用统计（简化处理）
        subtask_results = execution_results.get("subtask_results", {})
        for subtask_id, result in subtask_results.items():
            skill_name = result.get("skill", "unknown")
            self.execution_stats["skill_usage"][skill_name] = \
                self.execution_stats["skill_usage"].get(skill_name, 0) + 1
    
    def _create_error_response(self, user_request: str, error_message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "user_request": user_request,
            "error": error_message,
            "timestamp": time.time(),
            "components": {
                "analysis_completed": False,
                "execution_completed": False,
                "correction_applied": False
            }
        }
    
    def _create_final_response(self, **kwargs) -> Dict[str, Any]:
        """创建最终响应"""
        
        response = {
            "success": kwargs["execution_results"]["overall_status"] == "completed",
            "user_request": kwargs["user_request"],
            "timestamp": time.time(),
            "total_processing_time": kwargs["total_time"],
            "analysis_summary": {
                "complexity": kwargs["analysis_result"].get("complexity"),
                "detected_skills": [s.value for s in kwargs["analysis_result"].get("detected_skills", [])],
                "task_type": kwargs["analysis_result"].get("task_type")
            },
            "execution_summary": {
                "plan_id": kwargs["execution_plan"].get("template_id"),
                "plan_name": kwargs["execution_plan"].get("template_name"),
                "subtask_count": len(kwargs["execution_plan"].get("subtasks", [])),
                "completed_subtasks": sum(1 for r in kwargs["execution_results"].get("subtask_results", {}).values() 
                                         if r.get("status") == "completed"),
                "overall_status": kwargs["execution_results"]["overall_status"],
                "execution_time": kwargs["execution_results"].get("total_time", 0)
            },
            "process_health": {
                "score": kwargs["process_analysis"].get("efficiency_score", 0),
                "health_status": kwargs["process_analysis"].get("process_health", "unknown"),
                "bottleneck_count": len(kwargs["process_analysis"].get("bottlenecks", [])),
                "improvement_suggestions": kwargs["process_analysis"].get("improvement_suggestions", [])
            },
            "template_info": None,
            "components": {
                "analysis_completed": True,
                "execution_completed": True,
                "correction_applied": kwargs.get("options", {}).get("correction_applied", False)
            }
        }
        
        # 添加保存的模板信息
        if kwargs.get("saved_template"):
            response["template_info"] = {
                "template_id": kwargs["saved_template"].id,
                "template_name": kwargs["saved_template"].name,
                "category": kwargs["saved_template"].category.value
            }
        
        return response
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        
        error_stats = self.error_handler.get_error_statistics()
        
        return {
            "system": {
                "components_initialized": True,
                "config_loaded": bool(self.config),
                "uptime": self._get_uptime()  # 简化处理
            },
            "statistics": self.execution_stats,
            "error_statistics": error_stats,
            "template_library": {
                "total_templates": len(self.template_library.templates),
                "categories": list(set(t.category.value for t in self.template_library.templates.values()))
            }
        }
    
    def _get_uptime(self) -> int:
        """获取系统运行时间（简化处理）"""
        # 实际实现应该记录启动时间
        return int(time.time() - getattr(self, '_start_time', time.time()))
    
    def export_analysis_report(self, execution_id: str, output_format: str = "json") -> Optional[str]:
        """导出分析报告"""
        # 实际实现应该从数据库或文件中读取历史记录
        logger.info(f"导出分析报告: {execution_id}, 格式: {output_format}")
        return None

def main_cli():
    """命令行接口"""
    
    parser = argparse.ArgumentParser(description="多技能智能编排系统")
    parser.add_argument("request", nargs="?", help="用户请求文本")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    parser.add_argument("--status", action="store_true", help="显示系统状态")
    parser.add_argument("--list-templates", action="store_true", help="列出所有模板")
    parser.add_argument("--export-templates", help="导出模板到指定目录")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 初始化系统
    system = MultiSkillOrchestrationSystem(args.config)
    
    if args.status:
        # 显示系统状态
        status = system.get_system_status()
        
        if args.format == "json":
            output = json.dumps(status, ensure_ascii=False, indent=2)
        else:
            output = self._format_status_text(status)
        
        print(output)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
        
        return
    
    if args.list_templates:
        # 列出模板
        templates = system.template_library.templates
        
        template_list = []
        for template_id, template in templates.items():
            template_list.append({
                "id": template_id,
                "name": template.name,
                "category": template.category.value,
                "complexity": template.complexity,
                "usage_count": template.usage_count,
                "success_rate": f"{template.success_rate:.1%}"
            })
        
        if args.format == "json":
            output = json.dumps(template_list, ensure_ascii=False, indent=2)
        else:
            output = self._format_template_list_text(template_list)
        
        print(output)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
        
        return
    
    if args.export_templates:
        # 导出模板
        system.template_library.export_templates(args.export_templates)
        print(f"模板已导出到: {args.export_templates}")
        return
    
    if not args.request:
        parser.print_help()
        return
    
    # 处理用户请求
    print(f"处理请求: {args.request}")
    print("=" * 50)
    
    result = system.process_user_request(args.request)
    
    if args.format == "json":
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = self._format_result_text(result)
    
    print(output)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
    
    # 显示总结
    if result.get("success"):
        print(f"\n✅ 任务执行成功!")
    else:
        print(f"\n❌ 任务执行失败!")
    
    exec_summary = result.get("execution_summary", {})
    print(f"  执行计划: {exec_summary.get('plan_name', '未知')}")
    print(f"  完成状态: {exec_summary.get('overall_status', '未知')}")
    print(f"  子任务完成: {exec_summary.get('completed_subtasks', 0)}/{exec_summary.get('subtask_count', 0)}")
    print(f"  执行时间: {exec_summary.get('execution_time', 0):.1f}秒")

def _format_status_text(status: Dict[str, Any]) -> str:
    """格式化状态文本输出"""
    
    lines = []
    lines.append("=" * 60)
    lines.append("多技能智能编排系统 - 状态报告")
    lines.append("=" * 60)
    lines.append("")
    
    # 系统信息
    lines.append("📊 系统信息:")
    sys_info = status.get("system", {})
    lines.append(f"   组件状态: {'正常' if sys_info.get('components_initialized') else '异常'}")
    lines.append(f"   配置加载: {'成功' if sys_info.get('config_loaded') else '失败'}")
    lines.append(f"   运行时间: {sys_info.get('uptime', 0)} 秒")
    lines.append("")
    
    # 执行统计
    lines.append("📈 执行统计:")
    stats = status.get("statistics", {})
    lines.append(f"   总任务数: {stats.get('total_tasks', 0)}")
    lines.append(f"   成功任务: {stats.get('successful_tasks', 0)}")
    lines.append(f"   失败任务: {stats.get('failed_tasks', 0)}")
    lines.append(f"   成功率: {stats.get('successful_tasks', 0)/stats.get('total_tasks', 1)*100:.1f}%")
    lines.append(f"   平均执行时间: {stats.get('average_execution_time', 0):.1f} 秒")
    lines.append("")
    
    # 错误统计
    lines.append("⚠️  错误统计:")
    error_stats = status.get("error_statistics", {})
    lines.append(f"   总错误数: {error_stats.get('total_errors', 0)}")
    lines.append(f"   解决率: {error_stats.get('resolution_rate', 0)*100:.1f}%")
    
    if error_stats.get('most_common_error'):
        lines.append(f"   最常见错误: {error_stats['most_common_error']}")
    
    lines.append(f"   最近24小时错误: {error_stats.get('recent_errors_24h', 0)}")
    lines.append("")
    
    # 模板库
    lines.append("📚 模板库:")
    template_info = status.get("template_library", {})
    lines.append(f"   模板总数: {template_info.get('total_templates', 0)}")
    
    categories = template_info.get('categories', [])
    if categories:
        lines.append(f"   可用类别: {', '.join(categories)}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)

def _format_template_list_text(templates: List[Dict[str, Any]]) -> str:
    """格式化模板列表文本输出"""
    
    lines = []
    lines.append("=" * 60)
    lines.append("模板列表")
    lines.append("=" * 60)
    lines.append("")
    
    for i, template in enumerate(templates, 1):
        lines.append(f"{i}. {template['name']} (ID: {template['id']})")
        lines.append(f"   类别: {template['category']}")
        lines.append(f"   复杂度: {template['complexity']}")
        lines.append(f"   使用次数: {template['usage_count']}")
        lines.append(f"   成功率: {template['success_rate']}")
        lines.append("")
    
    lines.append(f"共 {len(templates)} 个模板")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def _format_result_text(result: Dict[str, Any]) -> str:
    """格式化结果文本输出"""
    
    lines = []
    lines.append("=" * 60)
    lines.append("任务执行结果")
    lines.append("=" * 60)
    lines.append("")
    
    lines.append(f"📝 用户请求: {result.get('user_request', '未知')}")
    lines.append("")
    
    # 分析摘要
    analysis = result.get("analysis_summary", {})
    lines.append("🔍 需求分析:")
    lines.append(f"   复杂度: {analysis.get('complexity', '未知')}")
    lines.append(f"   检测到的技能: {', '.join(analysis.get('detected_skills', []))}")
    lines.append(f"   任务类型: {analysis.get('task_type', '自定义')}")
    lines.append("")
    
    # 执行摘要
    exec_summary = result.get("execution_summary", {})
    lines.append("🚀 执行结果:")
    lines.append(f"   计划名称: {exec_summary.get('plan_name', '未知')}")
    lines.append(f"   总体状态: {exec_summary.get('overall_status', '未知')}")
    lines.append(f"   子任务: {exec_summary.get('completed_subtasks', 0)}/{exec_summary.get('subtask_count', 0)} 完成")
    lines.append(f"   执行时间: {exec_summary.get('execution_time', 0):.1f} 秒")
    lines.append("")
    
    # 流程健康度
    health = result.get("process_health", {})
    lines.append("🏥 流程健康度:")
    lines.append(f"   评分: {health.get('score', 0):.2f}/1.0")
    lines.append(f"   状态: {health.get('health_status', '未知')}")
    lines.append(f"   瓶颈数量: {health.get('bottleneck_count', 0)}")
    
    suggestions = health.get("improvement_suggestions", [])
    if suggestions:
        lines.append("   改进建议:")
        for suggestion in suggestions[:3]:  # 最多显示3条
            lines.append(f"     - {suggestion}")
    
    lines.append("")
    
    # 模板信息
    template_info = result.get("template_info")
    if template_info:
        lines.append("💾 模板保存:")
        lines.append(f"   模板ID: {template_info.get('template_id')}")
        lines.append(f"   模板名称: {template_info.get('template_name')}")
        lines.append(f"   类别: {template_info.get('category')}")
        lines.append("")
    
    lines.append(f"⏱️  总处理时间: {result.get('total_processing_time', 0):.1f} 秒")
    lines.append("=" * 60)
    
    return "\n".join(lines)

if __name__ == "__main__":
    main_cli()