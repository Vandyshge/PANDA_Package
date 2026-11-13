(() => {
  const sidebar = document.querySelector('.side');
  const menu = document.querySelector('.mobile');
  menu.addEventListener('click', () => {
    menu.setAttribute('aria-expanded', sidebar.classList.toggle('open'));
  });

  const dialog = document.querySelector('dialog[aria-label="Search documentation"]');
  const query = dialog.querySelector('input');
  const results = dialog.querySelector('ul');
  const status = dialog.querySelector('[role="status"]');
  function search() {
    const term = query.value.toLowerCase().trim();
    const words = term.split(/\s+/).filter(Boolean);
    const score = ({ title }) => {
      const name = title.toLowerCase();
      if (name === term || 'panda_md.' + name === term) return 0;
      if (name.includes(term)) return 1;
      return 2;
    };
    const matches = term
      ? window.pandaSearch.filter(({ title, text }) =>
        words.every(word => (title + ' ' + text).toLowerCase().includes(word))
      ).sort((left, right) => score(left) - score(right))
      : window.pandaSearch.filter(({ href }) => !href.includes('#'));
    results.replaceChildren(...matches.map(({ title, href }) => {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = href;
      link.textContent = title;
      item.append(link);
      return item;
    }));
    status.textContent = matches.length ? '' : 'No results. Try a method name or a different term.';
  }
  function openSearch() {
    if (dialog.open) return;
    dialog.showModal();
    query.focus();
    query.select();
    search();
  }
  document.querySelector('.search-toggle').addEventListener('click', openSearch);
  document.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      openSearch();
    }
  });
  query.addEventListener('input', search);
  query.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      event.preventDefault();
      results.querySelector('a')?.click();
    }
  });
  results.addEventListener('click', event => {
    if (event.target.closest('a')) dialog.close();
  });

  document.querySelectorAll('.code').forEach(block => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy';
    button.textContent = 'Copy';
    button.addEventListener('click', async () => {
      const code = block.querySelector('code');
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.textContent = 'Copied';
      } catch {
        const range = document.createRange();
        range.selectNodeContents(code);
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
        button.textContent = 'Selected';
      }
      setTimeout(() => { button.textContent = 'Copy'; }, 1500);
    });
    block.append(button);
  });

  const filters = document.querySelector('.filters');
  if (filters) {
    const rows = Array.from(document.querySelectorAll('tbody tr[data-pore]'));
    const apply = () => {
      const { pore, operation } = filters.elements;
      let count = 0;
      rows.forEach(row => {
        row.hidden = (pore.value && row.dataset.pore !== pore.value) ||
          (operation.value && row.dataset[operation.value] !== '1');
        count += Number(!row.hidden);
      });
      filters.querySelector('output').textContent = count + ' of ' + rows.length + ' shapes';
    };
    filters.addEventListener('change', apply);
    apply();
  }
})();
