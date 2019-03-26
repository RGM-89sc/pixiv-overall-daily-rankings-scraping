import time
import re
import os
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions
from selenium.webdriver.chrome.options import Options

url = 'https://www.pixiv.net/ranking.php?mode=daily&p='
img_base_path = './images/'
if not os.path.exists(img_base_path):
    os.mkdir(img_base_path)

options = Options()
options.add_argument('--proxy-server=socks5://localhost:1080')
options.add_argument('--headless')  # 无头模式
driver = webdriver.Chrome(options=options)


def download_img(referer, image_url, path):
    opener = urllib.request.build_opener()
    opener.addheaders = [('Referer', referer)]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(image_url, path)


def login(username, password):
    load_page('https://accounts.pixiv.net/login')
    driver.find_element_by_xpath('//input[@autocomplete="username"]').send_keys(username)
    driver.find_element_by_xpath('//input[@autocomplete="current-password"]').send_keys(password, Keys.ENTER)
    time.sleep(3)  # 等待cookie加载完成
    cookies = driver.get_cookies()


def load_page(page_url):
    while 1:
        try:
            driver.get(page_url)
            break
        except exceptions.TimeoutException:
            driver.get(page_url)


# 登录
login('your username', 'your password')


# 开始爬取
def overall_daily_rankings(base_url, start_page, end_page):
    for i in range(start_page, end_page + 1):
        print('正在获取页面：%s' % base_url + str(i))

        load_page(base_url + str(i))
        ranking_image_items = driver.find_elements_by_xpath(
            '//div[@class="ranking-image-item"]/a[@class!="_illust-series-title _illust-series-title-text"]')

        img_urls = []  # 图片主页地址列表
        for img_item in ranking_image_items:
            img_urls.append(img_item.get_attribute('href'))

        for img_url in img_urls:
            load_page(img_url)  # 进入图片主页
            # img_src = ''
            while 1:  # 如果找不到元素很可能是还没加载完成，所以循环查找元素
                try:
                    img_src = driver.find_element_by_xpath(
                        '//div[@id="root"]//main//section//figure/div/div/div/a').get_attribute('href')  # 原图地址
                    break
                except exceptions.NoSuchElementException:
                    time.sleep(0.5)

            if img_src.endswith('.jpg') or img_src.endswith('.png') or img_src.endswith('.gif'):  # 地址是图片地址
                # 保存图片
                filename = img_src.split('/')[-1]
                download_img(img_url, img_src, img_base_path + filename)
            else:  # 多图
                load_page(img_src)  # 进入多图页面
                img_list = driver.find_elements_by_xpath(
                    '//section[@id="main"]/section[@class="manga"]/div[@class="item-container"]/img')  # 获取所有图片
                # 创建目录
                dir_name = img_base_path + re.match(r'.+illust_id=([0-9]+)', img_src).group(1) + '/'
                if not os.path.exists(dir_name):
                    os.mkdir(dir_name)

                for img in img_list:
                    src = img.get_attribute('data-src')
                    filename = src.split('/')[-1]
                    download_img(img_src, src, dir_name + filename)
    driver.close()


overall_daily_rankings(url, 1, 3)
