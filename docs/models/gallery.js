const dialog = document.querySelector('.shape-dialog');
const title = dialog.querySelector('h2');
const status = dialog.querySelector('[role="status"]');
const view = dialog.querySelector('.shape-view');
const download = dialog.querySelector('a');
let viewerModule;
let request = 0;

document.querySelectorAll('[data-model]').forEach(button => {
  button.addEventListener('click', async () => {
    const current = ++request;
    const name = button.closest('article').querySelector('h3').textContent;
    title.textContent = name;
    download.href = button.dataset.model;
    status.textContent = 'Loading 3D model…';
    dialog.showModal();

    try {
      viewerModule ??= import('./model-viewer.min.js');
      await viewerModule;
      await customElements.whenDefined('model-viewer');
      if (!dialog.open || current !== request) return;
      const model = document.createElement('model-viewer');
      model.setAttribute('alt', name + ' interactive model');
      model.setAttribute('camera-controls', '');
      model.setAttribute('touch-action', 'pan-y');
      model.setAttribute('interaction-prompt', 'none');
      model.setAttribute('camera-orbit', '30deg 70deg auto');
      model.addEventListener('load', () => {
        if (current === request) status.textContent = 'Drag to rotate. Scroll or pinch to zoom.';
      }, { once: true });
      model.addEventListener('error', () => {
        if (current === request) status.textContent = 'The 3D view could not load. Download the GLB below.';
      }, { once: true });
      model.src = button.dataset.model;
      view.replaceChildren(model);
    } catch {
      viewerModule = undefined;
      if (current === request) status.textContent = 'The 3D view could not load. Download the GLB below.';
    }
  });
});

dialog.addEventListener('close', () => {
  if (!dialog.open) {
    request++;
    view.replaceChildren();
  }
});
