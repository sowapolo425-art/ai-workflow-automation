from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    demo_mode: bool
    webhook_token: str
    openai_base_url: str
    openai_api_key: str
    openai_chat_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            data_dir=Path(os.getenv("DATA_DIR", "data")),
            demo_mode=os.getenv("DEMO_MODE", "true").lower() == "true",
            webhook_token=os.getenv("WEBHOOK_TOKEN", ""),
            openai_base_url=os.getenv("OPENAI_BASE_URL", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", ""),
        )

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_base_url and self.openai_chat_model)
