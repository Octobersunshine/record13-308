import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("=" * 60)
print("测试箱线图 Web 服务 API")
print("=" * 60)

print("\n1. 测试首页访问...")
response = requests.get(f"{BASE_URL}/")
print(f"   状态码: {response.status_code}")
print(f"   内容类型: {response.headers.get('Content-Type')}")
assert response.status_code == 200, "首页访问失败"
print("   ✅ 首页访问成功")

print("\n2. 测试文件上传...")
test_file = "output/test_data.csv"
with open(test_file, 'rb') as f:
    files = {'file': ('test_data.csv', f, 'text/csv')}
    response = requests.post(f"{BASE_URL}/api/upload", files=files)

print(f"   状态码: {response.status_code}")
result = response.json()
print(f"   成功: {result.get('success')}")
print(f"   文件名: {result.get('original_filename')}")
print(f"   数据行数: {result.get('total_rows')}")
print(f"   数值列: {result.get('numeric_columns')}")
assert result.get('success'), f"上传失败: {result.get('error')}"
filename = result['filename']
print("   ✅ 文件上传成功")

print("\n3. 测试生成箱线图...")
generate_data = {
    'filename': filename,
    'columns': ['班级A', '班级B', '班级C', '班级D', '班级E'],
    'title': '班级成绩箱线图 - API测试',
    'show_stats': True
}
response = requests.post(
    f"{BASE_URL}/api/generate",
    json=generate_data,
    headers={'Content-Type': 'application/json'}
)
print(f"   状态码: {response.status_code}")
result = response.json()
print(f"   成功: {result.get('success')}")
print(f"   图片URL: {result.get('image_url')}")
print(f"   总异常值: {result.get('total_outliers')}")
assert result.get('success'), f"生成失败: {result.get('error')}"
print("   ✅ 箱线图生成成功")

print("\n4. 测试异常值分析 API...")
analyze_data = {
    'filename': filename,
    'column': '班级D',
    'k': 1.5
}
response = requests.post(
    f"{BASE_URL}/api/outliers",
    json=analyze_data,
    headers={'Content-Type': 'application/json'}
)
print(f"   状态码: {response.status_code}")
result = response.json()
print(f"   成功: {result.get('success')}")
print(f"   列名: {result.get('column')}")
print(f"   Q1: {result.get('q1'):.2f}, Q3: {result.get('q3'):.2f}, IQR: {result.get('iqr'):.2f}")
print(f"   正常范围: [{result.get('lower_bound'):.2f}, {result.get('upper_bound'):.2f}]")
print(f"   异常值数量: {result.get('outlier_count')}")
print(f"   异常值: {result.get('outliers')}")
assert result.get('success'), f"分析失败: {result.get('error')}"
print("   ✅ 异常值分析成功")

print("\n" + "=" * 60)
print("🎉 所有 API 测试通过！")
print("=" * 60)
print(f"\nWeb 服务运行在: {BASE_URL}")
print("可以在浏览器中打开该地址使用图形界面。")
