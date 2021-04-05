const cart = document.querySelector(".cart");
if (!cart) {
  alert("Could not find the cart");
}
function addToCart(obj) {
  console.log(obj.parentElement.getAttribute("name"));
}

// On load of the page, load the cart notif with users cart amount
