
// >>>>>>>>>>>>>>>>>>>> For tracking is_gallery_active after toggling gallery view

const input_hidden_gallery = document.querySelector(".js-hidden"); // form element (input type=hidden)

const page_links = document.querySelectorAll(".js-link");

// >>>>>>>>>>>>>>>>>>>> Toggling between grid and list view

const switch_button = document.querySelector(".js-switch");

const ul = document.querySelector(".js-ul");
const li_list = document.querySelectorAll(".js-ul li");
switch_button.addEventListener("click", (e) => {

    if (switch_button.checked){
        input_hidden_gallery.value = "active"
        ul.classList.add("css-wrapper-ul");
        for (const li of li_list){  
            li.classList.remove("flex-sm-row", "align-items-sm-start");
        }

        // Set page-links for pagination consistency with gallery view
        // Check that they are not active already (this check is necessary because down below I'm performing a programmatic click on the gallery button on page load)
        // Do this only if there is pagination
        if (page_links.length !== 0){
            let check_for_active = page_links[0].getAttribute("href");
            check_for_active = check_for_active.substring(check_for_active.length - 6);
            if (check_for_active !== "active") {
                for (const link of page_links) {
                    let href_value = link.getAttribute("href");
                    link.setAttribute("href", href_value + "active");
                }
            }
        }

    } else {
        input_hidden_gallery.value = "" // empty string represents inactive gallery view
        ul.classList.remove("css-wrapper-ul");
        for (const li of li_list){  
            li.classList.add("flex-sm-row", "align-items-sm-start");
        }

        // unset page-links for pagination consistency with gallery view
        // This check is also necessary as a consequence of the programmatic click down below
        // Do this only if there is pagination
        if (page_links.length !== 0){
            let check_for_active = page_links[0].getAttribute("href");
            check_for_active = check_for_active.substring(check_for_active.length - 6);
            if (check_for_active === "active") {
                for (const link of page_links) {
                    let href_value = link.getAttribute("href");
                    href_value = href_value.substring(0, href_value.length - 6);
                    link.setAttribute("href", href_value);
                }
            }
        }
    }
});

if (input_hidden_gallery.value){
    switch_button.click();
}


// >>>>>>>>>>>>>>>>>>>> Moving the form element around to and from modal

const parentOriginal = document.querySelector(".js-container-parent");
const parentModal = document.querySelector(".js-modal-parent");
const child = document.querySelector(".js-form-child");

// this adds the form to modal
document.querySelector(".js-modal-button").addEventListener("click", (e) => {

    parentModal.appendChild(child);
});



// this adds the form back to aside
const modalContainer = document.querySelector(".js-modal-container");
const modalCloseButton = document.querySelector(".js-close-modal-button");
document.addEventListener("click", (e) => {

    const element = e.target;

    if (element === modalContainer || element === modalCloseButton) {
        parentOriginal.appendChild(child);
    }

});


// >>>>>>>>>>>>>>>>>>>> Adding/removing from Watchlist

// -- simulate sleep:
// function sleep(ms) {
//     return new Promise(resolve => setTimeout(resolve, ms));
// }

async function modifyWatchlist(event, btn) {
    try {

        let action = btn.getAttribute("data-js-action");
        let listing_id = btn.getAttribute("data-js-id");

        const response = await fetch(`/watchlist/${action}/${listing_id}`);

        if (response.ok) {

            // loading spinner OFF
            // await sleep(2000); // uncomment fuction 'sleep' above to simulate sleep
            btn.querySelector("div").classList.remove("spinner-border", "spinner-border-sm", "text-primary", "opacity-75");
            btn.querySelector(".bi").classList.remove("visually-hidden");

            const badge = document.querySelector(".js-watchlist-badge");
            if (action === "add") {
                // ('remove' and 'bi-heart-fill' go together)
                btn.setAttribute("data-js-action", "remove");
                btn.setAttribute("title", "remove from watchlist");
                btn.querySelector(".bi").classList.replace("bi-heart", "bi-heart-fill");
                
                let count = parseInt(badge.textContent) + 1;
                badge.textContent = count;
            } else { 
                // ('add' and 'bi-heart' go together)
                btn.setAttribute("data-js-action", "add");
                btn.setAttribute("title", "add to watchlist");
                btn.querySelector(".bi").classList.replace("bi-heart-fill", "bi-heart");

                let count = parseInt(badge.textContent) - 1;
                badge.textContent = count;
            }
            
        }
    }
    catch (error) {
        console.error(`${error}`);
    }
}

const buttons = document.querySelectorAll('.js-watchlist-btn');
for (const btn of buttons){
    btn.addEventListener('click', (e) => {

        // loading spinner ON
        btn.querySelector("div").classList.add("spinner-border", "spinner-border-sm", "text-primary", "opacity-75");
        btn.querySelector(".bi").classList.add("visually-hidden");

        modifyWatchlist(e, btn);
    });
}




