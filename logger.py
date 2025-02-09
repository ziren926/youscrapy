import logging
from datetime import datetime
import os

class CustomLogger:
    def __init__(self, output_dir: str):
        # 创建日志目录
        self.logs_dir = os.path.join(output_dir, 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)

        # 设置日志文件名（包含时间戳）
        log_filename = f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_filepath = os.path.join(self.logs_dir, log_filename)

        # 配置日志记录器
        self.logger = logging.getLogger('ChinaTravelScraper')
        self.logger.setLevel(logging.INFO)

        # 创建文件处理器
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def debug(self, message: str):
        self.logger.debug(message)