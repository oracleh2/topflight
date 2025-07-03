import random
import hashlib
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
from app.models.profile import DeviceType


class FingerprintGenerator:
    """Генератор реалистичных browser fingerprints для разных типов устройств"""

    # Desktop разрешения
    DESKTOP_SCREEN_RESOLUTIONS = [
        (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
        (1280, 1024), (1680, 1050), (2560, 1440), (1600, 900),
        (1280, 720), (1024, 768)
    ]

    # Mobile разрешения (популярные смартфоны)
    MOBILE_SCREEN_RESOLUTIONS = [
        (375, 667),  # iPhone 6/7/8
        (414, 896),  # iPhone XR/11
        (390, 844),  # iPhone 12/13
        (393, 851),  # iPhone 14
        (360, 640),  # Samsung Galaxy S
        (412, 892),  # Samsung Galaxy S20
        (384, 854),  # Google Pixel
        (393, 873),  # OnePlus
        (375, 812),  # iPhone X/XS
        (428, 926),  # iPhone 12 Pro Max
    ]

    # Desktop User Agents
    DESKTOP_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]

    # Mobile User Agents
    MOBILE_USER_AGENTS = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; OnePlus 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    ]

    # Mobile WebGL рендереры
    MOBILE_WEBGL_RENDERERS = [
        "Adreno (TM) 660",
        "Adreno (TM) 640",
        "Mali-G78 MP20",
        "Apple A15 GPU",
        "Apple A14 GPU",
        "Mali-G77 MP11",
        "PowerVR GT7600 Plus",
    ]

    @classmethod
    def generate_realistic_fingerprint(cls, device_type: DeviceType = DeviceType.DESKTOP) -> Dict[str, Any]:
        """Генерирует реалистичный fingerprint для указанного типа устройства"""

        if device_type == DeviceType.MOBILE:
            return cls._generate_mobile_fingerprint()
        else:
            return cls._generate_desktop_fingerprint()

    @classmethod
    def _generate_desktop_fingerprint(cls) -> Dict[str, Any]:
        """Генерирует fingerprint для desktop устройства"""
        screen_width, screen_height = random.choice(cls.DESKTOP_SCREEN_RESOLUTIONS)
        user_agent = random.choice(cls.DESKTOP_USER_AGENTS)
        timezone_info = random.choice(cls.RUSSIAN_TIMEZONES)

        browser_info = cls._parse_user_agent(user_agent)

        fingerprint = {
            "device_type": "desktop",
            "browser": browser_info,
            "screen": cls._generate_desktop_screen_info(screen_width, screen_height),
            "viewport": cls._generate_desktop_viewport_info(screen_width, screen_height),
            "timezone": cls._generate_timezone_info(timezone_info),
            "webgl": cls._generate_desktop_webgl_info(),
            "canvas": cls._generate_canvas_info(),
            "audio": cls._generate_audio_info(),
            "fonts": cls._generate_desktop_fonts_list(),
            "plugins": cls._generate_plugins_list(browser_info["name"]),
            "hardware": cls._generate_desktop_hardware_info(),
            "webrtc": {"local_ips": [], "stun_connectivity": False},
            "apis": cls._generate_desktop_apis_info(),
            "network": cls._generate_network_info(),
            "touch": cls._generate_desktop_touch_info()
        }

        return fingerprint

    @classmethod
    def _generate_mobile_fingerprint(cls) -> Dict[str, Any]:
        """Генерирует fingerprint для mobile устройства"""
        screen_width, screen_height = random.choice(cls.MOBILE_SCREEN_RESOLUTIONS)
        user_agent = random.choice(cls.MOBILE_USER_AGENTS)
        timezone_info = random.choice(cls.RUSSIAN_TIMEZONES)

        browser_info = cls._parse_mobile_user_agent(user_agent)

        fingerprint = {
            "device_type": "mobile",
            "browser": browser_info,
            "screen": cls._generate_mobile_screen_info(screen_width, screen_height),
            "viewport": cls._generate_mobile_viewport_info(screen_width, screen_height),
            "timezone": cls._generate_timezone_info(timezone_info),
            "webgl": cls._generate_mobile_webgl_info(),
            "canvas": cls._generate_canvas_info(),
            "audio": cls._generate_mobile_audio_info(),
            "fonts": cls._generate_mobile_fonts_list(),
            "plugins": [],  # На мобильных обычно нет плагинов
            "hardware": cls._generate_mobile_hardware_info(),
            "webrtc": {"local_ips": [], "stun_connectivity": False},
            "apis": cls._generate_mobile_apis_info(),
            "network": cls._generate_mobile_network_info(),
            "touch": cls._generate_mobile_touch_info()
        }

        return fingerprint

    @classmethod
    def _parse_mobile_user_agent(cls, user_agent: str) -> Dict[str, Any]:
        """Парсит мобильный User Agent"""
        if "iPhone" in user_agent:
            browser_name = "Safari"
            platform = "iPhone"
            vendor = "Apple Computer, Inc."
        elif "Android" in user_agent and "Chrome" in user_agent:
            browser_name = "Chrome"
            platform = "Linux armv7l"
            vendor = "Google Inc."
        else:
            browser_name = "Chrome"
            platform = "Linux armv7l"
            vendor = "Google Inc."

        version = cls._extract_version(user_agent, f"{browser_name}/") if "Chrome" in user_agent else "17.1"

        return {
            "name": browser_name,
            "version": version,
            "user_agent": user_agent,
            "vendor": vendor,
            "platform": platform,
            "language": "ru-RU",
            "languages": ["ru-RU", "ru", "en-US", "en"]
        }

    @classmethod
    def _generate_mobile_screen_info(cls, width: int, height: int) -> Dict[str, Any]:
        """Генерирует информацию об экране мобильного устройства"""
        # Мобильные устройства часто имеют высокую плотность пикселей
        device_pixel_ratio = random.choice([2.0, 3.0, 2.625, 2.75, 3.5])

        return {
            "width": width,
            "height": height,
            "color_depth": 24,
            "pixel_depth": 24,
            "available_width": width,
            "available_height": height,
            "device_pixel_ratio": device_pixel_ratio,
            "orientation": random.choice(["portrait-primary", "portrait-secondary"])
        }

    @classmethod
    def _generate_mobile_viewport_info(cls, screen_width: int, screen_height: int) -> Dict[str, Any]:
        """Генерирует информацию о viewport мобильного браузера"""
        # На мобильных viewport обычно равен размеру экрана
        return {
            "width": screen_width,
            "height": screen_height - random.randint(50, 100),  # учитываем браузерную панель
            "inner_width": screen_width,
            "inner_height": screen_height - random.randint(50, 100),
            "outer_width": screen_width,
            "outer_height": screen_height
        }

    @classmethod
    def _generate_mobile_webgl_info(cls) -> Dict[str, Any]:
        """Генерирует WebGL информацию для мобильного устройства"""
        renderer = random.choice(cls.MOBILE_WEBGL_RENDERERS)

        return {
            "vendor": "WebKit",
            "renderer": renderer,
            "version": "WebGL 1.0",
            "shading_language_version": "WebGL GLSL ES 1.0"
        }

    @classmethod
    def _generate_mobile_hardware_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о железе мобильного устройства"""
        return {
            "concurrency": random.choice([4, 6, 8]),  # мобильные обычно имеют меньше ядер
            "memory": random.choice([3, 4, 6, 8, 12]),  # GB
            "touch_support": True,
            "max_touch_points": random.choice([5, 10])
        }

    @classmethod
    def _generate_mobile_touch_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о touch для мобильного устройства"""
        return {
            "touch_support": True,
            "max_touch_points": random.choice([5, 10]),
            "touch_event": True,
            "ontouchstart": True
        }

    @classmethod
    def _generate_desktop_touch_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о touch для desktop устройства"""
        return {
            "touch_support": False,
            "max_touch_points": 0,
            "touch_event": False,
            "ontouchstart": False
        }

    @classmethod
    def _generate_mobile_fonts_list(cls) -> List[str]:
        """Генерирует список шрифтов для мобильного устройства"""
        # Мобильные устройства обычно имеют ограниченный набор шрифтов
        mobile_fonts = [
            "Arial", "Helvetica", "Times", "Courier", "Verdana", "Georgia",
            "Palatino", "Garamond", "Bookman", "Trebuchet MS", "Arial Black",
            "Impact", "Sans-serif", "Serif", "Monospace"
        ]
        return mobile_fonts

    @classmethod
    def _generate_desktop_fonts_list(cls) -> List[str]:
        """Генерирует список шрифтов для desktop устройства"""
        return random.sample(cls.COMMON_FONTS, random.randint(15, len(cls.COMMON_FONTS)))

    @classmethod
    def _generate_mobile_audio_info(cls) -> Dict[str, Any]:
        """Генерирует Audio fingerprint для мобильного устройства"""
        fingerprint = round(random.uniform(35.0, 45.0), 14)  # мобильные дают другие значения
        return {
            "fingerprint": str(fingerprint),
            "sample_rate": 44100,  # стандартно для мобильных
            "max_channel_count": 2
        }

    @classmethod
    def _generate_mobile_network_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о сети для мобильного устройства"""
        return {
            "connection_type": random.choice(["cellular", "wifi"]),
            "effective_type": random.choice(["3g", "4g", "5g"]),
            "downlink": random.uniform(1.0, 100.0),
            "rtt": random.randint(20, 200)
        }

    @classmethod
    def _generate_mobile_apis_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о доступных API для мобильного устройства"""
        return {
            "webdriver": False,
            "automation": False,
            "notification": random.choice(["default", "granted", "denied"]),
            "geolocation": random.choice(["prompt", "granted"]),  # на мобильных чаще granted
            "camera": random.choice(["prompt", "granted"]),
            "microphone": random.choice(["prompt", "granted"]),
            "accelerometer": "granted",  # специфично для мобильных
            "gyroscope": "granted",
            "magnetometer": "granted"
        }

    # ... остальные методы остаются такими же

    @classmethod
    def create_browser_settings(cls, fingerprint: Dict[str, Any]) -> Dict[str, Any]:
        """Создает настройки браузера на основе fingerprint"""
        device_type = fingerprint.get("device_type", "desktop")

        base_settings = {
            "viewport": {
                "width": fingerprint["viewport"]["width"],
                "height": fingerprint["viewport"]["height"]
            },
            "user_agent": fingerprint["browser"]["user_agent"],
            "locale": fingerprint["browser"]["language"],
            "timezone_id": fingerprint["timezone"]["timezone"],
            "device_scale_factor": fingerprint["screen"]["device_pixel_ratio"],
            "has_touch": fingerprint["touch"]["touch_support"],
            "color_scheme": "light",
            "reduced_motion": "no-preference",
            "forced_colors": "none"
        }

        if device_type == "mobile":
            # Дополнительные настройки для мобильных
            base_settings.update({
                "is_mobile": True,
                "touch_support": True,
                "mobile_emulation": {
                    "device_name": cls._get_mobile_device_name(fingerprint),
                }
            })

        return base_settings

    @classmethod
    def _get_mobile_device_name(cls, fingerprint: Dict[str, Any]) -> str:
        """Определяет название мобильного устройства по fingerprint"""
        user_agent = fingerprint["browser"]["user_agent"]

        if "iPhone" in user_agent:
            if "iPhone OS 17" in user_agent:
                return "iPhone 14"
            elif "iPhone OS 16" in user_agent:
                return "iPhone 13"
            else:
                return "iPhone 12"
        elif "Samsung" in user_agent:
            return "Galaxy S21"
        elif "Pixel" in user_agent:
            return "Pixel 6"
        else:
            return "Generic Mobile"