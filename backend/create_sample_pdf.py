from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

# 确保uploads目录存在
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

# 创建PDF文件
pdf_path = os.path.join(uploads_dir, '马清雄.pdf')
c = canvas.Canvas(pdf_path, pagesize=letter)

# 添加内容
c.setFont("Helvetica", 16)
c.drawString(100, 750, "简历 - 马清雄")

c.setFont("Helvetica", 12)
c.drawString(100, 700, "个人信息:")
c.drawString(120, 680, "姓名: 马清雄")
c.drawString(120, 660, "职位: Python开发工程师")
c.drawString(120, 640, "经验: 5年")

c.drawString(100, 600, "技能:")
c.drawString(120, 580, "- Python编程")
c.drawString(120, 560, "- Web开发")
c.drawString(120, 540, "- 数据库设计")
c.drawString(120, 520, "- 系统架构")

c.drawString(100, 480, "工作经历:")
c.drawString(120, 460, "2020-至今: 高级Python开发工程师")
c.drawString(120, 440, "2018-2020: Python开发工程师")
c.drawString(120, 420, "2016-2018: 初级开发工程师")

c.drawString(100, 380, "教育背景:")
c.drawString(120, 360, "2012-2016: 计算机科学与技术学士")

c.save()

print(f"PDF文件已创建: {pdf_path}")