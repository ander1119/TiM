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

var modal = document.getElementById("myModal");
var openModalBtn = document.getElementById("openModalBtn");
var closeModalBtn = document.getElementsByClassName("close")[0];

// Open the modal
openModalBtn.onclick = function() {
    modal.style.display = "block";
}

// Close the modal
closeModalBtn.onclick = function() {
    modal.style.display = "none";
}

// Close the modal when clicking outside of it
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}