import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.api.ai_client import get_ai_client
from src.agents.resource_agent import ResourceAgent


def main():
    ai = get_ai_client()
    ra = ResourceAgent(ai)
    topic = "机器学习"
    print("=== 调用 generate_mindmap ===")
    try:
        mind = ai.generate_mindmap(topic)
        print("raw mindmap:\n", mind)
    except Exception as e:
        print("调用 generate_mindmap 异常:", e)

    print("=== 调用 generate_questions ===")
    try:
        qs = ai.generate_questions(topic, 3)
        print("raw questions:\n", qs)
    except Exception as e:
        print("调用 generate_questions 异常:", e)

    print("=== 使用 ResourceAgent.run() 汇总 ===")
    try:
        out = ra.run(topic)
        print("ResourceAgent 输出:\n", out)
    except Exception as e:
        print("ResourceAgent.run 异常:", e)


if __name__ == '__main__':
    main()
