#!/usr/bin/env python3
"""
雷达存储系统 - 健康检查与状态验证工具
部署后运行此脚本检查系统各组件的健康状态
"""

import sys
import json
import time
import urllib.request
import urllib.error

# ============================================================
# 配置
# ============================================================
SERVICES = {
    'MinIO-Node1': {
        'url': 'http://localhost:9011/minio/health/live',
        'type': 'minio',
        'expected': True
    },
    'MinIO-Node2': {
        'url': 'http://localhost:9012/minio/health/live',
        'type': 'minio'
    },
    'MinIO-Node3': {
        'url': 'http://localhost:9013/minio/health/live',
        'type': 'minio'
    },
    'MinIO-Node4': {
        'url': 'http://localhost:9014/minio/health/live',
        'type': 'minio'
    },
    'MinIO-Cold': {
        'url': 'http://localhost:9020/minio/health/live',
        'type': 'minio'
    },
    'Nginx-LB1': {
        'url': 'http://localhost:18080/health',
        'type': 'nginx'
    },
    'Nginx-LB2': {
        'url': 'http://localhost:28080/health',
        'type': 'nginx'
    },
    'Nginx-LB1-Status': {
        'url': 'http://localhost:19090/status',
        'type': 'nginx-status'
    },
    'Nginx-LB2-Status': {
        'url': 'http://localhost:29090/status',
        'type': 'nginx-status'
    },
    'Monitor': {
        'url': 'http://localhost:8888/health',
        'type': 'monitor'
    }
}


def check_service(name, config):
    """检查单个服务的健康状态"""
    try:
        req = urllib.request.Request(
            config['url'],
            method='GET',
            headers={'User-Agent': 'HealthCheck/1.0'}
        )
        resp = urllib.request.urlopen(req, timeout=5)
        status_code = resp.getcode()
        resp.read()  # 消耗响应
        return status_code == 200
    except Exception as e:
        return False


def print_result(name, status, service_type):
    """打印检查结果"""
    icon = {
        'minio': '📦',
        'nginx': '🌐',
        'nginx-status': '📊',
        'monitor': '📈'
    }.get(service_type, '🔌')
    
    status_icon = '✅' if status else '❌'
    print(f"  {status_icon} {icon} {name}: {'运行中' if status else '未响应'}")


def main():
    print("=" * 60)
    print("  雷达存储系统 - 健康检查工具")
    print("=" * 60)
    print()
    
    retry_count = 3
    all_ok = True
    
    for service_name, config in SERVICES.items():
        ok = False
        for attempt in range(retry_count):
            ok = check_service(service_name, config)
            if ok:
                break
            if attempt < retry_count - 1:
                time.sleep(2)
        
        print_result(service_name, ok, config.get('type', ''))
        if not ok:
            all_ok = False
    
    print()
    print("-" * 60)
    
    if all_ok:
        print("  ✅ 所有服务运行正常！")
    else:
        print("  ⚠️  部分服务未响应，请检查容器状态")
    
    print("=" * 60)
    print()
    
    # 打印访问地址
    print("📋 访问地址:")
    print(f"  MinIO Console:    http://localhost:19111 ~ 19114 (节点1~4)")
    print(f"  MinIO Cold:       http://localhost:19220")
    print(f"  S3 API (主):      http://localhost:18080")
    print(f"  S3 API (备):      http://localhost:28080")
    print(f"  Nginx状态(主):    http://localhost:19090/status")
    print(f"  Nginx状态(备):    http://localhost:29090/status")
    print(f"  监控面板:          http://localhost:8888")
    print()
    print("📡 雷达模拟器已自动启动 (20部雷达)")
    print()
    
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
