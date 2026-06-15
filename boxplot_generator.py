import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import pandas as pd
import os
import platform
from typing import Tuple, List, Dict, Union


def setup_chinese_font():
    """设置中文字体支持"""
    system = platform.system()
    if system == 'Windows':
        font_names = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong']
    elif system == 'Darwin':
        font_names = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'SimHei']
    else:
        font_names = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'SimHei']

    for font_name in font_names:
        try:
            plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            break
        except:
            continue

    plt.rcParams['axes.unicode_minus'] = False


setup_chinese_font()


def detect_outliers_iqr(data: np.ndarray, k: float = 1.5) -> Tuple[np.ndarray, float, float, float, float]:
    """
    使用 IQR 方法检测异常值

    Args:
        data: 输入数据数组
        k: 异常值系数，默认为 1.5

    Returns:
        异常值数组, Q1, Q3, IQR, 下界, 上界
    """
    data = np.asarray(data)
    data = data[~np.isnan(data)]

    if len(data) == 0:
        return np.array([]), 0, 0, 0, 0, 0

    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr

    outliers = data[(data < lower_bound) | (data > upper_bound)]
    return outliers, q1, q3, iqr, lower_bound, upper_bound


def get_outlier_indices(data: np.ndarray, k: float = 1.5) -> np.ndarray:
    """
    获取异常值在原始数据中的索引

    Args:
        data: 输入数据数组
        k: 异常值系数，默认为 1.5

    Returns:
        异常值索引数组
    """
    data = np.asarray(data)
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr

    indices = np.where((data < lower_bound) | (data > upper_bound))[0]
    return indices


def generate_boxplot(
    data: Union[pd.DataFrame, List[List[float]], np.ndarray],
    output_path: str,
    column_names: List[str] = None,
    title: str = "Boxplot with Outliers (1.5×IQR)",
    figsize: Tuple[int, int] = (12, 8),
    show_stats: bool = True
) -> Dict:
    """
    生成箱线图并标记异常值

    Args:
        data: 输入数据，可以是 DataFrame、二维列表或 numpy 数组
        output_path: 输出图片路径
        column_names: 列名列表
        title: 图表标题
        figsize: 图表大小
        show_stats: 是否显示统计信息

    Returns:
        包含统计信息的字典
    """
    if isinstance(data, pd.DataFrame):
        if column_names is None:
            column_names = list(data.columns)
        data_array = [data[col].dropna().values for col in column_names]
    elif isinstance(data, np.ndarray) and data.ndim == 2:
        if column_names is None:
            column_names = [f"Column {i+1}" for i in range(data.shape[1])]
        data_array = [data[:, i][~np.isnan(data[:, i])] for i in range(data.shape[1])]
    else:
        data = list(data)
        if column_names is None:
            column_names = [f"Column {i+1}" for i in range(len(data))]
        data_array = [np.asarray(col)[~np.isnan(np.asarray(col))] for col in data]

    stats_list = []
    outliers_list = []

    for i, col_data in enumerate(data_array):
        outliers, q1, q3, iqr, lower_bound, upper_bound = detect_outliers_iqr(col_data)
        stats = {
            'column': column_names[i],
            'count': len(col_data),
            'min': float(np.min(col_data)) if len(col_data) > 0 else 0,
            'max': float(np.max(col_data)) if len(col_data) > 0 else 0,
            'median': float(np.median(col_data)) if len(col_data) > 0 else 0,
            'q1': float(q1),
            'q3': float(q3),
            'iqr': float(iqr),
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
            'outliers': outliers.tolist(),
            'outlier_count': len(outliers)
        }
        stats_list.append(stats)
        outliers_list.append(outliers)

    fig, ax = plt.subplots(figsize=figsize)

    bp = ax.boxplot(
        data_array,
        patch_artist=True,
        labels=column_names,
        showmeans=True,
        meanline=False,
        meanprops={'marker': 'o', 'markerfacecolor': 'white', 'markeredgecolor': 'black', 'markersize': 8},
        medianprops={'color': 'red', 'linewidth': 2},
        whiskerprops={'color': 'blue', 'linewidth': 1.5},
        capprops={'color': 'blue', 'linewidth': 1.5},
        flierprops={'marker': 'x', 'markerfacecolor': 'red', 'markeredgecolor': 'red', 'markersize': 10, 'markeredgewidth': 2}
    )

    colors = ['#E6F2FF', '#FFE6E6', '#E6FFE6', '#FFF5E6', '#F0E6FF']
    for i, patch in enumerate(bp['boxes']):
        color = colors[i % len(colors)]
        patch.set_facecolor(color)
        patch.set_edgecolor('darkblue')
        patch.set_linewidth(1.5)

    all_data = np.concatenate([d for d in data_array if len(d) > 0])
    data_range = np.max(all_data) - np.min(all_data) if len(all_data) > 0 else 1

    for i, outliers in enumerate(outliers_list):
        outlier_count = len(outliers)
        if outlier_count > 0:
            col_data = data_array[i]
            
            y_max = np.max(col_data)
            
            ax.text(
                i + 1,
                y_max + data_range * 0.03,
                f'! {outlier_count}个异常值',
                ha='center',
                va='bottom',
                fontsize=10,
                color='#dc2626',
                fontweight='bold',
                bbox=dict(
                    boxstyle='round,pad=0.4',
                    facecolor='#fef2f2',
                    edgecolor='#fca5a5',
                    alpha=0.9
                )
            )

    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Value', fontsize=12, fontweight='bold')
    ax.set_xlabel('Groups', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')

    if show_stats:
        legend_text = []
        for stats in stats_list:
            text = (f"{stats['column']}: n={stats['count']}, "
                    f"Q1={stats['q1']:.2f}, Q3={stats['q3']:.2f}, "
                    f"IQR={stats['iqr']:.2f}\n"
                    f"  范围: [{stats['lower_bound']:.2f}, {stats['upper_bound']:.2f}], "
                    f"异常值: {stats['outlier_count']} 个")
            legend_text.append(text)

        stats_text = '\n'.join(legend_text)
        fig.text(0.02, -0.15, stats_text, fontsize=9, transform=ax.transAxes,
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8),
                 verticalalignment='top')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25)

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    result = {
        'image_path': output_path,
        'stats': stats_list,
        'total_outliers': sum(s['outlier_count'] for s in stats_list)
    }

    return result


def parse_csv(file_path: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    解析 CSV 文件

    Args:
        file_path: CSV 文件路径

    Returns:
        DataFrame 和数值列名列表
    """
    df = pd.read_csv(file_path)
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    return df, numeric_columns


def parse_excel(file_path: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    解析 Excel 文件

    Args:
        file_path: Excel 文件路径

    Returns:
        DataFrame 和数值列名列表
    """
    df = pd.read_excel(file_path)
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    return df, numeric_columns
