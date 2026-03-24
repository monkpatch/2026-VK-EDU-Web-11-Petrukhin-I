document.querySelectorAll('[data-like-state]').forEach((widget) => {
  const state = widget.dataset.likeState;
  if (state === 'up') {
    widget.querySelector('.btn-up')?.classList.add('btn-success');
  } else if (state === 'down') {
    widget.querySelector('.btn-down')?.classList.add('btn-danger');
  }
});
