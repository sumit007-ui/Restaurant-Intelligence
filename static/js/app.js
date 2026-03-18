/* ============================================================
   GLOBAL JS — Restaurant Intelligence
   Handles: Sidebar, Flash Toasts, Dropdowns, Feather Icons
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ── 1. Feather Icons ──────────────────────────────────
  if (typeof feather !== 'undefined') {
    feather.replace({ 'stroke-width': 1.8 });
  }

  // ── 2. Sidebar Toggle ─────────────────────────────────
  const sidebar     = document.getElementById('sidebar');
  const toggleBtn   = document.getElementById('toggle-sidebar');
  const mainContent = document.getElementById('main-content');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      if (mainContent) mainContent.classList.toggle('expanded');
    });
  }

  // ── 3. Flash Toasts ───────────────────────────────────
  const iconMap = {
    success: 'check-circle',
    danger:  'x-circle',
    warning: 'alert-triangle',
    info:    'info',
    error:   'x-circle',
  };

  document.querySelectorAll('.flash-message[data-category]').forEach(el => {
    const category = el.dataset.category;
    const message  = el.textContent.trim();
    if (!message) return;
    showToast(message, category);
  });

  function showToast(msg, type = 'info') {
    let container = document.getElementById('flash-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'flash-container';
      container.className = 'flash-container';
      document.body.appendChild(container);
    }

    const icon = iconMap[type] || 'info';
    const toast = document.createElement('div');
    toast.className = `flash-toast ${type}`;
    toast.innerHTML = `
      <i data-feather="${icon}" class="flash-icon" style="width:18px;height:18px;"></i>
      <span class="flash-text">${msg}</span>
      <button class="flash-close" onclick="this.parentElement.remove()">&#x2715;</button>
    `;
    container.appendChild(toast);
    if (typeof feather !== 'undefined') feather.replace({ 'stroke-width': 2 });

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(40px)';
      toast.style.transition = 'all 0.35s ease';
      setTimeout(() => toast.remove(), 350);
    }, 4500);
  }

  // Expose globally for manual use
  window.showToast = showToast;

  // ── 4. User Dropdown ──────────────────────────────────
  const userTrigger  = document.getElementById('user-trigger');
  const userDropdown = document.getElementById('user-dropdown');

  if (userTrigger && userDropdown) {
    userTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('show');
    });

    document.addEventListener('click', () => {
      userDropdown.classList.remove('show');
    });

    userDropdown.addEventListener('click', e => e.stopPropagation());
  }

  // ── 5. Active Sidebar Link ────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // ── 6. Confirm Delete Dialogs ─────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', function (e) {
      const msg = this.dataset.confirm || 'Are you sure?';
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // ── 7. AOS Init ───────────────────────────────────────
  if (typeof AOS !== 'undefined') {
    AOS.init({ duration: 450, once: true, offset: 30 });
  }
});
