from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import time
import threading
from queue import Queue
from dotenv import load_dotenv
from services.deepseek_service import DeepSeekService
from services.pdf_parser import PDFParser

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)

# 数据库配置
import os
database_dir = os.path.join(os.path.dirname(__file__), '..', 'database')
os.makedirs(database_dir, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(database_dir, "resume_match.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 全局变量存储匹配进度
match_progress = {}
progress_lock = threading.Lock()

# 数据库模型
class JobDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parsed_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'content': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'parsed_content': self.parsed_content,
            'created_at': self.created_at.isoformat()
        }

class MatchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_description_id = db.Column(db.Integer, db.ForeignKey('job_description.id'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resume.id'), nullable=False)
    match_score = db.Column(db.Float, nullable=False)
    analysis_result = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    job_description = db.relationship('JobDescription', backref='match_results')
    resume = db.relationship('Resume', backref='match_results')

# 创建数据库表
with app.app_context():
    db.create_all()

# API路由
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs = JobDescription.query.order_by(JobDescription.created_at.desc()).all()
    return jsonify([job.to_dict() for job in jobs])

@app.route('/api/jobs', methods=['POST'])
def create_job():
    data = request.get_json()
    job = JobDescription(
        title=data.get('title', ''),
        description=data.get('description', '')
    )
    db.session.add(job)
    db.session.commit()
    return jsonify(job.to_dict()), 201

@app.route('/api/jobs/<int:id>', methods=['DELETE'])
def delete_job(id):
    job = JobDescription.query.get_or_404(id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({'message': '删除成功'}), 200

@app.route('/api/resumes', methods=['GET'])
def get_resumes():
    resumes = Resume.query.order_by(Resume.created_at.desc()).all()
    return jsonify([resume.to_dict() for resume in resumes])

@app.route('/api/resumes', methods=['POST'])
def upload_resume():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    # 获取文件列表（支持单个和多个文件）
    files = request.files.getlist('file')
    
    # 检查是否有有效的文件
    valid_files = [file for file in files if file.filename != '']
    if not valid_files:
        return jsonify({'error': 'No valid file selected'}), 400
    
    results = []
    
    for file in valid_files:
        try:
            # 解析PDF文件
            pdf_content = PDFParser.parse_pdf(file)
            
            resume = Resume(
                filename=file.filename,
                content=pdf_content,
                parsed_content=pdf_content  # 这里可以添加更复杂的解析逻辑
            )
            db.session.add(resume)
            results.append({
                'success': True,
                'filename': file.filename,
                'data': resume.to_dict()
            })
        except Exception as e:
            results.append({
                'success': False,
                'filename': file.filename,
                'error': f'Error processing file: {str(e)}'
            })
    
    # 一次性提交所有数据库更改
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    # 返回批量上传结果
    return jsonify({
        'message': f'上传完成，成功 {len([r for r in results if r["success"]])}/{len(valid_files)} 个文件',
        'results': results
    }), 201

@app.route('/api/resumes/<int:id>', methods=['DELETE'])
def delete_resume(id):
    resume = Resume.query.get_or_404(id)
    db.session.delete(resume)
    db.session.commit()
    return jsonify({'message': '删除成功'}), 200

@app.route('/api/match', methods=['POST'])
def match_resume():
    data = request.get_json()
    job_id = data.get('job_id')
    resume_id = data.get('resume_id')
    
    if not job_id or not resume_id:
        return jsonify({'error': 'Job ID and Resume ID are required'}), 400
    
    job = JobDescription.query.get(job_id)
    resume = Resume.query.get(resume_id)
    
    if not job or not resume:
        return jsonify({'error': 'Job or Resume not found'}), 404
    
    try:
        # 调用DeepSeek API进行匹配分析
        deepseek_service = DeepSeekService()
        match_result = deepseek_service.analyze_match(job.description, resume.content)
        
        # 保存匹配结果
        match_record = MatchResult(
            job_description_id=job_id,
            resume_id=resume_id,
            match_score=match_result.get('total_score', 0),
            analysis_result=str(match_result)
        )
        db.session.add(match_record)
        db.session.commit()
        
        return jsonify(match_result), 200
    except Exception as e:
        return jsonify({'error': f'Error during matching: {str(e)}'}), 500

@app.route('/api/match-results', methods=['GET'])
def get_match_results():
    results = MatchResult.query.order_by(MatchResult.created_at.desc()).all()
    
    match_results = []
    for result in results:
        # 解析analysis_result中的数据
        analysis_data = {}
        try:
            # 首先尝试JSON解析
            import json
            analysis_data = json.loads(result.analysis_result)
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试使用ast.literal_eval解析Python字典格式
            try:
                import ast
                analysis_data = ast.literal_eval(result.analysis_result)
            except:
                # 如果两种方法都失败，使用默认结构
                analysis_data = {
                    'dimension_scores': {},
                    'total_score': result.match_score,
                    'overall_assessment': '分析结果解析失败',
                    'improvement_suggestions': []
                }
        
        # 确保analysis_data包含必要的字段
        if 'dimension_scores' not in analysis_data:
            analysis_data['dimension_scores'] = {}
        if 'total_score' not in analysis_data:
            analysis_data['total_score'] = result.match_score
        if 'overall_assessment' not in analysis_data:
            analysis_data['overall_assessment'] = '总体评估'
        if 'improvement_suggestions' not in analysis_data:
            analysis_data['improvement_suggestions'] = []
        
        match_results.append({
            'id': result.id,
            'job_title': result.job_description.title,
            'resume_filename': result.resume.filename,
            'match_score': result.match_score,
            'created_at': result.created_at.isoformat(),
            'analysis_data': analysis_data
        })
    
    return jsonify(match_results)

@app.route('/api/match-results/<int:id>', methods=['DELETE'])
def delete_match_result(id):
    result = MatchResult.query.get_or_404(id)
    db.session.delete(result)
    db.session.commit()
    return jsonify({'message': '删除成功'}), 200

@app.route('/api/match-results', methods=['DELETE'])
def clear_all_match_results():
    try:
        # 删除所有匹配结果
        MatchResult.query.delete()
        db.session.commit()
        return jsonify({'message': '所有匹配结果已清除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'清除失败: {str(e)}'}), 500

def _match_single_resume(job, resume, task_id, index, total):
    """单个简历匹配任务"""
    try:
        # 更新进度
        with progress_lock:
            match_progress[task_id] = {
                'current': index + 1,
                'total': total,
                'status': 'processing',
                'current_filename': resume.filename,
                'results': match_progress.get(task_id, {}).get('results', [])
            }
        
        # 调用DeepSeek API进行匹配分析
        deepseek_service = DeepSeekService()
        match_result = deepseek_service.analyze_match(job.description, resume.content)
        
        # 保存匹配结果
        match_record = MatchResult(
            job_description_id=job.id,
            resume_id=resume.id,
            match_score=match_result.get('total_score', 0),
            analysis_result=str(match_result)
        )
        db.session.add(match_record)
        
        result = {
            'resume_id': resume.id,
            'success': True,
            'data': match_result,
            'resume_filename': resume.filename
        }
        
        # 更新结果
        with progress_lock:
            match_progress[task_id]['results'].append(result)
            match_progress[task_id]['current'] = index + 1
        
        return result
        
    except Exception as e:
        result = {
            'resume_id': resume.id,
            'success': False,
            'error': str(e),
            'resume_filename': resume.filename
        }
        
        # 更新结果
        with progress_lock:
            match_progress[task_id]['results'].append(result)
            match_progress[task_id]['current'] = index + 1
        
        return result

@app.route('/api/batch-match', methods=['POST'])
def batch_match_resumes():
    data = request.get_json()
    job_id = data.get('job_id')
    resume_ids = data.get('resume_ids', [])
    
    if not job_id or not resume_ids:
        return jsonify({'error': 'Job ID and Resume IDs are required'}), 400
    
    job = JobDescription.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # 生成任务ID
    task_id = f"match_{int(time.time())}_{job_id}"
    
    # 初始化进度
    with progress_lock:
        match_progress[task_id] = {
            'current': 0,
            'total': len(resume_ids),
            'status': 'starting',
            'current_filename': '',
            'results': []
        }
    
    def run_batch_match():
        """异步执行批量匹配"""
        with app.app_context():
            try:
                # 更新状态为处理中
                with progress_lock:
                    match_progress[task_id]['status'] = 'processing'
                
                # 逐个处理简历
                for i, resume_id in enumerate(resume_ids):
                    resume = Resume.query.get(resume_id)
                    if not resume:
                        # 简历不存在
                        result = {
                            'resume_id': resume_id,
                            'success': False,
                            'error': 'Resume not found',
                            'resume_filename': f'Unknown (ID: {resume_id})'
                        }
                        with progress_lock:
                            match_progress[task_id]['results'].append(result)
                            match_progress[task_id]['current'] = i + 1
                        continue
                    
                    # 执行单个匹配
                    _match_single_resume(job, resume, task_id, i, len(resume_ids))
                
                # 提交所有数据库更改
                try:
                    db.session.commit()
                    # 更新状态为完成
                    with progress_lock:
                        match_progress[task_id]['status'] = 'completed'
                except Exception as e:
                    db.session.rollback()
                    with progress_lock:
                        match_progress[task_id]['status'] = 'error'
                        match_progress[task_id]['error'] = f'Database error: {str(e)}'
            
            except Exception as e:
                with progress_lock:
                    match_progress[task_id]['status'] = 'error'
                    match_progress[task_id]['error'] = f'Batch match error: {str(e)}'
    
    # 启动异步任务
    thread = threading.Thread(target=run_batch_match)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'message': '批量匹配任务已开始，请使用任务ID查询进度',
        'total': len(resume_ids)
    }), 202

@app.route('/api/match-progress/<task_id>', methods=['GET'])
def get_match_progress(task_id):
    """获取匹配进度"""
    with progress_lock:
        progress = match_progress.get(task_id)
    
    if not progress:
        return jsonify({'error': '任务不存在或已过期'}), 404
    
    return jsonify(progress), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)