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
 * 実績入力グリッドのデータモデル
 * DOM読み取りを排除し、JS変数で集計計算を行う
 */
const workLogModel = {
    rows: {},       // { "taskId-userId": { "2026-02-01": 4.0, ... } }
    rowKeys: [],    // ["taskId-userId", ...] — 行の順序を保持
    dateKeys: [],   // ["2026-02-01", "2026-02-02", ...]
    initialized: false,

    init(table) {
        this.rows = {};
        this.rowKeys = [];
        this.dateKeys = [];
        const dateSet = new Set();

        table.querySelectorAll('.log-row').forEach(row => {
            const cells = row.querySelectorAll('.log-cell');
            if (cells.length === 0) return;

            const key = `${cells[0].dataset.taskId}-${cells[0].dataset.userId}`;
            if (!this.rows[key]) {
                this.rows[key] = {};
                this.rowKeys.push(key);
            }

            cells.forEach(cell => {
                const date = cell.dataset.date;
                if (!dateSet.has(date)) {
                    dateSet.add(date);
                    this.dateKeys.push(date);
                }
                // click-to-edit: inputがあればinput.value、なければtdのテキスト
                const input = cell.querySelector('.log-input');
                this.rows[key][date] = input
                    ? safeParseFloat(input.value)
                    : safeParseFloat(cell.textContent);
            });
        });
        this.initialized = true;
    },

    update(taskId, userId, date, value) {
        const key = `${taskId}-${userId}`;
        if (!this.rows[key]) this.rows[key] = {};
        this.rows[key][date] = value;
    },

    getRowTotal(key) {
        const row = this.rows[key];
        if (!row) return 0;
        let total = 0;
        for (const d of this.dateKeys) total += row[d] || 0;
        return total;
    },

    getColTotal(date) {
        let total = 0;
        for (const key of this.rowKeys) {
            total += (this.rows[key][date] || 0);
        }
        return total;
    },

    getGrandTotal() {
        let total = 0;
        for (const key of this.rowKeys) {
            for (const d of this.dateKeys) {
                total += (this.rows[key][d] || 0);
            }
        }
        return total;
    }
};

/**
 * 実績入力の計算列を更新（データモデル方式）
 * 初回のみDOMから値を読み取ってモデルを構築。以降はモデルから集計しDOMに書き込むのみ。
 */
function updateWorkLogsCalculation() {
    const table = document.querySelector('.grid');
    if (!table || table.querySelector('.task-row')) return;  // アサイン管理は別関数

    if (!workLogModel.initialized) {
        workLogModel.init(table);
    }

    const fmtH = (v) => v > 0 ? `${v.toFixed(2)}h` : '-';
    const fmt = (v) => v > 0 ? v.toFixed(2) : '-';

    let grandTotal = 0;

    // 行合計の更新（DOM書き込みのみ）
    table.querySelectorAll('.log-row').forEach(row => {
        const firstCell = row.querySelector('.log-cell');
        if (!firstCell) return;
        const key = `${firstCell.dataset.taskId}-${firstCell.dataset.userId}`;
        const rowTotal = workLogModel.getRowTotal(key);

        const rowTotalCell = row.querySelector('.row-total');
        if (rowTotalCell) rowTotalCell.textContent = fmtH(rowTotal);

        grandTotal += rowTotal;
    });

    // 列合計の更新
    const totalRow = table.querySelector('.total-row');
    if (totalRow) {
        totalRow.querySelectorAll('.col-total').forEach((cell, index) => {
            const date = workLogModel.dateKeys[index];
            cell.textContent = fmt(date ? workLogModel.getColTotal(date) : 0);
        });

        const grandTotalCell = totalRow.querySelector('.grand-total');
        if (grandTotalCell) grandTotalCell.textContent = fmtH(grandTotal);
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
    const table = document.querySelector('.grid');
    if (!table || !table.querySelector('.task-row')) return;

    const monthCount = table.querySelectorAll('.grid-header .date-header').length;
    if (monthCount === 0) return;

    const fmtH = (v) => v > 0 ? `${v.toFixed(2)}h` : '-';
    const fmtMonth = (v) => v > 0 ? v.toFixed(2) : '-';

    // サブ行をタスクIDでグループ化（1回のDOM走査で完了）
    const subRowsByTask = {};
    table.querySelectorAll('.assignee-sub-row').forEach(row => {
        const tid = row.dataset.taskId;
        if (!subRowsByTask[tid]) subRowsByTask[tid] = [];
        subRowsByTask[tid].push(row);
    });

    // 案件・PJ集計用
    const issueAcc = {};
    const projAcc = {};

    table.querySelectorAll('.task-row').forEach(taskRow => {
        const tid = taskRow.dataset.taskId;
        const iid = taskRow.dataset.issueId;
        const pid = taskRow.dataset.projectId;

        if (!issueAcc[iid]) issueAcc[iid] = { pid, est: 0, act: 0, planTotal: 0, ar: null, ua: null, months: new Array(monthCount).fill(0) };
        if (!projAcc[pid]) projAcc[pid] = { est: 0, act: 0, planTotal: 0, ar: null, ua: null, months: new Array(monthCount).fill(0) };

        // 見積 — click-to-edit対応: inputがあればinput.value、なければcellのdata-value
        const estCell = taskRow.querySelector('.estimate-cell');
        const estInput = estCell ? estCell.querySelector('.estimate-input') : null;
        const est = estInput ? safeParseFloat(estInput.value) : (estCell ? safeParseFloat(estCell.dataset.value) : 0);

        // 実績（表示のみ）
        const actCell = taskRow.querySelector('.actual-cell');
        const act = actCell ? safeParseFloat(actCell.textContent) : 0;

        // 理論残 = 見積 − 実績
        const remaining = est - act;
        const remCell = taskRow.querySelector('.remaining-cell');
        if (remCell) {
            if (est === 0 && act === 0) {
                remCell.textContent = '-';
                remCell.toggleAttribute('data-negative', false);
            } else {
                remCell.textContent = `${remaining.toFixed(2)}h`;
                remCell.toggleAttribute('data-negative', remaining < 0);
            }
        }

        // 山積計・月別集計
        const subRows = subRowsByTask[tid] || [];
        let taskPlanTotal = 0;
        const taskMonths = new Array(monthCount).fill(0);
        const progressData = [];

        if (subRows.length > 0) {
            // マルチ担当: サブ行から集計 + タスク行のorphan plan
            const taskPTCell = taskRow.querySelector('.plan-total-summary');
            const taskHiddenPlan = taskPTCell ? safeParseFloat(taskPTCell.dataset.hiddenPlan) : 0;
            taskPlanTotal = taskHiddenPlan;

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

                // 完了%データ収集（加重平均用）— click-to-edit対応
                const progCell = subRow.querySelector('.progress-cell');
                const progInput = progCell ? progCell.querySelector('.progress-input') : null;
                const progValue = progInput ? progInput.value : (progCell ? progCell.dataset.value : '');
                if (progValue !== '' && progValue !== undefined) {
                    progressData.push({ progress: safeParseFloat(progValue), planTotal: subPlanTotal });
                }
            });

            // タスク行の月別集計セルを更新
            const gcs = taskRow.querySelectorAll('.gc');
            const start = gcs.length - monthCount;
            for (let idx = 0; idx < monthCount; idx++) {
                gcs[start + idx].textContent = fmtMonth(taskMonths[idx]);
            }
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
                progCell.toggleAttribute('data-weighted', progress !== null);
            }
        } else {
            // click-to-edit対応: inputがあればinput.value、なければcellのdata-value
            const progCell = taskRow.querySelector('.progress-cell');
            const progInput = progCell ? progCell.querySelector('.progress-input') : null;
            const progValue = progInput ? progInput.value : (progCell ? progCell.dataset.value : '');
            if (progValue !== '' && progValue !== undefined) {
                progress = safeParseFloat(progValue);
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
            sdCell.toggleAttribute('data-negative', sd < 0);
        }

        // 未割当 = 実際残 − 山積計
        let ua = null;
        if (ar !== null) ua = ar - taskPlanTotal;
        const uaCell = taskRow.querySelector('.unallocated-cell');
        if (uaCell) {
            if (ua !== null) {
                uaCell.textContent = `${ua.toFixed(2)}h`;
                uaCell.toggleAttribute('data-negative', ua < 0);
            } else {
                uaCell.textContent = '-';
                uaCell.toggleAttribute('data-negative', false);
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
            remCell.toggleAttribute('data-negative', false);
        } else {
            remCell.textContent = `${rem.toFixed(2)}h`;
            remCell.toggleAttribute('data-negative', rem < 0);
        }
    }

    const arCell = row.querySelector('.actual-remaining-summary');
    if (arCell) arCell.textContent = a.ar !== null ? `${a.ar.toFixed(2)}h` : '-';

    const sd = a.planTotal - rem;
    const sdCell = row.querySelector('.schedule-diff-summary');
    if (sdCell) {
        sdCell.textContent = `${sd.toFixed(2)}h`;
        sdCell.toggleAttribute('data-negative', sd < 0);
    }

    const ptCell = row.querySelector('.plan-total-summary');
    if (ptCell) ptCell.textContent = fmtH(a.planTotal);

    const uaCell = row.querySelector('.unallocated-summary');
    if (uaCell) {
        if (a.ua !== null) {
            uaCell.textContent = `${a.ua.toFixed(2)}h`;
            uaCell.toggleAttribute('data-negative', a.ua < 0);
        } else {
            uaCell.textContent = '-';
            uaCell.toggleAttribute('data-negative', false);
        }
    }

    const gcs = row.querySelectorAll('.gc');
    const start = gcs.length - monthCount;
    for (let idx = 0; idx < monthCount; idx++) {
        gcs[start + idx].textContent = fmtMonth(a.months[idx]);
    }
}

/**
 * ページ種別を判定して適切な計算関数を実行
 */
function recalculateAll() {
    // 実績入力
    if (document.querySelector('.grid')) {
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
let _recalcTimer = null;
function _debouncedRecalc() {
    if (_recalcTimer) return;
    _recalcTimer = requestAnimationFrame(() => {
        _recalcTimer = null;
        recalculateAll();
    });
}

/**
 * click-to-edit: log-cellをアクティブ化（input生成）
 */
function _activateLogCell(cell) {
    const currentValue = cell.textContent.trim();
    const input = document.createElement('input');
    input.type = 'number';
    input.className = 'log-input';
    input.step = '0.25';
    input.min = '0.25';
    input.value = currentValue;
    input.dataset.taskId = cell.dataset.taskId;
    input.dataset.userId = cell.dataset.userId;
    input.dataset.date = cell.dataset.date;
    input.dataset.originalValue = currentValue;

    cell.textContent = '';
    cell.appendChild(input);
    input.focus();
    input.select();

    // blur時にセルを非アクティブ化（2重呼び出しを防ぐ）
    let _logDeactivated = false;
    input.addEventListener('blur', () => {
        if (_logDeactivated) return;
        _logDeactivated = true;
        _deactivateLogCell(cell, input);
    });

    // キーボードナビゲーション
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            input.blur();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            // 元の値に戻す
            input.value = currentValue;
            input.blur();
        } else if (e.key === 'Tab') {
            e.preventDefault();
            const nextCell = e.shiftKey
                ? _findAdjacentLogCell(cell, -1)
                : _findAdjacentLogCell(cell, 1);
            input.blur();
            if (nextCell) _activateLogCell(nextCell);
        }
    });
}

/**
 * click-to-edit: log-cellを非アクティブ化（inputからテキストに戻す）
 */
function _deactivateLogCell(cell, input) {
    if (input.dataset.deactivating) return;
    input.dataset.deactivating = '1';

    const newValue = safeParseFloat(input.value);
    const originalValue = safeParseFloat(input.dataset.originalValue || '0');
    const display = newValue > 0 ? newValue.toFixed(2) : '';

    if (input.parentNode === cell) cell.removeChild(input);
    cell.textContent = display;

    // 値が変わった場合のみサーバー保存（workLogModelはinputイベントで既に更新済み）
    if (newValue !== originalValue) {
        _sendJSON('POST', '/work-logs', {
            task_id: input.dataset.taskId, user_id: input.dataset.userId,
            work_date: input.dataset.date, hours: newValue
        }, cell);
        _debouncedRecalc();
    }
}

/**
 * click-to-edit: 隣接するlog-cellを探す
 * @param {HTMLElement} cell - 現在のセル
 * @param {number} direction - 1=次, -1=前
 */
function _findAdjacentLogCell(cell, direction) {
    const row = cell.closest('.grid-row');
    const cells = Array.from(row.querySelectorAll('.log-cell'));
    const index = cells.indexOf(cell);
    const nextIndex = index + direction;

    if (nextIndex >= 0 && nextIndex < cells.length) {
        return cells[nextIndex];
    }

    // 行をまたぐ
    const rows = Array.from(row.closest('.grid').querySelectorAll('.log-row'));
    const rowIndex = rows.indexOf(row);
    const nextRow = rows[rowIndex + direction];
    if (nextRow) {
        const nextCells = nextRow.querySelectorAll('.log-cell');
        return direction > 0 ? nextCells[0] : nextCells[nextCells.length - 1];
    }
    return null;
}

/**
 * click-to-edit: status-cellをアクティブ化（select生成）
 */
function _activateStatusCell(cell) {
    const labels = JSON.parse(cell.dataset.labels);
    const current = cell.dataset.status;
    const action = cell.dataset.action;

    const select = document.createElement('select');
    select.className = `grid-status-select status-${current}`;

    // data属性をコピー
    if (cell.dataset.taskId) select.dataset.taskId = cell.dataset.taskId;
    if (cell.dataset.issueId) select.dataset.issueId = cell.dataset.issueId;
    select.dataset.action = action;

    for (const [value, label] of Object.entries(labels)) {
        const opt = document.createElement('option');
        opt.value = value;
        opt.textContent = label;
        if (value === current) opt.selected = true;
        select.appendChild(opt);
    }

    cell.textContent = '';
    cell.appendChild(select);
    select.focus();

    let deactivated = false;
    const deactivate = () => {
        if (deactivated) return;
        deactivated = true;
        _deactivateStatusCell(cell, select);
    };

    select.addEventListener('change', () => {
        const newStatus = select.value;
        // サーバー保存
        if (action === 'task-status') {
            _sendJSON('PUT', `/tasks/${cell.dataset.taskId}/status`, { status: newStatus }, cell);
        } else if (action === 'issue-status') {
            _sendJSON('PUT', `/work-logs/issue-status/${cell.dataset.issueId}`, { status: newStatus }, cell);
        }
        cell.dataset.status = newStatus;
        deactivate();
    });

    select.addEventListener('blur', deactivate);

    select.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            e.preventDefault();
            deactivate();
        }
    });
}

/**
 * click-to-edit: status-cellを非アクティブ化
 */
function _deactivateStatusCell(cell, select) {
    const status = cell.dataset.status;
    const labels = JSON.parse(cell.dataset.labels);
    cell.removeChild(select);
    cell.textContent = labels[status] || status;
    // セルのステータスクラスを更新
    cell.className = cell.className.replace(/\bstatus-\S+/g, '');
    cell.classList.add('gc', 'status-cell', `status-${status}`);
}

/**
 * click-to-edit: progress-cellをアクティブ化（input生成）
 */
function _activateProgressCell(cell) {
    const currentValue = cell.dataset.value || '';
    const input = document.createElement('input');
    input.type = 'number';
    input.className = 'progress-input';
    input.step = '1';
    input.min = '0';
    input.max = '100';
    input.value = currentValue;
    input.placeholder = '-';
    input.dataset.assigneeId = cell.dataset.assigneeId;

    cell.textContent = '';
    cell.appendChild(input);
    input.focus();
    input.select();

    let _progDeactivated = false;
    input.addEventListener('blur', () => {
        if (_progDeactivated) return;
        _progDeactivated = true;
        _deactivateProgressCell(cell, input);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            input.blur();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            input.value = currentValue;
            input.blur();
        } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
            e.preventDefault();
        }
    });
}

/**
 * click-to-edit: progress-cellを非アクティブ化
 */
function _deactivateProgressCell(cell, input) {
    if (input.dataset.deactivating) return;
    input.dataset.deactivating = '1';

    const newValue = input.value.trim();
    const oldValue = cell.dataset.value || '';
    const display = newValue !== '' ? `${newValue}%` : '';

    if (input.parentNode === cell) cell.removeChild(input);
    cell.textContent = display;
    cell.dataset.value = newValue;

    if (newValue !== oldValue) {
        _sendJSON('PUT', `/assignments/assignees/${input.dataset.assigneeId}/progress`, {
            progress_rate: newValue
        }, cell);
        _debouncedRecalc();
    }
}

/**
 * click-to-edit: estimate-cellをアクティブ化（input生成）
 */
function _activateEstimateCell(cell) {
    const currentValue = cell.dataset.value || '';
    const input = document.createElement('input');
    input.type = 'number';
    input.className = 'estimate-input';
    input.step = '0.25';
    input.min = '0';
    input.value = currentValue;
    input.dataset.taskId = cell.dataset.taskId;

    cell.textContent = '';
    cell.appendChild(input);
    input.focus();
    input.select();

    let _estDeactivated = false;
    input.addEventListener('blur', () => {
        if (_estDeactivated) return;
        _estDeactivated = true;
        _deactivateEstimateCell(cell, input);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            input.blur();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            input.value = currentValue;
            input.blur();
        } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
            e.preventDefault();
        }
    });
}

/**
 * click-to-edit: estimate-cellを非アクティブ化
 */
function _deactivateEstimateCell(cell, input) {
    if (input.dataset.deactivating) return;
    input.dataset.deactivating = '1';

    const newValue = input.value.trim();
    const oldValue = cell.dataset.value || '';
    const display = newValue && parseFloat(newValue) > 0 ? parseFloat(newValue).toFixed(2) : '';

    if (input.parentNode === cell) cell.removeChild(input);
    cell.textContent = display;
    cell.dataset.value = display;

    if (newValue !== oldValue) {
        _sendJSON('PUT', `/tasks/${input.dataset.taskId}/estimate`, {
            estimate_hours: newValue || 0
        }, cell);
        _debouncedRecalc();
    }
}

function _sendJSON(method, url, data, triggerEl) {
    const body = new URLSearchParams(data);
    if (triggerEl) triggerEl.classList.add('saving');
    return fetch(url, { method, body })
        .then(res => {
            if (triggerEl) triggerEl.classList.remove('saving');
            if (!res.ok) throw new Error(res.status);
            if (triggerEl) {
                triggerEl.classList.add('saved');
                setTimeout(() => triggerEl.classList.remove('saved'), 1500);
            }
        })
        .catch(() => {
            if (triggerEl) {
                triggerEl.classList.remove('saving');
                triggerEl.classList.add('error');
            }
        });
}

function _initGridDelegation() {
    document.addEventListener('change', (e) => {
        const t = e.target;
        t.classList.remove('error');

        // 工数入力 / 進捗率 / ステータス / 見積 — click-to-editのblurで処理するためchangeは不要

        // 月次計画 (.plan-input)
        if (t.matches('.plan-input')) {
            _sendJSON('POST', '/assignments/plans', {
                task_id: t.dataset.taskId, user_id: t.dataset.userId,
                year_month: t.dataset.yearMonth, planned_hours: t.value || 0
            }, t);
            return;
        }

        // 月次アサイン (.assign-input)
        if (t.matches('.assign-input')) {
            _sendJSON('POST', '/monthly-assignments', {
                user_id: t.dataset.userId, project_id: t.dataset.projectId,
                year_month: t.dataset.yearMonth, hours: t.value || 0
            }, t);
            return;
        }
    });
}

function initCalculation() {
    // グリッド入力のイベントデリゲーション
    _initGridDelegation();

    // click-to-edit: セルクリックで入力要素を動的生成
    document.addEventListener('click', (e) => {
        const cell = e.target.closest('.log-cell');
        if (cell && !cell.querySelector('.log-input')) {
            _activateLogCell(cell);
            return;
        }

        // status-cell click-to-edit
        const statusCell = e.target.closest('.status-cell');
        if (statusCell && !statusCell.querySelector('select') && statusCell.dataset.labels) {
            _activateStatusCell(statusCell);
            return;
        }

        // progress-cell click-to-edit（加重平均表示のdata-weightedは除外）
        const progressCell = e.target.closest('.progress-cell');
        if (progressCell && !progressCell.querySelector('.progress-input')
            && progressCell.dataset.assigneeId && !progressCell.hasAttribute('data-weighted')) {
            _activateProgressCell(progressCell);
            return;
        }

        // estimate-cell click-to-edit
        const estimateCell = e.target.closest('.estimate-cell');
        if (estimateCell && !estimateCell.querySelector('.estimate-input') && estimateCell.dataset.taskId) {
            _activateEstimateCell(estimateCell);
            return;
        }

        // 空plan-cellクリックでinput動的生成
        const planCell = e.target.closest('.plan-cell-empty');
        if (planCell) {
            const input = document.createElement('input');
            input.type = 'number';
            input.className = 'plan-input';
            input.step = '0.25';
            input.min = '0';
            input.dataset.taskId = planCell.dataset.taskId;
            input.dataset.userId = planCell.dataset.userId;
            input.dataset.yearMonth = planCell.dataset.yearMonth;

            planCell.classList.remove('plan-cell-empty');
            planCell.textContent = '';
            planCell.appendChild(input);
            input.focus();
        }
    });

    // 入力時にリアルタイム計算（デバウンス付き）
    document.addEventListener('input', (e) => {
        const t = e.target;
        if (t.matches('.log-input')) {
            workLogModel.update(t.dataset.taskId, t.dataset.userId, t.dataset.date, safeParseFloat(t.value));
        }
        if (t.matches('.log-input, .assign-input, .plan-input, .estimate-input, .progress-input, input[name="hours"]')) {
            _debouncedRecalc();
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

    // 初期表示時に計算
    document.addEventListener('DOMContentLoaded', recalculateAll);

    // HTMXの動的コンテンツ読み込み後にモデルリセット＋再計算
    document.addEventListener('htmx:afterSettle', () => {
        workLogModel.initialized = false;
        _debouncedRecalc();
    });
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
