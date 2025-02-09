import os
from datetime import datetime
import time
import signal
import sys
import json
import traceback

def setup_logger():
    """设置日志记录器"""
    try:
        from logger import CustomLogger
        output_dir = "china_travel_data"
        os.makedirs(output_dir, exist_ok=True)
        return CustomLogger(output_dir)
    except Exception as e:
        print(f"设置日志记录器失败: {str(e)}")
        raise

def check_python_version():
    """检查 Python 版本"""
    if sys.version_info < (3, 7):
        raise SystemError("需要 Python 3.7 或更高版本")

def main():
    try:
        # 检查 Python 版本
        check_python_version()

        # 设置日志记录器
        logger = setup_logger()

        # 记录系统信息
        logger.info(f"Python 版本: {sys.version}")
        logger.info(f"运行平台: {sys.platform}")

        # 记录开始时间和用户信息
        start_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username = os.getenv('USER', 'ziren926')
        logger.info(f"开始时间: {start_datetime}")
        logger.info(f"用户: {username}")

        # 导入 YouTubeScraper（在检查完所有依赖后）
        try:
            from youtube_scrapy import YouTubeScraper  # 改为正确的文件名
        except ImportError as e:
            logger.error(f"导入 YouTubeScraper 失败: {str(e)}")
            logger.error("请确保所有依赖都已正确安装")
            raise

        # 设置参数
        videos_per_search = 2000
        output_dir = "china_travel_data"

        # 初始化爬虫
        youtube_scraper = YouTubeScraper(logger, output_dir, videos_per_search)

        # 搜索关键词
        search_terms = ["china travel", "travel china", "china vlog", "中国旅游"]
        logger.info(f"搜索关键词: {', '.join(search_terms)}")
        logger.info(f"每个关键词计划获取 {videos_per_search} 个视频")

        # 创建输出文件
        output_file = os.path.join(output_dir, f"youtube_data_{start_datetime.replace(':', '-').replace(' ', '_')}.txt")

        # 写入元数据
        with open(output_file, 'w', encoding='utf-8') as f:
            metadata = {
                'start_time': start_datetime,
                'username': username,
                'search_terms': search_terms,
                'videos_per_search': videos_per_search,
                'python_version': sys.version,
                'platform': sys.platform
            }
            f.write(json.dumps(metadata, ensure_ascii=False) + '\n')

        # 开始爬取
        start_time = time.time()
        total_videos = youtube_scraper.fetch_videos(search_terms, output_file)

        # 输出统计信息
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"\n爬取完成！")
        logger.info(f"总用时: {duration:.2f} 秒")
        logger.info(f"共处理: {total_videos} 个视频")
        if total_videos > 0:  # 避免除零错误
            logger.info(f"平均每个视频用时: {duration/total_videos:.2f} 秒")
        logger.info(f"所有数据已保存到: {output_file}")

    except KeyboardInterrupt:
        logger.info("\n用户中断程序")
    except Exception as e:
        if 'logger' in locals():
            logger.error(f"程序运行出错: {str(e)}")
            logger.error("详细错误信息:")
            logger.error(traceback.format_exc())
        else:
            print(f"严重错误: {str(e)}")
            print("详细错误信息:")
            print(traceback.format_exc())
    finally:
        if 'logger' in locals():
            logger.info("程序结束")

if __name__ == "__main__":
    main()