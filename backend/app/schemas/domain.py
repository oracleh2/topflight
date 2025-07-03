from pydantic import BaseModel, validator
from typing import List, Optional
from app.models import DeviceType


class DomainAdd(BaseModel):
    domain: str

    @validator('domain')
    def validate_domain(cls, v):
        v = v.strip().lower()
        if not v:
            raise ValueError('Домен не может быть пустым')
        if len(v) > 255:
            raise ValueError('Домен слишком длинный')
        return v


class DomainResponse(BaseModel):
    id: str
    domain: str
    is_verified: bool
    created_at: str
    keywords_count: int


class KeywordAdd(BaseModel):
    keyword: str
    region_id: str
    device_type: DeviceType = DeviceType.DESKTOP
    check_frequency: str = "daily"

    @validator('keyword')
    def validate_keyword(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Ключевое слово не может быть пустым')
        if len(v) > 500:
            raise ValueError('Ключевое слово слишком длинное')
        return v


class KeywordResponse(BaseModel):
    id: str
    keyword: str
    region: dict
    device_type: str
    is_active: bool
    check_frequency: str
    created_at: str


class RegionResponse(BaseModel):
    id: str
    code: str
    name: str
    country_code: str