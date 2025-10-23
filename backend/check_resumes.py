from app import app, db, Resume

# 在应用上下文中运行
with app.app_context():
    # 检查Resume表数据
    resumes = Resume.query.all()
    print(f'共有 {len(resumes)} 条简历记录')

    for i, resume in enumerate(resumes):
        print(f'\n简历 {i+1}:')
        print(f'  ID: {resume.id}')
        print(f'  文件名: {resume.filename}')
        print(f'  文件内容长度: {len(resume.content) if resume.content else 0}')
        print(f'  创建时间: {resume.created_at}')