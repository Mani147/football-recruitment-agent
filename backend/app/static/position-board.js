const board = document.querySelector('.tactics-field');
const positionGroup = document.getElementById('position-group');
const objective = document.getElementById('research-objective');

function highlightPosition(group) {
  for (const pin of board.querySelectorAll('.role-pin')) {
    pin.setAttribute('aria-pressed', String(pin.dataset.group === group));
  }
}
board.addEventListener('click', event => {
  const pin = event.target.closest('.role-pin');
  if (!pin) return;
  if (positionGroup) {
    positionGroup.value = pin.dataset.group;
    positionGroup.dispatchEvent(new Event('change'));
    positionGroup.focus();
  } else {
    objective.value = pin.dataset.brief;
    objective.dispatchEvent(new Event('input'));
    objective.focus();
    highlightPosition(pin.dataset.group);
  }
});
if (positionGroup) {
  highlightPosition(positionGroup.value);
  positionGroup.addEventListener('change', () => highlightPosition(positionGroup.value));
} else {
  objective.addEventListener('input', () => highlightPosition(null));
}
