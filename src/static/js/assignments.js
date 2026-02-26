/**
 * アサイン管理画面のJS
 *
 * 責務: フィルター操作、折り畳み制御、担当者追加/削除（DOM操作）
 */

// === URL構築・フィルター管理 ===

function getCurrentFold() {
    return new URL(window.location.href).searchParams.get('fold') || '';
}

function buildUrl(users, projects, issues, tags, issueStatuses, taskStatuses, excludeDoneIssue, excludeDoneTask, fold) {
    const params = new URLSearchParams();
    users.forEach(u => params.append('user', u));
    projects.forEach(p => params.append('project', p));
    issues.forEach(i => params.append('issue', i));
    tags.forEach(t => params.append('tag', t));
    issueStatuses.forEach(s => params.append('issue_status', s));
    taskStatuses.forEach(s => params.append('task_status', s));
    if (excludeDoneIssue) params.set('exclude_done_issue', 'true');
    if (excludeDoneTask) params.set('exclude_done_task', 'true');
    const f = fold !== undefined ? fold : getCurrentFold();
    if (f) params.set('fold', f);
    return '/assignments?' + params.toString();
}

function getCurrentFilters() {
    const url = new URL(window.location.href);
    return {
        users: url.searchParams.getAll('user').map(Number),
        projects: url.searchParams.getAll('project').map(Number),
        issues: url.searchParams.getAll('issue').map(Number),
        tags: url.searchParams.getAll('tag').map(Number),
        issueStatuses: url.searchParams.getAll('issue_status').map(Number),
        taskStatuses: url.searchParams.getAll('task_status').map(Number),
        excludeDoneIssue: url.searchParams.get('exclude_done_issue') === 'true',
        excludeDoneTask: url.searchParams.get('exclude_done_task') === 'true',
    };
}

function _navigateWithFilters(f) {
    window.location.href = buildUrl(
        f.users, f.projects, f.issues, f.tags,
        f.issueStatuses, f.taskStatuses, f.excludeDoneIssue, f.excludeDoneTask
    );
}

function addFilter(type, value) {
    if (!value) return;
    const f = getCurrentFilters();
    const v = Number(value);
    if (type === 'user') {
        if (!f.users.includes(v)) f.users.push(v);
    } else if (type === 'project') {
        if (!f.projects.includes(v)) f.projects.push(v);
    } else if (type === 'issue') {
        if (!f.issues.includes(v)) f.issues.push(v);
    } else if (type === 'tag') {
        if (!f.tags.includes(v)) f.tags.push(v);
    } else if (type === 'issue_status') {
        if (!f.issueStatuses.includes(v)) f.issueStatuses.push(v);
    } else if (type === 'task_status') {
        if (!f.taskStatuses.includes(v)) f.taskStatuses.push(v);
    }
    _navigateWithFilters(f);
}

function removeFilter(type, id) {
    const f = getCurrentFilters();
    const v = Number(id);
    const removeFrom = (arr) => { const idx = arr.indexOf(v); if (idx > -1) arr.splice(idx, 1); };
    if (type === 'user') removeFrom(f.users);
    else if (type === 'project') removeFrom(f.projects);
    else if (type === 'issue') removeFrom(f.issues);
    else if (type === 'tag') removeFrom(f.tags);
    else if (type === 'issue_status') removeFrom(f.issueStatuses);
    else if (type === 'task_status') removeFrom(f.taskStatuses);
    _navigateWithFilters(f);
}

// === 完了除外トグル ===

function toggleExcludeDoneIssue() {
    const f = getCurrentFilters();
    f.excludeDoneIssue = !f.excludeDoneIssue;
    _navigateWithFilters(f);
}

function toggleExcludeDoneTask() {
    const f = getCurrentFilters();
    f.excludeDoneTask = !f.excludeDoneTask;
    _navigateWithFilters(f);
}

// === ステータス変更時の色クラス更新 ===

function updateStatusClass(select) {
    select.className = select.className.replace(/\bstatus-\S+/g, '');
    select.classList.add('grid-status-select', 'status-' + select.value);
}

// === 折り畳み機能（4階層対応） ===

function toggleProject(projectId) {
    const projectRow = document.querySelector(`.project-row[data-project-id="${projectId}"]`);
    const isFolded = projectRow.classList.toggle('folded');

    const childSelectors = [
        `.issue-row[data-project-id="${projectId}"]`,
        `.task-row[data-project-id="${projectId}"]`,
        `.assignee-sub-row[data-project-id="${projectId}"]`,
    ];

    if (isFolded) {
        document.querySelectorAll(childSelectors[0]).forEach(row => row.classList.add('collapsed', 'folded'));
        childSelectors.slice(1).forEach(sel =>
            document.querySelectorAll(sel).forEach(row => row.classList.add('collapsed'))
        );
    } else {
        document.querySelectorAll(childSelectors[0]).forEach(row => row.classList.remove('collapsed'));
        document.querySelectorAll(childSelectors[0]).forEach(issueRow => {
            const issueId = issueRow.dataset.issueId;
            if (issueRow.classList.contains('folded')) {
                [1, 2].forEach(i => {
                    document.querySelectorAll(
                        childSelectors[i].replace(`"${projectId}"`, `"${projectId}"][data-issue-id="${issueId}"`)
                    ).forEach(row => row.classList.add('collapsed'));
                });
            } else {
                document.querySelectorAll(
                    `.task-row[data-project-id="${projectId}"][data-issue-id="${issueId}"]`
                ).forEach(taskRow => {
                    taskRow.classList.remove('collapsed');
                    const taskId = taskRow.dataset.taskId;
                    const subHidden = taskRow.classList.contains('folded');
                    document.querySelectorAll(
                        `.assignee-sub-row[data-project-id="${projectId}"][data-issue-id="${issueId}"][data-task-id="${taskId}"]`
                    ).forEach(row => row.classList.toggle('collapsed', subHidden));
                });
            }
        });
    }
}

function toggleIssue(projectId, issueId) {
    const issueRow = document.querySelector(`.issue-row[data-project-id="${projectId}"][data-issue-id="${issueId}"]`);
    const isFolded = issueRow.classList.toggle('folded');

    const base = `[data-project-id="${projectId}"][data-issue-id="${issueId}"]`;
    document.querySelectorAll(`.task-row${base}`).forEach(row => row.classList.toggle('collapsed', isFolded));
    document.querySelectorAll(`.assignee-sub-row${base}`).forEach(row =>
        row.classList.toggle('collapsed', isFolded)
    );
}

function toggleTask(projectId, issueId, taskId) {
    const taskRow = document.querySelector(
        `.task-row[data-project-id="${projectId}"][data-issue-id="${issueId}"][data-task-id="${taskId}"]`
    );
    const isFolded = taskRow.classList.toggle('folded');

    const base = `[data-project-id="${projectId}"][data-issue-id="${issueId}"][data-task-id="${taskId}"]`;
    document.querySelectorAll(`.assignee-sub-row${base}`).forEach(row =>
        row.classList.toggle('collapsed', isFolded)
    );
}

function applyFold(mode) {
    if (mode === 'collapsed') {
        document.querySelectorAll('.project-row').forEach(row => row.classList.add('folded'));
        document.querySelectorAll('.issue-row').forEach(row => row.classList.add('collapsed', 'folded'));
        document.querySelectorAll('.task-row').forEach(row => row.classList.add('collapsed', 'folded'));
        document.querySelectorAll('.assignee-sub-row').forEach(row => row.classList.add('collapsed'));
    } else if (mode === 'issues') {
        document.querySelectorAll('.project-row').forEach(row => row.classList.remove('folded'));
        document.querySelectorAll('.issue-row').forEach(row => {
            row.classList.remove('collapsed');
            row.classList.add('folded');
        });
        document.querySelectorAll('.task-row, .assignee-sub-row').forEach(row => row.classList.add('collapsed'));
    } else if (mode === 'tasks') {
        document.querySelectorAll('.project-row').forEach(row => row.classList.remove('folded'));
        document.querySelectorAll('.issue-row').forEach(row => {
            row.classList.remove('collapsed');
            row.classList.remove('folded');
        });
        document.querySelectorAll('.task-row').forEach(row => {
            row.classList.remove('collapsed');
            row.classList.add('folded');
        });
        document.querySelectorAll('.assignee-sub-row').forEach(row => row.classList.add('collapsed'));
    } else {
        // expandAll
        document.querySelectorAll('.project-row, .issue-row, .task-row').forEach(row => row.classList.remove('folded'));
        document.querySelectorAll('.issue-row, .task-row, .assignee-sub-row').forEach(row => row.classList.remove('collapsed'));
    }
}

function setFoldUrl(mode) {
    const url = new URL(window.location.href);
    if (mode) {
        url.searchParams.set('fold', mode);
    } else {
        url.searchParams.delete('fold');
    }
    history.replaceState(null, '', url.toString());
}

function expandAll() {
    applyFold('');
    setFoldUrl('');
}

function collapseAll() {
    applyFold('collapsed');
    setFoldUrl('collapsed');
}

function collapseToIssues() {
    applyFold('issues');
    setFoldUrl('issues');
}

function collapseToTasks() {
    applyFold('tasks');
    setFoldUrl('tasks');
}

// === 担当者操作（DOM操作中心） ===

let _assigneeTimeout = null;

function _getMonths() {
    const headerRow = document.querySelector('.log-table thead tr');
    if (!headerRow) return [];
    return Array.from(headerRow.querySelectorAll('.date-header')).map(th => th.dataset.yearMonth);
}

function _getMonthCellCount() {
    return _getMonths().length || 7;
}

function _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function _planCellsHtml(taskId, userId) {
    const months = _getMonths();
    return months.map(ym =>
        `<td class="plan-cell"><input type="number" class="plan-input" step="0.25" min="0" value="" ` +
        `data-task-id="${taskId}" data-user-id="${userId}" data-year-month="${ym}" ` +
        `hx-post="/assignments/plans" hx-trigger="change" ` +
        `hx-vals='js:{task_id: event.target.dataset.taskId, user_id: event.target.dataset.userId, year_month: event.target.dataset.yearMonth, planned_hours: event.target.value || 0}' ` +
        `hx-swap="none"></td>`
    ).join('');
}

function _replaceMonthlyCells(row, taskId, userId) {
    const months = _getMonths();
    const logCells = row.querySelectorAll('td.log-cell');
    logCells.forEach((cell, i) => {
        if (i < months.length) {
            const ym = months[i];
            const td = document.createElement('td');
            td.className = 'plan-cell';
            td.innerHTML = `<input type="number" class="plan-input" step="0.25" min="0" value="" ` +
                `data-task-id="${taskId}" data-user-id="${userId}" data-year-month="${ym}" ` +
                `hx-post="/assignments/plans" hx-trigger="change" ` +
                `hx-vals='js:{task_id: event.target.dataset.taskId, user_id: event.target.dataset.userId, year_month: event.target.dataset.yearMonth, planned_hours: event.target.value || 0}' ` +
                `hx-swap="none">`;
            cell.replaceWith(td);
        }
    });
    htmx.process(row);
}

function _autocompleteHtml(taskId) {
    return (
        '<div class="assignee-autocomplete-wrapper">' +
        `<input type="text" class="autocomplete-input assignee-autocomplete-input" ` +
        `placeholder="ユーザーを検索..." autocomplete="off" ` +
        `data-task-id="${taskId}" ` +
        `oninput="searchAssignees(this, ${taskId})" ` +
        `onfocus="searchAssignees(this, ${taskId})" ` +
        `onblur="hideAssigneeAutocomplete(this)">` +
        '<div class="autocomplete-dropdown assignee-autocomplete-dropdown"></div>' +
        '</div>'
    );
}

// --- バッジ更新（マルチモード用） ---

function _updateAssigneeCount(taskId) {
    const taskRow = document.querySelector(`.task-row[data-task-id="${taskId}"]`);
    if (!taskRow) return;
    // シングルモード（data-assignee-id あり）ではバッジなし
    if (taskRow.dataset.assigneeId) return;
    const assigned = document.querySelectorAll(`.assignee-sub-row[data-task-id="${taskId}"][data-assignee-id]`).length;
    const badge = taskRow.querySelector('.assignee-count-badge');
    if (!badge) return;
    badge.textContent = assigned > 0 ? `${assigned}名` : '未割当';
    badge.classList.toggle('assignee-count-zero', assigned === 0);
}

// --- ＋ボタン: 担当行を追加 ---

function addAssigneeRow(taskId) {
    const taskRow = document.querySelector(`.task-row[data-task-id="${taskId}"]`);
    if (!taskRow) return;

    const hasSubRows = document.querySelectorAll(`.assignee-sub-row[data-task-id="${taskId}"]`).length > 0;
    const singleAssigneeId = taskRow.dataset.assigneeId;
    const countCell = taskRow.querySelector('.assignee-count-cell');

    if (!singleAssigneeId && !hasSubRows) {
        // 0名モード: task-row内のautocompleteにフォーカス
        const input = countCell.querySelector('.assignee-autocomplete-input');
        if (input) input.focus();
        return;
    }

    if (singleAssigneeId && !hasSubRows) {
        // 1名モード → マルチモードに移行
        const userName = countCell.querySelector('.assignee-display')?.textContent || '';
        const planInput = taskRow.querySelector('.plan-input');
        const userId = planInput ? planInput.dataset.userId : null;

        // 既存の担当者をサブ行に移動
        _createAssigneeSubRow(taskId, taskRow, singleAssigneeId, userName, userId);
        // 空のサブ行を追加
        _createEmptySubRow(taskId, taskRow);

        // task-rowをマルチモードに切り替え
        delete taskRow.dataset.assigneeId;
        countCell.innerHTML = '<span class="assignee-count-badge">1名</span>';

        // 作業列の−ボタンを除去
        const minusBtn = taskRow.querySelector('.task-actions .btn-remove-assignee');
        if (minusBtn) minusBtn.remove();
        return;
    }

    // マルチモード: サブ行を追加
    _createEmptySubRow(taskId, taskRow);
}

function _createAssigneeSubRow(taskId, taskRow, assigneeId, userName, userId) {
    const pid = taskRow.dataset.projectId;
    const iid = taskRow.dataset.issueId;
    const planCells = userId ? _planCellsHtml(taskId, userId) : '<td class="log-cell"></td>'.repeat(_getMonthCellCount());

    const tr = document.createElement('tr');
    tr.className = 'assignee-sub-row';
    tr.dataset.projectId = pid;
    tr.dataset.issueId = iid;
    tr.dataset.taskId = String(taskId);
    tr.dataset.assigneeId = String(assigneeId);
    tr.innerHTML =
        '<td class="assignee-indent"><button type="button" class="btn-remove-assignee" onclick="removeAssigneeRow(this)" title="担当行を削除">−</button></td>' +
        `<td class="assignee-name-cell"><span class="assignee-display">${_escapeHtml(userName)}</span></td>` +
        '<td></td>' +
        '<td></td>' +
        '<td></td>' +
        '<td></td>' +
        '<td></td>' +
        '<td></td>' +
        '<td></td>' +
        '<td class="summary-cell plan-total-summary">-</td>' +
        '<td></td>' +
        planCells;

    const existingSubs = document.querySelectorAll(`.assignee-sub-row[data-task-id="${taskId}"]`);
    if (existingSubs.length > 0) {
        existingSubs[existingSubs.length - 1].after(tr);
    } else {
        taskRow.after(tr);
    }
    htmx.process(tr);
}

function _createEmptySubRow(taskId, taskRow) {
    const pid = taskRow.dataset.projectId;
    const iid = taskRow.dataset.issueId;
    const monthCount = _getMonthCellCount();
    const emptyCells = '<td class="log-cell"></td>'.repeat(monthCount);

    const tr = document.createElement('tr');
    tr.className = 'assignee-sub-row';
    tr.dataset.projectId = pid;
    tr.dataset.issueId = iid;
    tr.dataset.taskId = String(taskId);
    tr.innerHTML =
        '<td class="assignee-indent"><button type="button" class="btn-remove-assignee" onclick="removeAssigneeRow(this)" title="担当行を削除">−</button></td>' +
        '<td class="assignee-name-cell">' + _autocompleteHtml(taskId) + '</td>' +
        '<td></td>' +
        '<td></td>' +
        '<td></td>' +
        '<td></td>' +
        '<td></td>' +
        '<td></td>' +
        '<td></td>' +
        '<td class="summary-cell plan-total-summary">-</td>' +
        '<td></td>' +
        emptyCells;

    const existingSubs = document.querySelectorAll(`.assignee-sub-row[data-task-id="${taskId}"]`);
    if (existingSubs.length > 0) {
        existingSubs[existingSubs.length - 1].after(tr);
    } else {
        taskRow.after(tr);
    }

    tr.querySelector('input').focus();
}

// --- −ボタン: サブ行の削除 ---

function removeAssigneeRow(button) {
    const row = button.closest('tr');
    if (!row) return;
    const assigneeId = row.dataset.assigneeId;
    const taskId = row.dataset.taskId;

    const doRemove = () => {
        row.remove();
        // サブ行が全てなくなったらtask-rowをautocompleteモードに戻す
        const remaining = document.querySelectorAll(`.assignee-sub-row[data-task-id="${taskId}"]`);
        if (remaining.length === 0) {
            _revertToAutocomplete(taskId);
        } else {
            _updateAssigneeCount(taskId);
        }
    };

    if (assigneeId) {
        if (!confirm('この担当を外しますか？')) return;
        fetch(`/assignments/assignees/${assigneeId}`, { method: 'DELETE' })
            .then(res => { if (res.ok) doRemove(); });
    } else {
        doRemove();
    }
}

// --- −ボタン: task-row内のシングル担当を削除 ---

function removeTaskAssignee(button) {
    const taskRow = button.closest('.task-row');
    if (!taskRow) return;
    const assigneeId = taskRow.dataset.assigneeId;
    const taskId = taskRow.dataset.taskId;
    if (!assigneeId) return;

    if (!confirm('この担当を外しますか？')) return;

    fetch(`/assignments/assignees/${assigneeId}`, { method: 'DELETE' })
        .then(res => {
            if (res.ok) {
                // autocompleteモードに戻す
                delete taskRow.dataset.assigneeId;
                const countCell = taskRow.querySelector('.assignee-count-cell');
                countCell.innerHTML = _autocompleteHtml(taskId);
                // −ボタンを除去
                button.remove();
            }
        });
}

// --- task-rowをautocompleteモードに戻す ---

function _revertToAutocomplete(taskId) {
    const taskRow = document.querySelector(`.task-row[data-task-id="${taskId}"]`);
    if (!taskRow) return;
    delete taskRow.dataset.assigneeId;
    const countCell = taskRow.querySelector('.assignee-count-cell');
    countCell.innerHTML = _autocompleteHtml(taskId);
    // 作業列の−ボタンがあれば除去
    const minusBtn = taskRow.querySelector('.task-actions .btn-remove-assignee');
    if (minusBtn) minusBtn.remove();
}

// --- オートコンプリート検索 ---

function searchAssignees(input, taskId) {
    const query = input.value.trim();
    const dropdown = input.nextElementSibling;

    clearTimeout(_assigneeTimeout);
    _assigneeTimeout = setTimeout(() => {
        fetch(`/search/task_users?task_id=${taskId}&q=${encodeURIComponent(query)}`)
            .then(res => res.text())
            .then(html => {
                dropdown.innerHTML = html;
                dropdown.classList.add('show');
            });
    }, 150);
}

function hideAssigneeAutocomplete(input) {
    setTimeout(() => {
        const dropdown = input.nextElementSibling;
        if (dropdown) dropdown.classList.remove('show');
    }, 200);
}

// --- ユーザー選択 ---

function selectAssignee(taskId, userId) {
    // アクティブな入力欄を特定（task-row内 or サブ行内）
    const allInputs = document.querySelectorAll(`.assignee-autocomplete-input[data-task-id="${taskId}"]`);
    let activeInput = null;
    allInputs.forEach(inp => { if (document.activeElement === inp) activeInput = inp; });
    const targetRow = activeInput ? activeInput.closest('tr') : null;

    // どちらにもない場合: 最初の空サブ行 or task-row
    const fallbackRow = targetRow ||
        document.querySelector(`.assignee-sub-row[data-task-id="${taskId}"]:not([data-assignee-id])`) ||
        document.querySelector(`.task-row[data-task-id="${taskId}"]`);

    fetch('/assignments/assignees', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `task_id=${taskId}&user_id=${userId}`
    })
    .then(res => {
        if (!res.ok) throw new Error('Failed');
        return res.json();
    })
    .then(data => {
        if (!fallbackRow) return;

        if (fallbackRow.classList.contains('task-row')) {
            // task-row内（0名モード → 1名モードに移行）
            fallbackRow.dataset.assigneeId = data.assignee_id;
            const countCell = fallbackRow.querySelector('.assignee-count-cell');
            countCell.innerHTML = `<span class="assignee-display">${_escapeHtml(data.user_name)}</span>`;
            // 月セルを計画入力欄に置き換え
            _replaceMonthlyCells(fallbackRow, taskId, userId);
            // 作業列に−ボタンを追加
            const taskActions = fallbackRow.querySelector('.task-actions');
            const plusBtn = taskActions.querySelector('.btn-add-assignee');
            if (plusBtn && !taskActions.querySelector('.btn-remove-assignee')) {
                const minusBtn = document.createElement('button');
                minusBtn.type = 'button';
                minusBtn.className = 'btn-remove-assignee';
                minusBtn.setAttribute('onclick', 'removeTaskAssignee(this)');
                minusBtn.title = '担当を外す';
                minusBtn.textContent = '−';
                plusBtn.after(minusBtn);
            }
        } else {
            // サブ行内
            fallbackRow.dataset.assigneeId = data.assignee_id;
            const nameCell = fallbackRow.querySelector('.assignee-name-cell');
            nameCell.innerHTML = `<span class="assignee-display">${_escapeHtml(data.user_name)}</span>`;
            // 月セルを計画入力欄に置き換え
            _replaceMonthlyCells(fallbackRow, taskId, userId);
            _updateAssigneeCount(taskId);
        }
    });
}

// === グリッド読み込み後の折り畳み状態復元 ===

document.addEventListener('htmx:afterSettle', () => {
    const fold = getCurrentFold();
    if (fold) applyFold(fold);
});
