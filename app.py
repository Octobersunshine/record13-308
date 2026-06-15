import os
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for

from boxplot_generator import (
    generate_boxplot,
    parse_csv,
    parse_excel,
    detect_outliers_iqr
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    if not file or not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式，请上传 CSV、Excel 或 TXT 文件'}), 400

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{timestamp}_{unique_id}.{file_ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if file_ext in ('csv', 'txt'):
            df, numeric_cols = parse_csv(filepath)
        else:
            df, numeric_cols = parse_excel(filepath)

        if not numeric_cols:
            os.remove(filepath)
            return jsonify({'error': '文件中未找到数值列'}), 400

        preview_data = df[numeric_cols].head(10).fillna('').to_dict('records')

        return jsonify({
            'success': True,
            'filename': filename,
            'original_filename': file.filename,
            'numeric_columns': numeric_cols,
            'total_rows': len(df),
            'preview': preview_data
        })

    except Exception as e:
        return jsonify({'error': f'文件解析失败: {str(e)}'}), 500


@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        filename = data.get('filename')
        selected_columns = data.get('columns', [])
        title = data.get('title', 'Boxplot with Outliers (1.5×IQR)')
        show_stats = data.get('show_stats', True)

        if not filename:
            return jsonify({'error': '缺少文件名参数'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        file_ext = filename.rsplit('.', 1)[1].lower()

        if file_ext in ('csv', 'txt'):
            df, numeric_cols = parse_csv(filepath)
        else:
            df, numeric_cols = parse_excel(filepath)

        if not selected_columns:
            selected_columns = numeric_cols

        invalid_cols = [col for col in selected_columns if col not in numeric_cols]
        if invalid_cols:
            return jsonify({'error': f'无效的列名: {", ".join(invalid_cols)}'}), 400

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        output_filename = f"boxplot_{timestamp}_{unique_id}.png"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        result = generate_boxplot(
            data=df,
            output_path=output_path,
            column_names=selected_columns,
            title=title,
            show_stats=show_stats
        )

        image_url = url_for('get_output', filename=output_filename, _external=True)

        stats_filename = f"stats_{timestamp}_{unique_id}.json"
        stats_path = os.path.join(app.config['OUTPUT_FOLDER'], stats_filename)
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(result['stats'], f, ensure_ascii=False, indent=2)

        return jsonify({
            'success': True,
            'image_url': image_url,
            'image_filename': output_filename,
            'stats_filename': stats_filename,
            'stats': result['stats'],
            'total_outliers': result['total_outliers']
        })

    except Exception as e:
        return jsonify({'error': f'生成箱线图失败: {str(e)}'}), 500


@app.route('/api/outliers', methods=['POST'])
def analyze_outliers():
    try:
        data = request.get_json()
        filename = data.get('filename')
        column = data.get('column')
        k = float(data.get('k', 1.5))

        if not filename or not column:
            return jsonify({'error': '缺少必要参数'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        file_ext = filename.rsplit('.', 1)[1].lower()

        if file_ext in ('csv', 'txt'):
            df, _ = parse_csv(filepath)
        else:
            df, _ = parse_excel(filepath)

        if column not in df.columns:
            return jsonify({'error': f'列 {column} 不存在'}), 400

        col_data = df[column].values
        outliers, outlier_indices, q1, q3, iqr, lower_bound, upper_bound = detect_outliers_iqr(col_data, k)
        outlier_details = [
            {'index': int(idx), 'value': float(val)}
            for idx, val in zip(outlier_indices, outliers)
        ]

        return jsonify({
            'success': True,
            'column': column,
            'q1': float(q1),
            'q3': float(q3),
            'iqr': float(iqr),
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
            'outliers': outliers.tolist(),
            'outlier_indices': outlier_indices.tolist(),
            'outlier_details': outlier_details,
            'outlier_count': len(outliers),
            'k': k
        })

    except Exception as e:
        return jsonify({'error': f'分析异常值失败: {str(e)}'}), 500


@app.route('/output/<filename>')
def get_output(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


@app.route('/api/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': '文件过大，最大支持 50MB'}), 413


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
