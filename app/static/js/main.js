/* EduSphere — Main JS */

// ── Toast notifications ──────────────────────────
function showToast(message, type = 'success') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>${icons[type] || icons.success}</span> ${message}`;
  document.body.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  });
}

// ── Confirm delete ───────────────────────────────
function confirmDelete(formId, name) {
  if (confirm(`Delete "${name}"? This action cannot be undone.`)) {
    document.getElementById(formId).submit();
  }
}

// ── Animate stat numbers ──────────────────────────
function animateNumber(el) {
  const target = parseInt(el.dataset.target, 10);
  if (isNaN(target)) return;
  const duration = 800;
  const step = target / (duration / 16);
  let current = 0;
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = Math.floor(current).toLocaleString();
    if (current >= target) clearInterval(timer);
  }, 16);
}

// ── Mobile sidebar toggle ────────────────────────
function toggleSidebar() {
  document.querySelector('.sidebar').classList.toggle('open');
}

// ── Active nav highlight ─────────────────────────
function highlightNav() {
  const path = window.location.pathname.split('/')[1] || 'dashboard';
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.remove('active');
    const href = el.getAttribute('href') || '';
    if (href.includes(path) || (path === 'dashboard' && href.includes('dashboard'))) {
      el.classList.add('active');
    }
  });
}

// ── Init ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Animate stat numbers
  document.querySelectorAll('.stat-number[data-target]').forEach(animateNumber);

  // Highlight nav
  highlightNav();

  // Auto-dismiss alerts
  const alerts = document.querySelectorAll('.auto-dismiss');
  alerts.forEach(a => setTimeout(() => a.remove(), 4000));

  // Form: prevent double submit
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function () {
      const btn = this.querySelector('[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Saving…';
      }
    });
  });
});
