from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import pandas as pd

import datetime

# 1. 先导入日志模块（在文件顶部，和其他import放在一起）
import logging
# 配置日志，让错误信息能打印到终端
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取任务：
    - 有day参数：返回当日未完成任务
    - 无day参数：返回所有任务（已完成+未完成），供前端筛选已完成任务
    """
    db = get_db()
    day_filter = request.args.get('day')

    if day_filter:
        # 场景1：有day参数（前端获取当日未完成任务）
        tasks = db.execute(
            'SELECT id, time, content, is_completed FROM tasks WHERE is_completed = 0 AND time LIKE ? ORDER BY time',
            (f'%{day_filter}%',)
        ).fetchall()
    else:
        # 场景2：无day参数（前端获取所有任务，用于筛选已完成）
        tasks = db.execute(
            'SELECT id, time, content, is_completed FROM tasks ORDER BY time'  # 去掉 WHERE is_completed = 0
        ).fetchall()
            
    db.close()
    return jsonify([dict(task) for task in tasks])

@app.route('/api/tasks/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    db = get_db()
    task = db.execute('SELECT id FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not task:
        db.close()
        return jsonify({'error': '任务不存在'}), 404

    # 标记任务为完成
    db.execute('UPDATE tasks SET is_completed = 1 WHERE id = ?', (task_id,))
    db.commit()

    # 优化：返回当日已完成任务列表，前端可直接使用
    today = datetime.date.today()
    weekday_map = {0: '星期一', 1: '星期二', 2: '星期三', 3: '星期四', 4: '星期五', 5: '星期六', 6: '星期日'}
    today_weekday = weekday_map[today.weekday()]
    
    completed_tasks = db.execute(
        'SELECT id, time, content, is_completed FROM tasks WHERE is_completed = 1 AND time LIKE ? ORDER BY time',
        (f'%{today_weekday}%',)
    ).fetchall()
    db.close()

    return jsonify([dict(task) for task in completed_tasks])


@app.route('/api/import_schedule', methods=['POST'])
def import_schedule():
    try:
        if 'schedule_file' not in request.files:
            logger.error("错误：请求中没有找到 'schedule_file' 文件字段")
            return jsonify({'error': '请求中没有文件，请重新选择Excel'}), 400
        
        file = request.files['schedule_file']
        if file.filename == '' or not file.filename.endswith('.xlsx'):
            logger.error(f"错误：文件格式不支持或未选择文件，上传的是 {file.filename}")
            return jsonify({'error': '请选择一个 .xlsx 格式的Excel文件'}), 400

        logger.debug(f"开始读取文件：{file.filename}")
        # 关键1：header=None（无表头）、skiprows=6（跳过前6行无效信息）
        df = pd.read_excel(file, sheet_name='Sheet1', header=None, skiprows=6, usecols='A:I')
        df.columns = ['时间段', '节次', '周一', '周二', '周三', '周四', '周五', '周六', '周日']  # 手动命名列，方便处理
        logger.debug(f"Excel读取成功，数据形状：{df.shape}")

        # 关键2：处理合并单元格的时间段（向下填充）
        # 比如“上午”只在第一行有值，下面行填充为“上午”，直到“下午”出现
        df['时间段'] = df['时间段'].fillna(method='ffill')  # ffill = forward fill（向前填充）
        logger.debug(f"时间段填充后前10行：\n{df[['时间段', '节次', '周三']].head(10).to_string()}")

        db = get_db()
        cursor = db.cursor()
        
        # 关键3：修正星期几与列的对应关系（确保周三能被读取）
        weekday_col_map = {
            '星期一': '周一',
            '星期二': '周二',
            '星期三': '周三',  # 对应Excel的“周三”列
            '星期四': '周四',
            '星期五': '周五',
            '星期六': '周六',
            '星期日': '周日'
        }

        inserted_count = 0

        # 遍历每一行数据（只处理有节次的行）
        for index, row in df.iterrows():
            时间段 = str(row['时间段']) if pd.notna(row['时间段']) else ""
            节次 = row['节次']
            
            # 跳过无节次的行（比如空行、备注行）
            if pd.isna(节次) or 时间段 == "nan":
                continue
            
            # 格式化节次（比如 3.0 → 3）
            节次_str = str(int(节次)) if isinstance(节次, (int, float)) else str(节次)
            time_desc = f"{时间段}{节次_str}节"  # 比如“上午3节”

            # 遍历星期一到星期日，读取对应列的课程
            for 星期几, 列名 in weekday_col_map.items():
                课程内容 = row[列名]
                if pd.isna(课程内容):
                    continue  # 无课程则跳过
                
                # 清洗课程内容（去除换行、多余空格）
                课程_str = str(课程内容).strip().replace('\n', ' ')
                # 只保留核心课程名（过滤掉“(3-4节)6-8周”这类备注，可选）
                if '(' in 课程_str:
                    课程核心 = 课程_str.split('(')[0].strip()
                else:
                    课程核心 = 课程_str
                
                # 组合任务数据（确保包含星期几，方便过滤）
                task_time = f"{星期几} {time_desc}"  # 比如“星期三 上午3节”
                task_content = f"{星期几} {time_desc} {课程核心}"  # 比如“星期三 上午3节 信息工程专业外语”

                # 插入数据库（避免重复导入）
                try:
                    # 先查询是否已有相同任务，避免重复
                    existing = cursor.execute(
                        'SELECT id FROM tasks WHERE time = ? AND content = ?',
                        (task_time, task_content)
                    ).fetchone()
                    if existing:
                        logger.debug(f"重复任务，已跳过：{task_content}")
                        continue

                    cursor.execute(
                        'INSERT INTO tasks (time, content) VALUES (?, ?)',
                        (task_time, task_content)
                    )
                    inserted_count += 1
                    logger.debug(f"插入成功：{task_content}")
                except Exception as e:
                    logger.warning(f"插入失败：{task_content}，错误：{str(e)}")
                    continue

        db.commit()
        db.close()
        
        logger.info(f"课表导入成功，共插入 {inserted_count} 条记录（含星期三课程）")
        return jsonify({'message': f'课表导入成功，共添加 {inserted_count} 条课程（含星期三）'})

    except Exception as e:
        logger.error("课表导入失败，详细错误：", exc_info=True)
        return jsonify({'error': f'导入失败：{str(e)}'}), 500


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    删除指定ID的任务
    - 先检查任务是否存在，不存在返回404
    - 存在则执行删除操作，返回成功信息
    """
    db = get_db()
    
    # 1. 检查任务是否存在（避免删除不存在的任务）
    existing_task = db.execute(
        'SELECT id FROM tasks WHERE id = ?',
        (task_id,)
    ).fetchone()
    
    if not existing_task:
        db.close()
        logger.warning(f"删除失败：任务ID {task_id} 不存在")
        return jsonify({'error': f'删除失败：任务不存在（ID：{task_id}）'}), 404  # 404=资源不存在
    
    # 2. 执行删除操作
    try:
        db.execute(
            'DELETE FROM tasks WHERE id = ?',
            (task_id,)
        )
        db.commit()
        logger.debug(f"删除成功：任务ID {task_id}")
        return jsonify({'message': f'任务已成功删除（ID：{task_id}）'}), 200  # 200=操作成功
    
    except Exception as e:
        db.rollback()  # 出错时回滚事务，避免数据库状态异常
        logger.error(f"删除任务ID {task_id} 失败：", exc_info=True)
        return jsonify({'error': f'删除失败：{str(e)}'}), 500  # 500=服务器错误
    
    finally:
        db.close()  # 无论成功/失败，都关闭数据库连接


# 运行服务器
if __name__ == '__main__':
    # 启动在 5000 端口，debug=True 表示代码修改后自动重启服务器
    app.run(debug=True)