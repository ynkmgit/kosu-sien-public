/**
 * アサイン管理画面のJS
 *
 * 責務: フィルター操作、折り畳み制御、担当者追加/削除（DOM操作）
 */

// === URL構築・フィルター管理 ===

function getCurrentFold() {
    return new URL(window.location.href).searchParams.get('fold') || '';
}

function getCurrentBaseMonth() {
    return new URL(window.location.href).searchParams.get('base_month') || '';
}

function buildUrl(users, projects, issues, tags, issueStatuses, taskStatuses, excludeDoneIssue, excludeDoneTask, fold, baseMonth) {
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
    const bm = baseMonth !== undefined ? baseMonth : getCurrentBaseMonth();
    if (bm) params.set('base_month', bm);
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
        baseMonth: url.searchParams.get('base_month') || '',
    };
}

function _navigateWithFilters(f) {
    window.location.href = buildUrl(
        f.users, f.projects, f.issues, f.tags,
        f.issueStatuses, f.taskStatuses, f.excludeDoneIssue, f.excludeDoneTask,
        undefined, f.baseMonth
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

// === 基準月ナビゲーション ===

function changeBaseMonth(ym) {
    const f = getCurrentFilters();
    f.baseMonth = ym;
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
    const table = document.querySelector('.grid');
    if (!table) return;
    if (mode === 'collapsed') {
        table.querySelectorAll('.project-row').forEach(row => row.classList.add('folded'));
        table.querySelectorAll('.issue-row').forEach(row => row.classList.add('collapsed', 'folded'));
        table.querySelectorAll('.task-row').forEach(row => row.classList.add('collapsed', 'folded'));
        table.querySelectorAll('.assignee-sub-row').forEach(row => row.classList.add('collapsed'));
    } else if (mode === 'issues') {
        table.querySelectorAll('.project-row').forEach(row => row.classList.remove('folded'));
        table.querySelectorAll('.issue-row').forEach(row => {
            row.classList.remove('collapsed');
            row.classList.add('folded');
        });
        table.querySelectorAll('.task-row, .assignee-sub-row').forEach(row => row.classList.add('collapsed'));
    } else if (mode === 'tasks') {
        table.querySelectorAll('.project-row').forEach(row => row.classList.remove('folded'));
        table.querySelectorAll('.issue-row').forEach(row => {
            row.classList.remove('collapsed');
            row.classList.remove('folded');
        });
        table.querySelectorAll('.task-row').forEach(row => {
            row.classList.remove('collapsed');
            row.classList.add('folded');
        });
        table.querySelectorAll('.assignee-sub-row').forEach(row => row.classList.add('collapsed'));
    } else {
        // expandAll
        table.querySelectorAll('.project-row, .issue-row, .task-row').forEach(row => row.classList.remove('folded'));
        table.querySelectorAll('.issue-row, .task-row, .assignee-sub-row').forEach(row => row.classList.remove('collapsed'));
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

// === 担当者操作（サーバーサイド HTML 生成方式） ===

let _assigneeTimeout = null;

/**
 * タスクブロック（task-row + サブ行群）をサーバーから取得した HTML で置換する
 */
function _replaceTaskBlock(taskId, html) {
    // 既存の task-row + サブ行を全削除
    const oldTaskRow = document.querySelector(`.task-row[data-task-id="${taskId}"]`);
    if (!oldTaskRow) return;
    document.querySelectorAll(`.assignee-sub-row[data-task-id="${taskId}"]`).forEach(r => r.remove());

    // サーバーから返された HTML を挿入
    const template = document.createElement('template');
    template.innerHTML = html;
    const newElements = template.content.children;

    // oldTaskRow の位置に新要素群を挿入
    const parent = oldTaskRow.parentNode;
    const ref = oldTaskRow.nextSibling;
    oldTaskRow.remove();
    // DocumentFragment から children を取り出す（ライブコレクションなので配列化）
    Array.from(template.content.children).forEach(el => {
        parent.insertBefore(el, ref);
    });
}

function _getBaseMonth() {
    return new URL(window.location.href).searchParams.get('base_month') || '';
}

// --- ＋ボタン: 担当行を追加 ---

function addAssigneeRow(taskId) {
    const taskRow = document.querySelector(`.task-row[data-task-id="${taskId}"]`);
    if (!taskRow) return;

    const hasSubRows = document.querySelectorAll(`.assignee-sub-row[data-task-id="${taskId}"]`).length > 0;
    const singleAssigneeId = taskRow.dataset.assigneeId;

    if (!singleAssigneeId && !hasSubRows) {
        // 0名モード: task-row内のautocompleteにフォーカス
        const input = taskRow.querySelector('.assignee-autocomplete-input');
        if (input) input.focus();
        return;
    }

    // マルチモード or 1名→マルチ移行: サーバーから空サブ行を取得して追加
    const body = new URLSearchParams();
    const bm = _getBaseMonth();
    if (bm) body.set('base_month', bm);

    fetch(`/assignments/tasks/${taskId}/add-row`, { method: 'POST', body })
        .then(res => {
            if (!res.ok) throw new Error('Failed');
            return res.text();
        })
        .then(html => {
            const template = document.createElement('template');
            template.innerHTML = html;
            const newRow = template.content.firstElementChild;

            const existingSubs = document.querySelectorAll(`.assignee-sub-row[data-task-id="${taskId}"]`);
            if (existingSubs.length > 0) {
                existingSubs[existingSubs.length - 1].after(newRow);
            } else {
                taskRow.after(newRow);
            }

            const input = newRow.querySelector('input');
            if (input) input.focus();
        });
}

// --- −ボタン: サブ行の削除 ---

function removeAssigneeRow(button) {
    const row = button.closest('.grid-row');
    if (!row) return;
    const assigneeId = row.dataset.assigneeId;
    const taskId = row.dataset.taskId;

    if (assigneeId) {
        if (!confirm('この担当を外しますか？')) return;
        const params = new URLSearchParams();
        const bm = _getBaseMonth();
        if (bm) params.set('base_month', bm);
        const qs = params.toString();

        fetch(`/assignments/assignees/${assigneeId}${qs ? '?' + qs : ''}`, { method: 'DELETE' })
            .then(res => {
                if (!res.ok) throw new Error('Failed');
                return res.text();
            })
            .then(html => _replaceTaskBlock(taskId, html));
    } else {
        // 未割当のサブ行は即削除（サーバー操作不要）
        row.remove();
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

    const params = new URLSearchParams();
    const bm = _getBaseMonth();
    if (bm) params.set('base_month', bm);
    const qs = params.toString();

    fetch(`/assignments/assignees/${assigneeId}${qs ? '?' + qs : ''}`, { method: 'DELETE' })
        .then(res => {
            if (!res.ok) throw new Error('Failed');
            return res.text();
        })
        .then(html => _replaceTaskBlock(taskId, html));
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
    const body = new URLSearchParams({ task_id: taskId, user_id: userId });
    const bm = _getBaseMonth();
    if (bm) body.set('base_month', bm);

    fetch('/assignments/assignees', { method: 'POST', body })
        .then(res => {
            if (!res.ok) throw new Error('Failed');
            return res.text();
        })
        .then(html => _replaceTaskBlock(taskId, html));
}

// === グリッド読み込み後の折り畳み状態復元 ===

document.addEventListener('htmx:afterSettle', () => {
    const fold = getCurrentFold();
    if (fold) applyFold(fold);
});
