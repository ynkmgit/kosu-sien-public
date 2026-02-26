/**
 * クライアントサイド計算ロジック
 *
 * 実績入力・月次アサイン・案件見積・アサイン管理の計算列をリアルタイム更新する。
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
 * アサイン管理グリッドの自動計算列を更新
 *
 * 対象列: 理論残, 完了%(加重平均), 実際残, 山積計, 予定差, 未割当
 * 月別集計（案件行・PJ行）もリアルタイム更新する
 */
function updateAssignmentGridCalculation() {
    const table = document.querySelector('.log-table');
    if (!table || !table.querySelector('.task-row')) return;

    const monthCount = table.querySelectorAll('thead .date-header').length;
    if (monthCount === 0) return;

    const fmtH = (v) => v > 0 ? `${v.toFixed(2)}h` : '-';
    const fmtMonth = (v) => v > 0 ? v.toFixed(2) : '-';

    // 案件・PJ集計用
    const issueAcc = {};
    const projAcc = {};

    table.querySelectorAll('.task-row').forEach(taskRow => {
        const tid = taskRow.dataset.taskId;
        const iid = taskRow.dataset.issueId;
        const pid = taskRow.dataset.projectId;

        if (!issueAcc[iid]) issueAcc[iid] = { pid, est: 0, act: 0, planTotal: 0, ar: null, ua: null, months: new Array(monthCount).fill(0) };
        if (!projAcc[pid]) projAcc[pid] = { est: 0, act: 0, planTotal: 0, ar: null, ua: null, months: new Array(monthCount).fill(0) };

        // 見積
        const estInput = taskRow.querySelector('.estimate-input');
        const est = estInput ? safeParseFloat(estInput.value) : 0;

        // 実績（表示のみ）
        const actCell = taskRow.querySelector('.actual-cell');
        const act = actCell ? safeParseFloat(actCell.textContent) : 0;

        // 理論残 = 見積 − 実績
        const remaining = est - act;
        const remCell = taskRow.querySelector('.remaining-cell');
        if (remCell) {
            if (est === 0 && act === 0) {
                remCell.textContent = '-';
                remCell.className = 'remaining-cell';
            } else {
                remCell.textContent = `${remaining.toFixed(2)}h`;
                remCell.className = remaining < 0 ? 'remaining-cell remaining-negative' : 'remaining-cell';
            }
        }

        // 山積計・月別集計
        const subRows = [...table.querySelectorAll(`.assignee-sub-row[data-task-id="${tid}"]`)];
        let taskPlanTotal = 0;
        const taskMonths = new Array(monthCount).fill(0);
        const progressData = [];

        if (subRows.length > 0) {
            // マルチ担当: サブ行から集計
            subRows.forEach(subRow => {
                let subVisiblePlan = 0;
                subRow.querySelectorAll('.plan-input').forEach((input, idx) => {
                    const v = safeParseFloat(input.value);
                    subVisiblePlan += v;
                    if (idx < monthCount) taskMonths[idx] += v;
                });
                // 非表示月の計画値を加算
                const subPTCell = subRow.querySelector('.plan-total-summary');
                const hiddenPlan = subPTCell ? safeParseFloat(subPTCell.dataset.hiddenPlan) : 0;
                const subPlanTotal = subVisiblePlan + hiddenPlan;
                taskPlanTotal += subPlanTotal;

                // サブ行の山積計を更新
                if (subPTCell) subPTCell.textContent = fmtH(subPlanTotal);

                // 完了%データ収集（加重平均用）
                const progInput = subRow.querySelector('.progress-input');
                if (progInput && progInput.value !== '') {
                    progressData.push({ progress: safeParseFloat(progInput.value), planTotal: subPlanTotal });
                }
            });

            // タスク行の月別集計セルを更新
            const allTds = [...taskRow.querySelectorAll('td')];
            allTds.slice(-monthCount).forEach((td, idx) => {
                td.textContent = fmtMonth(taskMonths[idx]);
            });
        } else {
            // 単一担当 or 未割当: タスク行のplan-inputから集計
            let visiblePlan = 0;
            taskRow.querySelectorAll('.plan-input').forEach((input, idx) => {
                const v = safeParseFloat(input.value);
                visiblePlan += v;
                if (idx < monthCount) taskMonths[idx] = v;
            });
            // 非表示月の計画値を加算
            const ptCellForHidden = taskRow.querySelector('.plan-total-summary');
            const hiddenPlan = ptCellForHidden ? safeParseFloat(ptCellForHidden.dataset.hiddenPlan) : 0;
            taskPlanTotal = visiblePlan + hiddenPlan;
        }

        // タスク行の山積計を更新
        const ptCell = taskRow.querySelector('.plan-total-summary');
        if (ptCell) ptCell.textContent = fmtH(taskPlanTotal);

        // 完了%（加重平均 or 単一値）
        let progress = null;
        if (subRows.length >= 2) {
            if (progressData.length > 0) {
                const totalWeight = progressData.reduce((s, d) => s + d.planTotal, 0);
                if (totalWeight > 0) {
                    progress = Math.round(progressData.reduce((s, d) => s + d.progress * d.planTotal, 0) / totalWeight);
                } else {
                    progress = Math.round(progressData.reduce((s, d) => s + d.progress, 0) / progressData.length);
                }
            }
            const progCell = taskRow.querySelector('.progress-cell');
            if (progCell && !progCell.querySelector('.progress-input')) {
                progCell.textContent = progress !== null ? `${progress}%` : '';
                progCell.className = progress !== null ? 'progress-cell weighted-progress' : 'progress-cell';
            }
        } else {
            const progInput = taskRow.querySelector('.progress-input');
            if (progInput && progInput.value !== '') {
                progress = safeParseFloat(progInput.value);
            }
        }

        // 実際残 = 見積 × (1 − 完了%/100)
        let ar = null;
        if (est > 0 && progress !== null) {
            ar = est * (1 - progress / 100);
        }
        const arCell = taskRow.querySelector('.actual-remaining-cell');
        if (arCell) arCell.textContent = ar !== null ? `${ar.toFixed(2)}h` : '-';

        // 予定差 = 山積計 − 理論残
        const sd = taskPlanTotal - remaining;
        const sdCell = taskRow.querySelector('.schedule-diff-cell');
        if (sdCell) {
            sdCell.textContent = `${sd.toFixed(2)}h`;
            sdCell.className = sd < 0 ? 'schedule-diff-cell schedule-diff-negative' : 'schedule-diff-cell';
        }

        // 未割当 = 実際残 − 山積計
        let ua = null;
        if (ar !== null) ua = ar - taskPlanTotal;
        const uaCell = taskRow.querySelector('.unallocated-cell');
        if (uaCell) {
            if (ua !== null) {
                uaCell.textContent = `${ua.toFixed(2)}h`;
                uaCell.className = ua < 0 ? 'unallocated-cell unallocated-negative' : 'unallocated-cell';
            } else {
                uaCell.textContent = '-';
                uaCell.className = 'unallocated-cell';
            }
        }

        // 案件・PJ集計に加算
        issueAcc[iid].est += est;
        issueAcc[iid].act += act;
        issueAcc[iid].planTotal += taskPlanTotal;
        if (ar !== null) issueAcc[iid].ar = (issueAcc[iid].ar || 0) + ar;
        if (ua !== null) issueAcc[iid].ua = (issueAcc[iid].ua || 0) + ua;
        taskMonths.forEach((v, i) => { issueAcc[iid].months[i] += v; });

        projAcc[pid].est += est;
        projAcc[pid].act += act;
        projAcc[pid].planTotal += taskPlanTotal;
        if (ar !== null) projAcc[pid].ar = (projAcc[pid].ar || 0) + ar;
        if (ua !== null) projAcc[pid].ua = (projAcc[pid].ua || 0) + ua;
        taskMonths.forEach((v, i) => { projAcc[pid].months[i] += v; });
    });

    // 案件行の集計更新
    table.querySelectorAll('.issue-row').forEach(row => {
        const a = issueAcc[row.dataset.issueId];
        if (a) _updateAggRow(row, a, monthCount);
    });

    // PJ行の集計更新
    table.querySelectorAll('.project-row').forEach(row => {
        const a = projAcc[row.dataset.projectId];
        if (a) _updateAggRow(row, a, monthCount);
    });
}

/** 案件行・PJ行の集計セルを更新 */
function _updateAggRow(row, a, monthCount) {
    const fmtH = (v) => v > 0 ? `${v.toFixed(2)}h` : '-';
    const fmtMonth = (v) => v > 0 ? v.toFixed(2) : '-';

    const estCell = row.querySelector('.estimate-summary');
    if (estCell) estCell.textContent = fmtH(a.est);

    const actCell = row.querySelector('.actual-summary');
    if (actCell) actCell.textContent = fmtH(a.act);

    const rem = a.est - a.act;
    const remCell = row.querySelector('.remaining-summary');
    if (remCell) {
        if (a.est === 0 && a.act === 0) {
            remCell.textContent = '-';
            remCell.className = 'summary-cell remaining-summary';
        } else {
            remCell.textContent = `${rem.toFixed(2)}h`;
            remCell.className = rem < 0 ? 'summary-cell remaining-summary remaining-negative' : 'summary-cell remaining-summary';
        }
    }

    const arCell = row.querySelector('.actual-remaining-summary');
    if (arCell) arCell.textContent = a.ar !== null ? `${a.ar.toFixed(2)}h` : '-';

    const sd = a.planTotal - rem;
    const sdCell = row.querySelector('.schedule-diff-summary');
    if (sdCell) {
        sdCell.textContent = `${sd.toFixed(2)}h`;
        sdCell.className = sd < 0 ? 'summary-cell schedule-diff-summary schedule-diff-negative' : 'summary-cell schedule-diff-summary';
    }

    const ptCell = row.querySelector('.plan-total-summary');
    if (ptCell) ptCell.textContent = fmtH(a.planTotal);

    const uaCell = row.querySelector('.unallocated-summary');
    if (uaCell) {
        if (a.ua !== null) {
            uaCell.textContent = `${a.ua.toFixed(2)}h`;
            uaCell.className = a.ua < 0 ? 'summary-cell unallocated-summary unallocated-negative' : 'summary-cell unallocated-summary';
        } else {
            uaCell.textContent = '-';
            uaCell.className = 'summary-cell unallocated-summary';
        }
    }

    const allTds = [...row.querySelectorAll('td')];
    allTds.slice(-monthCount).forEach((td, idx) => {
        td.textContent = fmtMonth(a.months[idx]);
    });
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

    // アサイン管理
    updateAssignmentGridCalculation();
}

/**
 * イベントリスナーの設定
 */
function initCalculation() {
    // 入力時にリアルタイム計算
    document.addEventListener('input', (e) => {
        if (e.target.matches('.log-input, .assign-input, .plan-input, .estimate-input, .progress-input, input[name="hours"]')) {
            recalculateAll();
        }
    });

    // 数値入力欄のキーボード操作
    document.addEventListener('keydown', (e) => {
        if (!e.target.matches('.log-input, .progress-input, .assign-input, .plan-input, .estimate-input')) return;

        // 上下キーを無効化（changeイベント発火が不安定なため）
        if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
            e.preventDefault();
        }

        // Enterキーで確定（フォーカスを外す）
        if (e.key === 'Enter') {
            e.preventDefault();
            e.target.blur();
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

/**
 * インライン追加フォームのトグル
 */
function toggleAddForm(button) {
    const tableCard = button.closest('.table-card');
    const addRow = tableCard.querySelector('.inline-add-row');
    if (addRow) {
        addRow.classList.toggle('hidden');
        button.classList.toggle('active');
        if (!addRow.classList.contains('hidden')) {
            const firstInput = addRow.querySelector('input');
            if (firstInput) firstInput.focus();
        }
    }
}

function hideAddForm(element) {
    const tableCard = element.closest('.table-card');
    const addRow = tableCard.querySelector('.inline-add-row');
    const button = tableCard.querySelector('.add-toggle');
    if (addRow) addRow.classList.add('hidden');
    if (button) button.classList.remove('active');
}
