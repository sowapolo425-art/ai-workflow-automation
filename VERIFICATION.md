# 交付与验证记录

日期：2026-10-05 初验、2026-10-06 公网复验（北京时间）。范围：求职作品集，全部客户、邮件和公司均为虚构；真实邮件发送、真实销售通知与真实客户数据不在范围内。

## 已交付

- FastAPI 工作流、SQLite 邮件/审计/模拟通知、四封虚构样本与只读销售工作台。
- 带 token 的本地 Webhook；公网演示模式关闭任意邮件接入，只允许固定样本。
- 可选兼容 OpenAI 的 LLM 做分类和诉求句选择；优先级按时限规则判定，回复由模板生成并等待人工审核。模型结果无效时记录规则回退。
- Dockerfile、Compose、本地测试、架构说明、运维与回退说明、面试提纲及真实页面截图。
- 广州服务器独立目录和 systemd 服务，复用项目 A 已有的本地 Qwen 接口，不启动第二份模型。

## 可重复的验证

| 检查 | 结果 |
| --- | --- |
| Windows 本地 `pytest -q` | **5 passed**；覆盖四类场景、端到端记录、重启后 SQLite 持久化、幂等、Webhook 鉴权与冲突、模型原句映射、类别规范化与无依据回退。另有 1 条依赖库弃用警告。 |
| Docker Compose | `config --quiet` 通过；使用本机缓存的 `python:3.11-slim` 完成镜像构建；容器启动后 API 可用。强制重建容器后记录数仍为 1，重复样本返回 `duplicate=true`。 |
| 本地页面 | Edge 实际渲染并保存 `screenshot.png`；页面显示流程、四封样本、销售工作台、模式与无外发标记。 |
| 云端资源隔离 | 部署前确认 `/home/ubuntu/apps/ai-workflow-automation`、`flowdesk.service`、8766 端口均未占用；磁盘可用约 22 GiB，内存可用约 1.8 GiB。B 使用独立目录、端口和服务。 |
| 云端服务 | `flowdesk.service`、`ai-rag-kb.service`、`ai-rag-llm.service` 均为 `active`；B 重启后 `email_count=4`，项目 A 的 `/api/status` 仍为 semantic/llm、文档数 1、只读。 |
| 云端四个真实处理回合 | 报价：报价咨询/中/`LLM 提取 + 类别规范化`；故障：技术支持/高/`LLM 分类/提取`；合作：商务合作/低/`LLM 分类/提取`；一般：一般咨询/低/`规则回退`。四条均 complete、有原文需求证据、草稿和模拟通知，`sent=false`。 |
| 云端重复投递与公开边界 | 报价再次提交返回同一 ID、`duplicate=true`；公网模式对有效任意邮件 Webhook 返回 403。 |
| 腾讯云防火墙 | 2026-10-06 在实例 `lhins-k80348lj` 的防火墙列表核对到新增规则：全部 IPv4 地址、TCP、8766、允许，备注“Flowdesk 项目 B 虚构样本演示”；原有 22/TCP、80/TCP、ICMP 规则仍在。 |
| 公网页面与 API | Windows 绕过代理直连 `http://139.199.90.153:8766/` 与 `/api/status` 均为 HTTP 200；Codex 浏览器实际渲染页面，显示 4 条已记录邮件、4 个完成流程、4 份待审核草稿、0 次真实外发。状态为 `demo_mode=true`、`email_count=4`、两项外发标记均为 `false`。 |
| 公网样本与边界 | `/api/samples` 返回四个预置样本；`/api/emails` 返回 4 条 complete 记录，四条详情均有原文证据、草稿和未发送的模拟通知。再次运行报价样本返回 `duplicate=true`、原 ID 1；向 `/api/webhook/email` 提交虚构测试邮件返回 HTTP 403。 |
| 项目 A 隔离复验 | 公网 `http://139.199.90.153/api/status` 为 HTTP 200，仍是 semantic/llm、文档数 1、只读；服务器内 `flowdesk.service`、`ai-rag-kb.service`、`ai-rag-llm.service` 均为 active。 |

公网浏览器截图见 [public-demo-20261006.jpg](public-demo-20261006.jpg)，腾讯云规则端口列截图见 [firewall-rule-20261006.jpg](firewall-rule-20261006.jpg)。

## 云端回退点

| 文件 | SHA-256 |
| --- | --- |
| `/home/ubuntu/apps/ai-workflow-automation/backups/workflow-final-20261005.sqlite3` | `8033eba72ef86751e592a9af03cee6a2ded66cde31c651365b8b4de01148f534` |
| 当前 `app/pipeline.py` | `435e6603a39962705a341f837a9d37224566de909ce870b6e4b79607951b8adb` |

旧版模型路径的数据库与源码也保留在同目录 `backups/`。回退方法见 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 公开交付与边界

- 独立 GitHub 仓库已于 2026-10-06 发布：[sowapolo425-art/ai-workflow-automation](https://github.com/sowapolo425-art/ai-workflow-automation)。发布前检查了跟踪文件与密钥相关文本；`.env`、数据库和运行数据不在仓库中。
- 当前服务器仅有 IP/HTTP，没有域名与 HTTPS；公开演示只能使用虚构样本。
