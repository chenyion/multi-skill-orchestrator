---
name: multi-skill-orchestrator
label: 多技能智能编排
description: "智能多技能编排系统，针对复杂业务需求自动拆解任务步骤、智能匹配现有Skill、编排最优执行链路，支持并行执行、异常重试、流程纠错，实现跨系统、跨场景的复杂任务全闭环自动化，同时沉淀任务执行模板支持一键复用。Use when user needs to handle complex multi-step tasks that require coordination of multiple specialized skills, such as: (1) Complete business analysis reports requiring data collection, analysis, visualization, and document creation, (2) Product development projects needing research, design, implementation, and testing, (3) Marketing campaigns requiring strategy, content creation, design, and analytics, (4) Any workflow involving 3+ different skills or requiring automated task decomposition and optimization."
---

# 多技能智能编排系统

## 概述

本技能为aily工作助手提供了先进的多技能智能编排能力，能够自动处理复杂业务需求，智能拆解任务步骤，匹配最优技能组合，编排高效执行链路，实现全闭环自动化。

## 核心架构

系统由以下核心组件构成：

1. **编排引擎** (`orchestrator_engine.py`) - 负责任务拆解、技能匹配和执行编排
2. **模板库** (`template_library.py`) - 提供丰富的预定义模板和智能计划生成
3. **错误处理器** (`error_handling.py`) - 实现异常检测、自动重试和流程纠正
4. **主协调器** (`main_orchestrator.py`) - 整合所有组件，提供统一接口

## 工作流程

### 1. 需求分析阶段
- 用户输入复杂业务需求
- 系统分析需求复杂度、所需技能类型
- 识别任务类型（数据分析、文档创建、网页开发等）

### 2. 任务拆解阶段
- 将复杂需求分解为原子级子任务
- 确定子任务之间的依赖关系
- 预估每个子任务的执行时间和资源需求

### 3. 技能匹配阶段
- 根据子任务需求智能匹配合适技能
- 考虑技能成功率、执行时间、兼容性
- 支持技能替代和备选方案

### 4. 编排优化阶段
- 生成最优执行顺序
- 识别可并行执行的任务组
- 计算理论最小执行时间

### 5. 执行监控阶段
- 实时监控任务执行状态
- 自动处理执行错误和异常
- 动态调整执行策略

### 6. 结果评估阶段
- 分析执行效率和成功率
- 识别流程瓶颈和改进点
- 自动沉淀成功流程为模板

## 快速开始

### 基本使用

```python
# 初始化编排系统
from main_orchestrator import MultiSkillOrchestrationSystem

system = MultiSkillOrchestrationSystem()

# 处理用户请求
user_request = "帮我分析销售数据，找出销售额最高的产品类别和月度趋势，然后生成一份飞书云文档报告"
result = system.process_user_request(user_request)

# 查看结果
if result["success"]:
    print(f"任务执行成功！耗时: {result['total_processing_time']:.1f}秒")
    print(f"流程健康度: {result['process_health']['health_status']}")
else:
    print(f"任务执行失败: {result.get('error')}")
```

### 命令行使用

```bash
# 显示系统状态
python scripts/main_orchestrator.py --status

# 处理用户请求
python scripts/main_orchestrator.py "帮我创建一份市场分析报告"

# 列出所有模板
python scripts/main_orchestrator.py --list-templates

# 导出模板
python scripts/main_orchestrator.py --export-templates ./my_templates
```

## 核心组件详解

### 编排引擎 (`orchestrator_engine.py`)

**主要功能**：
- 需求分析和复杂度评估
- 任务分解和依赖分析
- 技能匹配和优化
- 执行计划生成和优化

**关键类**：
- `MultiSkillOrchestrator`: 主编排器类
- `Subtask`: 子任务定义
- `SkillProfile`: 技能配置文件
- `ExecutionPlan`: 执行计划定义

**使用示例**：
```python
from orchestrator_engine import MultiSkillOrchestrator

orchestrator = MultiSkillOrchestrator()

# 分析需求
analysis = orchestrator.analyze_requirements("数据分析报告")

# 分解任务
subtasks = orchestrator.decompose_task("数据分析报告", analysis)

# 匹配技能
skill_mapping = orchestrator.match_skills(subtasks)

# 创建执行计划
plan = orchestrator.create_execution_plan(subtasks, skill_mapping)
```

### 模板库 (`template_library.py`)

**主要功能**：
- 预定义任务模板管理
- 智能模板匹配和推荐
- 自定义模板创建和保存
- 模板使用统计和优化

**关键类**：
- `TemplateLibrary`: 模板库管理器
- `TaskTemplate`: 任务模板定义
- `ExecutionPlanGenerator`: 执行计划生成器

**使用示例**：
```python
from template_library import TemplateLibrary

library = TemplateLibrary()

# 查找匹配模板
templates = library.find_matching_templates("市场分析报告")

# 获取模板详情
template = library.get_template("market_analysis_full")

# 创建自定义模板
custom_template = library.create_custom_template(
    user_request, execution_plan, execution_results
)
```

### 错误处理器 (`error_handling.py`)

**主要功能**：
- 错误类型自动检测和分类
- 智能重试策略（指数退避）
- 错误统计和分析
- 流程纠正和优化

**关键类**：
- `ErrorHandler`: 错误处理器
- `ErrorRecord`: 错误记录
- `ProcessCorrector`: 流程纠正器

**使用示例**：
```python
from error_handling import ErrorHandler

handler = ErrorHandler()

# 记录错误
record = handler.record_error(
    task_id="task_001",
    subtask_id="data_analysis",
    skill_name="data_analysis",
    error_message="内存不足错误"
)

# 处理错误
context = {"available_skills": ["data_analysis", "alternative_skill"]}
result = handler.handle_error(record, context)

# 获取错误统计
stats = handler.get_error_statistics()
```

## 配置选项

### 系统配置

创建配置文件 `config.json`:
```json
{
    "max_concurrent_tasks": 5,
    "default_retry_count": 3,
    "timeout_multiplier": 2.0,
    "enable_parallel_execution": true,
    "enable_auto_correction": true,
    "enable_template_suggestion": true,
    "log_level": "INFO",
    "persist_execution_history": true,
    "max_history_size": 1000
}
```

### 技能配置

技能配置文件在 `orchestrator_engine.py` 中定义，包括：
- 技能名称和类型
- 能力描述和输入要求
- 输出格式和执行时间估计
- 成功率和兼容技能

### 模板配置

模板在 `template_library.py` 中预定义，包括：
- 模板名称和类别
- 典型使用场景
- 子任务定义和依赖关系
- 技能要求和预估时间
- 成功标准和产出物

## 使用场景

### 场景1：完整业务分析报告

**用户请求**：
```
帮我分析上季度的销售数据，识别关键趋势和问题点，生成可视化图表，并创建一份包含改进建议的详细报告
```

**系统处理**：
1. 需求分析 → 数据分析 + 可视化 + 文档创建
2. 任务拆解 → 数据收集 → 清洗 → 分析 → 可视化 → 报告
3. 技能匹配 → aily-data → aily-chart → writer agent
4. 编排执行 → 顺序执行，图表生成可并行
5. 结果输出 → 分析报告 + 可视化图表 + 改进建议

### 场景2：产品开发项目

**用户请求**：
```
开发一个员工绩效考核系统，需要数据收集、分析、可视化和管理界面
```

**系统处理**：
1. 需求分析 → 数据工程 + 分析 + 可视化 + 开发
2. 任务拆解 → 需求分析 → 数据模型 → 后端API → 前端界面 → 测试
3. 技能匹配 → 分析 + 数据工程 + web开发 + 测试
4. 编排执行 → 依赖驱动，部分并行
5. 结果输出 → 完整系统 + 文档 + 测试报告

### 场景3：营销活动策划

**用户请求**：
```
为新产品发布策划一个社交媒体营销活动，需要内容创作、视觉设计和效果分析
```

**系统处理**：
1. 需求分析 → 策划 + 内容 + 设计 + 分析
2. 任务拆解 → 策略制定 → 内容创作 → 视觉设计 → 平台设置 → 效果追踪
3. 技能匹配 → 策划 + 创作 + 设计 + 分析
4. 编排执行 → 策略先行，内容设计并行
5. 结果输出 → 完整方案 + 素材库 + 分析模板

## 高级功能

### 并行执行优化

系统自动识别可并行执行的任务，优化执行效率：

```python
# 自动识别并行组
parallel_groups = plan.parallel_groups
# 示例: [['task1', 'task2'], ['task3'], ['task4', 'task5']]

# 计算优化效果
optimization = plan.optimized_estimated_time
# sequential: 顺序执行时间
# parallel_ideal: 并行理想时间
# improvement_rate: 改进率
```

### 异常处理策略

支持多种错误处理策略：

1. **自动重试** - 指数退避重试
2. **技能替代** - 寻找功能相似技能
3. **流程调整** - 调整依赖关系或跳过非关键任务
4. **资源优化** - 调整资源使用策略

### 流程健康度评估

系统自动评估流程健康度：

```python
health = result["process_health"]
# score: 效率评分 (0-1)
# health_status: excellent/good/fair/poor
# bottlenecks: 瓶颈列表
# improvement_suggestions: 改进建议
```

### 模板沉淀和学习

成功执行的流程自动保存为模板：

```python
# 自动创建模板
template = library.create_custom_template(
    user_request, execution_plan, execution_results
)

# 模板包含:
# - 原始请求和上下文
# - 子任务定义和依赖
# - 技能匹配结果
# - 执行统计和成功率
```

## 性能优化

### 内存优化

- 使用延迟加载减少内存占用
- 流式处理大数据集
- 定期清理历史记录

### 执行优化

- 智能缓存频繁使用的模板
- 预编译常用技能配置
- 并行处理独立任务

### 网络优化

- 连接池管理
- 请求合并和批处理
- 失败请求的智能重试

## 扩展开发

### 添加新技能

1. 在 `orchestrator_engine.py` 中添加技能配置：

```python
new_skill = SkillProfile(
    name="新技能名称",
    skill_type=SkillType.NEW_TYPE,
    description="技能描述",
    capabilities=["能力1", "能力2"],
    input_requirements=["输入要求"],
    output_format="输出格式",
    execution_time_estimate={"simple": 60, "medium": 180, "complex": 600},
    success_rate=0.9,
    compatibility=[SkillType.RELATED_TYPE]
)
```

2. 更新技能匹配逻辑

3. 添加相应的错误处理策略

### 创建自定义模板

1. 定义模板结构：

```python
template = TaskTemplate(
    id="custom_template_id",
    name="模板名称",
    category=TemplateCategory.DATA_ANALYSIS,
    description="模板描述",
    complexity="medium",
    typical_scenarios=["场景1", "场景2"],
    subtask_definitions=[...],
    dependencies=[...],
    skill_requirements=[...],
    estimated_time_range={"min": 60, "max": 180},
    success_criteria=[...],
    output_deliverables=[...],
    tags=["标签1", "标签2"]
)
```

2. 添加到模板库

3. 测试模板匹配和执行

### 集成外部系统

1. 实现自定义技能适配器
2. 配置API连接和认证
3. 添加错误处理和监控

## 故障排除

### 常见问题

#### 问题1：技能匹配失败
**症状**: 无法找到合适技能执行子任务
**解决方案**:
- 检查技能配置文件是否完整
- 验证技能类型定义是否正确
- 尝试手动指定技能或使用备选方案

#### 问题2：执行超时
**症状**: 任务执行时间过长或被中断
**解决方案**:
- 检查超时配置是否合理
- 优化任务拆分，减少单个任务复杂度
- 增加系统资源或减少并发度

#### 问题3：内存不足
**症状**: 内存错误或进程被杀死
**解决方案**:
- 减少数据处理批量大小
- 启用流式处理模式
- 增加系统内存或使用磁盘缓存

#### 问题4：依赖循环
**症状**: 任务无法确定执行顺序
**解决方案**:
- 检查任务依赖关系定义
- 移除循环依赖或添加虚拟任务
- 重新设计任务分解策略

### 调试信息

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

查看详细执行信息：

```bash
# 查看系统状态
python scripts/main_orchestrator.py --status --verbose

# 查看错误统计
python -c "from error_handling import ErrorHandler; h=ErrorHandler(); print(h.get_error_statistics())"

# 运行测试用例
python scripts/test_cases.py
```

### 监控指标

关键监控指标：
- 任务成功率 (>90%)
- 平均执行时间 (根据任务类型)
- 错误恢复率 (>80%)
- 模板匹配准确率 (>85%)
- 并行优化效率 (20-50%)

## 最佳实践

### 需求表达

- 明确具体，避免模糊描述
- 包含关键要素：目标、范围、产出物
- 分阶段描述复杂需求

### 技能配置

- 准确描述技能能力和限制
- 合理设置执行时间预估
- 定义清晰的输入输出要求

### 模板设计

- 基于真实成功案例创建模板
- 包含足够的变体和备选方案
- 定期更新和优化模板

### 错误处理

- 为常见错误定义处理策略
- 设置合理的重试次数和延迟
- 记录错误历史用于分析改进

### 性能优化

- 监控关键性能指标
- 定期清理无用数据
- 优化频繁执行的流程

## 资源文件说明

### scripts/ 目录
- `orchestrator_engine.py` - 编排引擎核心
- `template_library.py` - 模板库和管理器
- `error_handling.py` - 错误处理和流程纠正
- `main_orchestrator.py` - 主系统和命令行接口
- `test_cases.py` - 单元测试和集成测试

### references/ 目录
- `usage_examples.md` - 使用示例和最佳实践

### assets/ 目录
- （可选）模板文件、配置示例等

## 版本历史

### v1.0.0 (初始版本)
- 基础编排引擎
- 模板库管理
- 错误处理系统
- 流程纠正机制
- 完整的测试用例

### 规划功能
- 机器学习优化算法
- 实时性能监控面板
- 团队协作和分享功能
- 更丰富的预定义模板库

## 支持与反馈

如有问题或建议，请：
1. 查看详细错误日志
2. 运行测试用例验证功能
3. 检查配置文件和技能定义
4. 参考使用示例和最佳实践

---

**提示**: 本技能设计为高度可扩展的系统，可以根据具体业务需求进行定制和扩展。建议从简单的用例开始，逐步增加复杂功能。