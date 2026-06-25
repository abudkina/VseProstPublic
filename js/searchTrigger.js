/**
 * Десктоп: поле поиска всегда в строке.
 * Мобильный: лупа, по клику — нижняя панель с полем (поле переносится в панель).
 */
const MOBILE_BREAKPOINT = 768;

function isMobile() {
  return window.innerWidth < MOBILE_BREAKPOINT;
}

function initSearchTrigger() {
  const drawer = document.getElementById('searchDrawer');
  const input = document.getElementById('search');
  const btn = document.querySelector('.search-trigger-btn');
  if (!drawer || !input || !btn) return;

  const desktopSlot = input.closest('.search-filters')?.querySelector('.search-input-desktop') ?? document.querySelector('.search-input-desktop');
  const drawerSlot = drawer.querySelector('.search-drawer-input-slot');
  const backdrop = drawer.querySelector('.search-drawer-backdrop');
  const closeBtn = drawer.querySelector('.search-drawer-close');

  if (!desktopSlot || !drawerSlot) return;

  function moveInputToDrawer() {
    if (input.parentElement !== drawerSlot) drawerSlot.appendChild(input);
  }

  function moveInputToDesktop() {
    if (input.parentElement !== desktopSlot) desktopSlot.appendChild(input);
  }

  function openDrawer() {
    if (!isMobile()) return;
    moveInputToDrawer();
    drawer.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    setTimeout(() => input.focus(), 100);
  }

  function closeDrawer() {
    moveInputToDesktop();
    drawer.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
  }

  if (btn) btn.addEventListener('click', openDrawer);
  if (backdrop) backdrop.addEventListener('click', closeDrawer);
  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);

  input.addEventListener('blur', () => {
    setTimeout(() => {
      if (document.activeElement !== input && !input.value.trim()) closeDrawer();
    }, 150);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSearchTrigger);
} else {
  initSearchTrigger();
}
