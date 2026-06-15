import numpy as np
import pandas as pd
import os

np.random.seed(42)

n_samples = 100

group_a = np.random.normal(50, 10, n_samples)
group_b = np.random.normal(60, 8, n_samples)
group_c = np.random.normal(55, 12, n_samples)
group_d = np.random.normal(70, 6, n_samples)
group_e = np.random.normal(45, 15, n_samples)

group_a = np.append(group_a, [90, 95, 100])
group_b = np.append(group_b, [20, 15])
group_c = np.append(group_c, [120, 110])
group_d = np.append(group_d, [40, 35, 100, 105])
group_e = np.append(group_e, [5, 10])

max_len = max(len(group_a), len(group_b), len(group_c), len(group_d), len(group_e))

def pad_array(arr, length):
    return np.pad(arr, (0, length - len(arr)), constant_values=np.nan)

group_a = pad_array(group_a, max_len)
group_b = pad_array(group_b, max_len)
group_c = pad_array(group_c, max_len)
group_d = pad_array(group_d, max_len)
group_e = pad_array(group_e, max_len)

df = pd.DataFrame({
    '班级A': group_a,
    '班级B': group_b,
    '班级C': group_c,
    '班级D': group_d,
    '班级E': group_e
})

output_path = 'output'
os.makedirs(output_path, exist_ok=True)

csv_path = os.path.join(output_path, 'test_data.csv')
df.to_csv(csv_path, index=False, encoding='utf-8-sig')

print(f"测试数据已生成: {csv_path}")
print(f"数据形状: {df.shape}")
print("\n数据预览:")
print(df.head())
print("\n各列统计信息:")
for col in df.columns:
    data = df[col].dropna()
    q1 = data.quantile(0.25)
    q3 = data.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = data[(data < lower) | (data > upper)]
    print(f"\n{col}:")
    print(f"  数量: {len(data)}, 均值: {data.mean():.2f}, 中位数: {data.median():.2f}")
    print(f"  Q1: {q1:.2f}, Q3: {q3:.2f}, IQR: {iqr:.2f}")
    print(f"  正常范围: [{lower:.2f}, {upper:.2f}]")
    print(f"  异常值数量: {len(outliers)}, 异常值: {outliers.tolist()}")
