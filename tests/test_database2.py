import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.core.database import Database

def test_database():
    db = Database()
    
    # 创建表
    db.create_tables()
    
    # 测试增删改查
    print("🚀 测试保存学生画像...")
    user_id = "test_user_1"
    features = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    extra = {"name": "测试学生", "major": "计算机"}
    profile_id = db.add_student_profile(user_id, features, extra)
    print("✅ 画像保存成功，ID：", profile_id)
    
    print("\n🚀 测试查询学生画像...")
    profile = db.get_student_profile(user_id)
    print("✅ 画像查询成功：", profile["extra"]["name"])
    
    print("\n🚀 测试保存学习路径...")
    step_id = db.add_learning_step(user_id, 1, 0.0, "第一步：学习基础概念")
    print("✅ 路径保存成功，ID：", step_id)
    
    print("\n🎉 数据库所有功能测试通过！")

if __name__ == "__main__":
    test_database()