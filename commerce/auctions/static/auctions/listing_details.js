// https://docs.djangoproject.com/en/4.1/howto/csrf/#using-csrf
// https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch --> the json example is different from what im using here (im using application/x-www-form-urlencoded: data=str(field1=value1&field2=value2))
// https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/POST  

// bidding functionality elements 
const bid_form_btn = document.querySelector('.js-bid-form-btn');
const loading_spinner = document.querySelector('.js-bid-loading-spinner');
const bid_form = document.querySelector('.js-bid-form');
const min_bid_btn = document.querySelector('.js-min-bid-btn');
const current_price_elem = document.querySelector('.js-current-price');
const bid_form_btn_close = document.querySelector('.js-bid-form-close');
const bid_success = document.querySelector('.js-bid-success');
const bid_error = document.querySelector('.js-error');

// >>>>>>>>>>>>>>>>>>>> Comments functionality

// Sending the http request with the csrftoken

async function postData(url, data, csrftoken){

    try{
        const response = await fetch(url, {
            method: 'POST', // or 'PUT'
            headers: {
                // 'Content-Type': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            mode: 'same-origin', // assures that csrf token is not sent to another domain
            // body: JSON.stringify(data) // for 
            body: data
        });

        if (response.ok){
            // I expect json sent from the view
            const data = await response.json();
            console.log(data["message"]);
            window.location.reload();
        }
    }
    catch (error) {
        console.error(`${error}`);
    }
}


// event for comment submission

const comment_form = document.querySelector('.js-form-comment'); 
const csrftoken = comment_form.querySelector('input[type=hidden]').value;



comment_form.addEventListener("submit", (event) => {
    event.preventDefault();

    let comment = comment_form.querySelector('textarea').value;
    let data = `comment=${comment}&bidding_starts=${bid_form_btn.getAttribute('data-js-listing-start-date').replace('+','%2B')}`; // plus sign (+) gets sanatized into blank space when sending data as urlencoded so it needs to be replaced

    postData(`/listing/comment/${comment_form.getAttribute("data-js-listing")}`, data, csrftoken);
});


// events for replies 

const reply_forms_arr = document.querySelectorAll(".js-form-reply");
// already have the csrftoken

for (const reply_form of reply_forms_arr){

    reply_form.addEventListener("submit", (event) => {
        event.preventDefault();

        let reply = reply_form.querySelector('textarea').value;
        let reply_to = reply_form.getAttribute("data-js-reply-to");
        let data = `reply=${reply}&reply_to=${reply_to}&bidding_starts=${bid_form_btn.getAttribute('data-js-listing-start-date').replace('+','%2B')}`;
    
        postData(`/listing/reply/${reply_form.getAttribute("data-js-comment")}`, data, csrftoken);
    });
}


// >>>>>>>>>>>>>>>>>>>> Bidding functionality


// get updated min bid and current price
async function getMinBidAmount(listing_id, start_date){
    try{
        const response = await fetch(`/listing/${listing_id}/get-min-bid`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // 'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            mode: 'same-origin', // assures that csrf token is not sent to another domain
            body: JSON.stringify(
                    { 
                        bidding_starts: start_date
                    }
                )
            // body: data
        });

        console.log(response.status);
        if (response.ok) {

            const data = await response.json();
            console.log(data);
            // if listing closes or is edited
            if (data['reload']){
                window.location.reload()
            }
            // spinner off
            loading_spinner.classList.add('d-none');
            // show form
            bid_form.classList.remove('d-none');

            current_price_elem.textContent = data['current_price'];
            min_bid_btn.textContent = `Bid $${data['min_bid']}`;
            min_bid_btn.setAttribute('data-js-min-bid', data['min_bid']);
        }
    }
    catch (error){
        console.error(`Could not get data: ${error}`);
    }
}

// place bid function
async function placeBid(listing_id, bid_amount, start_date){
    try{
        const response = await fetch(`/listing/${listing_id}/set-bid`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // 'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            mode: 'same-origin', // assures that csrf token is not sent to another domain
            body: JSON.stringify(
                    {
                        bid: bid_amount, 
                        bidding_starts: start_date
                    }
                )
            // body: data
        });

        console.log(response.status);
        if (response.ok) {

            const data = await response.json();
            // if listing closes or is edited
            if (data['reload']){
                window.location.reload()
            }
            // spinner off
            loading_spinner.classList.add('d-none');

            // if error, show form with the error and updated values
            if (data['error']){
                bid_form.classList.remove('d-none');
                bid_error.classList.remove('d-none');
                bid_error.textContent = data['error'];

                current_price_elem.textContent = data['current_price'];
                min_bid_btn.textContent = `Bid $${data['min_bid']}`;
                min_bid_btn.setAttribute('data-js-min-bid', data['min_bid']);
            }   
            // else, display success message
            else{
                bid_form.classList.add('d-none');
                bid_success.classList.remove('d-none');
            }
        }
    }
    catch (error){
        console.error(`Could not get data: ${error}`);
    }
}

document.addEventListener('click', (event) => {

    const element = event.target;

    // reload page on closing modal
    if (element === bid_form_btn_close){
        window.location.reload();
    }
    
    // get data (min bid) on opening modal
    if (element === bid_form_btn){
        // make loading spinner visible
        loading_spinner.classList.remove('d-none');
        getMinBidAmount(
            bid_form_btn.getAttribute('data-js-listing-id'), 
            bid_form_btn.getAttribute('data-js-listing-start-date')
        );
    }

    // place min bid
    if (element === min_bid_btn){
        // hide form and make loading spinner visible
        bid_form.classList.add('d-none');
        loading_spinner.classList.remove('d-none');
        placeBid(
            bid_form_btn.getAttribute('data-js-listing-id'),
            min_bid_btn.getAttribute('data-js-min-bid'),
            bid_form_btn.getAttribute('data-js-listing-start-date')
        );
    }

    
});

// place custom bid
document.querySelector(".js-custom-bid-form").addEventListener("submit", (event) => {
    event.preventDefault();

    // hide form and make loading spinner visible
    bid_form.classList.add('d-none');
    loading_spinner.classList.remove('d-none');
    placeBid(
        bid_form_btn.getAttribute('data-js-listing-id'),
        document.querySelector('.js-custom-bid-input').value,
        bid_form_btn.getAttribute('data-js-listing-start-date')
    );

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
            const watchers_tag = document.querySelector(".js-details-watcher-count");
            if (action === "add") {
                // ('remove' and 'bi-heart-fill' go together)
                btn.setAttribute("data-js-action", "remove");
                btn.setAttribute("title", "remove from watchlist");
                btn.querySelector(".bi").classList.replace("bi-heart", "bi-heart-fill");
                
                let count = parseInt(badge.textContent) + 1;
                badge.textContent = count;
                count = parseInt(watchers_tag.textContent) + 1;
                watchers_tag.textContent = count;
            } else { 
                // ('add' and 'bi-heart' go together)
                btn.setAttribute("data-js-action", "add");
                btn.setAttribute("title", "add to watchlist");
                btn.querySelector(".bi").classList.replace("bi-heart-fill", "bi-heart");

                let count = parseInt(badge.textContent) - 1;
                badge.textContent = count;
                count = parseInt(watchers_tag.textContent) - 1;
                watchers_tag.textContent = count;
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