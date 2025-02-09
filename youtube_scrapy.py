from yt_dlp import YoutubeDL
import time
from typing import List, Dict
from logger import CustomLogger
import json
from datetime import datetime
import random
import os
import warnings
import requests

warnings.filterwarnings("ignore", category=DeprecationWarning)

class YouTubeScraper:
    def __init__(self, logger: CustomLogger, output_dir: str, videos_per_search: int = 2000):
        self.logger = logger
        self.output_dir = output_dir
        self.videos_per_search = videos_per_search

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 记录时间和用户信息
        self.start_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.username = os.getenv('USER', 'ziren926')
        self.logger.info(f"Current Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): {self.start_datetime}")
        self.logger.info(f"Current User's Login: {self.username}")

        # YouTube配置
        self.base_ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['zh-Hans', 'zh-CN', 'zh', 'en'],
            'skip_download': True,
            'extract_flat': 'in_playlist',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            }
        }

    def _extract_subtitle_text(self, subtitle_json: str) -> str:
        """从字幕JSON中提取纯文本"""
        try:
            # 将字符串转换为JSON对象
            subtitle_data = json.loads(subtitle_json)

            # 提取文本
            text_parts = []

            # 处理events数组
            if 'events' in subtitle_data:
                for event in subtitle_data['events']:
                    if 'segs' in event:
                        for seg in event['segs']:
                            if 'utf8' in seg:
                                # 清理文本
                                text = seg['utf8'].strip()
                                if text and text != '\n':
                                    text_parts.append(text)

            # 连接所有文本，用空格分隔
            return ' '.join(text_parts)
        except Exception as e:
            self.logger.error(f"解析字幕JSON失败: {str(e)}")
            return ""

    def _process_subtitles(self, subtitles: Dict) -> str:
        """处理字幕数据，将其转换为纯文本"""
        if not subtitles:
            return "无字幕"

        processed_subs = []

        # 处理手动字幕
        if 'manual' in subtitles:
            for lang, content in subtitles['manual'].items():
                if content:
                    text = self._extract_subtitle_text(content)
                    if text:
                        processed_subs.append(f"手动字幕_{lang}：{text}")

        # 处理自动字幕
        if 'auto' in subtitles:
            for lang, content in subtitles['auto'].items():
                if content:
                    text = self._extract_subtitle_text(content)
                    if text:
                        processed_subs.append(f"自动字幕_{lang}：{text}")

        return "\t".join(processed_subs) if processed_subs else "无字幕"

    def _get_video_data(self, video_url: str) -> Dict:
        """获取视频详细信息和字幕"""
        try:
            with YoutubeDL(self.base_ydl_opts) as ydl:
                self.logger.info("正在获取视频信息和字幕...")
                info = ydl.extract_info(video_url, download=False)

                subtitles = {
                    'manual': {},
                    'auto': {}
                }

                # 获取手动字幕
                if info.get('subtitles'):
                    for lang, formats in info['subtitles'].items():
                        if formats:
                            try:
                                # 优先使用 json3 格式
                                sub_format = next((f for f in formats if f['ext'] == 'json3'), formats[0])
                                response = requests.get(sub_format['url'])
                                if response.status_code == 200:
                                    subtitles['manual'][lang] = response.text
                            except Exception as e:
                                self.logger.error(f"获取手动字幕失败 ({lang}): {str(e)}")

                # 获取自动字幕
                if info.get('automatic_captions'):
                    for lang, formats in info['automatic_captions'].items():
                        if formats:
                            try:
                                sub_format = next((f for f in formats if f['ext'] == 'json3'), formats[0])
                                response = requests.get(sub_format['url'])
                                if response.status_code == 200:
                                    subtitles['auto'][lang] = response.text
                            except Exception as e:
                                self.logger.error(f"获取自动字幕失败 ({lang}): {str(e)}")

                return {
                    'info': info,
                    'subtitles': subtitles
                }

        except Exception as e:
            self.logger.error(f"获取视频数据失败: {str(e)}")
            return None

    def _save_video_data(self, video_data: Dict, file_path: str):
        """保存视频数据到文件"""
        try:
            # 确保所有字段都有默认值
            default_video_data = {
                '序号': '',
                '搜索关键词': '',
                '关键词序号': '',
                '爬取时间': '',
                '视频ID': '',
                '标题': '',
                '频道名': '',
                '频道ID': '',
                '发布时间': '',
                '视频链接': '',
                '缩略图链接': '',
                '视频时长': '',
                '观看次数': 0,
                '点赞数': 0,
                '评论数': 0,
                '描述': '',
                '处理状态': '',
                '字幕内容': '无字幕'
            }

            # 更新默认值
            default_video_data.update(video_data)

            # 构建数据字段，确保所有值都是字符串类型
            data_fields = [
                str(default_video_data['序号']),
                str(default_video_data['搜索关键词']),
                str(default_video_data['关键词序号']),
                str(default_video_data['爬取时间']),
                str(default_video_data['视频ID']),
                str(default_video_data['标题']).replace('\n', ' ').replace('\t', ' '),
                str(default_video_data['频道名']).replace('\n', ' ').replace('\t', ' '),
                str(default_video_data['频道ID']),
                str(default_video_data['发布时间']),
                str(default_video_data['视频链接']),
                str(default_video_data['缩略图链接']),
                str(default_video_data['视频时长']),
                str(default_video_data['观看次数']),
                str(default_video_data['点赞数']),
                str(default_video_data['评论数']),
                str(default_video_data['描述']).replace('\n', ' ').replace('\t', ' '),
                str(default_video_data['处理状态']),
                str(default_video_data['字幕内容'])
            ]

            # 写入数据
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\t'.join(data_fields) + '\n')
                f.flush()
                self.logger.info(f"已保存数据到: {file_path}")

        except Exception as e:
            self.logger.error(f"保存数据时出错: {str(e)}")
            self.logger.error(f"问题数据: {video_data}")

    def _process_single_video(self, video_info: Dict, term: str, term_index: int,
                              global_index: int, output_file: str) -> bool:
        """处理单个视频"""
        try:
            video_id = video_info.get('id', '')
            if not video_id:
                return False

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # 基本信息
            video_data = {
                '序号': global_index,
                '搜索关键词': term,
                '关键词序号': term_index,
                '爬取时间': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                '视频ID': video_id,
                '标题': video_info.get('title', ''),
                '频道名': video_info.get('uploader', ''),
                '频道ID': video_info.get('channel_id', ''),
                '发布时间': video_info.get('upload_date', ''),
                '视频链接': video_url,
                '缩略图链接': video_info.get('thumbnail', ''),
                '视频时长': video_info.get('duration_string', ''),
                '观看次数': video_info.get('view_count', 0),
                '点赞数': video_info.get('like_count', 0),
                '评论数': video_info.get('comment_count', 0),
                '描述': video_info.get('description', ''),
                '处理状态': '开始处理',
                '字幕内容': '无字幕'  # 设置默认值
            }

            # 获取字幕数据
            detailed_data = self._get_video_data(video_url)
            if detailed_data and detailed_data.get('subtitles'):
                subtitles_content = self._process_subtitles(detailed_data['subtitles'])
                if subtitles_content:
                    video_data['字幕内容'] = subtitles_content
                    video_data['处理状态'] = '处理完成'

            # 保存数据
            self._save_video_data(video_data, output_file)
            return True

        except Exception as e:
            self.logger.error(f"处理视频时出错: {str(e)}")
            try:
                if 'video_data' in locals():
                    video_data['处理状态'] = f'处理失败: {str(e)}'
                    video_data['字幕内容'] = '获取失败'
                    self._save_video_data(video_data, output_file)
            except:
                pass
            return False

    def fetch_videos(self, search_terms: List[str], output_file: str):
        """获取视频数据"""
        total_count = 0
        global_index = 0

        # 写入表头
        headers = [
            '序号', '搜索关键词', '关键词序号', '爬取时间', '视频ID', '标题',
            '频道名', '频道ID', '发布时间', '视频链接', '缩略图链接',
            '视频时长', '观看次数', '点赞数', '评论数', '描述', '处理状态', '字幕内容'
        ]
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\t'.join(headers) + '\n')

        search_ydl_opts = {**self.base_ydl_opts, 'extract_flat': True}

        for term_index, term in enumerate(search_terms, 1):
            self.logger.info(f"\n===== 正在处理第 {term_index}/{len(search_terms)} 个搜索词: {term} =====")
            self.logger.info(f"计划获取 {self.videos_per_search} 个视频")

            try:
                with YoutubeDL(search_ydl_opts) as ydl:
                    self.logger.info("正在搜索视频列表...")
                    results = ydl.extract_info(
                        f"ytsearch{self.videos_per_search}:{term}",
                        download=False
                    )

                    if results and 'entries' in results:
                        videos = [v for v in results['entries'] if v]
                        self.logger.info(f"找到 {len(videos)} 个视频")

                        for video in videos:
                            global_index += 1
                            self.logger.info(f"\n----- 处理第 {global_index} 个视频 -----")
                            self.logger.info(f"视频标题: {video.get('title', '')[:50]}")

                            if self._process_single_video(video, term, term_index, global_index, output_file):
                                total_count += 1
                                self.logger.info(f"视频处理成功 ({total_count}/{global_index})")

                            delay = random.uniform(3, 5)
                            self.logger.info(f"等待 {delay:.1f} 秒后继续...")
                            time.sleep(delay)

            except Exception as e:
                self.logger.error(f"处理搜索词 '{term}' 时出错: {str(e)}")
                continue

            if term != search_terms[-1]:
                delay = random.uniform(5, 10)
                self.logger.info(f"等待 {delay:.1f} 秒后处理下一个关键词...")
                time.sleep(delay)

        self.logger.info(f"\n===== 所有搜索完成 =====")
        self.logger.info(f"总共尝试处理: {global_index} 个视频")
        self.logger.info(f"成功处理: {total_count} 个视频")

        return total_count