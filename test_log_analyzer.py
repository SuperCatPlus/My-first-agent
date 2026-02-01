#!/usr/bin/env python3
# 测试日志分析功能

from tools.implementations.http_tools import HttpTools


def test_log_analyzer():
    """测试日志分析功能"""
    print("开始测试日志分析功能...")
    
    # 调用接口获取默认50行日志
    print("\n1. 测试默认参数调用接口...")
    response = HttpTools.get_log_last_lines()
    
    if "error" in response:
        print(f"❌ 接口调用失败: {response['error']}")
    else:
        print(f"✅ 接口调用成功，状态码: {response['status_code']}")
        print(f"响应内容长度: {len(response.get('text', ''))} 字符")
        
        # 分析日志
        print("\n2. 分析日志数据...")
        analysis_result = HttpTools.analyze_log_for_intrusion(response)
        
        if analysis_result["has_intrusion"]:
            print(f"⚠️  检测到 {analysis_result['total_intrusions']} 个渗透痕迹:")
            for intrusion in analysis_result["intrusions"]:
                print(f"  - {intrusion['type']}: {intrusion['pattern']}")
        else:
            print("✅ 未检测到渗透痕迹")
        
        # 打印日志样本
        print("\n3. 日志样本:")
        print(analysis_result["log_sample"])
    
    # 测试自定义行数参数
    print("\n4. 测试自定义行数参数(100行)...")
    response_custom = HttpTools.get_log_last_lines(lines_count=100)
    
    if "error" in response_custom:
        print(f"❌ 接口调用失败: {response_custom['error']}")
    else:
        print(f"✅ 接口调用成功，状态码: {response_custom['status_code']}")
        print(f"响应内容长度: {len(response_custom.get('text', ''))} 字符")


if __name__ == "__main__":
    test_log_analyzer()
