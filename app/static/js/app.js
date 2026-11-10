function posterImg(ev) {
  return ev.has_poster ? '<img class="poster-img" src="/api/events/' + encodeURIComponent(ev.id) + '/poster" alt="">' : '';
}

async function api(path, options = {}) {
  const init = {
    method: options.method || 'GET',
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  };
  if (options.json !== undefined) {
    init.headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(options.json);
  } else if (options.body !== undefined) {
    init.body = options.body;
  }
  let res;
  try {
    res = await fetch(path, init);
  } catch (e) {
    throw new Error('Could not reach the server');
  }
  let data = null;
  if (res.status !== 204) {
    try { data = await res.json(); } catch (e) { data = null; }
  }
  if (!res.ok) {
    const err = new Error((data && typeof data.error === 'string' && data.error) || 'Something went wrong, please try again');
    err.status = res.status;
    throw err;
  }
  return data;
}

async function getMe() {
  try {
    return await api('/api/me');
  } catch (e) {
    return null;
  }
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('en-GB', {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function formatPrice(n) {
  const value = Number(n);
  if (value === 0) return 'Free';
  return new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR' }).format(value);
}

function hueFor(id) {
  return (Number(id) * 137) % 360;
}

function dateBadge(iso) {
  const d = new Date(iso);
  return '<div class="date-badge"><span class="date-day">' + d.getDate() + '</span><span class="date-month">'
    + d.toLocaleString('en-GB', { month: 'short' }) + '</span></div>';
}

function renderNav(me) {
  const nav = document.getElementById('nav');
  const here = location.pathname;
  const link = (href, label) => '<a href="' + href + '"' + (here === href ? ' aria-current="page"' : '') + '>' + label + '</a>';
  let links = link(me ? '/events' : '/', 'Events');
  let user;
  if (me) {
    links += me.role === 'organizer' ? link('/organizer', 'My events') : link('/tickets', 'My tickets');
    user = '<span class="nav-email" title="' + escapeHtml(me.email) + '">' + escapeHtml(me.email) + '</span>'
      + '<form action="/logout" method="POST"><button class="btn btn-ghost" type="submit">Sign out</button></form>';
  } else {
    user = link('/login', 'Log in') + '<a class="btn btn-primary" href="/register">Register</a>';
  }
  nav.innerHTML = '<div class="container nav-inner"><a class="brand" href="/">Vibe Tickets</a>'
    + '<nav class="nav-links" aria-label="Main">' + links + '</nav><div class="nav-user">' + user + '</div></div>';
}

function toast(message, kind = 'success') {
  let box = document.getElementById('toasts');
  if (!box) {
    box = document.createElement('div');
    box.id = 'toasts';
    box.className = 'toasts';
    box.setAttribute('role', 'status');
    document.body.appendChild(box);
  }
  const t = document.createElement('div');
  t.className = 'toast toast-' + kind;
  t.textContent = message;
  box.appendChild(t);
  setTimeout(() => t.remove(), 4500);
}

function confirmDialog({ title, message, confirmLabel, danger = false }) {
  return new Promise((resolve) => {
    const dlg = document.createElement('dialog');
    dlg.className = 'modal';
    dlg.setAttribute('aria-labelledby', 'confirm-title');
    dlg.innerHTML = '<form method="dialog" class="modal-content"><h2 id="confirm-title"></h2><p class="muted"></p>'
      + '<div class="modal-actions"><button class="btn btn-ghost" value="cancel">Keep it</button>'
      + '<button class="btn ' + (danger ? 'btn-danger' : 'btn-primary') + '" value="ok"></button></div></form>';
    dlg.querySelector('h2').textContent = title;
    dlg.querySelector('p').textContent = message;
    dlg.querySelector('[value="ok"]').textContent = confirmLabel;
    dlg.addEventListener('close', () => { resolve(dlg.returnValue === 'ok'); dlg.remove(); });
    document.body.appendChild(dlg);
    dlg.showModal();
  });
}
