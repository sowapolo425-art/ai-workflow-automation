# 架构与处理约束

## 数据流

预置样本或本地带 token 的 Webhook 提交邮件。API 按 `message_id` 先写入 `emails`，再执行分析和草稿生成。结果更新到同一条邮件，需求以 JSON 保存，并新增一条 `notifications` 模拟通知。`events` 独立记录 received、classified、extracted、drafted、notified；LLM 失败时增加 fallback。所有表在同一 SQLite 文件，最终结果与通知在同一事务提交。

## 为什么这么设计

- **去重**：数据库唯一约束是最终裁决。重复投递返回已有结果；同 ID 不同内容返回冲突，避免覆盖。
- **可查证**：LLM 只能从编号的邮件原句中选择需求；代码把编号映射回原句作为 `need` 和 `evidence`，界面并列展示。此规则只保证证据存在，不保证模型的选择一定正确。
- **模型回退**：模型不可用、JSON 无效、类别超范围、选择的编号无效等情况会切到本地规则。优先级始终由时限关键词规则判定。记录中的 `analysis_mode` 和 `fallback` 事件标识真实执行路径。
- **人工控制**：回复由模板自动生成并只存草稿；通知只写入数据库，`sent=false`。代码中没有 SMTP、邮件平台或销售平台发送器。
- **演示隔离**：公开默认只允许四个固定样本。Webhook 在公开模式关闭；请求体、字段长度和操作频率受限。页面内容经 HTML 转义。

## 数据模型

| 表 | 关键字段 | 用途 |
| --- | --- | --- |
| `emails` | `message_id`、正文、类别、优先级、需求 JSON、草稿、模式、状态 | 主记录 |
| `events` | `email_id`、stage、detail、时间 | 审计流水 |
| `notifications` | `email_id`、channel、recipient、content、`sent=0` | 模拟销售通知 |

SQLite 适合单实例作品集。生产化需要外部队列与任务重试、多用户权限、隐私与保留策略、审计保护、数据库迁移、并发与外部集成测试。当前同步 LLM 请求最多等待 45 秒；重复请求在首个请求处理期间可能先看到 `processing`，之后查询详情即可看到最终状态。
