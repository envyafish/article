from urllib.parse import urlparse, parse_qs, urlencode
from curl_cffi import requests
from pyquery import PyQuery as pq
import re
from datetime import datetime, timedelta
import bencoder
import hashlib
import binascii

from app.core.config import config_manager
from app.utils.log import logger


def extract_and_convert_video_size(html_content):
    doc = pq(html_content)
    message_text = doc('.message').text()
    clean_text = re.sub(r'\s+', ' ', message_text).strip()
    pattern = r"(\d+\.?\d*)([GM])"
    match = re.search(pattern, clean_text)
    if not match:
        return None
    size_num_str, unit = match.groups()
    try:
        size_num = float(size_num_str)
    except ValueError:
        return None

    if unit.upper() == 'G':
        mb_size = size_num * 1024
    elif unit.upper() == 'M':
        mb_size = size_num
    else:
        return None
    return int(mb_size)


def extract_safeid(html_content):
    doc = pq(html_content)
    for script_elem in doc('script'):
        script_text = pq(script_elem).text().strip()
        if not script_text or 'safeid' not in script_text:
            continue
        match = re.search(r"safeid\s*=\s*['\"]([^'\"]+)['\"]", script_text)
        if match:
            return match.group(1)
    return None


def extract_exact_datetime(html_content):
    doc = pq(html_content)
    date_text = doc('dt.z.cl').eq(0).text().strip()
    if not date_text:
        return ""
    processed_text = date_text.replace('&nbsp;', ' ').strip()
    processed_text = re.sub(r'\s+', ' ', processed_text)
    today = datetime.now().date()
    if re.match(r'^\d+ 小时前$', processed_text):
        return today.strftime('%Y-%m-%d')
    elif processed_text.startswith('半小时前'):
        return today.strftime('%Y-%m-%d')
    elif re.match(r'^\d+ 分钟前$', processed_text):
        return today.strftime('%Y-%m-%d')
    elif re.match(r'^\d+ 秒前$', processed_text):
        return today.strftime('%Y-%m-%d')
    elif processed_text.startswith('昨天 '):
        yesterday = today - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    elif processed_text.startswith('前天 '):
        day_before_yesterday = today - timedelta(days=2)
        return day_before_yesterday.strftime('%Y-%m-%d')
    elif re.match(r'^\d+ 天前$', processed_text):
        days = int(re.search(r'(\d+) 天前', processed_text).group(1))
        target_date = today - timedelta(days=days)
        return target_date.strftime('%Y-%m-%d')
    elif re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', processed_text):
        pure_date_str = processed_text.split(' ')[0]
        return pure_date_str
    else:
        logger.error(f"警告：无法解析的日期格式 → {date_text}")
        return None


def extract_bracket_content(html_content):
    doc = pq(html_content)
    h2_text = doc('h2.n5_bbsnrbt').text()
    clean_text = h2_text.strip()
    pattern = r"\[(.*?)\]"
    match = re.search(pattern, clean_text)

    if match:
        return match.group(1)
    else:
        return None


class SHT:
    headers = {}
    cookie = {}


    def __init__(self):
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
        self.headers = {
            'User-Agent': ua
        }
        self.cookie = {
            '_safe': ''
        }


    def get_original(self, url):
        proxies = {
            "http": config_manager.get().PROXY,
            "https": config_manager.get().PROXY
        }
        res = requests.get(url, proxies=proxies, cookies=self.cookie, headers=self.headers,
                           allow_redirects=True, timeout=10, impersonate="chrome110")
        html = res.text.encode('utf-8')
        doc = pq(html)
        page_title = doc('head>title').text()
        if 'Just a moment' in page_title:
            logger.warning("触发CF，尝试过盾")
            html = self.bypass_cf(url)
            if not html:
                logger.error("过盾失败")
                return None
        doc = pq(html)
        if "var safeid" in doc.text():
            logger.warning("触发18禁,获取safeid")
            html = self.bypass_r18(html, url)
            if not html:
                logger.error("过18禁失败")
                return None
        doc = pq(html)
        page_title = doc('head>title').text()
        if "98堂" in page_title:
            return html
        else:
            logger.warning(page_title)
        return None

    def bypass_cf(self, url):
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
            "proxy": {"url": config_manager.get().PROXY},
            "cookies": [{"name": k, "value": v} for k, v in self.cookie.items()]
        }
        res = requests.post(config_manager.get().FLARE_SOLVERR_URL, headers={"Content-Type": "application/json"}, json=payload)
        result = res.json()
        if result['solution']['status'] != 200:
            return None
        html = result['solution']['response'].encode('utf-8')
        doc = pq(html)
        if "var safeid" in doc.text():
            safeid = extract_safeid(html)
            self.cookie['_safe'] = safeid
            return self.bypass_cf(url)
        return html

    def bypass_r18(self, html, url):
        proxies = {
            "http": config_manager.get().PROXY,
            "https": config_manager.get().PROXY
        }
        safeid = extract_safeid(html)
        if safeid:
            self.cookie['_safe'] = safeid
            res = requests.get(url, proxies=proxies, cookies=self.cookie, headers=self.headers,
                               allow_redirects=True, timeout=10, impersonate="chrome110")
            html = res.text.encode('utf-8')
            doc = pq(html)
            page_title = doc('head>title').text()
            if "98堂" in page_title:
                return html
        return None

    def crawler_tid_list(self, url):
        try:
            html = self.get_original(url)
            if html:
                doc = pq(html)
                items = doc("div.n5_htnrys.cl")[1:]
                id_list = []
                for item in items:
                    pq_item = pq(item)
                    link = pq_item("div a").eq(0).attr('href')  # 提取href属性
                    parsed_url = urlparse(link)
                    query_params = parse_qs(parsed_url.query)  # 解析为字典（值为列表）
                    tid = query_params.get('tid', [''])[0]
                    id_list.append(int(tid))
                return id_list
        except Exception as e:
            logger.error(f"抓取{url}失败:{e}")
        return []

    def crawler_detail(self, url):
        try:
            html = self.get_original(url)
            if html:
                doc = pq(html)
                all_text = doc('div.blockcode').text()
                magnet_pattern = r'magnet:\?xt=urn:btih:[0-9a-fA-F]+'
                match = re.search(magnet_pattern, all_text)
                magnet = None
                if match:
                    magnet = match.group()
                if not magnet:
                    torrent = doc("a:contains('.torrent')").eq(0)
                    if torrent:
                        torrent_url = torrent.attr('href')
                        magnet = self.parse_torrent_get_magnet(url, f"https://sehuatang.org/{torrent_url}")
                if magnet:
                    date = extract_exact_datetime(html)
                    size = extract_and_convert_video_size(html)
                    category = extract_bracket_content(html)
                    title = doc('h2.n5_bbsnrbt').text()
                    pattern = r"^\[.*?\]"
                    title = re.sub(pattern, "", title).strip()
                    img_elements = doc('div.message img')
                    img_src_list = []
                    for img in img_elements.items():
                        src = img.attr('src')
                        if src:
                            img_src_list.append(src.strip())
                    return {
                        "title": title,
                        "category": category,
                        "publish_date": date,
                        "magnet": magnet,
                        "preview_images": ",".join(img_src_list),
                        "size": size
                    }
        except Exception as e:
            logger.error(f"抓取{url}失败:{e}")
        return {}

    def parse_torrent_get_magnet(self, refer, torrent_source, is_local=False):
        proxies = {
            "http": config_manager.get().PROXY,
            "https": config_manager.get().PROXY
        }
        try:
            torrent_bin = None
            if is_local:
                with open(torrent_source, "rb") as f:
                    torrent_bin = f.read()
                if len(torrent_bin) == 0:
                    logger.error("错误：本地 torrent 文件为空")
                    return None
            else:
                header = self.headers
                header['Referer'] = refer
                resp = requests.get(
                    torrent_source,
                    proxies=proxies,
                    cookies=self.cookie,
                    headers=header,
                    allow_redirects=True,
                    timeout=10,
                    impersonate="chrome110"
                )
                resp.raise_for_status()
                torrent_bin = resp.content
                if len(torrent_bin) < 100:
                    logger.error(f"警告：下载内容过小（{len(torrent_bin)} 字节），非合法 torrent 文件")
                    return None

            torrent_dict = bencoder.decode(torrent_bin)
            if b"info" in torrent_dict:
                info_dict = torrent_dict[b"info"]
            elif "info" in torrent_dict:
                info_dict = torrent_dict["info"]
            else:
                logger.error("错误：种子缺少 info 核心字段（非合法 torrent 文件）")
                return None

            info_bin = bencoder.encode(info_dict)
            info_hash = hashlib.sha1(info_bin).digest()
            info_hash_hex = binascii.hexlify(info_hash).decode("utf-8")

            torrent_name = "Unknown_Torrent"
            if b"name" in info_dict:
                torrent_name = info_dict[b"name"]
            elif "name" in info_dict:
                torrent_name = info_dict["name"]

            if isinstance(torrent_name, bytes):
                try:
                    torrent_name = torrent_name.decode("utf-8")
                except UnicodeDecodeError:
                    torrent_name = torrent_name.decode("utf-8", errors="ignore")
            elif isinstance(torrent_name, str):
                pass
            else:
                torrent_name = str(torrent_name)
            encoded_name = urlencode({"dn": torrent_name})[3:]
            magnet_link = f"magnet:?xt=urn:btih:{info_hash_hex}&dn={encoded_name}"
            return magnet_link
        except Exception as e:
            logger.error(f"网络请求失败：{e}")
            return None


sht = SHT()
