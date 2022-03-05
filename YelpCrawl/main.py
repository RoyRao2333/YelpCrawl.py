import os
import csv
import time
import re
import pickle
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, urlencode, parse_qsl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import WebDriverException
from pathlib import Path

# init driver
option = webdriver.ChromeOptions()
# option.headless = True
driver = webdriver.Chrome(options=option)


def find_element_by_xpath(self, xpath):
    try:
        return self.find_element(by=By.XPATH, value=xpath)

    except WebDriverException:
        return None


def find_elements_by_xpath(self, xpath):
    try:
        return self.find_elements(by=By.XPATH, value=xpath)

    except WebDriverException:
        return None


def find_element_by_id(self, value):
    try:
        return self.find_elements(by=By.ID, value=value)

    except WebDriverException:
        return None


def wait_for_element_by_id(self, value):
    try:
        return WebDriverWait(self, 10).until(ec.presence_of_element_located((By.ID, value)))

    except WebDriverException:
        return None


def wait_for_element_by_xpath(self, value):
    try:
        return WebDriverWait(self, 10).until(ec.presence_of_element_located((By.XPATH, value)))

    except WebDriverException:
        return None


def find_elements_by_class_name(self, class_name):
    try:
        return self.find_elements(by=By.CLASS_NAME, value=class_name)

    except WebDriverException:
        return None


def makedir(path):
    folder = os.path.exists(path)

    if not folder:
        os.makedirs(path)


def save_img(img_url, path) -> bool:
    try:
        response = urlopen(img_url)

    except (URLError, HTTPError):
        print("Image fetch failed.")
        return False

    try:
        with open(path, 'wb') as img_file:
            img_file.write(response.read())
        return True

    except OSError:
        print("Image save failed.")
        return False


def get_param_from_url(url: str, key: str) -> str:
    parsed = urlparse(url)
    params = dict(parse_qsl(parsed.query))
    return params[key] if params[key] is not None else ""


def get_input():
    csv_reader = csv.reader(input_file)
    input_list = list()

    for line in csv_reader:
        item = line[0]
        if item is not None and isinstance(item, str):
            input_list.append(item)

    return input_list


def crawl(self, file):
    try:
        element_list = find_elements_by_xpath(self, "//a[contains(@class, 'tab-link--nav')][contains(@class, 'js-tab-link--nav')]")
    except WebDriverException:
        print("Network error, retry it later...")
        return

    for tab_element in element_list:
        tab_element.click()
        time.sleep(2)

        tab_label = tab_element.find_element(by=By.XPATH, value="./span[2]").text
        if tab_label in finished_tabs or "all" in tab_label.lower():
            continue
        # click first image item
        find_element_by_xpath(self, "//*[@class='biz-shim js-lightbox-media-link js-analytics-click']").click()

        if iterate(self, file):
            finished_tabs.append(tab_label)
            print(f"Tab {tab_label} completed.")

        else:
            print("Process ended due to a network error. Retrying...")
            self.get(entrance_url)
            time.sleep(2)


def iterate(self, file) -> bool:
    while True:
        try:
            wait_for_element_by_id(self, "lightbox")
        except WebDriverException:
            return False
        else:
            parse(self, file)

        try:
            wait_for_element_by_xpath(self, "//*[@id='lightbox-inner']/div[2]/div/div/div[2]/a[2]")

        except WebDriverException:
            try:
                close_element = wait_for_element_by_xpath(self, "//*[@id='lightbox-inner']/div[1]")
                close_element.click()
            except WebDriverException:
                pass

            return True

        else:
            next_element = wait_for_element_by_xpath(self, "//*[@id='lightbox-inner']/div[2]/div/div/div[2]/a[2]")
            if next_element.get_attribute("href") is None:
                try:
                    close_element = wait_for_element_by_xpath(self, "//*[@id='lightbox-inner']/div[1]")
                    close_element.click()
                except WebDriverException:
                    pass

                return True

            time.sleep(2)
            try:
                wait_for_element_by_xpath(self, "//*[@id='lightbox-inner']/div[2]/div/div/div[2]/a[2]").click()
            except WebDriverException:
                return True


def parse(self, file):
    writer = csv.writer(file)

    try:
        user_id = find_element_by_xpath(
            self,
            "//a[contains(@class, 'user-display-name')]"
        ).text
        is_merchant = "No"
    except WebDriverException:
        try:
            user_id = find_element_by_xpath(
                self,
                "//a[@data-analytics-label='biz-name']/span"
            ).text
            is_merchant = "Yes"
        except WebDriverException:
            pic_error_writer.writerow([self.current_url])
            print("Fetching pic error, retry it later...")
            return

    try:
        tab_label = find_element_by_xpath(
            self,
            "//a[@role='tab'][contains(@class, 'is-selected')]/span[contains(@class, 'tab-link_label')]"
        ).text
        comment = find_element_by_xpath(
            self,
            "//div[contains(@class, 'selected-photo-caption-text')]"
        ).text
        index = find_element_by_xpath(
            self,
            "//span[@class='media-count_current']"
        ).text
        img = wait_for_element_by_xpath(
            self,
            "//img[@class='photo-box-img'][@loading='auto']"
        ).get_attribute("src")
        date = find_element_by_xpath(
            self,
            "//span[contains(@class, 'selected-photo-upload-date')]"
        ).text
    except WebDriverException:
        pic_error_writer.writerow([self.current_url])
        print("Fetching pic error, retry it later...")
        return

    if img:
        image_name = f"[{tab_label}] {index}"
        image_path = os.path.join(img_folder_path, image_name + ".jpg")
        save_img(img, image_path)

    else:
        pic_error_writer.writerow([self.current_url])
        print("Fetching pic error, retry it later...")
        return

    writer.writerow([
        tab_label,
        image_name,
        comment,
        user_id,
        is_merchant,
        date
    ])
    file.flush()
    print("Fetched " + image_name)


if __name__ == '__main__':
    makedir("./Desktop/YelpResults/errors")

    input_path = Path(__file__).with_name("stores.csv")
    input_file = input_path.open(mode="r", encoding="utf-8-sig")
    store_error_file_path = os.path.join("./Desktop/YelpResults/errors", "store_error.csv")
    store_error_file = open(store_error_file_path, "w", encoding="utf-8-sig")
    store_error_writer = csv.writer(store_error_file)
    pic_error_file_path = os.path.join("./Desktop/YelpResults/errors", "pic_error.csv")
    pic_error_file = open(pic_error_file_path, "w", encoding="utf-8-sig")
    pic_error_writer = csv.writer(pic_error_file)

    # do your job
    for business_id in get_input():
        entrance_url = "https://www.yelp.com/biz_photos/" + business_id
        driver.get(entrance_url)

        cookie_path = Path(__file__).with_name("cookies.pkl")
        if cookie_path.is_file():
            cookies = pickle.load(cookie_path.open(mode="rb"))
            for cookie in cookies:
                driver.add_cookie(cookie)
        else:
            pickle.dump(driver.get_cookies(), cookie_path.open(mode="wb"))

        finished_tabs = list()

        # prepare dirs
        folder_path = os.path.join("./Desktop/YelpResults/", business_id)
        makedir(folder_path)
        img_folder_path = os.path.join(folder_path, "img")
        makedir(img_folder_path)

        output_file_path = os.path.join(folder_path, "manifest.csv")
        output_file = open(output_file_path, "w", encoding="utf-8-sig")
        output_writer = csv.writer(output_file)
        output_writer.writerow(["category", "img", "comment", "user_id", "is_merchant", "date"])
        crawl(driver, output_file)
        output_file.close()

        print("Business_id {} completed.".format(business_id))

    # deinit
    driver.quit()
    store_error_file.close()
    pic_error_file.close()
