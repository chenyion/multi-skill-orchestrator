#!/usr/bin/env python3
"""
异常处理和流程纠错机制
提供智能错误检测、自动重试、流程调整和故障转移能力
"""

import json
import time
import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
import random

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"        # 轻微错误，不影响整体流程
    MEDIUM = "medium"  # 中等错误，可能影响部分功能
    HIGH = "high"      # 严重错误，影响核心功能
    CRITICAL = "critical"  # 致命错误，流程无法继续

class ErrorType(Enum):
    """错误类型枚举"""
    SKILL_UNAVAILABLE = "skill_unavailable"      # 技能不可用
    SKILL_TIMEOUT = "skill_timeout"              # 技能执行超时
    SKILL_ERROR = "skill_error"                  # 技能执行错误
    DATA_VALIDATION = "data_validation"          # 数据验证失败
    DEPENDENCY_FAILURE = "dependency_failure"    # 依赖任务失败
    RESOURCE_LIMIT = "resource_limit"            # 资源限制
    NETWORK_ERROR = "network_error"              # 网络错误
    AUTHENTICATION_ERROR = "authentication_error" # 认证错误
    CONFIGURATION_ERROR = "configuration_error"  # 配置错误
    UNKNOWN_ERROR = "unknown_error"              # 未知错误

@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    task_id: str
    subtask_id: str
    skill_name: str
    error_type: ErrorType
    severity: ErrorSeverity
    error_message: str
    stack_trace: str
    timestamp: float
    retry_count: int = 0
    resolved: bool = False
    resolution_method: Optional[str] = None
    resolution_time: Optional[float] = None

@dataclass
class RetryStrategy:
    """重试策略配置"""
    max_retries: int = 3
    retry_delay_base: float = 1.0  # 基础延迟（秒）
    retry_delay_max: float = 60.0  # 最大延迟（秒）
    backoff_factor: float = 2.0    # 指数退避因子
    jitter: bool = True            # 是否添加随机抖动
    
    def calculate_delay(self, retry_count: int) -> float:
        """计算重试延迟"""
        delay = min(
            self.retry_delay_base * (self.backoff_factor ** retry_count),
            self.retry_delay_max
        )
        
        if self.jitter:
            # 添加±10%的随机抖动
            jitter_factor = random.uniform(0.9, 1.1)
            delay *= jitter_factor
        
        return delay

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, error_history_file: str = None):
        self.error_history_file = error_history_file or "/tmp/error_history.json"
        self.error_history: List[ErrorRecord] = self._load_error_history()
        self.retry_strategy = RetryStrategy()
        
        # 错误处理策略映射
        self.error_handlers = {
            ErrorType.SKILL_UNAVAILABLE: self._handle_skill_unavailable,
            ErrorType.SKILL_TIMEOUT: self._handle_skill_timeout,
            ErrorType.SKILL_ERROR: self._handle_skill_error,
            ErrorType.DATA_VALIDATION: self._handle_data_validation,
            ErrorType.DEPENDENCY_FAILURE: self._handle_dependency_failure,
            ErrorType.RESOURCE_LIMIT: self._handle_resource_limit,
            ErrorType.NETWORK_ERROR: self._handle_network_error,
            ErrorType.AUTHENTICATION_ERROR: self._handle_authentication_error,
            ErrorType.CONFIGURATION_ERROR: self._handle_configuration_error,
            ErrorType.UNKNOWN_ERROR: self._handle_unknown_error,
        }
        
        # 常见错误模式识别
        self.error_patterns = {
            r"timeout|timed out|请求超时": ErrorType.SKILL_TIMEOUT,
            r"connection refused|无法连接|网络错误": ErrorType.NETWORK_ERROR,
            r"authentication failed|认证失败|权限不足": ErrorType.AUTHENTICATION_ERROR,
            r"resource exhausted|资源不足|内存不足": ErrorType.RESOURCE_LIMIT,
            r"not found|找不到|不存在": ErrorType.SKILL_UNAVAILABLE,
            r"validation failed|验证失败|数据错误": ErrorType.DATA_VALIDATION,
            r"dependency|依赖|requires": ErrorType.DEPENDENCY_FAILURE,
            r"configuration|配置|设置错误": ErrorType.CONFIGURATION_ERROR,
        }
    
    def _load_error_history(self) -> List[ErrorRecord]:
        """加载错误历史记录"""
        try:
            with open(self.error_history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 转换回ErrorRecord对象
            history = []
            for item in data:
                item['error_type'] = ErrorType(item['error_type'])
                item['severity'] = ErrorSeverity(item['severity'])
                history.append(ErrorRecord(**item))
            
            return history
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_error_history(self):
        """保存错误历史记录"""
        try:
            # 转换为可序列化的字典
            data = []
            for record in self.error_history:
                record_dict = asdict(record)
                record_dict['error_type'] = record.error_type.value
                record_dict['severity'] = record.severity.value
                data.append(record_dict)
            
            with open(self.error_history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存错误历史失败: {e}")
    
    def detect_error_type(self, error_message: str, stack_trace: str = "") -> Tuple[ErrorType, ErrorSeverity]:
        """检测错误类型和严重程度"""
        error_text = (error_message + " " + stack_trace).lower()
        
        # 匹配错误模式
        detected_type = ErrorType.UNKNOWN_ERROR
        for pattern, error_type in self.error_patterns.items():
            if re.search(pattern, error_text, re.IGNORECASE):
                detected_type = error_type
                break
        
        # 确定严重程度
        severity = self._determine_severity(detected_type, error_text)
        
        logger.info(f"错误检测结果: 类型={detected_type.value}, 严重程度={severity.value}")
        return detected_type, severity
    
    def _determine_severity(self, error_type: ErrorType, error_text: str) -> ErrorSeverity:
        """确定错误严重程度"""
        
        severity_mapping = {
            ErrorType.SKILL_TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorType.NETWORK_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.SKILL_UNAVAILABLE: ErrorSeverity.HIGH,
            ErrorType.AUTHENTICATION_ERROR: ErrorSeverity.HIGH,
            ErrorType.RESOURCE_LIMIT: ErrorSeverity.HIGH,
            ErrorType.DEPENDENCY_FAILURE: ErrorSeverity.HIGH,
            ErrorType.DATA_VALIDATION: ErrorSeverity.MEDIUM,
            ErrorType.CONFIGURATION_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.SKILL_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.UNKNOWN_ERROR: ErrorSeverity.HIGH,
        }
        
        base_severity = severity_mapping.get(error_type, ErrorSeverity.MEDIUM)
        
        # 根据错误信息调整严重程度
        critical_keywords = ["fatal", "critical", "cannot continue", "无法继续", "严重错误"]
        low_keywords = ["warning", "minor", "非关键", "可忽略"]
        
        for keyword in critical_keywords:
            if keyword in error_text.lower():
                return ErrorSeverity.CRITICAL
        
        for keyword in low_keywords:
            if keyword in error_text.lower():
                return ErrorSeverity.LOW
        
        return base_severity
    
    def record_error(self, task_id: str, subtask_id: str, skill_name: str,
                    error_message: str, stack_trace: str = "") -> ErrorRecord:
        """记录错误"""
        
        error_type, severity = self.detect_error_type(error_message, stack_trace)
        
        error_record = ErrorRecord(
            error_id=f"err_{int(time.time())}_{random.randint(1000, 9999)}",
            task_id=task_id,
            subtask_id=subtask_id,
            skill_name=skill_name,
            error_type=error_type,
            severity=severity,
            error_message=error_message,
            stack_trace=stack_trace,
            timestamp=time.time(),
            retry_count=0
        )
        
        self.error_history.append(error_record)
        self._save_error_history()
        
        logger.warning(f"记录错误: {error_record.error_id} - {error_type.value} - {severity.value}")
        return error_record
    
    def handle_error(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理错误，返回处理结果"""
        
        handler = self.error_handlers.get(error_record.error_type, self._handle_unknown_error)
        resolution_result = handler(error_record, context)
        
        # 更新错误记录
        error_record.resolved = resolution_result.get("success", False)
        error_record.resolution_method = resolution_result.get("method")
        error_record.resolution_time = time.time() if error_record.resolved else None
        error_record.retry_count += 1
        
        self._save_error_history()
        
        return resolution_result
    
    def _handle_skill_unavailable(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理技能不可用错误"""
        logger.info(f"处理技能不可用错误: {error_record.skill_name}")
        
        # 尝试寻找替代技能
        alternative_skills = context.get("available_skills", [])
        current_skill = error_record.skill_name
        
        # 从可用技能中排除当前失败技能，寻找功能相似的替代
        alternative = None
        for skill in alternative_skills:
            if skill != current_skill:
                # 简单的技能替代逻辑，实际应该基于技能能力匹配
                alternative = skill
                break
        
        if alternative:
            logger.info(f"找到替代技能: {alternative}")
            return {
                "success": True,
                "method": "skill_replacement",
                "alternative_skill": alternative,
                "message": f"使用替代技能 {alternative} 替换 {current_skill}"
            }
        else:
            logger.warning("未找到合适的替代技能")
            return {
                "success": False,
                "method": "no_alternative",
                "message": "没有可用的替代技能，任务无法继续"
            }
    
    def _handle_skill_timeout(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理技能超时错误"""
        logger.info(f"处理技能超时错误: {error_record.skill_name}")
        
        # 检查重试次数
        max_retries = self.retry_strategy.max_retries
        if error_record.retry_count >= max_retries:
            logger.warning(f"已达到最大重试次数 ({max_retries})")
            return {
                "success": False,
                "method": "max_retries_exceeded",
                "message": f"技能 {error_record.skill_name} 超时重试次数已达上限"
            }
        
        # 计算重试延迟
        delay = self.retry_strategy.calculate_delay(error_record.retry_count)
        logger.info(f"将在 {delay:.1f} 秒后重试")
        
        return {
            "success": True,
            "method": "retry_with_delay",
            "retry_delay": delay,
            "message": f"计划在 {delay:.1f} 秒后重试技能 {error_record.skill_name}"
        }
    
    def _handle_skill_error(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理技能执行错误"""
        logger.info(f"处理技能执行错误: {error_record.skill_name}")
        
        error_msg = error_record.error_message.lower()
        
        # 分析错误原因
        if "input" in error_msg or "参数" in error_msg or "数据" in error_msg:
            # 输入数据问题
            return {
                "success": True,
                "method": "adjust_input",
                "message": "检测到输入数据问题，将调整输入参数重试",
                "adjustments": {"simplify_input": True, "validate_data": True}
            }
        elif "memory" in error_msg or "内存" in error_msg:
            # 内存问题
            return {
                "success": True,
                "method": "reduce_complexity",
                "message": "检测到内存问题，将降低任务复杂度重试",
                "adjustments": {"reduce_batch_size": True, "use_streaming": True}
            }
        else:
            # 通用重试
            return self._handle_general_retry(error_record, context)
    
    def _handle_data_validation(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据验证错误"""
        logger.info("处理数据验证错误")
        
        # 尝试数据清洗和修复
        return {
            "success": True,
            "method": "data_cleaning",
            "message": "将尝试数据清洗和格式转换",
            "actions": [
                "remove_invalid_chars",
                "normalize_format",
                "fill_missing_values"
            ]
        }
    
    def _handle_dependency_failure(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理依赖任务失败错误"""
        logger.info("处理依赖任务失败错误")
        
        # 获取依赖关系
        dependencies = context.get("dependencies", [])
        failed_dependency = error_record.subtask_id
        
        # 尝试寻找替代依赖或跳过
        if context.get("allow_skip", False):
            logger.info(f"允许跳过失败依赖: {failed_dependency}")
            return {
                "success": True,
                "method": "skip_dependency",
                "message": f"跳过失败的依赖任务 {failed_dependency}",
                "warning": "跳过依赖可能导致结果不完整"
            }
        else:
            return {
                "success": False,
                "method": "dependency_required",
                "message": f"关键依赖任务 {failed_dependency} 失败，无法继续"
            }
    
    def _handle_resource_limit(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理资源限制错误"""
        logger.info("处理资源限制错误")
        
        # 尝试优化资源使用
        return {
            "success": True,
            "method": "optimize_resources",
            "message": "将优化资源使用策略",
            "optimizations": [
                "reduce_concurrency",
                "increase_timeout",
                "use_compression",
                "batch_processing"
            ]
        }
    
    def _handle_network_error(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理网络错误"""
        logger.info("处理网络错误")
        
        # 网络错误通常需要重试
        return self._handle_general_retry(error_record, context)
    
    def _handle_authentication_error(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理认证错误"""
        logger.info("处理认证错误")
        
        # 认证错误可能需要重新获取凭证
        return {
            "success": True,
            "method": "refresh_credentials",
            "message": "将尝试刷新认证凭证",
            "actions": ["renew_token", "validate_permissions"]
        }
    
    def _handle_configuration_error(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理配置错误"""
        logger.info("处理配置错误")
        
        # 尝试修复配置
        return {
            "success": True,
            "method": "fix_configuration",
            "message": "将检查和修复配置",
            "actions": ["validate_config", "apply_defaults", "test_connection"]
        }
    
    def _handle_unknown_error(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理未知错误"""
        logger.info("处理未知错误")
        
        # 对于未知错误，尝试通用重试策略
        return self._handle_general_retry(error_record, context)
    
    def _handle_general_retry(self, error_record: ErrorRecord, context: Dict[str, Any]) -> Dict[str, Any]:
        """通用重试处理"""
        max_retries = self.retry_strategy.max_retries
        
        if error_record.retry_count >= max_retries:
            return {
                "success": False,
                "method": "max_retries_exceeded",
                "message": f"已达到最大重试次数 ({max_retries})"
            }
        
        delay = self.retry_strategy.calculate_delay(error_record.retry_count)
        
        return {
            "success": True,
            "method": "retry_with_backoff",
            "retry_delay": delay,
            "message": f"将在 {delay:.1f} 秒后重试 (第{error_record.retry_count + 1}次)"
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        if not self.error_history:
            return {"total_errors": 0}
        
        total_errors = len(self.error_history)
        resolved_errors = sum(1 for e in self.error_history if e.resolved)
        
        # 按错误类型统计
        error_type_stats = {}
        for error_type in ErrorType:
            count = sum(1 for e in self.error_history if e.error_type == error_type)
            if count > 0:
                error_type_stats[error_type.value] = count
        
        # 按严重程度统计
        severity_stats = {}
        for severity in ErrorSeverity:
            count = sum(1 for e in self.error_history if e.severity == severity)
            if count > 0:
                severity_stats[severity.value] = count
        
        # 最近24小时错误趋势
        twenty_four_hours_ago = time.time() - 24 * 3600
        recent_errors = sum(1 for e in self.error_history if e.timestamp > twenty_four_hours_ago)
        
        return {
            "total_errors": total_errors,
            "resolved_errors": resolved_errors,
            "resolution_rate": resolved_errors / total_errors if total_errors > 0 else 0,
            "error_type_distribution": error_type_stats,
            "severity_distribution": severity_stats,
            "recent_errors_24h": recent_errors,
            "most_common_error": max(error_type_stats.items(), key=lambda x: x[1])[0] if error_type_stats else None,
            "most_severe_error": max(severity_stats.items(), key=lambda x: x[1])[0] if severity_stats else None
        }

class ProcessCorrector:
    """流程纠正器"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
    
    def analyze_process_flow(self, execution_plan: Dict[str, Any], 
                           execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """分析流程执行情况，识别问题和改进点"""
        
        logger.info("分析流程执行情况")
        
        analysis = {
            "overall_status": execution_results.get("overall_status", "unknown"),
            "total_subtasks": len(execution_plan.get("subtasks", [])),
            "completed_subtasks": 0,
            "failed_subtasks": 0,
            "retried_subtasks": 0,
            "total_execution_time": execution_results.get("total_time", 0),
            "efficiency_score": 0,
            "bottlenecks": [],
            "improvement_suggestions": [],
            "process_health": "good"
        }
        
        # 统计子任务状态
        subtask_results = execution_results.get("subtask_results", {})
        for subtask_id, result in subtask_results.items():
            if result.get("status") == "completed":
                analysis["completed_subtasks"] += 1
            elif result.get("status") == "failed":
                analysis["failed_subtasks"] += 1
            
            if result.get("retries", 0) > 0:
                analysis["retried_subtasks"] += 1
        
        # 计算效率分数
        completion_rate = analysis["completed_subtasks"] / analysis["total_subtasks"] if analysis["total_subtasks"] > 0 else 0
        retry_rate = analysis["retried_subtasks"] / analysis["total_subtasks"] if analysis["total_subtasks"] > 0 else 0
        
        analysis["efficiency_score"] = (
            completion_rate * 0.6 +  # 完成率权重60%
            (1 - retry_rate) * 0.3 +  # 低重试率权重30%
            (max(0, 1 - analysis["total_execution_time"] / 3600)) * 0.1  # 执行时间权重10%
        )
        
        # 识别瓶颈
        analysis["bottlenecks"] = self._identify_bottlenecks(execution_plan, execution_results)
        
        # 生成改进建议
        analysis["improvement_suggestions"] = self._generate_improvements(analysis)
        
        # 评估流程健康度
        analysis["process_health"] = self._assess_process_health(analysis)
        
        return analysis
    
    def _identify_bottlenecks(self, execution_plan: Dict[str, Any], 
                            execution_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别执行瓶颈"""
        bottlenecks = []
        
        subtask_results = execution_results.get("subtask_results", {})
        subtasks = execution_plan.get("subtasks", [])
        
        # 查找执行时间过长的任务
        for subtask in subtasks:
            subtask_id = subtask.get("id")
            result = subtask_results.get(subtask_id, {})
            
            if result.get("execution_time", 0) > subtask.get("estimated_time", 60) * 2:
                bottlenecks.append({
                    "type": "execution_time",
                    "subtask_id": subtask_id,
                    "description": subtask.get("description", ""),
                    "estimated_time": subtask.get("estimated_time", 60),
                    "actual_time": result.get("execution_time", 0),
                    "suggestion": "优化算法或增加资源"
                })
        
        # 查找频繁失败的任务
        error_stats = self.error_handler.get_error_statistics()
        for subtask in subtasks:
            subtask_id = subtask.get("id")
            
            # 统计该子任务的错误数
            subtask_errors = sum(
                1 for e in self.error_handler.error_history 
                if e.subtask_id == subtask_id and not e.resolved
            )
            
            if subtask_errors >= 2:  # 失败2次以上
                bottlenecks.append({
                    "type": "failure_rate",
                    "subtask_id": subtask_id,
                    "description": subtask.get("description", ""),
                    "error_count": subtask_errors,
                    "suggestion": "检查依赖项或使用替代方案"
                })
        
        # 识别资源竞争
        parallel_groups = execution_plan.get("parallel_groups", [])
        if len(parallel_groups) > 3:
            bottlenecks.append({
                "type": "concurrency",
                "description": "并行任务过多可能导致资源竞争",
                "parallel_groups": len(parallel_groups),
                "suggestion": "减少并发度或增加资源分配"
            })
        
        return bottlenecks
    
    def _generate_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        improvements = []
        
        # 基于完成率的改进
        completion_rate = analysis["completed_subtasks"] / analysis["total_subtasks"]
        if completion_rate < 0.8:
            improvements.append("增加任务重试策略和超时设置")
        
        # 基于重试率的改进
        retry_rate = analysis["retried_subtasks"] / analysis["total_subtasks"]
        if retry_rate > 0.3:
            improvements.append("优化错误处理机制，减少不必要的重试")
        
        # 基于执行时间的改进
        if analysis["total_execution_time"] > 1800:  # 超过30分钟
            improvements.append("优化执行计划，增加并行度和减少依赖")
        
        # 基于瓶颈的改进
        for bottleneck in analysis["bottlenecks"]:
            improvements.append(bottleneck.get("suggestion", ""))
        
        # 通用改进建议
        if analysis["efficiency_score"] < 0.7:
            improvements.append("考虑重构流程，简化复杂任务")
        
        if len(analysis["bottlenecks"]) > 2:
            improvements.append("重新设计任务依赖关系，减少关键路径")
        
        return list(set(improvements))  # 去重
    
    def _assess_process_health(self, analysis: Dict[str, Any]) -> str:
        """评估流程健康度"""
        completion_rate = analysis["completed_subtasks"] / analysis["total_subtasks"]
        retry_rate = analysis["retried_subtasks"] / analysis["total_subtasks"]
        efficiency_score = analysis["efficiency_score"]
        
        if completion_rate >= 0.9 and retry_rate <= 0.1 and efficiency_score >= 0.8:
            return "excellent"
        elif completion_rate >= 0.8 and retry_rate <= 0.2 and efficiency_score >= 0.7:
            return "good"
        elif completion_rate >= 0.6 and retry_rate <= 0.3 and efficiency_score >= 0.6:
            return "fair"
        else:
            return "poor"
    
    def correct_process_flow(self, execution_plan: Dict[str, Any], 
                           analysis: Dict[str, Any]) -> Dict[str, Any]:
        """纠正流程，生成优化后的执行计划"""
        
        logger.info("开始流程纠正")
        
        corrected_plan = execution_plan.copy()
        
        # 应用改进建议
        improvements_applied = []
        
        # 1. 优化任务依赖关系
        if "重新设计任务依赖关系" in analysis.get("improvement_suggestions", []):
            corrected_plan = self._optimize_dependencies(corrected_plan)
            improvements_applied.append("optimized_dependencies")
        
        # 2. 调整并行度
        if "减少并发度或增加资源分配" in analysis.get("improvement_suggestions", []):
            corrected_plan = self._adjust_concurrency(corrected_plan)
            improvements_applied.append("adjusted_concurrency")
        
        # 3. 增加重试策略
        if "增加任务重试策略和超时设置" in analysis.get("improvement_suggestions", []):
            corrected_plan = self._enhance_retry_strategy(corrected_plan)
            improvements_applied.append("enhanced_retry_strategy")
        
        # 4. 优化执行时间预估
        if "优化算法或增加资源" in analysis.get("improvement_suggestions", []):
            corrected_plan = self._adjust_time_estimates(corrected_plan, analysis)
            improvements_applied.append("adjusted_time_estimates")
        
        # 记录纠正信息
        corrected_plan["correction_applied"] = True
        corrected_plan["correction_timestamp"] = time.time()
        corrected_plan["improvements_applied"] = improvements_applied
        corrected_plan["original_plan_id"] = execution_plan.get("template_id", "unknown")
        
        logger.info(f"流程纠正完成，应用了 {len(improvements_applied)} 项改进")
        return corrected_plan
    
    def _optimize_dependencies(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """优化任务依赖关系"""
        dependencies = plan.get("dependencies", [])
        
        # 简化依赖关系：移除不必要的间接依赖
        simplified_deps = []
        direct_dependencies = {}
        
        for dep in dependencies:
            if isinstance(dep, tuple) and len(dep) == 2:
                task_id, deps = dep
                if isinstance(deps, str):
                    deps = [deps]
                
                # 只保留直接依赖
                filtered_deps = []
                for d in deps:
                    # 检查这个依赖是否已经被其他依赖间接包含
                    if d not in direct_dependencies.get(task_id, []):
                        filtered_deps.append(d)
                
                if filtered_deps:
                    direct_dependencies[task_id] = filtered_deps
                    simplified_deps.append((task_id, filtered_deps))
        
        plan["dependencies"] = simplified_deps
        
        # 重新计算执行顺序
        from .template_library import ExecutionPlanGenerator
        generator = ExecutionPlanGenerator(None)  # 不需要模板库
        plan = generator.optimize_parallel_execution(plan)
        
        return plan
    
    def _adjust_concurrency(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """调整并行度"""
        parallel_groups = plan.get("parallel_groups", [])
        
        if len(parallel_groups) > 3:
            # 减少并行度：将一些并行组合并
            new_parallel_groups = []
            
            for i in range(0, len(parallel_groups), 2):
                if i + 1 < len(parallel_groups):
                    merged_group = parallel_groups[i] + parallel_groups[i + 1]
                    new_parallel_groups.append(merged_group)
                else:
                    new_parallel_groups.append(parallel_groups[i])
            
            plan["parallel_groups"] = new_parallel_groups
        
        return plan
    
    def _enhance_retry_strategy(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """增强重试策略"""
        subtasks = plan.get("subtasks", [])
        
        for subtask in subtasks:
            # 为每个子任务添加重试配置
            if "retry_config" not in subtask:
                subtask["retry_config"] = {
                    "max_retries": 3,
                    "retry_delay": 5,
                    "backoff_factor": 2.0,
                    "retry_on_errors": ["timeout", "network_error", "skill_error"]
                }
        
        plan["subtasks"] = subtasks
        return plan
    
    def _adjust_time_estimates(self, plan: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """调整时间预估"""
        subtasks = plan.get("subtasks", [])
        bottlenecks = analysis.get("bottlenecks", [])
        
        bottleneck_tasks = {b["subtask_id"]: b["actual_time"] for b in bottlenecks if "subtask_id" in b}
        
        for subtask in subtasks:
            subtask_id = subtask.get("id")
            
            if subtask_id in bottleneck_tasks:
                # 根据实际执行时间调整预估时间
                actual_time = bottleneck_tasks[subtask_id]
                new_estimate = actual_time * 1.2  # 增加20%缓冲
                subtask["estimated_time"] = int(new_estimate)
                
                # 添加优化建议
                subtask["optimization_suggestions"] = [
                    "考虑使用更高效的算法",
                    "增加处理资源",
                    "优化数据预处理"
                ]
        
        plan["subtasks"] = subtasks
        
        # 更新总预估时间
        total_estimated = sum(st.get("estimated_time", 60) for st in subtasks)
        if "estimated_time" in plan:
            plan["estimated_time"]["max"] = total_estimated
        
        return plan

def main():
    """演示错误处理和流程纠正功能"""
    
    # 创建错误处理器
    error_handler = ErrorHandler()
    
    print("错误处理器初始化完成")
    print("=" * 50)
    
    # 模拟记录一些错误
    test_errors = [
        {
            "task_id": "task_001",
            "subtask_id": "market_research",
            "skill_name": "web_search",
            "error_message": "请求超时: 网络连接不稳定",
            "stack_trace": ""
        },
        {
            "task_id": "task_001",
            "subtask_id": "data_analysis",
            "skill_name": "data_analysis",
            "error_message": "内存不足: 数据集过大",
            "stack_trace": "MemoryError at line 45..."
        },
        {
            "task_id": "task_001",
            "subtask_id": "chart_generation",
            "skill_name": "chart_generator",
            "error_message": "技能不可用: 服务维护中",
            "stack_trace": ""
        }
    ]
    
    print("模拟记录错误:")
    for error_info in test_errors:
        record = error_handler.record_error(**error_info)
        print(f"  - 记录错误: {record.error_id} ({record.error_type.value})")
    
    print()
    
    # 演示错误处理
    print("演示错误处理:")
    
    context = {
        "available_skills": ["data_analysis", "web_search", "chart_generator", "alternative_chart"],
        "dependencies": ["market_research", "data_analysis"],
        "allow_skip": True
    }
    
    for record in error_handler.error_history[-3:]:  # 处理最后3个错误
        print(f"\n处理错误: {record.error_id}")
        print(f"  类型: {record.error_type.value}")
        print(f"  严重程度: {record.severity.value}")
        print(f"  消息: {record.error_message}")
        
        result = error_handler.handle_error(record, context)
        print(f"  处理结果: {result['method']}")
        print(f"  成功: {result['success']}")
        if result['success']:
            print(f"  消息: {result['message']}")
    
    print()
    
    # 获取错误统计
    stats = error_handler.get_error_statistics()
    print("错误统计信息:")
    print(f"  总错误数: {stats['total_errors']}")
    print(f"  解决率: {stats['resolution_rate']:.1%}")
    print(f"  最常见错误: {stats['most_common_error']}")
    print(f"  最近24小时错误数: {stats['recent_errors_24h']}")
    
    print("\n" + "=" * 50)
    
    # 演示流程纠正
    print("演示流程纠正:")
    
    corrector = ProcessCorrector(error_handler)
    
    # 模拟执行计划
    execution_plan = {
        "template_id": "test_template",
        "subtasks": [
            {"id": "task1", "description": "数据收集", "estimated_time": 60},
            {"id": "task2", "description": "数据分析", "estimated_time": 120},
            {"id": "task3", "description": "图表生成", "estimated_time": 90},
            {"id": "task4", "description": "报告撰写", "estimated_time": 180}
        ],
        "dependencies": [
            ("task2", ["task1"]),
            ("task3", ["task2"]),
            ("task4", ["task3"])
        ],
        "parallel_groups": [["task1"], ["task2"], ["task3"], ["task4"]]
    }
    
    # 模拟执行结果
    execution_results = {
        "overall_status": "partial_failure",
        "total_time": 600,
        "subtask_results": {
            "task1": {"status": "completed", "execution_time": 70},
            "task2": {"status": "completed", "execution_time": 150, "retries": 2},
            "task3": {"status": "failed", "execution_time": 200, "retries": 3},
            "task4": {"status": "pending", "execution_time": 0}
        }
    }
    
    # 分析流程
    analysis = corrector.analyze_process_flow(execution_plan, execution_results)
    
    print("流程分析结果:")
    print(f"  总体状态: {analysis['overall_status']}")
    print(f"  完成率: {analysis['completed_subtasks']}/{analysis['total_subtasks']}")
    print(f"  效率分数: {analysis['efficiency_score']:.2f}")
    print(f"  流程健康度: {analysis['process_health']}")
    print(f"  瓶颈数: {len(analysis['bottlenecks'])}")
    print(f"  改进建议: {len(analysis['improvement_suggestions'])} 条")
    
    # 纠正流程
    corrected_plan = corrector.correct_process_flow(execution_plan, analysis)
    
    print("\n纠正后的执行计划:")
    print(f"  应用改进: {corrected_plan.get('improvements_applied', [])}")
    print(f"  依赖关系优化: {len(corrected_plan.get('dependencies', []))} 个")
    print(f"  并行组数: {len(corrected_plan.get('parallel_groups', []))}")

if __name__ == "__main__":
    main()