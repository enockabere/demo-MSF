// menu
// popovers Initialization
var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl)
})

$(document).ready(function () {
    $('table.display').DataTable({
        "pageLength": 5,
        "order": [
            [0, "desc"]
        ]
    });
});

const nxtBtn = document.querySelector('#submitBtn');
const form1 = document.querySelector('#form1');
const form2 = document.querySelector('#form2');
const form3 = document.querySelector('#form3');
const form4 = document.querySelector('#form4');
const form5 = document.querySelector('#form5');


const icon1 = document.querySelector('#icon1');
const icon2 = document.querySelector('#icon2');
const icon3 = document.querySelector('#icon3');
const icon4 = document.querySelector('#icon4');
const icon5 = document.querySelector('#icon5');


var viewId = 1;

function nextForm() {
    console.log("hellonext");
    viewId = viewId + 1;
    progressBar();
    displayForms();

    console.log(viewId);

}

function prevForm() {
    console.log("helloprev");
    viewId = viewId - 1;
    console.log(viewId);
    progressBar1();
    displayForms();
}

function progressBar1() {
    if (viewId === 1) {
        icon2.classList.add('active');
        icon2.classList.remove('active');
        icon3.classList.remove('active');
        icon4.classList.remove('active');
        icon5.classList.remove('active');
    }
    if (viewId === 2) {
        icon2.classList.add('active');
        icon3.classList.remove('active');
        icon4.classList.remove('active');
        icon5.classList.remove('active');
    }
    if (viewId === 3) {
        icon3.classList.add('active');
        icon4.classList.remove('active');
        icon5.classList.remove('active');
    }
    if (viewId === 4) {
        icon4.classList.add('active');
        icon5.classList.remove('active');
    }
    if (viewId === 5) {
        icon5.classList.add('active');
        nxtBtn.innerHTML = "Submit"
    }
    if (viewId > 5) {
        icon2.classList.remove('active');
        icon3.classList.remove('active');
        icon4.classList.remove('active');
        icon5.classList.remove('active');

    }
}

function progressBar() {
    if (viewId === 2) {
        icon2.classList.add('active');
    }
    if (viewId === 3) {
        icon3.classList.add('active');
    }
    if (viewId === 4) {
        icon4.classList.add('active');
    }
    if (viewId === 5) {
        icon5.classList.add('active');
        nxtBtn.innerHTML = "Submit"
    }
    if (viewId > 5) {
        icon2.classList.remove('active');
        icon3.classList.remove('active');
        icon4.classList.remove('active');
        icon5.classList.remove('active');

    }
}

function displayForms() {

    if (viewId > 5) {
        viewId = 1;
    }

    if (viewId === 1) {
        form1.style.display = 'block';
        form2.style.display = 'none';
        form3.style.display = 'none';
        form4.style.display = 'none';
        form5.style.display = 'none';


    } else if (viewId === 2) {
        form1.style.display = 'none';
        form2.style.display = 'block';
        form3.style.display = 'none';
        form4.style.display = 'none';
        form5.style.display = 'none';

    } else if (viewId === 3) {
        form1.style.display = 'none';
        form2.style.display = 'none';
        form3.style.display = 'block';
        form4.style.display = 'none';
        form5.style.display = 'none';
    } else if (viewId === 4) {
        form1.style.display = 'none';
        form2.style.display = 'none';
        form3.style.display = 'none';
        form4.style.display = 'block';
        form5.style.display = 'none';

    } else if (viewId === 5) {
        form1.style.display = 'none';
        form2.style.display = 'none';
        form3.style.display = 'none';
        form4.style.display = 'none';
        form5.style.display = 'block';

    }

}

// Example starter JavaScript for disabling form submissions if there are invalid fields
(function () {
    'use strict'

    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.querySelectorAll('.needs-validation')

    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
        .forEach(function (form) {
            form.addEventListener('submit', function (event) {
                if (!form.checkValidity()) {
                    event.preventDefault()
                    event.stopPropagation()
                }

                form.classList.add('was-validated')
            }, false)
        })
})()
$(function () {
    $('[data-toggle="tooltip"]').tooltip();
});
$(document).ready(function () {
    $("#approveBtn").click(function () {
        $("#approvalForm").toggle(500)
    })
})