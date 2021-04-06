const cart = document.querySelector(".cart_notif");
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

const getIdFromProduct = (obj) => {
  return obj.parentElement.getAttribute("name");
}

function addToCart(obj) {
  try {
    id = getIdFromProduct(obj);
    // make a ajax post request with the item this person wants to add to their cart 
    fetch("/cart/add", {
        method: "POST",
        body: JSON.stringify({id}),
        headers: new Headers({
          "Content-Type": "application/json"
        })
     })
    .then(async r => await r.json()) 
    .then((r) => {
      if (r.added) {
        cart.innerText = (+cart.innerText) + 1;
        obj.disabled = true;
        obj.parentElement.querySelector(".inCart").classList.toggle("hidden");
        obj.classList.toggle("disabled");
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

function removeFromCart(obj) {
  id = getIdFromProduct(obj);
  // make a fetch request to the web server to (ajax) to remove this product
  fetch("/cart/remove", {
    method: "POST",
    body: JSON.stringify({id}),
    headers: new Headers({
      "Content-Type": "application/json"
    })
  })
  .then(async r => await r.json())
  .then((r) => { 
    if (r.removed) {
      // decrement from cart
      cart.innerText = (+cart.innerText) - 1;
      obj.parentElement.parentElement.removeChild(obj.parentElement);
    } else {
      // TODO: when failed refresh the page? So you can show a flash message instead ?
      alert("Could not remove ", id, " from your cart. Refreh and try again")
    }
  })
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

const addButton = document.querySelectorAll('.addProduct');
const determineInCart = async () => {
  for (button of addButton) {
    try {
      var r = await fetch('/cart/'+ button.parentElement.getAttribute("name")+'/exist')
      r = await r.json();
      if (!r.result) {
        button.disabled= false;
      } else {
        button.parentElement.querySelector(".inCart").classList.remove('hidden');
        // does exist in our cart, do not allow to add
        button.disabled = true;
        button.classList.toggle("disabled");
      }
    } catch(e) {
      console.error(e);
    }
  }
}
if (addButton) {
  determineInCart();
}
