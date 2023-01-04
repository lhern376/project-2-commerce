// >>>>>>>>>>>>>>>>>>>> Tooltip setup

var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
});

/**
 * Alternatively to the above approach:
 */

// const tooltips = document.querySelectorAll('.tt') // .tt is the class selector set on the tooltips
// tooltips.forEach(t => {
//   new bootstrap.Tooltip(t)
// })