from pydantic import BaseModel, validator
from typing import List, Optional

from pydantic.v1 import Field

from app.models import DeviceType


class DomainAdd(BaseModel):
    domain: str

    @validator("domain")
    def validate_domain(cls, v):
        v = v.strip().lower()
        if not v:
            raise ValueError("Домен не может быть пустым")
        if len(v) > 255:
            raise ValueError("Домен слишком длинный")
        return v


class DomainResponse(BaseModel):
    id: str
    domain: str
    is_verified: bool
    created_at: str
    keywords_count: int


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
    region_type: Optional[str] = None

    class Config:
        from_attributes = True


class BulkKeywordsAdd(BaseModel):
    keywords: List[str] = Field(..., min_items=1, max_items=1000)
    region_id: str
    device_type: str = "desktop"  # Изменить на str вместо DeviceType
    check_frequency: str = "daily"

    @validator("device_type")
    def validate_device_type(cls, v):
        # Конвертируем в нижний регистр и проверяем
        v = v.lower()
        valid_types = ["desktop", "mobile", "tablet"]
        if v not in valid_types:
            raise ValueError(f"device_type должен быть одним из: {valid_types}")
        return v

    @validator("keywords")
    def validate_keywords(cls, v):
        # Очищаем и валидируем ключевые слова
        cleaned_keywords = []
        for keyword in v:
            keyword = keyword.strip()
            if keyword:
                if len(keyword) > 500:
                    raise ValueError(
                        f'Ключевое слово "{keyword[:50]}..." слишком длинное (максимум 500 символов)'
                    )
                cleaned_keywords.append(keyword)

        if not cleaned_keywords:
            raise ValueError("Список ключевых слов не может быть пустым")

        # Проверяем на дубликаты
        unique_keywords = list(set(cleaned_keywords))
        if len(unique_keywords) != len(cleaned_keywords):
            raise ValueError("Обнаружены дубликаты ключевых слов")

        return unique_keywords


# Схемы для загрузки файлов
class TextFileLoad(BaseModel):
    url: str = Field(..., description="URL текстового файла")


class ExcelFileLoad(BaseModel):
    url: str = Field(..., description="URL Excel файла")
    sheet: int = Field(default=1, ge=1, description="Номер листа")
    start_row: int = Field(default=1, ge=1, description="Начальная строка")


class WordFileLoad(BaseModel):
    url: str = Field(..., description="URL Word документа")


class KeywordUpdate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=500)
    region_id: str
    device_type: str = "desktop"
    check_frequency: str = "daily"
    is_active: bool = True

    @validator("device_type")
    def validate_device_type(cls, v):
        v = v.lower()
        valid_types = ["desktop", "mobile", "tablet"]
        if v not in valid_types:
            raise ValueError(f"device_type должен быть одним из: {valid_types}")
        return v

    @validator("keyword")
    def validate_keyword(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Ключевое слово не может быть пустым")
        return v


class BulkEditKeywords(BaseModel):
    added_keywords: List[str] = Field(default_factory=list)
    removed_keywords: List[str] = Field(
        default_factory=list
    )  # IDs ключевых слов для удаления
    new_keywords_settings: Optional[dict] = None


class BulkDeleteKeywords(BaseModel):
    keyword_ids: List[str] = Field(..., min_items=1, max_items=1000)


class KeywordAdd(BaseModel):
    keyword: str
    region_id: str
    device_type: DeviceType = DeviceType.DESKTOP
    check_frequency: str = "daily"
    is_active: bool = True

    @validator("keyword")
    def validate_keyword(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Ключевое слово не может быть пустым")
        if len(v) > 500:
            raise ValueError("Ключевое слово слишком длинное")
        return v
