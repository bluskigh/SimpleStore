const cart = document.querySelector(".cart");
if (!cart) {
  alert("Could not find the cart");
} else {
  // this should run on load of the page
  // update the cart with appropriate amount
  fetch('/cart/amount')
  .then(async r => await r.json())
  .then((r) => {
    // update the cart p with this result
    cart.innerText = r.amount;
  })
  .catch((e) => {console.error(e)})
}

function addToCart(obj) {
  try {
    id = obj.parentElement.getAttribute("name");
    // make a ajax post request with the item this person wants to add to their cart 
    fetch("/cart/add", 
      {
        method: "POST",
        header: new Headers({"Content-Type": "application/json"}),
        body: JSON.stringify({id})
      }
    ).then(async r => await r.json()) 
    .then((r) => {
      if (r.added) {
        cart.innerText = (+cart.innerText) + 1;
      }else {
        alert("There was an issue adding your item to the cart...Refresh and try again.");
      }
    })

    // if successful increment their cart icon 

  } catch(e) {
    console.print("Error should be because could not find cart. Nothing serious");
    console.error(e);
  }
}

// On load of the page, load the cart notif with users cart amount

const deleteButton = document.querySelector("#delete");
if (deleteButton) {
  const deleteForm = deleteButton.parentElement;
  deleteForm.addEventListener("submit", function(e) {
    e.preventDefault()
    if (prompt("Are you going sure?")) {
      // submit the form
      deleteForm.submit();
    } else {
      alert("Account was NOT deleted.");
    }
  })
}
