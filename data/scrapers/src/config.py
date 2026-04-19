from __future__ import annotations

import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DedupConfig(BaseModel):
    ttl_days: int = 7


class PriorityConfig(BaseModel):
    min_year: int = 2024


class PlaywrightConfig(BaseModel):
    headless: bool = True
    timeout: int = 30000


class DownloadKeywordConfig(BaseModel):
    positive: list[str] = Field(
        default_factory=lambda: [
            "tai",
            "tai ve",
            "tai xuong",
            "download",
            "pdf",
            "xem de",
            "file",
            ".pdf",
        ]
    )
    negative: list[str] = Field(
        default_factory=lambda: [
            "dang nhap",
            "quang cao",
            "lien he",
            "gioi thieu",
            "facebook",
            "zalo",
            "share",
            "binh luan",
        ]
    )
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "text": 3.0,
            "href": 4.0,
            "aria_label": 2.0,
            "title": 2.0,
            "class_name": 1.0,
            "element_id": 1.0,
            "nearby_text": 1.5,
        }
    )


class IntentKeywordConfig(BaseModel):
    subjects: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "toan": ["toan", "mon toan"],
            "van": ["van", "ngu van", "nguvan"],
            "anh": ["anh", "tieng anh", "ngoai ngu"],
            "ly": ["ly", "vat ly", "vat li"],
            "hoa": ["hoa", "hoa hoc"],
            "sinh": ["sinh", "sinh hoc"],
            "su": ["su", "lich su"],
            "dia": ["dia", "dia ly"],
            "gdcd": ["gdcd", "giao duc cong dan"],
            "gdktpl": ["gdktpl", "kinh te phap luat", "kinh te va phap luat"],
            "tin": ["tin", "tin hoc"],
            "cong_nghe": ["cong nghe"],
        }
    )
    grades: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "10": ["lop 10", "khoi 10", "10"],
            "11": ["lop 11", "khoi 11", "11"],
            "12": ["lop 12", "khoi 12", "12"],
            "thpt": ["thpt", "tot nghiep", "quoc gia"],
        }
    )
    exam_types: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "giua_hk1": ["giua ky 1", "giua hk1", "giua hoc ky 1", "gk1"],
            "hk1": ["hoc ky 1", "hk1", "ki 1", "ck1"],
            "giua_hk2": ["giua ky 2", "giua hk2", "giua hoc ky 2", "gk2"],
            "hk2": ["hoc ky 2", "hk2", "ki 2", "ck2"],
            "khao_sat": ["khao sat", "khao sat chat luong", "kscl"],
            "hsg": ["hsg", "hoc sinh gioi", "de thi hsg"],
            "thptqg": [
                "thptqg",
                "thpt qg",
                "tnthpt",
                "tot nghiep thpt",
                "thi tot nghiep thpt",
                "thi thpt quoc gia",
            ],
            "thi_thu": ["thi thu"],
            "de_cuong": ["de cuong"],
            "minh_hoa": ["minh hoa"],
        }
    )


class DetectorConfig(BaseModel):
    download_keywords: DownloadKeywordConfig = Field(default_factory=DownloadKeywordConfig)
    intent: IntentKeywordConfig = Field(default_factory=IntentKeywordConfig)
    max_click_attempts: int = 6
    network_wait_ms: int = 2500


class CrawlConfig(BaseModel):
    max_depth: int = 8
    max_pages: int = 500


class Settings(BaseSettings):
    storage_dir: str = "./storage/pdfs"
    data_dir: str = "./storage/state"
    dedup: DedupConfig = Field(default_factory=DedupConfig)
    priority: PriorityConfig = Field(default_factory=PriorityConfig)
    playwright: PlaywrightConfig = Field(default_factory=PlaywrightConfig)
    detectors: DetectorConfig = Field(default_factory=DetectorConfig)
    crawl: CrawlConfig = Field(default_factory=CrawlConfig)

    @classmethod
    def from_yaml(cls, path: str | Path = "config.yaml") -> Settings:
        p = Path(path)
        if p.exists():
            with open(p) as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db_path(self) -> Path:
        return self.data_path / "crawl_cache.db"
