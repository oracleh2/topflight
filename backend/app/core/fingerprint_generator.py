import random
import hashlib
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

from sqlalchemy.sql.coercions import cls

from app.models.profile import DeviceType


class FingerprintGenerator:
    """Генератор реалистичных browser fingerprints для разных типов устройств"""

    # Desktop разрешения
    DESKTOP_SCREEN_RESOLUTIONS = [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1280, 1024),
        (1680, 1050),
        (2560, 1440),
        (1600, 900),
        (1280, 720),
        (1024, 768),
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

    # Tablet разрешения
    TABLET_SCREEN_RESOLUTIONS = [
        (1024, 1366),  # iPad Pro
        (768, 1024),  # iPad standard
        (820, 1180),  # iPad Air
        (744, 1133),  # iPad Mini
        (800, 1280),  # Android tablets
        (962, 1280),  # Samsung Galaxy Tab
        (1200, 1920),  # Samsung Galaxy Tab S
        (1024, 1600),  # Nexus 10
        (1536, 2048),  # iPad Pro 12.9"
        (834, 1194),  # iPad Pro 11"
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

    # Российские часовые пояса
    RUSSIAN_TIMEZONES = [
        {
            "timezone": "Europe/Moscow",
            "offset": 180,  # UTC+3
            "name": "Москва",
            "abbreviation": "MSK",
        },
        {
            "timezone": "Europe/Samara",
            "offset": 240,  # UTC+4
            "name": "Самара",
            "abbreviation": "SAMT",
        },
        {
            "timezone": "Asia/Yekaterinburg",
            "offset": 300,  # UTC+5
            "name": "Екатеринбург",
            "abbreviation": "YEKT",
        },
        {
            "timezone": "Asia/Omsk",
            "offset": 360,  # UTC+6
            "name": "Омск",
            "abbreviation": "OMST",
        },
        {
            "timezone": "Asia/Krasnoyarsk",
            "offset": 420,  # UTC+7
            "name": "Красноярск",
            "abbreviation": "KRAT",
        },
        {
            "timezone": "Asia/Irkutsk",
            "offset": 480,  # UTC+8
            "name": "Иркутск",
            "abbreviation": "IRKT",
        },
        {
            "timezone": "Asia/Yakutsk",
            "offset": 540,  # UTC+9
            "name": "Якутск",
            "abbreviation": "YAKT",
        },
        {
            "timezone": "Asia/Vladivostok",
            "offset": 600,  # UTC+10
            "name": "Владивосток",
            "abbreviation": "VLAT",
        },
        {
            "timezone": "Asia/Magadan",
            "offset": 660,  # UTC+11
            "name": "Магадан",
            "abbreviation": "MAGT",
        },
        {
            "timezone": "Asia/Kamchatka",
            "offset": 720,  # UTC+12
            "name": "Камчатка",
            "abbreviation": "PETT",
        },
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

    # ===================== ОСНОВНЫЕ МЕТОДЫ =====================

    @classmethod
    def generate_realistic_fingerprint(
        cls, device_type: DeviceType = DeviceType.DESKTOP
    ) -> Dict[str, Any]:
        """Генерирует реалистичный fingerprint для указанного типа устройства"""
        if device_type == DeviceType.MOBILE:
            return cls._generate_mobile_fingerprint()
        elif device_type == DeviceType.TABLET:
            return cls._generate_tablet_fingerprint()
        else:  # DeviceType.DESKTOP
            return cls._generate_desktop_fingerprint()

    # @classmethod
    # def create_browser_settings(cls, fingerprint: Dict[str, Any]) -> Dict[str, Any]:
    #     """Создает настройки браузера на основе fingerprint"""
    #     device_type = fingerprint.get("device_type", "desktop")
    #
    #     base_settings = {
    #         "viewport": {
    #             "width": fingerprint["viewport"]["width"],
    #             "height": fingerprint["viewport"]["height"],
    #         },
    #         "user_agent": fingerprint["browser"]["user_agent"],
    #         "locale": fingerprint["browser"]["language"],
    #         "timezone_id": fingerprint["timezone"]["timezone"],
    #         "device_scale_factor": fingerprint["screen"]["device_pixel_ratio"],
    #         "has_touch": fingerprint["touch"]["touch_support"],
    #         "color_scheme": "light",
    #         "reduced_motion": "no-preference",
    #         "forced_colors": "none",
    #     }
    #
    #     if device_type == "mobile":
    #         base_settings.update(
    #             {
    #                 "is_mobile": True,
    #                 "touch_support": True,
    #                 "mobile_emulation": {
    #                     "device_name": cls._get_mobile_device_name(fingerprint),
    #                 },
    #             }
    #         )
    #
    #     return base_settings

    # ===================== ГЕНЕРАЦИЯ FINGERPRINT =====================

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
            "viewport": cls._generate_desktop_viewport_info(
                screen_width, screen_height
            ),
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
            "touch": cls._generate_desktop_touch_info(),
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
            "touch": cls._generate_mobile_touch_info(),
        }

        return fingerprint

    # ===================== ПАРСИНГ USER AGENT =====================

    @classmethod
    def _parse_user_agent(cls, user_agent: str) -> Dict[str, Any]:
        """Парсит User Agent для получения информации о браузере"""
        browser_info = {
            "user_agent": user_agent,
            "name": "Chrome",
            "version": "120.0.0.0",
            "platform": "Win32",
            "vendor": "Google Inc.",
            "language": "ru-RU",
            "languages": ["ru-RU", "ru", "en-US", "en"],
        }

        # Простая логика парсинга User Agent
        if "Chrome" in user_agent:
            browser_info["name"] = "Chrome"
            browser_info["vendor"] = "Google Inc."
        elif "Firefox" in user_agent:
            browser_info["name"] = "Firefox"
            browser_info["vendor"] = "Mozilla Foundation"
        elif "Safari" in user_agent and "Chrome" not in user_agent:
            browser_info["name"] = "Safari"
            browser_info["vendor"] = "Apple Computer, Inc."

        if "Mac OS X" in user_agent:
            browser_info["platform"] = "MacIntel"
        elif "Windows" in user_agent:
            browser_info["platform"] = "Win32"
        elif "Linux" in user_agent:
            browser_info["platform"] = "Linux x86_64"

        return browser_info

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

        version = (
            cls._extract_version(user_agent, f"{browser_name}/")
            if "Chrome" in user_agent
            else "17.1"
        )

        return {
            "name": browser_name,
            "version": version,
            "user_agent": user_agent,
            "vendor": vendor,
            "platform": platform,
            "language": "ru-RU",
            "languages": ["ru-RU", "ru", "en-US", "en"],
        }

    @classmethod
    def _extract_version(cls, user_agent: str, prefix: str) -> str:
        """Извлекает версию браузера из User Agent"""
        try:
            start = user_agent.index(prefix) + len(prefix)
            end = user_agent.index(" ", start)
            return user_agent[start:end]
        except ValueError:
            return "120.0.0.0"

    # ===================== ГЕНЕРАЦИЯ SCREEN INFO =====================

    @classmethod
    def _generate_desktop_screen_info(cls, width: int, height: int) -> Dict[str, Any]:
        """Генерирует информацию о экране для desktop"""
        return {
            "width": width,
            "height": height,
            "available_width": width,
            "available_height": height - 40,  # Учитываем панель задач
            "color_depth": 24,
            "pixel_depth": 24,
            "device_pixel_ratio": random.choice([1, 1.25, 1.5, 2]),
        }

    @classmethod
    def _generate_mobile_screen_info(cls, width: int, height: int) -> Dict[str, Any]:
        """Генерирует информацию об экране мобильного устройства"""
        device_pixel_ratio = random.choice([2.0, 3.0, 2.625, 2.75, 3.5])

        return {
            "width": width,
            "height": height,
            "color_depth": 24,
            "pixel_depth": 24,
            "available_width": width,
            "available_height": height,
            "device_pixel_ratio": device_pixel_ratio,
            "orientation": random.choice(["portrait-primary", "portrait-secondary"]),
        }

    # ===================== ГЕНЕРАЦИЯ VIEWPORT INFO =====================

    @classmethod
    def _generate_desktop_viewport_info(
        cls, screen_width: int, screen_height: int
    ) -> Dict[str, Any]:
        """Генерирует информацию о viewport для desktop"""
        viewport_width = screen_width - random.randint(0, 100)
        viewport_height = screen_height - random.randint(100, 200)

        return {
            "width": viewport_width,
            "height": viewport_height,
            "inner_width": viewport_width,
            "inner_height": viewport_height,
            "outer_width": screen_width,
            "outer_height": screen_height,
        }

    @classmethod
    def _generate_mobile_viewport_info(
        cls, screen_width: int, screen_height: int
    ) -> Dict[str, Any]:
        """Генерирует информацию о viewport мобильного браузера"""
        return {
            "width": screen_width,
            "height": screen_height
            - random.randint(50, 100),  # учитываем браузерную панель
            "inner_width": screen_width,
            "inner_height": screen_height - random.randint(50, 100),
            "outer_width": screen_width,
            "outer_height": screen_height,
        }

    # ===================== ГЕНЕРАЦИЯ TIMEZONE INFO =====================

    @classmethod
    def _generate_timezone_info(cls, timezone_info: Dict[str, Any]) -> Dict[str, Any]:
        """Генерирует информацию о временной зоне"""
        return {
            "timezone": timezone_info["timezone"],
            "offset": timezone_info["offset"],
            "name": timezone_info["name"],
            "abbreviation": timezone_info["abbreviation"],
            "dst": False,  # В России DST не используется с 2011 года
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ===================== ГЕНЕРАЦИЯ WEBGL INFO =====================

    @classmethod
    def _generate_desktop_webgl_info(cls) -> Dict[str, Any]:
        """Генерирует WebGL информацию для desktop"""
        return {
            "vendor": "Google Inc.",
            "renderer": "ANGLE (Intel, Intel(R) HD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "version": "OpenGL ES 2.0 (ANGLE 2.1.0)",
            "shading_language_version": "OpenGL ES GLSL ES 1.00 (ANGLE 2.1.0)",
            "max_texture_size": 16384,
            "max_viewport_dims": [16384, 16384],
            "supported_extensions": [
                "ANGLE_instanced_arrays",
                "EXT_blend_minmax",
                "EXT_color_buffer_half_float",
                "EXT_disjoint_timer_query",
                "EXT_frag_depth",
                "EXT_shader_texture_lod",
                "EXT_texture_compression_s3tc",
                "EXT_texture_filter_anisotropic",
                "WEBKIT_EXT_texture_filter_anisotropic",
                "EXT_sRGB",
                "OES_element_index_uint",
                "OES_standard_derivatives",
                "OES_texture_float",
                "OES_texture_float_linear",
                "OES_texture_half_float",
                "OES_texture_half_float_linear",
                "OES_vertex_array_object",
                "WEBGL_color_buffer_float",
                "WEBGL_compressed_texture_s3tc",
                "WEBGL_debug_renderer_info",
                "WEBGL_debug_shaders",
                "WEBGL_depth_texture",
                "WEBGL_draw_buffers",
                "WEBGL_lose_context",
            ],
        }

    @classmethod
    def _generate_mobile_webgl_info(cls) -> Dict[str, Any]:
        """Генерирует WebGL информацию для мобильного устройства"""
        renderer = random.choice(cls.MOBILE_WEBGL_RENDERERS)

        return {
            "vendor": "WebKit",
            "renderer": renderer,
            "version": "WebGL 1.0",
            "shading_language_version": "WebGL GLSL ES 1.0",
            "max_texture_size": 4096,
            "max_viewport_dims": [4096, 4096],
            "supported_extensions": [
                "EXT_blend_minmax",
                "EXT_color_buffer_half_float",
                "EXT_disjoint_timer_query",
                "EXT_frag_depth",
                "EXT_shader_texture_lod",
                "EXT_texture_filter_anisotropic",
                "OES_element_index_uint",
                "OES_standard_derivatives",
                "OES_texture_float",
                "OES_texture_float_linear",
                "OES_texture_half_float",
                "OES_texture_half_float_linear",
                "OES_vertex_array_object",
                "WEBGL_color_buffer_float",
                "WEBGL_debug_renderer_info",
                "WEBGL_debug_shaders",
                "WEBGL_depth_texture",
                "WEBGL_lose_context",
            ],
        }

    # ===================== ГЕНЕРАЦИЯ CANVAS, AUDIO =====================

    @classmethod
    def _generate_canvas_info(cls) -> Dict[str, Any]:
        """Генерирует Canvas fingerprint"""
        canvas_hash = hashlib.md5(str(random.random()).encode()).hexdigest()
        return {
            "hash": canvas_hash,
            "supported": True,
            "context_2d": True,
            "context_webgl": True,
        }

    @classmethod
    def _generate_audio_info(cls) -> Dict[str, Any]:
        """Генерирует Audio fingerprint"""
        return {
            "context_supported": True,
            "fingerprint": hashlib.md5(str(random.random()).encode()).hexdigest(),
            "sample_rate": 48000,
            "buffer_size": 4096,
        }

    @classmethod
    def _generate_mobile_audio_info(cls) -> Dict[str, Any]:
        """Генерирует Audio fingerprint для мобильного устройства"""
        fingerprint = round(random.uniform(35.0, 45.0), 14)
        return {
            "context_supported": True,
            "fingerprint": str(fingerprint),
            "sample_rate": 44100,
            "buffer_size": 2048,
            "max_channel_count": 2,
        }

    # ===================== ГЕНЕРАЦИЯ FONTS =====================

    @classmethod
    def _generate_desktop_fonts_list(cls) -> List[str]:
        """Генерирует список шрифтов для desktop"""
        return [
            "Arial",
            "Arial Black",
            "Arial Unicode MS",
            "Calibri",
            "Cambria",
            "Courier New",
            "Georgia",
            "Helvetica",
            "Impact",
            "Lucida Console",
            "Lucida Sans Unicode",
            "Microsoft Sans Serif",
            "Palatino Linotype",
            "Segoe UI",
            "Tahoma",
            "Times New Roman",
            "Trebuchet MS",
            "Verdana",
            "Webdings",
            "Wingdings",
            "Comic Sans MS",
            "Consolas",
            "Franklin Gothic Medium",
        ]

    @classmethod
    def _generate_mobile_fonts_list(cls) -> List[str]:
        """Генерирует список шрифтов для мобильного устройства"""
        return [
            "Arial",
            "Helvetica",
            "Times",
            "Courier",
            "Verdana",
            "Georgia",
            "Palatino",
            "Garamond",
            "Bookman",
            "Trebuchet MS",
            "Arial Black",
            "Impact",
            "Sans-serif",
            "Serif",
            "Monospace",
            "system-ui",
            "-apple-system",
            "BlinkMacSystemFont",
        ]

    # ===================== ГЕНЕРАЦИЯ PLUGINS =====================

    @classmethod
    def _generate_plugins_list(cls, browser_name: str) -> List[Dict[str, Any]]:
        """Генерирует список плагинов браузера"""
        if browser_name == "Chrome":
            return [
                {
                    "name": "Chrome PDF Plugin",
                    "filename": "internal-pdf-viewer",
                    "description": "Portable Document Format",
                },
                {
                    "name": "Chrome PDF Viewer",
                    "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    "description": "Portable Document Format",
                },
                {
                    "name": "Native Client",
                    "filename": "internal-nacl-plugin",
                    "description": "Native Client",
                },
            ]
        elif browser_name == "Firefox":
            return [
                {
                    "name": "PDF.js",
                    "filename": "pdf.js",
                    "description": "Portable Document Format",
                }
            ]
        else:
            return []

    # ===================== ГЕНЕРАЦИЯ HARDWARE =====================

    @classmethod
    def _generate_desktop_hardware_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о железе для desktop"""
        return {
            "cores": random.choice([4, 6, 8, 12, 16]),
            "memory": random.choice([8, 16, 32, 64]),  # GB
            "platform": "Win32",
            "architecture": "x86_64",
            "max_touch_points": 0,
            "pointer_type": "mouse",
        }

    @classmethod
    def _generate_mobile_hardware_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о железе мобильного устройства"""
        return {
            "concurrency": random.choice([4, 6, 8]),
            "memory": random.choice([3, 4, 6, 8, 12]),  # GB
            "platform": "Linux armv7l",
            "architecture": "arm",
            "touch_support": True,
            "max_touch_points": random.choice([5, 10]),
            "pointer_type": "touch",
        }

    # ===================== ГЕНЕРАЦИЯ APIS =====================

    @classmethod
    def _generate_desktop_apis_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о доступных API для desktop"""
        return {
            "webrtc": True,
            "geolocation": True,
            "notifications": True,
            "push_messaging": True,
            "webgl": True,
            "webgl2": True,
            "canvas": True,
            "audio": True,
            "video": True,
            "midi": True,
            "payment": True,
            "presentation": True,
            "bluetooth": True,
            "usb": True,
            "serial": True,
        }

    @classmethod
    def _generate_mobile_apis_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о доступных API для мобильного устройства"""
        return {
            "webdriver": False,
            "automation": False,
            "notification": random.choice(["default", "granted", "denied"]),
            "geolocation": random.choice(["prompt", "granted"]),
            "camera": random.choice(["prompt", "granted"]),
            "microphone": random.choice(["prompt", "granted"]),
            "accelerometer": "granted",
            "gyroscope": "granted",
            "magnetometer": "granted",
            "webrtc": True,
            "webgl": True,
            "webgl2": True,
            "canvas": True,
            "audio": True,
            "video": True,
            "midi": False,
            "payment": True,
            "presentation": False,
            "bluetooth": True,
            "usb": False,
            "serial": False,
            "device_orientation": True,
            "device_motion": True,
            "touch": True,
            "vibration": True,
        }

    # ===================== ГЕНЕРАЦИЯ NETWORK =====================

    @classmethod
    def _generate_network_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о сети"""
        return {
            "connection_type": random.choice(["4g", "wifi", "ethernet"]),
            "downlink": random.uniform(10, 100),
            "effective_type": random.choice(["4g", "3g"]),
            "rtt": random.randint(50, 200),
            "save_data": False,
        }

    @classmethod
    def _generate_mobile_network_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о сети для мобильного устройства"""
        return {
            "connection_type": random.choice(["cellular", "wifi"]),
            "effective_type": random.choice(["3g", "4g", "5g"]),
            "downlink": random.uniform(1.0, 100.0),
            "rtt": random.randint(20, 200),
            "save_data": random.choice([True, False]),
        }

    # ===================== ГЕНЕРАЦИЯ TOUCH =====================

    @classmethod
    def _generate_desktop_touch_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о touch для desktop"""
        return {
            "touch_support": False,
            "max_touch_points": 0,
            "touch_event": False,
            "pointer_event": True,
            "ontouchstart": False,
        }

    @classmethod
    def _generate_mobile_touch_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о touch для мобильного устройства"""
        return {
            "touch_support": True,
            "max_touch_points": random.choice([5, 10]),
            "touch_event": True,
            "pointer_event": True,
            "ontouchstart": True,
        }

    # ===================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====================

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

    @classmethod
    def generate_fingerprint(
        cls, device_type: DeviceType = DeviceType.DESKTOP
    ) -> Dict[str, Any]:
        """Генерирует полноценный реалистичный fingerprint для указанного типа устройства"""
        return cls.generate_realistic_fingerprint(device_type)

    @staticmethod
    def create_browser_settings(fingerprint: Dict[str, Any]) -> Dict[str, Any]:
        """Создает настройки браузера на основе fingerprint"""
        device_type = fingerprint.get("device_type", "desktop")

        base_settings = {
            "viewport": {
                "width": fingerprint["viewport"]["width"],
                "height": fingerprint["viewport"]["height"],
            },
            "user_agent": fingerprint["browser"]["user_agent"],
            "locale": fingerprint["browser"]["language"],
            "timezone_id": fingerprint["timezone"]["timezone"],
            "device_scale_factor": fingerprint["screen"]["device_pixel_ratio"],
            "has_touch": fingerprint["touch"]["touch_support"],
            "color_scheme": "light",
            "reduced_motion": "no-preference",
            "forced_colors": "none",
            "geolocation": {"latitude": 55.7558, "longitude": 37.6173, "accuracy": 100},
            "permissions": ["geolocation"],
            "extra_http_headers": {
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        }

        if device_type == "mobile":
            base_settings.update(
                {
                    "is_mobile": True,
                    "touch_support": True,
                    "mobile_emulation": {
                        "device_name": cls._get_mobile_device_name(fingerprint),
                    },
                }
            )
        elif device_type == "tablet":
            base_settings.update(
                {
                    "is_mobile": False,
                    "touch_support": True,
                    "mobile_emulation": {
                        "device_name": "iPad",
                    },
                }
            )
        else:  # desktop
            base_settings.update(
                {
                    "is_mobile": False,
                    "touch_support": False,
                }
            )

        return base_settings

    @classmethod
    def _generate_tablet_fingerprint(cls) -> Dict[str, Any]:
        """Генерирует fingerprint для tablet устройства"""
        screen_width, screen_height = random.choice(cls.TABLET_SCREEN_RESOLUTIONS)
        timezone_info = random.choice(cls.RUSSIAN_TIMEZONES)

        # Tablet User Agents
        tablet_user_agents = [
            "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; SM-T970) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-T875) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]

        user_agent = random.choice(tablet_user_agents)
        browser_info = cls._parse_tablet_user_agent(user_agent)

        fingerprint = {
            "device_type": "tablet",
            "browser": browser_info,
            "screen": cls._generate_tablet_screen_info(screen_width, screen_height),
            "viewport": cls._generate_tablet_viewport_info(screen_width, screen_height),
            "timezone": cls._generate_timezone_info(timezone_info),
            "webgl": cls._generate_tablet_webgl_info(),
            "canvas": cls._generate_canvas_info(),
            "audio": cls._generate_mobile_audio_info(),
            "fonts": cls._generate_mobile_fonts_list(),
            "plugins": [],
            "hardware": cls._generate_tablet_hardware_info(),
            "webrtc": {"local_ips": [], "stun_connectivity": False},
            "apis": cls._generate_tablet_apis_info(),
            "network": cls._generate_mobile_network_info(),
            "touch": cls._generate_tablet_touch_info(),
        }

        return fingerprint

    @classmethod
    def _parse_tablet_user_agent(cls, user_agent: str) -> Dict[str, Any]:
        """Парсит tablet User Agent"""
        if "iPad" in user_agent:
            browser_name = "Safari"
            platform = "iPad"
            vendor = "Apple Computer, Inc."
        elif "Android" in user_agent and "Chrome" in user_agent:
            browser_name = "Chrome"
            platform = "Linux armv7l"
            vendor = "Google Inc."
        else:
            browser_name = "Safari"
            platform = "iPad"
            vendor = "Apple Computer, Inc."

        version = (
            cls._extract_version(user_agent, f"{browser_name}/")
            if "Chrome" in user_agent
            else "17.1"
        )

        return {
            "name": browser_name,
            "version": version,
            "user_agent": user_agent,
            "vendor": vendor,
            "platform": platform,
            "language": "ru-RU",
            "languages": ["ru-RU", "ru", "en-US", "en"],
        }

    @classmethod
    def _generate_tablet_screen_info(cls, width: int, height: int) -> Dict[str, Any]:
        """Генерирует информацию об экране tablet"""
        device_pixel_ratio = random.choice([2.0, 1.5, 2.75])

        return {
            "width": width,
            "height": height,
            "color_depth": 24,
            "pixel_depth": 24,
            "available_width": width,
            "available_height": height,
            "device_pixel_ratio": device_pixel_ratio,
            "orientation": random.choice(["portrait-primary", "landscape-primary"]),
        }

    @classmethod
    def _generate_tablet_viewport_info(
        cls, screen_width: int, screen_height: int
    ) -> Dict[str, Any]:
        """Генерирует информацию о viewport tablet"""
        return {
            "width": screen_width,
            "height": screen_height - random.randint(60, 120),
            "inner_width": screen_width,
            "inner_height": screen_height - random.randint(60, 120),
            "outer_width": screen_width,
            "outer_height": screen_height,
        }

    @classmethod
    def _generate_tablet_webgl_info(cls) -> Dict[str, Any]:
        """Генерирует WebGL информацию для tablet"""
        tablet_renderers = [
            "Apple A12 GPU",
            "Apple A15 GPU",
            "Adreno (TM) 650",
            "Mali-G77 MP12",
            "PowerVR GT7600 Plus",
        ]

        renderer = random.choice(tablet_renderers)

        return {
            "vendor": "WebKit",
            "renderer": renderer,
            "version": "WebGL 1.0",
            "shading_language_version": "WebGL GLSL ES 1.0",
            "max_texture_size": 8192,
            "max_viewport_dims": [8192, 8192],
            "supported_extensions": [
                "EXT_blend_minmax",
                "EXT_color_buffer_half_float",
                "EXT_disjoint_timer_query",
                "EXT_frag_depth",
                "EXT_shader_texture_lod",
                "EXT_texture_filter_anisotropic",
                "OES_element_index_uint",
                "OES_standard_derivatives",
                "OES_texture_float",
                "OES_texture_float_linear",
                "OES_texture_half_float",
                "OES_texture_half_float_linear",
                "OES_vertex_array_object",
                "WEBGL_color_buffer_float",
                "WEBGL_debug_renderer_info",
                "WEBGL_debug_shaders",
                "WEBGL_depth_texture",
                "WEBGL_lose_context",
            ],
        }

    @classmethod
    def _generate_tablet_hardware_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о железе tablet"""
        return {
            "concurrency": random.choice([6, 8, 10]),
            "memory": random.choice([4, 6, 8, 12]),
            "platform": "iPad" if random.choice([True, False]) else "Linux armv7l",
            "architecture": "arm64",
            "touch_support": True,
            "max_touch_points": random.choice([10, 20]),
            "pointer_type": "touch",
        }

    @classmethod
    def _generate_tablet_apis_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о доступных API для tablet"""
        return {
            "webdriver": False,
            "automation": False,
            "notification": random.choice(["default", "granted", "denied"]),
            "geolocation": random.choice(["prompt", "granted"]),
            "camera": random.choice(["prompt", "granted"]),
            "microphone": random.choice(["prompt", "granted"]),
            "accelerometer": "granted",
            "gyroscope": "granted",
            "magnetometer": "granted",
            "webrtc": True,
            "webgl": True,
            "webgl2": True,
            "canvas": True,
            "audio": True,
            "video": True,
            "midi": False,
            "payment": True,
            "presentation": True,
            "bluetooth": True,
            "usb": False,
            "serial": False,
            "device_orientation": True,
            "device_motion": True,
            "touch": True,
            "vibration": True,
        }

    @classmethod
    def _generate_tablet_touch_info(cls) -> Dict[str, Any]:
        """Генерирует информацию о touch для tablet"""
        return {
            "touch_support": True,
            "max_touch_points": random.choice([10, 20]),
            "touch_event": True,
            "pointer_event": True,
            "ontouchstart": True,
        }
