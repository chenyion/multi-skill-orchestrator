#!/usr/bin/env python3
"""
多技能智能编排系统测试用例
"""

import sys
import os
import json
import time
import logging
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

from orchestrator_engine import MultiSkillOrchestrator, Subtask, ExecutionPlan, TaskStatus, SkillType
from template_library import TemplateLibrary, TaskTemplate, TemplateCategory
from error_handling import ErrorHandler, ErrorRecord, ErrorType, ErrorSeverity, ProcessCorrector
from main_orchestrator import MultiSkillOrchestrationSystem

logging.basicConfig(level=logging.WARNING)  # 测试时减少日志输出

class TestMultiSkillOrchestrator(unittest.TestCase):
    """测试编排引擎"""
    
    def setUp(self):
        self.orchestrator = MultiSkillOrchestrator()
    
    def test_analyze_requirements(self):
        """测试需求分析"""
        # 测试数据分析需求
        request = "帮我分析销售数据，生成趋势图表"
        result = self.orchestrator.analyze_requirements(request)
        
        self.assertIn("complexity", result)
        self.assertIn("detected_skills", result)
        self.assertIn(SkillType.DATA_ANALYSIS, result["detected_skills"])
        
        # 测试文档创建需求
        request = "撰写一份市场调研报告"
        result = self.orchestrator.analyze_requirements(request)
        
        self.assertIn(SkillType.DOCUMENT_CREATION, result["detected_skills"])
    
    def test_decompose_task(self):
        """测试任务分解"""
        request = "数据分析报告"
        analysis = {"detected_skills": [SkillType.DATA_ANALYSIS, SkillType.DOCUMENT_CREATION]}
        
        subtasks = self.orchestrator.decompose_task(request, analysis)
        
        self.assertGreater(len(subtasks), 0)
        self.assertIsInstance(subtasks[0], Subtask)
        
        # 检查子任务属性
        for subtask in subtasks:
            self.assertIsNotNone(subtask.id)
            self.assertIsNotNone(subtask.description)
            self.assertIsNotNone(subtask.required_skills)
    
    def test_match_skills(self):
        """测试技能匹配"""
        subtasks = [
            Subtask(
                id="task1",
                description="数据分析",
                required_skills=[SkillType.DATA_ANALYSIS],
                dependencies=[],
                estimated_time=60
            ),
            Subtask(
                id="task2",
                description="文档撰写",
                required_skills=[SkillType.DOCUMENT_CREATION],
                dependencies=[],
                estimated_time=120
            )
        ]
        
        skill_mapping = self.orchestrator.match_skills(subtasks)
        
        self.assertIn("task1", skill_mapping)
        self.assertIn("task2", skill_mapping)
        self.assertIn(skill_mapping["task1"], self.orchestrator.skill_profiles)
        self.assertIn(skill_mapping["task2"], self.orchestrator.skill_profiles)
    
    def test_create_execution_plan(self):
        """测试执行计划创建"""
        subtasks = [
            Subtask(
                id="task1",
                description="任务1",
                required_skills=[SkillType.DATA_ANALYSIS],
                dependencies=[],
                estimated_time=60
            ),
            Subtask(
                id="task2",
                description="任务2",
                required_skills=[SkillType.DOCUMENT_CREATION],
                dependencies=["task1"],
                estimated_time=120
            )
        ]
        
        skill_mapping = {"task1": "data_analysis", "task2": "document_creation"}
        
        plan = self.orchestrator.create_execution_plan(subtasks, skill_mapping)
        
        self.assertIsInstance(plan, ExecutionPlan)
        self.assertIn("task1", plan.execution_order)
        self.assertIn("task2", plan.execution_order)
        self.assertGreater(plan.estimated_total_time, 0)
    
    @patch('time.sleep')
    def test_execute_plan(self, mock_sleep):
        """测试执行计划（模拟）"""
        subtasks = [
            Subtask(
                id="task1",
                description="测试任务",
                required_skills=[SkillType.DATA_ANALYSIS],
                dependencies=[],
                estimated_time=60,
                max_retries=3
            )
        ]
        
        plan = ExecutionPlan(
            task_id="test_plan",
            subtasks=subtasks,
            execution_order=["task1"],
            parallel_groups=[["task1"]],
            estimated_total_time=60,
            skill_mapping={"task1": "data_analysis"}
        )
        
        results = self.orchestrator.execute_plan(plan)
        
        self.assertIn("plan_id", results)
        self.assertIn("overall_status", results)
        self.assertIn("subtask_results", results)
        self.assertIn("task1", results["subtask_results"])

class TestTemplateLibrary(unittest.TestCase):
    """测试模板库"""
    
    def setUp(self):
        self.library = TemplateLibrary()
    
    def test_find_matching_templates(self):
        """测试模板查找"""
        request = "市场分析报告"
        
        templates = self.library.find_matching_templates(request)
        
        self.assertGreater(len(templates), 0)
        self.assertIsInstance(templates[0], TaskTemplate)
        
        # 检查找到的模板是否包含关键词
        found_market_template = False
        for template in templates:
            if "市场" in template.name or "市场" in template.description:
                found_market_template = True
                break
        
        self.assertTrue(found_market_template, "应该找到市场相关的模板")
    
    def test_get_template(self):
        """测试获取模板"""
        # 获取已知存在的模板
        template = self.library.get_template("market_analysis_full")
        
        self.assertIsNotNone(template)
        self.assertEqual(template.id, "market_analysis_full")
        self.assertEqual(template.category, TemplateCategory.DATA_ANALYSIS)
    
    def test_create_custom_template(self):
        """测试创建自定义模板"""
        user_request = "测试自定义模板创建"
        execution_plan = {
            "subtasks": [
                {"id": "task1", "description": "测试任务1", "required_skills": ["test"], "estimated_time": 60},
                {"id": "task2", "description": "测试任务2", "required_skills": ["test"], "estimated_time": 90}
            ]
        }
        execution_results = {
            "total_time": 150,
            "subtask_results": {
                "task1": {"status": "completed"},
                "task2": {"status": "completed"}
            }
        }
        
        template = self.library.create_custom_template(
            user_request, execution_plan, execution_results
        )
        
        self.assertIsNotNone(template)
        self.assertIn("custom_", template.id)
        self.assertEqual(template.category, TemplateCategory.CUSTOM)
        self.assertIn("测试自定义模板创建", template.description)
    
    def test_update_template_stats(self):
        """测试更新模板统计"""
        template_id = "market_analysis_full"
        
        # 初始使用次数
        initial_template = self.library.get_template(template_id)
        initial_count = initial_template.usage_count
        
        # 更新统计（成功）
        self.library.update_template_stats(template_id, True)
        
        # 检查更新后的统计
        updated_template = self.library.get_template(template_id)
        self.assertEqual(updated_template.usage_count, initial_count + 1)
        self.assertGreater(updated_template.success_rate, 0)

class TestErrorHandler(unittest.TestCase):
    """测试错误处理器"""
    
    def setUp(self):
        self.handler = ErrorHandler()
    
    def test_detect_error_type(self):
        """测试错误类型检测"""
        # 测试超时错误
        error_msg = "请求超时: 连接服务器失败"
        error_type, severity = self.handler.detect_error_type(error_msg)
        
        self.assertEqual(error_type, ErrorType.SKILL_TIMEOUT)
        self.assertEqual(severity, ErrorSeverity.MEDIUM)
        
        # 测试网络错误
        error_msg = "网络连接失败"
        error_type, severity = self.handler.detect_error_type(error_msg)
        
        self.assertEqual(error_type, ErrorType.NETWORK_ERROR)
        self.assertEqual(severity, ErrorSeverity.MEDIUM)
        
        # 测试认证错误
        error_msg = "认证失败: 无效的API密钥"
        error_type, severity = self.handler.detect_error_type(error_msg)
        
        self.assertEqual(error_type, ErrorType.AUTHENTICATION_ERROR)
        self.assertEqual(severity, ErrorSeverity.HIGH)
    
    def test_record_error(self):
        """测试错误记录"""
        task_id = "test_task"
        subtask_id = "test_subtask"
        skill_name = "test_skill"
        error_message = "测试错误消息"
        
        record = self.handler.record_error(
            task_id, subtask_id, skill_name, error_message
        )
        
        self.assertIsNotNone(record)
        self.assertEqual(record.task_id, task_id)
        self.assertEqual(record.subtask_id, subtask_id)
        self.assertEqual(record.skill_name, skill_name)
        self.assertEqual(record.error_message, error_message)
        self.assertFalse(record.resolved)
        
        # 检查错误历史
        self.assertIn(record, self.handler.error_history)
    
    def test_handle_error(self):
        """测试错误处理"""
        # 创建一个错误记录
        record = ErrorRecord(
            error_id="test_error",
            task_id="test_task",
            subtask_id="test_subtask",
            skill_name="test_skill",
            error_type=ErrorType.SKILL_TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            error_message="请求超时",
            stack_trace="",
            timestamp=time.time()
        )
        
        context = {
            "available_skills": ["skill1", "skill2"],
            "dependencies": []
        }
        
        result = self.handler.handle_error(record, context)
        
        self.assertIn("success", result)
        self.assertIn("method", result)
        
        # 检查记录是否更新
        self.assertEqual(record.retry_count, 1)
    
    def test_get_error_statistics(self):
        """测试错误统计"""
        # 先记录一些错误
        self.handler.record_error("task1", "subtask1", "skill1", "错误1")
        self.handler.record_error("task1", "subtask2", "skill2", "错误2")
        
        stats = self.handler.get_error_statistics()
        
        self.assertEqual(stats["total_errors"], 2)
        self.assertIn("error_type_distribution", stats)
        self.assertIn("severity_distribution", stats)

class TestProcessCorrector(unittest.TestCase):
    """测试流程纠正器"""
    
    def setUp(self):
        self.error_handler = ErrorHandler()
        self.corrector = ProcessCorrector(self.error_handler)
    
    def test_analyze_process_flow(self):
        """测试流程分析"""
        execution_plan = {
            "subtasks": [
                {"id": "task1", "description": "任务1", "estimated_time": 60},
                {"id": "task2", "description": "任务2", "estimated_time": 120},
                {"id": "task3", "description": "任务3", "estimated_time": 90}
            ],
            "dependencies": [
                ("task2", ["task1"]),
                ("task3", ["task2"])
            ],
            "parallel_groups": [["task1"], ["task2"], ["task3"]]
        }
        
        execution_results = {
            "overall_status": "completed",
            "total_time": 300,
            "subtask_results": {
                "task1": {"status": "completed", "execution_time": 70, "retries": 0},
                "task2": {"status": "completed", "execution_time": 130, "retries": 1},
                "task3": {"status": "completed", "execution_time": 100, "retries": 0}
            }
        }
        
        analysis = self.corrector.analyze_process_flow(execution_plan, execution_results)
        
        self.assertIn("overall_status", analysis)
        self.assertIn("total_subtasks", analysis)
        self.assertIn("completed_subtasks", analysis)
        self.assertIn("efficiency_score", analysis)
        self.assertIn("bottlenecks", analysis)
        self.assertIn("improvement_suggestions", analysis)
        self.assertIn("process_health", analysis)
        
        self.assertEqual(analysis["total_subtasks"], 3)
        self.assertEqual(analysis["completed_subtasks"], 3)
        self.assertGreater(analysis["efficiency_score"], 0)
    
    def test_correct_process_flow(self):
        """测试流程纠正"""
        execution_plan = {
            "template_id": "test_template",
            "subtasks": [
                {"id": "task1", "description": "任务1", "estimated_time": 60},
                {"id": "task2", "description": "任务2", "estimated_time": 120}
            ],
            "dependencies": [("task2", ["task1"])],
            "parallel_groups": [["task1"], ["task2"]]
        }
        
        analysis = {
            "overall_status": "partial_failure",
            "total_subtasks": 2,
            "completed_subtasks": 1,
            "failed_subtasks": 1,
            "retried_subtasks": 1,
            "total_execution_time": 200,
            "efficiency_score": 0.6,
            "bottlenecks": [
                {
                    "type": "execution_time",
                    "subtask_id": "task2",
                    "description": "任务2",
                    "estimated_time": 120,
                    "actual_time": 180,
                    "suggestion": "优化算法"
                }
            ],
            "improvement_suggestions": ["优化算法", "增加重试策略"],
            "process_health": "fair"
        }
        
        corrected_plan = self.corrector.correct_process_flow(execution_plan, analysis)
        
        self.assertIn("correction_applied", corrected_plan)
        self.assertTrue(corrected_plan["correction_applied"])
        self.assertIn("improvements_applied", corrected_plan)
        self.assertGreater(len(corrected_plan["improvements_applied"]), 0)
        
        # 检查是否应用了改进
        subtasks = corrected_plan.get("subtasks", [])
        for subtask in subtasks:
            if subtask.get("id") == "task2":
                self.assertIn("optimization_suggestions", subtask)
                break

class TestMultiSkillOrchestrationSystem(unittest.TestCase):
    """测试完整编排系统"""
    
    def setUp(self):
        self.system = MultiSkillOrchestrationSystem()
    
    @patch.object(MultiSkillOrchestrator, 'execute_plan')
    @patch.object(ExecutionPlanGenerator, 'generate_custom_plan')
    @patch.object(MultiSkillOrchestrator, 'analyze_requirements')
    def test_process_user_request(self, mock_analyze, mock_generate, mock_execute):
        """测试处理用户请求"""
        # 设置模拟返回值
        mock_analyze.return_value = {
            "complexity": "medium",
            "detected_skills": ["data_analysis", "document_creation"],
            "task_type": "custom"
        }
        
        mock_generate.return_value = {
            "template_id": "custom_generated",
            "template_name": "智能生成计划",
            "subtasks": [
                {"id": "task1", "description": "数据分析", "estimated_time": 90},
                {"id": "task2", "description": "报告撰写", "estimated_time": 120}
            ],
            "execution_order": ["task1", "task2"],
            "parallel_groups": [["task1"], ["task2"]],
            "estimated_time": {"max": 210}
        }
        
        mock_execute.return_value = {
            "plan_id": "test_plan",
            "overall_status": "completed",
            "subtask_results": {
                "task1": {"status": "completed", "execution_time": 95},
                "task2": {"status": "completed", "execution_time": 125}
            },
            "total_time": 220
        }
        
        # 执行测试
        user_request = "帮我分析数据并生成报告"
        result = self.system.process_user_request(user_request)
        
        # 验证结果
        self.assertIn("success", result)
        self.assertTrue(result["success"])
        self.assertEqual(result["user_request"], user_request)
        self.assertIn("execution_summary", result)
        self.assertIn("process_health", result)
        
        # 验证模拟调用
        mock_analyze.assert_called_once_with(user_request)
        mock_generate.assert_called_once()
        mock_execute.assert_called_once()
    
    def test_get_system_status(self):
        """测试获取系统状态"""
        status = self.system.get_system_status()
        
        self.assertIn("system", status)
        self.assertIn("statistics", status)
        self.assertIn("error_statistics", status)
        self.assertIn("template_library", status)
        
        # 检查基本状态
        self.assertTrue(status["system"]["components_initialized"])
        self.assertTrue(status["system"]["config_loaded"])
        
        # 检查统计信息
        stats = status["statistics"]
        self.assertEqual(stats["total_tasks"], 0)  # 初始状态
    
    @patch.object(TemplateLibrary, 'find_matching_templates')
    def test_template_suggestion(self, mock_find):
        """测试模板建议"""
        # 模拟模板查找
        mock_template = Mock(spec=TaskTemplate)
        mock_template.id = "test_template"
        mock_template.name = "测试模板"
        mock_template.category = TemplateCategory.DATA_ANALYSIS
        mock_template.complexity = "medium"
        mock_template.usage_count = 5
        mock_template.success_rate = 0.9
        
        mock_find.return_value = [mock_template]
        
        # 测试启用模板建议
        self.system.config["enable_template_suggestion"] = True
        
        user_request = "数据分析报告"
        result = self.system.process_user_request(user_request, {"use_template": True})
        
        # 验证模板查找被调用
        mock_find.assert_called_once_with(user_request)
    
    @patch.object(ProcessCorrector, 'correct_process_flow')
    @patch.object(MultiSkillOrchestrator, 'execute_plan')
    def test_auto_correction(self, mock_execute, mock_correct):
        """测试自动纠正"""
        # 模拟执行失败
        mock_execute.return_value = {
            "plan_id": "test_plan",
            "overall_status": "partial_failure",
            "subtask_results": {},
            "total_time": 100
        }
        
        # 模拟纠正成功
        mock_correct.return_value = {
            "template_id": "corrected_plan",
            "subtasks": [],
            "correction_applied": True
        }
        
        # 测试启用自动纠正
        self.system.config["enable_auto_correction"] = True
        
        user_request = "测试请求"
        result = self.system.process_user_request(user_request)
        
        # 验证纠正被调用（因为执行失败）
        mock_correct.assert_called_once()

class IntegrationTest(unittest.TestCase):
    """集成测试"""
    
    def test_end_to_end_simple(self):
        """简单端到端测试"""
        system = MultiSkillOrchestrationSystem()
        
        # 配置系统（禁用某些功能以简化测试）
        system.config.update({
            "enable_parallel_execution": False,
            "enable_auto_correction": False,
            "enable_template_suggestion": False
        })
        
        # 简单请求
        user_request = "测试数据分析"
        
        # 处理请求
        result = system.process_user_request(user_request)
        
        # 验证基本结构
        self.assertIn("success", result)
        self.assertEqual(result["user_request"], user_request)
        self.assertIn("analysis_summary", result)
        self.assertIn("execution_summary", result)
        self.assertIn("process_health", result)
        
        # 验证统计更新
        self.assertEqual(system.execution_stats["total_tasks"], 1)
    
    def test_error_handling_integration(self):
        """错误处理集成测试"""
        system = MultiSkillOrchestrationSystem()
        
        # 模拟一个会出错的请求
        user_request = "测试会出错的请求"
        
        # 这里我们实际上测试的是错误处理系统是否正常初始化
        self.assertIsNotNone(system.error_handler)
        self.assertIsNotNone(system.process_corrector)
        
        # 检查错误处理器是否正常工作
        error_record = system.error_handler.record_error(
            "test_task", "test_subtask", "test_skill", "测试错误"
        )
        
        self.assertIsNotNone(error_record)
        self.assertEqual(error_record.error_message, "测试错误")
        
        # 检查错误统计
        stats = system.error_handler.get_error_statistics()
        self.assertGreaterEqual(stats["total_errors"], 1)

def run_performance_test():
    """运行性能测试"""
    import timeit
    
    system = MultiSkillOrchestrationSystem()
    
    # 测试需求分析性能
    def test_analyze():
        requests = [
            "数据分析报告",
            "市场调研文档",
            "产品落地页开发",
            "社交媒体营销方案"
        ]
        
        for request in requests:
            system.orchestrator.analyze_requirements(request)
    
    # 测试任务分解性能
    def test_decompose():
        analysis = {"detected_skills": ["data_analysis", "document_creation"]}
        system.orchestrator.decompose_task("测试任务", analysis)
    
    # 测试模板查找性能
    def test_template_find():
        system.template_library.find_matching_templates("市场分析")
    
    print("性能测试结果:")
    print(f"需求分析: {timeit.timeit(test_analyze, number=100):.3f}秒 (100次)")
    print(f"任务分解: {timeit.timeit(test_decompose, number=100):.3f}秒 (100次)")
    print(f"模板查找: {timeit.timeit(test_template_find, number=100):.3f}秒 (100次)")

if __name__ == "__main__":
    # 运行单元测试
    print("运行单元测试...")
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n测试结果: {result.testsRun}个测试运行")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    # 运行性能测试
    print("\n" + "="*50)
    print("运行性能测试...")
    run_performance_test()
    
    # 如果所有测试都通过，显示成功消息
    if result.wasSuccessful():
        print("\n✅ 所有测试通过!")
    else:
        print("\n❌ 测试失败!")
        sys.exit(1)