import asyncio
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import nonebot_plugin_localstore as store
from PIL import Image
from nonebot import require
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.plugins.gokz.core.file_oper import check_last_modified_date
from src.plugins.gokz.core.kreedz import format_kzmode
from src.plugins.gokz.core.steam_user import convert_steamid

require("nonebot_plugin_localstore")

executor = ThreadPoolExecutor(max_workers=5)


async def kzgoeu_screenshot_async(steamid, kz_mode, force_update=False):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor, kzgoeu_screenshot, steamid, kz_mode, force_update
    )
    return result


async def vnl_screenshot_async(steamid, force_update=False):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, vnl_screenshot, steamid, force_update)
    return result


def random_card():
    cache_dir: Path = store.get_cache_dir("plugin_name")
    png_files = list(cache_dir.glob("*.png"))
    if not png_files:
        raise FileNotFoundError("No .png files found in the cache directory")
    random_file = random.choice(png_files)
    return random_file


def kzgoeu_screenshot(steamid, kz_mode, force_update=False):
    steamid = convert_steamid(steamid)
    kz_mode = format_kzmode(kz_mode, 'm')

    steamid64 = convert_steamid(steamid, 64)

    cache_file = store.get_cache_file("plugin_name", f"{steamid64}_{kz_mode}.png")

    # Check last modified date of the file
    if not force_update:
        last_modified_date = check_last_modified_date(cache_file)
        if last_modified_date and (datetime.now() - last_modified_date <= timedelta(hours=1)):
            return str(cache_file)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--no-sandbox")  # Bypass OS security model

    driver = webdriver.Chrome(options=options)

    kzgo_url = f"https://kzgo.eu/players/{steamid}?{kz_mode}"
    driver.get(kzgo_url)

    width = 700
    height = 1000
    driver.set_window_size(width, height)

    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "progress-bg")))
    time.sleep(1)

    screenshot = driver.get_screenshot_as_png()
    driver.quit()
    img = Image.open(BytesIO(screenshot))

    # Crop the image
    left = 90
    top = 100
    right = width - 100
    bottom = height - 280
    cropped_img = img.crop((left, top, right, bottom))

    # Save the cropped screenshot to the cache directory
    cropped_img.save(cache_file)

    return str(cache_file)


def vnl_screenshot(steamid, force_update=False):
    steamid64 = convert_steamid(steamid, 2)
    steamid = convert_steamid(steamid)
    steamid64 = convert_steamid(steamid, 64)

    cache_file = store.get_cache_file("plugin_name", f"{steamid64}_kz_vanilla.png")

    # Check last modified date of the file
    if not force_update:
        last_modified_date = check_last_modified_date(cache_file)
        if last_modified_date and (datetime.now() - last_modified_date <= timedelta(days=1)):
            # If file modified within 1 day, return URL directly
            return str(cache_file)

    # Use Selenium to open the browser
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--no-sandbox")  # Bypass OS security model

    driver = webdriver.Chrome(options=options)

    # Open the VNL page
    kzgo_url = f"https://vnl.kz/#/stats/{steamid64}"
    driver.get(kzgo_url)

    # Set browser window size
    width = 920
    height = 620
    driver.set_window_size(width, height)

    # Wait for the webpage to load
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'TP')]"))
    )

    # Capture a screenshot of the entire webpage
    screenshot = driver.get_screenshot_as_png()

    # Close the browser
    driver.quit()

    # Open the screenshot with Pillow
    img = Image.open(BytesIO(screenshot))

    # Crop the image
    left = 0
    top = 65
    right = width - 15
    bottom = height - 95
    cropped_img = img.crop((left, top, right, bottom))

    # Save the cropped screenshot to the cache directory
    cropped_img.save(cache_file)

    return str(cache_file)

