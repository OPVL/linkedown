import json
from pprint import pp

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from lib.types import Config, Course

# driver = webdriver.Firefox()
# driver.get("http://www.youradress.org")  # put here the adress of your page
# # put here the content you have put in Notepad, ie the XPath
# elem = driver.find_elements_by_xpath("//*[@type='submit']")

# # Or find button by ID.
# button = driver.find_element_by_id("NEXT_BUTTON")
# print(elem.get_attribute("class"))
# driver.close()


def main():
    config = open("config.json", "r")
    config_json: Config = json.load(config)

    driver = webdriver.Firefox()
    driver.add_cookie(config_json["cookies"])

    results = get_download_information_for_course(config_json["courses"][0])

    pp(results)
    driver.close()


if __name__ == "__main__":
    main()


def get_download_information_for_course(course: Course, driver):
    download_url = course["url"]

    has_next_button = True

    course_videos = []
    num_videos = 0

    while has_next_button:
        download_url, title, has_next_button = get_download_information(
            download_url, driver
        )
        num_videos += 1
        course_videos.append(
            {
                "title": title,
                "url": download_url,
                "index": num_videos,
            }
        )

    return course_videos


def get_download_information(course_url: str, driver):
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
    driver.get(course_url)  # put here the adress of your page
    has_next_button = True

    next_button = driver.find_element(by="class", value="vjs-next-button")
    if not next_button:
        has_next_button = False

    video_screen = driver.find_element(by="id", value="vjs_video_3_html5_api")

    if not video_screen:
        raise Exception(
            f"No matching video element found on page: {course_url}",
            "#001",
        )

    video_source = video_screen.get_attribute("src")
    if not video_source:
        raise Exception(
            f"Video source not found on page: {course_url}",
            "#002",
        )

    video_title = driver.title

    return (video_title, video_source, has_next_button)
