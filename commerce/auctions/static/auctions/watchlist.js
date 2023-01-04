// in the watchlist, items can only be removed

// -- simulate sleep:
// function sleep(ms) {
//     return new Promise(resolve => setTimeout(resolve, ms));
// }


async function modifyWatchlist(event, btn) {
    try {

        let listing_id = btn.getAttribute("data-js-id");
        const response = await fetch(`/watchlist/remove/${listing_id}`);

        if (response.ok) {

            // loading spinner OFF (better to simulate in server)
            // await sleep(2000); // uncomment fuction 'sleep' above to simulate sleep

            const badge = document.querySelector(".js-watchlist-badge");
            let count = parseInt(badge.textContent) - 1;
            badge.textContent = count;

            // setting off animation (switch_button is already declared and assigned in main.js)
            // only animate if gallery view is turned off
            if (!switch_button.checked){
                btn.parentNode.parentNode.classList.add("animated-li");
                btn.parentNode.parentNode.style.animationPlayState = "running";
                btn.parentNode.parentNode.addEventListener("animationend", () => {
                    btn.parentNode.parentNode.remove();
                    btn_initial_quantity--;
                    if (btn_initial_quantity === 0){
                        window.location.reload();
                    }
                });
            }
            else {
                // remove from gallery with a different animation
                btn.parentNode.parentNode.classList.add("animated-li-gallery");
                btn.parentNode.parentNode.style.animationPlayState = "running";
                btn.parentNode.parentNode.addEventListener("animationend", () => {
                    btn.parentNode.parentNode.remove();
                    btn_initial_quantity--;
                    if (btn_initial_quantity === 0){
                        window.location.reload();
                    }
                });
            }
            
        }
    }
    catch (error) {
        console.error(`${error}`);
    }
}

// renamed const to resolve conflict in main.js ('buttons' const)
const btns = document.querySelectorAll('.js-btn');
// for keeping track of buttons closed
let btn_initial_quantity = btns.length;

for (const btn of btns){
    btn.addEventListener('click', (e) => {

        // loading spinner ON
        btn.querySelector("div").classList.add("spinner-border", "spinner-border-sm", "text-primary", "opacity-75");
        btn.querySelector(".bi").classList.add("visually-hidden");

        modifyWatchlist(e, btn);
    });
}


// >>>>>>>>>>>>>>>>>>>> Providing a fade animation only when list view is active (grid/gallery inactive)
// main.js already has these references

// const switch_button = document.querySelector(".js-switch");  
// const ul = document.querySelector(".js-ul");
// const li_list = document.querySelectorAll(".js-ul li");
