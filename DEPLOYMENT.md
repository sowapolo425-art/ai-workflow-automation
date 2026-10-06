# 广州云服务器部署与维护

本项目使用独立目录 `/home/ubuntu/apps/ai-workflow-automation`、独立服务 `flowdesk.service`、独立端口 `8766`。项目 A 的目录、80 端口服务和 8780 模型服务不需要修改。公开实例只运行四封虚构样本，Webhook 禁用。

## 环境

服务器：`gz-dev`（广州）。Python 3.11+、可访问 PyPI。`deploy/flowdesk.service` 是 systemd 模板。服务启动需 `.env` 文件：

```dotenv
DATA_DIR=/home/ubuntu/apps/ai-workflow-automation/data
DEMO_MODE=true
WEBHOOK_TOKEN=
OPENAI_BASE_URL=http://127.0.0.1:8780/v1
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=qwen2.5-1.5b-instruct-q4_k_m
```

此配置复用服务器已有的本地 Qwen 接口，不启动第二个模型。若模型不可用或结果校验失败，记录会明确显示“规则回退”。不要把真实密钥或客户资料写入公开仓库。云端 `.env` 仅在服务器，权限 600。

## 检查

```bash
systemctl is-active flowdesk.service ai-rag-kb.service ai-rag-llm.service
curl -fsS http://127.0.0.1:8766/api/status
curl -fsS http://127.0.0.1:8766/api/emails
sudo journalctl -u flowdesk.service -n 50 --no-pager
ss -ltn | grep 8766
```

公网演示地址：[http://139.199.90.153:8766/](http://139.199.90.153:8766/)。当前只有 IP/HTTP，没有域名与 HTTPS，只能用于虚构数据演示。

2026-10-06，在腾讯云轻量服务器实例 `lhins-k80348lj` 的“防火墙”中新增 **TCP 8766、全部 IPv4 地址、允许** 入站规则，备注为“Flowdesk 项目 B 虚构样本演示”；原有 22/TCP、80/TCP 和 ICMP 规则保留。随后从 Windows 绕过代理直连，页面、`/api/status`、四个样本记录与详情均返回正常；公网浏览器也实际渲染出页面。重复运行报价样本返回原记录，公网模式的任意邮件 Webhook 返回 403。项目 A 的公网状态接口和三个 systemd 服务复查正常。完整验收见 [VERIFICATION.md](VERIFICATION.md)。

## 更新与回退

更新前先备份应用目录的 `app/`、`requirements.txt` 和 `data/workflow.sqlite3`，记录备份校验和。新版本在独立目录验证测试后再替换源码并重启 `flowdesk.service`。回退时停止该服务，恢复备份的源码与数据库，然后启动并检查状态、四个场景及重复投递。无需重启项目 A 或本地模型。不要在服务器执行 `docker compose down -v`；云端使用 systemd，不依赖本地 Docker volume。
