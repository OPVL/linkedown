import functools
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pprint import pp
from time import sleep, time
from typing import List, Optional, Tuple

import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from lib.constants import BACKOFF_SCALE, PRESELECT_PAUSE
from lib.types import Chapter, Config, Course, Section
from lib.util import pretty_time_difference

config = open("config.json", "r")
config_json: Config = json.load(config)


def download(url: str, dest_folder: str):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    # be careful with file names
    filename = url.split("/")[-1].replace(" ", "_")
    file_path = os.path.join(dest_folder, filename)

    r = requests.get(url, stream=True, cookies=)
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:  # HTTP status code 4XX/5XX
        print(f"Download failed: status code {r.status_code}\n{r.text}")


def get_download_link(
    chapter_url: str,
    driver: WebDriver,
    preloaded: bool = False,
) -> Optional[Course]:
    """
    Get the download information for a given course.

    Args:
        course_url(str): the course to download
        driver(WebDriver): the web driver

    Returns:
        (
            str: video title - eg. Understanding Web Concepts
            str: video download url
            bool: has_next_button - used to download 'next' course video
        )
    """
    if not preloaded:
        driver.get(chapter_url)  # put here the adress of your page

    sleep(PRESELECT_PAUSE)

    classroom = driver.find_element(
        by=By.CSS_SELECTOR, value=".classroom-layout__media.ember-view"
    )

    if not classroom:
        raise Exception(
            f"Classroom not found on page: {chapter_url}",
            "#007",
        )

    video_screen = classroom.find_element(
        by=By.CSS_SELECTOR,
        value="video.vjs-tech",
    )

    if not video_screen:
        raise Exception(
            f"No matching video element found on page: {chapter_url}",
            "#001",
        )

    video_source = video_screen.get_attribute("src")
    if not video_source:
        raise Exception(
            f"Video source not found on page: {chapter_url}",
            "#002",
        )

    return {"url": video_source.strip(), "title": driver.title.strip()}


def get_sections(sidebar: WebElement) -> Tuple[List[Section], int]:
    """
    Get the sections from a sidebar element.

    Returns:
        List[Section]: the sections built form the sidebar
        int: the number of chapters contained in the sections
    """
    web_sections = sidebar.find_elements(
        by=By.CSS_SELECTOR, value="section.classroom-toc-section"
    )

    if len(web_sections) < 1:
        raise Exception("unable to load chapter sections", "#005")

    sections: List[Section] = []
    num_chapters = 0

    for section in web_sections:
        section_title = section.find_element(
            by=By.CSS_SELECTOR,
            value=".classroom-toc-section__toggle-title.t-14.t-bold.t-white",
        ).text

        sub_chapters = get_chapters(section)
        num_chapters += len(sub_chapters)
        sections.append(
            {
                "title": section_title,
                "chapters": sub_chapters,
                "num_chapters": len(sub_chapters),
            }
        )

    return sections, num_chapters


def get_chapters(section: WebElement) -> List[Chapter]:
    chapter_link_elements = section.find_elements(
        by=By.CSS_SELECTOR,
        value="a.ember-view.classroom-toc-item__link.t-normal",
    )

    sub_chapters = []

    if len(chapter_link_elements) < 1:
        raise Exception("unable to load chapters", "#004")

    for chapter in chapter_link_elements:
        url = chapter.get_attribute("href")
        title = chapter.find_elements(
            by=By.CSS_SELECTOR, value=".classroom-toc-item__title.t-14.t-white"
        )[0].text

        if re.search("chapter quiz", title, re.IGNORECASE) is not None:
            pp(f"skipping {title}. suspected quiz")
            continue

        if not url:
            raise Exception("Unable to get chapter link", "#003")

        chapter_obj: Chapter = {"href": url, "title": title}

        pp(chapter_obj)
        sub_chapters.append(chapter_obj)
    return sub_chapters


def build_index(
    course: Course,
    driver: WebDriver,
) -> Tuple[List[Section], int]:
    driver.get(course["url"])
    sleep(1)
    sidebar = driver.find_element(
        by=By.CSS_SELECTOR,
        value=".classroom-layout__sidebar",
    )
    if not sidebar:
        raise Exception("unable to get content sidebar", "#005")

    return get_sections(sidebar)


def new_driver():
    pp("booting driver")
    start_time = time()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = False
    chrome_options.binary_location = "/usr/bin/google-chrome-beta"

    chrome_service = Service(
        executable_path="./chromedriver",
        log_path="chrome.log",
    )

    driver = webdriver.Chrome(
        options=chrome_options,
        # project_name="LinkedIn Downloader",
        service=chrome_service,
    )

    driver.get("https://linkedin.com")
    driver.maximize_window()

    for key in config_json["cookies"].keys():
        cookie = {
            "name": key,
            "value": config_json["cookies"][key],
            "domain": config_json["web"]["cookie_host"],
            "path": "/",
        }

        driver.add_cookie(cookie_dict=cookie)

    pp(f"driver booted: {pretty_time_difference(start_time)}")
    return driver


def main():
    # driver = new_driver()
    course = config_json["courses"][0]

    # all_chapters, count = get_all_chapters(driver, course)

    # sections = get_all_download_links(driver, all_chapters, count)
    coursefile = open("introduction-to-web-design.json", "r")
    sections = json.load(coursefile)
    if not config_json["application"]["download"]:
        return

    for section in sections:
        with ThreadPoolExecutor(6) as executor:
            future_list = executor.submit(
                [
                    functools.partial(
                        download,
                        chapter["url"],
                        f'{course["title"]}/{section["title"]}/{chapter["title"]}',
                    )
                    for chapter in section["chapters"]
                ]
            )

        for chapter in section["chapters"]:

            download(
                chapter["url"],
                f'{course["title"]}/{section["title"]}/{chapter["title"]}',
            )


def get_all_download_links(driver, all_chapters, count) -> List[Section]:
    testjson = open("chapters.json", "w")
    start_time = time()
    estimate = est_ti(count)
    estimate_time = start_time - estimate

    pp(f"getting download links. est time: {pretty_time_difference(estimate_time)}")
    new_sections = []
    num = 0
    for section in all_chapters:
        pp(f'getting download links for chapter section: {section["title"]}')
        new_chapters = []
        failed = []
        for chapter in section["chapters"]:
            try:
                download_info = get_download_link(
                    chapter_url=chapter["href"],
                    driver=driver,
                )

                if download_info is None:
                    continue

            except Exception as exc:
                pp(exc.__str__())
                pp(
                    "failed to get download link."
                    + f"retying in {BACKOFF_SCALE * PRESELECT_PAUSE}"
                    + "s with new driver"
                )
                driver.quit()

                sleep(BACKOFF_SCALE * PRESELECT_PAUSE)
                driver = new_driver()
                try:
                    if config_json["application"]["preload_on_fail"]:
                        pp(f"preloading failed page {chapter['title']}")
                        driver.get(chapter["href"])
                        sleep(BACKOFF_SCALE * PRESELECT_PAUSE)

                    download_info = get_download_link(
                        chapter_url=chapter["href"],
                        driver=driver,
                        preloaded=config_json["application"]["preload_on_fail"],
                    )
                    pp(
                        f'Got link: {download_info["url"]}'
                        + f' for {download_info["title"]}'
                    )
                except NoSuchElementException as exc:
                    pp(f"Failed to get class for {driver.title}: {exc.msg}")
                    driver.quit()
                    driver = new_driver()
                    sleep(BACKOFF_SCALE * PRESELECT_PAUSE)
                    pp("driver rebooted")
                    failed.append(chapter)

                    continue

                chapter.update(download_info)

            new_chapters.append(
                {
                    "url": download_info["url"],
                    "title": download_info["title"],
                    "href": chapter["href"],
                }
            )

            num += 1

            sleep(PRESELECT_PAUSE / 10)
        new_sections.append(
            {
                "title": section["title"],
                "chapters": new_chapters,
            }
        )
    pp(f"got download links: {pretty_time_difference(start_time)}")
    diff = pretty_time_difference(start_time)
    pp(
        f"ahead of schedule by {diff}"
        if estimate_time > time()
        else f"behind schedule by {diff}s"
    )
    json.dump(new_sections, testjson)
    testjson.close()

    if len(failed) > 0:
        pp(f"failed to get download links for {len(failed)} chapters")
        failed_json = open("failed.json", "w")
        json.dump(failed, failed_json)

    driver.quit()

    return new_sections


def get_all_chapters(driver: WebDriver, course: Course):
    pp("getting chapters")
    start_time = time()
    all_chapters, count = build_index(
        course,
        driver,
    )
    pp(f"got chapters: {pretty_time_difference(start_time)}")
    return all_chapters, count


def est_ti(count) -> int:
    return count * PRESELECT_PAUSE * 2


if __name__ == "__main__":
    main()
