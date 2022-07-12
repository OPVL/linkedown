from typing import Dict, List, Optional, TypedDict


class Course(TypedDict):
    url: str
    title: Optional[str]


class WebConfig(TypedDict):
    video_element_id: str
    next_button_class: str
    course_title_class: str
    chapter_link_class: str
    user_agent: str


class CookieConfig(TypedDict):
    li_at: str
    li_ep_auth_context: str


class AppConfig(TypedDict):
    download: bool
    download_list: str
    logfile: str
    output_dir: str


class Config(TypedDict):
    web: WebConfig
    cookies: CookieConfig
    application: AppConfig
    courses: List[Course]


class Chapter(TypedDict):
    href: str
    title: str


class Section(TypedDict):
    title: str
    chapters: List[Chapter]
    num_chapters: int


class WebChapter(TypedDict):
    sections: List[Section]
