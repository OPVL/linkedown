import json
import os
import re
from pprint import pp
from time import sleep, time
from typing import Dict, List, Optional, Tuple

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from lib.types import Chapter, Config, Course, Section

# driver = webdriver.Firefox()
# driver.get("http://www.youradress.org")  # put here the adress of your page
# # put here the content you have put in Notepad, ie the XPath
# elem = driver.find_elements_by_xpath("//*[@type='submit']")

# # Or find button by ID.
# button = driver.find_element_by_id("NEXT_BUTTON")
# print(elem.get_attribute("class"))
# driver.close()

config = open("config.json", "r")
config_json: Config = json.load(config)


def download(url: str, dest_folder: str):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    filename = url.split("/")[-1].replace(" ", "_")  # be careful with file names
    file_path = os.path.join(dest_folder, filename)

    r = requests.get(url, stream=True)
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))


def get_download_link(chapter_url: str, driver: WebDriver) -> Optional[Course]:
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

    driver.get(chapter_url)  # put here the adress of your page

    sleep(1)

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
        value="section.classroom-layout__sidebar.classroom-layout__sidebar--visible.classroom-layout__sidebar--showing",
    )
    if not sidebar:
        raise Exception("unable to get content sidebar", "#005")

    return get_sections(sidebar)


def new_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = False
    chrome_options.binary_location = (
        "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta"
    )

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

    for key in config_json["cookies"].keys():
        cookie = {
            "name": key,
            "value": config_json["cookies"][key],
            "domain": "www.linkedin.com",
            "path": "/",
        }

        driver.add_cookie(cookie_dict=cookie)

    return driver


def main():
    real_start_time = time()

    pp("booting driver")
    driver = new_driver()
    pp(f"driver booted: {time() - real_start_time}s")

    pp("getting chapters")
    start_time = time()
    all_chapters, count = build_index(
        config_json["courses"][0],
        driver,
    )
    pp(f"got chapters: {time() - start_time}s")

    testjson = open("chapters.json", "w")

    start_time = time()
    estimate_time = count * 1.1
    pp(f"getting download links. est time: {estimate_time}s")
    new_sections = []
    for section in all_chapters:
        pp(f'getting download links for chapter section: {section["title"]}')
        new_chapters = []
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
                pp("failed to get download link. retying in 2 secs with new driver")
                driver.quit()

                sleep(2)
                driver = new_driver()
                download_info = get_download_link(
                    chapter_url=chapter["href"],
                    driver=driver,
                )
                pp(f'Got link: {download_info["url"]} for {download_info["title"]}')

            chapter.update(download_info)

            new_chapters.append(chapter)

            sleep(0.1)
        new_sections.append({"title": section["title"], "chapters": new_chapters})
    time_taken = time() - start_time
    pp(f"got download links: {time_taken}s")
    pp(
        f"ahead of schedule by {estimate_time - time_taken}s"
        if estimate_time > time_taken
        else f"behind schedule by {time_taken - estimate_time}"
    )
    json.dump(new_sections, testjson)
    testjson.close()

    # url, title = get_download_link(
    #     "https://www.linkedin.com/learning/introduction-to-web-design-and-development-14628245/understanding-css",
    #     driver,
    # )

    # pp(f"URL:{url} TITLE:{title}")
    driver.quit()


if __name__ == "__main__":
    main()
