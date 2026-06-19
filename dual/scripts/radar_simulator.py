#!/usr/bin/env python3
"""
雷达数据模拟器
模拟20-50部雷达设备向MinIO集群写入探测数据
支持: 不同类型雷达数据生成、断点续传、数据分片上传
"""

import os
import sys
import json
import time
import uuid
import hashlib
import logging
import threading
import random
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
import numpy as np
from botocore.config import Config as BotoConfig

# ============================================================
# 配置
# ============================================================
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'nginx-lb1:18080')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'radar-simulator')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'RadarSim@2024!')
RADAR_COUNT = int(os.getenv('RADAR_COUNT', '20'))
SIMULATION_INTERVAL = int(os.getenv('SIMULATION_INTERVAL', '30'))  # 秒
USE_SSL = os.getenv('USE_SSL', 'false').lower() == 'true'

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('radar-simulator')


class RadarConfig:
    """雷达设备配置"""

    # 雷达型号及参数
    RADAR_TYPES = {
        'weather': {
            'name': '气象雷达',
            'data_size_range': (1, 5),       # MB
            'interval': 300,                   # 5分钟
            'prefix': 'weather',
            'tags': {'radar-type': 'weather', 'priority': 'high'}
        },
        'surveillance': {
            'name': '监视雷达',
            'data_size_range': (5, 20),       # MB
            'interval': 60,                    # 1分钟
            'prefix': 'surveillance',
            'tags': {'radar-type': 'surveillance', 'priority': 'critical'}
        },
        'imaging': {
            'name': '成像雷达',
            'data_size_range': (10, 50),      # MB
            'interval': 600,                   # 10分钟
            'prefix': 'imaging',
            'tags': {'radar-type': 'imaging', 'priority': 'medium'}
        },
        'tracking': {
            'name': '跟踪雷达',
            'data_size_range': (0.5, 2),      # MB
            'interval': 10,                    # 10秒
            'prefix': 'tracking',
            'tags': {'radar-type': 'tracking', 'priority': 'critical'}
        }
    }

    @staticmethod
    def generate_radar_id(index):
        """生成雷达ID"""
        region = random.choice(['EAST', 'WEST', 'SOUTH', 'NORTH', 'CENTER'])
        return f"RADAR-{region}-{index:04d}"

    @staticmethod
    def assign_radar_type():
        """分配雷达类型（概率权重）"""
        types = ['weather', 'surveillance', 'imaging', 'tracking']
        weights = [0.25, 0.30, 0.20, 0.25]
        return random.choices(types, weights=weights)[0]


def generate_radar_data(radar_id, radar_type, data_size_mb):
    """
    生成模拟雷达数据
    生成类似真实雷达回波数据的二进制数据
    
    Args:
        radar_id: 雷达ID
        radar_type: 雷达类型
        data_size_mb: 数据大小(MB)
    """
    num_samples = int(data_size_mb * 1024 * 1024 / 8)  # 每个采样点8字节
    
    # 生成模拟雷达回波数据
    timestamp = datetime.now(timezone.utc)
    base_signal = np.sin(np.linspace(0, 2 * np.pi * 100, num_samples))
    noise = np.random.normal(0, 0.1, num_samples)
    signal = base_signal + noise
    
    # 添加目标回波
    num_targets = random.randint(1, 5)
    for _ in range(num_targets):
        target_pos = random.randint(0, num_samples - 100)
        target_amp = random.uniform(0.5, 2.0)
        signal[target_pos:target_pos + 100] += target_amp
    
    # 数据包头
    header = {
        'radar_id': radar_id,
        'radar_type': radar_type,
        'timestamp': timestamp.isoformat(),
        'data_size_bytes': len(signal) * 8,
        'sample_rate': random.randint(1000, 10000),
        'frequency': random.uniform(1.0, 10.0),
        'checksum': None
    }
    
    # 序列化数据
    header_bytes = json.dumps(header).encode('utf-8')
    data_bytes = signal.astype(np.float64).tobytes()
    
    # 计算校验和
    checksum = hashlib.sha256(data_bytes).hexdigest()
    header['checksum'] = checksum
    
    # 最终数据包: 头部长度(4字节) + 头部JSON + 二进制数据
    header_json = json.dumps(header).encode('utf-8')
    packet = len(header_json).to_bytes(4, 'big') + header_json + data_bytes
    
    return packet


def create_metadata(radar_id, radar_type, radar_config):
    """创建数据元信息"""
    config = RadarConfig.RADAR_TYPES[radar_type]
    return {
        'radar_id': radar_id,
        'radar_type': radar_type,
        'radar_name': config['name'],
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'data_version': '2.1',
        'data_format': 'binary/radar-raw',
        'calibration_status': random.choice(['calibrated', 'pending', 'verified']),
        'location': {
            'latitude': round(random.uniform(-90, 90), 6),
            'longitude': round(random.uniform(-180, 180), 6),
            'altitude': random.randint(0, 3000)
        }
    }


def upload_radar_data(s3_client, bucket, radar_id, radar_type, data):
    """
    上传雷达数据到MinIO
    
    支持分片上传和断点续传
    """
    timestamp = datetime.now()
    config = RadarConfig.RADAR_TYPES[radar_type]
    
    # 文件路径: radar-type/radar-id/date/hour/minute/radar-id_timestamp_uuid.bin
    date_path = timestamp.strftime('%Y/%m/%d')
    time_path = timestamp.strftime('%H/%M')
    file_uuid = str(uuid.uuid4())[:8]
    object_key = (
        f"{config['prefix']}/{radar_id}/"
        f"{date_path}/{time_path}/"
        f"{radar_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{file_uuid}.radar"
    )
    
    # 元数据标签
    tags = dict(config['tags'])
    tags['radar-id'] = radar_id
    tags['generated-at'] = timestamp.strftime('%Y%m%d%H%M%S')
    
    try:
        # 对于大文件使用分片上传
        if len(data) > 50 * 1024 * 1024:  # > 50MB
            return upload_multipart(s3_client, bucket, object_key, data, tags)
        else:
            # 直接上传
            s3_client.put_object(
                Bucket=bucket,
                Key=object_key,
                Body=data,
                ContentType='application/octet-stream',
                Metadata=tags,
                Tagging='&'.join([f'{k}={v}' for k, v in tags.items()])
            )
            return object_key, len(data)
    except Exception as e:
        logger.error(f"上传失败 [{radar_id}]: {str(e)}")
        raise


def upload_multipart(s3_client, bucket, object_key, data, tags):
    """分片上传大文件"""
    part_size = 10 * 1024 * 1024  # 10MB per part
    
    # 创建分片上传
    mpu = s3_client.create_multipart_upload(
        Bucket=bucket,
        Key=object_key,
        ContentType='application/octet-stream',
        Metadata=tags
    )
    
    upload_id = mpu['UploadId']
    parts = []
    
    try:
        # 上传各个分片
        for i in range(0, len(data), part_size):
            part_number = len(parts) + 1
            chunk = data[i:i + part_size]
            
            part = s3_client.upload_part(
                Bucket=bucket,
                Key=object_key,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=chunk
            )
            parts.append({
                'PartNumber': part_number,
                'ETag': part['ETag']
            })
        
        # 完成分片上传
        s3_client.complete_multipart_upload(
            Bucket=bucket,
            Key=object_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        
        return object_key, len(data)
    except Exception as e:
        # 中止上传
        try:
            s3_client.abort_multipart_upload(
                Bucket=bucket,
                Key=object_key,
                UploadId=upload_id
            )
        except:
            pass
        raise e


class RadarSimulator:
    """雷达模拟器主类"""
    
    def __init__(self):
        # 创建S3客户端
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"{'https' if USE_SSL else 'http'}://{MINIO_ENDPOINT}",
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            config=BotoConfig(
                connect_timeout=10,
                read_timeout=60,
                retries={'max_attempts': 3},
                max_pool_connections=50
            ),
            verify=False
        )
        
        # 初始化雷达设备
        self.radars = []
        for i in range(RADAR_COUNT):
            radar_id = RadarConfig.generate_radar_id(i + 1)
            radar_type = RadarConfig.assign_radar_type()
            self.radars.append({
                'id': radar_id,
                'type': radar_type,
                'config': RadarConfig.RADAR_TYPES[radar_type],
                'active': True,
                'total_uploads': 0,
                'total_bytes': 0
            })
        
        self.stats = {
            'start_time': time.time(),
            'total_uploads': 0,
            'total_bytes': 0,
            'failed_uploads': 0,
            'buckets': ['radar-data', 'radar-archive', 'radar-backup']
        }
    
    def simulate_radar(self, radar):
        """模拟单部雷达的数据生成和上传"""
        if not radar['active']:
            return None
        
        # 根据雷达类型生成不同大小的数据
        size_range = radar['config']['data_size_range']
        data_size_mb = random.uniform(*size_range)
        
        # 随机选择目标桶 (概率权重)
        bucket = random.choices(
            self.stats['buckets'],
            weights=[0.70, 0.20, 0.10]  # 70%实时数据, 20%归档, 10%备份
        )[0]
        
        try:
            # 生成数据
            data = generate_radar_data(radar['id'], radar['type'], data_size_mb)
            
            # 上传数据
            object_key, bytes_uploaded = upload_radar_data(
                self.s3_client, bucket, radar['id'], radar['type'], data
            )
            
            radar['total_uploads'] += 1
            radar['total_bytes'] += bytes_uploaded
            
            self.stats['total_uploads'] += 1
            self.stats['total_bytes'] += bytes_uploaded
            
            logger.info(
                f"✅ [{radar['id']}] {radar['type']} → {bucket}/{object_key} "
                f"({bytes_uploaded / 1024:.1f} KB)"
            )
            
            return object_key, bytes_uploaded
            
        except Exception as e:
            self.stats['failed_uploads'] += 1
            logger.error(f"❌ [{radar['id']}] 上传失败: {str(e)}")
            return None
    
    def run_simulation(self):
        """运行模拟循环"""
        logger.info(f"🚀 雷达数据模拟器启动")
        logger.info(f"📡 雷达数量: {RADAR_COUNT}")
        logger.info(f"⏱  上传间隔: {SIMULATION_INTERVAL} 秒")
        logger.info(f"🔗 MinIO端点: {MINIO_ENDPOINT}")
        
        # 使用线程池并行上传
        max_workers = min(RADAR_COUNT, 20)
        
        cycle = 0
        while True:
            cycle += 1
            cycle_start = time.time()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"📡 模拟周期 #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*60}")
            
            # 并行上传所有雷达数据
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.simulate_radar, radar): radar
                    for radar in self.radars
                }
                for future in as_completed(futures):
                    future.result()
            
            # 打印统计信息
            elapsed = time.time() - self.stats['start_time']
            throughput = self.stats['total_bytes'] / elapsed / 1024 / 1024 if elapsed > 0 else 0
            
            logger.info(f"\n📊 统计信息:")
            logger.info(f"   总上传次数: {self.stats['total_uploads']}")
            logger.info(f"   总数据量: {self.stats['total_bytes'] / 1024 / 1024:.2f} MB")
            logger.info(f"   失败次数: {self.stats['failed_uploads']}")
            logger.info(f"   运行时间: {elapsed:.0f} 秒")
            logger.info(f"   平均吞吐: {throughput:.2f} MB/s")
            
            # 等待下一周期
            cycle_duration = time.time() - cycle_start
            if cycle_duration < SIMULATION_INTERVAL:
                time.sleep(SIMULATION_INTERVAL - cycle_duration)


def main():
    """主函数"""
    simulator = RadarSimulator()
    try:
        simulator.run_simulation()
    except KeyboardInterrupt:
        logger.info("\n🛑 模拟器已停止")
        elapsed = time.time() - simulator.stats['start_time']
        logger.info(f"📊 最终统计:")
        logger.info(f"   运行时间: {elapsed:.0f} 秒")
        logger.info(f"   总上传: {simulator.stats['total_uploads']} 次")
        logger.info(f"   总数据量: {simulator.stats['total_bytes'] / 1024 / 1024:.2f} MB")
        logger.info(f"   失败: {simulator.stats['failed_uploads']} 次")


if __name__ == '__main__':
    main()
