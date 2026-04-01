"""
替代推荐智能体示例

展示如何使用替代推荐智能体处理用户的查询
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.substitute_agent import substitute_agent


def main():
    """
    主函数，展示如何使用替代推荐智能体
    """
    print("欢迎使用替代推荐智能助手！")
    print("你可以问我关于食谱搜索、食谱结构、食材邻域或替代推荐的问题。")
    print("输入 'exit' 退出程序。")
    print("=" * 50)
    
    while True:
        # 获取用户输入
        query = input("请输入你的问题: ")
        
        # 检查是否退出
        if query.lower() == "exit":
            print("再见！")
            break
        
        # 处理查询
        result = substitute_agent.process_query(query)
        
        # 输出结果
        print(f"\n{result['message']}")
        print("=" * 50)


if __name__ == "__main__":
    main()
