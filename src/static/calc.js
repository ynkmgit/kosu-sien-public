/**
 * クライアントサイド計算ロジック
 *
 * 実績入力・月次アサイン・案件見積の計算列をリアルタイム更新する。
 */

/**
 * 安全に数値をパースする
 * @param {string} value - パース対象の文字列
 * @returns {number} パース結果（失敗時は0）
 */
function safeParseFloat(value) {
    const parsed = parseFloat(value);
    return isNaN(parsed) ? 0 : parsed;
}

/**
 * 実績入力（週表示）の計算列を更新
 */
function updateWorkLogsCalculation() {
    const table = document.querySelector('.log-table, .week-table');
    if (!table) return;

    // 日計の初期化
    const dateColumns = {};
    table.querySelectorAll('.date-header').forEach((header, index) => {
        dateColumns[index] = 0;
    });

    let grandTotal = 0;

    // 各作業行を処理
    table.querySelectorAll('.log-row').forEach(row => {
        let rowTotal = 0;

        // 各セルの値を集計
        row.querySelectorAll('.log-input').forEach((input, index) => {
            const value = safeParseFloat(input.value);
            rowTotal += value;
            dateColumns[index] = (dateColumns[index] || 0) + value;
        });

        // 行合計を更新
        const rowTotalCell = row.querySelector('.row-total');
        if (rowTotalCell) {
            rowTotalCell.textContent = rowTotal > 0 ? `${rowTotal.toFixed(2)}h` : '-';
        }

        grandTotal += rowTotal;
    });

    // 列合計（日計）を更新
    const totalRow = table.querySelector('.total-row');
    if (totalRow) {
        totalRow.querySelectorAll('.col-total').forEach((cell, index) => {
            const value = dateColumns[index] || 0;
            cell.textContent = value > 0 ? value.toFixed(2) : '-';
        });

        // 総合計を更新
        const grandTotalCell = totalRow.querySelector('.grand-total');
        if (grandTotalCell) {
            grandTotalCell.textContent = `${grandTotal.toFixed(2)}h`;
        }
    }
}

/**
 * 案件見積の合計を更新
 */
function updateEstimateCalculation() {
    const table = document.getElementById('estimate-table');
    if (!table) return;

    let total = 0;

    // 各見積項目の工数を集計
    table.querySelectorAll('tbody tr:not(.total-row)').forEach(row => {
        const hoursInput = row.querySelector('input[name="hours"]');
        if (hoursInput) {
            total += safeParseFloat(hoursInput.value);
        } else {
            // 編集モードでない場合、セルのテキストから取得
            const hoursCell = row.querySelector('.hours-cell');
            if (hoursCell) {
                total += safeParseFloat(hoursCell.textContent);
            }
        }
    });

    // 合計行を更新
    const totalRow = table.querySelector('.total-row');
    if (totalRow) {
        const totalCell = totalRow.querySelectorAll('td')[1];
        if (totalCell) {
            totalCell.textContent = total.toFixed(2);
        }
    }
}

/**
 * 月次アサイン（簡易モード）の計算列を更新
 */
function updateMonthlyAssignmentCalculation() {
    const table = document.querySelector('.assign-table');
    if (!table) return;

    // 詳細モードの場合は計算しない（サーバー側データが必要）
    if (table.querySelector('.assign-cell[style*="vertical-align"]')) {
        return;
    }

    // プロジェクト計の初期化
    const projectTotals = {};
    let grandTotal = 0;

    // 各ユーザー行を処理
    table.querySelectorAll('.user-row').forEach(row => {
        let userTotal = 0;

        // 各プロジェクトセルの値を集計
        row.querySelectorAll('.assign-input').forEach((input, index) => {
            const value = safeParseFloat(input.value);
            userTotal += value;
            projectTotals[index] = (projectTotals[index] || 0) + value;
        });

        // 行合計（ユーザー合計）を更新
        const rowTotalCell = row.querySelector('.row-total');
        if (rowTotalCell) {
            const hoursDiv = rowTotalCell.querySelector('.total-hours');
            const mmDiv = rowTotalCell.querySelector('.total-mm');
            if (hoursDiv) {
                hoursDiv.textContent = userTotal > 0 ? `${userTotal.toFixed(1)}h` : '-';
            }
            if (mmDiv) {
                mmDiv.textContent = userTotal > 0 ? `${(userTotal / 160).toFixed(2)}MM` : '';
            }
        }

        grandTotal += userTotal;
    });

    // 列合計（プロジェクト計）を更新
    const totalRow = table.querySelector('.total-row');
    if (totalRow) {
        totalRow.querySelectorAll('.col-total').forEach((cell, index) => {
            const value = projectTotals[index] || 0;
            cell.textContent = value > 0 ? `${value.toFixed(1)}h` : '-';
        });

        // 総合計を更新
        const grandTotalCell = totalRow.querySelector('.grand-total');
        if (grandTotalCell) {
            grandTotalCell.textContent = grandTotal > 0 ? `${grandTotal.toFixed(1)}h` : '-';
        }
    }
}

/**
 * ページ種別を判定して適切な計算関数を実行
 */
function recalculateAll() {
    // 実績入力
    if (document.querySelector('.log-table, .week-table')) {
        updateWorkLogsCalculation();
    }

    // 案件見積
    if (document.getElementById('estimate-table')) {
        updateEstimateCalculation();
    }

    // 月次アサイン
    if (document.querySelector('.assign-table')) {
        updateMonthlyAssignmentCalculation();
    }
}

/**
 * イベントリスナーの設定
 */
function initCalculation() {
    // 入力時にリアルタイム計算
    document.addEventListener('input', (e) => {
        if (e.target.matches('.log-input, .assign-input, input[name="hours"]')) {
            recalculateAll();
        }
    });

    // HTMX リクエスト完了後にも計算（サーバー側の値と同期）
    document.addEventListener('htmx:afterRequest', (e) => {
        if (e.detail.successful) {
            recalculateAll();
        }
    });

    // 初期表示時に計算
    document.addEventListener('DOMContentLoaded', recalculateAll);

    // HTMXの動的コンテンツ読み込み後に計算
    document.addEventListener('htmx:afterSettle', recalculateAll);
}

// 初期化実行
initCalculation();
