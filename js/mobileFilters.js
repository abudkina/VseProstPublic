/**
 * Мобильные фильтры: по клику на иконку открывается панель выбора (drawer).
 * Используется на главной, решениях и избранном.
 */
const DRAWER_ID = 'mobileFilterDrawer';
const MOBILE_BREAKPOINT = 768;

function isMobile() {
  return window.innerWidth < MOBILE_BREAKPOINT;
}

function getDrawer() {
  return document.getElementById(DRAWER_ID);
}

function openDrawer(title, bodyContent) {
  const drawer = getDrawer();
  if (!drawer) return;
  const titleEl = drawer.querySelector('.mobile-filter-panel-title');
  const bodyEl = drawer.querySelector('.mobile-filter-panel-body');
  if (titleEl) titleEl.textContent = title;
  if (bodyEl) {
    bodyEl.innerHTML = '';
    if (typeof bodyContent === 'function') bodyContent(bodyEl);
    else if (bodyContent) bodyEl.appendChild(bodyContent);
  }
  drawer.classList.add('is-open');
  drawer.setAttribute('aria-hidden', 'false');
}

function closeDrawer() {
  const drawer = getDrawer();
  if (!drawer) return;
  drawer.classList.remove('is-open');
  drawer.setAttribute('aria-hidden', 'true');
  const bodyEl = drawer.querySelector('.mobile-filter-panel-body');
  if (bodyEl) {
    const hashtagsWrapper = bodyEl.querySelector('.hashtags-drawer-wrapper');
    if (hashtagsWrapper) {
      const desktopFilters = document.querySelector('.search-filters .filters.desktop');
      const dropdown = hashtagsWrapper.querySelector('.ts-dropdown');
      if (dropdown) {
        dropdown.classList.remove('ts-dropdown-in-drawer');
        document.body.appendChild(dropdown);
        if (hashtagsWrapper._dropdownWidthObserver) {
          hashtagsWrapper._dropdownWidthObserver.disconnect();
          delete hashtagsWrapper._dropdownWidthObserver;
        }
      }
      const moved = hashtagsWrapper.querySelector('.ts-wrapper, .vs-wrapper') || hashtagsWrapper.firstElementChild;
      if (moved && desktopFilters) desktopFilters.appendChild(moved);
    }
  }
}

const SORT_ICONS = {
  default: 'fa-sort',
  popularity: 'fa-fire',
  date: 'fa-calendar-alt',
  show: 'fa-eye'
};

function buildSortContent(onChange) {
  const fragment = document.createDocumentFragment();
  const sortSelect = document.getElementById('sort');
  const current = sortSelect ? sortSelect.value : 'default';
  const options = [
    { value: 'default', label: 'Сортировать' },
    { value: 'popularity', label: 'По популярности' },
    { value: 'date', label: 'По дате' },
    { value: 'show', label: 'По просмотрам' }
  ];
  options.forEach(opt => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'mobile-filter-option' + (opt.value === current ? ' is-active' : '');
    btn.dataset.value = opt.value;
    const icon = document.createElement('span');
    icon.className = 'mobile-filter-option-icon';
    icon.innerHTML = '<i class="fas ' + (SORT_ICONS[opt.value] || 'fa-sort') + '"></i>';
    btn.appendChild(icon);
    btn.appendChild(document.createTextNode(opt.label));
    btn.addEventListener('click', () => {
      if (sortSelect) {
        sortSelect.value = opt.value;
        sortSelect.dispatchEvent(new Event('change', { bubbles: true }));
      }
      if (onChange) onChange();
      closeDrawer();
    });
    fragment.appendChild(btn);
  });
  return fragment;
}

function buildCategoryContent(onChange) {
  const fragment = document.createDocumentFragment();
  const categorySelect = document.getElementById('category');
  if (!categorySelect) return fragment;
  const current = categorySelect.value;
  for (let i = 0; i < categorySelect.options.length; i++) {
    const opt = categorySelect.options[i];
    const value = opt.value;
    const label = opt.textContent.trim();
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'mobile-filter-option' + (String(value) === String(current) ? ' is-active' : '');
    btn.dataset.value = value;
    const icon = document.createElement('span');
    icon.className = 'mobile-filter-option-icon';
    icon.innerHTML = '<i class="fas fa-folder"></i>';
    btn.appendChild(icon);
    btn.appendChild(document.createTextNode(label));
    btn.addEventListener('click', () => {
      categorySelect.value = value;
      categorySelect.dispatchEvent(new Event('change', { bubbles: true }));
      if (onChange) onChange();
      closeDrawer();
    });
    fragment.appendChild(btn);
  }
  return fragment;
}

function buildHashtagsContent() {
  const wrapper = document.createElement('div');
  wrapper.className = 'hashtags-drawer-wrapper';
  const desktopFilters = document.querySelector('.search-filters .filters.desktop');
  const hashtagsSelect = document.getElementById('hashtags');
  if (!hashtagsSelect || !desktopFilters) return wrapper;
  const tsWrapper = desktopFilters.querySelector('.ts-wrapper, .vs-wrapper');
  const selectParent = hashtagsSelect.parentElement;
  const toMove = tsWrapper || (selectParent && selectParent.classList.contains('ts-wrapper') ? selectParent : hashtagsSelect);
  if (toMove) wrapper.appendChild(toMove);
  // Переносим dropdown TomSelect из body в панель, чтобы подсказки были видны поверх drawer
  const dropdown = document.body.querySelector('.ts-dropdown');
  if (dropdown) {
    dropdown.classList.add('ts-dropdown-in-drawer');
    wrapper.appendChild(dropdown);
    function setDropdownWidth() {
      const panel = wrapper.closest('.mobile-filter-panel');
      const w = panel ? panel.offsetWidth : Math.min(480, window.innerWidth * 0.92);
      dropdown.style.setProperty('width', w + 'px', 'important');
      dropdown.style.setProperty('min-width', '280px', 'important');
    }
    setDropdownWidth();
    // TomSelect перезаписывает width при открытии — подправляем при каждом показе
    const mo = new MutationObserver(setDropdownWidth);
    mo.observe(dropdown, { attributes: true, attributeFilter: ['style'] });
    wrapper._dropdownWidthObserver = mo;
  }
  return wrapper;
}

/**
 * @param {Object} opts
 * @param {function} [opts.onFilterChange] — вызывается после смены фильтра (перезагрузка списка)
 */
export function initMobileFilters(opts = {}) {
  const onFilterChange = opts.onFilterChange || (() => {});

  const drawer = getDrawer();
  if (!drawer) return;

  const backdrop = drawer.querySelector('.mobile-filter-drawer-backdrop');
  const closeBtn = drawer.querySelector('.mobile-filter-panel-close');
  if (backdrop) backdrop.addEventListener('click', closeDrawer);
  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);

  document.querySelectorAll('.mobile-filter-trigger').forEach(trigger => {
    trigger.addEventListener('click', () => {
      if (!isMobile()) return;
      const filter = trigger.getAttribute('data-filter');
      if (filter === 'sort') {
        openDrawer('Сортировка', (body) => body.appendChild(buildSortContent(onFilterChange)));
      } else if (filter === 'category') {
        openDrawer('Категория', (body) => body.appendChild(buildCategoryContent(onFilterChange)));
      } else if (filter === 'hashtags') {
        openDrawer('Хэштеги', buildHashtagsContent());
      }
    });
  });
}
