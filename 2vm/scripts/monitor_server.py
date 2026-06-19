#!/usr/bin/env python3
"""
雷达存储系统监控服务
提供: 实时数据面板、集群状态、统计信息
"""

import os
import json
import time
import threading
from datetime import datetime, timezone
from collections import defaultdict, deque

import boto3
from botocore.config import Config as BotoConfig
from flask import Flask, jsonify, render_template_string

# ============================================================
# 配置
# ============================================================
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'http://nginx-lb1:18080')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'radar-simulator')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'RadarSim@2024!')
REFRESH_INTERVAL = 10  # 刷新间隔(秒)

app = Flask(__name__)

# 全局状态
state = {
    'cluster_info': {},
    'buckets': [],
    'recent_uploads': deque(maxlen=100),
    'stats': defaultdict(int),
    'throughput_history': deque(maxlen=60),
    'last_update': None,
    'node_status': {}
}


class ClusterMonitor:
    """集群监控器"""
    
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            config=BotoConfig(connect_timeout=5, read_timeout=10),
            verify=False
        )
        
        self.admin_info = {}
        self._running = True
    
    def collect_stats(self):
        """收集集群统计信息"""
        while self._running:
            try:
                # 获取桶列表
                buckets = self.s3.list_buckets()
                state['buckets'] = []
                
                for bucket in buckets.get('Buckets', []):
                    bucket_name = bucket['Name']
                    
                    try:
                        # 获取桶信息
                        tagging = self.s3.get_bucket_tagging(Bucket=bucket_name)
                        tags = {t['Key']: t['Value'] for t in tagging.get('TagSet', [])}
                    except:
                        tags = {}
                    
                    # 获取桶对象数量(近似)
                    try:
                        objects = self.s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1000)
                        obj_count = objects.get('KeyCount', 0)
                        is_truncated = objects.get('IsTruncated', False)
                        
                        # 计算总大小
                        total_size = 0
                        if 'Contents' in objects:
                            total_size = sum(obj.get('Size', 0) for obj in objects['Contents'])
                    except:
                        obj_count = 0
                        total_size = 0
                    
                    state['buckets'].append({
                        'name': bucket_name,
                        'creation_date': bucket['CreationDate'].isoformat() if hasattr(bucket['CreationDate'], 'isoformat') else str(bucket['CreationDate']),
                        'tags': tags,
                        'object_count': obj_count,
                        'total_size': total_size,
                        'has_more': is_truncated
                    })
                
                state['last_update'] = datetime.now(timezone.utc).isoformat()
                
            except Exception as e:
                state['last_error'] = str(e)
            
            time.sleep(REFRESH_INTERVAL)
    
    def stop(self):
        self._running = False


# 启动监控线程
monitor = ClusterMonitor()
monitor_thread = threading.Thread(target=monitor.collect_stats, daemon=True)
monitor_thread.start()


# ============================================================
# 监控页面 - HTML模板
# ============================================================
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>雷达存储系统监控面板</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a1628;
            color: #e0e6ed;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #1a2744 0%, #0d1b3e 100%);
            padding: 20px 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #2a3f6a;
        }
        .header h1 { font-size: 24px; color: #4fc3f7; }
        .header p { color: #8899b4; margin-top: 5px; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }
        .card {
            background: #111d35;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #1e3260;
        }
        .card h3 {
            font-size: 13px;
            color: #6b8db5;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        .card .value {
            font-size: 28px;
            font-weight: bold;
            color: #4fc3f7;
        }
        .card .value.green { color: #66bb6a; }
        .card .value.yellow { color: #ffa726; }
        .card .value.red { color: #ef5350; }
        .card .sub { font-size: 12px; color: #6b8db5; margin-top: 4px; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #1a2744;
            font-size: 13px;
        }
        th { color: #6b8db5; font-weight: 600; }
        tr:hover { background: #0f1f3d; }
        
        .tag {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin: 1px;
        }
        .tag-hot { background: #c62828; color: #ffcdd2; }
        .tag-warm { background: #e65100; color: #ffe0b2; }
        .tag-cold { background: #1565c0; color: #bbdefb; }
        .tag-critical { background: #880e4f; color: #f8bbd0; }
        .tag-high { background: #bf360c; color: #ffccbc; }
        .tag-medium { background: #4a148c; color: #e1bee7; }
        
        .status-bar {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .dot-green { background: #66bb6a; }
        .dot-red { background: #ef5350; }
        .dot-yellow { background: #ffa726; }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #3a5070;
            font-size: 12px;
        }
        .progress-bar {
            width: 100%;
            height: 6px;
            background: #1a2744;
            border-radius: 3px;
            margin-top: 6px;
        }
        .progress-fill {
            height: 100%;
            border-radius: 3px;
            background: linear-gradient(90deg, #4fc3f7, #1de9b6);
            transition: width 0.5s;
        }
        @media (max-width: 600px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📡 雷达存储系统监控面板</h1>
        <p>4节点MinIO集群 | 双Nginx负载均衡 | 分层存储 | 最后更新: <span id="update-time">{{ last_update }}</span></p>
    </div>
    
    <div class="grid">
        <div class="card">
            <h3>📦 存储桶</h3>
            <div class="value">{{ buckets|length }}</div>
            <div class="sub">已创建的存储桶</div>
        </div>
        <div class="card">
            <h3>📊 对象总数</h3>
            <div class="value green">{{ total_objects }}</div>
            <div class="sub">所有桶中的对象数量</div>
        </div>
        <div class="card">
            <h3>💾 总数据量</h3>
            <div class="value">{{ total_size_formatted }}</div>
            <div class="sub">已存储的雷达数据总量</div>
        </div>
        <div class="card">
            <h3>🟢 集群状态</h3>
            <div class="value green">运行中</div>
            <div class="sub">MinIO集群健康</div>
        </div>
    </div>
    
    <div class="card" style="margin-bottom: 20px;">
        <h3>📋 存储桶详情</h3>
        <table>
            <thead>
                <tr>
                    <th>桶名称</th>
                    <th>对象数</th>
                    <th>数据量</th>
                    <th>标签</th>
                    <th>创建时间</th>
                </tr>
            </thead>
            <tbody>
                {% for bucket in buckets %}
                <tr>
                    <td><strong>{{ bucket.name }}</strong></td>
                    <td>{{ bucket.object_count }}{% if bucket.has_more %}+{% endif %}</td>
                    <td>{{ format_size(bucket.total_size) }}</td>
                    <td>
                        {% for key, value in bucket.tags.items() %}
                        <span class="tag tag-{{ value }}">{{ key }}={{ value }}</span>
                        {% endfor %}
                    </td>
                    <td>{{ bucket.creation_date[:19] if bucket.creation_date else 'N/A' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="card" style="margin-bottom: 20px;">
        <h3>🔄 最近上传活动</h3>
        <p style="color: #6b8db5; font-size: 12px; margin-bottom: 10px;">显示最近的上传记录</p>
        <div id="activity-log">
            {% for upload in recent_uploads %}
            <div style="padding: 4px 0; font-size: 12px; color: #8899b4; border-bottom: 1px solid #1a2744;">
                {{ upload }}
            </div>
            {% endfor %}
        </div>
    </div>
    
    <div class="footer">
        雷达存储系统监控 v1.0 | 数据自动刷新中...
    </div>
    
    <script>
        // 每10秒自动刷新
        setInterval(function() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('update-time').textContent = data.last_update || 'N/A';
                });
        }, 10000);
        
        // 页面自动刷新
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
'''


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes >= 1024**3:
        return f"{size_bytes / 1024**3:.2f} GB"
    elif size_bytes >= 1024**2:
        return f"{size_bytes / 1024**2:.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


@app.route('/')
def dashboard():
    """监控面板首页"""
    total_objects = sum(b.get('object_count', 0) for b in state['buckets'])
    total_size = sum(b.get('total_size', 0) for b in state['buckets'])
    
    return render_template_string(
        DASHBOARD_HTML,
        buckets=state['buckets'],
        total_objects=total_objects,
        total_size_formatted=format_size(total_size),
        recent_uploads=list(state['recent_uploads'])[-20:],
        last_update=state['last_update'] or 'N/A',
        format_size=format_size
    )


@app.route('/api/status')
def api_status():
    """API - 集群状态"""
    total_objects = sum(b.get('object_count', 0) for b in state['buckets'])
    total_size = sum(b.get('total_size', 0) for b in state['buckets'])
    
    return jsonify({
        'buckets': state['buckets'],
        'total_objects': total_objects,
        'total_size': total_size,
        'total_size_formatted': format_size(total_size),
        'last_update': state['last_update'],
        'status': 'healthy'
    })


@app.route('/api/buckets')
def api_buckets():
    """API - 桶列表"""
    return jsonify(state['buckets'])


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()})


if __name__ == '__main__':
    print(f"🚀 监控服务启动于 http://0.0.0.0:8888")
    app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)
