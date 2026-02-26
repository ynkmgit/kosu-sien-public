/**
 * 業務終了報告画面のJS
 *
 * 責務: テンプレートAPI連携、URL操作、クリップボード、オートコンプリート統合
 * テンプレート変数は #work-report-config の data属性から取得
 */

// === 設定読み込み ===

function getWorkReportConfig() {
    const el = document.getElementById('work-report-config');
    return {
        defaultTemplate: el.dataset.defaultTemplate || '',
        currentUserId: el.dataset.userId ? Number(el.dataset.userId) : null,
        templateId: el.dataset.templateId ? Number(el.dataset.templateId) : null,
    };
}

// === テンプレートAPI連携 ===

async function saveTemplate() {
    const { templateId } = getWorkReportConfig();
    if (!templateId) {
        return saveAsTemplate();
    }
    const body = document.getElementById('template-textarea').value;
    const hideZero = document.getElementById('hide-zero-progress').checked;
    const select = document.getElementById('template-select');
    const name = select.selectedOptions[0]?.textContent?.trim();

    try {
        const resp = await fetch(`/api/report-templates/${templateId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                body: body,
                options: { hideZeroProgress: hideZero }
            })
        });
        if (resp.ok) {
            alert('テンプレートを保存しました');
        } else {
            const err = await resp.json();
            alert('保存失敗: ' + (err.detail || '不明なエラー'));
        }
    } catch (e) {
        console.error('テンプレート保存エラー:', e);
    }
}

async function saveAsTemplate() {
    const name = prompt('新しいテンプレート名を入力してください');
    if (!name) return;

    const body = document.getElementById('template-textarea').value;
    const hideZero = document.getElementById('hide-zero-progress').checked;

    try {
        const resp = await fetch('/api/report-templates', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                body: body,
                options: { hideZeroProgress: hideZero }
            })
        });
        if (resp.ok) {
            const data = await resp.json();
            alert('テンプレートを作成しました');
            navigateWithTemplate(data.id);
        } else {
            const err = await resp.json();
            alert('作成失敗: ' + (err.detail || '不明なエラー'));
        }
    } catch (e) {
        console.error('テンプレート作成エラー:', e);
    }
}

async function deleteTemplate() {
    const { templateId } = getWorkReportConfig();
    if (!templateId) return;
    if (!confirm('このテンプレートを削除しますか？')) return;

    try {
        const resp = await fetch(`/api/report-templates/${templateId}`, {
            method: 'DELETE'
        });
        if (resp.ok) {
            navigateWithTemplate(null);
        } else {
            const err = await resp.json();
            alert('削除失敗: ' + (err.detail || '不明なエラー'));
        }
    } catch (e) {
        console.error('テンプレート削除エラー:', e);
    }
}

function selectTemplate(templateId) {
    navigateWithTemplate(templateId);
}

// === URL操作 ===

function buildBaseParams() {
    const { currentUserId, templateId } = getWorkReportConfig();
    const targetDate = document.getElementById('date-input').value;
    const params = new URLSearchParams();
    if (currentUserId) params.set('user', currentUserId);
    if (targetDate) params.set('target_date', targetDate);
    if (templateId) params.set('template_id', templateId);
    return params;
}

function navigateWithTemplate(templateId) {
    const { currentUserId } = getWorkReportConfig();
    const targetDate = document.getElementById('date-input').value;
    const params = new URLSearchParams();
    if (currentUserId) params.set('user', currentUserId);
    if (targetDate) params.set('target_date', targetDate);
    if (templateId) params.set('template_id', templateId);
    window.location.href = '/work-report?' + params.toString();
}

function updateUrl() {
    const params = buildBaseParams();
    window.location.href = '/work-report?' + params.toString();
}

function selectUser(userId) {
    const { templateId } = getWorkReportConfig();
    const targetDate = document.getElementById('date-input').value;
    const params = new URLSearchParams();
    params.set('user', userId);
    if (targetDate) params.set('target_date', targetDate);
    if (templateId) params.set('template_id', templateId);
    window.location.href = '/work-report?' + params.toString();
}

function removeUser() {
    const { templateId } = getWorkReportConfig();
    const targetDate = document.getElementById('date-input').value;
    const params = new URLSearchParams();
    if (targetDate) params.set('target_date', targetDate);
    if (templateId) params.set('template_id', templateId);
    window.location.href = '/work-report?' + params.toString();
}

// === オートコンプリート（共通モジュールのselectAutocompleteをオーバーライド）===

function selectAutocomplete(type, id, label) {
    if (type === 'user') {
        selectUser(id);
    }
}

// === クリップボード ===

function copyToClipboard() {
    const previewText = document.getElementById('report-preview-text');
    if (!previewText) {
        alert('コピーする内容がありません');
        return;
    }

    const text = previewText.textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.querySelector('.btn-copy');
        btn.textContent = 'コピー完了!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = 'コピー';
            btn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('コピーに失敗しました:', err);
        alert('コピーに失敗しました');
    });
}
