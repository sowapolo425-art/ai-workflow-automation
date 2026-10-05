"""Invented customer messages. No live inbox or customer information."""

SAMPLES = [
    {
        "id": "pricing",
        "message_id": "demo-pricing-001",
        "from_name": "林若晴（虚构）",
        "from_email": "lin.ruoqing@example.com",
        "subject": "团队版报价与试用咨询",
        "body": "你好，我们的虚构设计团队有 25 人，想了解团队版的年度报价和是否可以安排 14 天试用。希望本周五前收到方案，方便下周内部讨论。谢谢！",
    },
    {
        "id": "support",
        "message_id": "demo-support-002",
        "from_name": "周启明（虚构）",
        "from_email": "zhou.qiming@example.com",
        "subject": "导出功能出现错误",
        "body": "你好，今天我们在导出项目报表时一直提示错误，已重试三次。虚构团队明天上午要做汇报，请尽快协助排查。我们使用的是浏览器网页版。",
    },
    {
        "id": "partnership",
        "message_id": "demo-partner-003",
        "from_name": "陈一帆（虚构）",
        "from_email": "chen.yifan@example.com",
        "subject": "渠道合作意向",
        "body": "你好，我们是一家虚构的企业服务公司，想探讨渠道合作以及联合举办线上分享会。请介绍合作流程，方便我们安排一次沟通。",
    },
    {
        "id": "general",
        "message_id": "demo-general-004",
        "from_name": "许嘉宁（虚构）",
        "from_email": "xu.jianing@example.com",
        "subject": "产品资料咨询",
        "body": "你好，我想先了解产品的主要功能和适用场景。请发一份公开产品介绍，之后再决定是否深入交流。",
    },
]

SAMPLE_BY_ID = {sample["id"]: sample for sample in SAMPLES}
