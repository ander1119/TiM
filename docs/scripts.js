document.querySelectorAll('.bq-toggle-button').forEach(button => {
    button.addEventListener('click', () => {
        const blockquote = button.nextElementSibling;
        if (blockquote.classList.contains('closed-blockquote')) {
            blockquote.classList.toggle('opened-blockquote');
            blockquote.classList.toggle('closed-blockquote');
            button.textContent = blockquote.classList.contains('opened-blockquote') ? 'Click here to hide' : 'Click here to show';
        } else if (blockquote.classList.contains('opened-blockquote')) {
            blockquote.classList.toggle('opened-blockquote');
            blockquote.classList.toggle('closed-blockquote');
            button.textContent = blockquote.classList.contains('opened-blockquote') ? 'Click here to hide' : 'Click here to show';
        }
    });
});

var modalTrope = document.getElementById("myModalTrope");
var openModalBtnTrope = document.getElementById("openModalBtnTrope");
var closeModalBtnTrope = document.getElementsByClassName("closeTrope")[0];

// Open the modal
openModalBtnTrope.onclick = function() {
    modalTrope.style.display = "block";
}

// Close the modal
closeModalBtnTrope.onclick = function() {
    modalTrope.style.display = "none";
}

// Close the modal when clicking outside of it
window.onclick = function(event) {
    if (event.target == modalTrope) {
        modalTrope.style.display = "none";
    }
}

var modalMovie = document.getElementById("myModalMovie");
var openModalBtnMovie = document.getElementById("openModalBtnMovie");
var closeModalBtnMovie = document.getElementsByClassName("closeMovie")[0];

// Open the modal
openModalBtnMovie.onclick = function() {
    modalMovie.style.display = "block";
}

// Close the modal
closeModalBtnMovie.onclick = function() {
    modalMovie.style.display = "none";
}

// Close the modal when clicking outside of it
window.onclick = function(event) {
    if (event.target == modalMovie) {
        modalMovie.style.display = "none";
    }
}