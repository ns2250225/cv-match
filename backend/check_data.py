from app import app, db, MatchResult
from sqlalchemy import inspect

# 在应用上下文中运行
with app.app_context():
    # 检查数据库连接和表结构
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print('数据库表:', tables)

    # 检查MatchResult表结构
    if 'match_result' in tables:
        columns = inspector.get_columns('match_result')
        print('\nMatchResult表结构:')
        for col in columns:
            print(f'  {col["name"]}: {col["type"]}')

    # 检查实际数据
    results = MatchResult.query.all()
    print(f'\n共有 {len(results)} 条匹配结果')

    for i, result in enumerate(results[:3]):  # 只显示前3条
        print(f'\n结果 {i+1}:')
        print(f'  ID: {result.id}')
        print(f'  匹配分数: {result.match_score}')
        if result.analysis_result:
            print(f'  分析结果长度: {len(result.analysis_result)}')
            print(f'  分析结果前200字符: {result.analysis_result[:200]}')
            
            # 尝试解析JSON格式
            try:
                import json
                parsed_data = json.loads(result.analysis_result)
                print('  解析成功，数据结构:')
                print(f'    - 总分: {parsed_data.get("total_score", "N/A")}')
                print(f'    - 维度数量: {len(parsed_data.get("dimension_scores", {}))}')
                print(f'    - 改进建议数量: {len(parsed_data.get("improvement_suggestions", []))}')
            except json.JSONDecodeError:
                print('  解析失败，不是有效的JSON格式')
        else:
            print('  分析结果: 无数据')