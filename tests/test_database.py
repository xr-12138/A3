import sys
from pathlib import Path
import os

# 修复路径以能导入 src 包
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from src.core.database import Database


def test_database_crud():
    db_path = "/home/hjj/桌面/A3-main/data/user_profiles/profiles.db"
    # 确保一个干净的环境
    try:
        os.remove(db_path)
    except Exception:
        pass

    db = Database()
    db.create_tables()

    # student profile
    features = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    db.add_student_profile("user1", features, extra={"note": "初始"})
    prof = db.get_student_profile("user1")
    assert prof is not None
    assert prof["user_id"] == "user1"
    assert float(prof["feat1"]) == 1.0

    # update
    new_feats = [6,5,4,3,2,1]
    updated = db.update_student_profile("user1", features=new_feats, extra={"note": "更新"})
    assert updated >= 0
    prof2 = db.get_student_profile("user1")
    assert prof2 is not None
    assert float(prof2["feat6"]) == 1.0

    # learning paths
    db.add_learning_step("user1", 1, progress=0.1, details="step1")
    db.add_learning_step("user1", 2, progress=0.0, details="step2")
    path = db.get_learning_path("user1")
    assert len(path) == 2

    db.update_learning_step("user1", 1, progress=0.5)
    path2 = db.get_learning_path("user1")
    assert any(p["step"] == 1 and abs(p["progress"] - 0.5) < 1e-6 for p in path2)

    db.delete_learning_step("user1", 2)
    path3 = db.get_learning_path("user1")
    assert len(path3) == 1

    # resources
    db.add_resource("user1", "res1", "text", "内容1", metadata={"len": 3})
    res = db.get_resource("res1")
    assert res is not None
    assert res["resource_id"] == "res1"

    db.update_resource("res1", content="新内容")
    res2 = db.get_resource("res1")
    assert res2["content"] == "新内容"

    listed = db.list_resources("user1")
    assert isinstance(listed, list) and len(listed) >= 1

    db.delete_resource("res1")
    assert db.get_resource("res1") is None

    # cleanup
    db.delete_student_profile("user1")
    assert db.get_student_profile("user1") is None
