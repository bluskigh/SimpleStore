function closeFlash(obj) {
  // removing the current error from parent
  obj.parentElement.parentElement.removeChild(obj.parentElement);
}
