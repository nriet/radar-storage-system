#!/usr/bin/env python3
"""生成模拟雷达 NetCDF 文件并上传到 MinIO"""

import numpy as np
from netCDF4 import Dataset
from datetime import datetime, timezone
import os, sys, boto3, io
from botocore.config import Config

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'http://localhost:9010')
MINIO_ACCESS_KEY = 'radaradmin'
MINIO_SECRET_KEY = 'RadarAdmin@2024!'
BUCKET = 'radar-data'
OUTPUT_DIR = '/tmp/netcdf_output'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def gen_netcdf(radar_id, time_str, filepath):
    """生成模拟雷达回波 NetCDF 文件"""
    nc = Dataset(filepath, 'w', format='NETCDF4')

    # 维度
    nc.createDimension('time', None)
    nc.createDimension('range', 200)
    nc.createDimension('azimuth', 360)

    # 变量
    times = nc.createVariable('time', 'f8', ('time',))
    times.units = 'seconds since 1970-01-01 00:00:00'
    times.standard_name = 'time'

    ranges = nc.createVariable('range', 'f4', ('range',))
    ranges.units = 'meters'
    ranges.long_name = 'distance from radar'

    azis = nc.createVariable('azimuth', 'f4', ('azimuth',))
    azis.units = 'degrees'
    azis.long_name = 'azimuth angle'

    refl = nc.createVariable('reflectivity', 'f4', ('time', 'range', 'azimuth'))
    refl.units = 'dBZ'
    refl.long_name = 'Radar Reflectivity'
    refl.standard_name = 'equivalent_reflectivity_factor'

    vel = nc.createVariable('velocity', 'f4', ('time', 'range', 'azimuth'))
    vel.units = 'm/s'
    vel.long_name = 'Radial Velocity'
    vel.standard_name = 'radial_velocity'

    sw = nc.createVariable('spectrum_width', 'f4', ('time', 'range', 'azimuth'))
    sw.units = 'm/s'
    sw.long_name = 'Spectrum Width'

    # 全局属性
    nc.title = f'Simulated Radar Data - {radar_id}'
    nc.institution = 'Radar Data Storage System'
    nc.source = 'Simulation'
    nc.Conventions = 'CF-1.0'
    nc.radar_id = radar_id
    nc.radar_latitude = np.random.uniform(22, 42)
    nc.radar_longitude = np.random.uniform(100, 120)
    nc.radar_altitude = np.random.randint(0, 500)
    nc.wavelength = 0.05  # C-band
    nc.created = time_str

    # 填充数据
    times[:] = [datetime.now(timezone.utc).timestamp()]
    ranges[:] = np.linspace(100, 30000, 200)
    azis[:] = np.linspace(0, 359, 360)

    # 模拟回波：高斯形状目标 + 噪声
    r_grid, a_grid = np.meshgrid(ranges[:], azis[:], indexing='ij')
    target_r = np.random.uniform(5000, 25000)
    target_a = np.random.uniform(0, 360)
    target_z = 45 * np.exp(-((r_grid - target_r)**2 / (2 * 2000**2) + (a_grid - target_a)**2 / (2 * 30**2)))
    noise = np.random.normal(-10, 5, (200, 360))
    refl[0, :, :] = np.maximum(target_z + noise, -20)

    vel[0, :, :] = np.random.normal(0, 5, (200, 360))
    sw[0, :, :] = np.abs(np.random.normal(2, 1, (200, 360)))

    nc.close()
    print(f'  ✅ {os.path.basename(filepath)}  ({os.path.getsize(filepath)/1024:.0f}KB)')

def upload_to_minio(filepath, object_key):
    s3 = boto3.client(
        's3', endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(connect_timeout=10, read_timeout=60),
        verify=False
    )
    with open(filepath, 'rb') as f:
        s3.put_object(Bucket=BUCKET, Key=object_key, Body=f,
                      ContentType='application/x-netcdf')
    print(f'  📤 {object_key}')

# 生成 5 个雷达 × 每个 3 个时间片 = 15 个文件
RADARS = ['RADAR-EAST-001', 'RADAR-WEST-002', 'RADAR-SOUTH-003', 'RADAR-NORTH-004', 'RADAR-CENTER-005']
TIMESLOTS = ['20260620_120000', '20260620_120500', '20260620_121000']

print('=== 生成 NetCDF 文件 ===')
for rid in RADARS:
    for ts in TIMESLOTS:
        fname = f'{rid}_{ts}.nc'
        fpath = os.path.join(OUTPUT_DIR, fname)
        gen_netcdf(rid, ts, fpath)

print(f'\n=== 上传到 MinIO ({MINIO_ENDPOINT}/{BUCKET}) ===')
for rid in RADARS:
    for ts in TIMESLOTS:
        fname = f'{rid}_{ts}.nc'
        fpath = os.path.join(OUTPUT_DIR, fname)
        object_key = f'radar-netcdffiles/{rid}/{ts[:8]}/{fname}'
        upload_to_minio(fpath, object_key)

print(f'\n✅ 完成：{len(RADARS) * len(TIMESLOTS)} 个 NetCDF 文件已上传')
