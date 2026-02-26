/**
 * 実績入力画面のJS
 *
 * 責務: フィルター操作、表示切替、折り畳み制御
 * テンプレート変数は #work-logs-config の data属性から取得
 */

// === 設定読み込み ===

function getWorkLogsConfig() {
    const el = document.getElementById('work-logs-config');
    return {
        view: el.dataset.view || 'week',
        weekStart: el.dataset.weekStart || '',
        yearMonth: el.dataset.yearMonth || ''
    };
}

// === URL構築・フィルター管理 ===

function getCurrentFold() {
    return new URL(window.location.href).searchParams.get('fold') || '';
}

function buildUrl(users, projects, issues, tags, issueStatuses, taskStatuses, excludeDoneIssue, excludeDoneTask, view, dateParam, fold) {
    const params = new URLSearchParams();
    users.forEach(u => params.append('user', u));
    projects.forEach(p => params.append('project', p));
    issues.forEach(i => params.append('issue', i));
    tags.forEach(t => params.append('tag', t));
    issueStatuses.forEach(s => params.append('issue_status', s));
    taskStatuses.forEach(s => params.append('task_status', s));
    if (excludeDoneIssue) params.set('exclude_done_issue', 'true');
    if (excludeDoneTask) params.set('exclude_done_task', 'true');
    params.set('view', view);
    if (view === 'week') {
        params.set('week', dateParam);
    } else {
        params.set('month', dateParam);
    }
    const f = fold !== undefined ? fold : getCurrentFold();
    if (f) params.set('fold', f);
    return '/work-logs?' + params.toString();
}

function getCurrentFilters() {
    const url = new URL(window.location.href);
    const config = getWorkLogsConfig();
    return {
        users: url.searchParams.getAll('user').map(Number),
        projects: url.searchParams.getAll('project').map(Number),
        issues: url.searchParams.getAll('issue').map(Number),
        tags: url.searchParams.getAll('tag').map(Number),
        issueStatuses: url.searchParams.getAll('issue_status').map(Number),
        taskStatuses: url.searchParams.getAll('task_status').map(Number),
        excludeDoneIssue: url.searchParams.get('exclude_done_issue') === 'true',
        excludeDoneTask: url.searchParams.get('exclude_done_task') === 'true',
        view: url.searchParams.get('view') || config.view,
        week: url.searchParams.get('week') || config.weekStart,
        month: url.searchParams.get('month') || config.yearMonth,
    };
}

function _navigateWithFilters(f) {
    const dateParam = f.view === 'week' ? f.week : f.month;
    window.location.href = buildUrl(
        f.users, f.projects, f.issues, f.tags,
        f.issueStatuses, f.taskStatuses, f.excludeDoneIssue, f.excludeDoneTask,
        f.view, dateParam
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

function changeWeek(newWeek) {
    const f = getCurrentFilters();
    f.view = 'week';
    f.week = newWeek;
    _navigateWithFilters(f);
}

function changeMonth(newMonth) {
    const f = getCurrentFilters();
    f.view = 'month';
    f.month = newMonth;
    _navigateWithFilters(f);
}

function changeView(newView) {
    const f = getCurrentFilters();
    f.view = newView;
    if (newView === 'week') {
        const today = new Date();
        const dayOfWeek = today.getDay();
        const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
        const monday = new Date(today);
        monday.setDate(today.getDate() + diff);
        f.week = monday.toISOString().split('T')[0];
    } else {
        f.month = new Date().toISOString().slice(0, 7);
    }
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

// === 折り畳み機能 ===

function toggleProject(projectId) {
    const projectRow = document.querySelector(`.project-row[data-project-id="${projectId}"]`);
    const isFolded = projectRow.classList.toggle('folded');

    const issueRows = document.querySelectorAll(`.issue-row[data-project-id="${projectId}"]`);
    const logRows = document.querySelectorAll(`.log-row[data-project-id="${projectId}"]`);

    if (isFolded) {
        issueRows.forEach(row => row.classList.add('collapsed', 'folded'));
        logRows.forEach(row => row.classList.add('collapsed'));
    } else {
        issueRows.forEach(row => row.classList.remove('collapsed'));
        logRows.forEach(row => {
            const issueId = row.dataset.issueId;
            const issueRow = document.querySelector(`.issue-row[data-project-id="${projectId}"][data-issue-id="${issueId}"]`);
            if (issueRow && issueRow.classList.contains('folded')) {
                row.classList.add('collapsed');
            } else {
                row.classList.remove('collapsed');
            }
        });
    }
}

function toggleIssue(projectId, issueId) {
    const issueRow = document.querySelector(`.issue-row[data-project-id="${projectId}"][data-issue-id="${issueId}"]`);
    const isFolded = issueRow.classList.toggle('folded');

    const logRows = document.querySelectorAll(`.log-row[data-project-id="${projectId}"][data-issue-id="${issueId}"]`);
    logRows.forEach(row => row.classList.toggle('collapsed', isFolded));
}

function applyFold(mode) {
    if (mode === 'collapsed') {
        document.querySelectorAll('.project-row').forEach(row => row.classList.add('folded'));
        document.querySelectorAll('.issue-row').forEach(row => row.classList.add('collapsed', 'folded'));
        document.querySelectorAll('.log-row').forEach(row => row.classList.add('collapsed'));
    } else if (mode === 'issues') {
        document.querySelectorAll('.project-row').forEach(row => row.classList.remove('folded'));
        document.querySelectorAll('.issue-row').forEach(row => {
            row.classList.remove('collapsed');
            row.classList.add('folded');
        });
        document.querySelectorAll('.log-row').forEach(row => row.classList.add('collapsed'));
    } else {
        document.querySelectorAll('.project-row, .issue-row').forEach(row => row.classList.remove('folded'));
        document.querySelectorAll('.issue-row, .log-row').forEach(row => row.classList.remove('collapsed'));
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

// === グリッド読み込み後の折り畳み状態復元 ===

document.addEventListener('htmx:afterSettle', () => {
    const fold = getCurrentFold();
    if (fold) applyFold(fold);
});
