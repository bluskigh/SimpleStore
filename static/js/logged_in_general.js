const cart = document.querySelector(".cart");
if (!cart) {
  alert("Could not find the cart");
}
function addToCart(obj) {
  console.log(obj.parentElement.getAttribute("name"));
}

// On load of the page, load the cart notif with users cart amount

const deleteButton = document.createElement("#delete");
const deleteForm = deleteButton.parentElement;
deleteForm.addEventListener("submit", function(e) {
  e.preventDefault()
  if (prompt("Are you going sure?")) {
    // submit the form
    document.querySelector("#delete").submit();
  } else {
    alert("Account was NOT deleted.");
  }
})
