import json
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import os
from datetime import datetime
from logger import CustomLogger

class DataProcessor:
    def __init__(self, output_dir: str, logger: Optional[CustomLogger] = None):
        self.output_dir = output_dir
        self.logger = logger
        os.makedirs(output_dir, exist_ok=True)

    def _log(self, level: str, message: str):
        """内部日志记录方法"""
        if self.logger:
            if level == 'info':
                self.logger.info(message)
            elif level == 'error':
                self.logger.error(message)
            elif level == 'warning':
                self.logger.warning(message)
        else:
            print(f"{level.upper()}: {message}")

    def save_data(self, data: List[Dict], filename: str):
        """保存原始数据为 JSON 格式"""
        self._log('info', f"开始保存数据到文件: {filename}")
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._log('info', f"数据已成功保存到: {filepath}")

    def _convert_to_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """将数值列转换为数值类型"""
        numeric_columns = ['view_count', 'like_count', 'comment_count', 'share_count']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    def _validate_data(self, df: pd.DataFrame) -> bool:
        """验证数据框是否包含必要的列"""
        required_columns = ['platform']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            self._log('error', f"数据中缺少必要的列: {', '.join(missing_columns)}")
            return False
        return True

    def _prepare_dataframe(self, youtube_data: List[Dict], tiktok_data: List[Dict]) -> pd.DataFrame:
        """准备和验证数据框"""
        try:
            # 确保数据不为空
            if not youtube_data and not tiktok_data:
                self._log('warning', "YouTube和TikTok数据都为空")
                return pd.DataFrame()

            # 为数据添加平台标识
            processed_youtube_data = [
                {**item, 'platform': 'youtube'} for item in youtube_data
            ] if youtube_data else []

            processed_tiktok_data = [
                {**item, 'platform': 'tiktok'} for item in tiktok_data
            ] if tiktok_data else []

            # 合并数据
            all_data = processed_youtube_data + processed_tiktok_data

            # 创建DataFrame
            df = pd.DataFrame(all_data)

            # 打印数据框信息用于调试
            self._log('info', f"数据框列: {df.columns.tolist()}")
            self._log('info', f"数据框大小: {df.shape}")

            return df

        except Exception as e:
            self._log('error', f"准备数据框时发生错误: {str(e)}")
            raise

    def generate_report(self, youtube_data: List[Dict], tiktok_data: List[Dict], filename: str):
        """生成数据分析报告"""
        self._log('info', "开始生成数据分析报告...")

        try:
            # 准备数据框
            df = self._prepare_dataframe(youtube_data, tiktok_data)

            # 验证数据
            if df.empty:
                self._log('error', "没有可用的数据来生成报告")
                return

            if not self._validate_data(df):
                self._log('error', "数据验证失败")
                return

            # 转换数值列
            df = self._convert_to_numeric(df)

            # 创建 Excel 写入器
            filepath = os.path.join(self.output_dir, filename)
            self._log('info', "创建 Excel 报告...")

            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                # 总体概况
                self._log('info', "生成总体概况表...")
                self._create_overview_sheet(df, writer)

                # 平台数据对比
                self._log('info', "生成平台数据对比表...")
                self._create_platform_comparison_sheet(df, writer)

                # 详细数据
                self._log('info', "生成详细数据表...")
                self._create_detailed_data_sheet(df, writer)

                # 地理分布
                self._log('info', "生成地理分布表...")
                self._create_geographic_distribution_sheet(df, writer)

            self._log('info', f"数据分析报告已成功生成: {filepath}")

        except Exception as e:
            self._log('error', f"生成报告时发生错误: {str(e)}")
            raise

    def _create_overview_sheet(self, df: pd.DataFrame, writer: pd.ExcelWriter):
        """创建总体概况表"""
        try:
            # 创建一个基础的概况数据
            overview_data = {
                '总视频数': len(df),
                '数据获取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 添加平台相关的统计
            if 'platform' in df.columns:
                overview_data.update({
                    'YouTube视频数': len(df[df['platform'] == 'youtube']),
                    'TikTok视频数': len(df[df['platform'] == 'tiktok'])
                })

            # 添加数值统计
            if 'view_count' in df.columns:
                overview_data['平均观看数'] = df['view_count'].mean()
            if 'like_count' in df.columns:
                overview_data['平均点赞数'] = df['like_count'].mean()

            # 创建概况表
            overview = pd.DataFrame([overview_data])
            overview.to_excel(writer, sheet_name='总体概况', index=False)
            self._log('info', "总体概况表已创建")
        except Exception as e:
            self._log('error', f"创建总体概况表时发生错误: {str(e)}")
            raise

    def _create_platform_comparison_sheet(self, df: pd.DataFrame, writer: pd.ExcelWriter):
        """创建平台对比表"""
        try:
            if 'platform' not in df.columns:
                self._log('warning', "缺少platform列，跳过创建平台对比表")
                return

            numeric_columns = ['view_count', 'like_count', 'comment_count']
            available_columns = [col for col in numeric_columns if col in df.columns]

            if not available_columns:
                self._log('warning', "没有可用于创建平台对比表的数值列")
                return

            agg_dict = {col: ['count', 'mean', 'sum'] for col in available_columns}
            platform_stats = df.groupby('platform').agg(agg_dict).round(2)
            platform_stats.to_excel(writer, sheet_name='平台对比')
            self._log('info', "平台对比表已创建")
        except Exception as e:
            self._log('error', f"创建平台对比表时发生错误: {str(e)}")
            raise

    def _create_detailed_data_sheet(self, df: pd.DataFrame, writer: pd.ExcelWriter):
        """创建详细数据表"""
        try:
            possible_columns = [
                'platform', 'video_id', 'title', 'view_count', 'like_count',
                'comment_count', 'publish_time', 'channel_title', 'channel_country'
            ]

            # 只使用实际存在的列
            available_columns = [col for col in possible_columns if col in df.columns]

            if not available_columns:
                self._log('warning', "没有可用于创建详细数据表的列")
                return

            df[available_columns].to_excel(writer, sheet_name='详细数据', index=False)
            self._log('info', "详细数据表已创建")
        except Exception as e:
            self._log('error', f"创建详细数据表时发生错误: {str(e)}")
            raise

    def _create_geographic_distribution_sheet(self, df: pd.DataFrame, writer: pd.ExcelWriter):
        """创建地理分布表"""
        try:
            if 'channel_country' not in df.columns:
                self._log('warning', "缺少channel_country列，跳过创建地理分布表")
                return

            agg_columns = {'video_id': 'count'}
            if 'view_count' in df.columns:
                agg_columns['view_count'] = 'sum'
            if 'like_count' in df.columns:
                agg_columns['like_count'] = 'sum'

            geo_stats = df.groupby('channel_country').agg(agg_columns).round(2)
            geo_stats.to_excel(writer, sheet_name='地理分布')
            self._log('info', "地理分布表已创建")
        except Exception as e:
            self._log('error', f"创建地理分布表时发生错误: {str(e)}")
            raise