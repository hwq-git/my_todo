# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

# 初始化 Flask 应用
app = Flask(__name__)
# 解决跨域问题，允许前端调用后端 API
CORS(app)

# 数据库文件路径
DATABASE = 'tasks.db'

def get_db():
    """连接到 SQLite 数据库，如果数据库文件不存在则创建"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # 让查询结果可以像字典一样访问
    return conn

def init_db():
    """初始化数据库，创建 tasks 表"""
    with get_db() as db:
        db.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            content TEXT NOT NULL,
            is_completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        db.commit()

# 初始化数据库（应用启动时执行一次）
init_db()

# --- API 接口 ---

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取所有任务"""
    db = get_db()
    tasks = db.execute('SELECT id, time, content, is_completed FROM tasks ORDER BY time').fetchall()
    db.close()
    # 将查询结果转换为字典列表
    return jsonify([dict(task) for task in tasks])

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """添加一个新任务"""
    data = request.get_json()
    time = data.get('time')
    content = data.get('content')

    if not time or not content:
        return jsonify({'error': '时间和内容不能为空'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO tasks (time, content) VALUES (?, ?)', (time, content))
    db.commit()
    # 获取刚刚插入的任务的 ID
    task_id = cursor.lastrowid
    db.close()

    return jsonify({'id': task_id, 'time': time, 'content': content, 'is_completed': False}), 201

@app.route('/api/tasks/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    """将一个任务标记为已完成"""
    db = get_db()
    # 检查任务是否存在
    task = db.execute('SELECT id FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not task:
        db.close()
        return jsonify({'error': '任务不存在'}), 404

    db.execute('UPDATE tasks SET is_completed = 1 WHERE id = ?', (task_id,))
    db.commit()
    db.close()
    return jsonify({'message': '任务已标记为完成'})

# 运行服务器
if __name__ == '__main__':
    # 启动在 5000 端口，debug=True 表示代码修改后自动重启服务器
    app.run(debug=True)