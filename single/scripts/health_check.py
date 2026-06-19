#!/usr/bin/env python3
"""
雷达存储系统 - 健康检查工具
检查热/冷 MinIO 节点和 Nginx 状态
"""

import sys, json, time, urllib.request

SERVICES = {
    'MinIO-热数据(NVMe)':  {'url': 'http://localhost:9010/minio/health/live', 'type': 'minio'},
    'MinIO-冷数据(HDD)':   {'url': 'http://localhost:9020/minio/health/live', 'type': 'minio'},
    'Nginx-负载均衡':       {'url': 'http://localhost:18080/',                 'type': 'nginx'},
    '监控面板':             {'url': 'http://localhost:8888/health',            'type': 'monitor'},
}

def check(name, conf):
    try:
        r = urllib.request.urlopen(urllib.request.Request(conf['url']), timeout=5)
        return r.getcode() == 200
    except:
        return False

def main():
    print('=' * 50)
    print('  雷达存储系统 - 健康检查')
    print('=' * 50)
    all_ok = True
    for name, conf in SERVICES.items():
        ok = False
        for _ in range(3):
            ok = check(name, conf)
            if ok: break
            time.sleep(2)
        icon = {'minio':'📦','nginx':'🌐','monitor':'📈'}.get(conf['type'], '🔌')
        print(f"  {'✅' if ok else '❌'} {icon} {name}: {'正常' if ok else '未响应'}")
        if not ok: all_ok = False
    print()
    if all_ok:
        print('  ✅ 所有服务正常')
    else:
        print('  ⚠️  部分服务异常')
    print('=' * 50)
    print()
    print('📋 访问地址:')
    print('  MinIO 热:    http://localhost:9010')
    print('  MinIO 冷:    http://localhost:9020')
    print('  Nginx:       http://localhost:18080')
    print('  监控面板:    http://localhost:8888')
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
