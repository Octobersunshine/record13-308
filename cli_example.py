import argparse
import sys
import json
from boxplot_generator import generate_boxplot, parse_csv, parse_excel, detect_outliers_iqr


def main():
    parser = argparse.ArgumentParser(description='箱线图生成工具 - 基于 1.5×IQR 的异常值检测')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    generate_parser = subparsers.add_parser('generate', help='生成箱线图')
    generate_parser.add_argument('--input', '-i', required=True, help='输入文件路径 (CSV/Excel)')
    generate_parser.add_argument('--output', '-o', required=True, help='输出图片路径')
    generate_parser.add_argument('--columns', '-c', nargs='*', help='要分析的列名（默认所有数值列）')
    generate_parser.add_argument('--title', '-t', default='Boxplot with Outliers (1.5×IQR)', help='图表标题')
    generate_parser.add_argument('--no-stats', action='store_true', help='不显示统计信息')

    analyze_parser = subparsers.add_parser('analyze', help='分析单列异常值')
    analyze_parser.add_argument('--input', '-i', required=True, help='输入文件路径')
    analyze_parser.add_argument('--column', '-c', required=True, help='要分析的列名')
    analyze_parser.add_argument('--k', type=float, default=1.5, help='异常值系数 (默认 1.5)')

    args = parser.parse_args()

    if args.command == 'generate':
        try:
            file_ext = args.input.rsplit('.', 1)[1].lower()

            if file_ext in ('csv', 'txt'):
                df, numeric_cols = parse_csv(args.input)
            elif file_ext in ('xlsx', 'xls'):
                df, numeric_cols = parse_excel(args.input)
            else:
                print(f"错误: 不支持的文件格式: {file_ext}")
                sys.exit(1)

            columns = args.columns if args.columns else numeric_cols

            invalid_cols = [col for col in columns if col not in numeric_cols]
            if invalid_cols:
                print(f"错误: 无效的列名: {', '.join(invalid_cols)}")
                print(f"可用的数值列: {', '.join(numeric_cols)}")
                sys.exit(1)

            print(f"正在生成箱线图...")
            print(f"输入文件: {args.input}")
            print(f"分析列: {', '.join(columns)}")
            print(f"输出文件: {args.output}")

            result = generate_boxplot(
                data=df,
                output_path=args.output,
                column_names=columns,
                title=args.title,
                show_stats=not args.no_stats
            )

            print("\n✅ 箱线图生成成功！")
            print(f"\n📊 统计摘要:")
            for stats in result['stats']:
                print(f"\n  {stats['column']}:")
                print(f"    数据量: {stats['count']}, 中位数: {stats['median']:.2f}")
                print(f"    Q1: {stats['q1']:.2f}, Q3: {stats['q3']:.2f}, IQR: {stats['iqr']:.2f}")
                print(f"    正常范围: [{stats['lower_bound']:.2f}, {stats['upper_bound']:.2f}]")
                print(f"    异常值: {stats['outlier_count']} 个")
                if stats['outlier_count'] > 0:
                    print(f"    异常值列表: {[round(x, 2) for x in stats['outliers']]}")

            print(f"\n📈 总异常值数量: {result['total_outliers']}")
            print(f"🖼️  图片已保存至: {result['image_path']}")

        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            sys.exit(1)

    elif args.command == 'analyze':
        try:
            file_ext = args.input.rsplit('.', 1)[1].lower()

            if file_ext in ('csv', 'txt'):
                df, numeric_cols = parse_csv(args.input)
            elif file_ext in ('xlsx', 'xls'):
                df, numeric_cols = parse_excel(args.input)
            else:
                print(f"错误: 不支持的文件格式: {file_ext}")
                sys.exit(1)

            if args.column not in numeric_cols:
                print(f"错误: 列 '{args.column}' 不存在或不是数值列")
                print(f"可用的数值列: {', '.join(numeric_cols)}")
                sys.exit(1)

            col_data = df[args.column].dropna().values
            outliers, q1, q3, iqr, lower_bound, upper_bound = detect_outliers_iqr(col_data, args.k)

            print(f"\n📊 列 '{args.column}' 异常值分析 (k={args.k}):")
            print(f"  数据量: {len(col_data)}")
            print(f"  Q1 (25%分位数): {q1:.4f}")
            print(f"  Q3 (75%分位数): {q3:.4f}")
            print(f"  IQR (四分位距): {iqr:.4f}")
            print(f"  下界 (Q1 - {args.k}×IQR): {lower_bound:.4f}")
            print(f"  上界 (Q3 + {args.k}×IQR): {upper_bound:.4f}")
            print(f"  异常值数量: {len(outliers)}")
            if len(outliers) > 0:
                print(f"  异常值列表: {sorted([round(x, 4) for x in outliers])}")
            else:
                print("  ✅ 未检测到异常值")

        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
